"""Twilio WhatsApp webhook. Owner: Shreyan.

Flow: Twilio POSTs each incoming message here -> we work out the intent -> call CORE functions to record it
(queries, SOS, event status) -> reply with TwiML. The messaging layer never makes a clinical decision.

Journey states (set by clinicians only):
  ACTIVE / REMISSION / RELAPSE  -> normal
  PALLIATIVE                    -> same features, gentler checklist wording (see messages.py)
  TRANSFER_OF_CARE              -> automated messaging paused; SOS still works, messages still reach the care team
  DECEASED                      -> hard stop: no automated replies at all (inbound text is still logged for the team)
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.responses import Response

from core.auth import Actor
from core.db import get_db
from core.models import CareEvent, Patient
from core.routers.events import StatusIn, set_status
from core.routers.queries import create_query
from core.routers.sos import trigger_sos
from core.serialize import to_dict
from core.services import checklist
from core.services.journey_state import can_message
from whatsapp import messages, parser

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# patient_id -> (sent_at, [event ids in the order they were numbered in the message]).
# In-memory is fine for the prototype; after a restart we fall back to today's items in the same order.
_last_checklist: dict[str, tuple[datetime, list[str]]] = {}
WINDOW = timedelta(hours=24)


def twiml(text: str | None) -> Response:
    if not text:
        return Response('<?xml version="1.0" encoding="UTF-8"?><Response/>', media_type="application/xml")
    safe = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{safe}</Message></Response>',
                    media_type="application/xml")


def _find_patient(db, sender: str) -> Patient | None:
    sender = (sender or "").strip()
    bare = sender.removeprefix("whatsapp:")
    return (db.query(Patient).filter(Patient.phone_whatsapp.in_([sender, bare, f"whatsapp:{bare}"])).first())


def checklist_items(db, patient_id: str) -> list[CareEvent]:
    """The numbered items the patient is answering: the last checklist sent (if < 24 h old), else today's."""
    sent = _last_checklist.get(patient_id)
    if sent and datetime.utcnow() - sent[0] < WINDOW:
        rows = [db.get(CareEvent, eid) for eid in sent[1]]
        return [r for r in rows if r is not None]
    items, _ = checklist.todays_items(db, patient_id)
    return items


def record_checklist_reply(db, actor: Actor, p: Patient, body: str) -> str:
    items = checklist_items(db, p.id)
    if not items:
        return messages.t(p, "no_items")
    answers = parser.parse_checklist_reply(body)
    everyone = parser.parse_all(body)
    if everyone:
        # "all done" covers the items not answered yet; if everything was answered, it applies to all.
        open_ = [i for i, ev in enumerate(items, 1) if not ev.response_state or ev.status == "NO_RESPONSE"]
        answers = [(i, everyone) for i in (open_ or range(1, len(items) + 1))]

    recorded, unknown = [], []
    for n, state in answers:
        if not 1 <= n <= len(items):
            unknown.append(n)
            continue
        ev = items[n - 1]
        late = ev.status == "NO_RESPONSE"
        previous = ev.response_state if ev.response_state in {"COMPLETED", "REPORTED_MISSED", "CONFLICTING"} else None
        if previous == "CONFLICTING" or (previous and previous != state):
            state = "CONFLICTING"      # patient changed their answer for the same occurrence -> team reviews it
        set_status(ev.id, StatusIn(status=state, source="patient"), db=db, actor=actor)
        recorded.append((n, ev.title, state, late))
    return messages.render_recorded(p, recorded, unknown)


@router.post("/webhook")
def webhook(From: str = Form(...), Body: str = Form(""), db=Depends(get_db)):
    p = _find_patient(db, From)
    if not p:
        return twiml("This number isn't registered with OnKo. Please contact your care team.")
    actor = Actor("patient", p.id)
    body = (Body or "").strip()
    kind = parser.intent(body) if body else "MENU"
    state = p.journey_state or "ACTIVE_TREATMENT"

    # SOS is patient-declared and always routed (except after a verified deceased status).
    if kind == "SOS" and state != "DECEASED":
        trigger_sos(db, actor, p.id, "whatsapp")
        notified = messages.notify_caregivers(db, p, "WhatsApp")
        return twiml(messages.t(p, "sos_ack_cg" if notified else "sos_ack"))

    if not can_message(state):
        # Paused / hard stop: anything the person writes still reaches the care team, no automated conversation.
        if body and kind not in {"MENU", "MENU_MEDS", "MENU_QUERY"}:
            create_query(db, actor, p.id, body, "whatsapp")
        return twiml(None if state == "DECEASED" else messages.t(p, "paused"))

    if kind == "MENU":
        return twiml(messages.render_menu(p))
    if kind == "MENU_MEDS":
        return twiml(messages.render_meds(p, [to_dict(i) for i in checklist_items(db, p.id)]))
    if kind == "MENU_QUERY":
        return twiml(messages.t(p, "query_prompt"))
    if kind == "CHECKLIST":
        return twiml(record_checklist_reply(db, actor, p, body))
    if kind == "OPT_OUT":
        create_query(db, actor, p.id, "Patient asked to stop WhatsApp messages (replied STOP).", "whatsapp")
        return twiml(messages.t(p, "optout"))
    create_query(db, actor, p.id, body, "whatsapp")
    return twiml(messages.t(p, "query_ack"))


@router.post("/send-checklist/{patient_id}")
def send_checklist(patient_id: str, db=Depends(get_db)):
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    if not can_message(p.journey_state):
        return {"sent": False, "reason": f"Messaging paused for journey state {p.journey_state}"}
    items, _ = checklist.todays_items(db, patient_id)
    body = messages.render_checklist(p, [to_dict(i) for i in items])
    sent = messages.send(p.phone_whatsapp, body)
    _last_checklist[p.id] = (datetime.utcnow(), [i.id for i in items])
    return {"sent": sent, "preview": body, "items": len(items)}
