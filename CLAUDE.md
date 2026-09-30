# Rules for every AI coding agent in this repo

You are helping build OnKo, a cancer care continuity prototype. Three people work in this repo at the same time. Collisions break the build.

## Hard rules
1. Only edit files inside the folder you were asked to work in. Check the folder's own CLAUDE.md.
2. NEVER edit `contracts/`, `apps/api/main.py`, `.env.example`, or another person's folder unless the user explicitly says so.
3. Follow `contracts/api.md` and `contracts/schemas.json` exactly — field names, types, paths. If something seems missing from the contract, tell the user instead of inventing it.
4. Don't rename, move or "clean up" files you weren't asked to touch.
5. Don't add dependencies without telling the user (they must announce it to the team).

## Product safety rules (non-negotiable — this is the pitch)
- AI organizes, summarizes and structures. The clinician interprets and decides.
- No diagnosis, no clinical risk scores, no "high-risk patient" labels, no prognosis.
- Never interpret lab values. Show "Hb: 9.2 — CBC, 20 Sep", never "patient is anemic".
- The Copilot never invents a medicine, dose, test or treatment the doctor didn't enter.
- Nothing reaches the patient's journey until the doctor approves it.
- SOS is patient-triggered only. The AI never infers an emergency.
- Journey states (remission, palliative, deceased…) are set by clinicians only.
- Attention queue uses labels: NEEDS_REVIEW / FOLLOW_UP / QUERY / SOS — with a plain-language reason.
