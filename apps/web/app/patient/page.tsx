import Timeline from "@/components/Timeline";
import SOSButton from "@/components/SOSButton";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";
const PATIENT_ID = "p_rajesh"; // demo patient

export default async function PatientHome() {
  const d = await api.patient360(PATIENT_ID);
  const p = d.patient;
  return (
    <main className="max-w-4xl mx-auto px-6 py-10 md:px-8">
      <div className="flex items-center justify-between">
        <h1 className="text-4xl font-semibold">{p.name.split(" ")[0]}&apos;s care journey</h1>
        <SOSButton patientId={p.id} />
      </div>
      <div className="mt-6 bg-white border border-onko-line rounded-2xl p-6">
        <div className="text-base text-onko-ink/60">Doctor-approved regimen</div>
        <div className="mt-1 text-lg font-semibold">{p.regimen_label} · Cycle {p.cycle_current} of {p.cycle_total}</div>
      </div>
      <h2 className="text-2xl font-semibold mt-10 mb-4">Timeline</h2>
      <Timeline events={d.timeline} />
    </main>
  );
}
