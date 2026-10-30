# Pinnacle WhatsApp lead assistant

Greets social-media leads on WhatsApp 24/7, asks the qualifying questions in English, Afrikaans or isiZulu,
records the lead in a Google Sheet and emails a consultant to call at the time the prospect chose.

```
WhatsApp Cloud API -> /webhook (FastAPI on Railway) -> flow engine -> Google Sheet + email alert
                                                          \-> Claude (understands free text, answers FAQ)
```

**Design rule:** code owns the questions, qualification triage and fee wording. Claude never decides
a price or whether someone "qualifies"; it only helps understand replies and answer general questions
from `knowledge/faq.md`. If Claude is down or unconfigured the bot still works.

## Try it now (no WhatsApp needed)
```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
python simulator.py --no-llm        # add ANTHROPIC_API_KEY and drop --no-llm to test the AI parts
pytest
```

## What you control
| File | Purpose |
|---|---|
| `app/content.py` | Every client-facing message (3 languages), debt bands, answer options |
| `config/fees.yaml` | Fee range per debt band. **Empty = bot quotes no fee.** Fill in after testing |
| `knowledge/faq.md` | The only facts the AI may use. Needs David's sign-off |
| `app/flow.py` `assess()` | Lead triage (LIKELY/UNSURE) shown to consultants only |

## Safety built in
- Opens by saying it is an AI, with a POPIA notice; nothing is asked until the prospect replies YES.
- STOP at any time opts out (only an explicit START brings them back).
- Self-harm language (EN/AF/ZU) -> helpline numbers sent, bot goes quiet, URGENT email. **Verify the helpline numbers before launch.**
- "Agent / speak to a person", or 3 misunderstood answers -> bot goes quiet and a consultant is alerted.
- Fees only ever come from `fees.yaml`; any AI reply containing money amounts is discarded.
- Nobody is auto-rejected: every completed lead goes to a consultant.
- Webhook signatures are verified; duplicate deliveries are ignored.

## Going live
1. **Meta**: developers.facebook.com -> create app (Business) -> add WhatsApp. Add your existing WhatsApp Business
   app number using Meta's *coexistence* option so it keeps working on your phone while the bot handles the API
   (confirm the current requirements in Meta's onboarding). Create a permanent System User token.
2. **Google**: create a service account, enable the Sheets API, share the target Sheet with the service account's email.
3. **Railway**: deploy this repo, add a volume mounted at `/data` and set `DB_PATH=/data/sessions.sqlite3`,
   and set the variables from `.env.example` in Railway (never in the repo, never in chat).
4. **Webhook**: in Meta set callback URL `https://<railway-domain>/webhook` and your verify token; subscribe to `messages`.
5. **Test** with your own number in all three languages, including STOP, a person request and a question.
6. **Before real leads**: David approves `knowledge/faq.md` and the wording in `content.py`; a native speaker
   reads the Afrikaans and isiZulu.

## Not built yet
- Voice-note transcription (bot currently asks them to type).
- Follow-up nudges to leads who go quiet (needs approved WhatsApp templates once past the 24h window).
- Calendar booking, CRM sync, WhatsApp alert to consultants (email for now).
- Fee sliding scale: add bands in `content.py` and fees in `fees.yaml`.
