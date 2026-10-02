# Backend core — reference

Owner: Samprada · Folder: `apps/api/core/` · Contract: `contracts/api.md`, `contracts/schemas.json`

This page describes what the code in `apps/api/core/` does today. If this page and the code disagree, the code wins — please fix the page.

---

## 1. What core owns

| Area | Where |
|---|---|
| Data model (patients, care plan, events, attention, queries, reports, caregivers, audit) | `models.py` |
| Demo auth (headers → actor) and per-patient access | `auth.py` |
| Patients, timeline, Patient 360, journey state, mark-reviewed | `routers/patients.py` |
| Care plan drafts and the approval gate | `routers/careplan.py`, `services/recurrence.py` |
| Event status, today's checklist, demo advance-day / reset | `routers/events.py`, `services/checklist.py` |
| Attention queue, assignment, dashboard counts | `routers/attention.py`, `services/attention.py` |
| Patient queries | `routers/queries.py` |
| Reports (upload, list, mark reviewed) | `routers/reports.py` |
| SOS | `routers/sos.py` |
| Caregivers, consent lifecycle, caregiver view | `routers/caregivers.py` |
| Audit log | `routers/audit.py`, `services/audit.py` |
| Journey-state rules (one place) | `services/journey_state.py` |
| "Since last review" rule-based fallback | `services/review.py` |
| Clock (naive UTC) | `timeutil.py` |
| Demo data | `seed.py` |

Core calls AI only through `ai.*` functions (`structure_care_plan`, `classify_query`, `extract_report_values`, `since_last_review`, `end_date_for`). Core writes no prompts. WhatsApp (`whatsapp/`) calls three core functions directly — `set_status`, `create_query`, `trigger_sos` — with `Actor("patient", <that patient's id>)`. In the other direction, core's `trigger_sos` calls `whatsapp.messages.notify_caregivers`, so app and WhatsApp SOS alert caregivers the same way (§4).

---

## 2. Run, seed, reset, test

All commands run from `apps/api/`.

| What | Command | Effect |
|---|---|---|
| Load demo data | `python -m core.seed` | **Drops and recreates all tables**, then loads the demo data. Use this when the server is stopped. |
| Start the API | `uvicorn main:app --reload --port 8000` | On startup `init_db()` creates missing tables and adds any new columns to existing tables in place (nullable → NULL; columns with a server default → that value). |
| Reset while the server runs | `POST /demo/reset` with headers `X-Role: doctor`, `X-User-Id: doc_mehta` | Deletes every row and reloads the demo data inside the running app; tables are kept. Returns `{"reset": true}`. |
| Simulate the day ending | `POST /demo/advance-day` (doctor) | Closes the 24h window (see §5) and re-runs the attention rules for every patient. Returns `{"marked_no_response": n}`. |
| Tests | `python -m pytest tests` | Uses `test_onko.db` with AI and Twilio keys blanked; `onko.db` is never touched. |

Database: `DATABASE_URL` (default `sqlite:///./onko.db`). Seed dates are relative to the moment of seeding, so after a reset "today" is today.

### Deployment

Two environment variables (see `.env.example`) make a deployed demo safer. Both are read on every request, so changing them only needs a restart to reload `.env`, no code change.

| Variable | Default | Effect when set |
|---|---|---|
| `DEMO_ACCESS_CODE` | unset (empty = unset) | Every request that goes through core auth must also send `X-Access-Code: <value>`, else **401 `Access code required`**. This is checked before the role/user headers, so a wrong code reveals nothing about users. |
| `DEMO_ROUTES_ENABLED` | `true` | `false` / `0` / `no` / `off` → `POST /demo/reset` and `POST /demo/advance-day` answer **404** before any auth, so nobody can wipe or advance a deployed demo. |

#### Supabase (Postgres)

Core runs on SQLite (local dev, tests) and Postgres (Supabase) with the same code. Only `DATABASE_URL` changes.

1. In Supabase, create a project in the **South Asia (Mumbai)** region (`ap-south-1`), closest to the demo's users. Keep the database password.
2. Open **Connect → Connection string** and pick **Session pooler** (port 5432; reachable over IPv4).
3. Write the URL with the psycopg driver and put it in the repo-root `.env`:
   ```
   DATABASE_URL=postgresql+psycopg://postgres.<project-ref>:<password>@aws-0-ap-south-1.pooler.supabase.com:5432/postgres
   ```
   Copy the host and `postgres.<project-ref>` user exactly as Supabase shows them. URL-encode special characters in the password (`@` → `%40`, `#` → `%23`, `/` → `%2F`). A plain `postgresql://…` URL also works: core rewrites it to `postgresql+psycopg://`.
4. Install the driver with the rest: `pip install -r requirements.txt` (includes `psycopg[binary]`).
5. From `apps/api`, run **`python -m core.seed` once**. It creates the tables and loads the demo data; it drops core's tables first, so don't run it against data you want to keep. After that, reset with `POST /demo/reset` like on SQLite.
6. Start the API as usual. Postgres connections use `pool_pre_ping`, so connections the pooler closed while idle are replaced instead of failing. On later model changes `init_db()` adds new columns with a standard `ALTER TABLE … ADD COLUMN` (no SQLite PRAGMAs), so no manual migration is needed for added columns.

Tests always use SQLite (`test_onko.db`), never Supabase.

The two WhatsApp routes (in `whatsapp/`):

| Route | Protection |
|---|---|
| `POST /whatsapp/send-checklist/{id}` | Doctor or care_team headers — plus `X-Access-Code` when `DEMO_ACCESS_CODE` is set (same checks as core) — **or** `X-Cron-Secret` equal to `CRON_SECRET`, for a scheduler calling over HTTP. Patients and caregivers get 403. `python -m whatsapp.daily` sends directly through the database and needs no header. |
| `POST /whatsapp/webhook` | Not covered by the access code (Twilio can't send custom headers). Instead it rejects requests without a valid Twilio signature (403) whenever `TWILIO_AUTH_TOKEN` is set; `TWILIO_VALIDATE_SIGNATURE=false` turns that off for local debugging. |

`/docs` and `/openapi.json` are not behind the access code. WhatsApp's internal calls into core build their actor directly and are unaffected. The web app must add `X-Access-Code` to every request when the code is set. Tests force both switches off in `tests/conftest.py`, whatever your `.env` says.

### Deployed (shared demo)

| What | Where |
|---|---|
| Backend | https://onko-api.onrender.com (Render). API docs at `/docs`. |
| Database | One shared Supabase database (Session pooler URL, §2 Supabase); every teammate's actions land in the same data. |
| Access code | Shared by DM only. Never write it in the repo, docs, issues or chat channels. |

- **Free tier sleeps.** Render's free instance stops after about 15 minutes without traffic; the first request after that takes a while to wake it. Open `/docs` a minute before demoing.
- **Reset only by agreement.** `POST /demo/reset` (and `python -m core.seed` against the Supabase URL) wipes everyone's shared data. Agree in the group first.

---

## 3. Demo identities

Every request sends `X-Role` and `X-User-Id` (see §8). These are the seeded users.

### Staff

| `X-Role` | `X-User-Id` | Name |
|---|---|---|
| `doctor` | `doc_mehta` | Dr. Mehta |
| `care_team` | `nurse_anita` | Nurse Anita |

### Patients (`X-Role: patient`, `X-User-Id` = patient id)

| Patient id | Name | Journey state | Chapter | Story in the seed |
|---|---|---|---|---|
| `p_rajesh` | Rajesh Kumar | ACTIVE_TREATMENT | 1 | Chemo today, Capecitabine missed yesterday, unreviewed CBC report, open nausea query |
| `p_priya` | Priya Sundaram | ACTIVE_TREATMENT | 1 | Chemo tomorrow; caregiver invite still pending |
| `p_arjun` | Arjun Reddy | ACTIVE_TREATMENT | 1 | 3 unanswered check-ins; FOLLOW_UP assigned to `nurse_anita` |
| `p_lakshmi` | Lakshmi Devi | REMISSION_SURVIVORSHIP | 1 | No events |
| `p_meera` | Meera Iyer | PALLIATIVE (from ACTIVE_TREATMENT, 14 days ago) | 1 | Missed dose that raises nothing; open medication query that raises QUERY |
| `p_vikram` | Vikram Singh | TRANSFER_OF_CARE (from ACTIVE_TREATMENT, 2 days ago) | 1 | Upcoming events; checklist paused |
| `p_farhan` | Farhan Ali | RELAPSE (from REMISSION_SURVIVORSHIP, 7 days ago) | 2 | Completed chapter-1 history, chapter-2 events after the relapse |
| `p_kamala` | Kamala Rao | DECEASED (from PALLIATIVE, 10 days ago) | 1 | Completed history only, no attention |

### Caregivers (`X-Role: caregiver`, `X-User-Id` = caregiver id)

| Caregiver id | Name | Patient | Relation | Consent |
|---|---|---|---|---|
| `cg_sunita` | Sunita Kumar | `p_rajesh` | Wife | GRANTED |
| `cg_karthik` | Karthik Sundaram | `p_priya` | Brother | PENDING |
| `cg_lakshmi` | Lakshmi Iyer | `p_meera` | Daughter | GRANTED |
| `cg_harpreet` | Harpreet Singh | `p_vikram` | Wife | GRANTED |
| `cg_ayesha` | Ayesha Ali | `p_farhan` | Sister | GRANTED |
| `cg_suresh` | Suresh Rao | `p_kamala` | Son | GRANTED |

All caregivers except Karthik have `view_journey`, `upload_reports` and `receive_escalations` on. Karthik has the model default (`view_journey` and `receive_escalations` on, `upload_reports` off) but no access until he accepts. Seeded ids are fixed, so they survive a reset; caregivers invited later get random ids.

### Seeded attention queue

Every seeded reason is built by the same functions the rules use (§4), so it reads exactly like a rule-generated reason and `clear_reason` can remove it. Dates are relative to the day you seed.

| Patient | Label | Reasons | Assigned |
|---|---|---|---|
| Rajesh | NEEDS_REVIEW | "Medication reported missed: Capecitabine 500mg, {yesterday, DD Mon}"; "New report awaiting review: CBC — 20 Sep" | — |
| Rajesh | QUERY | "New patient concern logged: Patient reports nausea since yesterday and mild discomfort." | — |
| Arjun | FOLLOW_UP | "3 consecutive daily check-ins unanswered: {3 days ago}, {2 days ago}, {yesterday}" (each DD Mon) | `nurse_anita` |
| Meera | QUERY | "New patient concern logged: Asks whether the evening tablet can be taken after dinner instead of before." | — |

---

## 4. Attention rules (deterministic, no AI, no scores)

Each patient has at most one open item (`PENDING` or `ACKNOWLEDGED`) per label. A new reason is added to that open item; if there is none, a new item is created. The same reason is never added twice. The queue is ordered SOS → NEEDS_REVIEW → QUERY → FOLLOW_UP, then oldest first.

| Rule | When it runs | Label | Exact reason text | Not raised for |
|---|---|---|---|---|
| A MEDICATION or TREATMENT event is set to `REPORTED_MISSED` | `PATCH /events/{id}/status` (also WhatsApp checklist replies) | NEEDS_REVIEW | `Medication reported missed: {title}, {DD Mon}` or `Treatment reported missed: {title}, {DD Mon}` (date = scheduled date) | PALLIATIVE, DECEASED |
| 3 or more NO_RESPONSE events in a row (the most recent run; UPCOMING/CURRENT events are skipped, any other status ends the run) | `POST /demo/advance-day` | FOLLOW_UP | `{n} consecutive daily check-ins unanswered: {DD Mon, DD Mon, …}` (each date once; replaces the older wording of this reason) | PALLIATIVE, TRANSFER_OF_CARE, DECEASED |
| A query not RESOLVED, open for more than 24 whole hours (first raised at 25h) | `POST /demo/advance-day` | QUERY | `Query unresolved for {hours}h: {summary}` (replaces the older hours for the same query) | DECEASED |
| New query classified SYMPTOM_CONCERN or MEDICATION (ADMINISTRATIVE raises nothing) | `POST /queries`, WhatsApp free text | QUERY | `New patient concern logged: {summary}` | DECEASED (the query is still saved) |
| Report uploaded and not yet reviewed | `POST /patients/{id}/reports`; again on `POST /demo/advance-day` for every unreviewed report | NEEDS_REVIEW | `New report awaiting review: {title}` | DECEASED (the report is still saved) |
| SOS pressed by the patient (or their consented caregiver, or staff on their behalf) | `POST /sos`, WhatsApp "SOS" | SOS | `Patient-triggered SOS via {channel}` (`app`, `whatsapp`, …) | DECEASED: `POST /sos` returns 409; a WhatsApp "SOS" gets no reply and raises nothing |

**SOS also alerts caregivers.** Every SOS that raises an item (app or WhatsApp) sends a WhatsApp alert to the patient's caregivers who have consent GRANTED and `receive_escalations` on. This happens in every journey state except DECEASED — **including TRANSFER_OF_CARE**, where only routine automated messages are paused. A repeat SOS for the same patient within 60 seconds is still recorded (`sos_triggered`) on the open SOS item, but doesn't alert caregivers again; the check uses the `caregivers_notified` audit entry, so it holds across restarts. The patient's WhatsApp reply says whether caregivers were alerted.

**Reasons are removed** (with an audit entry) when:

| Event | Removed from | Reasons removed |
|---|---|---|
| Query changed to RESOLVED (`PATCH /queries/{id}`) | QUERY | `New patient concern logged: {summary}` and `Query unresolved for …h: {summary}` for that query |
| Report marked reviewed (`PATCH /reports/{id}/reviewed`) | NEEDS_REVIEW | `New report awaiting review: {title}` |
| Patient switched to PALLIATIVE | FOLLOW_UP (all reasons) and NEEDS_REVIEW (`… reported missed: …` reasons only) | see left |
| Patient switched to DECEASED | every open item | all reasons |

An item left with no reasons is set to CLOSED (`attention_closed`); otherwise `attention_reason_cleared`.

---

## 5. Daily checklist and the 24h window

- `GET /patients/{id}/checklist/today` returns that patient's events scheduled today (UTC calendar day), `window_closes_at` = midnight UTC tonight, `sent: false`, plus `paused` and `reason`. For TRANSFER_OF_CARE and DECEASED: `items: []`, `paused: true`, `reason: "Journey state <STATE>"`; otherwise `paused: false`, `reason: null`.
- `POST /demo/advance-day` marks events NO_RESPONSE when all of these hold:
  - status is UPCOMING or CURRENT, and the event was scheduled more than 24h ago;
  - the patient's checklist is not paused (not TRANSFER_OF_CARE / DECEASED);
  - **paused-period rule:** if the patient's `previous_journey_state` is TRANSFER_OF_CARE or DECEASED, only events scheduled after `journey_state_changed_at` count. Events from the paused period stay UPCOMING. After any other state change, earlier events are marked as normal.

---

## 6. Journey states

Journey states are set only by a doctor (`PATCH /patients/{id}/journey-state`). A real change sets `journey_state_changed_at` = now and `previous_journey_state` = the old state; re-sending the same state changes neither.

| State | Daily checklist | Window → NO_RESPONSE | Missed-dose NEEDS_REVIEW | Check-in FOLLOW_UP | Queries, reports, SOS | On switching into this state | Caregiver view `upcoming` | WhatsApp messaging (`can_message`) |
|---|---|---|---|---|---|---|---|---|
| ACTIVE_TREATMENT | yes | yes | yes | yes | yes | — | yes | yes |
| REMISSION_SURVIVORSHIP | yes | yes | yes | yes | yes | — | yes | yes |
| RELAPSE | yes | yes | yes | yes | yes | `journey_chapter` + 1 (audited) | yes | yes |
| PALLIATIVE | yes | yes | **no** | **no** | yes | open FOLLOW_UP closed; missed-dose reasons removed from NEEDS_REVIEW (report reasons stay) | yes | yes (gentler checklist wording in `whatsapp/`) |
| TRANSFER_OF_CARE | **paused** | **no** | yes¹ | **no** | yes | existing items stay open | yes | **no** routine messages (`send-checklist` returns `sent: false`; inbound text becomes a query and gets a "paused" reply). SOS still raises the item **and alerts caregivers** |
| DECEASED | **paused** | **no** | **no** | **no** | **no** new items; `POST /sos` → 409 | every open item closed | **[]** (history only) | **no** (hard stop: no replies at all; inbound text is still saved as a query, without an attention item; WhatsApp "SOS" is ignored; no caregiver alerts) |

¹ Only if a missed dose is reported through `PATCH /events/{id}/status`; the checklist that would normally produce it is paused.

Switching back to ACTIVE_TREATMENT or RELAPSE resumes everything; nothing is re-raised just by switching — the rules raise items again on the next event or advance-day.

### Relapse chapters

- Patients and events have `journey_chapter` (default 1). Switching to RELAPSE adds 1 to the patient's chapter (audited `journey_chapter_started`). A second relapse later gives chapter 3.
- Every new CareEvent gets its patient's current chapter automatically, whichever code creates it (care-plan approval or anything else); an explicitly given chapter is kept. Old events keep their chapter and are never deleted.
- `GET /patients/{id}/timeline` and the 360 `timeline` return all chapters, sorted by `scheduled_at`, each event carrying `journey_chapter`.

---

## 7. Care plan and the approval gate

AI output is only ever a DRAFT. Only `POST /careplan/draft/{id}/approve` (doctor) creates CareEvents. An approved or already-decided draft returns 404.

On approve, in this order:

1. **Start date check.** Every item needs a `start_date` that `datetime.fromisoformat` accepts (`2026-10-15` or a full datetime). If any are missing or invalid: **400 `Set a start date for: {comma-separated titles}`** ("untitled item" if no title) and nothing is created.
2. **End date from duration.** For items with no `end_date`, `ai.copilot.end_date_for(item)` computes one from the doctor's text (`source_span`): "for N days/weeks", "x N days/weeks", "xN days" or "× N days/weeks" → `start_date + N days − 1` (inclusive; a week is 7 days; e.g. start 15 Oct "for 14 days" → 28 Oct, "× 3 days" → 17 Oct). No duration in the text → `end_date` stays null. The computed value is saved on the CarePlanItem.
3. **Recurrence → events**, from `start_date` to `end_date` inclusive:

| `recurrence` | Events |
|---|---|
| `daily HH:MM` or `daily HH:MM, HH:MM, …` (case-insensitive; every time must be valid) | Every day at each time (duplicates removed) |
| `every N days` / `every 1 day` (N ≥ 1) | Every N days at 09:00 |
| null, empty, or anything else (e.g. `twice weekly`, `daily 25:00`, `every 0 days`) | One event at `start_date` 09:00 |

   - Valid recurrence but no `end_date` → events on the start date only (no duration is invented).
   - `end_date` before `start_date` → treated as the start date.
   - Events get `source: copilot_approved`, `care_plan_item_id`, and the patient's current `journey_chapter`.
4. The draft becomes APPROVED; audit `care_plan_approved` with `n_items` and `n_events`.

---

## 8. Access control (demo auth)

**Headers are required on every core route.**

| Situation | Response |
|---|---|
| `DEMO_ACCESS_CODE` is set and `X-Access-Code` is missing or wrong (checked first; see §2 Deployment) | 401 `Access code required` |
| `X-Role` or `X-User-Id` missing or empty | 401 `Missing X-Role / X-User-Id` |
| `X-Role` not one of doctor, care_team, patient, caregiver | 400 `Unknown role` |
| Id not found for that role (doctor/care_team must be in `users` **with that role**; patient in `patients`; caregiver in `caregivers`, any consent status) | 401 `Unknown user for role` |
| Role not allowed on the route | 403 `Role '<role>' cannot do this` |
| Not allowed for this patient | 403 `No access to this patient` |

"Staff" = doctor or care_team. A **consented caregiver** = consent GRANTED for that patient. Patients can only reach their own id. On `/patients/{id}…` routes the access check runs before the 404, so only staff learn whether an unknown patient id exists.

| Route | Doctor | Care team | Patient (own) | Consented caregiver |
|---|---|---|---|---|
| `GET /patients`, `GET /attention`, `GET /attention/mine`, `GET /dashboard/overview`, `GET /queries`, `GET /audit` | ✓ | ✓ | — | — |
| `PATCH /attention/{id}` | ✓ any item | ✓ own or unassigned items | — | — |
| `PATCH /queries/{id}`, `PATCH /reports/{id}/reviewed` | ✓ | ✓ | — | — |
| `GET /patients/{id}`, `/timeline`, `/360`, `/careplan`, `/reports`, `/caregivers` | ✓ | ✓ | ✓ | — (use their own view) |
| `GET /patients/{id}/checklist/today` | ✓ | ✓ | ✓ | ✓ minimized events |
| `PATCH /events/{id}/status` (checked against the event's patient) | ✓ | ✓ | ✓ | ✓ minimized response |
| `POST /queries`, `POST /sos` | ✓ | ✓ | ✓ | ✓ |
| `POST /patients/{id}/reports` | ✓ | ✓ | ✓ | ✓ only with `upload_reports` (else 403 `Caregiver has no upload permission`) |
| `POST /patients/{id}/caregivers` (invite), `PATCH /caregivers/{id}` (permissions) | ✓ | ✓ | ✓ | — |
| `POST /caregivers/{id}/accept` | — | — | — | that caregiver only (any consent status) |
| `POST /caregivers/{id}/revoke` | ✓ | ✓ | ✓ | that caregiver only (stepping away) |
| `POST /caregivers/{id}/reinvite` | ✓ | ✓ | ✓ | — |
| `GET /caregivers/{id}/view` | ✓ | — | — | that caregiver only |
| `PATCH /patients/{id}/journey-state`, `POST /patients/{id}/mark-reviewed`, `POST /careplan/draft`, `PUT /careplan/draft/{id}`, `POST /careplan/draft/{id}/approve`, `POST /demo/advance-day`, `POST /demo/reset` | ✓ | — | — | — |
| `POST /whatsapp/send-checklist/{id}` (in `whatsapp/`; or `X-Cron-Secret`, see §2) | ✓ | ✓ | — | — |

### Caregiver minimized view — `GET /caregivers/{id}/view`

Requires consent GRANTED **and** `permissions.view_journey`, even for the doctor; otherwise 403 `Caregiver access not granted`. Every successful call is audited (`caregiver_view_accessed`).

| Field | Content |
|---|---|
| `patient` | `id`, `name`, `journey_state`, `preferred_language` only |
| `upcoming` | Events from now to 7 days ahead, plus today's CURRENT/UPCOMING items even if their time has passed; sorted by date; `[]` if DECEASED |
| `recent` | Last 7 days of COMPLETED / REPORTED_MISSED / NO_RESPONSE events, newest first |
| `can_upload_reports`, `receives_escalations` | From the caregiver's permissions |

Every event a caregiver receives — here, in the checklist, and from `PATCH /events/{id}/status` — has only `id`, `type`, `title`, `scheduled_at`, `status` (one helper: `serialize.minimized_event`). Never sent to caregivers: diagnosis, event details (doses, instructions), reports, queries, attention items, other caregivers' numbers.

---

## 9. Caregiver consent lifecycle

Invite → Accept → Assign responsibilities → Switch / Revoke → Re-invite.

| Step | Route | Who | Transition | Already in target state | Other |
|---|---|---|---|---|---|
| Invite | `POST /patients/{id}/caregivers` | patient, staff | new caregiver, PENDING | — | — |
| Accept | `POST /caregivers/{id}/accept` | that caregiver | PENDING → GRANTED | GRANTED: 200, no change | REVOKED: **409 `Consent was revoked; the patient must re-invite`** |
| Assign responsibilities | `PATCH /caregivers/{id}` body `{ permissions }` | patient, staff | — | — | sending `consent_status` → **400**, pointing to the three routes below |
| Revoke | `POST /caregivers/{id}/revoke` | patient, staff, or the caregiver themself | any → REVOKED | REVOKED: 200, no change | — |
| Re-invite | `POST /caregivers/{id}/reinvite` | patient, staff | REVOKED → PENDING | PENDING: 200, no change | GRANTED: **409 `Caregiver already has consent; nothing to re-invite`** |

Revoking takes effect immediately: every caregiver check and SOS notification looks for GRANTED at the time of the call. No attention reason or stored notification is tied to a caregiver, so nothing else needs cleaning up. A caregiver can't change their own permissions, invite others, or revoke a fellow caregiver.

---

## 10. Attention assignment and handoff

| Feature | Behaviour |
|---|---|
| Filters on `GET /attention` | `?assigned_to=`, `?label=`, `?patient_id=`, `?status=`; combinable. Without `?status=`, CLOSED is left out; `?status=CLOSED` shows them. Unknown label/status → 400. |
| `GET /attention/mine` | The caller's items that are not CLOSED. |
| `PATCH /attention/{id}` body `{ status?, assigned_to? }` | Either field may be omitted. |
| Assignee | Must be a doctor or care_team user id, else **400 `assigned_to must be a doctor or care_team user id`** and nothing changes. Unassigning (null) is not supported. |
| Who may change an item | Doctor: any item. Care team: only unassigned items or items assigned to them (status **and** reassignment), else **403 `This item is assigned to someone else`**. A nurse who hands an item to the doctor can no longer change it. |
| Audit | Status change → `attention_update` (before/after status). First assignment → `attention_assigned`; reassignment → `attention_handoff` with old and new assignee. Re-sending the same value writes nothing. |

---

## 11. Audit actions

Every audit entry has `actor_id`, `actor_role`, `action`, `entity_type`, `entity_id`, `before`, `after`, `timestamp`. Read them with `GET /audit?entity_id=` (staff only; newest 200).

`actor_role` is one of the four roles, or **`system`** (with `actor_id` `whatsapp`) for automated actions written by `whatsapp/`. That's always the case for `caregivers_notified`, and for `whatsapp_checklist_sent` when the daily scheduler or the cron secret sent the checklist; when a doctor or nurse calls `send-checklist`, the entry records that person. The contract (`AuditLog` in `contracts/schemas.json`) lists it as `Role|system`, so the web app should expect it when showing audit history.

| Action | Entity | Written when |
|---|---|---|
| `journey_state_change` | patient | Doctor sets a journey state |
| `journey_chapter_started` | patient | Switch to RELAPSE adds a chapter |
| `patient_marked_reviewed` | patient | `POST /patients/{id}/mark-reviewed` |
| `copilot_draft_created` | care_plan_draft | AI draft created |
| `copilot_draft_edited` | care_plan_draft | Doctor edits a draft |
| `care_plan_approved` | care_plan_draft | Draft approved (`n_items`, `n_events`) |
| `event_status` | care_event | Event status changed |
| `query_created` | patient_query | Query created (app or WhatsApp) |
| `query_update` | patient_query | Query status/response changed |
| `report_uploaded` | report | Report uploaded |
| `report_reviewed` | report | Report marked reviewed |
| `sos_triggered` | attention_item | SOS raised |
| `attention_update` | attention_item | Item status changed |
| `attention_assigned` | attention_item | Item assigned for the first time |
| `attention_handoff` | attention_item | Item reassigned |
| `attention_reason_cleared` | attention_item | Some reasons removed (query resolved, report reviewed, journey state) |
| `attention_closed` | attention_item | Last reason removed, item closed |
| `caregiver_invited` | caregiver | Caregiver invited |
| `caregiver_updated` | caregiver | Permissions changed |
| `caregiver_consent_accepted` | caregiver | PENDING → GRANTED |
| `caregiver_consent_revoked` | caregiver | → REVOKED |
| `caregiver_reinvited` | caregiver | REVOKED → PENDING |
| `caregiver_view_accessed` | caregiver | Caregiver view opened |
| `caregivers_notified` | patient | SOS alert sent to caregivers (`after.names`, `after.channel`); written by `whatsapp/` with actor role `system`; also drives the 60-second de-dupe |
| `whatsapp_checklist_sent` | patient | WhatsApp checklist sent (`after.event_ids` = the numbered order the patient saw, used to match "1 done, 3 missed" replies for 24h); written by `whatsapp/`; actor role `system` when sent by the scheduler or cron secret, otherwise the staff member who sent it |

---

## 12. Known limitations

- **"Today" is the UTC calendar day** everywhere in core (checklist, dashboard `consultations_today`, open-today items). For users in India (UTC+5:30), anything before 05:30 IST counts as the previous day. Stored datetimes are naive UTC.
- **Demo auth is header-based, not a real login.** Anyone who knows a valid id can send it as a header; there are no passwords, tokens or sessions. `DEMO_ACCESS_CODE` keeps strangers out of a deployed demo, but it is one shared code for everyone, not a per-user login.
- **Events from before a relapse stay scheduled** until the doctor changes the plan. A relapse starts a new chapter but does not cancel chapter-1 events that are still UPCOMING; they keep appearing in the checklist and timeline.
- **Rules run on events, not on a clock.** The FOLLOW_UP streak, the open-query >24h rule and re-raising unreviewed reports only run on `POST /demo/advance-day`; there is no background scheduler.
- **Caregivers invited after seeding get random ids**; only the seeded ones are fixed.
