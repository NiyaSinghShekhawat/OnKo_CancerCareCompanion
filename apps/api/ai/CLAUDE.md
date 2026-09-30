# Folder: apps/api/ai — owner: Shreyan

You may ONLY edit files inside `apps/api/ai/` (and `apps/api/whatsapp/`).
Do not edit `main.py`, `contracts/`, `core/` or `apps/web/`.

- Every public function returns EXACTLY the shape in `contracts/ai_outputs.json`, always with `ok`.
- On API error / bad JSON / guardrail failure → return the fallback shape with ok=False. Never raise.
- All output passes through `guardrails.py` before returning.
- Function signatures are frozen (see contracts/api.md). Core calls them directly.

## The AI must NEVER
- diagnose, interpret lab values (normal/abnormal/low/high), infer severity or emergency
- recommend, start, stop or change any medication or treatment
- add a medicine / test / dose / treatment that isn't in the doctor's text
- produce risk scores, prognosis, or "high-risk" labels
