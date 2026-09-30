import Link from "next/link";
import {AlertCircle,CalendarClock,CheckCircle2,FileText,Pill,Route,ShieldCheck} from "lucide-react";
import CaregiverShell from "@/components/CaregiverShell";
import {api} from "@/lib/api";
import {fmtDate,fmtTime,statusText} from "@/lib/format";

export const dynamic="force-dynamic";

export default async function CaregiverHome(){
 const d=await api.patient360("p_rajesh");
 const caregiver=d.caregivers[0];
 if(!caregiver)return <main className="mx-auto max-w-xl p-8">No caregiver access is linked to this patient.</main>;
 const granted=caregiver.consent_status==="GRANTED", canView=granted&&caregiver.permissions.view_journey;
 const upcoming=d.timeline.filter(e=>["UPCOMING","CURRENT"].includes(e.status)).slice(0,3);
 const followUp=d.timeline.filter(e=>["REPORTED_MISSED","NO_RESPONSE","CONFLICTING"].includes(e.status));
 return <CaregiverShell patient={d.patient} caregiver={caregiver}>
  <div className="mx-auto max-w-5xl space-y-6">
   <section className="rounded-3xl bg-white p-5 shadow-sm sm:p-7">
    <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start"><div><p className="onko-eyebrow">Caregiver overview</p><h1 className="mt-1 text-[28px] font-bold tracking-tight sm:text-[36px]">Supporting {d.patient.name}</h1><p className="mt-2 max-w-2xl text-[14px] leading-6 text-onko-muted">A shared view of the care journey, limited to the information and actions {d.patient.name.split(" ")[0]} has consented to share with you.</p></div><Link href="/caregiver/access" className="onko-button-secondary shrink-0"><ShieldCheck size={17}/>View access</Link></div>
    <div className="mt-6 flex flex-wrap gap-2"><span className="rounded-full bg-onko-softteal px-3 py-1.5 text-[12px] font-semibold text-onko-teal">{caregiver.consent_status==="GRANTED"?"Consent active":"Consent "+caregiver.consent_status.toLowerCase()}</span><span className="rounded-full bg-onko-surface px-3 py-1.5 text-[12px] font-semibold text-onko-muted">{caregiver.relation}</span><span className="rounded-full bg-onko-surface px-3 py-1.5 text-[12px] font-semibold text-onko-muted">Cycle {d.patient.cycle_current} of {d.patient.cycle_total}</span></div>
   </section>
   {!canView?<section className="rounded-3xl bg-white p-7 text-center shadow-sm"><ShieldCheck className="mx-auto text-onko-teal"/><h2 className="mt-3 text-[20px] font-bold">Journey access is not currently shared</h2><p className="mx-auto mt-2 max-w-lg text-[14px] leading-6 text-onko-muted">Care information stays hidden unless the patient has granted caregiver journey access.</p></section>:<>
    <section className="grid gap-3 sm:grid-cols-3"><div className="rounded-2xl bg-white p-5 shadow-sm"><Route className="text-onko-teal" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">UPCOMING</p><p className="mt-1 text-[28px] font-bold">{upcoming.length}</p></div><div className="rounded-2xl bg-white p-5 shadow-sm"><AlertCircle className="text-onko-amber" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">RECORDED FOLLOW-UP</p><p className="mt-1 text-[28px] font-bold">{followUp.length}</p></div><div className="rounded-2xl bg-white p-5 shadow-sm"><FileText className="text-onko-teal" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">SHARED REPORTS</p><p className="mt-1 text-[28px] font-bold">{d.reports.length}</p></div></section>
    <section className="grid gap-6 lg:grid-cols-[1.35fr_.65fr]"><div className="rounded-3xl bg-white p-5 shadow-sm sm:p-6"><div className="flex items-center justify-between gap-3"><div><p className="onko-eyebrow">Coming up</p><h2 className="mt-1 text-[22px] font-bold">Care journey</h2></div><Link href="/caregiver/journey" className="text-[13px] font-semibold text-onko-teal">View journey →</Link></div><div className="mt-5 space-y-3">{upcoming.length?upcoming.map(e=><div key={e.id} className="rounded-2xl bg-onko-surface p-4"><div className="flex items-start justify-between gap-3"><div><p className="text-[12px] font-semibold text-onko-teal">{fmtDate(e.scheduled_at)} · {fmtTime(e.scheduled_at)}</p><h3 className="mt-1 text-[16px] font-bold">{e.title}</h3><p className="mt-1 text-[12px] capitalize text-onko-muted">{e.type.toLowerCase()}</p></div><span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-onko-muted">{statusText[e.status]}</span></div></div>):<p className="text-[14px] text-onko-muted">No upcoming recorded activities.</p>}</div></div>
     <div className="space-y-4"><Link href="/caregiver/medications" className="block rounded-3xl bg-white p-5 shadow-sm"><Pill className="text-onko-teal"/><h3 className="mt-4 text-[17px] font-bold">Medication</h3><p className="mt-1 text-[13px] leading-5 text-onko-muted">See medication activity shared by the patient.</p></Link><Link href="/caregiver/records" className="block rounded-3xl bg-white p-5 shadow-sm"><CalendarClock className="text-onko-teal"/><h3 className="mt-4 text-[17px] font-bold">Reports & records</h3><p className="mt-1 text-[13px] leading-5 text-onko-muted">{caregiver.permissions.upload_reports?"You may upload reports on the patient's behalf.":"View-only according to current consent."}</p></Link></div>
    </section>
    {followUp.length>0&&<section className="rounded-3xl bg-white p-5 shadow-sm sm:p-6"><div className="flex items-center gap-2"><CheckCircle2 size={19} className="text-onko-teal"/><h2 className="text-[19px] font-bold">Recent recorded updates</h2></div><div className="mt-4 space-y-2">{followUp.slice(0,3).map(e=><div key={e.id} className="rounded-xl bg-onko-surface p-4"><strong className="text-[14px]">{e.title}</strong><p className="mt-1 text-[12px] text-onko-muted">{statusText[e.status]} · {fmtDate(e.scheduled_at)}</p></div>)}</div></section>}
   </>}
   <p className="px-2 text-center text-[12px] leading-5 text-onko-muted">OnKo shows recorded activity shared by the patient. Clinical interpretation, prescriptions and treatment decisions remain with the care team.</p>
  </div>
 </CaregiverShell>
}