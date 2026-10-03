import Link from "next/link";
import {
  ArrowRight,
  HeartHandshake,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";

const roles = [
  {
    href: "/patient/login",
    name: "Patient",
    tag: "Daily companion",
    description: "Follow your care journey, view today's care items, keep reports together, ask for help and stay connected with your care team.",
    note: "A calmer view focused on what you need today.",
    icon: UserRound,
    primary: true,
  },
  {
    href: "/doctor",
    name: "Doctor",
    tag: "Clinical workspace",
    description: "Review recorded activity, Patient 360, reports, queries, attention items and doctor-controlled care plans in one longitudinal workspace.",
    note: "OnKo organizes the record. You interpret and decide.",
    icon: Stethoscope,
  },
  {
    href: "/caregiver/login",
    name: "Caregiver",
    tag: "Consent-based support",
    description: "Stay informed about the parts of the care journey the patient has chosen to share and help with permitted coordination and uploads.",
    note: "Access remains governed by patient consent.",
    icon: HeartHandshake,
  },
];

export default function Home() {
  return (
    <main className="min-h-screen bg-onko-canvas">
      <header className="border-b border-onko-line bg-white/90 backdrop-blur-xl">
        <div className="mx-auto flex h-20 max-w-[1400px] items-center justify-between px-5 md:px-10">
          <Link href="/" className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-2xl bg-onko-teal text-base font-bold text-white">O</span>
            <div>
              <div className="text-xl font-bold tracking-tight text-onko-teal">OnKo</div>
              <div className="text-[11px] font-medium text-onko-muted">Cancer Care Companion</div>
            </div>
          </Link>
          <div className="hidden items-center gap-2 rounded-full border border-onko-line bg-onko-surface px-3 py-2 text-sm font-semibold text-onko-muted sm:flex">
            <ShieldCheck size={15} className="text-onko-teal" />
            Connected care, clinician-led
          </div>
        </div>
      </header>

      <section className="relative mx-auto max-w-[1240px] overflow-hidden px-5 pb-14 pt-12 md:px-10 md:pb-20 md:pt-16">
        <div className="pointer-events-none absolute left-1/2 top-0 -z-0 h-72 w-[680px] -translate-x-1/2 rounded-full bg-onko-softteal/70 blur-3xl" />

        <div className="relative z-10 mx-auto max-w-3xl text-center">
          <div className="mx-auto grid h-14 w-14 place-items-center rounded-full border border-onko-line bg-white shadow-card">
            <HeartHandshake size={25} className="text-onko-teal" />
          </div>
          <p className="mt-5 text-sm font-bold uppercase tracking-[0.18em] text-onko-tealaccent">Choose your workspace</p>
          <h1 className="mt-3 text-5xl font-bold tracking-[-0.035em] text-onko-ink md:text-6xl">Your cancer care journey, connected.</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg leading-8 text-onko-muted md:text-xl">
            OnKo keeps patients, caregivers and doctors aligned across appointments, medicines, reports, questions and milestones — while clinical decisions remain with the doctor.
          </p>
        </div>

        <div className="relative z-10 mt-10 grid gap-4 md:grid-cols-2">
          {roles.map((role) => {
            const Icon = role.icon;
            return (
              <Link key={role.name} href={role.href} className="group onko-card flex min-h-[320px] flex-col p-7 transition duration-300 hover:-translate-y-0.5 hover:border-onko-teal/30 hover:shadow-lg md:p-8">
                <div className="flex items-start justify-between gap-4">
                  <span className={"grid h-14 w-14 place-items-center rounded-full " + (role.primary ? "bg-onko-softteal text-onko-teal" : "bg-onko-surface text-onko-teal")}>
                    <Icon size={26} strokeWidth={1.8} />
                  </span>
                  <span className="rounded-full bg-onko-surface px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.08em] text-onko-muted">{role.tag}</span>
                </div>
                <h2 className="mt-6 text-3xl font-bold tracking-tight">{role.name}</h2>
                <p className="mt-2 flex-1 text-base leading-7 text-onko-muted">{role.description}</p>
                <div className="mt-5 rounded-xl bg-onko-surface px-4 py-3 text-sm leading-5 text-onko-muted">{role.note}</div>
                <div className={"mt-5 flex items-center justify-between rounded-xl px-4 py-3 text-sm font-bold transition " + (role.primary ? "bg-onko-teal text-white group-hover:bg-onko-tealdark" : "border border-onko-line bg-white text-onko-teal group-hover:bg-onko-softteal")}>
                  <span>Continue as {role.name}</span>
                  <ArrowRight size={17} className="transition-transform group-hover:translate-x-1" />
                </div>
              </Link>
            );
          })}
        </div>

        <div className="relative z-10 mt-6 flex flex-col items-start justify-between gap-4 rounded-2xl border border-onko-line bg-onko-surface px-5 py-4 md:flex-row md:items-center">
          <div>
            <p className="text-sm font-bold">One journey, different views.</p>
            <p className="mt-1 text-sm leading-5 text-onko-muted">Each workspace shows the information and actions appropriate to that role, while the underlying patient journey stays connected.</p>
          </div>
          <div className="shrink-0 rounded-full bg-white px-3 py-2 text-sm font-semibold text-onko-teal shadow-sm">Patient-focused · Doctor-controlled</div>
        </div>
      </section>

      <footer className="border-t border-onko-line bg-white">
        <div className="mx-auto flex max-w-[1240px] flex-col gap-2 px-5 py-6 text-sm text-onko-muted md:flex-row md:items-center md:justify-between md:px-10">
          <span><strong className="text-onko-teal">OnKo</strong> · Cancer Care Companion</span>
          <span>The doctor decides the care. OnKo keeps the journey connected.</span>
        </div>
      </footer>
    </main>
  );
}
