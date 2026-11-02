"""One-turn-at-a-time test harness (used for live role-play tests, no WhatsApp needed).

    python chat.py "client message"                  # engine only
    python chat.py --faq "answer text" "client msg"  # supply the AI's FAQ answer for this turn
    python chat.py --reset
State is kept in a JSON file between turns.
"""
import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone

from app import flow
from app.pricing import load_pricebook

STATE = os.environ.get("CHAT_STATE", "data/chat_state.json")
ap = argparse.ArgumentParser()
ap.add_argument("text", nargs="?")
ap.add_argument("--faq")
ap.add_argument("--reset", action="store_true")
ap.add_argument("--show", action="store_true")
ap.add_argument("--at", help="pretend it is this SAST time, e.g. 2026-11-02T21:00")
args = ap.parse_args()

os.makedirs(os.path.dirname(STATE), exist_ok=True)
if args.reset and os.path.exists(STATE):
    os.remove(STATE)
s = flow.Session(**json.load(open(STATE))) if os.path.exists(STATE) else flow.Session(phone="27000000000")


class Stub:
    def faq(self, q, lang):
        return args.faq

    def classify(self, *a, **k):
        return None

    def normalise_callback(self, *a, **k):
        return None


pricebook = load_pricebook()
if args.text is not None:
    now = datetime.fromisoformat(args.at).replace(tzinfo=flow.SAST) if args.at else datetime.now(timezone.utc)
    reply = flow.handle(s, args.text, now, Stub(), pricebook)
    for m in reply.messages:
        print(m + "\n")
    if reply.events:
        print(f"[events: {reply.events}]")
    json.dump(asdict(s), open(STATE, "w"))
if args.show or args.text is None:
    print(json.dumps(asdict(s), indent=2, ensure_ascii=False))
