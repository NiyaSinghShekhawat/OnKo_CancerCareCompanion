"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useRef,useState} from "react";
import {CalendarDays,ChevronDown,ClipboardList,FileText,Home,Languages,MessageSquareText,Pill,Route,UserRound,UsersRound} from "lucide-react";
import SOSButton from "@/components/SOSButton";

const nav=[
 {href:"/patient",label:"Today",icon:Home},
 {href:"/patient/journey",label:"Journey",icon:Route},
 {href:"/patient/medications",label:"Medication",icon:Pill},
 {href:"/patient/queries",label:"Query",icon:MessageSquareText},
];

const more=[
 {href:"/patient/care",label:"Appointments & care activities",icon:CalendarDays},
 {href:"/patient/records",label:"Reports & records",icon:FileText},
 {href:"/patient/summary",label:"Portable care summary",icon:ClipboardList},
 {href:"/patient/profile",label:"Caregiver, consent & preferences",icon:UsersRound},
];

export default function PatientShell({patient,children}:{patient:{id:string;name:string;journey_state:string;regimen_label:string;cycle_current:number},children:React.ReactNode}){
 const path=usePathname(),[open,setOpen]=useState(false),ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{const close=(e:MouseEvent)=>{if(ref.current&&!ref.current.contains(e.target as Node))setOpen(false)};document.addEventListener("mousedown",close);return()=>document.removeEventListener("mousedown",close)},[]);
 const initials=patient.name.split(" ").map(x=>x[0]).join("").slice(0,2);
 return <div className="min-h-screen bg-[#ECFAF7] text-onko-ink">
  <header className="sticky top-0 z-40 border-b border-[#D7EEEA] bg-[#ECFAF7]/95 backdrop-blur">
   <div className="mx-auto flex min-h-[76px] max-w-[1180px] items-center justify-between gap-3 px-4 sm:px-7">
    <Link href="/patient" className="flex min-w-0 items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full bg-white text-[13px] font-bold text-onko-teal shadow-sm">OnKo</span><div className="hidden min-w-0 sm:block"><strong className="text-[15px]">{patient.name}</strong><p className="truncate text-[12px] text-onko-muted">{patient.regimen_label} · cycle {patient.cycle_current}</p></div></Link>
    <div className="flex items-center gap-2"><SOSButton patientId={patient.id}/>
     <div className="relative" ref={ref}><button onClick={()=>setOpen(v=>!v)} aria-label="Open patient menu" aria-expanded={open} className="flex h-11 items-center gap-2 rounded-full border border-[#CFE5E1] bg-white pl-2 pr-3 shadow-sm"><span className="grid h-8 w-8 place-items-center rounded-full bg-onko-teal text-[12px] font-bold text-white">{initials}</span><ChevronDown size={15} className={"text-onko-muted transition "+(open?"rotate-180":"")}/></button>
      {open&&<div className="absolute right-0 mt-2 w-[310px] overflow-hidden rounded-2xl border border-onko-line bg-white shadow-xl">
       <div className="border-b border-onko-line bg-onko-surface p-4"><p className="text-[15px] font-bold">{patient.name}</p><p className="mt-1 text-[12px] capitalize text-onko-muted">{patient.journey_state.replaceAll("_"," ").toLowerCase()}</p></div>
       <div className="p-2">{more.map(m=>{const I=m.icon;return <Link key={m.href} href={m.href} onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[14px] font-semibold hover:bg-onko-hover"><span className="grid h-9 w-9 place-items-center rounded-lg bg-onko-softteal text-onko-teal"><I size={17}/></span>{m.label}</Link>})}</div>
       <div className="border-t border-onko-line p-2"><Link href="/patient/profile#language" onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[13px] text-onko-muted hover:bg-onko-hover"><Languages size={17}/>Language & communication preferences</Link></div>
      </div>}
     </div>
    </div>
   </div>
  </header>
  <main className="mx-auto w-full max-w-[860px] px-4 pb-28 pt-5 sm:px-7 sm:pt-7 lg:pb-28">{children}</main>
  <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-[#D7EEEA] bg-[#F4FCFA]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur"><div className="mx-auto flex h-[78px] max-w-[680px] items-center justify-around px-1">{nav.map(n=>{const I=n.icon,active=n.href==="/patient"?path===n.href:path.startsWith(n.href);return <Link key={n.href} href={n.href} className={"flex min-w-[70px] flex-col items-center gap-1 rounded-xl px-2 py-2 text-[11px] font-semibold "+(active?"text-onko-teal":"text-onko-muted")}><I size={23}/><span>{n.label}</span></Link>})}</div></nav>
 </div>
}