"""The conversation engine.

Code owns the flow, the qualification logic and the fee wording. The LLM (optional) only
helps understand free-text answers and answer general questions from the approved FAQ.
`handle()` is pure apart from mutating the session, so it is easy to test.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .content import (
    AGENT_PHRASES, BANDS, COST_PHRASES, DISTRESS_PHRASES, NO_WORDS, OPTIONS, REQUEST_STARTS, START_WORDS, STOP_PHRASES, YES_WORDS,
    band_key, options_text, rand, tr,
)

SAST = timezone(timedelta(hours=2))
STEPS = ["lang", "consent", "name", "debt", "marital", "province", "review", "callback"]
MAX_FAILS = 3
MIN_DEBT_BAND = "0-100000"  # Pinnacle does not take cases under R100 000


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


AF_WORDS = {"ek", "jy", "nie", "wat", "hoe", "kan", "gaan", "die", "het", "dit", "ons", "tronk", "skuld", "moet", "sal",
            "asseblief", "dankie", "wil", "ook", "maar", "nog", "vir", "toe", "my", "jou", "sê", "wanneer", "hoekom", "baie"}
EN_WORDS = {"the", "i", "you", "is", "are", "what", "how", "can", "will", "to", "of", "and", "a", "it", "do", "does",
            "my", "me", "this", "that", "with", "for", "if", "be", "have", "not", "when", "why", "who", "about", "please"}
ZU_PREFIXES = ("ngi", "uku", "nga", "ngo", "ngu", "kwa", "uma", "yin", "kan", "ngin", "angi", "ubu", "ama", "aba")
ZU_WORDS = {"yebo", "cha", "futhi", "kodwa", "impela", "kakhulu", "nini", "kuphi", "ngubani", "yini", "kanjani", "uma",
            "ngicela", "ngiyabonga", "angikwazi", "ngifuna", "ngingakwazi", "ukuthi", "nami", "wami", "lami"}


def detect_lang(text):
    """Cheap language detector for en / af / zu. Returns None unless it is clear (>= 3 words)."""
    words = norm(text).split()
    if len(words) < 3:
        return None
    en = sum(w in EN_WORDS for w in words)
    af = sum(w in AF_WORDS for w in words)
    zu = sum(w in ZU_WORDS or (len(w) > 5 and w.startswith(ZU_PREFIXES) and w not in EN_WORDS) for w in words)
    if af >= 2 and af > en and af >= zu:
        return "af"
    if zu >= 2 and zu > en:
        return "zu"
    if en >= 2 and en > af and en > zu:
        return "en"
    return None


def maybe_switch_language(s, text):
    lang = detect_lang(text)
    if lang and lang != s.lang and s.step not in ("new", "lang"):
        s.notes.append(f"Switched language {s.lang} -> {lang}")
        s.lang = lang


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


def is_cost_question(text):
    return has_phrase(text, COST_PHRASES)


def looks_like_question(text):
    t = norm(text)
    words = t.split()
    if len(words) < 3:
        return False  # "yes?" / "no?" are answers, not questions
    t = " ".join(words)
    if is_cost_question(t) or any(t.startswith(r) for r in REQUEST_STARTS):
        return True
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
    """Monthly-instalment wording from config/fees.yaml. Empty string if the band has no approved figures."""
    if not fees:
        return ""
    entry = fees.get(s.answers.get("debt_band", ""))
    if not entry or not entry.get("monthly_min") or not entry.get("monthly_max"):
        return ""
    rng = tr("range", lang, min=rand(entry["monthly_min"]), max=rand(entry["monthly_max"]))
    term = tr("term", lang, months=entry["months"]) if entry.get("months") else ""
    return tr("fee_line", lang, range=rng, term=term)


def assess(s):
    """Triage for the consultant only. Never shown to, or used to turn away, the prospect.

    DRAFT rules; refine with real outcomes. Under debt review needs the consultant to
    explain next steps first; 
    """
    a = s.answers
    if a.get("review") == "yes":
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
    maybe_switch_language(s, t)
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

    if s.status == "not_fit":
        _after_not_fit(s, t, out, now, llm, fees, bands)
        return out

    if s.status == "completed":
        _after_completion(s, t, out, now, llm, fees)
        return out

    if s.step == "new":
        s.step = "lang"
        out.messages.append(ask(s, "lang"))
        return out

    _answer_step(s, t, out, now, llm, fees, bands)
    return out


def _after_completion(s, t, out, now, llm, fees):
    is_q = looks_like_question(t)
    if is_q or len(norm(t).split()) >= 4:  # a real message, not just "ok" / "thanks"
        ans, gap = _faq_or_cost(s, t, llm, fees)
        s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
        if ans:
            out.messages.append(ans)
            return
        out.messages.append(tr("faq_fallback" if is_q else "already_done", s.lang, name=s.name or "").strip())
        return
    s.notes.append("Client wrote after completing: " + t[:200])
    out.messages.append(tr("already_done", s.lang, name=s.name or ""))


def _faq_or_cost(s, t, llm, fees):
    """Fee questions are answered from config/fees.yaml (never by the AI); everything else from the FAQ."""
    if is_cost_question(t):
        line = fee_range(s, fees, s.lang).strip()
        if line:
            return line, False
        note = "Asked about COST - consultant should open the call with the fee"
        if note not in s.notes:
            s.notes.append(note)
    return split_gap(llm.faq(t, s.lang) if llm else None)


def _answer_question(s, t, out, llm, step, bands, fees):
    """Answer what they asked, log it, then gently return to the current question."""
    answer, gap = _faq_or_cost(s, t, llm, fees)
    s.notes.append(("Asked: " if answer and not gap else "UNANSWERED: ") + t[:200])
    out.messages.append((answer or tr("faq_fallback", s.lang).strip()) + "\n\n" + ask(s, step, bands))


def _answer_step(s, t, out, now, llm, fees, bands):
    step = s.step

    # A genuine question is always answered first, even if it contains words that look like an answer.
    if step != "callback" and looks_like_question(t):
        _answer_question(s, t, out, llm, step, bands, fees)
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
        elif step == "debt" and s.answers["debt_band"] == MIN_DEBT_BAND:
            _not_fit(s, out)
        else:
            s.step = next_step(step)
            out.messages.append(ask(s, s.step, bands))
        return

    # --- not an answer: if it's a real message, let the AI/FAQ respond before treating it as a failed answer
    if llm and len(norm(t).split()) >= 4 and step != "callback":
        answer, gap = _faq_or_cost(s, t, llm, fees)
        if answer:
            s.notes.append(("Asked: " if not gap else "UNANSWERED: ") + t[:200])
            out.messages.append(answer + "\n\n" + ask(s, step, bands))
            return

    # --- not understood: a gentle re-ask, and hand over after repeated failures
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


def _not_fit(s, out):
    """Below the minimum debt the fees cost more than the debt: say so kindly and stop. No consultant call."""
    s.status = "not_fit"
    s.qualification = "not_fit"
    s.notes.append("Debt under R100 000 - not a fit, no consultant call")
    out.messages.append(tr("not_fit", s.lang, name=s.name))
    out.events.append("not_fit")


def _after_not_fit(s, t, out, now, llm, fees, bands):
    """Let them correct the amount (it was only a rough estimate); otherwise answer questions politely."""
    amount = parse_amount(t)
    band = band_for_amount(amount, bands) if amount else None
    if band and band != MIN_DEBT_BAND:
        s.status, s.step, s.fails = "active", "marital", 0
        s.answers["debt_band"], s.answers["debt_amount_stated"] = band, amount
        s.qualification = ""
        s.notes.append("Corrected debt amount to over R100 000")
        out.messages.append(ask(s, "marital", bands))
        return
    if looks_like_question(t):
        ans, gap = _faq_or_cost(s, t, llm, fees)
        s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
        if ans:
            out.messages.append(ans)
            return
    out.messages.append(tr("not_fit_followup", s.lang, name=s.name))


def _finish(s, out, now, fees):
    s.status = "completed"
    s.qualification = assess(s)
    after = "" if in_business_hours(now) else tr("after_hours", s.lang)
    out.messages.append(tr(
        "done", s.lang, name=s.name, callback=s.answers["callback_raw"],
        fee=fee_range(s, fees, s.lang), after=after,
    ))
    out.events.append("completed")
