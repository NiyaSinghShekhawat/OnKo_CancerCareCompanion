import Link from "next/link";
import { ArrowRight, CircleAlert, Clock3, MessageSquareText, Siren } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";
import { labelText } from "@/lib/format";
export const dynamic="force-dynamic";
const icon={SOS:Siren,NEEDS_REVIEW:CircleAlert,QUERY:MessageSquareText,FOLLOW_UP:Clock3};
const tone={SOS:"bg-red-50 text-onko-sos",NEEDS_REVIEW:"bg-onko-amberbg text-onko-amber",QUERY:"bg-violet-50 text-violet-700",FOLLOW_UP:"bg-onko-softteal text-onko-teal"};
export default async function AttentionPage(){const items=await api.attention();return <DoctorShell>
<div className="flex flex-wrap items-end justify-between gap-4"><div><p className="onko-eyebrow text-onko-teal">Doctor workflow</p><h1 className="mt-2 text-[44px] font-bold tracking-tight">Attention Queue</h1><p className="mt-2 max-w-3xl text-[16px] leading-7 text-onko-muted">Recorded workflow events surfaced for review. Labels describe why an item is here; they are not clinical risk scores.</p></div><span className="onko-chip bg-white text-onko-teal shadow-sm">{items.filter(i=>i.status==="PENDING").length} pending</span></div>
<div className="mt-7 flex flex-wrap gap-2">{["All",...Object.keys(labelText)].map(x=><span key={x} className={"onko-chip "+(x==="All"?"bg-onko-teal text-white":"bg-white text-onko-muted")}>{x==="All"?"All":labelText[x as keyof typeof labelText]}</span>)}</div>
<div className="mt-5 grid gap-4">{items.map(a=>{const Icon=icon[a.label];return <article key={a.id} className="onko-card p-6"><div className="flex flex-wrap items-start justify-between gap-4"><div><span className={"onko-chip "+tone[a.label]}><Icon size={15}/>{labelText[a.label]}</span><h2 className="mt-3 text-[22px] font-bold">{a.patient_name}</h2><p className="mt-1 text-[13px] font-semibold uppercase tracking-wide text-onko-muted">{a.status.toLowerCase()} · {a.assigned_to?"Assigned":"Unassigned"}</p></div><Link href={"/doctor/patients/"+a.patient_id} className="onko-button-secondary">Patient 360 <ArrowRight size={16}/></Link></div><div className="mt-5 rounded-xl bg-onko-surface p-5"><p className="text-[12px] font-bold uppercase tracking-[.1em] text-onko-muted">Why this was surfaced</p><ul className="mt-3 grid gap-2 text-[15px] leading-6">{a.reasons.map(r=><li key={r} className="flex gap-3"><span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-onko-teal"/>{r}</li>)}</ul></div></article>})}</div>
</DoctorShell>}
