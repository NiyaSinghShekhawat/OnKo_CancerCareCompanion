// The ONLY place that talks to the backend. Toggle mocks with NEXT_PUBLIC_USE_MOCKS.
import type {
  Patient, AttentionItem, DashboardOverview, Patient360, DailyChecklist, CarePlanDraft,
  CarePlanItem, CarePlanItemPatch, CarePlanDeleteResult, CopilotItem, CareEvent, EventStatus, PatientQuery, Role,
} from "./types";
import patientsMock from "@/mocks/patients.json";
import attentionMock from "@/mocks/attention.json";
import overviewMock from "@/mocks/overview.json";
import p360Mock from "@/mocks/patient360_rajesh.json";
import checklistMock from "@/mocks/checklist_rajesh.json";
import draftMock from "@/mocks/copilot_draft.json";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

let role: Role = "doctor";
let userId = "doc_mehta";
export function setActor(r: Role, id: string) { role = r; userId = id; }

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", "X-Role": role, "X-User-Id": userId, ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

const mock = <T,>(data: unknown) => Promise.resolve(data as T);

export const api = {
  patients: () => USE_MOCKS ? mock<Patient[]>(patientsMock) : req<Patient[]>("/patients"),
  patient360: (id: string) => USE_MOCKS ? mock<Patient360>(p360Mock) : req<Patient360>(`/patients/${id}/360`),
  attention: () => USE_MOCKS ? mock<AttentionItem[]>(attentionMock) : req<AttentionItem[]>("/attention"),
  overview: () => USE_MOCKS ? mock<DashboardOverview>(overviewMock) : req<DashboardOverview>("/dashboard/overview"),
  checklistToday: (id: string) => USE_MOCKS ? mock<DailyChecklist>(checklistMock) : req<DailyChecklist>(`/patients/${id}/checklist/today`),

  carePlan: (id: string) => USE_MOCKS ? mock<CarePlanItem[]>((p360Mock as Patient360).care_plan) : req<CarePlanItem[]>(`/patients/${id}/careplan`),

  updateCarePlanItem: (id: string, patch: CarePlanItemPatch) =>
    USE_MOCKS ? mock<CarePlanItem>({ ...((p360Mock as Patient360).care_plan.find(x => x.id === id) as CarePlanItem), ...patch })
      : req<CarePlanItem>(`/careplan/items/${id}`, { method: "PATCH", body: JSON.stringify(patch) }),
  deleteCarePlanItem: (id: string) =>
    USE_MOCKS ? mock<CarePlanDeleteResult>({ id, patient_id: "", removed: true, future_events_removed: 0, historical_events_preserved: 0 })
      : req<CarePlanDeleteResult>(`/careplan/items/${id}`, { method: "DELETE" }),

  createDraft: (patient_id: string, raw_text: string) =>
    USE_MOCKS ? mock<CarePlanDraft>(draftMock)
      : req<CarePlanDraft>("/careplan/draft", { method: "POST", body: JSON.stringify({ patient_id, raw_text }) }),
  updateDraft: (id: string, items: CopilotItem[]) =>
    USE_MOCKS ? mock<CarePlanDraft>({ ...draftMock, items })
      : req<CarePlanDraft>(`/careplan/draft/${id}`, { method: "PUT", body: JSON.stringify({ items }) }),
  approveDraft: (id: string) =>
    USE_MOCKS ? mock<CareEvent[]>([]) : req<CareEvent[]>(`/careplan/draft/${id}/approve`, { method: "POST" }),

  setEventStatus: (id: string, status: EventStatus) =>
    USE_MOCKS ? mock<CareEvent>({}) : req<CareEvent>(`/events/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }),
  updateAttention: (id: string, status: string, assigned_to?: string | null) =>
    USE_MOCKS ? mock<AttentionItem>({ id, status, assigned_to } as AttentionItem)
      : req<AttentionItem>(`/attention/${id}`, {
          method: "PATCH",
          body: JSON.stringify(assigned_to === undefined ? { status } : { status, assigned_to }),
        }),
  sendQuery: (patient_id: string, text: string) =>
    USE_MOCKS ? mock<PatientQuery>({}) : req<PatientQuery>("/queries", { method: "POST", body: JSON.stringify({ patient_id, text, channel: "app" }) }),
  updateQuery: (id: string, status: string, response?: string) =>
    USE_MOCKS ? mock<PatientQuery>({ id, status, response } as PatientQuery)
      : req<PatientQuery>(`/queries/${id}`, { method: "PATCH", body: JSON.stringify({ status, response: response || null }) }),
  sos: (patient_id: string) =>
    USE_MOCKS ? mock<AttentionItem>({}) : req<AttentionItem>("/sos", { method: "POST", body: JSON.stringify({ patient_id, channel: "app" }) }),
};
