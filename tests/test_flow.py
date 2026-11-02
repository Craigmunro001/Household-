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
    replies = run(s, "hi", lang, YES[lang], "craig", province, debt, "2", "2", term, "2", "2", "tomorrow after 2pm", "1", **kw)
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
    assert "Wed 4 Nov, after 14:00" in replies[-1].messages[0]


def test_estimate_message_has_figure_and_mandatory_disclaimer_underneath():
    _, replies = full_chat()
    msg = replies[8].messages[0]
    assert "R4,788.86 per month over 25 months" in msg
    assert msg.index("R4,788.86") < msg.index(DISCLAIMER)
    assert "formal quote" in msg
    assert "Which of these best describes" not in msg
    assert "married" in replies[8].messages[1].lower()


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
    assert "R4,788.86" in replies[8].messages[0]
    assert s.lang == ("af" if lang == "2" else "zu")


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
    r = run(s, "hi", "1", "yes", "craig", "3", debt, "2", "2")
    assert "estimate" not in s.answers and s.step == "marital" and s.status == "active"
    assert "outside the range" in r[-1].messages[0] and "months" not in r[-1].messages[0]
    assert "R" not in r[-1].messages[0].replace("Reply", "").split("\n\n")[0].replace("R250", "")  # no figure quoted
    assert any("consultant to work out" in n for n in s.notes)


def test_range_or_several_figures_asks_for_one_total_and_does_not_guess():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "between 200k and 250k")
    assert s.step == "debt" and "one total figure" in r[-1].messages[0] and "debt_amount" not in s.answers
    r = handle(s, "ok about 230000", NIGHT, pricebook=PB)
    assert s.step == "home"


def test_term_outside_25_to_36_is_refused_without_offering_exceptions():
    for text in ("48 months", "60", "12 months", "5 years"):
        s = Session(phone="1")
        r = run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "2", text)
        assert s.step == "term" and "estimate" not in s.answers
        assert "25 to 36 months" in r[-1].messages[0]
        assert "exception" not in r[-1].messages[0].lower() and "ask" not in r[-1].messages[0].lower()


def test_term_26_to_35_not_offered_is_reasked():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "2", "28")
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
    assert s.status == "active" and s.answers["debt_amount"] == 135000 and s.step == "home"
    assert "own a home" in r.messages[0]


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
    run(s, "hi", "1", "yes", "craig", "3", "800000", "2", "2", "2", "2", "tomorrow at 10am", "1")
    assert s.status == "completed"
    r = handle(s, "how much will I pay?", NIGHT, llm=FakeLLM("Your consultant confirms. [GAP]"), pricebook=PB)
    assert "R" not in r.messages[0] and any("COST" in n for n in s.notes)


def test_request_phrased_as_statement_is_treated_as_a_question():
    s, _ = full_chat()
    r = handle(s, "Please tell me more or less what I'm going to pay if my debt's 2,500 or 250,000 rand.", NIGHT, pricebook=PB)
    assert "R4,788.86" in r.messages[0] and "details are with our team" not in r.messages[0]


# ------------------------------------------------------------ consent, safety, handover
def test_consent_says_virtual_assistant_without_hammering_ai_and_keeps_popia_and_stop():
    s = Session(phone="1")
    msg = run(s, "hi", "1")[-1].messages[0]
    assert "virtual assistant" in msg and "not a person" not in msg and "AI" not in msg
    assert "STOP" in msg and "POPIA" in msg


def test_bot_never_denies_being_an_ai_when_asked_directly():
    import pathlib
    faq = pathlib.Path("knowledge/faq.md").read_text()
    assert "I'm Pinnacle's virtual assistant, an AI, so not a person" in faq


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
    assert s.answers["callback"] == "Thu 5 Nov, 10:00" and r.events == ["callback_updated"]
    assert "Thu 5 Nov, 10:00" in r.messages[0]


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
    assert "Craig" in subject and "+27820000000" in body and "Call back: Wed 4 Nov, after 14:00" in body
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


# ------------------------------------------------------------ assets: warn immediately, then the lead chooses
def asset_chat(*answers, lang="1"):
    s = Session(phone="1")
    return s, run(s, "hi", lang, YES[lang], "craig", "3", "250000", *answers)


def test_asks_home_first_and_shows_no_figure_before_the_asset_questions():
    s, r = asset_chat()
    assert s.step == "home" and "own a home" in r[-1].messages[0] and "estimate" not in s.answers


@pytest.mark.parametrize("home_answer", ["1", "yes", "I own a house", "bonded", "yes it's fully paid off"])
def test_owning_a_home_triggers_the_warning_immediately_before_the_vehicle_question(home_answer):
    s, r = asset_chat(home_answer)
    assert s.status == "active" and s.step == "home_ack" and "vehicle" not in s.answers
    msg = r[-1].messages[0]
    assert "trustee" in msg and "sold, usually by auction" in msg and "pay off part of your debts" in msg
    assert "under finance" not in msg and "Would you like to continue?" in msg


def test_home_owner_who_continues_is_then_asked_about_the_vehicle():
    s, _ = asset_chat("1")
    r = handle(s, "yes", NIGHT, pricebook=PB)
    assert s.step == "vehicle" and "under finance" in r.messages[0]
    assert "home" in s.answers["asset_ack"] and any("WARNED" in n for n in s.notes)


def test_no_home_goes_straight_to_the_vehicle_question_without_a_warning():
    s, r = asset_chat("2")
    assert s.step == "vehicle" and "asset_ack" not in s.answers and "under finance" in r[-1].messages[0]


def test_financed_vehicle_gets_its_own_warning():
    s, r = asset_chat("2", "1")
    assert s.step == "vehicle_ack" and "the bank will take it back" in r[-1].messages[0]
    assert "most likely" not in r[-1].messages[0] and "auction" not in r[-1].messages[0]


def test_home_and_vehicle_each_get_their_own_separate_warning():
    s, _ = asset_chat("1", "yes", "1")
    assert s.step == "vehicle_ack"
    r = handle(s, "yes", NIGHT, pricebook=PB)
    assert s.step == "term" and set(s.answers["asset_ack"]) == {"home", "vehicle"}


def test_no_financed_vehicle_after_a_home_warning_goes_straight_to_the_term_question():
    s, _ = asset_chat("1", "yes", "2")
    assert s.step == "term" and set(s.answers["asset_ack"]) == {"home"}


@pytest.mark.parametrize("answer", ["2", "no", "No, I'd rather not"])
def test_declining_after_the_home_warning_ends_politely_and_never_asks_about_the_vehicle(answer):
    s, _ = asset_chat("1")
    r = handle(s, answer, NIGHT, pricebook=PB)
    assert s.status == "not_fit" and s.answers["not_fit_reason"] == "assets" and r.events == ["not_fit"]
    assert "CONTINUE" in r.messages[0] and "vehicle" not in s.answers and "call you" not in r.messages[0]
    assert "not_fit" not in notify.SUBJECTS


def test_lead_who_declined_the_home_warning_can_change_their_mind_and_resumes_at_the_vehicle_question():
    s, _ = asset_chat("1", "no")
    r = handle(s, "CONTINUE", NIGHT, pricebook=PB)
    assert s.status == "active" and s.step == "vehicle" and "home" in s.answers["asset_ack"]


def test_lead_who_declined_the_vehicle_warning_can_change_their_mind_and_resumes_at_the_term_question():
    s, _ = asset_chat("2", "1", "no")
    assert s.status == "not_fit" and s.answers["not_fit_asset"] == "vehicle"
    handle(s, "continue", NIGHT, pricebook=PB)
    assert s.status == "active" and s.step == "term" and "vehicle" in s.answers["asset_ack"]


def test_misread_home_question_is_corrected_by_asking_it_again():
    s, _ = asset_chat("1", "no")
    r = handle(s, "sorry I misunderstood, I actually rent", NIGHT, pricebook=PB)
    assert s.status == "active" and s.step == "home" and "home" not in s.answers and "own a home" in r.messages[0]
    handle(s, "2", NIGHT, pricebook=PB)
    r = handle(s, "no it's paid off", NIGHT, pricebook=PB)
    assert s.step == "term" and "asset_ack" not in s.answers


def test_misread_vehicle_question_is_corrected_by_asking_it_again():
    s, _ = asset_chat("2", "1", "no")
    r = handle(s, "sorry, the car is fully paid off", NIGHT, pricebook=PB)
    assert s.step == "vehicle" and "vehicle" not in s.answers and "under finance" in r.messages[0]


def test_lead_who_continues_gets_the_normal_estimate_and_is_flagged_for_the_consultant():
    s = Session(phone="27820000000")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "1", "yes", "2", "1", "2", "2", "tomorrow after 2pm", "1")  # home yes, warned, continue, no vehicle, 25m, married in community... review no
    assert s.status == "completed" and s.answers["estimate"]["monthly"] == 4788.86
    assert s.qualification == "unsure" and set(s.answers["asset_ack"]) == {"home"}
    subject, body = notify.build("completed", s)
    assert "Asset warning: home (told it would be sold by the trustee, usually at auction" in body and "Owns a home: yes" in body


def test_no_assets_means_no_warning_and_a_clean_record():
    s, _ = full_chat()
    assert "asset_ack" not in s.answers and s.qualification == "likely"


def test_asset_warning_afrikaans_and_zulu():
    s = Session(phone="1")
    r = run(s, "hi", "2", "ja", "pieter", "3", "250000", "1")
    assert "kurator" in r[-1].messages[0] and "veiling" in r[-1].messages[0]
    s = Session(phone="1")
    r = run(s, "hi", "3", "yebo", "thandi", "3", "250000", "1")
    assert "trustee" in r[-1].messages[0] and "auction" in r[-1].messages[0]


def test_under_100k_is_still_declined_before_any_asset_question():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "60k")
    assert s.answers["not_fit_reason"] == "debt" and "own a home" not in r[-1].messages[0]


def test_lead_record_shows_asset_answers_and_when_each_warning_was_accepted():
    from app.leads import COLUMNS, lead_row
    s, _ = full_chat()
    row = dict(zip(COLUMNS, lead_row(s)))
    assert row["Owns home"] == "no" and row["Vehicle"] == "none" and row["Asset warning accepted"] == ""
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "1", "yes", "1", "yes")
    row = dict(zip(COLUMNS, lead_row(s)))
    assert row["Owns home"] == "yes" and row["Vehicle"] == "financed"
    assert "home " in row["Asset warning accepted"] and "vehicle " in row["Asset warning accepted"]


# ------------------------------------------------------------ a fully paid-off vehicle: no warning, no promise
@pytest.mark.parametrize("answer", ["3", "it's fully paid off", "I have a car but it is paid up", "freehold", "no finance on it"])
def test_paid_off_vehicle_gets_no_warning_and_a_neutral_note_then_continues(answer):
    s, _ = asset_chat("2")
    r = handle(s, answer, NIGHT, pricebook=PB)
    assert s.answers["vehicle"] == "paid_off" and s.step == "term" and "asset_ack" not in s.answers
    msg = r.messages[0]
    assert "different situation" in msg and "talk you through the options" in msg and "25 to 36 months" in msg


def test_paid_off_vehicle_never_promises_a_plan_or_mentions_transferring_it():
    s, _ = asset_chat("2")
    msg = handle(s, "3", NIGHT, pricebook=PB).messages[0].lower()
    for forbidden in ("make a plan", "we can", "transfer", "wife", "spouse", "name", "guarantee", "keep your"):
        assert forbidden not in msg


def test_paid_off_vehicle_is_flagged_for_the_consultant():
    from app.leads import COLUMNS, lead_row
    s = Session(phone="27820000000")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "3", "1", "2", "2", "tomorrow after 2pm", "1")
    assert s.status == "completed" and s.answers["vehicle"] == "paid_off"
    assert any("paid-off vehicle" in n for n in s.notes)
    assert dict(zip(COLUMNS, lead_row(s)))["Vehicle"] == "paid off"
    assert "Vehicle: fully paid off" in notify.build("completed", s)[1]


def test_vehicle_menu_has_three_clear_choices():
    s, r = asset_chat("2")
    msg = r[-1].messages[0]
    assert "1. Yes, a vehicle under finance" in msg and "2. No vehicle" in msg and "3. I have a vehicle, but it's fully paid off" in msg


def test_home_owner_who_accepts_the_warning_is_always_asked_about_the_vehicle_next():
    s, _ = asset_chat("1")
    r = handle(s, "yes", NIGHT, pricebook=PB)
    assert s.step == "vehicle" and "vehicle" in r.messages[0]


def test_decline_messages_mention_only_the_situation_that_matches_the_declined_question():
    for lang, choice in (("1", "yes"), ("2", "ja"), ("3", "yebo")):
        s = Session(phone="1")
        home = run(s, "hi", lang, choice, "craig", "3", "250000", "1", "2")[-1].messages[0]
        s = Session(phone="1")
        veh = run(s, "hi", lang, choice, "craig", "3", "250000", "2", "1", "2")[-1].messages[0]
        if lang == "1":
            assert "rent your home" in home and "vehicle is fully paid off" not in home
            assert "vehicle is fully paid off" in veh and "rent your home" not in veh
        else:
            assert home != veh


def test_followup_after_a_decline_is_also_tailored():
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "1", "2")
    msg = handle(s, "ok thanks", NIGHT, pricebook=PB).messages[0]
    assert "vehicle is fully paid off" in msg and "rent your home" not in msg
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "1", "2")
    msg = handle(s, "ok thanks", NIGHT, pricebook=PB).messages[0]
    assert "rent your home" in msg and "vehicle is fully paid off" not in msg


@pytest.mark.parametrize("polite", ["ok thanks", "okay", "thank you", "alright then", "ok bye"])
def test_a_polite_acknowledgement_after_declining_does_not_restart_the_process(polite):
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "1", "2")
    handle(s, polite, NIGHT, pricebook=PB)
    assert s.status == "not_fit" and "asset_ack" not in s.answers


@pytest.mark.parametrize("again", ["CONTINUE", "yes please", "go ahead", "I've changed my mind, yes"])
def test_an_explicit_change_of_mind_after_declining_does_resume(again):
    s = Session(phone="1")
    run(s, "hi", "1", "yes", "craig", "3", "250000", "1", "2")
    handle(s, again, NIGHT, pricebook=PB)
    assert s.status == "active" and s.step == "vehicle"


# ------------------------------------------------------------ call-back time: guided, never asks the same thing twice
def at_callback(*answers, now=NIGHT, lang="1"):
    """A lead who has answered everything up to the call-time question (Tue 23:00 SAST, so tomorrow = Wed 4 Nov)."""
    s = Session(phone="1")
    run(s, "hi", lang, YES[lang], "craig", "3", "250000", "2", "2", "1", "2", "2", now=now)
    assert s.step == "callback"
    return s, [handle(s, a, now, pricebook=PB) for a in answers]


def last(r):
    return r[-1].messages[0]


def test_callback_question_offers_two_real_slots_another_day_and_let_the_consultant_choose():
    s, _ = at_callback()
    msg = flow.ask(s, "callback")
    assert "1. tomorrow (Wed 4 Nov), 08:00" in msg and "2. tomorrow (Wed 4 Nov), 10:00" in msg
    assert "3. Another day or time" in msg and "4. Let my consultant suggest a time" in msg


def test_friday_night_offers_monday_slots_not_a_saturday():
    FRI = datetime(2026, 11, 6, 20, 0, tzinfo=timezone.utc)   # Fri 22:00 SAST
    s, _ = at_callback(now=FRI)
    msg = flow.ask(s, "callback")
    assert "Mon 9 Nov" in msg and "Sat" not in msg and "tomorrow" not in msg


@pytest.mark.parametrize("pick,label", [("1", "Wed 4 Nov, 08:00"), ("2", "Wed 4 Nov, 10:00")])
def test_picking_an_offered_slot_books_it_straight_away(pick, label):
    s, r = at_callback(pick)
    assert s.status == "completed" and s.answers["callback"] == label and s.answers["callback_in_hours"] is True
    assert label in last(r) and "flagged" not in last(r)


def test_another_day_walks_through_day_then_time_with_numbered_picks():
    s, r = at_callback("3")
    assert "Which day suits you?" in last(r) and "1. Tomorrow (Wed 4 Nov)" in last(r) and "2. Thu 5 Nov" in last(r)
    assert "4. Another day" in last(r)
    r = [handle(s, "2", NIGHT, pricebook=PB)]
    assert "Thu 5 Nov, got it. What time suits you?" in last(r) and "3. 12:00" in last(r) and "6. A different time" in last(r)
    r = [handle(s, "2", NIGHT, pricebook=PB)]
    assert s.status == "completed" and s.answers["callback"] == "Thu 5 Nov, 10:00"


@pytest.mark.parametrize("bare,shown", [("10", "10:00"), ("9am", "09:00"), ("14:30", "14:30"), ("10 30", "10:30"), ("10.30", "10:30")])
def test_a_bare_time_is_repeated_back_and_only_the_day_is_asked(bare, shown):
    s, r = at_callback(bare)
    msg = last(r)
    assert s.status == "active" and f"{shown}, got it." in msg and "Which day suits you?" in msg
    assert "1. Tomorrow (Wed 4 Nov)" in msg and "make sure I get the time" not in msg


def test_a_bare_time_then_a_day_pick_books_that_time_on_that_day():
    s, _ = at_callback("10", "2")
    assert s.status == "completed" and s.answers["callback"] == "Thu 5 Nov, 10:00"


def test_a_bare_day_is_repeated_back_and_only_the_time_is_asked_then_a_typed_time_books_it():
    s, r = at_callback("tomorrow")
    assert "Tomorrow (Wed 4 Nov), got it. What time suits you?" in last(r) and "5. 16:00" in last(r)
    handle(s, "10:30", NIGHT, pricebook=PB)
    assert s.status == "completed" and s.answers["callback"] == "Wed 4 Nov, 10:30"


def test_a_freely_typed_day_and_time_is_repeated_back_for_confirmation_before_booking():
    s, r = at_callback("10:30 on the 5th")
    assert s.status == "active" and s.answers["cb_stage"] == "confirm"
    assert "Just to confirm: Thu 5 Nov, 10:30. Is that right?" in last(r)
    handle(s, "1", NIGHT, pricebook=PB)
    assert s.status == "completed" and s.answers["callback"] == "Thu 5 Nov, 10:30"


def test_saying_no_at_the_confirmation_restarts_gently_with_the_day_picks():
    s, r = at_callback("Friday at 4pm", "2")
    assert s.status == "active" and "Which day suits you?" in last(r) and s.answers.get("cb_stage") == "day"


@pytest.mark.parametrize("typed,label", [
    ("Friday at 4pm", "Fri 6 Nov, 16:00"), ("tomorrow after 2pm", "Wed 4 Nov, after 14:00"), ("08h00 tomorrow", "Wed 4 Nov, 08:00"),
    ("Monday 14:30", "Mon 9 Nov, 14:30"), ("Wednesday morning", "Wed 4 Nov, morning"), ("5 Nov 10am", "Thu 5 Nov, 10:00"),
    ("05/11 at 10:30", "Thu 5 Nov, 10:30"), ("the 5th at 10", "Thu 5 Nov, 10:00"), ("nov 6 at 2pm", "Fri 6 Nov, 14:00"),
])
def test_many_ways_of_writing_a_date_and_time_all_land_on_the_right_confirmation(typed, label):
    s, r = at_callback(typed, "1")
    assert s.status == "completed" and s.answers["callback"] == label, typed


def test_the_confusing_message_is_not_guessed_it_triggers_the_two_step_walkthrough():
    s, r = at_callback("10 and 30th of the 5th")
    msg = last(r)
    assert s.status == "active" and "two quick steps" in msg and "Which day suits you?" in msg


def test_can_we_do_a_saturday_is_understood_asks_the_time_with_a_note_then_flags_it():
    s, r = at_callback("can we do it on a Saturday?")
    msg = last(r)
    assert s.status == "active" and "Sat 7 Nov, got it. What time suits you?" in msg and "flag it for your consultant" in msg
    r = [handle(s, "2", NIGHT, pricebook=PB)]
    assert s.status == "completed" and s.answers["callback"] == "Sat 7 Nov, 10:00" and s.answers["callback_in_hours"] is False
    msg = last(r)
    assert "I've noted Sat 7 Nov, 10:00 as your preferred time" in msg and "outside our standard calling hours" in msg
    assert "will call you" not in msg and "guarantee" not in msg.lower()
    assert any("OUTSIDE standard hours" in n for n in s.notes)


def test_a_typed_weekend_time_is_confirmed_with_a_note_and_then_flagged_never_promised():
    s, r = at_callback("Saturday 10am")
    assert "Just to confirm: Sat 7 Nov, 10:00." in last(r) and "your consultant will confirm it" in last(r)
    r = [handle(s, "yes", NIGHT, pricebook=PB)]
    assert s.answers["callback_in_hours"] is False and "preferred time" in last(r) and "will call you" not in last(r)


@pytest.mark.parametrize("typed", ["Sunday evening", "Saturday morning", "tomorrow at 7pm", "tomorrow at 6am"])
def test_out_of_hours_requests_are_accepted_but_flagged_never_promised(typed):
    s, r = at_callback(typed, "1")
    assert s.status == "completed" and s.answers["callback_in_hours"] is False
    assert "outside our standard calling hours" in last(r) and "will call you" not in last(r)


def test_in_hours_request_is_not_flagged():
    s, r = at_callback("Friday at 4pm", "1")
    assert s.answers["callback_in_hours"] is True and "outside our standard" not in last(r) and "will call you" in last(r)


def test_a_time_that_has_already_passed_is_explained_and_the_day_is_asked():
    s, r = at_callback("today at 9am")
    assert "That time has already passed" in last(r) and "Which day suits you?" in last(r)


def test_consultant_suggest_a_time_option_and_phrases():
    for typed in ("4", "you choose", "whenever", "any time is fine"):
        s, r = at_callback(typed)
        assert s.status == "completed" and s.answers["callback_flexible"] is True, typed
        assert "be in touch to agree a time" in last(r)


def test_failing_to_understand_never_repeats_the_same_message_and_ends_with_the_consultant_choosing():
    s, r = at_callback("gibberish here", "more gibberish", "still nonsense")
    msgs = [x.messages[0] for x in r]
    assert len(set(msgs)) == 3                                    # three different messages, no repeats
    assert "two quick steps" in msgs[0] and "ask your consultant to suggest a time" in msgs[1]
    assert s.status == "completed" and "(consultant to confirm)" in s.answers["callback"]


def test_second_failure_offers_the_consultant_and_saying_yes_finishes_gracefully():
    s, r = at_callback("blah blah", "blah blah blah", "1")
    assert s.status == "completed" and s.answers["callback_flexible"] is True


def test_second_failure_then_no_returns_to_the_normal_options():
    s, r = at_callback("blah blah", "blah blah blah", "2")
    assert s.status == "active" and "1. tomorrow (Wed 4 Nov), 08:00" in last(r)


def test_question_mid_booking_is_answered_then_the_current_step_is_shown_again():
    s, r = at_callback("3", "is the call free?")
    assert "Which day suits you?" in last(r) and s.status == "active"
    assert any("UNANSWERED" in n or "Asked" in n for n in s.notes)


def test_typing_a_new_request_instead_of_answering_the_confirmation_just_works():
    s, r = at_callback("Friday at 4pm", "actually Monday at 9am", "1")
    assert s.status == "completed" and s.answers["callback"] == "Mon 9 Nov, 09:00"


def test_afrikaans_call_time_journey():
    s = Session(phone="1")
    run(s, "hi", "2", "ja", "pieter", "3", "250000", "2", "2", "1", "2", "2")
    assert "1. môre (Wo 4 Nov), 08:00" in flow.ask(s, "callback") and "4. Laat my konsultant 'n tyd voorstel" in flow.ask(s, "callback")
    r = handle(s, "10", NIGHT, pricebook=PB)
    assert "10:00, reg so." in r.messages[0] and "Watter dag pas jou?" in r.messages[0]
    handle(s, "2", NIGHT, pricebook=PB)
    assert s.answers["callback"] == "Do 5 Nov, 10:00"  # second pick = Thursday, in Afrikaans


def test_zulu_call_time_options_and_confirmation():
    s = Session(phone="1")
    run(s, "hi", "3", "yebo", "thandi", "3", "250000", "2", "2", "1", "2", "2")
    assert "1. kusasa (Lwesithathu 4 Nov), 08:00" in flow.ask(s, "callback")
    r = handle(s, "Lwesihlanu 4pm", NIGHT, pricebook=PB)
    assert "Ukuqinisekisa nje" in r.messages[0]


def test_lead_record_and_alert_show_the_exact_call_time_and_flag_out_of_hours():
    from app.leads import COLUMNS, lead_row
    s, _ = at_callback("Saturday morning", "1")
    assert dict(zip(COLUMNS, lead_row(s)))["Callback preference"] == "Sat 7 Nov, morning"
    s2, _ = at_callback("Friday at 4pm", "1")
    assert dict(zip(COLUMNS, lead_row(s2)))["Callback preference"] == "Fri 6 Nov, 16:00"


def test_the_callback_state_is_cleaned_up_after_booking():
    s, _ = at_callback("10", "2")
    assert not any(k in s.answers for k in flow.CB_KEYS)


# ------------------------------------------------------------ friendlier wording and the progress count
def test_questions_get_a_friendly_lead_in_with_the_leads_name():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "Craig")
    assert "Lovely to meet you, Craig!" in r[-1].messages[0] and "Which province are you in?" in r[-1].messages[0]
    r = handle(s, "3", NIGHT, pricebook=PB)
    assert "Thanks, Craig, we're on our way!" in r.messages[0] and "Roughly how much do you owe" in r.messages[0]


def test_progress_count_appears_late_in_the_flow_and_counts_down():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "2", "1", "2", "2")
    # vehicle(5 left incl. term) ... let's check the actual sequence of messages
    msgs = [m for rep in r for m in rep.messages]
    joined = "\n".join(msgs)
    assert "Only 5 questions left." in joined and "Only 4 questions left." in joined
    assert "Only 3 questions left." in joined and "Only 2 questions left." in joined
    assert "Last one, promise!" in joined and "Only 1 questions left" not in joined


def test_progress_count_is_correct_when_the_term_question_is_skipped():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "800000", "2", "2")  # out of estimate range: no term question
    assert "Only 3 questions left." in r[-1].messages[0]   # marital, review, callback


def test_reasking_does_not_repeat_the_jokes():
    s = Session(phone="1", step="province", name="Craig", lang="en")
    r = handle(s, "banana", NIGHT, pricebook=PB)
    assert "Sorry, I didn't quite catch that." in r.messages[0] and "Lovely to meet you" not in r.messages[0]


def test_friendly_wording_exists_in_all_three_languages():
    from app.content import LEADS
    for step, by_lang in LEADS.items():
        assert set(by_lang) == {"en", "af", "zu"}, step


# ------------------------------------------------------------ the recap and the CHANGE flow
def test_finishing_sends_the_booking_confirmation_then_a_plain_recap():
    s, r = full_chat()
    assert len(r[-1].messages) == 2 and r[-1].events == ["completed"]
    recap = r[-1].messages[1]
    for line in ("Here's what I've noted, Craig:", "• Province: Gauteng", "• Debt: about R250 000", "• Home: No",
                 "• Vehicle: None", "• Married: Yes, in community of property", "• Debt review: No", "• Call: Wed 4 Nov, after 14:00",
                 "reply CHANGE"):
        assert line in recap, line


def test_recap_reports_what_was_actually_said_about_assets():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "2", "180000", "1", "yes", "3", "2", "3", "2", "2")
    recap = r[-1].messages[1]
    assert s.status == "completed" and "• Home: Yes, I own a home" in recap and "• Vehicle: Fully paid off" in recap
    assert "• Province: Free State" in recap and "• Married: Yes, out of community of property" in recap


def test_recap_never_repeats_the_fee_figure():
    _, r = full_chat()
    assert "R4,788.86" not in r[-1].messages[1] and "per month" not in r[-1].messages[1]


def test_recap_when_the_consultant_is_to_suggest_the_time():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "250000", "2", "2", "1", "2", "2", "4")
    assert "• Call: Consultant to suggest a time" in r[-1].messages[1]


def test_recap_in_afrikaans_and_zulu():
    for lang, choice, marker in (("2", "ja", "Hier is wat ek genoteer het"), ("3", "yebo", "Nanku engikuqophile")):
        s, r = full_chat(lang=lang)
        assert marker in r[-1].messages[1]


def test_no_recap_for_leads_who_were_declined():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "3", "60k")
    assert all("Here's what I've noted" not in m for rep in r for m in rep.messages)


def test_change_asks_what_to_change_then_flags_it_for_the_consultant():
    s, _ = full_chat()
    r = handle(s, "CHANGE", NIGHT, pricebook=PB)
    assert "What would you like to change?" in r.messages[0] and r.events == []
    r = handle(s, "I actually own a house, I tapped the wrong button", NIGHT, pricebook=PB)
    assert r.events == ["correction_requested"] and "passed that to your consultant" in r.messages[0]
    assert any(n.startswith("CORRECTION requested by lead: I actually own a house") for n in s.notes)
    subject, body = notify.build("correction_requested", s)
    assert "correction" in subject.lower() and "I actually own a house" in body


def test_change_followed_by_a_new_call_time_just_updates_the_time():
    s, _ = full_chat()
    handle(s, "I need to change the time", NIGHT, pricebook=PB)
    r = handle(s, "Friday at 3pm", NIGHT, pricebook=PB)
    assert r.events == ["callback_updated"] and s.answers["callback"] == "Fri 6 Nov, 15:00" and "Fri 6 Nov, 15:00" in r.messages[0]


@pytest.mark.parametrize("word", ["verander", "this is wrong", "there's a mistake", "shintsha"])
def test_change_is_recognised_in_all_three_languages_and_common_phrasings(word):
    s, _ = full_chat()
    assert s.answers.get("awaiting_correction") is None
    handle(s, word, NIGHT, pricebook=PB)
    assert s.answers.get("awaiting_correction") is True


# ------------------------------------------------------------ "is this a scam?": fixed approved answer, no names
TRUST_QUESTIONS = ["is this a scam?", "Are you guys legit", "this sounds like a scam to me", "can I trust you with my information",
                   "who are you people", "Oh, you guys fucking around. Is this a scam?", "is it fraud?"]


@pytest.mark.parametrize("q", TRUST_QUESTIONS)
def test_trust_questions_get_the_fixed_answer_even_if_the_ai_says_something_else(q):
    s = Session(phone="1", step="province", lang="en", name="Craig")
    r = handle(s, q, NIGHT, llm=FakeLLM("AI improvises: we are NCR approved and registered!"), pricebook=PB)
    msg = r.messages[0]
    assert "since 2016" in msg and "East Coast Radio" in msg and "3 years" in msg and "Hot FM" in msg and "2 years" in msg
    assert "Vuma FM in KwaZulu-Natal for over a year" in msg
    assert "never ask for your banking details" in msg and "company documents" in msg and "type AGENT" in msg
    assert "improvises" not in msg and "Which province" in msg   # and the question carries on
    assert s.fails == 0 and s.step == "province"


def test_the_trust_answer_never_names_an_attorney_claims_a_registration_or_implies_approval():
    msg = flow.trust_text("en").lower()
    for forbidden in ("attorney", "david", "schoonraad", "law society", "legal practice", "registered with", "approved", "accredited",
                      "ncr", "guarantee", "endorse"):
        assert forbidden not in msg, forbidden


def test_the_trust_answer_works_in_every_language_and_at_every_stage():
    for lang, marker in (("en", "since 2016"), ("af", "sedert 2016"), ("zu", "kusukela ngo-2016")):
        assert marker in flow.trust_text(lang)
    s, _ = full_chat()                                    # after completing
    assert "since 2016" in handle(s, "is this legit?", NIGHT, pricebook=PB).messages[0]
    s2, _ = at_callback("is this a scam?")                # in the middle of booking a call
    assert "since 2016" in last(_) and s2.step == "callback"
    s3 = Session(phone="1")                               # after being declined
    run(s3, "hi", "1", "yes", "craig", "3", "60k")
    assert "since 2016" in handle(s3, "is this a scam?", NIGHT, pricebook=PB).messages[0]


def test_a_trust_statement_without_a_question_mark_still_gets_the_answer():
    s = Session(phone="1", step="debt", lang="en", name="Craig")
    assert "since 2016" in handle(s, "I think you are scammers", NIGHT, pricebook=PB).messages[0]


def test_the_ck_number_is_only_added_when_craig_supplies_it(monkeypatch):
    assert "registration number" not in flow.trust_text("en")
    monkeypatch.setattr(flow, "COMPANY_REG_NUMBER", "CK2016/123456/23")
    assert "Our registration number is CK2016/123456/23." in flow.trust_text("en")


@pytest.mark.parametrize("q", ["am I speaking to a real person?", "Are you a bot?", "is this AI", "are you human", "is this automated?"])
def test_asking_what_it_is_gets_an_honest_fixed_answer_and_is_not_treated_as_a_handover(q):
    s = Session(phone="1", step="province", lang="en", name="Craig")
    r = handle(s, q, NIGHT, llm=FakeLLM("I am totally human!"), pricebook=PB)
    msg = r.messages[0]
    assert "an AI, so not a person" in msg and "type AGENT" in msg and "totally human" not in msg and "since 2016" not in msg
    assert s.status == "active" and r.events == [] and "Which province" in msg


@pytest.mark.parametrize("q", ["I want to speak to a real person", "can I talk to a human please"])
def test_asking_to_SPEAK_to_a_person_is_still_a_handover_request(q):
    s = Session(phone="1", step="province", lang="en", name="Craig")
    assert handle(s, q, DAY, pricebook=PB).events == ["handover"]


def test_the_ai_only_ever_sees_clean_approved_answers_no_names_notes_or_tags():
    import pathlib
    from app.llm import faq_for_prompt
    prompt = faq_for_prompt(pathlib.Path("knowledge/faq.md").read_text())
    assert "## Q: Is this a scam?" in prompt and "since 2016" in prompt
    for leak in ("David", "Schoonraad", "Craig", "DRAFT", "VERIFY", "CONFLICT", "NOT YET COVERED", "HOW THIS FILE WORKS", "[From", "Claude"):
        assert leak not in prompt, leak


def test_no_client_facing_text_contains_an_attorney_name():
    import pathlib
    from app import content
    blob = repr(content.M) + pathlib.Path("knowledge/faq.md").read_text().split("## Q:", 1)[1]
    assert "Schoonraad" not in blob


def test_all_three_radio_stations_appear_in_every_language_and_in_the_ai_knowledge():
    import pathlib
    from app.llm import faq_for_prompt
    for lang in ("en", "af", "zu"):
        msg = flow.trust_text(lang)
        assert "East Coast Radio" in msg and "Vuma FM" in msg and "Hot FM" in msg, lang
    prompt = faq_for_prompt(pathlib.Path("knowledge/faq.md").read_text())
    assert prompt.count("Vuma FM") == 2   # the scam answer and the "where have I heard of you" answer


def test_the_radio_history_is_worded_as_advertising_in_every_language():
    en = flow.trust_text("en")
    assert "We've advertised on East Coast Radio" in en and "were on" not in en and "endorse" not in en
    assert "geadverteer" in flow.trust_text("af") and "sakhangisa" in flow.trust_text("zu")
    import pathlib
    from app.llm import faq_for_prompt
    prompt = faq_for_prompt(pathlib.Path("knowledge/faq.md").read_text())
    assert "advertised on East Coast Radio" in prompt and "we were on East Coast" not in prompt
