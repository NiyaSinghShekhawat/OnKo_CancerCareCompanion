import Link from "next/link";
import { CalendarDays, ChevronRight, ClipboardList, FileText, MessageSquareText, UserRound, Users } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import Timeline from "@/components/Timeline";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Patient360Page({ params }: { params: { id: string } }) {
  const d = await api.patient360(params.id);
  const p = d.patient;
  const appointments = d.timeline.filter((e) => e.type === "APPOINTMENT");

  return (
    <DoctorShell>
      <div className="flex items-center gap-2 text-xs font-semibold text-onko-muted">
        <Link href="/doctor/patients" className="hover:text-onko-teal">Patients</Link><ChevronRight size={13} /><span>{p.name}</span>
      </div>

      <section className="onko-card mt-4 overflow-hidden">
        <div className="flex flex-wrap items-start justify-between gap-5 p-5 md:p-6">
          <div className="flex gap-4">
            <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-onko-softteal text-onko-teal"><UserRound size={23} /></div>
            <div>
              <div className="flex flex-wrap items-center gap-2"><h1 className="text-2xl font-bold tracking-tight">{p.name}</h1><span className="onko-chip bg-onko-softteal text-onko-teal">{p.journey_state.replaceAll("_", " ").toLowerCase()}</span></div>
              <p className="mt-1 text-sm text-onko-muted">{p.age} years · {p.gender} · {p.diagnosis_label}</p>
              <p className="mt-1 text-sm font-medium">{p.regimen_label} · Cycle {p.cycle_current} of {p.cycle_total}</p>
            </div>
          </div>
          <Link href={"/doctor/careplan/" + p.id} className="onko-button-primary"><ClipboardList size={17} />Care Plan Copilot</Link>
        </div>
        <div className="flex gap-1 overflow-x-auto border-t border-onko-line bg-onko-surface px-4 py-2 text-sm font-semibold">
          {["Overview", "Care Journey", "Reports", "Appointments", "Queries", "Caregiver & Consent"].map((tab, i) => (
            <a key={tab} href={i === 0 ? "#overview" : "#" + tab.toLowerCase().replaceAll(" ", "-").replace("&-", "")} className={"whitespace-nowrap rounded-lg px-3 py-2 " + (i === 0 ? "bg-white text-onko-teal shadow-sm" : "text-onko-muted hover:bg-white")}>{tab}</a>
          ))}
        </div>
      </section>

      <div id="overview" className="mt-6 grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(330px,.65fr)]">
        <div className="grid gap-6">
          <section className="onko-card p-5">
            <div className="flex items-center justify-between gap-3">
              <div><p className="onko-eyebrow">Since your last review</p><h2 className="mt-1 text-lg font-bold">Recorded changes</h2></div>
              <span className="text-xs text-onko-muted">{p.last_reviewed_at ? "Last reviewed " + fmtDate(p.last_reviewed_at) : "No previous review recorded"}</span>
            </div>
            <ul className="mt-4 grid gap-3">{d.since_last_review.bullets.map((b) => <li key={b} className="rounded-xl bg-onko-surface px-4 py-3 text-sm leading-6">{b}</li>)}</ul>
          </section>
          <section id="care-journey" className="onko-card p-5">
            <div className="mb-5 flex items-center justify-between"><div><p className="onko-eyebrow">Longitudinal record</p><h2 className="mt-1 text-lg font-bold">Care journey</h2></div><CalendarDays size={19} className="text-onko-teal" /></div>
            <Timeline events={d.timeline} />
          </section>
        </div>

        <aside className="grid content-start gap-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="onko-card p-4"><FileText size={17} className="text-onko-teal" /><p className="mt-3 text-2xl font-bold">{d.reports.length}</p><p className="text-xs text-onko-muted">Reports</p></div>
            <div className="onko-card p-4"><MessageSquareText size={17} className="text-onko-teal" /><p className="mt-3 text-2xl font-bold">{d.open_queries.length}</p><p className="text-xs text-onko-muted">Queries</p></div>
            <div className="onko-card p-4"><Users size={17} className="text-onko-teal" /><p className="mt-3 text-2xl font-bold">{d.caregivers.length}</p><p className="text-xs text-onko-muted">Caregivers</p></div>
          </div>

          <section id="reports" className="onko-card p-5">
            <h2 className="font-bold">Reports</h2>
            <div className="mt-3 grid gap-3">{d.reports.map((r) => (
              <div key={r.id} className="rounded-xl border border-onko-line bg-onko-surface p-3 text-sm">
                <div className="flex items-center justify-between gap-2"><span className="font-semibold">{r.title}</span><span className="text-xs text-onko-muted">{fmtDate(r.uploaded_at)}</span></div>
                <div className="mt-2 grid gap-1 text-onko-muted">{r.extracted_values.map((v) => <div key={v.name}>{v.name}: {v.value} {v.unit}</div>)}</div>
                <details className="mt-2"><summary className="cursor-pointer text-xs font-semibold text-onko-teal">View source text</summary><pre className="mt-2 whitespace-pre-wrap text-xs text-onko-muted">{r.text}</pre></details>
              </div>
            ))}</div>
          </section>

          <section id="appointments" className="onko-card p-5">
            <h2 className="font-bold">Appointments</h2>
            <div className="mt-3 grid gap-2">{appointments.length ? appointments.map((a) => <div key={a.id} className="rounded-xl bg-onko-surface p-3 text-sm"><p className="font-semibold">{a.title}</p><p className="mt-1 text-xs text-onko-muted">{fmtDate(a.scheduled_at)} · {a.status.replaceAll("_", " ").toLowerCase()}</p></div>) : <p className="text-sm text-onko-muted">No appointments recorded.</p>}</div>
          </section>

          <section id="queries" className="onko-card p-5">
            <h2 className="font-bold">Open queries</h2>
            <div className="mt-3 grid gap-3">{d.open_queries.length ? d.open_queries.map((q) => <div key={q.id} className="rounded-xl border border-onko-line bg-onko-surface p-3 text-sm"><div className="text-[11px] font-semibold uppercase tracking-wide text-onko-muted">{q.category.replaceAll("_", " ").toLowerCase()} · via {q.channel}</div><p className="mt-1 leading-5">{q.summary}</p></div>) : <p className="text-sm text-onko-muted">No open queries.</p>}</div>
          </section>

          <section id="caregiver-consent" className="onko-card p-5">
            <h2 className="font-bold">Caregiver & consent</h2>
            <div className="mt-3 grid gap-3">{d.caregivers.length ? d.caregivers.map((c) => <div key={c.id} className="rounded-xl bg-onko-surface p-3 text-sm"><div className="flex items-center justify-between gap-2"><span className="font-semibold">{c.name}</span><span className="onko-chip bg-white text-onko-muted">{c.consent_status.toLowerCase()}</span></div><p className="mt-1 text-xs text-onko-muted">{c.relation} · {c.type} caregiver</p></div>) : <p className="text-sm text-onko-muted">No caregiver access recorded.</p>}</div>
          </section>
        </aside>
      </div>
    </DoctorShell>
  );
}
