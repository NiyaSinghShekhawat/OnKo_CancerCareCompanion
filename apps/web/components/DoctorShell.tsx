import Link from "next/link";
import { Bell, CalendarDays, ClipboardList, FileText, LayoutDashboard, MessageSquareText, Search, ShieldCheck, Users, UsersRound } from "lucide-react";
import SafetyNote from "./SafetyNote";

const nav=[
  {href:"/doctor",label:"Overview",icon:LayoutDashboard},
  {href:"/doctor/patients",label:"Patients",icon:Users},
  {href:"/doctor/attention",label:"Attention Queue",icon:ShieldCheck},
  {href:"/doctor/queries",label:"Queries",icon:MessageSquareText},
  {href:"/doctor/reports",label:"Reports",icon:FileText},
  {href:"/doctor/appointments",label:"Appointments",icon:CalendarDays},
  {href:"/doctor/careplans",label:"Care Plans",icon:ClipboardList},
  {href:"/doctor/team",label:"My Team",icon:UsersRound},
];

export default function DoctorShell({children}:{children:React.ReactNode}){return <div className="min-h-screen bg-onko-canvas text-onko-ink">
<aside className="fixed inset-y-0 left-0 z-30 hidden w-[280px] border-r border-onko-line bg-white xl:flex xl:flex-col">
<Link href="/" className="flex h-[82px] items-center gap-3 border-b border-onko-line px-5"><span className="grid h-11 w-11 place-items-center rounded-xl bg-onko-teal text-base font-bold text-white">O</span><div><div className="text-[21px] font-bold leading-tight text-onko-teal">OnKo</div><div className="text-[12px] font-semibold uppercase tracking-[.12em] text-onko-muted">Oncology Care</div></div></Link>
<div className="border-b border-onko-line px-4 py-5"><p className="text-[12px] font-bold uppercase tracking-[.12em] text-onko-muted">Active perspective</p><div className="mt-2 grid grid-cols-3 rounded-xl bg-onko-softteal p-1 text-center text-[13px] font-semibold"><span className="rounded-lg bg-white px-2 py-2.5 text-onko-teal shadow-sm">Doctor</span><Link href="/patient" className="px-2 py-2.5 text-onko-muted">Patient</Link><Link href="/caregiver" className="px-2 py-2.5 text-onko-muted">Caregiver</Link></div></div>
<nav className="flex-1 space-y-1 overflow-y-auto px-3 py-5">{nav.map(({href,label,icon:Icon})=><Link key={href} href={href} className="flex items-center gap-3 rounded-lg px-3 py-3 text-[15px] font-semibold transition hover:bg-onko-softteal hover:text-onko-teal"><Icon size={19}/>{label}</Link>)}</nav>
<div className="m-4 flex items-center gap-2 rounded-xl bg-onko-softteal px-3 py-3 text-[13px] font-semibold text-onko-teal"><span className="h-2 w-2 rounded-full bg-onko-teal"/>Clinician-led workspace</div></aside>
<div className="xl:pl-[280px]"><header className="sticky top-0 z-20 flex h-[76px] items-center gap-4 border-b border-onko-line bg-white/95 px-6 backdrop-blur md:px-9"><div className="relative hidden max-w-3xl flex-1 md:block"><Search className="absolute left-4 top-1/2 -translate-y-1/2 text-onko-muted" size={18}/><input aria-label="Search patients" placeholder="Search patients, records, queries..." className="w-full rounded-xl bg-onko-surface py-3 pl-11 pr-4 text-[15px] outline-none placeholder:text-onko-muted/70 focus:ring-1 focus:ring-onko-teal"/></div><div className="ml-auto hidden items-center gap-2 rounded-full bg-onko-softteal px-4 py-2 text-[13px] font-semibold text-onko-muted lg:flex"><span className="h-2 w-2 rounded-full bg-onko-teal"/><span>Clinical Lead:</span><strong className="text-onko-ink">Dr. Rajiv Mehta, MD</strong></div><button aria-label="Notifications" className="grid h-11 w-11 place-items-center rounded-full bg-onko-surface text-onko-muted"><Bell size={19}/></button><div className="grid h-11 w-11 place-items-center rounded-full bg-onko-teal text-sm font-bold text-white">RM</div></header>
<main className="mx-auto w-full max-w-[1600px] px-6 py-7 md:px-9 md:py-9">{children}<SafetyNote/></main></div></div>}
