# Core backend — Samprada
Document here: data model decisions, attention rules, checklist window logic, how to reseed.

## Attention rules (deterministic, no AI)
| Rule | Label | Reason text |
|---|---|---|
| Event status REPORTED_MISSED (medication/treatment) | NEEDS_REVIEW | "Medication reported missed: {title}, {date}" |
| 3+ consecutive NO_RESPONSE daily check-ins | FOLLOW_UP | "{n} consecutive daily check-ins unanswered: {dates}" |
| Query open > 24h | QUERY | "Query unresolved for {hours}h: {summary}" |
| New SYMPTOM_CONCERN / MEDICATION query | QUERY | "New patient concern logged: {summary}" |
| Report uploaded, not reviewed | NEEDS_REVIEW | "New report awaiting review: {title}" |
| SOS triggered | SOS | "Patient-triggered SOS via {channel}" |
