from datetime import datetime, timezone

import pytest

from app import flow, notify
from app.flow import Session, handle, parse_amount, parse_choice

NIGHT = datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc)   # Tue 23:00 SAST
DAY = datetime(2026, 11, 3, 8, 0, tzinfo=timezone.utc)      # Tue 10:00 SAST
FEES = {"150000-200000": {"min": 15000, "max": 20000}}


def run(session, *texts, now=NIGHT, fees=None, llm=None):
    replies = []
    for t in texts:
        replies.append(handle(session, t, now, llm=llm, fees=fees))
    return replies


def full_chat(lang_choice, **kw):
    s = Session(phone="27820000000")
    replies = run(s, "hi", lang_choice, "yes" if lang_choice == "1" else ("ja" if lang_choice == "2" else "yebo"),
                  "craig", "4", "2", "4", "2", "tomorrow after 2pm", **kw)
    return s, replies


def test_happy_path_english():
    s, replies = full_chat("1")
    assert s.status == "completed" and s.lang == "en"
    assert s.name == "Craig"
    assert s.answers["debt_band"] == "150000-200000"
    assert s.answers["marital"] == "in_community"
    assert s.answers["province"] == "KZN"
    assert s.answers["review"] == "no"
    assert s.qualification == "likely"
    assert s.consent_at
    assert "completed" in replies[-1].events
    assert "tomorrow after 2pm" in replies[-1].messages[0]


@pytest.mark.parametrize("choice,marker", [("2", "Dankie"), ("3", "Ngiyabonga")])
def test_other_languages(choice, marker):
    s, replies = full_chat(choice)
    assert s.status == "completed"
    assert marker in replies[-1].messages[0]
    assert s.lang == ("af" if choice == "2" else "zu")


def test_no_fee_quoted_when_not_configured():
    _, replies = full_chat("1", fees={})
    assert "R" not in replies[-1].messages[0]


def test_fee_quoted_only_from_config_and_marked_as_estimate():
    _, replies = full_chat("1", fees=FEES)
    msg = replies[-1].messages[0]
    assert "R15 000" in msg and "R20 000" in msg and "estimate" in msg


def test_after_hours_note():
    _, night = full_chat("1", now=NIGHT)
    _, day = full_chat("1", now=DAY)
    assert "Mon–Fri" in night[-1].messages[0]
    assert "Mon–Fri" not in day[-1].messages[0]


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
    assert s.status == "opted_out"
    assert r[3].events == ["opted_out"]
    assert r[4].messages == []


def test_distress_escalates_with_helpline():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "honestly I want to kill myself")
    assert s.status == "distress"
    assert "distress" in r[-1].events
    assert "0800 567 567" in r[-1].messages[0]
    assert run(s, "ok")[0].messages == []  # bot stays quiet; a human takes over


def test_distress_afrikaans_and_zulu():
    for phrase in ("ek wil myself doodmaak", "ngifuna ukufa"):
        s = Session(phone="1", lang="en", step="name")
        assert "distress" in handle(s, phrase, NIGHT).events


def test_ask_for_person_hands_over():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "can I speak to a person")
    assert s.status == "handover" and r[-1].events == ["handover"]
    assert run(s, "hello")[0].messages == []


def test_three_misunderstood_answers_hand_over():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "banana", "banana", "banana")
    assert s.status == "handover" and "handover" in r[-1].events


def test_question_gets_fallback_and_reasks_without_penalty():
    s = Session(phone="1")
    r = run(s, "hi", "1", "yes", "craig", "what does this cost?")
    assert s.step == "debt" and s.fails == 0
    assert "consultant" in r[-1].messages[0] and "1." in r[-1].messages[0]


def test_unknown_language_defaults_to_english():
    s = Session(phone="1")
    run(s, "hi", "blah", "blah")
    assert s.lang == "en" and s.step == "consent"


def test_voice_note_asks_for_text():
    s = Session(phone="1")
    r = handle(s, "", NIGHT, kind="other")
    assert "voice" in r.messages[0].lower()


def test_completed_client_writing_again_is_logged():
    s, _ = full_chat("1")
    r = handle(s, "please call after 5", NIGHT)
    assert "consultant will call" in r.messages[0]
    assert any("after 5" in n for n in s.notes)


@pytest.mark.parametrize("text,band", [
    ("R250 000", "200000-300000"), ("250k", "200000-300000"), ("1,5m", "500000+"),
    ("about 95000", "0-100000"), ("1 200 000", "500000+"), ("R110000", "100000-120000"),
    ("1.2 million", "500000+"), ("130 duisend", "120000-150000"),
])
def test_debt_amounts_map_to_bands(text, band):
    assert parse_choice("debt", text) == band


def test_small_bare_numbers_are_menu_choices_not_amounts():
    assert parse_amount("3") is None
    assert parse_choice("debt", "3") == "120000-150000"


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
    s, _ = full_chat("1")
    subject, body = notify.build("completed", s)
    assert "Craig" in subject and "+27820000000" in body and "tomorrow after 2pm" in body
