import { Filter, ShieldCheck } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import StatCards from "@/components/StatCards";
import AttentionQueue from "@/components/AttentionQueue";
import { serverApi } from "@/lib/server-api";
export const dynamic="force-dynamic";
export default async function DoctorHome(){
 const [overview,attention]=await Promise.all([serverApi.overview(),serverApi.attention()]);
 return <DoctorShell>
   <div className="rounded-xl border border-onko-softteal bg-onko-softteal/55 px-5 py-4 text-[14px] leading-6 text-onko-teal"><ShieldCheck size={17} className="mr-2 inline"/> <strong>Clinical Boundary Notice:</strong> OnKo organizes and surfaces observable workflow events. Clinicians interpret clinical significance and direct all care actions.</div>
   <div className="mt-6 flex flex-wrap items-end justify-between gap-5"><div><p className="text-[13px] font-bold uppercase tracking-[.12em] text-onko-teal">Attending command console · Care journey orchestration</p><h1 className="mt-2 text-[48px] font-bold leading-[1.05] tracking-[-.035em]">Good morning, Dr. Mehta</h1><p className="mt-2 text-[17px] leading-7 text-onko-muted">Here is what needs your attention today across {overview.active_patients} active patient care journeys.</p></div><button className="onko-button-secondary"><Filter size={16}/>View filters</button></div>
   <div className="my-6 border-b border-onko-line"/>
   <StatCards data={overview}/>
   <section className="mt-8"><div className="mb-4 flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-[30px] font-bold tracking-tight">Explainable Attention Queue</h2><p className="mt-1 text-[15px] text-onko-muted">Observable clinical milestones and patient-reported workflow interruptions requiring doctor action.</p></div><span className="onko-chip bg-white text-onko-teal shadow-sm">All ({attention.length})</span></div><AttentionQueue items={attention}/></section>
 </DoctorShell>
}
