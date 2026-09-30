from core.models import AuditLog


def log(db, actor, action: str, entity_type: str, entity_id: str, before=None, after=None):
    db.add(AuditLog(actor_id=actor.user_id, actor_role=actor.role, action=action,
                    entity_type=entity_type, entity_id=entity_id, before=before, after=after))
