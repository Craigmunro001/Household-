import hashlib
import hmac
import logging
import re
from dataclasses import dataclass

import httpx

from .content import OPTIONS

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
                    rid = str(r.get("id", ""))
                    kind, text = "text", rid if rid.isdigit() else r.get("title", "")  # the id is the option number
                elif m.get("type") == "button":
                    kind, text = "text", m["button"].get("text", "")
                out.append(Incoming(m["id"], m["from"], kind, text, names.get(m["from"], "")))
    return out


# Meta's documented limits (developers.facebook.com, WhatsApp Cloud API interactive messages)
BTN_MAX, BTN_TITLE, BTN_BODY = 3, 20, 1024
ROW_MAX, ROW_TITLE, ROW_DESC, LIST_BODY, LIST_LABEL = 10, 24, 72, 4096, 20
CHOOSE = {"en": "Choose", "af": "Kies", "zu": "Khetha"}

# Short titles for option labels that are too long (or too ambiguous once cut) for a button.
_SHORTS = {
    "home": {"no": ("No home", "Geen huis", "Anginayo indlu")},
    "vehicle": {"yes": ("Yes, under finance", "Ja, gefinansier", "Yebo, sakhokhelwa"),
                "no": ("No vehicle", "Geen voertuig", "Asikho isithuthi"),
                "paid_off": ("Vehicle paid off", "Voertuig afbetaal", "Sikhokhiwe sonke")},
    "asset_ack": {"yes": ("Yes, continue", "Ja, gaan voort", "Yebo, qhubeka"),
                  "no": ("No, rather not", "Nee, liewer nie", "Cha, angithandi")},
    "marital": {"not_married": ("Not married", "Nie getroud", "Angishadile"),
                "in_community": ("In community", "Binne gemeenskap", "Ngokuhlanganyela"),
                "out_of_community": ("Out of community", "Buite gemeenskap", "Ngaphandle"),
                "unsure": ("Married, not sure", "Getroud, nie seker", "Ngishadile, angazi")},
}
SHORT = {
    "Yes, let's go!": "Yes, let's go!", "Ja, kom ons gaan!": "Ja, kom ons gaan!", "Yebo, masiqale!": "Yebo, masiqale!",
    "Let my consultant suggest a time": "Consultant picks", "Laat my konsultant 'n tyd voorstel": "Konsultant kies",
    "Mayibe umeluleki wami aphakamise isikhathi": "Umeluleki akhethe",
    "No, let me try again": "No, try again", "Nee, laat ek weer probeer": "Nee, probeer weer", "Cha, ake ngizame futhi": "Cha, zama futhi",
}
for _step, _values in _SHORTS.items():
    for _value, _labels, _kw in OPTIONS[_step]:
        if _value in _values:
            for _i, _lang in enumerate(("en", "af", "zu")):
                SHORT[_labels[_lang]] = _values[_value][_i]

_OPTION_LINE = re.compile(r"^(\d{1,2})\.\s+(.+)$")
_DROP_HINT = re.compile(r"^\(Reply with a number")  # only makes sense when typing


def _cap(text):
    return text if text.startswith("isiZulu") else text[:1].upper() + text[1:]


def short(label, limit):
    """A title that fits -> (title, was_cut). Prefers the curated short title, then drops brackets, then cuts."""
    t = SHORT.get(label, label)
    if len(t) <= limit:
        return _cap(t), False
    t2 = re.sub(r"\s*\([^)]*\)", "", t).strip(" ,")
    if t2 and len(t2) <= limit:
        return _cap(t2), False
    return _cap(t2[: limit - 1].rstrip() + "…"), True


def split_options(text):
    """-> (body, [(id, label), ...]) when the message ends in a numbered list 1., 2., 3. ..., else (text, [])."""
    lines = text.split("\n")
    idx = [i for i, ln in enumerate(lines) if _OPTION_LINE.match(ln)]
    if len(idx) < 2 or idx != list(range(idx[0], idx[-1] + 1)):
        return text, []
    opts = [_OPTION_LINE.match(ln).groups() for ln in lines[idx[0]: idx[-1] + 1]]
    if [o[0] for o in opts] != [str(i) for i in range(1, len(opts) + 1)]:
        return text, []
    pre = "\n".join(lines[: idx[0]]).strip()
    post = "\n".join(ln for ln in lines[idx[-1] + 1:] if not _DROP_HINT.match(ln)).strip()
    body = "\n\n".join(p for p in (pre, post) if p)
    return (body, opts) if body else (text, [])


def render(text, lang="en"):
    """Turn a bot message into a WhatsApp payload body: reply buttons (2-3 short options), a list (up to 10),
    or plain text. The option NUMBER is the id, so a tap comes back as the same "2" the bot understands typed."""
    body, opts = split_options(text)
    plain = {"type": "text", "text": {"body": text, "preview_url": False}}
    if not opts:
        return plain
    cut = [short(label, BTN_TITLE) for _, label in opts]
    titles = [t for t, _ in cut]
    if 2 <= len(opts) <= BTN_MAX and not any(c for _, c in cut) and len(set(titles)) == len(titles) and len(body) <= BTN_BODY:
        return {"type": "interactive", "interactive": {
            "type": "button", "body": {"text": body},
            "action": {"buttons": [{"type": "reply", "reply": {"id": oid, "title": t}} for (oid, _), t in zip(opts, titles)]}}}
    if len(opts) <= ROW_MAX and len(body) <= LIST_BODY:
        rows, seen = [], set()
        for oid, label in opts:
            title, _ = short(label, ROW_TITLE)
            if title in seen:
                title = short(f"{oid}. {title}", ROW_TITLE)[0]
            seen.add(title)
            row = {"id": oid, "title": title}
            if label != title:
                row["description"] = label[:ROW_DESC]
            rows.append(row)
        return {"type": "interactive", "interactive": {
            "type": "list", "body": {"text": body},
            "action": {"button": CHOOSE[lang][:LIST_LABEL], "sections": [{"title": "·", "rows": rows}]}}}
    return plain


def describe(payload):
    """A human-readable picture of what the lead will see (used by the test tools)."""
    if payload["type"] == "text":
        return payload["text"]["body"]
    i = payload["interactive"]
    if i["type"] == "button":
        return i["body"]["text"] + "\n" + "  ".join(f"[ {b['reply']['title']} ]" for b in i["action"]["buttons"])
    rows = i["action"]["sections"][0]["rows"]
    lines = [f"  ○ {r['title']}" + (f"  — {r['description']}" if r.get("description") else "") for r in rows]
    return i["body"]["text"] + f"\n[ {i['action']['button']} ▾ ]\n" + "\n".join(lines)


class WhatsAppClient:
    def __init__(self, settings):
        self.url = f"https://graph.facebook.com/{settings.wa_api_version}/{settings.wa_phone_number_id}/messages"
        self.headers = {"Authorization": f"Bearer {settings.wa_token}"}
        self.http = httpx.AsyncClient(timeout=15)

    async def _post(self, payload):
        r = await self.http.post(self.url, headers=self.headers, json={"messaging_product": "whatsapp", **payload})
        if r.status_code >= 400:
            log.error("send failed %s %s", r.status_code, r.text)
        return r

    async def send_text(self, to, body):
        return await self._post({"to": to, "type": "text", "text": {"body": body, "preview_url": False}})

    async def send(self, to, text, lang="en"):
        """Buttons/lists where they fit; if WhatsApp rejects the interactive message, send the same words as text."""
        payload = render(text, lang)
        r = await self._post({"to": to, **payload})
        if r.status_code >= 400 and payload["type"] == "interactive":
            log.warning("interactive message rejected, falling back to text")
            r = await self.send_text(to, text)
        return r

    async def mark_read(self, msg_id):
        await self.http.post(self.url, headers=self.headers, json={
            "messaging_product": "whatsapp", "status": "read", "message_id": msg_id,
        })
