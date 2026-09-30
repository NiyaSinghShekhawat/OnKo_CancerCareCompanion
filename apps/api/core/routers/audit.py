from fastapi import APIRouter, Depends
from core.db import get_db
from core.models import AuditLog
from core.serialize import to_dict

router = APIRouter(tags=["audit"])


@router.get("/audit")
def list_audit(entity_id: str | None = None, db=Depends(get_db)):
    q = db.query(AuditLog)
    if entity_id:
        q = q.filter_by(entity_id=entity_id)
    return [to_dict(a) for a in q.order_by(AuditLog.timestamp.desc()).limit(200)]
