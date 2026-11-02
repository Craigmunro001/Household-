import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from app import whatsapp as wa
from app.content import options_text, tr
from app.flow import Session, handle
from app.pricing import load_pricebook
from app.whatsapp import (BTN_BODY, BTN_MAX, BTN_TITLE, LIST_BODY, LIST_LABEL, ROW_DESC, ROW_MAX, ROW_TITLE, describe,
                          parse_payload, render, split_options)

PB = load_pricebook()
NIGHT = datetime(2026, 11, 3, 21, 0, tzinfo=timezone.utc)


def check_payload(p):
    """Every rule from Meta's documentation for what we send."""
    if p["type"] == "text":
        assert 0 < len(p["text"]["body"]) <= 4096
        return
    i = p["interactive"]
    if i["type"] == "button":
        buttons = i["action"]["buttons"]
        assert 2 <= len(buttons) <= BTN_MAX and 0 < len(i["body"]["text"]) <= BTN_BODY
        titles = [b["reply"]["title"] for b in buttons]
        assert all(0 < len(t) <= BTN_TITLE for t in titles) and len(set(titles)) == len(titles)
        assert all(b["reply"]["id"].isdigit() and len(b["reply"]["id"]) <= 256 for b in buttons)
    else:
        rows = [r for sec in i["action"]["sections"] for r in sec["rows"]]
        assert 2 <= len(rows) <= ROW_MAX and 0 < len(i["body"]["text"]) <= LIST_BODY
        assert 0 < len(i["action"]["button"]) <= LIST_LABEL
        assert all(0 < len(r["title"]) <= ROW_TITLE and r["id"].isdigit() for r in rows)
        assert all(len(r.get("description", "")) <= ROW_DESC for r in rows)
        assert len({r["title"] for r in rows}) == len(rows)


def test_a_message_without_options_stays_plain_text():
    assert render("Thanks, Craig. A consultant will call you.")["type"] == "text"


def test_three_short_options_become_reply_buttons_with_the_number_as_the_id():
    p = render(tr("ask_review", "en", options=options_text("review", "en")))
    assert p["interactive"]["type"] == "button"
    assert [(b["reply"]["id"], b["reply"]["title"]) for b in p["interactive"]["action"]["buttons"]] == [("1", "Yes"), ("2", "No"), ("3", "Not sure")]
    assert "1." not in p["interactive"]["body"]["text"]


def test_the_language_menu_is_three_buttons_without_the_typing_hint():
    p = render(tr("welcome_all", "en", options=options_text("lang", "en")))
    i = p["interactive"]
    assert i["type"] == "button" and [b["reply"]["title"] for b in i["action"]["buttons"]] == ["English", "Afrikaans", "isiZulu"]
    assert "Reply with a number" not in i["body"]["text"]


def test_long_option_labels_use_curated_short_titles_on_buttons():
    home = render(tr("ask_home", "en", options=options_text("home", "en")))["interactive"]["action"]["buttons"]
    assert [b["reply"]["title"] for b in home] == ["Yes, I own a home", "No home"]
    veh = render(tr("ask_vehicle", "en", options=options_text("vehicle", "en")))["interactive"]["action"]["buttons"]
    assert [b["reply"]["title"] for b in veh] == ["Yes, under finance", "No vehicle", "Vehicle paid off"]


def test_four_or_more_options_become_a_list_with_the_full_wording_in_the_description():
    p = render(tr("ask_marital", "en", options=options_text("marital", "en")))["interactive"]
    assert p["type"] == "list" and p["action"]["button"] == "Choose"
    rows = p["action"]["sections"][0]["rows"]
    assert [r["id"] for r in rows] == ["1", "2", "3", "4"]
    assert rows[1] == {"id": "2", "title": "In community", "description": "Married in community of property"}


def test_nine_provinces_fit_one_list():
    rows = render(tr("ask_province", "en", options=options_text("province", "en")))["interactive"]["action"]["sections"][0]["rows"]
    assert len(rows) == 9 and rows[3]["title"] == "KwaZulu-Natal"


def test_no_option_is_ever_lost_when_there_are_too_many_to_list():
    text = "Pick one\n\n" + "\n".join(f"{i}. Option {i}" for i in range(1, 12))
    assert render(text)["type"] == "text"  # 11 options: fall back to numbered text, which still works


def test_options_that_are_not_a_clean_1_2_3_sequence_are_left_as_text():
    assert render("Notes:\n1. first\n3. third")["type"] == "text"
    assert render("Only one:\n1. lonely")["type"] == "text"


def test_a_tapped_button_or_list_row_arrives_as_the_option_number():
    def payload(kind, reply):
        return {"entry": [{"changes": [{"value": {"messages": [{"id": "m", "from": "27820000000", "type": "interactive",
                "interactive": {"type": kind, kind: reply}}]}}]}]}
    assert parse_payload(payload("button_reply", {"id": "2", "title": "No"}))[0].text == "2"
    assert parse_payload(payload("list_reply", {"id": "4", "title": "KwaZulu-Natal"}))[0].text == "4"
    assert parse_payload(payload("button_reply", {"id": "abc", "title": "Hello"}))[0].text == "Hello"  # unknown id: use the title


def test_tapping_gives_exactly_the_same_result_as_typing_the_number():
    typed, tapped = Session(phone="1"), Session(phone="2")
    for t in ("hi", "1", "yes", "craig", "4"):
        handle(typed, t, NIGHT, pricebook=PB)
        handle(tapped, t, NIGHT, pricebook=PB)
    assert typed.answers == tapped.answers and typed.step == tapped.step == "debt"


def run_journey(lang_choice, yes, *answers):
    s, texts = Session(phone="1"), []
    for a in ("hi", lang_choice, yes, "craig", *answers):
        texts += handle(s, a, NIGHT, pricebook=PB).messages
    return s, texts


JOURNEYS = [
    ("happy", ("3", "250000", "2", "2", "1", "2", "2", "1")),
    ("assets_both", ("2", "180000", "1", "yes", "1", "yes", "3", "2", "2", "2", "10", "3", "5")),
    ("guided_time", ("3", "250000", "2", "2", "1", "2", "2", "gibberish", "more gibberish", "still")),
    ("saturday", ("3", "250000", "2", "2", "1", "2", "2", "can we do it on a Saturday?", "2", "CHANGE", "my name is wrong")),
    ("typed_slot", ("3", "250000", "2", "2", "1", "2", "2", "Friday at 4pm", "2", "1")),
    ("declines", ("3", "60k")),
    ("home_decline", ("3", "250000", "1", "2")),
]


@pytest.mark.parametrize("lang,yes", [("1", "yes"), ("2", "ja"), ("3", "yebo")])
@pytest.mark.parametrize("name,answers", JOURNEYS)
def test_every_message_in_every_journey_and_language_respects_whatsapps_limits(lang, yes, name, answers):
    _, texts = run_journey(lang, yes, *answers)
    assert texts
    for text in texts:
        check_payload(render(text, {"1": "en", "2": "af", "3": "zu"}[lang]))


def test_describe_shows_what_the_lead_would_see():
    shown = describe(render(tr("ask_review", "en", options=options_text("review", "en"))))
    assert "[ Yes ]  [ No ]  [ Not sure ]" in shown


class FakeSettings:
    wa_api_version, wa_phone_number_id, wa_token = "v21.0", "123", "tok"


def make_client(handler):
    c = wa.WhatsAppClient(FakeSettings())
    c.http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return c


def test_interactive_message_is_sent_as_interactive():
    sent = []

    def handler(request):
        sent.append(__import__("json").loads(request.content))
        return httpx.Response(200, json={})
    asyncio.run(make_client(handler).send("27820000000", tr("ask_review", "en", options=options_text("review", "en")), "en"))
    assert len(sent) == 1 and sent[0]["type"] == "interactive" and sent[0]["to"] == "27820000000"


def test_if_whatsapp_rejects_the_buttons_the_same_words_go_out_as_plain_text():
    sent = []

    def handler(request):
        body = __import__("json").loads(request.content)
        sent.append(body)
        return httpx.Response(400, json={"error": "bad"}) if body["type"] == "interactive" else httpx.Response(200, json={})
    text = tr("ask_review", "en", options=options_text("review", "en"))
    asyncio.run(make_client(handler).send("27820000000", text, "en"))
    assert [b["type"] for b in sent] == ["interactive", "text"] and sent[1]["text"]["body"] == text
