"use client";

import {useMemo,useState} from "react";
import {ChevronLeft,ChevronRight,CalendarDays} from "lucide-react";
import type {CareEvent} from "@/lib/types";
import {fmtTime} from "@/lib/format";

type Props={
  events: CareEvent[];
  title?: string;
  compact?: boolean;
};

const weekdays=["Sun","Mon","Tue","Wed","Thu","Fri","Sat"];

function monthStart(d:Date){return new Date(d.getFullYear(),d.getMonth(),1)}
function addMonths(d:Date,n:number){return new Date(d.getFullYear(),d.getMonth()+n,1)}
function keyOf(d:Date){return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}-${String(d.getDate()).padStart(2,"0")}`}
function eventKey(e:CareEvent){const d=new Date(e.scheduled_at);return keyOf(d)}
function monthLabel(d:Date){return d.toLocaleDateString("en-IN",{month:"long",year:"numeric"})}
function flagged(e:CareEvent){return ["REPORTED_MISSED","NO_RESPONSE","CONFLICTING"].includes(e.status)}
function statusClass(e:CareEvent){
  if(e.status==="CONFLICTING") return "border-red-200 bg-red-50 text-onko-sos";
  if(e.status==="REPORTED_MISSED"||e.status==="NO_RESPONSE") return "border-amber-200 bg-onko-amberbg text-onko-amber";
  if(e.status==="COMPLETED") return "border-onko-softteal bg-onko-softteal text-onko-teal";
  if(e.status==="CURRENT") return "border-onko-teal bg-white text-onko-teal";
  return "border-onko-line bg-white text-onko-muted";
}

export default function CareJourneyCalendar({events,title="Care calendar",compact=false}:Props){
  const initial=useMemo(()=>{
    const now=new Date();
    const hasCurrent=events.some(e=>{const d=new Date(e.scheduled_at);return d.getMonth()===now.getMonth()&&d.getFullYear()===now.getFullYear()});
    if(hasCurrent||events.length===0)return monthStart(now);
    return monthStart(new Date(events[0].scheduled_at));
  },[events]);
  const [month,setMonth]=useState(initial);
  const [selected,setSelected]=useState<string|null>(null);

  const grouped=useMemo(()=>{
    const map=new Map<string,CareEvent[]>();
    for(const e of events){
      const k=eventKey(e);
      if(!map.has(k))map.set(k,[]);
      map.get(k)!.push(e);
    }
    for(const list of map.values())list.sort((a,b)=>+new Date(a.scheduled_at)-+new Date(b.scheduled_at));
    return map;
  },[events]);

  const start=monthStart(month);
  const firstCell=new Date(start);
  firstCell.setDate(1-start.getDay());
  const cells=Array.from({length:42},(_,i)=>{const d=new Date(firstCell);d.setDate(firstCell.getDate()+i);return d});
  const selectedEvents=selected?(grouped.get(selected)??[]):[];

  return <div>
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h3 className={compact?"text-[18px] font-bold":"text-[22px] font-bold"}>{title}</h3><p className="mt-1 text-[12px] text-onko-muted">Use the arrows to review past or future recorded activities.</p></div>
      <div className="flex items-center gap-2">
        <button onClick={()=>{setMonth(m=>addMonths(m,-1));setSelected(null)}} aria-label="Previous month" className="grid h-9 w-9 place-items-center rounded-lg border border-onko-line bg-white hover:bg-onko-hover"><ChevronLeft size={17}/></button>
        <div className="min-w-[150px] text-center text-[14px] font-bold">{monthLabel(month)}</div>
        <button onClick={()=>{setMonth(m=>addMonths(m,1));setSelected(null)}} aria-label="Next month" className="grid h-9 w-9 place-items-center rounded-lg border border-onko-line bg-white hover:bg-onko-hover"><ChevronRight size={17}/></button>
      </div>
    </div>

    <div className="mt-4 flex flex-wrap gap-2 text-[11px]">
      <span className="rounded-full bg-onko-softteal px-2.5 py-1 text-onko-teal">Completed</span>
      <span className="rounded-full border border-onko-line bg-white px-2.5 py-1 text-onko-muted">Upcoming</span>
      <span className="rounded-full bg-onko-amberbg px-2.5 py-1 text-onko-amber">Needs follow-up</span>
      <span className="rounded-full bg-red-50 px-2.5 py-1 text-onko-sos">Conflicting</span>
    </div>

    <div className="mt-4 overflow-x-auto">
      <div className="min-w-[720px]">
        <div className="grid grid-cols-7 border-b border-onko-line pb-2">{weekdays.map(w=><div key={w} className="px-2 text-[11px] font-bold uppercase tracking-wide text-onko-muted">{w}</div>)}</div>
        <div className="mt-2 grid grid-cols-7 gap-1.5">
          {cells.map(d=>{
            const k=keyOf(d),dayEvents=grouped.get(k)??[],inMonth=d.getMonth()===month.getMonth(),hasFlag=dayEvents.some(flagged);
            return <button key={k} onClick={()=>dayEvents.length&&setSelected(k)} className={"min-h-[92px] rounded-xl border p-2 text-left transition "+(selected===k?"border-onko-teal ring-1 ring-onko-teal":hasFlag?"border-amber-200 bg-onko-amberbg/50":"border-onko-line bg-white")+(inMonth?"":" opacity-45")}>
              <div className="flex items-center justify-between"><span className="text-[12px] font-bold">{d.getDate()}</span>{hasFlag&&<span className="h-2 w-2 rounded-full bg-onko-amber"/>}</div>
              <div className="mt-2 grid gap-1">
                {dayEvents.slice(0,compact?2:3).map(e=><div key={e.id} className={"truncate rounded-md border px-1.5 py-1 text-[10px] font-semibold "+statusClass(e)}>{fmtTime(e.scheduled_at)} · {e.title}</div>)}
                {dayEvents.length>(compact?2:3)&&<div className="text-[10px] font-semibold text-onko-muted">+{dayEvents.length-(compact?2:3)} more</div>}
              </div>
            </button>
          })}
        </div>
      </div>
    </div>

    <div className="mt-4 rounded-2xl bg-onko-surface p-4">
      {selectedEvents.length?<div><div className="flex items-center gap-2"><CalendarDays size={16} className="text-onko-teal"/><strong className="text-[14px]">{new Date(selectedEvents[0].scheduled_at).toLocaleDateString("en-IN",{day:"numeric",month:"long",year:"numeric"})}</strong></div><div className="mt-3 grid gap-2">{selectedEvents.map(e=><div key={e.id} className="rounded-xl bg-white p-3"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-[11px] font-semibold uppercase text-onko-muted">{e.type.toLowerCase()} · {fmtTime(e.scheduled_at)}</p><p className="mt-1 text-[14px] font-bold">{e.title}</p></div><span className={"rounded-full border px-2 py-1 text-[10px] font-semibold "+statusClass(e)}>{e.status.replaceAll("_"," ").toLowerCase()}</span></div>{Object.keys(e.details||{}).length>0&&<p className="mt-2 text-[12px] leading-5 text-onko-muted">{Object.values(e.details).join(" · ")}</p>}</div>)}</div></div>:<p className="text-[12px] text-onko-muted">Select a day with recorded activity to view details.</p>}
    </div>
  </div>
}
