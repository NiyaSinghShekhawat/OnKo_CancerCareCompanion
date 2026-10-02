"""Demo auth: role + user id come from headers. Good enough for a prototype, clearly labeled.
Both headers are required; there is no default user."""
from fastapi import Depends, Header, HTTPException
from core.db import get_db

STAFF = ("doctor", "care_team")


class Actor:
    def __init__(self, role: str, user_id: str):
        self.role, self.user_id = role, user_id


def get_actor(x_role: str | None = Header(None), x_user_id: str | None = Header(None),
              db=Depends(get_db)) -> Actor:
    """HTTP callers only. Internal callers (whatsapp/) build Actor(...) directly and skip this."""
    if not x_role or not x_user_id:
        raise HTTPException(401, "Missing X-Role / X-User-Id")
    if x_role not in {"doctor", "patient", "caregiver", "care_team"}:
        raise HTTPException(400, "Unknown role")
    if not _user_exists(db, x_role, x_user_id):
        raise HTTPException(401, "Unknown user for role")
    return Actor(x_role, x_user_id)


def _user_exists(db, role: str, user_id: str) -> bool:
    from core.models import Caregiver, Patient, User
    if role in STAFF:
        user = db.get(User, user_id)
        return user is not None and user.role == role
    if role == "patient":
        return db.get(Patient, user_id) is not None
    return db.get(Caregiver, user_id) is not None   # any consent status: a PENDING caregiver must be able to accept


def require(actor: Actor, *roles: str):
    if actor.role not in roles:
        raise HTTPException(403, f"Role '{actor.role}' cannot do this")


def require_patient_access(actor: Actor, patient_id: str, db, allow_caregivers: bool = True):
    """Staff: any patient. Patient: only themselves. Caregiver: only a patient who GRANTED them consent."""
    if actor.role in STAFF:
        return
    if actor.role == "patient" and actor.user_id == patient_id:
        return
    if actor.role == "caregiver" and allow_caregivers:
        from core.models import Caregiver
        if db.query(Caregiver).filter_by(id=actor.user_id, patient_id=patient_id, consent_status="GRANTED").first():
            return
    raise HTTPException(403, "No access to this patient")
