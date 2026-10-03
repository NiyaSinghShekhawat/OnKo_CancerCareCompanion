import CaregiverShell from "@/components/CaregiverShell";
import CaregiverEventCard from "@/components/CaregiverEventCard";
import { Bell, ShieldAlert } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic = "force-dynamic";
export default async function CaregiverNotifications() {
  const caregiverId=currentCaregiverId();
  const view = await serverApi.caregiverView(caregiverId);
  const CAREGIVER = { id: view.caregiver.id, name: view.caregiver.name, relation: view.caregiver.relation };
  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-4xl">
        <p className="onko-eyebrow">Care coordination</p>
        <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">Notifications</h1>
        <p className="mt-2 text-[14px] leading-6 text-onko-muted">Only caregiver-directed coordination information permitted by the current consent is shown.</p>
        {view.receives_escalations?<div className="mt-7 grid gap-3"><div className="rounded-2xl bg-white p-5 shadow-sm"><div className="flex gap-3"><Bell className="text-onko-teal"/><div><strong>Escalation notifications enabled</strong><p className="mt-1 text-[12px] text-onko-muted">You may receive caregiver-directed escalation updates.</p></div></div></div>{view.upcoming.slice(0,4).map(e=><CaregiverEventCard key={e.id} event={e}/>)}</div>:<div className="mt-7 rounded-3xl bg-white p-7 text-center shadow-sm"><ShieldAlert className="mx-auto text-onko-muted"/><h2 className="mt-3 text-[20px] font-bold">Escalation notifications are not shared</h2><p className="mt-2 text-[14px] text-onko-muted">The patient has not granted this permission.</p></div>}
      </div>
    </CaregiverShell>
  );
}
