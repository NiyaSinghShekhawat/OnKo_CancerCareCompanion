from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from core.db import get_db
from core.auth import get_actor
from core.models import PatientQuery, Patient
from core.serialize import to_dict
from core.services import audit, attention
from ai.classify import classify_query

router = APIRouter(tags=["queries"])


class QueryIn(BaseModel):
    patient_id: str
    text: str
    channel: str = "app"


def create_query(db, actor, patient_id: str, text: str, channel: str) -> PatientQuery:
    """Also called by whatsapp/webhook.py."""
    p = db.get(Patient, patient_id)
    if not p:
        raise HTTPException(404, "Patient not found")
    c = classify_query(text)
    q = PatientQuery(patient_id=p.id, text=text, channel=channel, category=c["category"],
                     summary=c["summary"], route_to=c["route_to"])
    db.add(q)
    db.flush()
    if c["category"] in {"SYMPTOM_CONCERN", "MEDICATION"}:
        attention.raise_item(db, p, "QUERY", f"New patient concern logged: {c['summary']}")
    audit.log(db, actor, "query_created", "patient_query", q.id, None, c)
    db.commit()
    return q


@router.post("/queries")
def post_query(body: QueryIn, db=Depends(get_db), actor=Depends(get_actor)):
    return to_dict(create_query(db, actor, body.patient_id, body.text, body.channel))


@router.get("/queries")
def list_queries(status: str | None = None, db=Depends(get_db)):
    q = db.query(PatientQuery)
    if status:
        q = q.filter_by(status=status.upper())
    return [to_dict(x) for x in q.order_by(PatientQuery.created_at.desc())]


class QueryUpdate(BaseModel):
    status: str
    response: str | None = None


@router.patch("/queries/{qid}")
def update_query(qid: str, body: QueryUpdate, db=Depends(get_db), actor=Depends(get_actor)):
    q = db.get(PatientQuery, qid)
    if not q:
        raise HTTPException(404, "Not found")
    q.status, q.response = body.status, body.response or q.response
    audit.log(db, actor, "query_update", "patient_query", q.id, None, body.model_dump())
    db.commit()
    return to_dict(q)
