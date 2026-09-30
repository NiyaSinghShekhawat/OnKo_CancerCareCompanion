# Folder: apps/api/whatsapp — owner: Shreyan
Same rules as ai/CLAUDE.md. Only edit inside `apps/api/ai/` and `apps/api/whatsapp/`.
- Use core functions (`core.routers.queries.create_query`, `core.routers.sos.trigger_sos`, event status update) — don't write to the DB directly with new logic.
- Check `core.services.journey_state.can_message(state)` before sending ANY message.
- ONE daily checklist message, not one message per activity.
- Clinical decisions never happen in the messaging layer.
