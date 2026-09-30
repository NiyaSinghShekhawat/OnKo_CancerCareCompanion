import Link from "next/link";
import { CalendarDays } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";
import { fmtDate, fmtTime, statusText } from "@/lib/format";
export const dynamic="force-dynamic";
export default async function AppointmentsPage(){const patients=await api.patients();const data=(await Promise.all(patients.map(async p=>({p,d:await api.patient360(p.id)})))).flatMap(({p,d})=>d.timeline.filter(e=>e.type==="APPOINTMENT").map(e=>({p,e}))).sort((a,b)=>a.e.scheduled_at.localeCompare(b.e.scheduled_at));return <DoctorShell>
<p className="onko-eyebrow text-onko-teal">Schedule</p><h1 className="mt-2 text-[44px] font-bold tracking-tight">Appointments</h1><p className="mt-2 text-[16px] leading-7 text-onko-muted">Recorded appointments across active patient journeys.</p>
<div className="mt-7 grid gap-4">{data.length?data.map(({p,e})=><article key={e.id} className="onko-card grid gap-5 p-6 md:grid-cols-[90px_1fr_auto] md:items-center"><div className="grid h-[78px] place-items-center rounded-xl bg-onko-softteal text-onko-teal"><CalendarDays size={27}/></div><div><p className="text-[13px] font-bold uppercase tracking-wide text-onko-muted">{fmtDate(e.scheduled_at)} · {fmtTime(e.scheduled_at)}</p><h2 className="mt-1 text-[20px] font-bold">{e.title}</h2><Link href={"/doctor/patients/"+p.id} className="mt-1 inline-block text-[14px] font-semibold text-onko-teal">{p.name}</Link></div><span className="onko-chip bg-onko-surface text-onko-muted">{statusText[e.status]}</span></article>):<div className="onko-card p-6 text-[15px] text-onko-muted">No appointments recorded.</div>}</div>
</DoctorShell>}
