"""Call-back time: offer real slots, understand free text ("Friday after 2pm", "Saturday morning"),
and flag anything outside standard calling hours (Mon-Fri 08:00-17:00 SAST) for a consultant to confirm.
Pure functions; no promises are made about out-of-hours requests."""
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

SAST = timezone(timedelta(hours=2))

DAY_NAMES = {
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    "af": ["Ma", "Di", "Wo", "Do", "Vr", "Sa", "So"],
    "zu": ["Msombuluko", "Lwesibili", "Lwesithathu", "Lwesine", "Lwesihlanu", "Mgqibelo", "Sonto"],
}
MONTH_NAMES = {
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    "af": ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Des"],
    "zu": ["Jan", "Feb", "Mas", "Eph", "Mey", "Jun", "Jul", "Aga", "Sep", "Okt", "Nov", "Dis"],
}
TOMORROW = {"en": "tomorrow", "af": "môre", "zu": "kusasa"}
PERIOD_WORDS = {
    "morning": {"en": "morning", "af": "oggend", "zu": "ekuseni"},
    "afternoon": {"en": "afternoon", "af": "middag", "zu": "ntambama"},
    "evening": {"en": "evening", "af": "aand", "zu": "kusihlwa"},
}
AFTER = {"en": "after", "af": "na", "zu": "ngemva kwe-"}

WEEKDAYS = {  # keyword -> Monday=0
    **{w: 0 for w in ("monday", "mon", "maandag", "msombuluko", "umsombuluko")},
    **{w: 1 for w in ("tuesday", "tue", "tues", "dinsdag", "ulwesibili", "lwesibili")},
    **{w: 2 for w in ("wednesday", "wed", "woensdag", "ulwesithathu", "lwesithathu")},
    **{w: 3 for w in ("thursday", "thu", "thur", "thurs", "donderdag", "ulwesine", "lwesine")},
    **{w: 4 for w in ("friday", "fri", "vrydag", "ulwesihlanu", "lwesihlanu")},
    **{w: 5 for w in ("saturday", "sat", "saterdag", "umgqibelo", "mgqibelo")},
    **{w: 6 for w in ("sunday", "sun", "sondag", "usonto", "sonto")},
}
TODAY_WORDS = {"today", "vandag", "namuhla"}
TOMORROW_WORDS = {"en": {"tomorrow", "tomorow", "tommorow", "tommorrow"}}
PERIODS = {
    "morning": ("morning", "oggend", "ekuseni"),
    "afternoon": ("afternoon", "middag", "ntambama"),
    "evening": ("evening", "tonight", "night", "aand", "kusihlwa", "ebusuku"),
}
PERIOD_HOURS = {"morning": 8, "afternoon": 12, "evening": 17}
OTHER_DAY_PHRASES = ["another day", "other day", "different day", "another time", "different time", "ander dag", "ander tyd",
                     "elinye usuku", "elinye isikhathi"]


@dataclass
class Parsed:
    kind: str                 # slot | day_only | time_only | past | none
    day: date = None
    hour: int = None
    minute: int = 0
    period: str = None        # morning | afternoon | evening
    after: bool = False


def _clean(text):
    t = text.lower().replace("’", "'")
    for a, b in (("ê", "e"), ("ë", "e"), ("è", "e"), ("é", "e"), ("ô", "o"), ("ö", "o"), ("û", "u"), ("ü", "u")):
        t = t.replace(a, b)
    return t


def local(now):
    return now.astimezone(SAST)


def next_working_day(now):
    d = local(now).date() + timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


def day_label(d, now, lang):
    """'tomorrow (Wed 4 Nov)' or 'Mon 9 Nov'."""
    base = f"{DAY_NAMES[lang][d.weekday()]} {d.day} {MONTH_NAMES[lang][d.month - 1]}"
    if d == local(now).date() + timedelta(days=1):
        return f"{TOMORROW[lang]} ({base})"
    return base


def slot(day, hour, minute=0):
    return Parsed("slot", day, hour, minute)


def _hour_from_text(h, ampm, has_minutes=False):
    if ampm == "pm" and h < 12:
        h += 12
    elif ampm == "am" and h == 12:
        h = 0
    elif ampm is None:
        if 1 <= h <= 7:
            h += 12       # "2" means 2pm, "7" means 7pm
        # 8-11 stay morning, 12 stays noon, 13-23 are already 24h
    return h


def _find_time(t, day_present):
    """-> (hour, minute) or None."""
    m = re.search(r"(\d{1,2})\s*[:h.]\s*(\d{2})\s*(am|pm)?", t)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        return (_hour_from_text(h, m.group(3), True), mi) if h <= 23 and mi < 60 else None
    m = re.search(r"\b(\d{1,2})\s*(am|pm|nm|vm)\b", t)
    if m:
        h = int(m.group(1))
        suffix = {"nm": "pm", "vm": "am"}.get(m.group(2), m.group(2))
        return (_hour_from_text(h, suffix, False), 0) if 1 <= h <= 12 else None
    m = re.search(r"\b(\d{1,2})\s*(?:o'?clock|uur)\b", t)
    if m:
        h = int(m.group(1))
        return (_hour_from_text(h, None, False), 0) if 1 <= h <= 23 else None
    m = re.search(r"(?:\bat\b|\bom\b|\bngo-?|@|\baround\b|\babout\b|\bby\b)\s*(\d{1,2})\b", t)
    if m:
        h = int(m.group(1))
        return (_hour_from_text(h, None, False), 0) if 1 <= h <= 23 else None
    m = re.fullmatch(r"\s*(\d{1,2})\s*", t)
    if m or (day_present and (m := re.search(r"(\d{1,2})\s*$", t))):
        h = int(m.group(1))
        return (_hour_from_text(h, None, False), 0) if 1 <= h <= 23 else None
    return None


def parse_callback(text, now, lang="en", pending_day=None):
    """Understand a free-text call-back request. A slot needs BOTH a day and a time (or part of day)."""
    t = _clean(text)
    words = set(re.findall(r"[a-z]+", t))
    today = local(now).date()

    day = pending_day
    if words & TODAY_WORDS:
        day = today
    elif words & (TOMORROW_WORDS["en"] | ({"more"} if lang == "af" else set())) or "kusasa" in words:
        day = today + timedelta(days=1)
    else:
        for w in words:
            if w in WEEKDAYS:
                day = ("weekday", WEEKDAYS[w])
                break

    period = next((p for p, kws in PERIODS.items() if words & set(kws)), None)
    after = bool(words & {"after", "from", "na", "ngemva"})
    tm = _find_time(t, day is not None)

    if isinstance(day, tuple):  # resolve weekday name to the next such date
        target = today + timedelta(days=(day[1] - today.weekday()) % 7)
        if target == today and not (tm and (tm[0], tm[1]) > (local(now).hour, local(now).minute)):
            target += timedelta(days=7)
        day = target

    if tm is None and period is None:
        return Parsed("day_only", day) if day else Parsed("none")
    if day is None:
        return Parsed("time_only")

    hour, minute = tm if tm else (PERIOD_HOURS[period], 0)
    start = datetime(day.year, day.month, day.day, hour, minute, tzinfo=SAST)
    if start <= local(now):
        return Parsed("past", day, hour, minute, period if not tm else None, after)
    return Parsed("slot", day, hour, minute, period if not tm else None, after)


def in_standard_hours(p):
    if p.day.weekday() >= 5:
        return False
    if p.period == "evening":
        return False
    return 8 <= p.hour < 17


def label(p, lang="en"):
    base = f"{DAY_NAMES[lang][p.day.weekday()]} {p.day.day} {MONTH_NAMES[lang][p.day.month - 1]}"
    if p.period:
        return f"{base}, {PERIOD_WORDS[p.period][lang]}"
    clock = f"{p.hour:02d}:{p.minute:02d}"
    return f"{base}, {AFTER[lang]} {clock}" if p.after else f"{base}, {clock}"
