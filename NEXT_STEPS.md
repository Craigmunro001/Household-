# Handoff: where we stopped (30 Oct 2026)

## Built and pushed (branch claude/whatsapp-chatbot-pinnacle-leads-wm09f4, 70 tests passing)
- WhatsApp Cloud API webhook, conversation engine, Google Sheet lead capture, email alerts, terminal simulator.
- Languages: English, Afrikaans, isiZulu. Switches automatically if the lead writes in another language.
- Craig's 5 questions: debt (R bands or typed amount), marital status, province, debt review/counselling, call time.
- Questions are always answered first (from knowledge/faq.md), then the bot returns to its question.
- Fee questions are answered from config/fees.yaml only (never by the AI). Table is EMPTY, so no fee is quoted yet.
- Unanswered questions are logged as "UNANSWERED" in the lead's Notes; cost questions are flagged for the consultant.
- Safety: AI disclosure + POPIA notice, STOP, self-harm escalation, AGENT handover, spouse/marital mismatch flag.

## Test-run findings (all fixed unless noted)
- Fixed: questions phrased as requests ("please tell me...") were ignored; answer words inside questions were misread.
- Fixed: language switching; cost flag; partial answers marked [GAP].
- OPEN: bot accepted "08h00 tomorrow" when tomorrow was Saturday. Needs date/weekday check, offer next slot (Claude to build).
- OPEN: replies are too long for WhatsApp; split into shorter messages.
- Not tested live: the real Claude layer (no API key in this environment), real WhatsApp, real Google Sheet.

## Price book (2 Nov) - DONE
- config/fees.yaml now holds Craig's generated tables (Gauteng / outside Gauteng x 19 brackets x 25/30/36 months). Arithmetic-checked: every figure = total / months, brackets contiguous, no typos found.
- Flow is now: language, consent, name, province, debt (exact amount), term (25/30/36), then the estimate with the mandatory disclaimer, then marital, debt review, call time.
- Under R100 000: kindly declined. R100 000-R120 000 and over R500 000: no figure, consultant works it out.
- Open points flagged to Craig: bracket edges (exactly R140 000 goes to the HIGHER bracket); firm described as "debt-review firm" in the pasted spec (wrong word for a VSE business, and "debt review" is a regulated activity); FAQ conflict on whether cars/property can be sold; email address not collected (WhatsApp number only) - decide.

## Asset rule (3 Nov) - DONE (revised twice: warn first, lead decides; warning comes IMMEDIATELY)
- "Do you own a home (bonded or not)?" Yes -> immediate friendly warning BEFORE any vehicle question: a trustee is appointed for the creditors and the home would be sold, usually by auction, to pay part of the debts; "Would you like to continue?". Continue -> then the vehicle question. No -> ends politely (reply CONTINUE later, or say they misread and the question is re-asked).
- "Do you have a vehicle still under finance?" Yes -> its own warning (the bank would most likely take it back). Same continue/decline handling.
- Acknowledgements recorded separately per asset with timestamps (Sheet column "Asset warning accepted"; alert email says what they were told). Triage = UNSURE for consultant.
- CONFIRMED by Craig: a home owner who accepts the home warning ALWAYS gets the vehicle question next.
- Vehicle question now has 3 choices: 1 financed, 2 no vehicle, 3 vehicle fully paid off. Financed -> "the bank will take it back" warning (continue/decline). Paid off -> neutral note ("a different situation, your consultant will talk you through the options"), no warning, flagged to the consultant in the Sheet/email.
- LEGAL NOTE (Claude, for David): Craig mentioned a possible "plan" for a paid-off car such as putting it in a spouse's name. The bot deliberately says nothing like that and never promises a plan. Moving assets around shortly before a sequestration can be attacked as a disposition without value / voidable preference / collusive dealing under the Insolvency Act, and concealing assets can be an offence. David should vet exactly what consultants may advise on this, and it should never be scripted into the bot or ads.
- OPEN: price book does not mention assets; confirm the estimate is valid for asset owners.
- OPEN: bot warning is a record, NOT a substitute for the consultant's own explanation/consent. David to confirm what the consultant must still do.
- OPEN: wording "sold, usually by auction" / "taken back by the bank": David to approve.

## After-hours handover (3 Nov) - DONE
- If a lead asks for a person outside Mon-Fri 08:00-17:00 SAST, the bot says the team is resting until tomorrow/Monday/08:00 this morning, keeps helping and carries on with the questions (or asks what time suits if already completed, then updates the call time). A second request hands over for real with the return time. In business hours it hands over immediately as before. Consultant gets an email either way (different subjects).
- chat.py has --at <SAST time> to test after-hours behaviour.
- STILL TO DO (call-time handling): accept a bare "2" as 2pm; store the call time as a real date ("Tue 3 Nov, 15:00") for the consultant; never confirm a Saturday/Sunday/after-hours call time (offer the next slot).

## Call-back time + friendlier wording (3 Nov) - DONE
- Call-time question offers: 1) next working day 08:00, 2) next working day 10:00, 3) another day or time; or type a day+time in EN/AF/ZU ("Friday at 4pm", "tomorrow after 2pm", "Dinsdag om 3nm"). Stored as an exact label ("Wed 4 Nov, 10:00") in the Sheet and email.
- A bare time ("10", "9am") never gets guessed: the options are shown again. A day with no time asks for the time.
- Saturday / Sunday / evening / before 08:00 requests ARE accepted but recorded as a *preferred time* and flagged ("OUTSIDE standard hours") for the consultant to confirm or suggest the nearest time. The bot never promises an out-of-hours call.
- Every question has a friendly lead-in using the lead's name, and "Only N questions left." appears from 5 down (term question counted only when we can estimate).
- Afrikaans/isiZulu lead-ins and call-time wording are drafts for native speakers to check.
- Known polish: after a bare "10" the options message repeats its opening sentence.

## Recap + WhatsApp buttons (3 Nov) - DONE
- End of chat: confirmation message, then a plain recap (province, debt, home, vehicle, married, debt review, call time; never the fee figure). "Reply CHANGE" -> asks what to fix and flags it to the consultant (email subject "Lead flagged a correction"); a new call time typed after CHANGE is applied directly.
- WhatsApp buttons: numbered options become reply buttons (2-3 short options) or a list (4-10) automatically; the option NUMBER is the id so a tap = typing that number (no flow changes). Long labels use curated short titles; full wording goes in list row descriptions. If WhatsApp rejects an interactive message the same words are sent as text. Typing always still works.
- Limits used (confirmed from Meta's developer docs on 3 Nov): buttons max 3, title 20, body 1024; lists max 10 rows, row title 24, description 72, button label 20, body 4096.
- NOT TESTED LIVE: real WhatsApp delivery of buttons/lists (no credentials in this environment). Interactive replies only work inside the 24h customer-service window, which is always true for replies.
- chat.py --wa shows how a lead sees each message.

## Trust ("is this a scam?") - DONE (3 Nov), decisions by Craig
- NO attorney or personal names anywhere in the chat; only company documents may be shared (via the consultant on the call). Optional: Craig may share the CK number: set COMPANY_REG_NUMBER in app/content.py and it is appended to the answer automatically.
- Facts the bot may state (from Craig): in business since 2016; advertised on East Coast Radio (KZN) for 3 years, Vuma FM (KZN) for over a year, Hot FM (Gauteng) for 2 years. Worded factually; it must not imply the stations endorse Pinnacle.
- "Is this a scam / are you legit / can I trust you / who are you" gets a FIXED approved answer (not the AI) in EN/AF/ZU, at any stage of the chat, ending with "type AGENT". No registrations, regulators or approvals are claimed.
- "Am I speaking to a real person / are you a bot?" gets a FIXED honest answer (it is an AI) and is no longer mistaken for a request to speak to someone (this was a bug).
- The AI now sees only clean Q&A text (no internal notes, names or tags) and is told never to name any attorney, firm or staff member.
- CONFIRMED by Craig (3 Nov): the radio history is ADVERTISING (East Coast Radio 3 yrs, Hot FM 2 yrs, Vuma FM just over 1 yr). Wording: "we've advertised on ...". It shows an established business; it is not a regulator's approval or the stations' endorsement and must never be presented as one.

## FAQ batch 1 (Craig, 3 Nov)
- Q1 "Why is this better than debt review?" -> loaded as "the main differences" (debt review can tie you in for 5 years or more [Craig changed 7 to 5 on 3 Nov]; you keep paying interest, sometimes lowered; the debt review flag stays until the whole process is completed). Framed as differences, not "better", with the balancing line that voluntary surrender has its own consequences. This one is Craig's call (the attorney is not involved in debt review). Added follow-up "I'm under debt review, should I cancel?" -> the bot never advises cancelling or stopping payments.

## Next steps, in order
1. Craig: the ~50 questions and answers, in batches of 10-15 (best source: real lead questions).
2. Craig: trust facts (attorney firm and how to verify, company details/address/website, registrations) for "is this a scam?".
3. Claude: callback-time fix (weekend / after-hours check, offer next slot).
4. David Schoonraad: review every [DRAFT-VERIFY] and [CONFLICT-CHECK] answer in knowledge/faq.md, the estimate/disclaimer wording and the "interest free / total never grows" claims.
5. Native check: Afrikaans (Craig) and isiZulu (someone else) of all client-facing text, including the translated disclaimer.
6. Go live: Meta WhatsApp app + number (coexistence), Google service account, Railway deploy (see README). Own-number test, then small pilot.

## Decisions made by Craig
- Lead under debt review: the bot just carries on to the call booking (no note); the consultant is told via the UNSURE triage and the debt-review line in the Sheet/email. (3 Nov)

## Open decisions for Craig
- Under-R100k wording is a draft: David to approve. Should the bot point them to a free alternative (e.g. NCR / a registered debt counsellor)? That is advice, so only with approval.
- Marketing: put "debt over R100 000" in the ad copy so you stop paying for leads that can't be served.
- Triage rule (LIKELY/UNSURE) is a placeholder: under debt review = UNSURE.
- Keep or remove the first-name question (not one of the five).
- Alert emails: who receives them? Collect an email address from the lead as well as the WhatsApp number?
