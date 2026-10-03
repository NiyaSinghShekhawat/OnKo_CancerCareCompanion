import CaregiverShell from "@/components/CaregiverShell";
import CaregiverLifecycle from "@/components/CaregiverLifecycle";
import { CheckCircle2, LockKeyhole, ShieldCheck } from "lucide-react";
import { serverApi } from "@/lib/server-api";
import type { Caregiver } from "@/lib/types";

export const dynamic = "force-dynamic";
const CAREGIVER = { id: "cg_sunita", name: "Sunita Kumar", relation: "Wife" };

export default async function CaregiverAccess() {
  const view = await serverApi.caregiverView(CAREGIVER.id);
  const caregiver: Caregiver = {
    id: CAREGIVER.id,
    patient_id: view.patient.id,
    name: CAREGIVER.name,
    relation: CAREGIVER.relation,
    phone_whatsapp: "",
    type: "family",
    consent_status: "GRANTED",
    permissions: {
      view_journey: true,
      upload_reports: view.can_upload_reports,
      receive_escalations: view.receives_escalations,
    },
  };

  const scopes = [
    ["View care journey", true, "Minimized upcoming and recent care activities"],
    ["Upload reports", view.can_upload_reports, "Add reports on the patient's behalf"],
    ["Receive escalations", view.receives_escalations, "Receive caregiver-directed escalation notifications"],
  ] as const;

  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-4xl space-y-6">
        <section className="rounded-3xl bg-white p-6 shadow-sm sm:p-8">
          <div className="flex items-start gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-onko-softteal text-onko-teal"><ShieldCheck/></span>
            <div>
              <p className="onko-eyebrow">Access & consent</p>
              <h1 className="mt-1 text-[28px] font-bold sm:text-[36px]">{CAREGIVER.name}</h1>
              <p className="mt-1 text-[14px] text-onko-muted">{CAREGIVER.relation} · caregiver</p>
            </div>
          </div>
          <div className="mt-6 rounded-2xl bg-onko-surface p-4">
            <p className="text-[12px] font-semibold text-onko-muted">PATIENT CONSENT</p>
            <p className="mt-1 text-[17px] font-bold text-onko-teal">GRANTED</p>
          </div>
        </section>

        <section className="rounded-3xl bg-white p-6 shadow-sm sm:p-8">
          <h2 className="text-[21px] font-bold">What is shared</h2>
          <p className="mt-1 text-[13px] leading-5 text-onko-muted">The caregiver endpoint exposes only consented coordination information.</p>
          <div className="mt-5 space-y-3">{scopes.map(([name,on,desc])=><div key={name} className="flex items-start gap-3 rounded-2xl bg-onko-surface p-4"><CheckCircle2 className={"mt-0.5 shrink-0 "+(on?"text-onko-teal":"text-onko-muted")} size={20}/><div><strong className="text-[15px]">{name}</strong><p className="mt-1 text-[12px] leading-5 text-onko-muted">{desc}</p></div></div>)}</div>
        </section>

        <CaregiverLifecycle caregiver={caregiver} mode="caregiver"/>

        <section className="flex items-start gap-3 rounded-2xl border border-[#D7EEEA] bg-[#F4FCFA] p-5">
          <LockKeyhole className="mt-0.5 shrink-0 text-onko-teal" size={20}/>
          <div><h2 className="text-[15px] font-bold">Consent-enforced access</h2><p className="mt-1 text-[13px] leading-5 text-onko-muted">Revoking access takes effect immediately. A revoked caregiver must be re-invited by the patient before accepting again.</p></div>
        </section>
      </div>
    </CaregiverShell>
  );
}
