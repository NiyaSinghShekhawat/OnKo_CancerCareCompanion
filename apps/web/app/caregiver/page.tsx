import Link from "next/link";
import { AlertCircle, CalendarClock, CheckCircle2, Pill, Route, ShieldCheck } from "lucide-react";
import CaregiverShell from "@/components/CaregiverShell";
import CaregiverEventCard from "@/components/CaregiverEventCard";
import { serverApi } from "@/lib/server-api";
import {currentCaregiverId} from "@/lib/caregiver-session";

export const dynamic = "force-dynamic";
export default async function CaregiverHome() {
  const caregiverId=currentCaregiverId();
  const view = await serverApi.caregiverView(caregiverId);
  const CAREGIVER = { id: view.caregiver.id, name: view.caregiver.name, relation: view.caregiver.relation };
  return (
    <CaregiverShell patient={view.patient} caregiver={CAREGIVER}>
      <div className="mx-auto max-w-5xl space-y-6">
        <section className="rounded-3xl bg-white p-5 shadow-sm sm:p-7">
          <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-start">
            <div>
              <p className="onko-eyebrow">Caregiver overview</p>
              <h1 className="mt-1 text-[28px] font-bold tracking-tight sm:text-[36px]">Supporting {view.patient.name}</h1>
              <p className="mt-2 max-w-2xl text-[14px] leading-6 text-onko-muted">
                This is the consent-limited caregiver view. Clinical reports, diagnoses, queries and attention details are not exposed here.
              </p>
            </div>
            <Link href="/caregiver/access" className="onko-button-secondary shrink-0"><ShieldCheck size={17}/>View access</Link>
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            <span className="rounded-full bg-onko-softteal px-3 py-1.5 text-[12px] font-semibold text-onko-teal">Consent active</span>
            <span className="rounded-full bg-onko-surface px-3 py-1.5 text-[12px] font-semibold text-onko-muted">{CAREGIVER.relation}</span>
            <span className="rounded-full bg-onko-surface px-3 py-1.5 text-[12px] font-semibold capitalize text-onko-muted">{view.patient.journey_state.replaceAll("_"," ").toLowerCase()}</span>
          </div>
        </section>

        <section className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-white p-5 shadow-sm"><Route className="text-onko-teal" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">UPCOMING</p><p className="mt-1 text-[28px] font-bold">{view.upcoming.length}</p></div>
          <div className="rounded-2xl bg-white p-5 shadow-sm"><AlertCircle className="text-onko-amber" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">RECENT UPDATES</p><p className="mt-1 text-[28px] font-bold">{view.recent.length}</p></div>
          <div className="rounded-2xl bg-white p-5 shadow-sm"><CheckCircle2 className="text-onko-teal" size={20}/><p className="mt-4 text-[12px] font-semibold text-onko-muted">REPORT UPLOAD</p><p className="mt-1 text-[16px] font-bold">{view.can_upload_reports?"Allowed":"Not shared"}</p></div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.35fr_.65fr]">
          <div>
            <div className="mb-3 flex items-center justify-between"><h2 className="text-[20px] font-bold">Coming up</h2><Link href="/caregiver/journey" className="text-[13px] font-semibold text-onko-teal">View journey →</Link></div>
            <div className="grid gap-3">{view.upcoming.slice(0,3).map(e=><CaregiverEventCard key={e.id} event={e}/>)}</div>
          </div>
          <aside className="grid content-start gap-3">
            <Link href="/caregiver/medications" className="block rounded-3xl bg-white p-5 shadow-sm"><Pill className="text-onko-teal"/><h3 className="mt-4 text-[17px] font-bold">Medication activity</h3><p className="mt-1 text-[13px] leading-5 text-onko-muted">See only the minimized medication schedule shared with you.</p></Link>
            <Link href="/caregiver/records" className="block rounded-3xl bg-white p-5 shadow-sm"><CalendarClock className="text-onko-teal"/><h3 className="mt-4 text-[17px] font-bold">Report upload</h3><p className="mt-1 text-[13px] leading-5 text-onko-muted">{view.can_upload_reports?"You may upload a report on the patient's behalf.":"Report upload is not included in current consent."}</p></Link>
          </aside>
        </section>

        <p className="px-2 text-center text-[12px] leading-5 text-onko-muted">Caregiver access uses the minimized caregiver endpoint; no report values, diagnosis details, queries or internal attention items are returned.</p>
      </div>
    </CaregiverShell>
  );
}
