import CaregiverShell from "@/components/CaregiverShell";
import ReportUploadPrototype from "@/components/ReportUploadPrototype";
import { serverApi } from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic = "force-dynamic";
export default async function CaregiverRecords() {
  const caregiverId=currentCaregiverId();
  const view = await serverApi.caregiverView(caregiverId);
  const CAREGIVER = { id: view.caregiver.id, name: view.caregiver.name, relation: view.caregiver.relation };
  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-4xl">
        <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
          <div>
            <p className="onko-eyebrow">Caregiver records</p>
            <h1 className="mt-1 text-[30px] font-bold sm:text-[38px]">Report upload</h1>
            <p className="mt-2 text-[14px] leading-6 text-onko-muted">The caregiver role may upload when consent allows it, but does not browse the patient&apos;s report list or extracted clinical values.</p>
          </div>
          {view.can_upload_reports&&<ReportUploadPrototype/>}
        </div>
        <section className="mt-7 rounded-3xl bg-white p-6 shadow-sm">
          <h2 className="text-[20px] font-bold">{view.can_upload_reports?"Upload permission active":"Upload permission not shared"}</h2>
          <p className="mt-2 text-[14px] leading-6 text-onko-muted">{view.can_upload_reports?"Current consent allows this caregiver to add a report on the patient's behalf. Existing reports remain private from the caregiver endpoint.":"The patient has not granted report-upload permission to this caregiver."}</p>
        </section>
      </div>
    </CaregiverShell>
  );
}
