import hashlib
import hmac
import logging
from dataclasses import dataclass

import httpx

log = logging.getLogger("pinnacle.whatsapp")


@dataclass
class Incoming:
    msg_id: str
    phone: str
    kind: str  # text | other
    text: str
    profile_name: str = ""


def verify_signature(app_secret, body: bytes, header: str) -> bool:
    if not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(app_secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header.removeprefix("sha256="))


def parse_payload(payload: dict) -> list:
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            names = {c.get("wa_id"): c.get("profile", {}).get("name", "") for c in value.get("contacts", [])}
            for m in value.get("messages", []):
                kind, text = "other", ""
                if m.get("type") == "text":
                    kind, text = "text", m["text"]["body"]
                elif m.get("type") == "interactive":
                    r = m["interactive"].get("button_reply") or m["interactive"].get("list_reply") or {}
                    kind, text = "text", r.get("title", "")
                elif m.get("type") == "button":
                    kind, text = "text", m["button"].get("text", "")
                out.append(Incoming(m["id"], m["from"], kind, text, names.get(m["from"], "")))
    return out


class WhatsAppClient:
    def __init__(self, settings):
        self.url = f"https://graph.facebook.com/{settings.wa_api_version}/{settings.wa_phone_number_id}/messages"
        self.headers = {"Authorization": f"Bearer {settings.wa_token}"}
        self.http = httpx.AsyncClient(timeout=15)

    async def send_text(self, to, body):
        r = await self.http.post(self.url, headers=self.headers, json={
            "messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": body, "preview_url": False},
        })
        if r.status_code >= 400:
            log.error("send failed %s %s", r.status_code, r.text)

    async def mark_read(self, msg_id):
        await self.http.post(self.url, headers=self.headers, json={
            "messaging_product": "whatsapp", "status": "read", "message_id": msg_id,
        })
