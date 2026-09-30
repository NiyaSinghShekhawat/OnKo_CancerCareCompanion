"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { CalendarDays, FileText, HeartHandshake, Home, Pill, Route, UserRound } from "lucide-react";
import SOSButton from "@/components/SOSButton";

const nav=[
 {href:"/patient",label:"Today",icon:Home},
 {href:"/patient/journey",label:"Journey",icon:Route},
 {href:"/patient/medications",label:"Medications",icon:Pill},
 {href:"/patient/records",label:"Records",icon:FileText},
 {href:"/patient/help",label:"Help",icon:HeartHandshake},
];
export default function PatientShell({patient,children}:{patient:{id:string;name:string;journey_state:string;regimen_label:string;cycle_current:number},children:React.ReactNode}){
 const path=usePathname();
 return <div className="min-h-screen bg-onko-canvas text-onko-ink">
  <header className="sticky top-0 z-40 border-b border-onko-line bg-white/95 backdrop-blur">
   <div className="mx-auto flex min-h-[72px] max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
    <Link href="/patient" className="min-w-0"><div className="flex items-center gap-2"><span className="grid h-9 w-9 place-items-center rounded-xl bg-onko-teal text-sm font-bold text-white">O</span><div className="min-w-0"><div className="flex items-center gap-2"><strong className="text-[18px]">OnKo</strong><span className="hidden rounded-full bg-onko-softteal px-2 py-0.5 text-[11px] font-semibold text-onko-teal sm:inline">Care Path</span></div><p className="truncate text-[12px] text-onko-muted">{patient.journey_state.replaceAll("_"," ").toLowerCase()} · {patient.regimen_label} cycle {patient.cycle_current}</p></div></div></Link>
    <div className="flex items-center gap-2"><SOSButton patientId={patient.id}/><div className="hidden h-9 w-9 place-items-center rounded-full bg-onko-softteal text-[12px] font-bold text-onko-teal sm:grid">{patient.name.split(" ").map(x=>x[0]).join("").slice(0,2)}</div></div>
   </div>
  </header>
  <div className="mx-auto grid max-w-7xl lg:grid-cols-[210px_minmax(0,1fr)]">
   <aside className="hidden border-r border-onko-line bg-white/70 p-4 lg:block"><nav className="sticky top-24 grid gap-2">{nav.map(n=>{const I=n.icon,active=n.href==="/patient"?path===n.href:path.startsWith(n.href);return <Link key={n.href} href={n.href} className={"flex items-center gap-3 rounded-xl px-4 py-3 text-[15px] font-semibold "+(active?"bg-onko-teal text-white":"text-onko-muted hover:bg-onko-hover")}><I size={19}/>{n.label}</Link>})}<div className="mt-5 rounded-xl bg-onko-softteal p-4"><CalendarDays size={18} className="text-onko-teal"/><p className="mt-2 text-[13px] font-semibold">Your recorded care plan</p><p className="mt-1 text-[12px] leading-5 text-onko-muted">Tasks and instructions shown here come from your care record.</p></div></nav></aside>
   <main className="min-w-0 px-4 pb-28 pt-5 sm:px-6 sm:pt-7 lg:px-8 lg:pb-10">{children}</main>
  </div>
  <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-onko-line bg-white/95 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"><div className="mx-auto flex h-[72px] max-w-xl items-center justify-around px-1">{nav.map(n=>{const I=n.icon,active=n.href==="/patient"?path===n.href:path.startsWith(n.href);return <Link key={n.href} href={n.href} className={"flex min-w-[58px] flex-col items-center gap-1 rounded-lg px-2 py-2 text-[11px] font-semibold "+(active?"text-onko-teal":"text-onko-muted")}><I size={22}/><span>{n.label}</span></Link>})}</div></nav>
 </div>
}