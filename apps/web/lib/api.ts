// The browser/client API. Server Components use lib/server-api.ts so they can
// forward the session access-code cookie to FastAPI.
import type {
  Patient, AttentionItem, DashboardOverview, Patient360, DailyChecklist, CarePlanDraft,
CarePlanItem, CarePlanItemPatch, CarePlanDeleteResult, CopilotItem, CareEvent,
EventStatus, PatientQuery, Role, CaregiverView, Caregiver, Report,
} from "./types";
import patientsMock from "@/mocks/patients.json";
import attentionMock from "@/mocks/attention.json";
import overviewMock from "@/mocks/overview.json";
import p360Mock from "@/mocks/patient360_rajesh.json";
import checklistMock from "@/mocks/checklist_rajesh.json";
import draftMock from "@/mocks/copilot_draft.json";
import { getBrowserAccessCode } from "./access-code";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export type ActorRef = { role: Role; userId: string };

export type EnrollmentPayload = {
  name: string;
  age: number;
  gender: string;
  preferred_language: string;
  phone: string;
  abha_id?: string | null;
  diagnosis_label: string;
  regimen_label: string;
  cycle_current: number;
  cycle_total: number;
};

export type EnrollmentResult = {
  patient: Patient;
  login_id: string;
  whatsapp_sent: boolean;
  warning?: string;
  demo_password?: string;
};

export type CaregiverInviteResult = {
  caregiver: Caregiver;
  login_id: string;
  whatsapp_sent: boolean;
  warning?: string;
  password?: string;
  demo_password?: string;
};

export type CaregiverLoginResult = {
  ok: boolean;
  caregiver_id: string;
  name: string;
  patient_id: string;
};

export type PatientLoginResult = {
  ok: boolean;
  patient_id: string;
  name: string;
  must_change: boolean;
};

let role: Role = "doctor";
let userId = "doc_mehta";

export function setActor(r: Role, id: string) {
  role = r;
  userId = id;
}

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`[${status}] ${detail}`);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

async function req<T>(path: string, init?: RequestInit, actor?: ActorRef): Promise<T> {
  const who = actor ?? { role, userId };
  const accessCode = getBrowserAccessCode();
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-Role": who.role,
      "X-User-Id": who.userId,
      ...(accessCode ? { "X-Access-Code": accessCode } : {}),
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = await res.text();
    try {
      const parsed = JSON.parse(detail);
      detail = parsed.detail ?? detail;
    } catch {
      // Keep the plain-text backend response.
    }
    if (res.status === 401 && /access code required/i.test(detail) && typeof window !== "undefined") {
      window.location.assign("/access");
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

const mock = <T,>(data: unknown) => Promise.resolve(data as T);

function attentionQuery(filters?: {
  label?: string;
  patient_id?: string;
  assigned_to?: string;
  status?: string;
}) {
  const p = new URLSearchParams();
  Object.entries(filters ?? {}).forEach(([key, value]) => {
    if (value) p.set(key, value);
  });
  const q = p.toString();
  return q ? `/attention?${q}` : "/attention";
}

export const api = {
  patients: () => USE_MOCKS ? mock<Patient[]>(patientsMock) : req<Patient[]>("/patients"),
  patient360: (id: string) => USE_MOCKS ? mock<Patient360>(p360Mock) : req<Patient360>(`/patients/${id}/360`),
  attention: (filters?: { label?: string; patient_id?: string; assigned_to?: string; status?: string }) =>
    USE_MOCKS ? mock<AttentionItem[]>(attentionMock) : req<AttentionItem[]>(attentionQuery(filters)),
  attentionMine: (user = "nurse_anita") =>
    USE_MOCKS
      ? mock<AttentionItem[]>((attentionMock as AttentionItem[]).filter(x => x.assigned_to === user))
      : req<AttentionItem[]>("/attention/mine", undefined, { role: "care_team", userId: user }),
  overview: () => USE_MOCKS ? mock<DashboardOverview>(overviewMock) : req<DashboardOverview>("/dashboard/overview"),
  checklistToday: (id: string) =>
    USE_MOCKS ? mock<DailyChecklist>(checklistMock) : req<DailyChecklist>(`/patients/${id}/checklist/today`),

  caregiverView: (id: string) =>
    USE_MOCKS
      ? mock<CaregiverView>({
          caregiver: {
            id: "cg_sunita",
            patient_id: "p_rajesh",
            name: "Sunita Kumar",
            relation: "Wife",
            phone_whatsapp: "",
            type: "family",
            consent_status: "GRANTED",
            permissions: { view_journey: true, upload_reports: true, receive_escalations: true },
          },
          patient: {
            id: "p_rajesh",
            name: "Rajesh Kumar",
            journey_state: "ACTIVE_TREATMENT",
            preferred_language: "Hindi",
          },
          upcoming: [],
          recent: [],
          can_upload_reports: true,
          receives_escalations: true,
        })
      : req<CaregiverView>(`/caregivers/${id}/view`, undefined, { role: "caregiver", userId: id }),

  carePlan: (id: string) =>
    USE_MOCKS ? mock<CarePlanItem[]>((p360Mock as unknown as Patient360).care_plan) : req<CarePlanItem[]>(`/patients/${id}/careplan`),

  updateCarePlanItem: (id: string, patch: CarePlanItemPatch) =>
  USE_MOCKS
    ? mock<CarePlanItem>({
        ...((p360Mock as unknown as Patient360).care_plan.find(
          x => x.id === id
        ) as CarePlanItem),
        ...patch,
      })
    : req<CarePlanItem>(
        `/careplan/items/${id}`,
        {
          method: "PATCH",
          body: JSON.stringify(patch),
        }
      ),

deleteCarePlanItem: (id: string) =>
  USE_MOCKS
    ? mock<CarePlanDeleteResult>({
        id,
        patient_id: "",
        removed: true,
        future_events_removed: 0,
        historical_events_preserved: 0,
      })
    : req<CarePlanDeleteResult>(
        `/careplan/items/${id}`,
        { method: "DELETE" }
      ),

  createDraft: (patient_id: string, raw_text: string) =>
    USE_MOCKS ? mock<CarePlanDraft>(draftMock)
      : req<CarePlanDraft>("/careplan/draft", { method: "POST", body: JSON.stringify({ patient_id, raw_text }) }),
  updateDraft: (id: string, items: CopilotItem[]) =>
    USE_MOCKS ? mock<CarePlanDraft>({ ...draftMock, items })
      : req<CarePlanDraft>(`/careplan/draft/${id}`, { method: "PUT", body: JSON.stringify({ items }) }),
  approveDraft: (id: string) =>
    USE_MOCKS ? mock<CareEvent[]>([]) : req<CareEvent[]>(`/careplan/draft/${id}/approve`, { method: "POST" }),

  markPatientReviewed: (id: string) =>
    USE_MOCKS ? mock<Patient>({ id } as Patient)
      : req<Patient>(`/patients/${id}/mark-reviewed`, { method: "POST" }, { role: "doctor", userId: "doc_mehta" }),

  markReportReviewed: (id: string) =>
    USE_MOCKS ? mock<Report>({ id, reviewed: true } as Report)
      : req<Report>(`/reports/${id}/reviewed`, { method: "PATCH" }, { role: "doctor", userId: "doc_mehta" }),

  setEventStatus: (id: string, status: EventStatus, actor?: ActorRef) =>
    USE_MOCKS ? mock<CareEvent>({ id, status } as CareEvent)
      : req<CareEvent>(`/events/${id}/status`, { method: "PATCH", body: JSON.stringify({ status }) }, actor),

  updateAttention: (
    id: string,
    patch: { status?: string; assigned_to?: string },
    actor?: ActorRef,
  ) =>
    USE_MOCKS ? mock<AttentionItem>({ id, ...patch } as AttentionItem)
      : req<AttentionItem>(`/attention/${id}`, { method: "PATCH", body: JSON.stringify(patch) }, actor),

  sendQuery: (patient_id: string, text: string, actor?: ActorRef) =>
    USE_MOCKS ? mock<PatientQuery>({})
      : req<PatientQuery>("/queries", { method: "POST", body: JSON.stringify({ patient_id, text, channel: "app" }) }, actor),

  updateQuery: (
  id: string,
  status: string,
  response?: string
) =>
  USE_MOCKS
    ? mock<PatientQuery>({
        id,
        status,
        response,
      } as PatientQuery)
    : req<PatientQuery>(
        `/queries/${id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            status,
            response: response || null,
          }),
        }
      ),

  sendEnrollmentOtp: (phone: string) =>
    req<{ sent: boolean; expires_in_minutes: number; phone: string; demo_otp?: string }>(
      "/patients/enrollment/send-otp",
      { method: "POST", body: JSON.stringify({ phone }) },
      { role: "doctor", userId: "doc_mehta" },
    ),

  verifyEnrollmentOtp: (phone: string, otp: string) =>
    req<{ verified: boolean; phone: string }>(
      "/patients/enrollment/verify-otp",
      { method: "POST", body: JSON.stringify({ phone, otp }) },
      { role: "doctor", userId: "doc_mehta" },
    ),

  enrollPatient: (payload: EnrollmentPayload) =>
    req<EnrollmentResult>(
      "/patients/enroll",
      { method: "POST", body: JSON.stringify(payload) },
      { role: "doctor", userId: "doc_mehta" },
    ),

  patientLogin: (patient_id: string, password: string) =>
    req<PatientLoginResult>(
      "/patient-auth/login",
      { method: "POST", body: JSON.stringify({ patient_id, password }) },
      { role: "patient", userId: patient_id || "patient_login" },
    ),

  addCaregiver: (patient_id: string, payload: {name:string; relation:string; phone_whatsapp:string; type?:string}) =>
    req<CaregiverInviteResult>(
      `/patients/${patient_id}/caregivers`,
      { method: "POST", body: JSON.stringify(payload) },
      { role: "patient", userId: patient_id },
    ),

  caregiverLogin: (caregiver_id: string, password: string) =>
    req<CaregiverLoginResult>(
      "/caregiver-auth/login",
      { method: "POST", body: JSON.stringify({ caregiver_id, password }) },
      { role: "caregiver", userId: caregiver_id || "caregiver_login" },
    ),

  acceptCaregiver: (id: string) =>
    req<Caregiver>(`/caregivers/${id}/accept`, { method: "POST" }, { role: "caregiver", userId: id }),
  revokeCaregiver: (id: string, actor?: ActorRef) =>
    req<Caregiver>(`/caregivers/${id}/revoke`, { method: "POST" }, actor),
  reinviteCaregiver: (id: string, actor?: ActorRef) =>
    req<Caregiver>(`/caregivers/${id}/reinvite`, { method: "POST" }, actor),
  updateCaregiverPermissions: (id: string, permissions: Caregiver["permissions"], actor?: ActorRef) =>
    req<Caregiver>(`/caregivers/${id}`, { method: "PATCH", body: JSON.stringify({ permissions }) }, actor),

  sos: (patient_id: string, actor?: ActorRef) =>
    USE_MOCKS ? mock<AttentionItem>({})
      : req<AttentionItem>("/sos", { method: "POST", body: JSON.stringify({ patient_id, channel: "app" }) }, actor),
};
