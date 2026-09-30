"use client";
import { useState } from "react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";
import type { CarePlanDraft, CopilotItem, EventType } from "@/lib/types";

const TYPES: EventType[] = ["MEDICATION", "INVESTIGATION", "TREATMENT", "APPOINTMENT", "MILESTONE"];

export default function CopilotPage({ params }: { params: { id: string } }) {
  const [text, setText] = useState("");
  const [draft, setDraft] = useState<CarePlanDraft | null>(null);
  const [approved, setApproved] = useState(false);
  const [busy, setBusy] = useState(false);

  const edit = (i: number, patch: Partial<CopilotItem>) =>
    draft && setDraft({ ...draft, items: draft.items.map((it, j) => (j === i ? { ...it, ...patch } : it)) });

  return (
    <DoctorShell>
      <h1 className="text-2xl font-semibold">Care Plan Copilot</h1>
      <p className="text-onko-ink/70 mt-1">Write the plan you have decided. OnKo structures it; nothing reaches the patient until you approve.</p>

      <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4}
        placeholder="e.g. Cycle 5 chemo on 15 Oct. Capecitabine 500mg BD after food for 14 days. CBC on 13 Oct."
        className="mt-6 w-full border border-onko-line rounded-lg p-3 bg-white" />
      <button disabled={busy || !text} onClick={async () => { setBusy(true); setDraft(await api.createDraft(params.id, text)); setBusy(false); }}
        className="mt-3 bg-onko-teal text-white px-4 py-2 rounded-md disabled:opacity-50">
        {busy ? "Structuring…" : "Structure plan"}
      </button>

      {draft && (
        <section className="mt-8">
          <h2 className="font-semibold mb-3">Draft — review and edit</h2>
          {draft.warnings?.map((w) => <p key={w} className="text-sm text-onko-amber mb-2">{w}</p>)}
          <div className="bg-white border border-onko-line rounded-lg overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-onko-ink/60"><tr><th className="p-3">Type</th><th className="p-3">Item</th><th className="p-3">Start</th><th className="p-3">End</th><th className="p-3">From your text</th></tr></thead>
              <tbody>
                {draft.items.map((it, i) => (
                  <tr key={i} className="border-t border-onko-line">
                    <td className="p-2"><select value={it.type} onChange={(e) => edit(i, { type: e.target.value as EventType })} className="border rounded p-1">
                      {TYPES.map((t) => <option key={t}>{t}</option>)}</select></td>
                    <td className="p-2"><input value={it.title} onChange={(e) => edit(i, { title: e.target.value })} className="border rounded p-1 w-full" /></td>
                    <td className="p-2"><input type="date" value={it.start_date} onChange={(e) => edit(i, { start_date: e.target.value })} className="border rounded p-1" /></td>
                    <td className="p-2"><input type="date" value={it.end_date ?? ""} onChange={(e) => edit(i, { end_date: e.target.value || null })} className="border rounded p-1" /></td>
                    <td className="p-2 text-onko-ink/60 italic">{it.source_span}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button disabled={approved} onClick={async () => { await api.updateDraft(draft.id, draft.items); await api.approveDraft(draft.id); setApproved(true); }}
            className="mt-4 bg-onko-teal text-white px-4 py-2 rounded-md disabled:opacity-60">
            {approved ? "Plan approved — added to patient journey" : "Approve plan"}
          </button>
        </section>
      )}
    </DoctorShell>
  );
}
