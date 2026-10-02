"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2 } from "lucide-react";
import { api } from "@/lib/api";

export default function ReportReviewControl({ reportId, reviewed }: { reportId: string; reviewed: boolean }) {
  const router = useRouter();
  const [done, setDone] = useState(reviewed);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function markReviewed() {
    if (done) return;
    setBusy(true);
    setError("");
    try {
      await api.markReportReviewed(reportId);
      setDone(true);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update report");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        onClick={markReviewed}
        disabled={done || busy}
        className={"onko-button-secondary disabled:opacity-70 " + (done ? "text-onko-teal" : "")}
      >
        {done ? (
          <>
            <CheckCircle2 size={15} />
            Reviewed
          </>
        ) : busy ? (
          "Updating…"
        ) : (
          "Mark reviewed"
        )}
      </button>
      {error && <p className="max-w-xs text-right text-[11px] text-onko-sos">{error}</p>}
    </div>
  );
}
