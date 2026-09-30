import type { CareEvent } from "@/lib/types";
import { fmtDate,fmtTime,statusText } from "@/lib/format";
export default function Timeline({events}:{events:CareEvent[]}){
 return <ol className="ml-2 grid gap-4 border-l-2 border-onko-line pl-6">{events.map(e=><li key={e.id} className="relative rounded-xl bg-onko-surface p-4"><span className="absolute -left-[31px] top-5 h-3 w-3 rounded-full border-2 border-white bg-onko-teal ring-2 ring-onko-softteal"/><div className="text-[11px] font-semibold uppercase tracking-wide text-onko-muted">{fmtDate(e.scheduled_at)} · {fmtTime(e.scheduled_at)} · {e.type.toLowerCase()}</div><div className="mt-1 text-[14px] font-bold">{e.title}</div><div className="mt-1 text-[12px] text-onko-teal">{statusText[e.status]}</div>{e.details?.instructions&&<div className="mt-2 text-[12px] leading-5 text-onko-muted">{e.details.instructions}</div>}</li>)}</ol>
}
