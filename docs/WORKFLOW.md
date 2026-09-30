# How we work without breaking each other's code

## Ownership
| Person | Folders | Branch prefix |
|---|---|---|
| Samprada | `apps/api/core/` | `samprada/` |
| Niya | `apps/web/` | `niya/` |
| Shreyan | `apps/api/ai/`, `apps/api/whatsapp/` | `shreyan/` |
| All (agree first) | `contracts/`, `apps/api/main.py`, `.env.example`, `requirements.txt` | — |

## Daily loop
```bash
git checkout dev && git pull
git checkout samprada/attention-engine     # your branch
git merge dev                              # stay current
# ... vibe code inside your folder only ...
git add . && git commit -m "core: attention rules for missed meds"
git push -u origin samprada/attention-engine
# open PR -> dev
```

## Commit prefixes
`core:` `web:` `ai:` `wa:` `contracts:` `docs:`

## Rules
1. Tell your AI agent which folder it's in. Every folder has a CLAUDE.md — point your tool at it.
2. Shared files (`contracts/`, `main.py`, `requirements.txt`) → message the group first.
3. Adding a Python package → post "adding X to requirements.txt" in chat, then push that one-line change on its own.
4. Merge to `dev` at checkpoints. Never let a branch drift more than ~3 hours.
5. `main` only gets `dev` after a full demo run works.
6. Frontend uses mocks until Checkpoint 1. Mocks must match `contracts/schemas.json`.

## Checkpoints
- **Phase 0 (together):** contracts agreed, skeleton runs, `.env` shared privately (never commit keys)
- **Checkpoint 1:** CRUD + seed live, Copilot + classifier return valid JSON, dashboard renders mocks → Niya switches to real API
- **Checkpoint 2:** full demo flow works end-to-end (see DEMO_FLOW.md)
- **Freeze:** bug fixes only → record demo video → finish PPT (each person does slides for their own part)

## If you get a merge conflict
- In your own folder → fix it yourself.
- In a shared file → don't guess. Ping the group, fix it together on a call.
