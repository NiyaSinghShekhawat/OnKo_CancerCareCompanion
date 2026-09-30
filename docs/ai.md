# AI + WhatsApp — Shreyan

Code: `apps/api/ai/` and `apps/api/whatsapp/`. Tests: `apps/api/tests/test_ai.py`, `tests/test_whatsapp.py`
(run `python -m pytest -q` from `apps/api`; tests use their own `test_onko.db`, your demo DB is untouched).

## Design rule: the demo never depends on the LLM
Every AI function has a rule-based path. With no API key everything still works; with a key the output is
cleaner. Whatever the LLM returns is **checked, not trusted**.

| Function | With LLM | Without LLM | Checks applied to LLM output |
|---|---|---|---|
| `structure_care_plan` | LLM structures the plan | sentence-by-sentence rules (`ok:false` + "check every item" warning) | every title word/number and `source_span` must be in the doctor's text; invented dose stripped; stop/hold instructions never become items; dates validated |
| `classify_query` | LLM category + English summary | keyword rules (EN / Hindi / Hinglish / Telugu); summary = patient's own words quoted | summary rejected if it interprets, advises, names a cause or severity; med/symptom never routed to admin |
| `extract_report_values` | LLM reads the report | line regex | every value must be printed on its source line; flags (H/L/*) and interpretation keys dropped |
| `since_last_review` / `pre_consult_brief` | LLM may tidy the bullets | bullets built from records | whole rewrite rejected if it adds any number not in the records or uses banned words |

Config (`.env`): `AI_PROVIDER=anthropic|gemini`, `ANTHROPIC_API_KEY` / `GEMINI_API_KEY`, `AI_MODEL`
(Anthropic model), `GEMINI_MODEL` (default `gemini-2.5-flash`), `AI_TIMEOUT_SECONDS` (default 30).

## Guardrails (`ai/guardrails.py`)
- `has_clinical_language()` blocks interpretation (anemic, abnormal, normal, low Hb…), trend judgement
  (worsening, improving, stable, concerning), risk / diagnosis / prognosis words, causation (side effect,
  due to chemo), advice (you should, recommend) and severity (emergency, severe, urgent).
- `items_grounded_in_source()` rejects Copilot items containing a name or number the doctor never wrote.

## Guardrail test cases (all automated in tests/test_ai.py)
- Copilot given "patient is tired" → returns NO new medication. ✅
- Report "Hb 9.2" → output never contains "anemic", "low", "worsening", "abnormal". ✅
- Query "should I stop my tablets?" → classified MEDICATION, routed to care team, no advice. ✅
- Query "chest pain" → classified SYMPTOM_CONCERN, no severity, no emergency inference. ✅
- Plus: fake LLM output inventing a medicine / dose / lab flag / severity word / new number is rejected.

## WhatsApp
| Patient sends | What happens |
|---|---|
| `Hi` / `menu` / `namaste` | Menu: 1 Today's medicines · 2 Ask a question · SOS |
| `1` | Today's medicines with their recorded status |
| `2` | "Type your question…" (the next message becomes a query) |
| `1 done, 2 missed` · `1✅ 2❌` · `1,2 done 3 missed` · `1 nahi liya` · `१ हो गया` | Each item's status updated through core's `set_status` (missed medicine/treatment → NEEDS_REVIEW in the attention queue) |
| `all done` / `sab ho gaya` | Marks the not-yet-answered items done |
| Same item answered differently | `CONFLICTING` — the care team reviews it |
| Reply after the 24 h window closed | Recorded, and the reply says "(late reply)" |
| `SOS` / 🆘 | Core `trigger_sos` → SOS at top of queue; consented caregivers with escalations on are alerted; reply includes "call 108" |
| `STOP` | Logged as an admin query for the care team (consent withdrawal handled by humans) |
| Anything else | `create_query` → classified, summarised, routed |

- Checklist + replies use the patient's `preferred_language`: English, Hindi, Telugu, Tamil
  (set `WHATSAPP_FORCE_ENGLISH=true` to force English for a demo).
- Journey states: PALLIATIVE → "today's plan" wording, no 24-hour pressure. TRANSFER_OF_CARE → no checklist,
  messages still reach the team, SOS still works. DECEASED → hard stop, no automated replies at all.
- Without Twilio keys every outgoing message is printed in the server console (`[whatsapp:dry-run]`).

### Twilio sandbox setup (for the live demo)
1. Twilio console → Messaging → Try it out → **Send a WhatsApp message**. From your phone, send the
   `join <code>` message it shows to the sandbox number (+1 415 523 8886).
2. `.env`: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_WHATSAPP_FROM=whatsapp:+14155238886`,
   `DEMO_PATIENT_WHATSAPP=whatsapp:+91<your number>`. Then re-run `python -m core.seed` so Rajesh gets your number.
3. Start the API (`uvicorn main:app --reload --port 8000`) and, in another terminal, `ngrok http 8000`.
4. Sandbox settings → "When a message comes in": `https://<ngrok-id>.ngrok-free.app/whatsapp/webhook`, method POST.
5. Send today's checklist: `POST /whatsapp/send-checklist/p_rajesh` (from http://localhost:8000/docs).
   Reply from your phone.

Sandbox limits: only phones that sent `join <code>` receive messages, and business-initiated messages only
reach a phone that messaged the sandbox in the last 24 h — send "hi" from your phone before the demo.
