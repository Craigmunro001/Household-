# Go-live checklist: Pinnacle WhatsApp lead assistant

Decision (3 Nov): the bot runs on its OWN dedicated WhatsApp number. The busy client line is not touched.

Run `python preflight.py` (and later `python preflight.py --url https://<your-railway-domain>`) at any point: it lists what is still missing and never prints secrets.

## Who does what
| # | Step | Who | Notes |
|---|------|-----|-------|
| 1 | Get the bot's number | Craig | A new SIM or a landline/VoIP number that can receive a verification SMS/voice call, **not** registered on WhatsApp. Keep it for the bot only. |
| 2 | Meta Business account + **business verification** | Craig | business.facebook.com. Verification needs your company documents (matches your "company documents only" rule). **Start this first: it can take days.** |
| 3 | Meta developer app (type Business) + WhatsApp product, add the number, verify it | Craig (Claude can guide screen by screen) | Set the display name to "Pinnacle Debt Solutions". |
| 4 | System User + **permanent token**; copy the Phone Number ID and the App Secret | Craig | Never paste these into chat or the repo. They go into Railway's variables. |
| 5 | Anthropic API key | Craig | console.anthropic.com. Optional but recommended: without it the bot still runs, but the FAQ AI is off. |
| 6 | Google service account + share the lead Sheet with its email | Craig | Enable the Sheets API. Paste the JSON into `GOOGLE_SERVICE_ACCOUNT_JSON` in Railway. |
| 7 | Alert mailbox (SMTP app password) + who receives alerts | Craig | `NOTIFY_TO`, `SMTP_*`. |
| 8 | Deploy to Railway, add a **volume** at `/data`, set variables from `.env.example`, `DB_PATH=/data/sessions.sqlite3`, **one instance only** | Claude (with your OK) or Craig | Conversations live in a SQLite file; more than one instance would split them. |
| 9 | In Meta: callback URL `https://<domain>/webhook`, your verify token, subscribe to `messages` | Craig | `preflight.py --url` checks the handshake first. |
| 10 | Test on your own phone in all three languages: tap buttons, type numbers, STOP, AGENT, a question, a Saturday call time, the recap + CHANGE | Craig + Claude | First time buttons run on a real phone. |
| 11 | Small pilot (a few real leads), then watch the Sheet's **Notes** column for `UNANSWERED` and `CORRECTION` | Craig | Grow `knowledge/faq.md` from real questions. |

## Must be settled before real leads
- [ ] The legal side has read: the asset warnings, "stop paying creditors on acceptance", the fee estimate + disclaimer wording, the debt-review comparison.
- [ ] A native speaker has read the Afrikaans; someone has read the isiZulu.
- [ ] POPIA housekeeping: Information Officer in place; a privacy notice you can link to; a note of who processes lead data (Meta/WhatsApp, Anthropic, Google, Railway, the mailbox provider), several of which are outside South Africa; a retention rule (e.g. how long not-fit leads stay in the Sheet). Ask your compliance adviser.
- [ ] Who reads the alert emails, and who confirms out-of-hours call-back requests.
- [ ] Meta policy: the bot is a narrow lead-qualification assistant (its AI only answers from your approved Q&As). Meta's rules (effective 15 Jan 2026) bar *general-purpose* AI assistants from WhatsApp Business; business bots using AI for customer service appear to be fine. Read Meta's current WhatsApp Business Solution Terms yourself to be sure.

## Day-one watch list
- `/health` shows `llm: true`, `sheet: GoogleSheetSink`, and the price-book date.
- Sheet columns **Status / Qualification / Notes**; email subjects "New qualified lead", "Lead wants a person", "URGENT: distressed lead", "Lead flagged a correction".
- Count `not_fit` rows by reason (debt / home / vehicle / assets) for the first two weeks, and tell whoever runs the ads.

## Rollback
Set the Meta webhook subscription off (or pause the Railway service). The client line is unaffected because the bot has its own number.
