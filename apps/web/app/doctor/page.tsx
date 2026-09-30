import { ArrowRight, Clock3, ShieldCheck } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import StatCards from "@/components/StatCards";
import AttentionQueue from "@/components/AttentionQueue";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DoctorHome() {
  const [overview, attention] = await Promise.all([api.overview(), api.attention()]);
  return (
    <DoctorShell>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="onko-eyebrow">Command center</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">Good morning, Dr. Mehta</h1>
          <p className="mt-2 max-w-2xl text-sm text-onko-muted md:text-base">A factual view of recorded patient activity, pending workflow items and today&apos;s care operations.</p>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-onko-line bg-white px-3 py-2 text-xs font-medium text-onko-muted"><ShieldCheck size={16} className="text-onko-teal" /> Clinician review remains the decision point</div>
      </div>

      <section className="mt-7"><StatCards data={overview} /></section>

      <div className="mt-8 grid gap-6 2xl:grid-cols-[minmax(0,1.55fr)_minmax(320px,.65fr)]">
        <section>
          <div className="mb-3"><h2 className="text-xl font-bold tracking-tight">Attention queue</h2><p className="mt-1 text-sm text-onko-muted">Explainable workflow signals surfaced with their recorded reasons.</p></div>
          <AttentionQueue items={attention} />
        </section>

        <aside className="grid content-start gap-4">
          <div className="onko-card p-5">
            <div className="flex items-center justify-between">
              <div><p className="onko-eyebrow">Today</p><h2 className="mt-1 text-lg font-bold">Consultations</h2></div>
              <div className="grid h-10 w-10 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><Clock3 size={19} /></div>
            </div>
            <div className="mt-5 flex items-end justify-between border-b border-onko-line pb-4">
              <div><p className="text-4xl font-bold tracking-tight">{overview.consultations_today}</p><p className="mt-1 text-sm text-onko-muted">scheduled for today</p></div>
              <ArrowRight size={18} className="text-onko-muted" />
            </div>
            <p className="mt-4 text-xs leading-5 text-onko-muted">Open a patient&apos;s 360 view to review recorded events, reports and unresolved queries before consultation.</p>
          </div>
          <div className="rounded-2xl border border-onko-softteal bg-onko-softteal/60 p-5">
            <p className="text-sm font-bold text-onko-teal">How this queue works</p>
            <p className="mt-2 text-sm leading-6 text-onko-muted">OnKo surfaces observable workflow events. It does not assign clinical risk or interpret their medical significance.</p>
          </div>
        </aside>
      </div>
    </DoctorShell>
  );
}
