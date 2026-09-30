import { CalendarDays, ClipboardCheck, FileText, MessageSquareText, Siren, Users } from "lucide-react";
import type { DashboardOverview } from "@/lib/types";
const cards = [
  ["active_patients","Active patients","Under active care",Users,"teal"],
  ["consultations_today","Consultations","Today",CalendarDays,"teal"],
  ["missed_activities","Missed activities","Recorded workflow events",ClipboardCheck,"amber"],
  ["open_queries","Care queries","Pending",MessageSquareText,"teal"],
  ["reports_pending_review","Reports","Awaiting review",FileText,"teal"],
  ["sos_open","Direct check-ins","Patient initiated",Siren,"red"],
] as const;
export default function StatCards({data}:{data:DashboardOverview}){
 return <div className="grid grid-cols-2 gap-3 lg:grid-cols-3 2xl:grid-cols-6">{cards.map(([key,label,helper,Icon,tone])=><div key={key} className="onko-card min-h-[150px] p-4">
   <div className="flex items-start justify-between"><p className="text-[11px] font-bold uppercase tracking-[.08em] text-onko-muted">{label}</p><Icon size={17} className={tone==="red"?"text-onko-sos":tone==="amber"?"text-onko-amber":"text-onko-teal"}/></div>
   <div className={"mt-4 text-[36px] font-bold leading-none tracking-tight "+(tone==="red"?"text-onko-sos":tone==="amber"?"text-onko-amber":"text-onko-ink")}>{data[key]}</div>
   <p className="mt-3 text-[12px] leading-5 text-onko-muted">{helper}</p>
 </div>)}</div>
}
