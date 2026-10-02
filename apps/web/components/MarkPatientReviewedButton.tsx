"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function MarkPatientReviewedButton({ patientId }: { patientId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function markReviewed() {
    setBusy(true);
    setError("");
    try {
      await api.markPatientReviewed(patientId);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to mark patient reviewed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button onClick={markReviewed} disabled={busy} className="onko-button-secondary disabled:opacity-50">
        <CheckCircle2 size={16} />
        {busy ? "Updating…" : "Mark as reviewed"}
      </button>
      {error && <p className="max-w-xs text-right text-[11px] text-onko-sos">{error}</p>}
    </div>
  );
}
