"use client";
import {useState} from "react";
import {CalendarClock,CheckCircle2,CircleAlert,ClipboardCheck,Pill,Stethoscope,Target} from "lucide-react";
import {api} from "@/lib/api";
import type {CareEvent,EventStatus} from "@/lib/types";
import {fmtDate,fmtTime,statusText} from "@/lib/format";
const icons={MEDICATION:Pill,INVESTIGATION:ClipboardCheck,TREATMENT:Stethoscope,APPOINTMENT:CalendarClock,MILESTONE:Target};
const actionCopy={
 MEDICATION:{done:"Mark as taken",missed:"Report missed"},
 INVESTIGATION:{done:"Mark completed",missed:"Report not completed"},
 TREATMENT:{done:"Mark attended",missed:"Report missed"},
 APPOINTMENT:{done:"Mark attended",missed:"Report missed"},
 MILESTONE:{done:"Mark completed",missed:"Report not completed"},
};
export default function PatientEventCard({event,interactive=false}:{event:CareEvent;interactive?:boolean}){
 const [status,setStatus]=useState<EventStatus>(event.status),[busy,setBusy]=useState(false);const I=icons[event.type],copy=actionCopy[event.type];
 async function update(next:EventStatus){setBusy(true);try{await api.setEventStatus(event.id,next);setStatus(next)}finally{setBusy(false)}}
 const canRespond=interactive&&(status==="UPCOMING"||status==="CURRENT"||status==="NO_RESPONSE");
 return <article className="rounded-2xl bg-onko-surface p-4 sm:p-5"><div className="flex items-start gap-3"><div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><I size={20}/></div><div className="min-w-0 flex-1"><div className="flex flex-wrap items-center justify-between gap-2"><div><p className="text-[12px] font-semibold text-onko-teal">{fmtTime(event.scheduled_at)} · {event.type.toLowerCase()}</p><h3 className="mt-0.5 text-[17px] font-bold">{event.title}</h3></div><span className={"rounded-full px-2.5 py-1 text-[12px] font-semibold "+(status==="REPORTED_MISSED"||status==="NO_RESPONSE"?"bg-onko-amberbg text-onko-amber":status==="CONFLICTING"?"bg-red-50 text-onko-sos":"bg-white text-onko-muted")}>{statusText[status]}</span></div>
 {Object.entries(event.details||{}).length>0&&<div className="mt-3 rounded-xl bg-white p-3 text-[14px] leading-6 text-onko-muted">{Object.entries(event.details).map(([k,v])=><p key={k}><span className="font-semibold capitalize text-onko-ink">{k.replaceAll("_"," ")}:</span> {v}</p>)}</div>}
 {canRespond&&<div className="mt-3 grid gap-2 sm:grid-cols-2"><button disabled={busy} onClick={()=>update("COMPLETED")} className="onko-button-primary"><CheckCircle2 size={17}/>{copy.done}</button><button disabled={busy} onClick={()=>update("REPORTED_MISSED")} className="onko-button-secondary text-onko-amber"><CircleAlert size={17}/>{copy.missed}</button></div>}
 {event.response_state&&<p className="mt-3 rounded-lg bg-white px-3 py-2 text-[12px] text-onko-muted"><strong>Recorded response:</strong> {event.response_state.replaceAll("_"," ").toLowerCase()}</p>}
 <p className="mt-3 text-[12px] text-onko-muted">{fmtDate(event.scheduled_at)} · Source: {event.source}</p></div></div></article>
}