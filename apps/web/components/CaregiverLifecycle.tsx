"use client";

import { useState } from "react";
import { Link2, ShieldCheck, UserRoundCheck, UserRoundX } from "lucide-react";
import type { Caregiver } from "@/lib/types";
import { api } from "@/lib/api";

export default function CaregiverLifecycle({
  caregiver,
  mode = "patient",
}: {
  caregiver: Caregiver;
  mode?: "patient" | "caregiver";
}) {
  const [state, setState] = useState<Caregiver["consent_status"]>(caregiver.consent_status);
  const [perms, setPerms] = useState(caregiver.permissions);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function moveConsent(action: "revoke" | "reinvite") {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated =
        action === "revoke"
          ? await api.revokeCaregiver(
              caregiver.id,
              { role: "patient", userId: caregiver.patient_id },
            )
          : await api.reinviteCaregiver(caregiver.id, { role: "patient", userId: caregiver.patient_id });
      setState(updated.consent_status);
      setMessage(
        updated.consent_status === "GRANTED"
          ? "Caregiver consent is active."
          : updated.consent_status === "PENDING"
            ? "A new invitation is pending caregiver acceptance."
            : "Caregiver access has been revoked.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update caregiver consent");
    } finally {
      setBusy(false);
    }
  }

  async function savePermissions() {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const updated = await api.updateCaregiverPermissions(
        caregiver.id,
        perms,
        { role: "patient", userId: caregiver.patient_id },
      );
      setPerms(updated.permissions);
      setMessage("Caregiver permissions updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to update caregiver permissions");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-3xl bg-white p-6 shadow-sm sm:p-8">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="onko-eyebrow">Caregiver access</p>
          <h2 className="mt-1 text-[22px] font-bold">Consent & permissions</h2>
          <p className="mt-1 text-[13px] text-onko-muted">
            The patient controls caregiver access and the information shared.
          </p>
        </div>
        <span
          className={
            "rounded-full px-3 py-1.5 text-[12px] font-bold " +
            (state === "GRANTED"
              ? "bg-onko-softteal text-onko-teal"
              : state === "PENDING"
                ? "bg-onko-amberbg text-onko-amber"
                : "bg-red-50 text-onko-sos")
          }
        >
          {state}
        </span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <State icon={<Link2 size={18} />} title="Invited" active={state === "PENDING"} />
        <State icon={<UserRoundCheck size={18} />} title="Consent granted" active={state === "GRANTED"} />
        <State icon={<UserRoundX size={18} />} title="Access revoked" active={state === "REVOKED"} />
      </div>

      <div className="mt-5 flex flex-wrap gap-2">
        {mode === "patient" && state === "GRANTED" && (
          <button disabled={busy} onClick={() => void moveConsent("revoke")} className="onko-button-secondary text-onko-sos disabled:opacity-50">
            Revoke caregiver access
          </button>
        )}
        {mode === "patient" && state === "REVOKED" && (
          <button disabled={busy} onClick={() => void moveConsent("reinvite")} className="onko-button-primary disabled:opacity-50">
            Re-invite caregiver
          </button>
        )}
      </div>

      {mode === "patient" && (
        <div className="mt-6 rounded-2xl bg-onko-surface p-4">
          <div className="flex items-center gap-2">
            <ShieldCheck size={18} className="text-onko-teal" />
            <strong className="text-[14px]">Shared permissions</strong>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-3">
            {([
              ["View journey", "view_journey"],
              ["Upload reports", "upload_reports"],
              ["Receive escalations", "receive_escalations"],
            ] as const).map(([label, key]) => (
              <button
                key={key}
                onClick={() => setPerms({ ...perms, [key]: !perms[key] })}
                className={
                  "rounded-xl border p-3 text-left text-[13px] font-semibold " +
                  (perms[key] ? "border-onko-teal bg-onko-softteal text-onko-teal" : "border-onko-line bg-white")
                }
              >
                {label}
              </button>
            ))}
          </div>
          <button disabled={busy} onClick={() => void savePermissions()} className="onko-button-secondary mt-3 disabled:opacity-50">
            Save permissions
          </button>
        </div>
      )}

      {message && <p className="mt-4 rounded-xl bg-onko-softteal p-3 text-[13px] font-semibold text-onko-teal">{message}</p>}
      {error && <p className="mt-4 rounded-xl bg-red-50 p-3 text-[13px] text-onko-sos">{error}</p>}
    </section>
  );
}

function State({ icon, title, active }: { icon: React.ReactNode; title: string; active: boolean }) {
  return (
    <div className={"rounded-2xl border p-4 " + (active ? "border-onko-teal bg-onko-softteal" : "border-onko-line bg-white")}>
      <span className={active ? "text-onko-teal" : "text-onko-muted"}>{icon}</span>
      <p className="mt-3 text-[13px] font-bold">{title}</p>
    </div>
  );
}
