# OnKo API Contract (v1)

**FROZEN after Phase 0.** To change anything here: post in the group chat, all three agree, one person edits, everyone pulls.

Base URL: `http://localhost:8000`
All requests send header `X-Role: doctor | patient | caregiver | care_team` and `X-User-Id: <id>` (simple demo auth).
Shapes of every entity live in `schemas.json`. AI output shapes live in `ai_outputs.json`.

---

## Patients — owner: Samprada (`core/routers/patients.py`)
| Method | Path | Returns |
|---|---|---|
| GET | `/patients` | `Patient[]` (registry, filter `?status=` `?q=`) |
| GET | `/patients/{id}` | `Patient` |
| GET | `/patients/{id}/timeline` | `CareEvent[]` sorted by `scheduled_at` |
| GET | `/patients/{id}/360` | `Patient360` |
| PATCH | `/patients/{id}/journey-state` | body `{ state, reason }` → `Patient` (doctor only) |
| POST | `/patients/{id}/mark-reviewed` | → `Patient` (doctor only; sets last_reviewed_at = now) |

## Care plan — owner: Samprada (`core/routers/careplan.py`)
| Method | Path | Returns |
|---|---|---|
| POST | `/careplan/draft` | body `{ patient_id, raw_text }` → `CarePlanDraft` (calls `ai.copilot`) |
| PUT | `/careplan/draft/{draft_id}` | body `CarePlanDraft` (doctor edits) → `CarePlanDraft` |
| POST | `/careplan/draft/{draft_id}/approve` | → `CareEvent[]` created (APPROVAL GATE) |
| GET | `/patients/{id}/careplan` | `CarePlanItem[]` |

## Events / check-ins — owner: Samprada (`core/routers/events.py`)
| Method | Path | Returns |
|---|---|---|
| PATCH | `/events/{event_id}/status` | body `{ status, source }` → `CareEvent` |
| GET | `/patients/{id}/checklist/today` | `DailyChecklist` |
| POST | `/demo/advance-day` | runs 24h window close → marks NO_RESPONSE, regenerates attention |
| POST | `/demo/reset` | wipes all data and reloads the demo seed → `{ reset: true }` |

## Attention queue — owner: Samprada (`core/routers/attention.py` + `core/services/attention.py`)
| Method | Path | Returns |
|---|---|---|
| GET | `/attention` | `AttentionItem[]` (doctor/care-team panel) |
| PATCH | `/attention/{id}` | body `{ status, assigned_to? }` → `AttentionItem` |
| GET | `/dashboard/overview` | `DashboardOverview` (stats cards) |

## Queries — owner: Samprada routes, Shreyan AI (`core/routers/queries.py`)
| Method | Path | Returns |
|---|---|---|
| POST | `/queries` | body `{ patient_id, text, channel }` → `PatientQuery` (classified + summarized by `ai.classify`) |
| GET | `/queries?status=open` | `PatientQuery[]` |
| PATCH | `/queries/{id}` | body `{ status, response? }` → `PatientQuery` |

## Reports — owner: Samprada routes, Shreyan AI (`core/routers/reports.py`)
| Method | Path | Returns |
|---|---|---|
| POST | `/patients/{id}/reports` | body `{ title, text, uploaded_by_role }` → `Report` (values extracted by `ai.extract`) |
| GET | `/patients/{id}/reports` | `Report[]` |
| PATCH | `/reports/{id}/reviewed` | sets `reviewed = true`, clears its NEEDS_REVIEW reason → `Report` (doctor / care_team only) |

## SOS — owner: Samprada (`core/routers/sos.py`)
| Method | Path | Returns |
|---|---|---|
| POST | `/sos` | body `{ patient_id, channel, note? }` → `AttentionItem` (label `SOS`) + notifies caregivers |

## Caregivers — owner: Samprada (`core/routers/caregivers.py`)
| Method | Path | Returns |
|---|---|---|
| GET | `/patients/{id}/caregivers` | `Caregiver[]` |
| POST | `/patients/{id}/caregivers` | invite → `Caregiver` (consent `PENDING`) |
| PATCH | `/caregivers/{id}` | `{ consent_status, permissions }` |

## Audit — owner: Samprada
| GET | `/audit?entity_id=` | `AuditLog[]` |

## WhatsApp — owner: Shreyan (`whatsapp/webhook.py`)
| Method | Path | Returns |
|---|---|---|
| POST | `/whatsapp/webhook` | Twilio form payload → TwiML reply |
| POST | `/whatsapp/send-checklist/{patient_id}` | sends today's checklist |

---

## Python function contract between core ↔ ai (owner: Shreyan)
Core routers call these. They are pure functions: input → validated dict matching `ai_outputs.json`.

```python
from ai.copilot import structure_care_plan      # (raw_text: str, patient_ctx: dict) -> CopilotOutput
from ai.classify import classify_query          # (text: str) -> QueryClassification
from ai.extract import extract_report_values    # (report_text: str) -> ReportExtraction
from ai.summarize import since_last_review      # (events: list[dict], queries: list[dict], reports: list[dict]) -> ReviewSummary
from ai.summarize import pre_consult_brief      # (patient360: dict) -> ReviewSummary
```
If the AI fails or output fails validation, return the fallback shape with `"ok": false` — never crash the route.
