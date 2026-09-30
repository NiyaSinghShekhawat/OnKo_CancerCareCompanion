import Timeline from "@/components/Timeline";
import SOSButton from "@/components/SOSButton";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";
const PATIENT_ID = "p_rajesh"; // demo patient

export default async function PatientHome() {
  const d = await api.patient360(PATIENT_ID);
  const p = d.patient;
  return (
    <main className="max-w-xl mx-auto px-5 py-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{p.name.split(" ")[0]}&apos;s care journey</h1>
        <SOSButton patientId={p.id} />
      </div>
      <div className="mt-4 bg-white border border-onko-line rounded-lg p-4">
        <div className="text-sm text-onko-ink/60">Doctor-approved regimen</div>
        <div className="font-medium">{p.regimen_label} · Cycle {p.cycle_current} of {p.cycle_total}</div>
      </div>
      <h2 className="font-semibold mt-8 mb-3">Timeline</h2>
      <Timeline events={d.timeline} />
    </main>
  );
}
