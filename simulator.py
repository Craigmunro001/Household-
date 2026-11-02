"""Chat with the bot in your terminal, no WhatsApp needed.

    python simulator.py            # uses Claude if ANTHROPIC_API_KEY is set
    python simulator.py --no-llm   # fully deterministic
Type /quit to leave. Lead record is printed at the end.
"""
import argparse
import json
from datetime import datetime, timezone

from app import flow, leads
from app.pricing import load_pricebook
from app.config import get_settings
from app.llm import make_llm

ap = argparse.ArgumentParser()
ap.add_argument("--no-llm", action="store_true")
args = ap.parse_args()

settings = get_settings()
llm = None if args.no_llm else make_llm(settings)
pricebook = load_pricebook()
s = flow.Session(phone="27000000000")
print(f"[simulator] LLM {'ON (' + settings.model + ')' if llm else 'OFF'}. Say hi to start.\n")
while True:
    try:
        text = input("you > ")
    except EOFError:
        break
    if text.strip() == "/quit":
        break
    reply = flow.handle(s, text, datetime.now(timezone.utc), llm, pricebook)
    for m in reply.messages:
        print(f"\nbot > {m}\n")
    for e in reply.events:
        print(f"[event: {e}]")
print(json.dumps(dict(zip(leads.COLUMNS, leads.lead_row(s))), indent=2, ensure_ascii=False))
