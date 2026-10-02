"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Check,
  FlaskConical,
  Pencil,
  Plus,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";
import type { CarePlanDraft, CarePlanItem, CopilotItem, EventType } from "@/lib/types";

const TYPES: EventType[] = ["MEDICATION", "INVESTIGATION", "TREATMENT", "APPOINTMENT", "MILESTONE"];

export default function CopilotPage({ params }: { params: { id: string } }) {
  const [text, setText] = useState("");
  const [draft, setDraft] = useState<CarePlanDraft | null>(null);
  const [approved, setApproved] = useState(false);
  const [busy, setBusy] = useState(false);

  const [existing, setExisting] = useState<CarePlanItem[]>([]);
  const [loadingPlan, setLoadingPlan] = useState(true);
  const [planError, setPlanError] = useState("");
  const [editing, setEditing] = useState<CarePlanItem | null>(null);
  const [savingExisting, setSavingExisting] = useState(false);
  const [removingId, setRemovingId] = useState<string | null>(null);

  const loadExisting = async () => {
    setPlanError("");
    try {
      setExisting(await api.carePlan(params.id));
    } catch (err) {
      setPlanError(err instanceof Error ? err.message : "Unable to load care plan");
    } finally {
      setLoadingPlan(false);
    }
  };

  useEffect(() => {
    setLoadingPlan(true);
    void loadExisting();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.id]);

  const editDraft = (i: number, patch: Partial<CopilotItem>) =>
    draft && setDraft({ ...draft, items: draft.items.map((it, j) => (j === i ? { ...it, ...patch } : it)) });

  const removeDraft = (i: number) =>
    draft && setDraft({ ...draft, items: draft.items.filter((_, j) => j !== i) });

  const move = (i: number, dir: -1 | 1) => {
    if (!draft) return;
    const j = i + dir;
    if (j < 0 || j >= draft.items.length) return;
    const items = [...draft.items];
    [items[i], items[j]] = [items[j], items[i]];
    setDraft({ ...draft, items });
  };

  const add = () =>
    draft &&
    setDraft({
      ...draft,
      items: [
        ...draft.items,
        {
          type: "MILESTONE",
          title: "New care-plan item",
          details: {},
          start_date: new Date().toISOString().slice(0, 10),
          end_date: null,
          recurrence: null,
          source_span: "Added manually by clinician",
        },
      ],
    });

  const saveExisting = async () => {
    if (!editing) return;
    setSavingExisting(true);
    setPlanError("");
    try {
      const updated = await api.updateCarePlanItem(editing.id, {
        type: editing.type,
        title: editing.title,
        details: editing.details,
        start_date: editing.start_date,
        end_date: editing.end_date,
        recurrence: editing.recurrence,
      });
      setExisting(items => items.map(item => (item.id === updated.id ? updated : item)));
      setEditing(null);
    } catch (err) {
      setPlanError(err instanceof Error ? err.message : "Unable to save care-plan item");
    } finally {
      setSavingExisting(false);
    }
  };

  const removeExisting = async (item: CarePlanItem) => {
    const confirmed = window.confirm(
      `Remove "${item.title}" from the active care plan?\n\nFuture scheduled activity will be removed. Previously recorded activity will stay in the patient history.`,
    );
    if (!confirmed) return;

    setRemovingId(item.id);
    setPlanError("");
    try {
      await api.deleteCarePlanItem(item.id);
      setExisting(items => items.filter(x => x.id !== item.id));
      if (editing?.id === item.id) setEditing(null);
    } catch (err) {
      setPlanError(err instanceof Error ? err.message : "Unable to remove care-plan item");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <DoctorShell>
      <div className="max-w-[1380px]">
        <section className="onko-card overflow-hidden">
          <div className="border-b border-onko-line px-6 py-5">
            <p className="onko-eyebrow">Current approved care plan</p>
            <h1 className="mt-1 text-[30px] font-bold">Review Existing Plan</h1>
            <p className="mt-2 text-[14px] text-onko-muted">
              Previously approved items stay visible here before you add or restructure anything new.
            </p>
          </div>

          <div className="p-6">
            {planError && (
              <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-onko-sos">
                {planError}
              </div>
            )}

            {loadingPlan ? (
              <p className="text-[14px] text-onko-muted">Loading approved plan…</p>
            ) : existing.length ? (
              <div className="grid gap-3">
                {existing.map(item => (
                  <article key={item.id} className="rounded-xl border border-onko-line bg-onko-surface p-4">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div className="min-w-0">
                        <div className="flex flex-wrap items-center gap-2">
                          <strong className="text-[16px]">{item.title}</strong>
                          <span className="onko-chip bg-white text-onko-muted">{item.type.toLowerCase()}</span>
                          <span className="onko-chip bg-onko-softteal text-onko-teal">Approved</span>
                        </div>
                        <p className="mt-2 text-[13px] text-onko-muted">
                          {item.start_date}
                          {item.end_date ? ` → ${item.end_date}` : ""}
                          {item.recurrence ? ` · ${item.recurrence}` : ""}
                        </p>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => setEditing({ ...item })}
                          className="onko-button-secondary"
                          aria-label={`Edit ${item.title}`}
                        >
                          <Pencil size={14} />
                          Edit
                        </button>
                        <button
                          onClick={() => void removeExisting(item)}
                          disabled={removingId === item.id}
                          className="onko-button-secondary text-onko-sos disabled:opacity-50"
                          aria-label={`Remove ${item.title}`}
                        >
                          <Trash2 size={14} />
                          {removingId === item.id ? "Removing…" : "Remove"}
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <p className="text-[14px] text-onko-muted">No approved care-plan items yet.</p>
            )}
          </div>
        </section>

        <section className="onko-card mt-6 overflow-hidden">
          <div className="flex items-center justify-between border-b border-onko-line bg-onko-softteal/55 px-6 py-5">
            <div>
              <p className="text-[12px] font-bold uppercase tracking-[.1em] text-onko-teal">
                Care Plan Copilot · Human-governed workflow structuring
              </p>
              <h1 className="mt-1 text-[30px] font-bold">Structure an Already-Decided Plan</h1>
            </div>
            <span className="onko-chip bg-white text-onko-teal">Zero diagnostic generation</span>
          </div>

          <div className="p-6">
            <p className="text-[15px] font-bold uppercase tracking-[.08em] text-onko-muted">
              Doctor&apos;s dictated / typed clinical entry
            </p>
            <textarea
              value={text}
              onChange={e => setText(e.target.value)}
              rows={4}
              placeholder="CBC before chemotherapy on 24 Sept. Capecitabine 500mg BID with food for 14 days..."
              className="mt-2 w-full rounded-xl border border-onko-line bg-onko-surface p-4 text-[16px] leading-7 outline-none focus:border-onko-teal"
            />
            <div className="mt-3 flex justify-end">
              <button
                disabled={busy || !text}
                onClick={async () => {
                  setBusy(true);
                  setApproved(false);
                  try {
                    setDraft(await api.createDraft(params.id, text));
                  } finally {
                    setBusy(false);
                  }
                }}
                className="onko-button-primary disabled:opacity-50"
              >
                <Sparkles size={15} />
                {busy ? "Structuring…" : "Structure Plan (Done)"}
              </button>
            </div>
          </div>
        </section>

        {draft && (
          <section className="mt-6">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-[12px] font-bold uppercase tracking-[.1em] text-violet-700">Draft workflow stage</p>
                <h2 className="mt-1 text-[23px] font-bold">
                  {draft.items.length} items structured from your input. Review, adjust, or reclassify below.
                </h2>
              </div>
              <span className="onko-chip bg-onko-amberbg text-onko-amber">Requires clinician approval</span>
            </div>

            {!!draft.warnings?.length && (
              <div className="mb-4 rounded-xl border border-amber-200 bg-onko-amberbg p-4 text-onko-amber">
                <div className="flex gap-3">
                  <AlertTriangle size={19} className="mt-0.5 shrink-0" />
                  <div>
                    <p className="text-[14px] font-bold">Review these Copilot warnings before approval</p>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-[13px] leading-5">
                      {draft.warnings.map((warning, i) => (
                        <li key={`${warning}-${i}`}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            <div className="mb-3 flex justify-end">
              <button onClick={add} className="onko-button-secondary">
                <Plus size={15} />
                Add item
              </button>
            </div>

            <div className="grid gap-3">
              {draft.items.map((it, i) => (
                <article key={i} className="onko-card p-6">
                  <div className="grid gap-4 lg:grid-cols-[180px_1fr_170px_170px]">
                    <label className="text-[15px] font-bold uppercase text-onko-muted">
                      Type
                      <select
                        value={it.type}
                        onChange={e => editDraft(i, { type: e.target.value as EventType })}
                        className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                      >
                        {TYPES.map(t => (
                          <option key={t}>{t}</option>
                        ))}
                      </select>
                    </label>

                    <label className="text-[15px] font-bold uppercase text-onko-muted">
                      Workflow item
                      <input
                        value={it.title}
                        onChange={e => editDraft(i, { title: e.target.value })}
                        className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                      />
                    </label>

                    <label className="text-[15px] font-bold uppercase text-onko-muted">
                      Start
                      <input
                        type="date"
                        value={it.start_date}
                        onChange={e => editDraft(i, { start_date: e.target.value })}
                        className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                      />
                    </label>

                    <label className="text-[15px] font-bold uppercase text-onko-muted">
                      End
                      <input
                        type="date"
                        value={it.end_date ?? ""}
                        onChange={e => editDraft(i, { end_date: e.target.value || null })}
                        className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                      />
                    </label>
                  </div>

                  <div className="mt-4 flex flex-wrap justify-end gap-2">
                    <button onClick={() => move(i, -1)} className="onko-button-secondary">
                      <ArrowUp size={14} />
                      Up
                    </button>
                    <button onClick={() => move(i, 1)} className="onko-button-secondary">
                      <ArrowDown size={14} />
                      Down
                    </button>
                    <button onClick={() => removeDraft(i)} className="onko-button-secondary text-onko-sos">
                      <Trash2 size={14} />
                      Remove
                    </button>
                  </div>

                  <div className="mt-4 flex gap-2 rounded-xl bg-onko-softteal/60 p-3 text-[14px] text-onko-muted">
                    <FlaskConical size={15} className="shrink-0 text-onko-teal" />
                    <span>
                      <strong>Extracted from doctor input:</strong> “{it.source_span}”
                    </span>
                  </div>
                </article>
              ))}
            </div>

            <div className="mt-4 flex justify-end">
              <button
                disabled={approved || !draft.items.length}
                onClick={async () => {
                  await api.updateDraft(draft.id, draft.items);
                  await api.approveDraft(draft.id);
                  setApproved(true);
                  await loadExisting();
                }}
                className="onko-button-primary disabled:opacity-60"
              >
                <Check size={15} />
                {approved ? "Plan approved — added to journey" : "Approve plan"}
              </button>
            </div>
          </section>
        )}

        {editing && (
          <div className="fixed inset-0 z-50 grid place-items-center bg-black/35 p-4">
            <section className="w-full max-w-2xl rounded-2xl bg-white shadow-2xl">
              <div className="flex items-start justify-between border-b border-onko-line px-6 py-5">
                <div>
                  <p className="onko-eyebrow">Approved care-plan item</p>
                  <h2 className="mt-1 text-[24px] font-bold">Edit recorded plan</h2>
                  <p className="mt-1 text-[13px] text-onko-muted">
                    Saving changes rebuilds future scheduled activity only. Previously recorded activity remains in history.
                  </p>
                </div>
                <button
                  onClick={() => setEditing(null)}
                  className="rounded-lg p-2 text-onko-muted hover:bg-onko-surface"
                  aria-label="Close edit care plan"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="grid gap-4 p-6 sm:grid-cols-2">
                <label className="text-[13px] font-bold uppercase text-onko-muted">
                  Type
                  <select
                    value={editing.type}
                    onChange={e => setEditing({ ...editing, type: e.target.value as EventType })}
                    className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                  >
                    {TYPES.map(t => (
                      <option key={t}>{t}</option>
                    ))}
                  </select>
                </label>

                <label className="text-[13px] font-bold uppercase text-onko-muted">
                  Title
                  <input
                    value={editing.title}
                    onChange={e => setEditing({ ...editing, title: e.target.value })}
                    className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                  />
                </label>

                <label className="text-[13px] font-bold uppercase text-onko-muted">
                  Start date
                  <input
                    type="date"
                    value={editing.start_date}
                    onChange={e => setEditing({ ...editing, start_date: e.target.value })}
                    className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                  />
                </label>

                <label className="text-[13px] font-bold uppercase text-onko-muted">
                  End date
                  <input
                    type="date"
                    value={editing.end_date ?? ""}
                    onChange={e => setEditing({ ...editing, end_date: e.target.value || null })}
                    className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                  />
                </label>

                <label className="text-[13px] font-bold uppercase text-onko-muted sm:col-span-2">
                  Recurrence / schedule
                  <input
                    value={editing.recurrence ?? ""}
                    onChange={e => setEditing({ ...editing, recurrence: e.target.value || null })}
                    placeholder="daily 09:00, 21:00 or every 7 days"
                    className="mt-2 w-full rounded-lg border border-onko-line p-2.5 text-[15px]"
                  />
                  <span className="mt-1 block text-[12px] font-normal normal-case text-onko-muted">
                    Supported formats: daily HH:MM[, HH:MM ...] or every N days.
                  </span>
                </label>
              </div>

              <div className="flex justify-end gap-2 border-t border-onko-line px-6 py-4">
                <button onClick={() => setEditing(null)} disabled={savingExisting} className="onko-button-secondary">
                  Cancel
                </button>
                <button
                  onClick={() => void saveExisting()}
                  disabled={savingExisting || !editing.title.trim() || !editing.start_date}
                  className="onko-button-primary disabled:opacity-50"
                >
                  <Check size={15} />
                  {savingExisting ? "Saving…" : "Save changes"}
                </button>
              </div>
            </section>
          </div>
        )}
      </div>
    </DoctorShell>
  );
}
