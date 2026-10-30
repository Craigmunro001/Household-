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

## Next steps, in order
1. Craig: fee table (min/max per band) and how fees are paid (upfront / instalments / WellTech finance). Goes in config/fees.yaml.
2. Craig: the ~50 likely questions with answers, in batches of 10-15, any format. Best source: real lead questions from old chats.
   Claude formats them into knowledge/faq.md.
3. Craig: trust facts (attorney firm and how to verify, company details/address/website, any registrations) for "is this a scam?".
4. Claude: callback-time fix (weekend / after-hours check, offer next slot).
5. David Schoonraad: review every [DRAFT-VERIFY] answer in knowledge/faq.md and the fee wording in app/content.py.
   Especially: assets/car, credit record, prison, employer finding out (what is published and where), joint estates.
6. Native check: Afrikaans (Craig) and isiZulu (someone else) of all client-facing text.
7. Go live: Meta WhatsApp app + number (coexistence), Google service account, Railway deploy (see README). Own-number test, then small pilot.

## Open decisions for Craig
- Do you take on very small debts (e.g. R2 500)? What should the bot say?
- WellTech payroll deductions: if used, the employer is involved; bot wording about "will my employer find out" must match.
- Triage rule (LIKELY/UNSURE) is a placeholder: under debt review or debt under R100k = UNSURE.
- Keep or remove the first-name question (not one of the five).
- Alert emails: who receives them?
