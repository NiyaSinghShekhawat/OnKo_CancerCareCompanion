import CaregiverShell from "@/components/CaregiverShell";
import CaregiverEventCard from "@/components/CaregiverEventCard";
import { serverApi } from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic = "force-dynamic";
export default async function CaregiverMedications() {
  const caregiverId=currentCaregiverId();
  const view = await serverApi.caregiverView(caregiverId);
  const CAREGIVER = { id: view.caregiver.id, name: view.caregiver.name, relation: view.caregiver.relation };
  const meds = [...view.recent, ...view.upcoming].filter(e=>e.type==="MEDICATION");
  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-4xl">
        <p className="onko-eyebrow">Shared medication activity</p>
        <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">Medication</h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">Caregiver responses contain only the activity title, type, time and status. Dose details and clinical instructions are intentionally not exposed.</p>
        <div className="mt-7 grid gap-4">{meds.length?meds.map(e=><CaregiverEventCard key={e.id} event={e}/>):<div className="rounded-3xl bg-white p-6 text-onko-muted shadow-sm">No medication activity is currently shared.</div>}</div>
      </div>
    </CaregiverShell>
  );
}
