import Link from "next/link";
import { ArrowRight, CircleAlert, Clock3, MessageSquareText, Siren } from "lucide-react";
import type { AttentionItem } from "@/lib/types";
import { labelText } from "@/lib/format";
const tone:Record<string,string>={SOS:"border-red-200 bg-red-50 text-onko-sos",NEEDS_REVIEW:"border-amber-200 bg-onko-amberbg text-onko-amber",QUERY:"border-violet-200 bg-violet-50 text-violet-700",FOLLOW_UP:"border-onko-softteal bg-onko-softteal text-onko-teal"};
const icons={SOS:Siren,NEEDS_REVIEW:CircleAlert,QUERY:MessageSquareText,FOLLOW_UP:Clock3};
export default function AttentionQueue({items}:{items:AttentionItem[]}){
 if(!items.length)return <div className="onko-card p-5 text-[14px] text-onko-muted">Nothing needs attention right now.</div>;
 return <div className="grid gap-4">{items.map(a=>{const Icon=icons[a.label];return <article key={a.id} className={"rounded-xl border bg-white p-5 shadow-card "+(a.label==="SOS"?"border-l-4 border-l-onko-sos":a.label==="NEEDS_REVIEW"?"border-l-4 border-l-amber-500":"border-onko-line border-l-4 border-l-onko-teal")}>
   <div className="flex flex-wrap items-center gap-2"><span className={"inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide "+tone[a.label]}><Icon size={12}/>{labelText[a.label]}</span><h3 className="text-[16px] font-bold">{a.patient_name}</h3></div>
   <div className={"mt-4 rounded-xl p-4 "+(a.label==="SOS"?"bg-red-50":"bg-onko-softteal/60")}><p className="mb-2 text-[10px] font-bold uppercase tracking-[.1em] text-onko-muted">Surfaced workflow facts</p><ul className="grid gap-2 text-[13px] leading-5">{a.reasons.map(r=><li key={r} className="flex gap-2"><span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-onko-teal"/><span>{r}</span></li>)}</ul></div>
   <div className="mt-4 flex justify-end"><Link href={"/doctor/patients/"+a.patient_id} className="onko-button-primary">Open Patient 360 <ArrowRight size={15}/></Link></div>
 </article>})}</div>
}
