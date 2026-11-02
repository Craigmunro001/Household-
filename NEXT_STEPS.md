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
- DECISION TO CONFIRM: after a lead accepts the HOME warning we still ask the vehicle question (the consultant needs it and the vehicle has its own consequence). Craig said "don't go onto the vehicle side" - read as "not before warning". If he wants the vehicle question skipped for home owners, it is a one-line change.
- OPEN: price book does not mention assets; confirm the estimate is valid for asset owners.
- OPEN: bot warning is a record, NOT a substitute for the consultant's own explanation/consent. David to confirm what the consultant must still do.
- OPEN: wording "sold, usually by auction" / "taken back by the bank": David to approve.

## After-hours handover (3 Nov) - DONE
- If a lead asks for a person outside Mon-Fri 08:00-17:00 SAST, the bot says the team is resting until tomorrow/Monday/08:00 this morning, keeps helping and carries on with the questions (or asks what time suits if already completed, then updates the call time). A second request hands over for real with the return time. In business hours it hands over immediately as before. Consultant gets an email either way (different subjects).
- chat.py has --at <SAST time> to test after-hours behaviour.
- STILL TO DO (call-time handling): accept a bare "2" as 2pm; store the call time as a real date ("Tue 3 Nov, 15:00") for the consultant; never confirm a Saturday/Sunday/after-hours call time (offer the next slot).

## Next steps, in order
1. Craig: the ~50 questions and answers, in batches of 10-15 (best source: real lead questions).
2. Craig: trust facts (attorney firm and how to verify, company details/address/website, registrations) for "is this a scam?".
3. Claude: callback-time fix (weekend / after-hours check, offer next slot).
4. David Schoonraad: review every [DRAFT-VERIFY] and [CONFLICT-CHECK] answer in knowledge/faq.md, the estimate/disclaimer wording and the "interest free / total never grows" claims.
5. Native check: Afrikaans (Craig) and isiZulu (someone else) of all client-facing text, including the translated disclaimer.
6. Go live: Meta WhatsApp app + number (coexistence), Google service account, Railway deploy (see README). Own-number test, then small pilot.

## Open decisions for Craig
- Under-R100k wording is a draft: David to approve. Should the bot point them to a free alternative (e.g. NCR / a registered debt counsellor)? That is advice, so only with approval.
- Marketing: put "debt over R100 000" in the ad copy so you stop paying for leads that can't be served.
- Triage rule (LIKELY/UNSURE) is a placeholder: under debt review = UNSURE.
- Keep or remove the first-name question (not one of the five).
- Alert emails: who receives them? Collect an email address from the lead as well as the WhatsApp number?
