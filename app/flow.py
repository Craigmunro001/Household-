"""The conversation engine.

Code owns the flow, the qualification logic and the fee wording. The LLM (optional) only
helps understand free-text answers and answer general questions from the approved FAQ.
`handle()` is pure apart from mutating the session, so it is easy to test.
"""
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from . import callback as cb
from .pricing import load_pricebook
from .content import (
    AGENT_PHRASES, AI_QUESTION_PHRASES, CHANGE_PHRASES, CHANGED_MIND_PHRASES, CORRECTION_WORDS, COST_PHRASES, DISTRESS_PHRASES, NO_WORDS, OPTIONS, REQUEST_STARTS, START_WORDS, STOP_PHRASES,
    COMPANY_REG_NUMBER, LEADS, M, ALL_DEBTS_PHRASES, EXCLUSION_PHRASES, MISSED_PHRASES, OPTIONS, PAYMENT_PHRASES, PAYOFF_PHRASES, QUESTIONISH, SUMMONS_PHRASES, TERMS, TRUST_PHRASES, WHEN, YES_WORDS, money, options_text, tr,
)

SAST = timezone(timedelta(hours=2))
STEPS = ["lang", "consent", "name", "province", "debt", "home", "home_ack", "vehicle", "vehicle_ack", "term", "marital", "review", "callback"]
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


def _is_question_shaped(text):
    t = norm(text)
    first = t.split()[0] if t.split() else ""
    return "?" in text or first in QUESTION_WORDS or any(t.startswith(r) for r in REQUEST_STARTS) or has_phrase(text, QUESTIONISH)


def is_missed_payment_question(text):
    return has_phrase(text, MISSED_PHRASES) and _is_question_shaped(text)


def is_exclusion_question(text):
    """SARS / maintenance / fines / municipal / 'which debts are excluded': only when phrased as a question."""
    return has_phrase(text, EXCLUSION_PHRASES) and _is_question_shaped(text)


def is_all_debts_question(text):
    """Only when it is actually phrased as a question or request: 'all debts' also appears in plain answers."""
    if not has_phrase(text, ALL_DEBTS_PHRASES):
        return False
    t = norm(text)
    first = t.split()[0] if t.split() else ""
    return "?" in text or first in QUESTION_WORDS or any(t.startswith(r) for r in REQUEST_STARTS) or has_phrase(text, QUESTIONISH)


def is_summons_question(text):
    return has_phrase(text, SUMMONS_PHRASES)


def is_payoff_question(text):
    return has_phrase(text, PAYOFF_PHRASES)


def is_payment_question(text):
    return has_phrase(text, PAYMENT_PHRASES)


def is_ai_question(text):
    return has_phrase(text, AI_QUESTION_PHRASES)


def is_trust_question(text):
    return has_phrase(text, TRUST_PHRASES)


def trust_text(lang):
    reg = tr("trust_reg", lang, reg=COMPANY_REG_NUMBER) if COMPANY_REG_NUMBER else ""
    return tr("trust", lang, reg=reg)


def looks_like_question(text):
    t = norm(text)
    words = t.split()
    if len(words) < 3:
        return False  # "yes?" / "no?" are answers, not questions
    t = " ".join(words)
    if is_cost_question(t) or is_trust_question(t) or is_ai_question(t) or is_payment_question(t) or is_payoff_question(t) or is_summons_question(t) or is_all_debts_question(t) or is_exclusion_question(t) or is_missed_payment_question(t) or any(t.startswith(r) for r in REQUEST_STARTS):
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


def requested_months(text):
    """The number of months a lead asked for ('48', '60 months', '5 years', '2.5 years'), or None."""
    t = norm(text)
    m = re.search(r"\b(\d{1,3}(?:[.,]\d)?)\b", text.lower().replace(",", "."))
    if not m:
        return None
    n = float(m.group(1))
    if re.search(r"\b(year|years|yr|yrs|jaar|nyaka|unyaka|iminyaka)\b", t):
        n *= 12
    return int(n) if n == int(n) else None


def parse_term(text):
    """-> (months, out_of_range). Only 25, 30 or 36 are valid; any other number outside 25-36 is 'out of range'."""
    t = norm(text)
    if t in ("1", "2", "3"):
        return TERMS[int(t) - 1], False
    n = requested_months(text)
    if n is None:
        return None, False
    if n in TERMS:
        return n, False
    return None, not (25 <= n <= 36)


# ---------------------------------------------------------------- messages
QUESTION_ORDER = ["province", "debt", "home", "vehicle", "term", "marital", "review", "callback"]
_DEFAULT_PB = None


def _can_quote(amount, pb):
    global _DEFAULT_PB
    if pb is None:
        _DEFAULT_PB = _DEFAULT_PB or load_pricebook()
        pb = _DEFAULT_PB
    return bool(pb and pb.can_quote(amount))


def questions_left(s, step, pb=None):
    """How many questions remain, counting this one (the term question is skipped when we cannot estimate)."""
    order = list(QUESTION_ORDER)
    amount = s.answers.get("debt_amount")
    if amount is not None and not _can_quote(amount, pb):
        order.remove("term")
    return len(order) - order.index(step) if step in order else 0


def lead_in(s, step, pb=None):
    parts = [LEADS[step][s.lang].format(name=s.name)]
    n = questions_left(s, step, pb)
    if 2 <= n <= 5:
        parts.append(tr("progress", s.lang, n=n))
    return " ".join(parts)


def ask(s, step, lead=False, pb=None):
    """The question for a step. lead=True adds the friendly lead-in and progress count (moving forward, not re-asking)."""
    if step == "lang":
        return tr("welcome_all", "en", options=options_text("lang", "en"))
    if step == "consent":
        return tr("consent", s.lang)
    if step == "name":
        return tr("ask_name", s.lang)
    if step in ("home_ack", "vehicle_ack"):
        return tr(f"ask_{step}", s.lang, name=s.name, options=options_text(step, s.lang))
    if step == "debt":
        body = tr("ask_debt", s.lang)
    elif step == "term":
        body = tr("ask_term", s.lang, options=options_text("term", s.lang))
    elif step == "callback":
        now = datetime.fromisoformat(s.updated_at) if s.updated_at else datetime.now(timezone.utc)
        body = tr("ask_callback", s.lang, d=cb.day_label(cb.next_working_day(now), now, s.lang))
    elif step in ("province", "marital", "review", "home", "vehicle"):
        body = tr(f"ask_{step}", s.lang, options=options_text(step, s.lang))
    else:
        raise ValueError(step)
    return f"{lead_in(s, step, pb)} {body}" if lead and step in LEADS else body


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
    if s.answers.get("review") == "yes" or s.answers.get("asset_ack"):
        return "unsure"
    return "likely"


def in_business_hours(now):
    local = now.astimezone(SAST)
    return local.weekday() < 5 and 8 <= local.hour < 17


def next_available(now, lang):
    """When the team is next back, in words: this morning / tomorrow / Monday."""
    local = now.astimezone(SAST)
    if local.weekday() < 5 and local.hour < 8:
        key = "today"
    elif local.weekday() in (0, 1, 2, 3, 6):  # Mon-Thu, Sun: the next day is a working day
        key = "tomorrow"
    else:                                       # Fri after hours, Saturday
        key = "monday"
    return WHEN[key][lang]


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
    if s.step != "new" and s.status != "not_fit" and wants_agent(t) and not is_ai_question(t):
        where = "after completing the questions" if s.status == "completed" else f"at step '{s.step}'"
        when = next_available(now, s.lang)
        if not in_business_hours(now) and not s.answers.get("agent_after_hours"):
            # Team is resting: keep helping instead of going silent, and promise a call-back when they are back.
            s.answers["agent_after_hours"] = True
            s.notes.append(f"Asked for a person {where} after hours - bot continuing; consultant to call {when}")
            msg = tr("agent_after_hours", s.lang, when=when)
            if s.status == "completed":
                s.answers["awaiting_callback"] = True
                msg += "\n\n" + tr("agent_after_hours_time", s.lang)
            else:
                msg += "\n\n" + ask(s, s.step)
            out.messages.append(msg)
            out.events.append("person_requested")
            return out
        s.status = "handover"
        s.notes.append(f"Asked for a person {where}")
        out.messages.append(tr("handover" if in_business_hours(now) else "handover_after_hours", s.lang, when=when))
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
    if s.answers.pop("awaiting_correction", False) and len(t) >= 2:
        now = datetime.fromisoformat(s.updated_at)
        parsed = cb.parse_callback(t, now, s.lang)
        if parsed.kind == "slot":  # it is a new call time: just apply it
            in_hours = _record_callback(s, parsed, t, now)
            shown = s.answers["callback"] + ("" if in_hours else tr("callback_outside", s.lang))
            s.notes.append(f"Call time changed by lead to: {s.answers['callback']}")
            out.messages.append(tr("callback_updated", s.lang, name=s.name, callback=shown))
            out.events.append("callback_updated")
        else:
            s.notes.append(f"CORRECTION requested by lead: {t[:300]}")
            out.messages.append(tr("correction_thanks", s.lang))
            out.events.append("correction_requested")
        return
    if has_phrase(t, CHANGE_PHRASES) and len(norm(t).split()) <= 12 and not s.answers.get("awaiting_callback"):
        s.answers["awaiting_correction"] = True
        out.messages.append(tr("ask_correction", s.lang))
        return
    if s.answers.pop("awaiting_callback", False) and not is_q and len(t) >= 2:
        now = datetime.fromisoformat(s.updated_at)
        parsed = cb.parse_callback(t, now, s.lang)
        if parsed.kind == "slot":
            in_hours = _record_callback(s, parsed, t, now)
            shown = s.answers["callback"] + ("" if in_hours else tr("callback_outside", s.lang))
        else:
            s.answers.update(callback=tr("callback_unclear", s.lang, raw=t[:100]), callback_raw=t[:200], callback_in_hours=False)
            s.notes.append(f"Call time update not understood, taken as typed: {t[:100]} - consultant to confirm")
            shown = s.answers["callback"]
        s.notes.append(f"Call time updated to: {s.answers['callback']}")
        out.messages.append(tr("callback_updated", s.lang, name=s.name, callback=shown))
        out.events.append("callback_updated")
        return
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
    """Fee questions come from the price book and "is this a scam?" from approved fixed wording (never the AI);
    everything else from the FAQ."""
    if is_ai_question(t):  # honesty about what it is never depends on the AI
        return tr("am_i_ai", s.lang), False
    if is_payment_question(t):  # the sequence matters: wrong wording here makes people stop paying too early
        return tr("payments", s.lang), False
    if is_payoff_question(t):
        return tr("payoff", s.lang), False
    if is_missed_payment_question(t):  # kind, honest, and never reads as permission to skip a payment
        note = "Asked what happens if a payment is missed - worry about affordability: check it on the call"
        if note not in s.notes:
            s.notes.append(note)
        return tr("missed_payment", s.lang), False
    if is_exclusion_question(t):  # never list or explain them: the consultant covers it
        return tr("exclusions", s.lang), False
    if is_all_debts_question(t):
        return tr("all_debts", s.lang), False
    if is_summons_question(t):
        note = "Lead mentions a summons or judgment - consultant to get the details of the accounts"
        if note not in s.notes:
            s.notes.append(note)
        return tr("summons", s.lang), False
    if is_trust_question(t):
        return trust_text(s.lang), False
    if is_cost_question(t):
        if s.answers.get("estimate"):
            return restate_estimate(s), False
        amount = s.answers.get("debt_amount")
        can_still_quote = pb and (amount is None or pb.can_quote(amount))
        if s.status == "active" and can_still_quote and s.step in ("lang", "consent", "name", "province", "debt", "home", "home_ack", "vehicle", "vehicle_ack", "term"):
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


def _decline(s, out, reason, note, message):
    s.status, s.qualification = "not_fit", "not_fit"
    s.answers["not_fit_reason"] = reason
    s.notes.append(note)
    out.messages.append(message)
    out.events.append("not_fit")


def _after_debt(s, out, amount, pb):
    """Debt amount accepted: decline if too small, otherwise on to the asset questions."""
    s.answers["debt_amount"] = amount
    if amount < decline_below(pb):
        _decline(s, out, "debt", f"Debt under R{decline_below(pb):,} - not a fit, no consultant call",
                 tr("not_fit", s.lang, name=s.name))
    else:
        s.step = "home"
        out.messages.append(ask(s, "home", lead=True, pb=pb))


def _after_assets(s, out, pb):
    """No home and no financed vehicle: ask the term (if we can estimate), or leave the figure to a consultant."""
    amount = s.answers["debt_amount"]
    if pb and pb.can_quote(amount):
        s.step = "term"
        out.messages.append(ask(s, "term", lead=True, pb=pb))
    else:
        s.step = "marital"
        s.notes.append("Debt outside estimate range - consultant to work out the figure")
        out.messages.append(tr("no_figure", s.lang) + "\n\n" + ask(s, "marital", lead=True, pb=pb))


def _asset_answer(s, out, step, value, pb):
    """home / vehicle. Owning either triggers an immediate, friendly warning; nothing else is asked until they choose."""
    s.answers[step] = value
    if value == "yes":
        s.step = f"{step}_ack"
        out.messages.append(ask(s, s.step))
    elif step == "home":
        s.step = "vehicle"
        out.messages.append(ask(s, "vehicle", lead=True, pb=pb))
    else:
        _after_assets(s, out, pb)
        if value == "paid_off":  # a different situation: no warning, no promise; the consultant covers the options
            s.notes.append("Has a fully paid-off vehicle - consultant to discuss options")
            out.messages[-1] = tr("vehicle_paid_off", s.lang) + "\n\n" + out.messages[-1]


def _accept_asset_risk(s, out, pb, which):
    """They were warned (home -> trustee sells it, vehicle -> bank takes it back) and still want to go ahead."""
    s.answers.setdefault("asset_ack", {})[which] = {"at": s.updated_at}
    s.notes.append(f"WARNED about their {which} ({'sold by the trustee, usually at auction' if which == 'home' else 'taken back by the bank'}); "
                   "chose to continue - consultant to assess")
    if which == "home":
        s.step = "vehicle"
        out.messages.append(ask(s, "vehicle", lead=True, pb=pb))
    else:
        _after_assets(s, out, pb)


def _answer_step(s, t, out, now, llm, pb):
    step = s.step

    if step == "callback":
        _answer_callback(s, t, out, now, llm, pb)
        return

    # A genuine question is always answered first, even if it contains words that look like an answer
    # (but a debt amount like "250000, all my debts" is an answer).
    if looks_like_question(t) and not (step == "debt" and all_amounts(t) and "?" not in t):
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
        if n == "1" or n in YES_WORDS or (words and words[0] in YES_WORDS):
            s.consent_at, ok = s.updated_at, True
        elif n == "2" or n in NO_WORDS:
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
                out.messages += [figure, ask(s, "marital", lead=True, pb=pb)]
                return
        elif out_of_range:
            longer = (requested_months(t) or 0) > max(TERMS)  # why we can't go longer vs how to finish sooner; no exceptions offered
            out.messages.append(tr("term_range_long" if longer else "term_range_short", s.lang))
            return
    else:
        value = parse_choice(step, t) or (llm.classify(step, t, s.lang) if llm else None)
        if value and step in ("home", "vehicle"):
            s.fails = 0
            _asset_answer(s, out, step, value, pb)
            return
        if value and step in ("home_ack", "vehicle_ack"):
            s.fails = 0
            which = step.removesuffix("_ack")
            if value == "yes":
                _accept_asset_risk(s, out, pb, which)
            else:
                s.answers["not_fit_asset"] = which
                _decline(s, out, "assets", f"Warned about their {which}; chose not to continue - no consultant call",
                         tr(f"not_fit_{which}", s.lang, name=s.name))
            return
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
            out.messages.append(ask(s, s.step, lead=True, pb=pb))
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
    """Let them correct the answer (the debt amount was only a rough estimate; or they misread an asset question)."""
    reason = s.answers.get("not_fit_reason", "debt")
    if reason == "assets":
        which = s.answers.get("not_fit_asset", "home")
        if has_phrase(t, CHANGED_MIND_PHRASES):  # changed their mind (explicitly: "ok thanks" does not count)
            s.status, s.fails, s.qualification = "active", 0, ""
            _accept_asset_risk(s, out, pb, which)
            return
        if has_phrase(t, CORRECTION_WORDS):         # they misread the question: ask it again
            s.status, s.step, s.fails, s.qualification = "active", which, 0, ""
            s.answers.pop(which, None)
            s.notes.append(f"Re-asked the {which} question after a correction")
            out.messages.append(ask(s, which))
            return
        if looks_like_question(t):
            ans, gap = _faq_or_cost(s, t, llm, pb)
            s.notes.append(("Asked: " if ans and not gap else "UNANSWERED: ") + t[:200])
            if ans:
                out.messages.append(ans)
                return
        out.messages.append(tr(f"not_fit_{which}_followup", s.lang, name=s.name))
        return
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


def _option_label(step, value, lang):
    return next(labels[lang] for v, labels, _ in OPTIONS[step] if v == value)


def recap_text(s):
    """A plain-words read-back of everything noted, so the lead can spot a mistake (and we show we listened)."""
    a, lang = s.answers, s.lang
    flexible = a.get("callback_flexible")
    return tr("recap", lang, name=s.name,
              province=_option_label("province", a["province"], lang) if a.get("province") else "-",
              debt=f"R{a['debt_amount']:,}".replace(",", "\u00a0") if a.get("debt_amount") else "-",
              home=M["recap_home"][a.get("home", "no")][lang],
              vehicle=M["recap_vehicle"][a.get("vehicle", "no")][lang],
              marital=M["recap_marital"][a.get("marital", "not_married")][lang],
              review=M["recap_review"][a.get("review", "unsure")][lang],
              callback=a.get("callback", "-") if not flexible else tr("callback_flexible", lang))


def _finish(s, out, now):
    s.status, s.step = "completed", "done"
    s.qualification = assess(s)
    if s.answers.get("callback_flexible"):
        out.messages.append(tr("done_flexible", s.lang, name=s.name))
    elif s.answers.get("callback_in_hours", True):
        out.messages.append(tr("done", s.lang, name=s.name, callback=s.answers["callback"], after=""))
    else:  # outside standard hours: a preferred time, never a promise
        out.messages.append(tr("done_flagged", s.lang, name=s.name, callback=s.answers["callback"]))
    out.messages.append(recap_text(s))
    out.events.append("completed")


def _upper_first(text):
    return text[:1].upper() + text[1:]


def _record_callback(s, parsed, raw, now):
    """Store the agreed call time. Anything outside standard hours is accepted but flagged: no promise is made."""
    label = cb.label(parsed, s.lang)
    in_hours = cb.in_standard_hours(parsed)
    s.answers.update(callback=label, callback_raw=raw[:200], callback_in_hours=in_hours,
                     callback_date=parsed.day.isoformat())
    s.answers.pop("callback_stage", None)
    s.answers.pop("callback_day", None)
    if not in_hours:
        s.notes.append(f"Callback requested OUTSIDE standard hours: {label} - consultant to confirm or suggest nearest time")
    return in_hours


CB_KEYS = ("cb_stage", "cb_day", "cb_time", "cb_confirm", "cb_attempts")


def _cb_reset(s):
    for k in CB_KEYS:
        s.answers.pop(k, None)


def _cb_day_options(s, now):
    picks = cb.day_picks(now)
    lines = [f"{i}. {_upper_first(cb.day_label(d, now, s.lang))}" for i, d in enumerate(picks, 1)]
    return "\n".join(lines + [f"{len(picks) + 1}. {tr('opt_another_day', s.lang)}"]), picks


def _cb_time_options(s):
    lines = [f"{i}. {cb.clock(h)}" for i, h in enumerate(cb.TIME_PICKS, 1)]
    return "\n".join(lines + [f"{len(cb.TIME_PICKS) + 1}. {tr('opt_other_time', s.lang)}"])


def _cb_ask_day(s, out, now, intro=""):
    s.answers["cb_stage"] = "day"
    options, _ = _cb_day_options(s, now)
    out.messages.append(tr("cb_ask_day", s.lang, intro=intro, options=options))


def _cb_ask_time(s, out, now, day):
    s.answers["cb_stage"], s.answers["cb_day"] = "time", day.isoformat()
    note = tr("callback_weekend_note", s.lang) if day.weekday() >= 5 else ""
    out.messages.append(tr("cb_ask_time", s.lang, day=_upper_first(cb.day_label(day, now, s.lang)),
                           options=_cb_time_options(s), note=note))


def _cb_current_prompt(s, now):
    """The question for whatever stage the lead is at (used after answering a side question)."""
    stage, a = s.answers.get("cb_stage"), s.answers
    if stage == "day":
        return tr("cb_ask_day", s.lang, intro="", options=_cb_day_options(s, now)[0])
    if stage == "time" and a.get("cb_day"):
        d = datetime.fromisoformat(a["cb_day"]).date()
        return tr("cb_ask_time", s.lang, day=_upper_first(cb.day_label(d, now, s.lang)), options=_cb_time_options(s), note="")
    if stage == "suggest":
        return tr("cb_suggest", s.lang)
    return ask(s, "callback")


def _cb_confirm(s, out, parsed, raw):
    s.answers["cb_stage"] = "confirm"
    s.answers["cb_confirm"] = {"day": parsed.day.isoformat(), "hour": parsed.hour, "minute": parsed.minute,
                               "period": parsed.period, "after": parsed.after, "raw": raw[:200]}
    note = "" if cb.in_standard_hours(parsed) else tr("cb_confirm_note", s.lang)
    out.messages.append(tr("cb_confirm", s.lang, label=cb.label(parsed, s.lang), note=note))


def _cb_flexible(s, out, now):
    _cb_reset(s)
    s.answers.update(callback=tr("callback_flexible", s.lang), callback_raw="consultant to suggest", callback_in_hours=True,
                     callback_flexible=True)
    s.notes.append("Lead asked the consultant to suggest a call time")
    _finish(s, out, now)


def _cb_book(s, out, now, parsed, raw):
    _cb_reset(s)
    _record_callback(s, parsed, raw, now)
    s.fails = 0
    _finish(s, out, now)


def _answer_callback(s, t, out, now, llm, pb):
    """Booking the call. Never asks the same thing twice: it repeats back what it understood and asks only
    for what is missing, narrows day then time with numbered picks, confirms typed times, and always offers
    a way out (let the consultant suggest a time)."""
    a, n = s.answers, norm(t)
    stage = a.get("cb_stage")
    day = datetime.fromisoformat(a["cb_day"]).date() if a.get("cb_day") else None
    tm = tuple(a["cb_time"]) if a.get("cb_time") else None
    yes, no = n == "1" or n in YES_WORDS, n == "2" or n in NO_WORDS

    if has_phrase(t, cb.FLEXIBLE_PHRASES) or (stage is None and n == "4"):
        return _cb_flexible(s, out, now)

    if stage == "suggest":
        if yes:
            return _cb_flexible(s, out, now)
        if no:
            _cb_reset(s)
            out.messages.append(ask(s, "callback"))
            return
    elif stage == "confirm":
        c = a["cb_confirm"]
        if yes:
            parsed = cb.Parsed("slot", datetime.fromisoformat(c["day"]).date(), c["hour"], c["minute"], c["period"], c["after"])
            return _cb_book(s, out, now, parsed, c["raw"])
        if no:
            _cb_reset(s)
            return _cb_ask_day(s, out, now)
        a.pop("cb_confirm", None)
        a.pop("cb_stage", None)  # they typed something new: treat it as a new request
        stage = None
    elif stage == "day" and n.isdigit():
        picks = cb.day_picks(now)
        i = int(n)
        if 1 <= i <= len(picks):
            if tm:
                return _cb_book(s, out, now, cb.Parsed("slot", picks[i - 1], tm[0], tm[1]), f"{picks[i - 1]} {tm}")
            return _cb_ask_time(s, out, now, picks[i - 1])
        if i == len(picks) + 1:
            out.messages.append(tr("cb_day_other", s.lang))
            return
    elif stage == "time" and n.isdigit() and day:
        i = int(n)
        if 1 <= i <= len(cb.TIME_PICKS):
            return _cb_book(s, out, now, cb.Parsed("slot", day, cb.TIME_PICKS[i - 1], 0), f"{day} {cb.TIME_PICKS[i - 1]}:00")
        if i == len(cb.TIME_PICKS) + 1:
            out.messages.append(tr("cb_time_other", s.lang))
            return
    elif stage is None and n in ("1", "2"):  # the two slots we offered up front
        return _cb_book(s, out, now, cb.slot(cb.next_working_day(now), 8 if n == "1" else 10), t)
    elif stage is None and (n == "3" or has_phrase(t, cb.OTHER_DAY_PHRASES)):
        return _cb_ask_day(s, out, now)

    typed = cb.parse_callback(t, now, s.lang)                 # what the text says on its own
    parsed = cb.parse_callback(t, now, s.lang, day, tm)       # ... combined with what we already know
    if parsed.kind == "slot":
        s.fails = 0
        if typed.day is not None and typed.kind == "slot":    # a full day+time typed freely: repeat it back first
            return _cb_confirm(s, out, parsed, t)
        return _cb_book(s, out, now, parsed, t)               # the day came from a pick, so the typed time is enough
    if parsed.kind == "day_only":
        return _cb_ask_time(s, out, now, parsed.day)
    if parsed.kind == "time_only":
        a["cb_time"] = [parsed.hour, parsed.minute]
        shown = cb.PERIOD_WORDS[parsed.period][s.lang] if parsed.period else cb.clock(parsed.hour, parsed.minute)
        return _cb_ask_day(s, out, now, tr("cb_intro_time", s.lang, time=shown))
    if parsed.kind == "past":
        a.pop("cb_time", None)
        return _cb_ask_day(s, out, now, tr("cb_intro_past", s.lang))

    # --- could not make sense of it
    if looks_like_question(t):
        answer, gap = _faq_or_cost(s, t, llm, pb)
        s.notes.append(("Asked: " if answer and not gap else "UNANSWERED: ") + t[:200])
        out.messages.append((answer or tr("faq_fallback", s.lang).strip()) + "\n\n" + _cb_current_prompt(s, now))
        return
    a["cb_attempts"] = a.get("cb_attempts", 0) + 1
    if a["cb_attempts"] == 1:                                  # 1st: walk them through it in two easy steps
        return _cb_ask_day(s, out, now, tr("cb_intro_guided", s.lang))
    if a["cb_attempts"] == 2:                                  # 2nd: offer to take the decision off their hands
        a["cb_stage"] = "suggest"
        out.messages.append(tr("cb_suggest", s.lang))
        return
    _cb_reset(s)                                               # 3rd: take their words and let the consultant sort it out
    a.update(callback=tr("callback_unclear", s.lang, raw=t[:100]), callback_raw=t[:200], callback_in_hours=False)
    s.notes.append(f"Callback request not understood, taken as typed: {t[:100]} - consultant to confirm")
    _finish(s, out, now)
