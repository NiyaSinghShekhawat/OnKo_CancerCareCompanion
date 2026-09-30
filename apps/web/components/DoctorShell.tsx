import Link from "next/link";
import {
  Bell, CalendarDays, ClipboardList, FileText, LayoutDashboard, MessageSquareText,
  Search, ShieldCheck, Users, UsersRound,
} from "lucide-react";
import SafetyNote from "./SafetyNote";

const nav = [
  { href: "/doctor", label: "Overview", icon: LayoutDashboard },
  { href: "/doctor/patients", label: "Patients", icon: Users },
];
const secondary = [
  { label: "Attention Queue", icon: ShieldCheck },
  { label: "Queries", icon: MessageSquareText },
  { label: "Reports", icon: FileText },
  { label: "Appointments", icon: CalendarDays },
  { label: "Care Plans", icon: ClipboardList },
  { label: "Care Team", icon: UsersRound },
];

export default function DoctorShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-onko-canvas text-onko-ink">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-[250px] border-r border-onko-line bg-white xl:flex xl:flex-col">
        <Link href="/" className="flex h-[76px] items-center gap-3 border-b border-onko-line px-5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-onko-teal text-sm font-bold text-white">O</span>
          <div><div className="text-[18px] font-bold leading-tight text-onko-teal">OnKo</div><div className="text-[10px] font-semibold uppercase tracking-[.12em] text-onko-muted">Oncology Care</div></div>
        </Link>

        <div className="border-b border-onko-line px-4 py-4">
          <p className="text-[10px] font-bold uppercase tracking-[.12em] text-onko-muted">Active perspective</p>
          <div className="mt-2 grid grid-cols-2 rounded-xl bg-onko-softteal p-1 text-center text-xs font-semibold">
            <span className="rounded-lg bg-white px-2 py-2 text-onko-teal shadow-sm">Doctor</span>
            <Link href="/patient" className="px-2 py-2 text-onko-muted">Patient</Link>
            <Link href="/caregiver" className="px-2 py-2 text-onko-muted">Caregiver</Link>
            <span className="px-2 py-2 text-onko-muted">Care Team</span>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {nav.map(({ href, label, icon: Icon }) => <Link key={href} href={href} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-semibold transition hover:bg-onko-softteal hover:text-onko-teal"><Icon size={17}/>{label}</Link>)}
          {secondary.map(({ label, icon: Icon }) => <div key={label} className="flex items-center gap-3 rounded-lg px-3 py-2.5 text-[14px] font-medium text-onko-muted"><Icon size={17}/>{label}</div>)}
        </nav>

        <div className="m-4 flex items-center gap-2 rounded-xl bg-onko-softteal px-3 py-3 text-xs font-semibold text-onko-teal"><span className="h-2 w-2 rounded-full bg-onko-teal"/>Safer Harbor Core <span className="ml-auto text-[10px] text-onko-muted">v2.4</span></div>
      </aside>

      <div className="xl:pl-[250px]">
        <header className="sticky top-0 z-20 flex h-[68px] items-center gap-4 border-b border-onko-line bg-white/95 px-5 backdrop-blur md:px-7">
          <div className="relative hidden max-w-2xl flex-1 md:block"><Search className="absolute left-3 top-1/2 -translate-y-1/2 text-onko-muted" size={16}/><input aria-label="Search patients" placeholder="Search patients, records, queries...  Cmd+K" className="w-full rounded-xl bg-onko-surface py-2.5 pl-10 pr-4 text-[13px] outline-none placeholder:text-onko-muted/70 focus:ring-1 focus:ring-onko-teal"/></div>
          <div className="ml-auto hidden items-center gap-2 rounded-full bg-onko-softteal px-3 py-1.5 text-[11px] font-semibold text-onko-muted lg:flex"><span className="h-2 w-2 rounded-full bg-onko-teal"/><span>Clinical Lead:</span><strong className="text-onko-ink">Dr. Rajiv Mehta, MD</strong></div>
          <button aria-label="Notifications" className="grid h-9 w-9 place-items-center rounded-full bg-onko-surface text-onko-muted"><Bell size={17}/></button>
          <div className="grid h-9 w-9 place-items-center rounded-full bg-onko-teal text-xs font-bold text-white">RM</div>
        </header>
        <main className="mx-auto w-full max-w-[1480px] px-5 py-6 md:px-7 md:py-7">{children}<SafetyNote /></main>
      </div>
    </div>
  );
}
