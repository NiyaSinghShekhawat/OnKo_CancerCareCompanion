import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import type {
  Patient, AttentionItem, DashboardOverview, Patient360, DailyChecklist,
  CarePlanItem, Role, CaregiverView,
} from "./types";
import patientsMock from "@/mocks/patients.json";
import attentionMock from "@/mocks/attention.json";
import overviewMock from "@/mocks/overview.json";
import p360Mock from "@/mocks/patient360_rajesh.json";
import checklistMock from "@/mocks/checklist_rajesh.json";
import { ACCESS_CODE_COOKIE } from "./access-code";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS === "true";

export type ServerActor = { role: Role; userId: string };
export const DOCTOR_ACTOR: ServerActor = { role: "doctor", userId: "doc_mehta" };
export const NURSE_ACTOR: ServerActor = { role: "care_team", userId: "nurse_anita" };

function sessionAccessCode() {
  const raw = cookies().get(ACCESS_CODE_COOKIE)?.value ?? "";
  if (!raw) return "";
  try {
    return decodeURIComponent(raw);
  } catch {
    return raw;
  }
}

async function req<T>(path: string, actor: ServerActor = DOCTOR_ACTOR): Promise<T> {
  const accessCode = sessionAccessCode();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      "X-Role": actor.role,
      "X-User-Id": actor.userId,
      ...(accessCode ? { "X-Access-Code": accessCode } : {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail = await res.text();
    try {
      const parsed = JSON.parse(detail);
      detail = parsed.detail ?? detail;
    } catch {
      // Keep the backend response as text.
    }
    if (res.status === 401 && /access code required/i.test(detail)) {
      redirect("/access");
    }
    if (res.status === 401) {
      redirect("/access-denied?status=401");
    }
    if (res.status === 403) {
      redirect("/access-denied?status=403");
    }
    throw new Error(`[${res.status}] ${detail}`);
  }
  return res.json() as Promise<T>;
}

const mock = <T,>(data: unknown) => Promise.resolve(data as T);

function attentionPath(filters?: {
  label?: string;
  patient_id?: string;
  assigned_to?: string;
  status?: string;
}) {
  const params = new URLSearchParams();
  Object.entries(filters ?? {}).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = params.toString();
  return query ? `/attention?${query}` : "/attention";
}

export const serverApi = {
  patients: (actor: ServerActor = DOCTOR_ACTOR) =>
    USE_MOCKS ? mock<Patient[]>(patientsMock) : req<Patient[]>("/patients", actor),

  patient360: (id: string, actor: ServerActor = DOCTOR_ACTOR) =>
    USE_MOCKS ? mock<Patient360>(p360Mock) : req<Patient360>(`/patients/${id}/360`, actor),

  attention: (
    filters?: { label?: string; patient_id?: string; assigned_to?: string; status?: string },
    actor: ServerActor = DOCTOR_ACTOR,
  ) =>
    USE_MOCKS ? mock<AttentionItem[]>(attentionMock) : req<AttentionItem[]>(attentionPath(filters), actor),

  attentionMine: (actor: ServerActor = NURSE_ACTOR) =>
    USE_MOCKS
      ? mock<AttentionItem[]>((attentionMock as AttentionItem[]).filter(item => item.assigned_to === actor.userId))
      : req<AttentionItem[]>("/attention/mine", actor),

  overview: (actor: ServerActor = DOCTOR_ACTOR) =>
    USE_MOCKS ? mock<DashboardOverview>(overviewMock) : req<DashboardOverview>("/dashboard/overview", actor),

  checklistToday: (id: string, actor: ServerActor = { role: "patient", userId: id }) =>
    USE_MOCKS ? mock<DailyChecklist>(checklistMock) : req<DailyChecklist>(`/patients/${id}/checklist/today`, actor),

  carePlan: (id: string, actor: ServerActor = DOCTOR_ACTOR) =>
    USE_MOCKS
      ? mock<CarePlanItem[]>((p360Mock as unknown as Patient360).care_plan)
      : req<CarePlanItem[]>(`/patients/${id}/careplan`, actor),

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
      : req<CaregiverView>(`/caregivers/${id}/view`, { role: "caregiver", userId: id }),
};
