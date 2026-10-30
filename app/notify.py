"""Consultant alerts by email. Always logs, so nothing is lost if SMTP isn't configured."""
import logging
import smtplib
from email.message import EmailMessage

from .content import BANDS, band_key, band_label

log = logging.getLogger("pinnacle.notify")
_BAND_LABELS = {band_key(b): band_label(b, "en") for b in BANDS}

SUBJECTS = {
    "completed": "New qualified lead",
    "handover": "Lead wants a person",
    "distress": "URGENT: distressed lead, call personally",
}


def build(event, s):
    a = s.answers
    subject = f"[Pinnacle] {SUBJECTS[event]}: {s.name or s.phone}"
    body = "\n".join([
        f"Event: {event}",
        f"Name: {s.name}",
        f"WhatsApp: +{s.phone}",
        f"Language: {s.lang}",
        f"Debt: {_BAND_LABELS.get(a.get('debt_band', ''), 'n/a')}",
        f"Marital status: {a.get('marital', 'n/a')}",
        f"Province: {a.get('province', 'n/a')}",
        f"Under debt review: {a.get('review', 'n/a')}",
        f"Call back: {a.get('callback', 'n/a')}",
        f"Triage: {s.qualification.upper() or 'n/a'}",
        f"Notes: {' | '.join(s.notes) or '-'}",
    ])
    return subject, body


def send(settings, event, s):
    if event not in SUBJECTS:
        return
    subject, body = build(event, s)
    log.info("ALERT %s\n%s", subject, body)
    if not (settings.smtp_host and settings.notify_to):
        return
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, settings.notify_from, ", ".join(settings.notify_to)
    msg.set_content(body)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.starttls()
            smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(msg)
    except Exception:
        log.exception("email alert failed")
