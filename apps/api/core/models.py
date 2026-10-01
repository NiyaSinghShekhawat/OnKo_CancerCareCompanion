"""Tables mirror contracts/schemas.json. Field names must stay identical."""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, JSON, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core.db import Base


def _id() -> str:
    return uuid.uuid4().hex[:12]


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)  # doctor | care_team | patient | caregiver


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    name: Mapped[str] = mapped_column(String)
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[str] = mapped_column(String)
    abha_id: Mapped[str | None] = mapped_column(String, nullable=True)
    phone_whatsapp: Mapped[str] = mapped_column(String)
    preferred_language: Mapped[str] = mapped_column(String, default="English")
    diagnosis_label: Mapped[str] = mapped_column(String)
    regimen_label: Mapped[str] = mapped_column(String, default="")
    cycle_current: Mapped[int] = mapped_column(Integer, default=0)
    cycle_total: Mapped[int] = mapped_column(Integer, default=0)
    journey_state: Mapped[str] = mapped_column(String, default="ACTIVE_TREATMENT")
    journey_state_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    doctor_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"))
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CarePlanItem(Base):
    __tablename__ = "care_plan_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    start_date: Mapped[str] = mapped_column(String)
    end_date: Mapped[str | None] = mapped_column(String, nullable=True)
    recurrence: Mapped[str | None] = mapped_column(String, nullable=True)
    approved_by: Mapped[str] = mapped_column(String)
    approved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CarePlanDraft(Base):
    __tablename__ = "care_plan_drafts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    raw_text: Mapped[str] = mapped_column(Text)
    items: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="DRAFT")
    created_by: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CareEvent(Base):
    __tablename__ = "care_events"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    type: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="UPCOMING")
    response_state: Mapped[str | None] = mapped_column(String, nullable=True)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String, default="doctor")
    care_plan_item_id: Mapped[str | None] = mapped_column(String, nullable=True)


class AttentionItem(Base):
    __tablename__ = "attention_items"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    patient_name: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    assigned_to: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PatientQuery(Base):
    __tablename__ = "patient_queries"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    text: Mapped[str] = mapped_column(Text)
    channel: Mapped[str] = mapped_column(String, default="app")
    category: Mapped[str] = mapped_column(String, default="ADMINISTRATIVE")
    summary: Mapped[str] = mapped_column(Text, default="")
    route_to: Mapped[str] = mapped_column(String, default="admin_queue")
    status: Mapped[str] = mapped_column(String, default="OPEN")
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    title: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text)
    extracted_values: Mapped[list] = mapped_column(JSON, default=list)
    uploaded_by_role: Mapped[str] = mapped_column(String)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class Caregiver(Base):
    __tablename__ = "caregivers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    patient_id: Mapped[str] = mapped_column(String, ForeignKey("patients.id"))
    name: Mapped[str] = mapped_column(String)
    relation: Mapped[str] = mapped_column(String)
    phone_whatsapp: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String, default="family")
    consent_status: Mapped[str] = mapped_column(String, default="PENDING")
    permissions: Mapped[dict] = mapped_column(JSON, default=lambda: {
        "view_journey": True, "upload_reports": False, "receive_escalations": True})


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=_id)
    actor_id: Mapped[str] = mapped_column(String)
    actor_role: Mapped[str] = mapped_column(String)
    action: Mapped[str] = mapped_column(String)
    entity_type: Mapped[str] = mapped_column(String)
    entity_id: Mapped[str] = mapped_column(String)
    before: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    after: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
