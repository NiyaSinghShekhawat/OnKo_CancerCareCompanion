"""Twilio WhatsApp webhook. Owner: Shreyan."""
from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response
from core.db import get_db
from core.auth import Actor
from core.models import Patient
from core.serialize import to_dict
from core.services import checklist
from core.services.journey_state import can_message
from core.routers.queries import create_query
from core.routers.sos import trigger_sos
from whatsapp import messages, parser

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


def twiml(text: str) -> Response:
    safe = text.replace("&", "&amp;").replace("<", "&lt;")
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>',
                    media_type="application/xml")


@router.post("/webhook")
def webhook(From: str = Form(...), Body: str = Form(""), db=Depends(get_db)):
    p = db.query(Patient).filter_by(phone_whatsapp=From).first()
    if not p:
        return twiml("This number isn't registered with OnKo. Please contact your care team.")
    actor = Actor("patient", p.id)
    kind = parser.intent(Body)

    if kind == "MENU":
        return twiml(messages.MENU)
    if kind == "SOS":
        trigger_sos(db, actor, p.id, "whatsapp")
        return twiml("Your SOS has been sent to your caregiver and care team.")
    if kind == "CHECKLIST":
        # TODO(Shreyan): map numbers to today's items and PATCH their status via core
        return twiml("Thanks, your checklist has been updated.")
    create_query(db, actor, p.id, Body, "whatsapp")
    return twiml("Thanks, your message has been shared with your care team. They will get back to you.")


@router.post("/send-checklist/{patient_id}")
def send_checklist(patient_id: str, db=Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    if not can_message(p.journey_state):
        return {"sent": False, "reason": f"Messaging paused for journey state {p.journey_state}"}
    items, _ = checklist.todays_items(db, patient_id)
    body = messages.render_checklist(p.name, [to_dict(i) for i in items])
    sent = messages.send(p.phone_whatsapp, body)
    return {"sent": sent, "preview": body}
