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
MONTHS = {
    **{m: i + 1 for i, names in enumerate([("jan", "january", "januarie"), ("feb", "february", "februarie"), ("mar", "march", "maart", "mrt"),
       ("apr", "april"), ("may", "mei"), ("jun", "june", "junie"), ("jul", "july", "julie"), ("aug", "august", "augustus"),
       ("sep", "sept", "september"), ("oct", "october", "oktober", "okt"), ("nov", "november"), ("dec", "december", "desember", "des")])
       for m in names},
}
_MONTH_RE = "|".join(sorted(MONTHS, key=len, reverse=True))
FLEXIBLE_PHRASES = ["consultant suggest", "you choose", "you decide", "any time", "anytime", "whenever", "doesnt matter", "doesn't matter",
                    "suggest a time", "kies jy", "enige tyd", "maak nie saak", "ngaso sonke isikhathi"]
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
    m = re.search(r"\b(\d{1,2})\s+(00|15|30|45)\b", t)
    if m and int(m.group(1)) <= 23:
        return (_hour_from_text(int(m.group(1)), None), int(m.group(2)))
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


def _extract_dates(t, today):
    """Dates written as '5 Nov', 'nov 5', '5th of November', '05/11' or just 'the 5th'.
    -> (list of distinct dates, text with the date parts removed). Several different dates = ambiguous."""
    found, rest = [], t

    def add(day, month):
        try:
            d = date(today.year, month, day) if month else date(today.year, today.month, day)
        except ValueError:
            return
        if d < today:  # already gone: next occurrence
            try:
                d = date(today.year + (1 if month else 0), month or (today.month % 12) + 1, day) if month else \
                    date(today.year + (today.month == 12), (today.month % 12) + 1, day)
            except ValueError:
                return
        found.append(d)

    for rx, order in ((rf"\b(\d{{1,2}})\s*(?:st|nd|rd|th)?\s*(?:of\s+|van\s+)?({_MONTH_RE})\b", "dm"),
                      (rf"\b({_MONTH_RE})\s+(\d{{1,2}})\b", "md"),
                      (r"\b(\d{1,2})\s*[/-]\s*(\d{1,2})\b", "dm")):
        for m in list(re.finditer(rx, rest)):
            a, b = m.group(1), m.group(2)
            day, month = (int(a), MONTHS.get(b) or int(b)) if order == "dm" else (int(b), MONTHS[a])
            if 1 <= day <= 31 and 1 <= month <= 12:
                add(day, month)
            rest = rest.replace(m.group(0), " ")
    for m in list(re.finditer(r"\b(\d{1,2})\s*(?:st|nd|rd|th)\b", rest)):
        if 1 <= int(m.group(1)) <= 31:
            add(int(m.group(1)), None)
        rest = rest.replace(m.group(0), " ")
    return sorted(set(found)), rest


def parse_callback(text, now, lang="en", pending_day=None, pending_time=None):
    """Understand a free-text call-back request. A slot needs BOTH a day and a time (or part of day)."""
    t = _clean(text)
    today = local(now).date()
    dates, t = _extract_dates(t, today)
    if len(dates) > 1:
        return Parsed("none")  # two different dates in one message: too ambiguous to guess
    words = set(re.findall(r"[a-z]+", t))

    day = dates[0] if dates else pending_day
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
    tm = _find_time(t, day is not None) or pending_time

    if isinstance(day, tuple):  # resolve weekday name to the next such date
        target = today + timedelta(days=(day[1] - today.weekday()) % 7)
        if target == today and not (tm and (tm[0], tm[1]) > (local(now).hour, local(now).minute)):
            target += timedelta(days=7)
        day = target

    if tm is None and period is None:
        return Parsed("day_only", day) if day else Parsed("none")
    if day is None:
        h, mi = tm if tm else (PERIOD_HOURS[period], 0)
        return Parsed("time_only", None, h, mi, period if not tm else None, after)

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


TIME_PICKS = (8, 10, 12, 14, 16)


def day_picks(now, count=3):
    """The next few working days, starting tomorrow (or Monday)."""
    days, d = [], next_working_day(now)
    while len(days) < count:
        days.append(d)
        d += timedelta(days=1)
        while d.weekday() >= 5:
            d += timedelta(days=1)
    return days


def clock(hour, minute=0):
    return f"{hour:02d}:{minute:02d}"
