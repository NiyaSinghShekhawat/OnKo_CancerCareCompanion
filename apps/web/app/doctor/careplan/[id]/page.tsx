"use client";
import { useState } from "react";
import { Check, FileText, Sparkles } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";
import type { CarePlanDraft, CopilotItem, EventType } from "@/lib/types";

const TYPES: EventType[] = ["MEDICATION", "INVESTIGATION", "TREATMENT", "APPOINTMENT", "MILESTONE"];

export default function CopilotPage({ params }: { params: { id: string } }) {
  const [text, setText] = useState("");
  const [draft, setDraft] = useState<CarePlanDraft | null>(null);
  const [approved, setApproved] = useState(false);
  const [busy, setBusy] = useState(false);
  const edit = (i: number, patch: Partial<CopilotItem>) => draft && setDraft({ ...draft, items: draft.items.map((it, j) => (j === i ? { ...it, ...patch } : it)) });

  return (
    <DoctorShell>
      <div className="max-w-5xl">
        <p className="onko-eyebrow">Care planning</p>
        <div className="mt-2 flex flex-wrap items-start justify-between gap-4">
          <div><h1 className="text-3xl font-bold tracking-tight">Care Plan Copilot</h1><p className="mt-2 max-w-2xl text-sm leading-6 text-onko-muted">Structure an already-decided clinical plan into operational workflow items. Nothing reaches the patient journey until you review and approve it.</p></div>
          <span className="onko-chip bg-onko-softteal text-onko-teal"><Sparkles size={13} className="mr-1.5" />Workflow assistant</span>
        </div>

        <section className="onko-card mt-7 p-5 md:p-6">
          <div className="flex items-center gap-3"><div className="grid h-10 w-10 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><FileText size={19} /></div><div><h2 className="font-bold">Doctor&apos;s plan</h2><p className="text-xs text-onko-muted">Enter only the plan you have already decided.</p></div></div>
          <textarea value={text} onChange={(e) => setText(e.target.value)} rows={5} placeholder="e.g. Cycle 5 chemo on 15 Oct. Capecitabine 500mg BD after food for 14 days. CBC on 13 Oct. Review on 16 Oct." className="mt-5 w-full resize-y rounded-xl border border-onko-line bg-onko-surface p-4 text-sm leading-6 outline-none transition placeholder:text-onko-muted/60 focus:border-onko-teal focus:bg-white" />
          <div className="mt-3 flex justify-end"><button disabled={busy || !text} onClick={async () => { setBusy(true); setDraft(await api.createDraft(params.id, text)); setBusy(false); }} className="onko-button-primary disabled:cursor-not-allowed disabled:opacity-50"><Sparkles size={16} />{busy ? "Structuring…" : "Structure plan"}</button></div>
        </section>

        {draft && (
          <section className="mt-7">
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div><p className="onko-eyebrow">AI-structured output</p><h2 className="mt-1 text-xl font-bold">Draft — review and edit</h2></div><span className="onko-chip bg-onko-amberbg text-onko-amber">Requires clinician approval</span></div>
            {draft.warnings?.map((w) => <p key={w} className="mb-3 rounded-xl border border-amber-200 bg-onko-amberbg px-4 py-3 text-sm text-onko-amber">{w}</p>)}
            <div className="grid gap-3">
              {draft.items.map((it, i) => (
                <div key={i} className="onko-card p-4 md:p-5">
                  <div className="grid gap-4 lg:grid-cols-[170px_1fr_160px_160px]">
                    <label className="text-xs font-semibold text-onko-muted">Type<select value={it.type} onChange={(e) => edit(i, { type: e.target.value as EventType })} className="mt-1.5 w-full rounded-lg border border-onko-line bg-white p-2.5 text-sm text-onko-ink">{TYPES.map((t) => <option key={t}>{t}</option>)}</select></label>
                    <label className="text-xs font-semibold text-onko-muted">Workflow item<input value={it.title} onChange={(e) => edit(i, { title: e.target.value })} className="mt-1.5 w-full rounded-lg border border-onko-line bg-white p-2.5 text-sm text-onko-ink" /></label>
                    <label className="text-xs font-semibold text-onko-muted">Start date<input type="date" value={it.start_date} onChange={(e) => edit(i, { start_date: e.target.value })} className="mt-1.5 w-full rounded-lg border border-onko-line bg-white p-2.5 text-sm text-onko-ink" /></label>
                    <label className="text-xs font-semibold text-onko-muted">End date<input type="date" value={it.end_date ?? ""} onChange={(e) => edit(i, { end_date: e.target.value || null })} className="mt-1.5 w-full rounded-lg border border-onko-line bg-white p-2.5 text-sm text-onko-ink" /></label>
                  </div>
                  <div className="mt-4 rounded-xl bg-onko-surface px-3 py-2 text-xs text-onko-muted"><span className="font-semibold">Grounded in your text:</span> “{it.source_span}”</div>
                </div>
              ))}
            </div>
            <div className="mt-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-onko-softteal bg-onko-softteal/60 p-4">
              <p className="max-w-2xl text-xs leading-5 text-onko-muted">Review every item before approval. OnKo structures the doctor&apos;s stated intent; it does not independently introduce medicines, investigations or treatments.</p>
              <button disabled={approved} onClick={async () => { await api.updateDraft(draft.id, draft.items); await api.approveDraft(draft.id); setApproved(true); }} className="onko-button-primary disabled:opacity-60"><Check size={16} />{approved ? "Plan approved — added to journey" : "Approve plan"}</button>
            </div>
          </section>
        )}
      </div>
    </DoctorShell>
  );
}
