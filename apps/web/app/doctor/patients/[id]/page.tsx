import Link from "next/link";
import { CalendarDays, ClipboardList, FileText, MessageSquareText, UserRound, Users } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import Timeline from "@/components/Timeline";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
export const dynamic="force-dynamic";
export default async function Patient360Page({params}:{params:{id:string}}){
 const d=await api.patient360(params.id),p=d.patient,appointments=d.timeline.filter(e=>e.type==="APPOINTMENT");
 return <DoctorShell>
  <section className="onko-card overflow-hidden">
   <div className="flex flex-wrap items-start justify-between gap-5 p-6"><div className="flex gap-4"><div className="grid h-14 w-14 place-items-center rounded-full bg-onko-softteal text-onko-teal"><UserRound size={26}/></div><div><div className="flex flex-wrap items-center gap-2"><h1 className="text-[27px] font-bold tracking-tight">{p.name}</h1><span className="onko-chip bg-onko-teal text-white">{p.journey_state.replaceAll("_"," ").toLowerCase()}</span></div><p className="mt-1 text-[13px] text-onko-muted">{p.age} yrs · {p.gender} · {p.diagnosis_label}</p><p className="mt-2 text-[13px] font-semibold">{p.regimen_label} · Cycle {p.cycle_current} of {p.cycle_total}</p></div></div>
   <div className="flex flex-wrap gap-2"><Link href={"/doctor/careplan/"+p.id} className="onko-button-primary"><ClipboardList size={16}/>Edit Care Plan</Link><button className="onko-button-secondary"><FileText size={15}/>Add Record / Lab</button><button className="onko-button-secondary"><MessageSquareText size={15}/>Send Query</button></div></div>
   <div className="flex gap-1 overflow-x-auto border-t border-onko-line px-5 py-2 text-[12px] font-semibold">{["Overview","Care Journey","My Team","Medications","Treatments","Investigations","Reports","Appointments","Queries","Caregiver & Consent"].map((x,i)=><a key={x} href={i===0?"#overview":"#"+x.toLowerCase().replaceAll(" ","-").replace("&-","")} className={"whitespace-nowrap rounded-lg px-3 py-2 "+(i===0?"bg-onko-teal text-white":"text-onko-muted hover:bg-onko-softteal")}>{x}</a>)}</div>
  </section>
  <div id="overview" className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]">
   <div className="grid gap-5"><section className="onko-card p-5"><div className="flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.1em] text-onko-teal">Since your last review</p><h2 className="mt-1 text-[20px] font-bold">Recorded changes</h2></div><span className="text-[11px] text-onko-muted">{p.last_reviewed_at?"Last reviewed "+fmtDate(p.last_reviewed_at):"No previous review recorded"}</span></div><div className="mt-4 grid gap-2">{d.since_last_review.bullets.map(b=><div key={b} className="rounded-xl bg-onko-softteal/60 px-4 py-3 text-[13px] leading-5">{b}</div>)}</div></section>
   <section className="onko-card p-5"><div className="mb-4 flex items-center justify-between"><div><p className="text-[10px] font-bold uppercase tracking-[.1em] text-onko-teal">Longitudinal record</p><h2 className="mt-1 text-[20px] font-bold">Care Journey</h2></div><CalendarDays size={18} className="text-onko-teal"/></div><Timeline events={d.timeline}/></section></div>
   <aside className="grid content-start gap-4"><div className="grid grid-cols-3 gap-2"><div className="onko-card p-4"><FileText size={17} className="text-onko-teal"/><p className="mt-2 text-[26px] font-bold">{d.reports.length}</p><p className="text-[11px] text-onko-muted">Reports</p></div><div className="onko-card p-4"><MessageSquareText size={17} className="text-onko-teal"/><p className="mt-2 text-[26px] font-bold">{d.open_queries.length}</p><p className="text-[11px] text-onko-muted">Queries</p></div><div className="onko-card p-4"><Users size={17} className="text-onko-teal"/><p className="mt-2 text-[26px] font-bold">{d.caregivers.length}</p><p className="text-[11px] text-onko-muted">Caregivers</p></div></div>
   <section id="reports" className="onko-card p-5"><h2 className="text-[17px] font-bold">Reports</h2><div className="mt-3 grid gap-3">{d.reports.map(r=><div key={r.id} className="rounded-xl bg-onko-surface p-3 text-[13px]"><div className="flex justify-between gap-2"><strong>{r.title}</strong><span className="text-[11px] text-onko-muted">{fmtDate(r.uploaded_at)}</span></div>{r.extracted_values.map(v=><p key={v.name} className="mt-2 text-onko-muted">{v.name}: {v.value} {v.unit}</p>)}</div>)}</div></section>
   <section id="appointments" className="onko-card p-5"><h2 className="text-[17px] font-bold">Appointments</h2><div className="mt-3 grid gap-2">{appointments.length?appointments.map(a=><div key={a.id} className="rounded-xl bg-onko-surface p-3 text-[13px]"><strong>{a.title}</strong><p className="mt-1 text-[11px] text-onko-muted">{fmtDate(a.scheduled_at)}</p></div>):<p className="text-[13px] text-onko-muted">No appointments recorded.</p>}</div></section>
   </aside>
  </div>
 </DoctorShell>
}
