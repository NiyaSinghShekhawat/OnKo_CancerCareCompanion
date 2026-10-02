"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Clock3, X } from "lucide-react";
import { api } from "@/lib/api";
import type { AttentionStatus, Role } from "@/lib/types";

const assignees = [
  { id: "doc_mehta", label: "Dr. Mehta" },
  { id: "nurse_anita", label: "Nurse Anita" },
];

export default function DoctorAttentionActions({
  attentionId,
  initialStatus,
  assignedTo,
  actorRole = "doctor",
  actorId = "doc_mehta",
}: {
  attentionId: string;
  initialStatus: AttentionStatus;
  assignedTo: string | null;
  actorRole?: Role;
  actorId?: string;
}) {
  const router = useRouter();
  const [status, setStatus] = useState<AttentionStatus>(initialStatus);
  const [assignee, setAssignee] = useState(assignedTo ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const actor = { role: actorRole, userId: actorId };

  async function updateStatus(next: AttentionStatus) {
    setBusy(true);
    setError("");
    try {
      const updated = await api.updateAttention(attentionId, { status: next }, actor);
      setStatus(updated.status);
      setAssignee(updated.assigned_to ?? "");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update attention item");
    } finally {
      setBusy(false);
    }
  }

  async function assign(next: string) {
    if (!next) return;
    setBusy(true);
    setError("");
    try {
      const updated = await api.updateAttention(attentionId, { assigned_to: next }, actor);
      setAssignee(updated.assigned_to ?? "");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to assign attention item");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-4 border-t border-onko-line pt-4">
      <div className="flex flex-wrap items-center gap-2">
        <button disabled={busy} onClick={() => void updateStatus("ACKNOWLEDGED")} className="onko-button-secondary disabled:opacity-50">
          <CheckCircle2 size={15}/>Acknowledge
        </button>
        <select
          value={assignee}
          disabled={busy}
          onChange={e => void assign(e.target.value)}
          className="rounded-lg border border-onko-line bg-white px-3 py-2 text-[13px] disabled:opacity-50"
        >
          <option value="">Assign reviewer</option>
          {assignees.map(a=><option key={a.id} value={a.id}>{a.label}</option>)}
        </select>
        <button disabled={busy} onClick={() => void updateStatus("HANDLED")} className="onko-button-secondary disabled:opacity-50">
          <Clock3 size={15}/>Mark handled
        </button>
        <button disabled={busy} onClick={() => void updateStatus("CLOSED")} className="onko-button-secondary disabled:opacity-50">
          <X size={15}/>Close
        </button>
        <span className="ml-auto rounded-full bg-onko-softteal px-3 py-1.5 text-[11px] font-bold text-onko-teal">{status.replaceAll("_"," ")}</span>
      </div>
      {error&&<p className="mt-2 text-[12px] text-onko-sos">{error}</p>}
    </div>
  );
}
