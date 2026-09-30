"""SOS is PATIENT-TRIGGERED only. The AI never infers an emergency."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor
from core.models import Patient
from core.serialize import to_dict
from core.services import audit, attention

router = APIRouter(tags=["sos"])


class SOSIn(BaseModel):
    patient_id: str
    channel: str = "app"
    note: str | None = None


def trigger_sos(db, actor, patient_id: str, channel: str, note: str | None = None):
    """Also called by whatsapp/webhook.py."""
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    item = attention.raise_item(db, p, "SOS", f"Patient-triggered SOS via {channel}")
    db.flush()
    audit.log(db, actor, "sos_triggered", "attention_item", item.id, None, {"channel": channel, "note": note})
    # TODO(Samprada + Shreyan): notify consented caregivers via whatsapp.messages.notify_caregivers
    db.commit()
    return item


@router.post("/sos")
def sos(body: SOSIn, db=Depends(get_db), actor=Depends(get_actor)):
    return to_dict(trigger_sos(db, actor, body.patient_id, body.channel, body.note))
