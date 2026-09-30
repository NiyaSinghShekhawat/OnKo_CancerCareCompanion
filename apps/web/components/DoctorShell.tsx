import Link from "next/link";
import { Bell, ChevronDown, LayoutDashboard, Search, Users } from "lucide-react";
import SafetyNote from "./SafetyNote";

const nav = [
  { href: "/doctor", label: "Command Center", icon: LayoutDashboard },
  { href: "/doctor/patients", label: "Patients", icon: Users },
];

const upcoming = ["Queries", "Reports", "Appointments", "My Team"];

export default function DoctorShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-onko-canvas text-onko-ink">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-onko-line bg-white lg:flex lg:flex-col">
        <div className="flex h-20 items-center border-b border-onko-line px-6">
          <Link href="/doctor" className="flex items-center gap-3" aria-label="OnKo doctor home">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-onko-teal text-sm font-bold text-white">O</span>
            <div>
              <div className="text-lg font-bold tracking-tight">OnKo</div>
              <div className="text-[11px] font-medium text-onko-muted">Cancer Care Companion</div>
            </div>
          </Link>
        </div>

        <div className="flex-1 px-4 py-6">
          <p className="onko-eyebrow px-3">Doctor workspace</p>
          <nav className="mt-3 grid gap-1">
            {nav.map(({ href, label, icon: Icon }) => (
              <Link key={href} href={href} className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-onko-ink transition hover:bg-onko-softteal hover:text-onko-teal">
                <Icon size={18} strokeWidth={1.8} />
                {label}
              </Link>
            ))}
          </nav>

          <p className="onko-eyebrow mt-8 px-3">Care operations</p>
          <div className="mt-3 grid gap-1">
            {upcoming.map((label) => (
              <div key={label} className="flex items-center justify-between rounded-xl px-3 py-2.5 text-sm text-onko-muted">
                <span>{label}</span>
                <span className="text-[10px] uppercase tracking-wide text-onko-muted/70">Soon</span>
              </div>
            ))}
          </div>
        </div>

        <div className="border-t border-onko-line p-4">
          <div className="rounded-2xl bg-onko-surface p-3">
            <p className="text-sm font-semibold">Dr. Mehta</p>
            <p className="mt-0.5 text-xs text-onko-muted">Medical Oncology</p>
          </div>
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-20 items-center gap-4 border-b border-onko-line bg-white/95 px-5 backdrop-blur md:px-8">
          <div className="relative hidden max-w-xl flex-1 md:block">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-onko-muted" size={17} />
            <input aria-label="Search patients" placeholder="Search patients, reports, queries..." className="w-full rounded-xl border border-onko-line bg-onko-surface py-2.5 pl-10 pr-4 text-sm outline-none transition placeholder:text-onko-muted/70 focus:border-onko-teal focus:bg-white" />
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button aria-label="Notifications" className="grid h-10 w-10 place-items-center rounded-xl border border-onko-line bg-white text-onko-muted transition hover:bg-onko-hover"><Bell size={18} /></button>
            <button className="hidden items-center gap-2 rounded-xl border border-onko-line bg-white px-3 py-2 text-sm font-semibold sm:flex">Dr. Mehta <ChevronDown size={15} className="text-onko-muted" /></button>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1500px] px-5 py-7 md:px-8 md:py-9">
          {children}
          <SafetyNote />
        </main>
      </div>
    </div>
  );
}
