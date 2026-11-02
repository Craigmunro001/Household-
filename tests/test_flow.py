from datetime import datetime, timezone

import pytest

from app import flow, notify
from app.flow import Session, handle, parse_amount, parse_choice, parse_term
from app.pricing import load_pricebook

NIGHT = datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc)   # Tue 23:00 SAST
DAY = datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc)      # Tue 10:00 SAST
PB = load_pricebook()
DISCLAIMER = "It is an estimate based on our standard calculation"


class FakeLLM:
    def __init__(self, answer):
        self.answer = answer

    def faq(self, q, lang):
        return self.answer

    def classify(self, *a, **k):
        return None

    def normalise_callback(self, *a, **k):
        return None


def run(session, *texts, now=NIGHT, pb=PB, llm=None):
    return [handle(session, t, now, llm=llm, pricebook=pb) for t in texts]


YES = {"1": "yes", "2": "ja", "3": "yebo"}


def full_chat(lang="1", province="3", debt="250000", term="1", **kw):
    s = Session(phone="27820000000")
    replies = run(s, "hi", lang, YES[lang], "craig", province, debt, term, "2", "2", "tomorrow after 2pm", **kw)
    return s, replies


# ------------------------------------------------------------ happy paths and languages
def test_happy_path_english_gauteng_25_months():
    s, replies = full_chat()
    assert s.status == "completed" and s.lang == "en" and s.name == "Craig"
    a = s.answers
    assert a["province"] == "GP" and a["debt_amount"] == 250000 and a["term"] == 25
    assert a["estimate"]["monthly"] == 4788.86 and a["estimate"]["bracket"] == "R240,000 - R260,000"
    assert a["marital"] == "in_community" and a["review"] == "no"
    assert s.qualification == "likely" and s.consent_at
    assert "completed" in replies[-1].events
    assert "tomorrow after 2pm" in replies[-1].messages[0]


def test_estimate_message_has_figure_and_mandatory_disclaimer_underneath():
    _, replies = full_chat()
    msg = replies[6].messages[0]
    assert "R4,788.86 per month over 25 months" in msg
    assert msg.index("R4,788.86") < msg.index(DISCLAIMER)
    assert "formal quote" in msg
    assert "Which of these best describes" not in msg
    assert "married" in replies[6].messages[1].lower()


@pytest.mark.parametrize("term,months,monthly", [("1", 25, 4788.86), ("2", 30, 3990.72), ("3", 36, 3325.60), ("36 months", 36, 3325.60)])
def test_all_three_terms_gauteng(term, months, monthly):
    s, _ = full_chat(term=term)
    assert s.answers["estimate"]["months"] == months and s.answers["estimate"]["monthly"] == monthly


def test_outside_gauteng_uses_the_higher_table():
    s, _ = full_chat(province="4", term="3")  # KwaZulu-Natal, 36 months
    assert s.answers["province"] == "KZN" and s.answers["estimate"]["monthly"] == 3637.98
    assert s.answers["estimate"]["gauteng"] is False


@pytest.mark.parametrize("lang,marker", [("2", "Dankie"), ("3", "Ngiyabonga")])
def test_other_languages_complete_with_a_figure(lang, marker):
    s, replies = full_chat(lang=lang)
    assert s.status == "completed" and marker in replies[-1].messages[0]
    assert "R4,788.86" in replies[6].messages[0]
    assert s.lang == ("af" if lang == "2" else "zu")


def test_after_hours_note():
    _, night = full_chat(now=NIGHT)
    _, day = full_chat(now=DAY)
    assert "Mon–Fri" in night[-1].messages[0]
    assert "Mon–Fri" not in day[-1].messages[0]


# ------------------------------------------------------------ bracket and range rules
@pytest.mark.parametrize("debt,bracket", [
    ("120000", "R120,000 - R140,000"), ("139999", "R120,000 - R140,000"), ("140000", "R140,000 - R160,000"),
    ("R499 999", "R480,000 - R500,000"), ("500000", "R480,000 - R500,000"), ("250k", "R240,000 - R260,000"),
])
def test_bracket_boundaries(debt, bracket):
    s, _ = full_chat(debt=debt)
    assert s.answers["estimate"]["bracket"] == bracket


@pytest.mark.parametrize("debt", ["100000", "110 000", "119999", "500001", "R650 000", "1.2m"])
def test_outside_estimate_range_gets_no_figure_and_no_term_question(debt):
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", debt)
    assert "estimate" not in s.answers and s.step == "marital" and s.status == "active"
    assert "outside the range" in r[-1].messages[0] and "months" not in r[-1].messages[0]
    assert "R" not in r[-1].messages[0].replace("Reply", "").split("\n\n")[0].replace("R250", "")  # no figure quoted
    assert any("consultant to work out" in n for n in s.notes)


def test_range_or_several_figures_asks_for_one_total_and_does_not_guess():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "between 200k and 250k")
    assert s.step == "debt" and "one total figure" in r[-1].messages[0] and "debt_amount" not in s.answers
    r = handle(s, "ok about 230000", NIGHT, pricebook=PB)
    assert s.step == "term"


def test_term_outside_25_to_36_is_refused_without_offering_exceptions():
    for text in ("48 months", "60", "12 months", "5 years"):
        s = Session(phone="1")
        r = run(s, "hi", "1", "yes", "craig", "3", "250000", text)
        assert s.step == "term" and "estimate" not in s.answers
        assert "25 to 36 months" in r[-1].messages[0]
        assert "exception" not in r[-1].messages[0].lower() and "ask" not in r[-1].messages[0].lower()


def test_term_26_to_35_not_offered_is_reasked():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "250000", "28")
    assert s.step == "term" and "estimate" not in s.answers and s.fails == 1


def test_estimate_is_audited_in_the_lead_record():
    from app.leads import COLUMNS, lead_row
    s, _ = full_chat()
    row = dict(zip(COLUMNS, lead_row(s)))
    assert row["Estimate shown (R/month)"] == 4788.86 and row["Term (months)"] == 25 and row["Province"] == "GP"


# ------------------------------------------------------------ under R100 000
def test_debt_under_100k_is_politely_declined_without_more_questions_or_alert():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "about 80 000")
    assert s.status == "not_fit" and r[-1].events == ["not_fit"]
    assert "R100 000" in r[-1].messages[0] and "married" not in r[-1].messages[0]
    assert "not_fit" not in notify.SUBJECTS


def test_not_fit_lead_can_correct_the_amount_and_continue_to_the_term_question():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "60k")
    assert s.status == "not_fit"
    r = handle(s, "sorry I added it up again, it's about R135 000", NIGHT, pricebook=PB)
    assert s.status == "active" and s.answers["debt_amount"] == 135000 and s.step == "term"
    assert "25 to 36 months" in r.messages[0]


def test_not_fit_lead_gets_followup_not_silence():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "60k")
    assert "send me the amount" in handle(s, "ok thanks", NIGHT, pricebook=PB).messages[0]


def test_not_fit_afrikaans():
    s = Session(phone="1")
    r = run(s, "hi", "2", "ja", "pieter", "3", "r60k")
    assert "begin ons proses" in r[-1].messages[0]


# ------------------------------------------------------------ cost questions come from the price book, never the AI
def test_cost_question_before_term_explains_what_is_needed_and_reasks():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "How much will this cost me?", llm=FakeLLM("AI says R999"))
    assert "rough monthly estimate" in r[-1].messages[0] and "999" not in r[-1].messages[0]
    assert s.step == "province"


def test_cost_question_after_estimate_restates_the_same_figure():
    s, _ = full_chat()
    r = handle(s, "What are your fees?", NIGHT, llm=FakeLLM("AI says R999"), pricebook=PB)
    assert "R4,788.86" in r.messages[0] and "999" not in r.messages[0] and DISCLAIMER in r.messages[0]


def test_cost_question_for_out_of_range_debt_never_quotes_and_flags_consultant():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "800000", "2", "2", "tomorrow")
    assert s.status == "completed"
    r = handle(s, "how much will I pay?", NIGHT, llm=FakeLLM("Your consultant confirms. [GAP]"), pricebook=PB)
    assert "R" not in r.messages[0] and any("COST" in n for n in s.notes)


def test_request_phrased_as_statement_is_treated_as_a_question():
    s, _ = full_chat()
    r = handle(s, "Please tell me more or less what I'm going to pay if my debt's 2,500 or 250,000 rand.", NIGHT, pricebook=PB)
    assert "R4,788.86" in r.messages[0] and "details are with our team" not in r.messages[0]


# ------------------------------------------------------------ consent, safety, handover
def test_ai_disclosure_and_stop_in_consent():
    s = Session(phone="1")
    r = run(s, "hi", "1")
    assert "AI" in r[-1].messages[0] and "STOP" in r[-1].messages[0] and "POPIA" in r[-1].messages[0]


def test_consent_declined_stops():
    s = Session(phone="1")
    run(s, "hi", "1", "no")
    assert s.status == "opted_out" and not s.consent_at


def test_stop_opts_out_and_silent_afterwards():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "STOP", "hello?")
    assert s.status == "opted_out" and r[3].events == ["opted_out"] and r[4].messages == []


def test_distress_escalates_with_helpline():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "honestly I want to kill myself")
    assert s.status == "distress" and "distress" in r[-1].events and "0800 567 567" in r[-1].messages[0]
    assert run(s, "ok")[0].messages == []


def test_distress_afrikaans_and_zulu():
    for phrase in ("ek wil myself doodmaak", "ngifuna ukufa"):
        s = Session(phone="1", lang="en", step="name")
        assert "distress" in handle(s, phrase, NIGHT).events


def test_ask_for_person_in_business_hours_hands_over_and_goes_silent():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "can I speak to a person", now=DAY)
    assert s.status == "handover" and r[-1].events == ["handover"]
    assert run(s, "hello", now=DAY)[0].messages == []


def test_ask_for_person_after_hours_keeps_helping_and_continues_the_flow():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "can I speak to a person")[-1]
    assert s.status == "active" and r.events == ["person_requested"] and s.step == "province"
    msg = r.messages[0]
    assert "resting until tomorrow" in msg and "call you back" in msg and "Which province" in msg
    r2 = handle(s, "4", NIGHT, pricebook=PB)  # the conversation just carries on
    assert s.answers["province"] == "KZN" and "Roughly how much" in r2.messages[0]


def test_second_request_for_a_person_after_hours_hands_over_with_return_time():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "I want a human")
    r = handle(s, "no I really want a person", NIGHT, pricebook=PB)
    assert s.status == "handover" and r.events == ["handover"] and "tomorrow" in r.messages[0]


def test_friday_night_and_saturday_say_monday_not_tomorrow():
    FRI = datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)   # Fri 22:00 SAST
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", now=FRI)
    r = handle(s, "agent please", FRI, pricebook=PB)
    assert "until Monday" in r.messages[0] and "tomorrow" not in r.messages[0]


def test_early_weekday_morning_says_08_00_this_morning():
    EARLY = datetime(2026, 11, 3, 3, 0, tzinfo=timezone.utc)  # Tue 05:00 SAST
    assert flow.next_available(EARLY, "en") == "08:00 this morning"


def test_person_requested_after_completion_asks_for_a_time_and_updates_it():
    s, _ = full_chat()
    r = handle(s, "I want to speak to a person", NIGHT, pricebook=PB)
    assert "What time would suit you?" in r.messages[0] and r.events == ["person_requested"]
    r = handle(s, "Thursday at 10am", NIGHT, pricebook=PB)
    assert s.answers["callback"] == "Thursday at 10am" and r.events == ["callback_updated"]
    assert "Thursday at 10am" in r.messages[0]


def test_person_request_in_afrikaans_after_hours():
    s = Session(phone="1")
    r = run(s, "hi", "2", "ja", "pieter", "ek wil met 'n regte mens praat")[-1]
    assert "Ons span rus tot môre" in r.messages[0]


def test_not_fit_lead_asking_for_a_person_is_not_promised_a_call():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "60k")
    r = handle(s, "I want to speak to a person", NIGHT, pricebook=PB)
    assert "call you back" not in r.messages[0] and s.status == "not_fit"


def test_three_misunderstood_answers_hand_over():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "banana", "banana", "banana")
    assert s.status == "handover" and "handover" in r[-1].events


def test_question_gets_fallback_and_reasks_without_penalty():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "what does voluntary surrender mean?", pb=None)
    assert s.step == "province" and s.fails == 0
    assert "consultant" in r[-1].messages[0] and "1." in r[-1].messages[0]


def test_unknown_language_defaults_to_english():
    s = Session(phone="1")
    run(s, "hi", "blah", "blah")
    assert s.lang == "en" and s.step == "consent"


def test_voice_note_asks_for_text():
    assert "voice" in handle(Session(phone="1"), "", NIGHT, kind="other").messages[0].lower()


def test_completed_client_writing_again_is_logged():
    s, _ = full_chat()
    r = handle(s, "please call after 5", NIGHT, pricebook=PB)
    assert "consultant will call" in r.messages[0] and any("after 5" in n for n in s.notes)


# ------------------------------------------------------------ parsing
@pytest.mark.parametrize("text,amount", [
    ("R250 000", 250000), ("250k", 250000), ("1,5m", 1500000), ("about 95000", 95000), ("1 200 000", 1200000),
    ("R110000", 110000), ("1.2 million", 1200000), ("130 duisend", 130000), ("3", None), ("I have 3 cards, 250k in all", 250000),
])
def test_amount_parsing(text, amount):
    assert parse_amount(text) == amount


@pytest.mark.parametrize("text,value", [("1", (25, False)), ("2", (30, False)), ("3", (36, False)), ("30 months", (30, False)),
                                        ("60 months", (None, True)), ("28", (None, False)), ("hello", (None, False))])
def test_term_parsing(text, value):
    assert parse_term(text) == value


@pytest.mark.parametrize("text,value", [
    ("2", "in_community"), ("married in community of property", "in_community"),
    ("out of community", "out_of_community"), ("buite gemeenskap van goedere", "out_of_community"),
    ("I'm divorced", "not_married"), ("single", "not_married"), ("angishadile", "not_married"),
    ("married but I'm not sure", "unsure"),
])
def test_marital_parsing(text, value):
    assert parse_choice("marital", text) == value


@pytest.mark.parametrize("text,value", [
    ("4", "KZN"), ("Ballito", "KZN"), ("Gauteng", "GP"), ("joburg", "GP"), ("Wes-Kaap", "WC"),
    ("Western Cape", "WC"), ("northern cape", "NC"), ("noordwes", "NW"), ("Free State", "FS"),
])
def test_province_parsing(text, value):
    assert parse_choice("province", text) == value


def test_review_not_sure_beats_not():
    assert parse_choice("review", "not sure") == "unsure"
    assert parse_choice("review", "not under debt review") == "no"


def test_name_cleaning():
    assert flow.clean_name("my name is john smith") == "John Smith"
    assert flow.clean_name("what is this?") is None


def test_alert_email_content():
    s, _ = full_chat()
    subject, body = notify.build("completed", s)
    assert "Craig" in subject and "+27820000000" in body and "tomorrow after 2pm" in body
    assert "R4,788.86/month over 25 months" in body and "Gauteng" in body


# ------------------------------------------------------------ AI-assisted behaviour (stubbed)
def test_question_containing_answer_words_is_answered_not_misparsed():
    s = Session(phone="1", step="review", lang="en", name="Craig")
    r = handle(s, "no what is the difference between debt review and debt counselling?", NIGHT, llm=FakeLLM("They are the same thing."))
    assert "same thing" in r.messages[0] and "1. Yes" in r.messages[0]
    assert s.step == "review" and "review" not in s.answers
    assert s.notes == ["Asked: no what is the difference between debt review and debt counselling?"]


def test_unanswered_question_is_logged_for_faq_growth():
    s = Session(phone="1", step="province", lang="en", name="Craig")
    handle(s, "do you work with people in Namibia?", NIGHT, llm=FakeLLM(None))
    assert s.notes[0].startswith("UNANSWERED:")


def test_short_yes_no_with_question_mark_still_counts_as_answer():
    s = Session(phone="1", step="review", lang="en", name="Craig")
    handle(s, "no?", NIGHT)
    assert s.answers["review"] == "no"


def test_partial_answer_is_logged_as_gap_and_marker_hidden():
    s = Session(phone="1", step="province", lang="en", name="Craig")
    r = handle(s, "how long does it take and what happens to my house?", NIGHT, llm=FakeLLM("Your consultant confirms. [GAP]"))
    assert "[GAP]" not in r.messages[0] and any(n.startswith("UNANSWERED:") for n in s.notes)


def test_spouse_mentioned_after_saying_not_married_is_flagged():
    s = Session(phone="1", step="province", lang="en", name="Craig", answers={"marital": "not_married"})
    handle(s, "will my wife find out", NIGHT, llm=FakeLLM(None))
    assert any("clarify" in n for n in s.notes)


def test_short_acknowledgement_after_completion_gets_canned_reply():
    s, _ = full_chat()
    assert "SHOULD NOT" not in handle(s, "ok thanks", NIGHT, llm=FakeLLM("SHOULD NOT BE USED")).messages[0]


def test_unrecognised_but_real_message_mid_flow_goes_to_ai_without_penalty():
    s = Session(phone="1", step="review", lang="en", name="Craig")
    r = handle(s, "my brother says he went through this and it was a nightmare", NIGHT, llm=FakeLLM("I'm sorry to hear that."))
    assert "sorry" in r.messages[0] and "1. Yes" in r.messages[0] and s.fails == 0


@pytest.mark.parametrize("text,lang", [
    ("Kan ek tronk toe gaan?", "af"), ("Wat is die verskil tussen skuldhersiening en skuldberading", "af"),
    ("ngingakwazi yini ukuthi ngilahlekelwe yimoto yami", "zu"), ("What is the difference between these two", "en"),
    ("ja", None), ("Craig", None), ("tomorrow after 2pm", None),
])
def test_language_detection(text, lang):
    assert flow.detect_lang(text) == lang


def test_conversation_switches_to_afrikaans_when_lead_writes_afrikaans():
    s, _ = full_chat()
    r = handle(s, "Kan ek tronk toe gaan?", NIGHT, llm=FakeLLM("Nee."), pricebook=PB)
    assert s.lang == "af" and r.messages == ["Nee."]


def test_mid_flow_language_switch_changes_next_question_too():
    s = Session(phone="1", step="review", lang="en", name="Craig")
    r = handle(s, "Wat is skuldhersiening en hoe werk dit eintlik", NIGHT, llm=FakeLLM("Antwoord."))
    assert s.lang == "af" and "skuldhersiening" in r.messages[0].lower() and "1. Ja" in r.messages[0]
