import CaregiverShell from "@/components/CaregiverShell";
import CaregiverEventCard from "@/components/CaregiverEventCard";
import { serverApi } from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic = "force-dynamic";
export default async function CaregiverJourney() {
  const caregiverId=currentCaregiverId();
  const view = await serverApi.caregiverView(caregiverId);
  const CAREGIVER = { id: view.caregiver.id, name: view.caregiver.name, relation: view.caregiver.relation };
  const events = [...view.recent, ...view.upcoming].sort((a,b)=>new Date(a.scheduled_at).getTime()-new Date(b.scheduled_at).getTime());
  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-4xl">
        <p className="onko-eyebrow">Shared care journey</p>
        <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">{view.patient.name}&apos;s journey</h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">Only minimized activities from the consented caregiver view are shown.</p>
        <div className="mt-7 grid gap-4">{events.length?events.map(e=><CaregiverEventCard key={e.id} event={e}/>):<div className="rounded-3xl bg-white p-6 text-[14px] text-onko-muted shadow-sm">No shared activities are currently available.</div>}</div>
      </div>
    </CaregiverShell>
  );
}
