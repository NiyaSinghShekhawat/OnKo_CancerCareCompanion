// Mirrors contracts/schemas.json — do not rename fields.
export type Role = "doctor" | "patient" | "caregiver" | "care_team";
export type EventType = "MEDICATION" | "INVESTIGATION" | "TREATMENT" | "APPOINTMENT" | "MILESTONE";
export type EventStatus = "UPCOMING" | "CURRENT" | "COMPLETED" | "REPORTED_MISSED" | "NO_RESPONSE" | "RESCHEDULED" | "CONFLICTING";
export type JourneyState = "ACTIVE_TREATMENT" | "REMISSION_SURVIVORSHIP" | "RELAPSE" | "TRANSFER_OF_CARE" | "PALLIATIVE" | "DECEASED";
export type AttentionLabel = "NEEDS_REVIEW" | "FOLLOW_UP" | "QUERY" | "SOS";
export type AttentionStatus = "PENDING" | "ACKNOWLEDGED" | "HANDLED" | "CLOSED";
export type QueryCategory = "ADMINISTRATIVE" | "MEDICATION" | "SYMPTOM_CONCERN";

export interface Patient {
  id: string; name: string; age: number; gender: string; abha_id: string | null;
  phone_whatsapp: string; preferred_language: string; diagnosis_label: string;
  regimen_label: string; cycle_current: number; cycle_total: number;
  journey_state: JourneyState; journey_state_changed_at: string | null; previous_journey_state: JourneyState | null;
  journey_chapter: number; doctor_id: string; last_reviewed_at: string | null; created_at: string;
}

export interface CareEvent {
  id: string; patient_id: string; type: EventType; title: string; details: Record<string, string>;
  scheduled_at: string; status: EventStatus; response_state: string | null; responded_at: string | null;
  source: string; care_plan_item_id: string | null; journey_chapter: number;
}

export interface CarePlanItem {
  id: string; patient_id: string; type: EventType; title: string; details: Record<string, string>;
  start_date: string; end_date: string | null; recurrence: string | null; approved_by: string; approved_at: string;
}

export type CarePlanItemPatch = Partial<Pick<CarePlanItem, "type" | "title" | "details" | "start_date" | "end_date" | "recurrence">>;
export interface CarePlanDeleteResult {
  id: string; patient_id: string; removed: boolean; future_events_removed: number; historical_events_preserved: number;
}

export interface CopilotItem {
  type: EventType; title: string; details: Record<string, string>; start_date: string;
  end_date: string | null; recurrence: string | null; source_span: string;
}

export interface CarePlanDraft {
  id: string; patient_id: string; raw_text: string; items: CopilotItem[];
  status: "DRAFT" | "APPROVED" | "REJECTED"; created_by: string; created_at: string;
  warnings?: string[]; ok?: boolean;
}

export interface AttentionItem {
  id: string; patient_id: string; patient_name: string; label: AttentionLabel; reasons: string[];
  status: AttentionStatus; assigned_to: string | null; created_at: string;
}

export interface PatientQuery {
  id: string; patient_id: string; text: string; channel: "whatsapp" | "app"; category: QueryCategory;
  summary: string; route_to: string; status: string; response: string | null; created_at: string;
}

export interface ExtractedValue { name: string; value: string; unit: string; reference_range_as_printed: string; source_line: string; }

export interface Report {
  id: string; patient_id: string; title: string; text: string; extracted_values: ExtractedValue[];
  uploaded_by_role: Role; uploaded_at: string; reviewed: boolean;
}

export interface Caregiver {
  id: string; patient_id: string; name: string; relation: string; phone_whatsapp: string;
  type: "family" | "professional"; consent_status: "PENDING" | "GRANTED" | "REVOKED";
  permissions: { view_journey: boolean; upload_reports: boolean; receive_escalations: boolean };
}

export interface MinimizedCareEvent {
  id: string; type: EventType; title: string; scheduled_at: string; status: EventStatus;
}

export interface CaregiverView {
  caregiver: Caregiver;
  patient: {
    id: string; name: string; journey_state: JourneyState; preferred_language: string;
  };
  upcoming: MinimizedCareEvent[];
  recent: MinimizedCareEvent[];
  can_upload_reports: boolean;
  receives_escalations: boolean;
}

export interface ReviewSummary { ok: boolean; since: string | null; bullets: string[]; upcoming: string[]; }

export interface Patient360 {
  patient: Patient; care_plan: CarePlanItem[]; timeline: CareEvent[]; open_queries: PatientQuery[];
  query_history?: PatientQuery[];
  reports: Report[]; caregivers: Caregiver[]; attention: AttentionItem[]; attention_history?: AttentionItem[];
  since_last_review: ReviewSummary;
}

export interface DailyChecklist {
  patient_id: string; date: string; items: CareEvent[]; window_closes_at: string; sent: boolean;
  paused: boolean; reason: string | null;
}

export interface DashboardOverview {
  active_patients: number; consultations_today: number; missed_activities: number;
  open_queries: number; reports_pending_review: number; sos_open: number;
}
