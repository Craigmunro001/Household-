"""Go-live pre-flight check. Never prints secret values.

    python preflight.py                              # configuration only
    python preflight.py --url https://your-app.up.railway.app   # also checks the deployed webhook
Exit code 1 if anything REQUIRED is missing.
"""
import argparse
import os
import sys

import httpx

REQUIRED = [
    ("WHATSAPP_TOKEN", "permanent System User token from Meta"),
    ("WHATSAPP_PHONE_NUMBER_ID", "from Meta > WhatsApp > API setup"),
    ("WHATSAPP_VERIFY_TOKEN", "any random string; type the same into Meta's webhook page"),
    ("WHATSAPP_APP_SECRET", "Meta app secret: the bot refuses unsigned webhooks without it"),
]
RECOMMENDED = [
    ("ANTHROPIC_API_KEY", "without it the bot still works, but free-text answers and the FAQ AI are off"),
    ("GOOGLE_SHEET_ID", "without it leads are only written to a local file (lost on redeploy)"),
    ("GOOGLE_SERVICE_ACCOUNT_JSON", "service-account JSON; share the Sheet with its email"),
    ("NOTIFY_TO", "who gets the consultant alert emails"),
    ("SMTP_HOST", "e.g. smtp.gmail.com"),
    ("SMTP_USER", "mailbox that sends the alerts"),
    ("SMTP_PASSWORD", "app password for that mailbox"),
]
OK, WARN, FAIL = "OK  ", "WARN", "FAIL"


def check_env(env):
    rows = []
    for name, hint in REQUIRED:
        rows.append((OK if env.get(name) else FAIL, name, "set" if env.get(name) else f"MISSING - {hint}"))
    for name, hint in RECOMMENDED:
        rows.append((OK if env.get(name) else WARN, name, "set" if env.get(name) else f"not set - {hint}"))
    if env.get("DEV_MODE", "0") == "1":
        rows.append((FAIL, "DEV_MODE", "is 1: webhook signatures are NOT checked. Set it to 0 (or remove it) in production"))
    db = env.get("DB_PATH", "data/sessions.sqlite3")
    on_volume = db.startswith("/data") or db.startswith("/app/data") or db.startswith("/mnt")
    rows.append((OK if on_volume else WARN, "DB_PATH", f"{db}" + ("" if on_volume else " - not on a mounted volume: conversations are lost on every redeploy")))
    return rows


def check_content():
    rows = []
    try:
        from app.pricing import load_pricebook
        pb = load_pricebook()
        rows.append((OK if pb else FAIL, "price book", f"loaded ({pb.generated})" if pb else "config/fees.yaml missing or invalid: the bot would quote NO figures"))
    except Exception as e:  # pragma: no cover
        rows.append((FAIL, "price book", f"error: {e}"))
    try:
        import pathlib
        from app.llm import faq_for_prompt
        faq = faq_for_prompt(pathlib.Path("knowledge/faq.md").read_text())
        leaks = [w for w in ("David", "Schoonraad", "DRAFT", "VERIFY", "CONFLICT") if w in faq]
        rows.append((OK if faq and not leaks else FAIL, "FAQ knowledge", f"{faq.count('## Q:')} answers" if not leaks else f"internal text would reach the AI: {leaks}"))
    except Exception as e:  # pragma: no cover
        rows.append((FAIL, "FAQ knowledge", f"error: {e}"))
    return rows


def check_url(url, verify_token, client=None):
    rows, url = [], url.rstrip("/")
    c = client or httpx.Client(timeout=15)
    try:
        r = c.get(f"{url}/health")
        body = r.json() if r.status_code == 200 else {}
        rows.append((OK if r.status_code == 200 else FAIL, "deployed /health", f"HTTP {r.status_code}"))
        if body:
            rows.append((OK if body.get("price_book") else FAIL, "deployed price book", str(body.get("price_book"))))
            rows.append((OK if body.get("llm") else WARN, "deployed AI layer", "on" if body.get("llm") else "off (no ANTHROPIC_API_KEY on the server)"))
            rows.append((OK if body.get("sheet") == "GoogleSheetSink" else WARN, "deployed lead store", str(body.get("sheet"))))
        h = c.get(f"{url}/webhook", params={"hub.mode": "subscribe", "hub.verify_token": verify_token, "hub.challenge": "preflight123"})
        rows.append((OK if h.status_code == 200 and h.text == "preflight123" else FAIL, "webhook handshake",
                     "Meta's verification step will work" if h.status_code == 200 else f"HTTP {h.status_code}: the verify token on the server differs from the one you typed"))
        p = c.post(f"{url}/webhook", json={"entry": []})
        rows.append((OK if p.status_code == 403 else FAIL, "unsigned webhook rejected", "forged messages are refused" if p.status_code == 403 else f"HTTP {p.status_code}: SECURITY: unsigned requests are being accepted"))
    except Exception as e:
        rows.append((FAIL, "deployed app", f"could not reach {url}: {e}"))
    return rows


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--url")
    args = ap.parse_args(argv)
    rows = check_env(os.environ) + check_content()
    if args.url:
        rows += check_url(args.url, os.environ.get("WHATSAPP_VERIFY_TOKEN", ""))
    for status, name, detail in rows:
        print(f"[{status}] {name}: {detail}")
    failed = [r for r in rows if r[0] == FAIL]
    print(f"\n{len(failed)} blocking problem(s), {sum(r[0] == WARN for r in rows)} warning(s).")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
