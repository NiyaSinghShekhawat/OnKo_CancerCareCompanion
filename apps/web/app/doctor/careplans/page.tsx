import Link from "next/link";
import { ArrowRight, ClipboardList } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { serverApi } from "@/lib/server-api";
export const dynamic="force-dynamic";
export default async function CarePlansPage(){const patients=await serverApi.patients();return <DoctorShell>
<p className="onko-eyebrow text-onko-teal">Doctor-controlled care</p><h1 className="mt-2 text-[44px] font-bold tracking-tight">Care Plans</h1><p className="mt-2 max-w-3xl text-[16px] leading-7 text-onko-muted">Open a patient workspace to structure care that has already been decided. Copilot drafts remain editable and do not enter the journey until clinician approval.</p>
<div className="mt-7 grid gap-4 lg:grid-cols-2">{patients.map(p=><article key={p.id} className="onko-card p-6"><div className="flex items-start gap-4"><span className="grid h-12 w-12 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><ClipboardList size={22}/></span><div><h2 className="text-[20px] font-bold">{p.name}</h2><p className="mt-1 text-[14px] text-onko-muted">{p.regimen_label||"No regimen label recorded"} · Cycle {p.cycle_current}/{p.cycle_total}</p></div></div><div className="mt-5 flex flex-wrap gap-3"><Link href={"/doctor/patients/"+p.id} className="onko-button-secondary">Patient 360</Link><Link href={"/doctor/careplan/"+p.id} className="onko-button-primary">Open Care Plan Copilot <ArrowRight size={16}/></Link></div></article>)}</div>
</DoctorShell>}
