import Link from "next/link";
import DoctorShell from "@/components/DoctorShell";
import Timeline from "@/components/Timeline";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";

export const dynamic = "force-dynamic";

export default async function Patient360Page({ params }: { params: { id: string } }) {
  const d = await api.patient360(params.id);
  const p = d.patient;
  return (
    <DoctorShell>
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-semibold">{p.name}</h1>
          <p className="text-onko-ink/70">{p.age} · {p.diagnosis_label} · {p.regimen_label} cycle {p.cycle_current} of {p.cycle_total}</p>
        </div>
        <Link href={`/doctor/careplan/${p.id}`} className="bg-onko-teal text-white px-4 py-2 rounded-md">Open Care Plan Copilot</Link>
      </div>

      <section className="mt-8 bg-white border border-onko-line rounded-lg p-5">
        <h2 className="font-semibold">Since your last review</h2>
        <ul className="mt-2 list-disc pl-5 text-sm">
          {d.since_last_review.bullets.map((b) => <li key={b}>{b}</li>)}
        </ul>
      </section>

      <div className="grid md:grid-cols-2 gap-6 mt-6">
        <section>
          <h2 className="font-semibold mb-3">Timeline</h2>
          <Timeline events={d.timeline} />
        </section>
        <section className="grid gap-6 content-start">
          <div>
            <h2 className="font-semibold mb-2">Reports</h2>
            {d.reports.map((r) => (
              <div key={r.id} className="bg-white border border-onko-line rounded-lg p-4 text-sm">
                <div className="font-medium">{r.title}</div>
                {r.extracted_values.map((v) => (
                  <div key={v.name}>{v.name}: {v.value} {v.unit} — {r.title.split(" ")[0]}, {fmtDate(r.uploaded_at)}</div>
                ))}
                <details className="mt-2"><summary className="cursor-pointer text-onko-teal">Source document</summary>
                  <pre className="whitespace-pre-wrap text-xs mt-2">{r.text}</pre></details>
              </div>
            ))}
          </div>
          <div>
            <h2 className="font-semibold mb-2">Open queries</h2>
            {d.open_queries.map((q) => (
              <div key={q.id} className="bg-white border border-onko-line rounded-lg p-4 text-sm">
                <div className="text-xs text-onko-ink/60">{q.category.replace("_", " ").toLowerCase()} · via {q.channel}</div>
                {q.summary}
              </div>
            ))}
          </div>
        </section>
      </div>
    </DoctorShell>
  );
}
