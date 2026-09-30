# Folder: apps/api/core — owner: Samprada

You may ONLY edit files inside `apps/api/core/`.
Do not edit `main.py`, `contracts/`, `ai/`, `whatsapp/` or `apps/web/`.

- Models and responses must match `contracts/schemas.json` field names exactly.
- Routes must match `contracts/api.md` paths exactly.
- Call AI only through the functions listed in `contracts/api.md` (import from `ai.*`). Never write prompts here.
- Attention queue is RULE-BASED (see `docs/core.md`). No AI, no risk scores, no "high-risk" labels.
- Every create/update/approve/escalate writes an audit log via `services/audit.py`.
- Copilot output is saved as DRAFT. Only `/careplan/draft/{id}/approve` creates CareEvents.
- Journey state DECEASED → no messages. PALLIATIVE → no adherence-style nudges.
