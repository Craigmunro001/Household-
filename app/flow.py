"""The conversation engine.

Code owns the flow, the qualification logic and the fee wording. The LLM (optional) only
helps understand free-text answers and answer general questions from the approved FAQ.
`handle()` is pure apart from mutating the session, so it is easy to test.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .content import (
    AGENT_PHRASES, BANDS, DISTRESS_PHRASES, NO_WORDS, OPTIONS, START_WORDS, STOP_PHRASES, YES_WORDS,
    band_key, options_text, rand, tr,
)

SAST = timezone(timedelta(hours=2))
STEPS = ["lang", "consent", "name", "debt", "marital", "province", "review", "callback"]
MAX_FAILS = 3


@dataclass
class Session:
    phone: str
    step: str = "new"
    lang: str = "en"
    status: str = "active"  # active | completed | handover | distress | opted_out
    name: str = ""
    answers: dict = field(default_factory=dict)
    fails: int = 0
    consent_at: str = ""
    created_at: str = ""
    updated_at: str = ""
    qualification: str = ""
    notes: list = field(default_factory=list)


@dataclass
class Reply:
    messages: list = field(default_factory=list)
    events: list = field(default_factory=list)  # completed | handover | distress | opted_out


# ---------------------------------------------------------------- text helpers
def norm(text):
    t = text.lower().replace("’", "'").replace("‘", "'").replace("-", " ")
    t = (t.replace("é", "e").replace("ê", "e").replace("ë", "e").replace("è", "e")
          .replace("ô", "o").replace("ö", "o").replace("û", "u").replace("ü", "u"))
    t = re.sub(r"[^\w' ]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def has_phrase(text, phrases):
    t = f" {norm(text)} "
    return any(f" {norm(p)} " in t for p in phrases)


def is_stop(text):
    t = norm(text)
    return len(t.split()) <= 4 and has_phrase(t, STOP_PHRASES)


def is_distress(text):
    return has_phrase(text, DISTRESS_PHRASES)


def wants_agent(text):
    t = norm(text)
    return len(t.split()) <= 10 and has_phrase(t, AGENT_PHRASES)


QUESTION_WORDS = {
    "what", "how", "why", "when", "who", "will", "can", "do", "does", "is", "are", "should", "could",
    "wat", "hoe", "hoekom", "wanneer", "wie", "kan", "sal", "is", "yini", "kanjani", "ngubani", "nini", "ngingakwazi",
}


SPOUSE_WORDS = ["wife", "husband", "spouse", "wyf", "vrou", "eggenoot", "eggenote", "umfazi", "umyeni"]
GAP_MARK = "[GAP]"


def split_gap(answer):
    """The AI marks a partly-answered question with [GAP]; strip it and report whether it was there."""
    if answer and GAP_MARK in answer:
        return answer.replace(GAP_MARK, "").strip(), True
    return answer, False


def note_spouse_mismatch(s, text):
    if s.answers.get("marital") == "not_married" and has_phrase(text, SPOUSE_WORDS):
        note = "Mentions a spouse but marital answer was 'not married' - consultant to clarify"
        if note not in s.notes:
            s.notes.append(note)


def looks_like_question(text):
    t = norm(text)
    words = t.split()
    if len(words) < 3:
        return False  # "yes?" / "no?" are answers, not questions
    return "?" in text or words[0] in QUESTION_WORDS


# ---------------------------------------------------------------- answer parsing
def parse_choice(step, text, bands=BANDS):
    """Return the chosen option value, or None."""
    t = norm(text)
    if step == "debt":
        if t.isdigit() and 1 <= int(t) <= len(bands):
            return band_key(bands[int(t) - 1])
        amount = parse_amount(text)
        if amount is not None:
            return band_for_amount(amount, bands)
        return None
    options = OPTIONS[step]
    if t.isdigit():
        i = int(t)
        return options[i - 1][0] if 1 <= i <= len(options) else None
    best = {}
    padded = f" {t} "
    for value, _, keywords in options:
        for kw in keywords:
            k = f" {norm(kw)} "
            if k in padded:
                best[value] = max(best.get(value, 0), len(k))
    if not best:
        return None
    top = max(best.values())
    winners = [v for v, n in best.items() if n == top]
    return winners[0] if len(winners) == 1 else None


def parse_amount(text):
    """'R250 000', '250k', '1,5m', '1.2 million', '250000' -> rand amount, or None for small/no numbers."""
    t = text.lower().replace(" ", " ")
    t = re.sub(r"(?<=\d)[ ](?=\d{3}(?!\d))", "", t)  # 250 000 -> 250000
    t = re.sub(r",(?=\d{3}(?!\d))", "", t)           # 1,500,000 -> 1500000
    t = t.replace(",", ".")                          # 1,5m -> 1.5m
    m = re.search(r"(\d+(?:\.\d+)?)\s*(k|m|million|miljoen|millioni|thousand|duisend|inkulungwane)?(?![a-z])", t)
    if not m:
        return None
    value = float(m.group(1))
    suffix = m.group(2)
    if suffix in ("k", "thousand", "duisend", "inkulungwane"):
        value *= 1_000
    elif suffix in ("m", "million", "miljoen", "millioni"):
        value *= 1_000_000
    elif value < 1_000:
        return None  # bare small number: not a trustworthy amount
    return int(value)


def band_for_amount(amount, bands=BANDS):
    for lo, hi in bands:
        if amount >= lo and (hi is None or amount < hi):
            return band_key((lo, hi))
    return None


# ---------------------------------------------------------------- messages
def ask(s, step, bands=BANDS):
    if step == "lang":
        return tr("welcome_all", "en", options=options_text("lang", "en"))
    if step == "consent":
        return tr("consent", s.lang)
    if step == "name":
        return tr("ask_name", s.lang)
    if step == "debt":
        return tr("ask_debt", s.lang, name=s.name, options=options_text("debt", s.lang, bands))
    if step in ("marital", "province", "review"):
        return tr(f"ask_{step}", s.lang, options=options_text(step, s.lang))
    if step == "callback":
        return tr("ask_callback", s.lang)
    raise ValueError(step)


def next_step(step):
    return STEPS[STEPS.index(step) + 1]


def clean_name(text):
    t = text.strip()
    t = re.sub(r"^(my name is|i am|i'm|im|ek is|my naam is|igama lami ngu|igama lami yi|ngingu)\s+", "", t, flags=re.I)
    t = re.sub(r"[^\w' -]", "", t).strip()
    words = t.split()
    if not words or len(words) > 4 or len(t) > 40 or looks_like_question(text):
        return None
    return " ".join(w.capitalize() for w in words)


def fee_range(s, fees, lang):
    if not fees:
        return ""
    entry = fees.get(s.answers.get("debt_band", ""))
    if not entry or not entry.get("min") or not entry.get("max"):
        return ""
    rng = tr("range", lang, min=rand(entry["min"]), max=rand(entry["max"]))
    return tr("fee_line", lang, range=rng)


def assess(s):
    """Triage for the consultant only. Never shown to, or used to turn away, the prospect.

    DRAFT rules; refine with real outcomes. Under debt review needs the consultant to
    explain next steps first; very low debt may not justify the process.
    """
    a = s.answers
    if a.get("review") == "yes" or a.get("debt_band") == "0-100000":
        return "unsure"
    return "likely"


def in_business_hours(now):
    local = now.astimezone(SAST)
    return local.weekday() < 5 and 8 <= local.hour < 17


# ---------------------------------------------------------------- engine
def handle(s, text, now, llm=None, fees=None, kind="text", bands=BANDS):
    iso = now.astimezone(SAST).isoformat(timespec="seconds")
    s.created_at = s.created_at or iso
    s.updated_at = iso
    out = Reply()
    t = (text or "").strip()

    if s.status == "handover":
        return out  # a human has it; stay silent
    if s.status == "opted_out":
        if norm(t) in START_WORDS:
            s.status, s.step, s.fails = "active", "new", 0
        else:
            return out
    if kind != "text" or not t:
        out.messages.append(tr("voice_note", s.lang))
        return out
    note_spouse_mismatch(s, t)
    if is_stop(t) and s.step != "new":
        s.status = "opted_out"
        out.messages.append(tr("stopped", s.lang))
        out.events.append("opted_out")
        return out
    if is_distress(t):
        s.status = "distress"
        s.notes.append("Distress language detected - call personally ASAP")
        msgs = [tr("distress", s.lang)] if s.step not in ("new", "lang") else [tr("distress", l) for l in ("en", "af", "zu")]
        out.messages += msgs
        out.events.append("distress")
        return out
    if s.step != "new" and wants_agent(t):
        s.status = "handover"
        s.notes.append(f"Asked for a person at step '{s.step}'")
        out.messages.append(tr("handover", s.lang))
        out.events.append("handover")
        return out

    if s.status == "distress":
        return out

    if s.status == "completed":
        _after_completion(s, t, out, now, llm)
        return out

    if s.step == "new":
        s.step = "lang"
        out.messages.append(ask(s, "lang"))
        return out

    _answer_step(s, t, out, now, llm, fees, bands)
    return out


def _after_completion(s, t, out, now, llm):
    if looks_like_question(t):
        ans, gap = split_gap(llm.faq(t, s.lang) if llm else None)
        s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
        if ans:
            out.messages.append(ans)
            return
        out.messages.append(tr("faq_fallback", s.lang).strip())
        return
    s.notes.append("Client wrote after completing: " + t[:200])
    out.messages.append(tr("already_done", s.lang, name=s.name or ""))


def _answer_question(s, t, out, llm, step, bands):
    """Answer what they asked, log it, then gently return to the current question."""
    answer, gap = split_gap(llm.faq(t, s.lang) if llm else None)
    s.notes.append(("Asked: " if answer and not gap else "UNANSWERED: ") + t[:200])
    out.messages.append((answer or tr("faq_fallback", s.lang).strip()) + "\n\n" + ask(s, step, bands))


def _answer_step(s, t, out, now, llm, fees, bands):
    step = s.step

    # A genuine question is always answered first, even if it contains words that look like an answer.
    if step != "callback" and looks_like_question(t):
        _answer_question(s, t, out, llm, step, bands)
        return

    # --- parse the answer for this step
    ok = False
    if step == "lang":
        value = parse_choice("lang", t)
        if value:
            s.lang, ok = value, True
    elif step == "consent":
        n = norm(t)
        words = n.split()
        if n in YES_WORDS or (words and words[0] in YES_WORDS):
            s.consent_at, ok = s.updated_at, True
        elif n in NO_WORDS:
            s.status = "opted_out"
            out.messages.append(tr("declined", s.lang))
            out.events.append("opted_out")
            return
    elif step == "name":
        name = clean_name(t)
        if name:
            s.name, ok = name, True
    elif step == "callback":
        if not ("?" in t and len(t.split()) >= 5) and len(t) >= 2:
            s.answers["callback_raw"] = t[:200]
            s.answers["callback"] = (llm.normalise_callback(t, now) if llm else None) or t[:200]
            ok = True
    else:
        value = parse_choice(step, t, bands) or (llm.classify(step, t, s.lang, bands) if llm else None)
        if value:
            s.answers["debt_band" if step == "debt" else step] = value
            if step == "debt":
                amt = parse_amount(t)
                if amt:
                    s.answers["debt_amount_stated"] = amt
            ok = True

    # --- success: move on
    if ok:
        s.fails = 0
        if step == "callback":
            _finish(s, out, now, fees)
        else:
            s.step = next_step(step)
            out.messages.append(ask(s, s.step, bands))
        return

    # --- not understood: a question gets an answer, anything else gets a gentle re-ask
    s.fails += 1
    if s.fails >= MAX_FAILS:
        s.status = "handover"
        s.notes.append(f"Bot could not understand answers at step '{step}'")
        out.messages.append(tr("handover", s.lang))
        out.events.append("handover")
        return
    prefix = tr("reask", s.lang)

    if step == "lang" and s.fails >= 2:
        s.lang, s.step, s.fails = "en", "consent", 0  # default to English rather than stall
        out.messages.append(ask(s, "consent", bands))
        return
    out.messages.append(prefix + ask(s, step, bands))


def _finish(s, out, now, fees):
    s.status = "completed"
    s.qualification = assess(s)
    after = "" if in_business_hours(now) else tr("after_hours", s.lang)
    out.messages.append(tr(
        "done", s.lang, name=s.name, callback=s.answers["callback_raw"],
        fee=fee_range(s, fees, s.lang), after=after,
    ))
    out.events.append("completed")
