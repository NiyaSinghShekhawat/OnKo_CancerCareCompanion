"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Send, UserRoundCheck } from "lucide-react";
import { api } from "@/lib/api";

export default function DoctorQueryActions({
  queryId,
  initialStatus = "OPEN",
}: {
  queryId: string;
  initialStatus?: string;
}) {
  const router = useRouter();
  const [response, setResponse] = useState("");
  const [status, setStatus] = useState(initialStatus);
  const [assignee, setAssignee] = useState("");
  const [busy, setBusy] = useState<"resolve" | "send" | "escalate" | null>(null);
  const [error, setError] = useState("");

  async function update(nextStatus: string, responseText?: string, action?: typeof busy) {
    setBusy(action ?? "resolve");
    setError("");
    try {
      await api.updateQuery(queryId, nextStatus, responseText);
      setStatus(nextStatus);
      if (responseText) setResponse("");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update query");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mt-4 rounded-xl border border-onko-line bg-white p-4">
      <div className="flex flex-wrap gap-2">
        <select
          value={assignee}
          onChange={e => setAssignee(e.target.value)}
          className="rounded-lg border border-onko-line px-3 py-2 text-[13px]"
        >
          <option value="">Assign reviewer</option>
          <option>Ananya Rao</option>
          <option>Kavya Nair</option>
          <option>Dr. Rajiv Mehta</option>
        </select>

        <button
          disabled={!!busy}
          onClick={() => void update("ESCALATED", undefined, "escalate")}
          className="onko-button-secondary disabled:opacity-50"
        >
          <UserRoundCheck size={15} />
          {busy === "escalate" ? "Escalating…" : "Escalate to doctor"}
        </button>

        <button
          disabled={!!busy}
          onClick={() => void update("RESOLVED", undefined, "resolve")}
          className="onko-button-secondary disabled:opacity-50"
        >
          <CheckCircle2 size={15} />
          {busy === "resolve" ? "Resolving…" : "Resolve"}
        </button>

        <span className="ml-auto onko-chip bg-onko-softteal text-onko-teal">{status}</span>
      </div>

      <textarea
        value={response}
        onChange={e => setResponse(e.target.value)}
        rows={3}
        placeholder="Write the care-team response…"
        className="mt-3 w-full rounded-xl border border-onko-line bg-onko-surface p-3 text-[14px] outline-none focus:border-onko-teal"
      />

      <div className="mt-2 flex justify-end">
        <button
          disabled={!response.trim() || !!busy}
          onClick={() => void update("RESOLVED", response.trim(), "send")}
          className="onko-button-primary disabled:opacity-50"
        >
          <Send size={15} />
          {busy === "send" ? "Sending…" : "Send response & resolve"}
        </button>
      </div>

      {error && <p className="mt-2 text-[12px] text-onko-sos">{error}</p>}
      <p className="mt-2 text-[11px] text-onko-muted">
        Responses are clinician-authored. Resolved queries leave this active queue and remain in patient history.
      </p>
    </div>
  );
}
