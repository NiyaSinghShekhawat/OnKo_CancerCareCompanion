"""Twilio WhatsApp webhook. Owner: Shreyan.

Flow: Twilio POSTs each incoming message here -> we work out the intent -> call CORE functions to record it
(queries, SOS, event status) -> reply with TwiML. The messaging layer never makes a clinical decision.

Journey states (set by clinicians only):
  ACTIVE / REMISSION / RELAPSE  -> normal
  PALLIATIVE                    -> same features, gentler checklist wording (see messages.py)
  TRANSFER_OF_CARE              -> automated messaging paused; SOS still works, messages still reach the care team
  DECEASED                      -> hard stop: no automated replies at all (inbound text is still logged for the team)
"""
import hmac
import inspect
import os
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Request
from fastapi.responses import Response

from core.auth import STAFF, Actor, get_actor, require
from core.db import get_db
from core.models import AuditLog, CareEvent, Patient
from core.routers.events import StatusIn, set_status
from core.routers.queries import create_query
from core.routers.sos import trigger_sos
from core.serialize import to_dict
from core.services import audit, checklist
from core.services.journey_state import can_message
from core.timeutil import utcnow
from whatsapp import messages, parser

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

WINDOW = timedelta(hours=24)
SENT_ACTION = "whatsapp_checklist_sent"   # audit entry; its `after.event_ids` is the numbered order the patient saw
SYSTEM = Actor("system", "whatsapp")


# ---------------- Twilio request signature ----------------

def _signature_required() -> bool:
    """On whenever a Twilio auth token is configured. TWILIO_VALIDATE_SIGNATURE=false switches it off (local debugging)."""
    if (os.getenv("TWILIO_VALIDATE_SIGNATURE") or "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    return bool((os.getenv("TWILIO_AUTH_TOKEN") or "").strip())


def _public_urls(request: Request) -> list[str]:
    """The URL Twilio signed. Behind Render / ngrok the app sees http://internal-host, so rebuild it."""
    path = request.url.path + (f"?{request.url.query}" if request.url.query else "")
    base = (os.getenv("PUBLIC_BASE_URL") or "").strip().rstrip("/")
    if base:
        return [base + path]
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    proto = (request.headers.get("x-forwarded-proto") or request.url.scheme).split(",")[0].strip()
    return [f"{proto}://{host}{path}", f"https://{host}{path}"]


async def verify_twilio(request: Request, x_twilio_signature: str | None = Header(None)):
    """Reject webhook calls that weren't signed by Twilio with our auth token (stops fake replies / fake SOS)."""
    if not _signature_required():
        return
    from twilio.request_validator import RequestValidator
    validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN", "").strip())
    params = dict(await request.form())
    if not x_twilio_signature or not any(validator.validate(u, params, x_twilio_signature)
                                         for u in _public_urls(request)):
        raise HTTPException(403, "Invalid Twilio signature")


# ---------------- who can trigger outgoing messages ----------------

def staff_or_cron(x_role: str | None = Header(None), x_user_id: str | None = Header(None),
                  x_access_code: str | None = Header(None), x_cron_secret: str | None = Header(None),
                  db=Depends(get_db)) -> Actor:
    """Doctor / care team (normal X-Role auth + X-Access-Code when DEMO_ACCESS_CODE is set),
    or the daily scheduler presenting CRON_SECRET. In /docs: x-role = doctor, x-user-id = doc_mehta."""
    secret = (os.getenv("CRON_SECRET") or "").strip()
    if secret and x_cron_secret and hmac.compare_digest(x_cron_secret.encode(), secret.encode()):
        return SYSTEM
    if "x_access_code" in inspect.signature(get_actor).parameters:      # core's access-code check
        actor = get_actor(x_role=x_role, x_user_id=x_user_id, x_access_code=x_access_code, db=db)
    else:                                                                 # older core: enforce it here
        expected = os.getenv("DEMO_ACCESS_CODE") or ""
        if expected and not hmac.compare_digest((x_access_code or "").encode(), expected.encode()):
            raise HTTPException(401, "Access code required")
        actor = get_actor(x_role=x_role, x_user_id=x_user_id, db=db)
    require(actor, *STAFF)
    return actor


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
    """The numbered items the patient is answering: the last checklist sent (if < 24 h old), else today's.

    The sent order lives in the audit log (not memory), so it survives restarts and works with several workers.
    """
    sent = (db.query(AuditLog)
            .filter(AuditLog.action == SENT_ACTION, AuditLog.entity_id == patient_id,
                    AuditLog.timestamp >= utcnow() - WINDOW)
            .order_by(AuditLog.timestamp.desc()).first())
    if sent and (sent.after or {}).get("event_ids"):
        rows = [db.get(CareEvent, eid) for eid in sent.after["event_ids"]]
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


@router.post("/webhook", dependencies=[Depends(verify_twilio)])
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
        trigger_sos(db, actor, p.id, "whatsapp")          # core raises the SOS item AND alerts caregivers
        notified = messages.recently_notified(db, p)
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


def deliver_checklist(db, p: Patient, actor: Actor = SYSTEM) -> dict:
    """Render + send today's ONE checklist and record its numbering. Used by the route and by whatsapp.daily."""
    if not can_message(p.journey_state):
        return {"sent": False, "reason": f"Messaging paused for journey state {p.journey_state}"}
    items, _ = checklist.todays_items(db, p.id)
    body = messages.render_checklist(p, [to_dict(i) for i in items])
    sent, error = messages.send_detail(p.phone_whatsapp, body)
    audit.log(db, actor, SENT_ACTION, "patient", p.id, None,
              {"event_ids": [i.id for i in items], "sent": sent})
    db.commit()
    out = {"sent": sent, "preview": body, "items": len(items), "to": messages.mask_phone(p.phone_whatsapp)}
    if not sent:
        out["error"] = error
    return out


@router.post("/send-checklist/{patient_id}")
def send_checklist(patient_id: str, db=Depends(get_db), actor: Actor = Depends(staff_or_cron)):
    """Doctor / care team only (or the scheduler with X-Cron-Secret) — stops strangers spending Twilio credit."""
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    return deliver_checklist(db, p, actor)
