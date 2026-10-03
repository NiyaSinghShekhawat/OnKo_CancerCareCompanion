"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useRef,useState} from "react";
import {CalendarDays,ChevronDown,ClipboardList,FileText,Home,Languages,MessageCircle,MessageSquareText,Pill,Route,UsersRound} from "lucide-react";
import SOSButton from "@/components/SOSButton";
import { setActor } from "@/lib/api";

const primary=[
 {href:"/patient",label:"Overview",icon:Home},
 {href:"/patient/journey",label:"Journey",icon:Route},
 {href:"/patient/medications",label:"Medication",icon:Pill},
 {href:"/patient/queries",label:"Query",icon:MessageSquareText},
 {href:"/patient/records",label:"Add Report",icon:FileText},
];
const more=[
 {href:"/patient/care",label:"Appointments & care activities",icon:CalendarDays},
 {href:"/patient/whatsapp",label:"WhatsApp check-in demo",icon:MessageCircle},
 {href:"/patient/summary",label:"Portable care summary",icon:ClipboardList},
 {href:"/patient/profile",label:"Caregiver, consent & preferences",icon:UsersRound},
];

const navCopy={English:["Overview","Journey","Medication","Query","Add Report"],Hindi:["अवलोकन","यात्रा","दवा","प्रश्न","रिपोर्ट जोड़ें"],Telugu:["అవలోకనం","ప్రయాణం","మందులు","ప్రశ్న","రిపోర్ట్ జోడించండి"]} as const;
export default function PatientShell({patient,children}:{patient:{id:string;name:string;journey_state:string;regimen_label:string;cycle_current:number},children:React.ReactNode}){
 const path=usePathname(),[open,setOpen]=useState(false),[language,setLanguage]=useState<keyof typeof navCopy>("English"),ref=useRef<HTMLDivElement>(null);
 useEffect(()=>setActor("patient",patient.id),[patient.id]);
 useEffect(()=>{const saved=window.localStorage.getItem("onko-language");if(saved==="Hindi"||saved==="Telugu"||saved==="English")setLanguage(saved);const sync=()=>{const v=window.localStorage.getItem("onko-language");if(v==="Hindi"||v==="Telugu"||v==="English")setLanguage(v)};window.addEventListener("onko-language-change",sync);return()=>window.removeEventListener("onko-language-change",sync)},[]);
 useEffect(()=>{const close=(e:MouseEvent)=>{if(ref.current&&!ref.current.contains(e.target as Node))setOpen(false)};document.addEventListener("mousedown",close);return()=>document.removeEventListener("mousedown",close)},[]);
 const initials=patient.name.split(" ").map(x=>x[0]).join("").slice(0,2);
 const patientHref=(href:string)=>{const [base,hash]=href.split("#");return `${base}?id=${encodeURIComponent(patient.id)}${hash?`#${hash}`:""}`};
 const active=(href:string)=>href==="/patient"?path===href:path.startsWith(href);
 return <div className="min-h-screen bg-[#ECFAF7] text-onko-ink">
  <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:text-onko-teal">Skip to content</a><header className="fixed inset-x-0 top-0 z-50 border-b border-[#D7EEEA] bg-[#ECFAF7]/95 backdrop-blur">
   <div className="mx-auto flex h-[70px] max-w-[1440px] items-center gap-4 px-4 sm:px-6 lg:h-[82px] lg:px-10">
    <Link href={patientHref("/patient")} className="flex shrink-0 items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full bg-white text-[13px] font-bold text-onko-teal shadow-sm lg:h-11 lg:w-11">OnKo</span><div className="hidden xl:block"><strong className="text-[14px]">{patient.name}</strong><p className="max-w-[180px] truncate text-[11px] text-onko-muted">{patient.regimen_label} · cycle {patient.cycle_current}</p></div></Link>
    <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 md:flex lg:gap-2">{primary.map((n,i)=>{const I=n.icon;return <Link key={n.href} href={patientHref(n.href)} className={"flex items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition lg:px-4 lg:text-[14px] "+(active(n.href)?"bg-white text-onko-teal shadow-sm":"text-onko-muted hover:bg-white/70 hover:text-onko-ink")}><I size={17}/><span>{navCopy[language][i]}</span></Link>})}</nav>
    <div className="ml-auto flex shrink-0 items-center gap-2"><SOSButton patientId={patient.id}/><div className="relative" ref={ref}><button onClick={()=>setOpen(v=>!v)} aria-label="Open patient menu" aria-expanded={open} className="flex h-11 items-center gap-2 rounded-full border border-[#CFE5E1] bg-white pl-2 pr-3 shadow-sm"><span className="grid h-8 w-8 place-items-center rounded-full bg-onko-teal text-[12px] font-bold text-white">{initials}</span><ChevronDown size={15} className={"text-onko-muted transition "+(open?"rotate-180":"")}/></button>
     {open&&<div className="absolute right-0 mt-2 w-[min(310px,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-onko-line bg-white shadow-xl"><div className="border-b border-onko-line bg-onko-surface p-4"><p className="text-[15px] font-bold">{patient.name}</p><p className="mt-1 text-[12px] capitalize text-onko-muted">{patient.journey_state.replaceAll("_"," ").toLowerCase()}</p></div><div className="p-2">{more.map(m=>{const I=m.icon;return <Link key={m.href} href={patientHref(m.href)} onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[14px] font-semibold hover:bg-onko-hover"><span className="grid h-9 w-9 place-items-center rounded-lg bg-onko-softteal text-onko-teal"><I size={17}/></span>{m.label}</Link>})}</div><div className="border-t border-onko-line p-2"><Link href={patientHref("/patient/profile#language")} onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[13px] text-onko-muted hover:bg-onko-hover"><Languages size={17}/>Language & communication preferences</Link></div></div>}
    </div></div>
   </div>
  </header>
  <main id="main-content" className="mx-auto w-full max-w-[1440px] px-4 pb-28 pt-[94px] sm:px-6 md:pb-12 md:pt-[98px] lg:px-10 lg:pt-[114px]">{children}</main>
  <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-[#D7EEEA] bg-[#F4FCFA]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"><div className="mx-auto grid h-[76px] max-w-xl grid-cols-5 items-center px-1">{primary.map((n,i)=>{const I=n.icon;return <Link key={n.href} href={patientHref(n.href)} className={"flex min-w-0 flex-col items-center gap-1 rounded-xl px-1 py-2 text-[10px] font-semibold "+(active(n.href)?"text-onko-teal":"text-onko-muted")}><I size={21}/><span className="truncate">{navCopy[language][i]}</span></Link>})}</div></nav>
 </div>
}