import hashlib
import hmac
import json
import os

os.environ.update({
    "DB_PATH": ":memory:", "WHATSAPP_VERIFY_TOKEN": "tok", "WHATSAPP_APP_SECRET": "sekret",
    "HUMAN_DELAY_SECONDS": "0", "GOOGLE_SHEET_ID": "", "ANTHROPIC_API_KEY": "",
})

from fastapi.testclient import TestClient  # noqa: E402

from app import main  # noqa: E402

sent = []


async def fake_send(to, body):
    sent.append((to, body))


async def fake_read(msg_id):
    pass


main.wa.send_text = fake_send
main.wa.mark_read = fake_read
main.sink = type("S", (), {"upsert": lambda self, s: None})()
client = TestClient(main.app)


def payload(msg_id, text, phone="27821112222"):
    return {"entry": [{"changes": [{"value": {
        "contacts": [{"wa_id": phone, "profile": {"name": "Test"}}],
        "messages": [{"id": msg_id, "from": phone, "type": "text", "text": {"body": text}}],
    }}]}]}


def post(p, secret="sekret"):
    body = json.dumps(p).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return client.post("/webhook", content=body, headers={"x-hub-signature-256": sig, "content-type": "application/json"})


def test_verification_handshake():
    r = client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "tok", "hub.challenge": "123"})
    assert r.status_code == 200 and r.text == "123"
    assert client.get("/webhook", params={"hub.mode": "subscribe", "hub.verify_token": "bad", "hub.challenge": "1"}).status_code == 403


def test_bad_signature_rejected():
    assert post(payload("a", "hi"), secret="wrong").status_code == 403


def test_message_gets_reply_and_duplicates_ignored():
    sent.clear()
    assert post(payload("m1", "hi")).status_code == 200
    assert len(sent) == 1 and "language" in sent[0][1].lower()
    post(payload("m1", "hi"))  # Meta retry of the same message id
    assert len(sent) == 1
    post(payload("m2", "1"))
    assert any("virtual assistant" in b for _, b in sent)
