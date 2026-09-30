"use client";
import { useState } from "react";
import { CalendarClock, CheckCircle2, CircleAlert, ClipboardCheck, Pill, Stethoscope } from "lucide-react";
import { api } from "@/lib/api";
import type { CareEvent, EventStatus } from "@/lib/types";
import { fmtDate,fmtTime,statusText } from "@/lib/format";
const icons={MEDICATION:Pill,INVESTIGATION:ClipboardCheck,TREATMENT:Stethoscope,APPOINTMENT:CalendarClock,MILESTONE:CheckCircle2};
export default function PatientEventCard({event,interactive=false}:{event:CareEvent;interactive?:boolean}){
 const [status,setStatus]=useState<EventStatus>(event.status),[busy,setBusy]=useState(false); const I=icons[event.type];
 async function update(next:EventStatus){setBusy(true);try{await api.setEventStatus(event.id,next);setStatus(next)}finally{setBusy(false)}}
 return <article className="rounded-2xl bg-onko-surface p-4 sm:p-5">
  <div className="flex items-start gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><I size={20}/></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-[12px] font-semibold text-onko-teal">{fmtTime(event.scheduled_at)} · {event.type.toLowerCase()}</p><h3 className="mt-0.5 text-[17px] font-bold">{event.title}</h3></div><span className={"rounded-full px-2.5 py-1 text-[12px] font-semibold "+(status==="REPORTED_MISSED"?"bg-red-50 text-onko-sos":"bg-white text-onko-muted")}>{statusText[status]}</span></div>
  {Object.entries(event.details||{}).length>0&&<div className="mt-3 rounded-xl bg-white p-3 text-[14px] leading-6 text-onko-muted">{Object.entries(event.details).map(([k,v])=><p key={k}><span className="font-semibold capitalize text-onko-ink">{k.replaceAll("_"," ")}:</span> {v}</p>)}</div>}
  {interactive&&event.type==="MEDICATION"&&(status==="UPCOMING"||status==="CURRENT")&&<div className="mt-3 grid gap-2 sm:grid-cols-2"><button disabled={busy} onClick={()=>update("COMPLETED")} className="onko-button-primary"><CheckCircle2 size={17}/>Mark as taken</button><button disabled={busy} onClick={()=>update("REPORTED_MISSED")} className="onko-button-secondary text-onko-sos"><CircleAlert size={17}/>Report missed</button></div>}
  <p className="mt-3 text-[12px] text-onko-muted">{fmtDate(event.scheduled_at)} · Source: {event.source}</p></div></div>
 </article>
}