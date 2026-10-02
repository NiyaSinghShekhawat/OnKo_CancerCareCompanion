"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, ClipboardList, MessageSquareText, Pill, Send, Stethoscope } from "lucide-react";
import { api } from "@/lib/api";
import { fmtDate } from "@/lib/format";
import type { Patient, PatientQuery, QueryCategory } from "@/lib/types";

const choices: {
  id: QueryCategory;
  title: string;
  description: string;
  icon: typeof MessageSquareText;
  placeholder: string;
}[] = [
  {
    id: "ADMINISTRATIVE",
    title: "General question",
    description: "Appointments, documents, scheduling, navigation or routine information.",
    icon: MessageSquareText,
    placeholder: "e.g. When is my next appointment?",
  },
  {
    id: "MEDICATION",
    title: "Medication-related",
    description:
      "Ask about medication already prescribed by your care team. OnKo will not change medication instructions.",
    icon: Pill,
    placeholder: "e.g. I have a question about the timing written for my medicine.",
  },
  {
    id: "SYMPTOM_CONCERN",
    title: "Body manifestation / concern",
    description: "Report pain, discomfort, a symptom or another bodily change for care-team review.",
    icon: Stethoscope,
    placeholder: "Describe what you are experiencing in your own words…",
  },
];

export default function PatientQueriesClient({
  p,
  openQueries,
  queryHistory,
}: {
  p: Patient;
  openQueries: PatientQuery[];
  queryHistory: PatientQuery[];
}) {
  const router = useRouter();
  const [category, setCategory] = useState<QueryCategory>("ADMINISTRATIVE");
  const [text, setText] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  const selected = useMemo(() => choices.find(c => c.id === category)!, [category]);
  const pastQueries = queryHistory.filter(q => q.status === "RESOLVED");

  async function submit() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      await api.sendQuery(
        p.id,
        text.trim(),
        { role: "patient", userId: p.id }
      );
      setSent(true);
      setText("");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto w-full max-w-[1320px]">
      <p className="onko-eyebrow">Care-team communication</p>
      <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">Queries</h1>
      <p className="mt-2 max-w-2xl text-[15px] leading-6 text-onko-muted">
        Choose what your message is about. OnKo can organize and route it for review; it does not diagnose symptoms or
        change treatment.
      </p>

      <section className="mt-6">
        <h2 className="text-[18px] font-bold">What do you need help with?</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {choices.map(c => {
            const I = c.icon;
            const active = category === c.id;
            return (
              <button
                key={c.id}
                onClick={() => {
                  setCategory(c.id);
                  setSent(false);
                }}
                className={
                  "rounded-2xl border p-5 text-left transition " +
                  (active
                    ? "border-onko-teal bg-onko-softteal shadow-sm"
                    : "border-onko-line bg-white hover:bg-onko-hover")
                }
              >
                <span
                  className={
                    "grid h-11 w-11 place-items-center rounded-xl " +
                    (active ? "bg-onko-teal text-white" : "bg-onko-softteal text-onko-teal")
                  }
                >
                  <I size={20} />
                </span>
                <h3 className="mt-4 text-[17px] font-bold">{c.title}</h3>
                <p className="mt-2 text-[13px] leading-5 text-onko-muted">{c.description}</p>
              </button>
            );
          })}
        </div>
      </section>

      <section className="onko-card mt-5 p-5 sm:p-6">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-onko-softteal text-onko-teal">
            <ClipboardList size={19} />
          </span>
          <div>
            <p className="text-[12px] font-bold uppercase tracking-wide text-onko-muted">Selected category</p>
            <h2 className="text-[19px] font-bold">{selected.title}</h2>
          </div>
        </div>

        <textarea
          value={text}
          onChange={e => {
            setText(e.target.value);
            setSent(false);
          }}
          rows={5}
          placeholder={selected.placeholder}
          className="mt-4 w-full rounded-xl border border-onko-line bg-onko-surface p-4 text-[15px] leading-6 outline-none focus:border-onko-teal"
        />

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <p className="max-w-xl text-[12px] leading-5 text-onko-muted">
            {category === "SYMPTOM_CONCERN"
              ? "Your message is sent for human review. OnKo does not determine the cause or severity of a symptom."
              : "Your message will be routed to the appropriate care-team workflow."}
          </p>
          <button onClick={submit} disabled={!text.trim() || busy} className="onko-button-primary disabled:opacity-50">
            <Send size={17} />
            {busy ? "Sending…" : "Send query"}
          </button>
        </div>

        {sent && (
          <div className="mt-4 flex gap-3 rounded-xl bg-onko-softteal p-4 text-[13px] font-semibold text-onko-teal">
            <CheckCircle2 size={18} className="shrink-0" />
            Query recorded for care-team review.
          </div>
        )}
      </section>

      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-[18px] font-bold">Open queries</h2>
          <span className="onko-chip bg-white text-onko-muted">{openQueries.length}</span>
        </div>
        <div className="grid gap-3">
          {openQueries.length ? (
            openQueries.map(q => (
              <article key={q.id} className="onko-card p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[12px] font-bold uppercase tracking-wide text-onko-teal">
                      {choices.find(c => c.id === q.category)?.title}
                    </p>
                    <p className="mt-2 text-[15px] leading-6">{q.text}</p>
                  </div>
                  <span className="onko-chip bg-onko-surface text-onko-muted">{q.status}</span>
                </div>
                {q.response && (
                  <div className="mt-4 rounded-xl bg-onko-softteal p-4 text-[14px] leading-6">
                    <strong>Care-team response:</strong> {q.response}
                  </div>
                )}
              </article>
            ))
          ) : (
            <div className="onko-card p-5 text-[14px] text-onko-muted">No open queries are recorded.</div>
          )}
        </div>
      </section>

      <section className="mt-5">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <h2 className="text-[18px] font-bold">Past queries</h2>
            <p className="mt-1 text-[13px] text-onko-muted">Resolved conversations stay available for your records.</p>
          </div>
          <span className="onko-chip bg-white text-onko-muted">{pastQueries.length}</span>
        </div>

        <div className="grid gap-3">
          {pastQueries.length ? (
            pastQueries.map(q => (
              <article key={q.id} className="onko-card p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-[12px] font-bold uppercase tracking-wide text-onko-teal">
                      {choices.find(c => c.id === q.category)?.title ?? q.category.replaceAll("_", " ")}
                    </p>
                    <p className="mt-1 text-[12px] text-onko-muted">{fmtDate(q.created_at)} · {q.channel}</p>
                  </div>
                  <span className="onko-chip bg-onko-softteal text-onko-teal">Resolved</span>
                </div>

                <div className="mt-4 rounded-xl bg-onko-surface p-4">
                  <p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">Your message</p>
                  <p className="mt-2 text-[14px] leading-6">{q.text}</p>
                </div>

                {q.response ? (
                  <div className="mt-3 rounded-xl bg-onko-softteal p-4">
                    <p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">Care-team response</p>
                    <p className="mt-2 text-[14px] leading-6">{q.response}</p>
                  </div>
                ) : (
                  <p className="mt-3 text-[13px] text-onko-muted">Resolved without a recorded written response.</p>
                )}
              </article>
            ))
          ) : (
            <div className="onko-card p-5 text-[14px] text-onko-muted">No resolved queries yet.</div>
          )}
        </div>
      </section>
    </div>
  );
}
