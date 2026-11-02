"""Consultant alerts by email. Always logs, so nothing is lost if SMTP isn't configured."""
import logging
import smtplib
from email.message import EmailMessage


log = logging.getLogger("pinnacle.notify")

VEHICLE_LABEL = {"yes": "under finance", "no": "none", "paid_off": "fully paid off"}

SUBJECTS = {
    "completed": "New qualified lead",
    "handover": "Lead wants a person",
    "distress": "URGENT: distressed lead, call personally",
    "person_requested": "Lead asked for a person after hours (bot is continuing, call back next working day)",
    "callback_updated": "Lead changed their call time",
    "correction_requested": "Lead flagged a correction - fix before calling",
}


def build(event, s):
    a = s.answers
    subject = f"[Pinnacle] {SUBJECTS[event]}: {s.name or s.phone}"
    body = "\n".join([
        f"Event: {event}",
        f"Name: {s.name}",
        f"WhatsApp: +{s.phone}",
        f"Language: {s.lang}",
        f"Debt stated: R{a['debt_amount']:,}" if a.get("debt_amount") else "Debt stated: n/a",
        f"Estimate shown: R{a['estimate']['monthly']:,.2f}/month over {a['estimate']['months']} months ({a['estimate']['bracket']}, {'Gauteng' if a['estimate']['gauteng'] else 'outside Gauteng'})" if a.get("estimate") else "Estimate shown: none (consultant to quote)",
        f"Owns a home: {a.get('home', 'n/a')} | Vehicle: {VEHICLE_LABEL.get(a.get('vehicle'), 'n/a')}",
        ("Asset warning: " + "; ".join(f"{k} (told it would be {'sold by the trustee, usually at auction' if k == 'home' else 'taken back by the bank'}, chose to continue at {v['at']})" for k, v in a["asset_ack"].items())) if a.get("asset_ack") else "Asset warning: not applicable",
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
