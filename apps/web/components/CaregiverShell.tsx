"use client";
import Link from "next/link";
import {usePathname} from "next/navigation";
import {useEffect,useRef,useState} from "react";
import {Bell,ChevronDown,FileText,Home,Pill,Route,ShieldCheck,UsersRound} from "lucide-react";

const primary=[
 {href:"/caregiver",label:"Overview",icon:Home},
 {href:"/caregiver/journey",label:"Journey",icon:Route},
 {href:"/caregiver/medications",label:"Medication",icon:Pill},
 {href:"/caregiver/records",label:"Reports",icon:FileText},
];

export default function CaregiverShell({patient,caregiver,children}:{patient:{name:string;regimen_label:string;cycle_current:number},caregiver:{name:string;relation:string;consent_status:string;permissions:{view_journey:boolean;upload_reports:boolean;receive_escalations:boolean}},children:React.ReactNode}){
 const path=usePathname(),[open,setOpen]=useState(false),ref=useRef<HTMLDivElement>(null);
 useEffect(()=>{const close=(e:MouseEvent)=>{if(ref.current&&!ref.current.contains(e.target as Node))setOpen(false)};document.addEventListener("mousedown",close);return()=>document.removeEventListener("mousedown",close)},[]);
 const initials=caregiver.name.split(" ").map(x=>x[0]).join("").slice(0,2);
 const active=(href:string)=>href==="/caregiver"?path===href:path.startsWith(href);
 const consented=caregiver.consent_status==="GRANTED";
 return <div className="min-h-screen bg-[#ECFAF7] text-onko-ink">
  <header className="fixed inset-x-0 top-0 z-50 border-b border-[#D7EEEA] bg-[#ECFAF7]/95 backdrop-blur">
   <div className="mx-auto flex h-[70px] max-w-[1440px] items-center gap-4 px-4 sm:px-6 lg:h-[82px] lg:px-10">
    <Link href="/caregiver" className="flex shrink-0 items-center gap-3"><span className="grid h-10 w-10 place-items-center rounded-full bg-white text-[13px] font-bold text-onko-teal shadow-sm lg:h-11 lg:w-11">OnKo</span><div className="hidden xl:block"><strong className="text-[14px]">Supporting {patient.name}</strong><p className="max-w-[190px] truncate text-[11px] text-onko-muted">{patient.regimen_label} · cycle {patient.cycle_current}</p></div></Link>
    <nav className="hidden min-w-0 flex-1 items-center justify-center gap-1 md:flex lg:gap-2">{primary.map(n=>{const I=n.icon;return <Link key={n.href} href={n.href} className={"flex items-center gap-2 rounded-xl px-3 py-2.5 text-[13px] font-semibold transition lg:px-4 lg:text-[14px] "+(active(n.href)?"bg-white text-onko-teal shadow-sm":"text-onko-muted hover:bg-white/70 hover:text-onko-ink")}><I size={17}/><span>{n.label}</span></Link>})}</nav>
    <div className="ml-auto flex shrink-0 items-center gap-2"><span className={"hidden rounded-full px-3 py-2 text-[12px] font-semibold sm:inline-flex "+(consented?"bg-white text-onko-teal":"bg-onko-amberbg text-onko-amber")}><ShieldCheck size={15} className="mr-1.5"/>{consented?"Consent active":"Access limited"}</span><div className="relative" ref={ref}><button onClick={()=>setOpen(v=>!v)} aria-label="Open caregiver menu" aria-expanded={open} className="flex h-11 items-center gap-2 rounded-full border border-[#CFE5E1] bg-white pl-2 pr-3 shadow-sm"><span className="grid h-8 w-8 place-items-center rounded-full bg-onko-teal text-[12px] font-bold text-white">{initials}</span><ChevronDown size={15} className={"text-onko-muted transition "+(open?"rotate-180":"")}/></button>
     {open&&<div className="absolute right-0 mt-2 w-[min(320px,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-onko-line bg-white shadow-xl"><div className="border-b border-onko-line bg-onko-surface p-4"><p className="text-[15px] font-bold">{caregiver.name}</p><p className="mt-1 text-[12px] text-onko-muted">{caregiver.relation} · caregiver</p></div><div className="p-2"><Link href="/caregiver/notifications" onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[14px] font-semibold hover:bg-onko-hover"><span className="grid h-9 w-9 place-items-center rounded-lg bg-onko-softteal text-onko-teal"><Bell size={17}/></span>Notifications</Link><Link href="/caregiver/access" onClick={()=>setOpen(false)} className="flex items-center gap-3 rounded-xl px-3 py-3 text-[14px] font-semibold hover:bg-onko-hover"><span className="grid h-9 w-9 place-items-center rounded-lg bg-onko-softteal text-onko-teal"><UsersRound size={17}/></span>Access & patient consent</Link></div><div className="border-t border-onko-line p-3 text-[12px] leading-5 text-onko-muted">You only see information Rajesh has consented to share. Patient access can be changed or revoked.</div></div>}
    </div></div>
   </div>
  </header>
  <main className="mx-auto w-full max-w-[1440px] px-4 pb-28 pt-[94px] sm:px-6 md:pb-12 md:pt-[98px] lg:px-10 lg:pt-[114px]">{children}</main>
  <nav className="fixed inset-x-0 bottom-0 z-50 border-t border-[#D7EEEA] bg-[#F4FCFA]/95 pb-[env(safe-area-inset-bottom)] backdrop-blur md:hidden"><div className="mx-auto grid h-[76px] max-w-xl grid-cols-4 items-center px-1">{primary.map(n=>{const I=n.icon;return <Link key={n.href} href={n.href} className={"flex min-w-0 flex-col items-center gap-1 rounded-xl px-1 py-2 text-[10px] font-semibold "+(active(n.href)?"text-onko-teal":"text-onko-muted")}><I size={21}/><span className="truncate">{n.label}</span></Link>})}</div></nav>
 </div>
}