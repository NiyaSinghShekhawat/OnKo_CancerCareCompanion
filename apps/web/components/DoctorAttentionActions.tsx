"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Clock3, X } from "lucide-react";
import { api } from "@/lib/api";
import type { AttentionStatus } from "@/lib/types";

export default function DoctorAttentionActions({
  attentionId,
  initialStatus,
  assignedTo,
}: {
  attentionId: string;
  initialStatus: AttentionStatus;
  assignedTo: string | null;
}) {
  const router = useRouter();
  const [status, setStatus] = useState<AttentionStatus>(initialStatus);
  const [assignee, setAssignee] = useState(assignedTo || "");
  const [busy, setBusy] = useState<AttentionStatus | "ASSIGN" | null>(null);
  const [error, setError] = useState("");

  async function update(nextStatus: AttentionStatus, nextAssignee: string | null = assignee || null) {
    setBusy(nextStatus);
    setError("");
    try {
      const updated = await api.updateAttention(attentionId, nextStatus, nextAssignee);
      setStatus(updated.status);
      setAssignee(updated.assigned_to || "");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update attention item");
    } finally {
      setBusy(null);
    }
  }

  async function assign(nextAssignee: string) {
    setAssignee(nextAssignee);
    setBusy("ASSIGN");
    setError("");
    try {
      const updated = await api.updateAttention(attentionId, status, nextAssignee || null);
      setAssignee(updated.assigned_to || "");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update assignment");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="mt-4 border-t border-onko-line pt-4">
      <div className="flex flex-wrap items-center gap-2">
        <button
          disabled={!!busy}
          onClick={() => void update("ACKNOWLEDGED")}
          className="onko-button-secondary disabled:opacity-50"
        >
          <CheckCircle2 size={15} />
          {busy === "ACKNOWLEDGED" ? "Acknowledging…" : "Acknowledge"}
        </button>

        <select
          value={assignee}
          disabled={!!busy}
          onChange={e => void assign(e.target.value)}
          className="rounded-lg border border-onko-line bg-white px-3 py-2 text-[13px] disabled:opacity-50"
        >
          <option value="">Unassigned</option>
          <option>Ananya Rao</option>
          <option>Kavya Nair</option>
          <option>Dr. Rajiv Mehta</option>
        </select>

        <button
          disabled={!!busy}
          onClick={() => void update("HANDLED")}
          className="onko-button-secondary disabled:opacity-50"
        >
          <Clock3 size={15} />
          {busy === "HANDLED" ? "Handling…" : "Mark handled"}
        </button>

        <button
          disabled={!!busy}
          onClick={() => void update("CLOSED")}
          className="onko-button-secondary disabled:opacity-50"
        >
          <X size={15} />
          {busy === "CLOSED" ? "Closing…" : "Close"}
        </button>

        <span className="ml-auto rounded-full bg-onko-softteal px-3 py-1.5 text-[11px] font-bold text-onko-teal">
          {status.replaceAll("_", " ")}
        </span>
      </div>

      {error && <p className="mt-2 text-[12px] text-onko-sos">{error}</p>}
      <p className="mt-2 text-[11px] text-onko-muted">
        Handled and closed items leave this active queue but remain available in Patient 360 history.
      </p>
    </div>
  );
}
