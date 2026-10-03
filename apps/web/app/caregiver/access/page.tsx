import CaregiverShell from "@/components/CaregiverShell";
import {CheckCircle2,LockKeyhole,ShieldCheck} from "lucide-react";
import {serverApi} from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic="force-dynamic";

export default async function CaregiverAccess(){
  const caregiverId=currentCaregiverId();
  const view=await serverApi.caregiverView(caregiverId);
  const caregiver={id:view.caregiver.id,name:view.caregiver.name,relation:view.caregiver.relation};
  const scopes=[
    ["View care journey",true,"Minimized upcoming and recent care activities"],
    ["Upload reports",view.can_upload_reports,"Add reports on the patient's behalf"],
    ["Receive escalations",view.receives_escalations,"Receive caregiver-directed escalation notifications"],
  ] as const;

  return <CaregiverShell patient={view.patient} caregiver={caregiver}>
    <div className="mx-auto max-w-4xl space-y-6">
      <section className="rounded-3xl bg-white p-6 shadow-sm sm:p-8">
        <div className="flex items-start gap-4"><span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-onko-softteal text-onko-teal"><ShieldCheck/></span><div><p className="onko-eyebrow">Access & consent</p><h1 className="mt-1 text-[28px] font-bold sm:text-[36px]">{view.caregiver.name}</h1><p className="mt-1 text-[14px] text-onko-muted">{view.caregiver.relation} · caregiver</p></div></div>
        <div className="mt-6 rounded-2xl bg-onko-surface p-4"><p className="text-[12px] font-semibold text-onko-muted">PATIENT CONSENT</p><p className="mt-1 text-[17px] font-bold text-onko-teal">{view.caregiver.consent_status}</p></div>
      </section>
      <section className="rounded-3xl bg-white p-6 shadow-sm sm:p-8"><h2 className="text-[21px] font-bold">What is shared</h2><p className="mt-1 text-[13px] leading-5 text-onko-muted">This dashboard only shows information the patient has chosen to share.</p><div className="mt-5 space-y-3">{scopes.map(([name,on,desc])=><div key={name} className="flex items-start gap-3 rounded-2xl bg-onko-surface p-4"><CheckCircle2 className={"mt-0.5 shrink-0 "+(on?"text-onko-teal":"text-onko-muted")} size={20}/><div><strong className="text-[15px]">{name}</strong><p className="mt-1 text-[12px] leading-5 text-onko-muted">{desc}</p></div></div>)}</div></section>
      <section className="flex items-start gap-3 rounded-2xl border border-[#D7EEEA] bg-[#F4FCFA] p-5"><LockKeyhole className="mt-0.5 shrink-0 text-onko-teal" size={20}/><div><h2 className="text-[15px] font-bold">Patient-controlled access</h2><p className="mt-1 text-[13px] leading-5 text-onko-muted">Permission changes and access revocation are controlled from the patient's Profile & access page. Caregivers cannot revoke or expand their own access.</p></div></section>
    </div>
  </CaregiverShell>
}
