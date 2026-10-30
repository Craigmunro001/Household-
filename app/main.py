import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

import yaml
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response

from . import flow, leads, notify
from .config import get_settings
from .llm import make_llm
from .store import SessionStore
from .whatsapp import WhatsAppClient, parse_payload, verify_signature

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("pinnacle")

settings = get_settings()
app = FastAPI(title="Pinnacle WhatsApp assistant")
store = SessionStore(settings.db_path)
sink = leads.make_sink(settings)
llm = make_llm(settings)
wa = WhatsAppClient(settings)
locks = defaultdict(asyncio.Lock)  # one conversation processed at a time


def load_fees():
    try:
        with open("config/fees.yaml") as f:
            raw = yaml.safe_load(f) or {}
        return {k: v for k, v in raw.items() if v}
    except FileNotFoundError:
        return {}


@app.get("/health")
def health():
    return {"ok": True, "llm": bool(llm), "sheet": type(sink).__name__}


@app.get("/webhook")
def verify(request: Request):
    q = request.query_params
    if q.get("hub.mode") == "subscribe" and q.get("hub.verify_token") == settings.wa_verify_token:
        return Response(q.get("hub.challenge", ""), media_type="text/plain")
    raise HTTPException(403)


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    body = await request.body()
    if not settings.dev_mode:
        if not settings.wa_app_secret or not verify_signature(
            settings.wa_app_secret, body, request.headers.get("x-hub-signature-256", "")
        ):
            raise HTTPException(403, "bad signature")
    for msg in parse_payload(await request.json()):
        background.add_task(process, msg)
    return {"ok": True}  # always 200 fast so Meta doesn't retry


async def process(msg):
    async with locks[msg.phone]:
        try:
            if not store.first_time_seen(msg.msg_id):
                return
            await wa.mark_read(msg.msg_id)
            s = store.load(msg.phone)
            reply = await asyncio.to_thread(
                flow.handle, s, msg.text, datetime.now(timezone.utc), llm, load_fees(), msg.kind
            )
            store.save(s)
            for i, text in enumerate(reply.messages):
                if i:
                    await asyncio.sleep(settings.human_delay)
                await wa.send_text(msg.phone, text)
            if s.consent_at or reply.events:
                await asyncio.to_thread(sink.upsert, s)
            for event in reply.events:
                await asyncio.to_thread(notify.send, settings, event, s)
        except Exception:
            log.exception("failed processing message from %s", msg.phone)
