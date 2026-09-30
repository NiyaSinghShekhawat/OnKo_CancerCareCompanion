# OnKo — Cancer Care Companion

> The doctor decides the care. OnKo makes sure the journey stays connected.

Team 404 Found · Cancer Care (NCG) · Long-term Care Engagement
Samprada Reddy · Niya Singh Shekhawat · Shreyan Samal · Dr. Sheelu S Reddy

## Who owns what

| Folder | Owner | What lives there |
|---|---|---|
| `apps/api/core/` | Samprada | DB, models, seed data, CRUD routes, attention engine, checklist, journey states, RBAC, audit |
| `apps/web/` | Niya | Next.js doctor / patient / caregiver dashboards |
| `apps/api/ai/` | Shreyan | Care Plan Copilot, query classifier, report extraction, summaries, guardrails |
| `apps/api/whatsapp/` | Shreyan | Twilio webhook, checklist messages, reply parsing |
| `contracts/` | All three | FROZEN after Phase 0. Change only when all three agree. |
| `apps/api/main.py` | All three | Written once in Phase 0. Don't edit without telling the group. |

## Setup

```bash
git clone https://github.com/SampradaReddy/OnKo_CancerCareCompanion.git
cd OnKo_CancerCareCompanion
cp .env.example .env          # fill in your keys
```

### Backend
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m core.seed            # load demo patients
uvicorn main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd apps/web
npm install
cp .env.local.example .env.local
npm run dev
```
App: http://localhost:3000
Set `NEXT_PUBLIC_USE_MOCKS=true` to work without the backend.

### WhatsApp (Shreyan)
Twilio WhatsApp Sandbox → set the incoming webhook to `https://<ngrok-url>/whatsapp/webhook`.
```bash
ngrok http 8000
```

## Git workflow

- `main` → demo-stable only. Never push directly.
- `dev` → integration branch. Merge here via PR.
- Your branches: `samprada/<feature>`, `niya/<feature>`, `shreyan/<feature>`
- Start of every session: `git checkout dev && git pull && git checkout <your-branch> && git merge dev`
- Merge to `dev` at checkpoints, small PRs, not one huge merge at the end.

See `docs/WORKFLOW.md` for the full rules and `contracts/` for the API.
