"""The conversation engine.

Code owns the flow, the qualification logic and the fee wording. The LLM (optional) only
helps understand free-text answers and answer general questions from the approved FAQ.
`handle()` is pure apart from mutating the session, so it is easy to test.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .content import (
    AGENT_PHRASES, COST_PHRASES, DISTRESS_PHRASES, NO_WORDS, OPTIONS, REQUEST_STARTS, START_WORDS, STOP_PHRASES,
    TERMS, YES_WORDS, money, options_text, tr,
)

SAST = timezone(timedelta(hours=2))
STEPS = ["lang", "consent", "name", "province", "debt", "term", "marital", "review", "callback"]
MAX_FAILS = 3
DEFAULT_DECLINE_BELOW = 100_000  # Pinnacle does not take cases under R100 000 (the price book can override)


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
    events: list = field(default_factory=list)  # completed | handover | distress | opted_out | not_fit


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
def parse_choice(step, text):
    """Return the chosen option value for a menu step, or None."""
    t = norm(text)
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


_AMOUNT = r"(\d+(?:\.\d+)?)\s*(k|m|million|miljoen|millioni|thousand|duisend|inkulungwane)?(?![a-z])"


def all_amounts(text):
    """Every rand amount in the text: 'R250 000', '250k', '1,5m', '1.2 million', '250000'. Bare numbers under 1 000 are ignored."""
    t = text.lower().replace("\u00a0", " ")
    t = re.sub(r"(?<=\d)[ ](?=\d{3}(?!\d))", "", t)  # 250 000 -> 250000
    t = re.sub(r",(?=\d{3}(?!\d))", "", t)           # 1,500,000 -> 1500000
    t = t.replace(",", ".")                          # 1,5m -> 1.5m
    out = []
    for m in re.finditer(_AMOUNT, t):
        value, suffix = float(m.group(1)), m.group(2)
        if suffix in ("k", "thousand", "duisend", "inkulungwane"):
            value *= 1_000
        elif suffix in ("m", "million", "miljoen", "millioni"):
            value *= 1_000_000
        elif value < 1_000:
            continue
        out.append(int(value))
    return out


def parse_amount(text):
    amounts = all_amounts(text)
    return amounts[0] if amounts else None


def parse_term(text):
    """-> (months, out_of_range). Only 25, 30 or 36 are valid; any other number outside 25-36 is 'out of range'."""
    t = norm(text)
    if t in ("1", "2", "3"):
        return TERMS[int(t) - 1], False
    m = re.search(r"\b(\d{1,3})\b", t)
    if not m:
        return None, False
    n = int(m.group(1))
    if n in TERMS:
        return n, False
    return None, not (25 <= n <= 36)


# ---------------------------------------------------------------- messages
def ask(s, step):
    if step == "lang":
        return tr("welcome_all", "en", options=options_text("lang", "en"))
    if step == "consent":
        return tr("consent", s.lang)
    if step == "name":
        return tr("ask_name", s.lang)
    if step == "debt":
        return tr("ask_debt", s.lang)
    if step == "province":
        return tr("ask_province", s.lang, name=s.name, options=options_text("province", s.lang))
    if step == "term":
        return tr("ask_term", s.lang, options=options_text("term", s.lang))
    if step in ("marital", "review"):
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


def decline_below(pb):
    return pb.decline_below if pb else DEFAULT_DECLINE_BELOW


def estimate_text(s, pb, months):
    """Figure straight from the price book (never the AI), with an audit record of exactly what was shown."""
    amount = s.answers.get("debt_amount")
    if not pb or amount is None:
        return None
    q = pb.quote(amount, s.answers.get("province") == "GP", months)
    if not q:
        return None
    s.answers["term"] = months
    s.answers["estimate"] = {"monthly": q.monthly, "months": q.months, "bracket": q.bracket_label,
                             "gauteng": q.gauteng, "price_book": q.generated}
    return tr("estimate", s.lang, amount=money(q.monthly), months=q.months)


def restate_estimate(s):
    e = s.answers["estimate"]
    return tr("estimate", s.lang, amount=money(e["monthly"]), months=e["months"])


def assess(s):
    """Triage for the consultant only. Never shown to, or used to turn away, the prospect.

    DRAFT rules; refine with real outcomes. Under debt review needs the consultant to
    explain next steps first.
    """
    if s.answers.get("review") == "yes":
        return "unsure"
    return "likely"


def in_business_hours(now):
    local = now.astimezone(SAST)
    return local.weekday() < 5 and 8 <= local.hour < 17


# ---------------------------------------------------------------- engine
def handle(s, text, now, llm=None, pricebook=None, kind="text"):
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
        _after_not_fit(s, t, out, llm, pricebook)
        return out

    if s.status == "completed":
        _after_completion(s, t, out, llm, pricebook)
        return out

    if s.step == "new":
        s.step = "lang"
        out.messages.append(ask(s, "lang"))
        return out

    _answer_step(s, t, out, now, llm, pricebook)
    return out


def _after_completion(s, t, out, llm, pb):
    is_q = looks_like_question(t)
    if is_q or len(norm(t).split()) >= 4:  # a real message, not just "ok" / "thanks"
        ans, gap = _faq_or_cost(s, t, llm, pb)
        s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
        if ans:
            out.messages.append(ans)
            return
        out.messages.append(tr("faq_fallback" if is_q else "already_done", s.lang, name=s.name or "").strip())
        return
    s.notes.append("Client wrote after completing: " + t[:200])
    out.messages.append(tr("already_done", s.lang, name=s.name or ""))


def _faq_or_cost(s, t, llm, pb):
    """Fee questions are answered from the price book (never by the AI); everything else from the FAQ."""
    if is_cost_question(t):
        if s.answers.get("estimate"):
            return restate_estimate(s), False
        amount = s.answers.get("debt_amount")
        can_still_quote = pb and (amount is None or pb.can_quote(amount))
        if s.status == "active" and can_still_quote and s.step in ("lang", "consent", "name", "province", "debt", "term"):
            return tr("cost_need_info", s.lang), False
        note = "Asked about COST - consultant should open the call with the fee"
        if note not in s.notes:
            s.notes.append(note)
    return split_gap(llm.faq(t, s.lang) if llm else None)


def _answer_question(s, t, out, llm, step, pb):
    """Answer what they asked, log it, then gently return to the current question."""
    answer, gap = _faq_or_cost(s, t, llm, pb)
    s.notes.append(("Asked: " if answer and not gap else "UNANSWERED: ") + t[:200])
    out.messages.append((answer or tr("faq_fallback", s.lang).strip()) + "\n\n" + ask(s, step))


def _after_debt(s, out, amount, pb):
    """Debt amount accepted: decline, ask the term (if we can estimate), or hand the figure to a consultant."""
    s.answers["debt_amount"] = amount
    if amount < decline_below(pb):
        s.status = "not_fit"
        s.qualification = "not_fit"
        s.notes.append(f"Debt under R{decline_below(pb):,} - not a fit, no consultant call")
        out.messages.append(tr("not_fit", s.lang, name=s.name))
        out.events.append("not_fit")
    elif pb and pb.can_quote(amount):
        s.step = "term"
        out.messages.append(ask(s, "term"))
    else:
        s.step = "marital"
        s.notes.append("Debt outside estimate range - consultant to work out the figure")
        out.messages.append(tr("no_figure", s.lang) + "\n\n" + ask(s, "marital"))


def _answer_step(s, t, out, now, llm, pb):
    step = s.step

    # A genuine question is always answered first, even if it contains words that look like an answer.
    if step != "callback" and looks_like_question(t):
        _answer_question(s, t, out, llm, step, pb)
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
    elif step == "debt":
        amounts = sorted(set(all_amounts(t)))
        if len(amounts) > 1:  # a range, or several figures: we need one total, never a guess between rows
            out.messages.append(tr("one_figure", s.lang))
            return
        if amounts:
            s.fails = 0
            _after_debt(s, out, amounts[0], pb)
            return
    elif step == "term":
        months, out_of_range = parse_term(t)
        if months:
            figure = estimate_text(s, pb, months)
            if figure:
                s.fails, s.step = 0, "marital"
                out.messages += [figure, ask(s, "marital")]
                return
        elif out_of_range:
            out.messages.append(tr("term_range", s.lang))  # "nothing shorter or longer"; no exceptions offered
            return
    elif step == "callback":
        if not ("?" in t and len(t.split()) >= 5) and len(t) >= 2:
            s.answers["callback_raw"] = t[:200]
            s.answers["callback"] = (llm.normalise_callback(t, now) if llm else None) or t[:200]
            ok = True
    else:
        value = parse_choice(step, t) or (llm.classify(step, t, s.lang) if llm else None)
        if value:
            s.answers[step] = value
            ok = True

    # --- success: move on
    if ok:
        s.fails = 0
        if step == "callback":
            _finish(s, out, now)
        else:
            s.step = next_step(step)
            out.messages.append(ask(s, s.step))
        return

    # --- not an answer: if it's a real message, let the AI/FAQ respond before treating it as a failed answer
    if llm and len(norm(t).split()) >= 4 and step != "callback":
        answer, gap = _faq_or_cost(s, t, llm, pb)
        if answer:
            s.notes.append(("Asked: " if not gap else "UNANSWERED: ") + t[:200])
            out.messages.append(answer + "\n\n" + ask(s, step))
            return

    # --- not understood: a gentle re-ask, and hand over after repeated failures
    s.fails += 1
    if s.fails >= MAX_FAILS:
        s.status = "handover"
        s.notes.append(f"Bot could not understand answers at step '{step}'")
        out.messages.append(tr("handover", s.lang))
        out.events.append("handover")
        return
    if step == "lang" and s.fails >= 2:
        s.lang, s.step, s.fails = "en", "consent", 0  # default to English rather than stall
        out.messages.append(ask(s, "consent"))
        return
    out.messages.append(tr("reask", s.lang) + ask(s, step))


def _after_not_fit(s, t, out, llm, pb):
    """Let them correct the amount (it was only a rough estimate); otherwise answer questions politely."""
    amount = parse_amount(t)
    if amount and amount >= decline_below(pb):
        s.status, s.fails, s.qualification = "active", 0, ""
        s.notes.append(f"Corrected debt amount to R{amount:,}")
        _after_debt(s, out, amount, pb)
        return
    if looks_like_question(t):
        ans, gap = _faq_or_cost(s, t, llm, pb)
        s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
        if ans:
            out.messages.append(ans)
            return
    out.messages.append(tr("not_fit_followup", s.lang, name=s.name))


def _finish(s, out, now):
    s.status = "completed"
    s.qualification = assess(s)
    after = "" if in_business_hours(now) else tr("after_hours", s.lang)
    out.messages.append(tr("done", s.lang, name=s.name, callback=s.answers["callback_raw"], after=after))
    out.events.append("completed")
