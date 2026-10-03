import {CalendarDays,ChevronRight,ClipboardList,PauseCircle,Target} from "lucide-react";
import Link from "next/link";
import PatientShell from "@/components/PatientShell";
import PatientEventCard from "@/components/PatientEventCard";
import CareJourneyCalendar from "@/components/CareJourneyCalendar";
import {serverApi} from "@/lib/server-api";
import {fmtDate} from "@/lib/format";
import {currentPatientId} from "@/lib/patient-session";
export const dynamic="force-dynamic";
const DEMO_PATIENTS=new Set(["p_rajesh","p_priya","p_arjun","p_lakshmi","p_meera","p_vikram","p_farhan","p_kamala"]);
export default async function PatientHome({searchParams}:{searchParams?:{id?:string}}){
 const patientId=currentPatientId(searchParams);
 const actor={role:"patient" as const,userId:patientId}; const [d,checklist]=await Promise.all([serverApi.patient360(patientId,actor),serverApi.checklistToday(patientId,actor)]);const p=d.patient;
 const future=d.timeline.filter(e=>new Date(e.scheduled_at)>new Date(checklist.date+"T23:59:59")).slice(0,3);
 const completed=d.timeline.filter(e=>e.status==="COMPLETED").length,missed=d.timeline.filter(e=>e.status==="REPORTED_MISSED"||e.status==="NO_RESPONSE").length,pending=d.timeline.filter(e=>e.status==="UPCOMING"||e.status==="CURRENT").length;
 const resolvedQueries = (d.query_history ?? [])
  .filter(q => q.status === "RESOLVED")
  .slice(0, 3);
 return <PatientShell patient={p}><div className="mx-auto w-full max-w-[1320px]">
  <section className="flex flex-wrap items-center justify-between gap-4"><div><p className="onko-eyebrow">{fmtDate(checklist.date)}</p><h1 className="mt-1 text-[30px] font-bold tracking-tight sm:text-[38px]">Good to see you, {p.name.split(" ")[0]}</h1><p className="mt-2 text-[15px] text-onko-muted">Here is what is recorded for your care today.</p></div></section>
  {d.caregivers.length>0&&<div className="mt-5 rounded-2xl bg-onko-softteal px-4 py-3 text-[14px] text-onko-muted"><strong className="text-onko-ink">{d.caregivers[0].name}</strong> is linked as your {d.caregivers[0].relation.toLowerCase()} caregiver.</div>}
  {checklist.paused?<section className="onko-card mt-5 border-onko-amber/30 bg-onko-amberbg p-5 sm:p-6"><div className="flex items-start gap-3"><PauseCircle className="mt-0.5 shrink-0 text-onko-amber" size={22}/><div><p className="onko-eyebrow">Daily checklist paused</p><h2 className="mt-1 text-[20px] font-bold">{p.journey_state==="TRANSFER_OF_CARE"?"Care is currently being transferred":p.journey_state==="DECEASED"?"Daily care messaging is paused":"Checklist temporarily paused"}</h2><p className="mt-2 text-[14px] leading-6 text-onko-muted">{p.journey_state==="TRANSFER_OF_CARE"?"OnKo has paused daily checklist prompts during transfer of care. Recorded history remains available.":p.journey_state==="DECEASED"?"No further daily checklist prompts are sent for this journey state. Historical records remain available to authorized users.":checklist.reason||"The daily checklist is not active for the current journey state."}</p></div></div></section>:<section className="onko-card mt-5 p-4 sm:p-6 lg:p-7"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="onko-eyebrow">Today</p><h2 className="mt-1 text-[22px] font-bold">Your next steps</h2></div><span className="onko-chip bg-onko-softteal text-onko-teal">{checklist.items.length} recorded items</span></div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{checklist.items.map(e=><PatientEventCard key={e.id} event={e} interactive/>)}</div><p className="mt-4 text-[12px] text-onko-muted">Daily response window closes {fmtDate(checklist.window_closes_at)}. A non-response is recorded as no response, not as a confirmed missed medicine.</p></section>}
  <section className="mt-5"><div className="mb-3 flex items-center justify-between"><h2 className="text-[20px] font-bold">Journey overview</h2><Link href="/patient/care" className="text-[13px] font-semibold text-onko-teal">See care activities</Link></div><div className="grid grid-cols-1 gap-3 sm:grid-cols-3"><div className="onko-card p-4"><p className="text-[12px] text-onko-muted">Completed</p><p className="mt-1 text-[25px] font-bold text-onko-teal">{completed}</p></div><div className="onko-card p-4"><p className="text-[12px] text-onko-muted">Upcoming</p><p className="mt-1 text-[25px] font-bold">{pending}</p></div><div className="onko-card p-4"><p className="text-[12px] text-onko-muted">Needs follow-up</p><p className="mt-1 text-[25px] font-bold text-onko-amber">{missed}</p></div></div></section>
  {resolvedQueries.length > 0 && (
  <section className="onko-card mt-5 p-5 sm:p-6">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="onko-eyebrow">Query history</p>
        <h2 className="mt-1 text-[20px] font-bold">
          Recent care-team responses
        </h2>
      </div>

      <Link
        href="/patient/queries"
        className="text-[13px] font-semibold text-onko-teal"
      >
        View all queries
      </Link>
    </div>

    <div className="mt-4 grid gap-3">
      {resolvedQueries.map(q => (
        <article
          key={q.id}
          className="rounded-xl bg-onko-surface p-4"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[12px] font-bold uppercase tracking-wide text-onko-teal">
                {q.category.replaceAll("_", " ")}
              </p>

              <p className="mt-2 text-[14px] leading-6">
                {q.text}
              </p>
            </div>

            <span className="onko-chip bg-onko-softteal text-onko-teal">
              Resolved
            </span>
          </div>

          {q.response && (
            <div className="mt-3 rounded-xl bg-white p-3 text-[14px] leading-6">
              <strong>Care-team response:</strong> {q.response}
            </div>
          )}

          <p className="mt-2 text-[12px] text-onko-muted">
            {fmtDate(q.created_at)}
          </p>
        </article>
      ))}
    </div>
  </section>
)}
{resolvedQueries.length > 0 && (
  <section className="onko-card mt-5 p-5 sm:p-6">
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="onko-eyebrow">Query history</p>
        <h2 className="mt-1 text-[20px] font-bold">
          Recent care-team responses
        </h2>
      </div>

      <Link
        href="/patient/queries"
        className="text-[13px] font-semibold text-onko-teal"
      >
        View all queries
      </Link>
    </div>

    <div className="mt-4 grid gap-3">
      {resolvedQueries.map(q => (
        <article key={q.id} className="rounded-xl bg-onko-surface p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-[12px] font-bold uppercase tracking-wide text-onko-teal">
                {q.category.replaceAll("_", " ")}
              </p>

              <p className="mt-2 text-[14px] leading-6">
                {q.text}
              </p>
            </div>

            <span className="onko-chip bg-onko-softteal text-onko-teal">
              Resolved
            </span>
          </div>

          {q.response && (
            <div className="mt-3 rounded-xl bg-white p-3 text-[14px] leading-6">
              <strong>Care-team response:</strong> {q.response}
            </div>
          )}

          <p className="mt-2 text-[12px] text-onko-muted">
            {fmtDate(q.created_at)}
          </p>
        </article>
      ))}
    </div>
  </section>
)}
  <div className="mt-5 grid gap-5 lg:grid-cols-[1.35fr_.65fr]"><section><div className="mb-3 flex items-center justify-between"><h2 className="text-[20px] font-bold">Up next in your journey</h2><Link href="/patient/journey" className="text-[13px] font-semibold text-onko-teal">Full journey</Link></div><div className="grid gap-2">{future.length?future.map(e=><Link key={e.id} href="/patient/journey" className="onko-card flex items-center gap-3 p-4 hover:bg-onko-hover"><div className="grid h-11 w-11 place-items-center rounded-xl bg-onko-softteal text-onko-teal"><CalendarDays size={19}/></div><div className="min-w-0 flex-1"><strong className="text-[15px]">{e.title}</strong><p className="text-[13px] text-onko-muted">{fmtDate(e.scheduled_at)}</p></div><ChevronRight size={18} className="text-onko-muted"/></Link>):<p className="onko-card p-4 text-[14px] text-onko-muted">No later items are recorded.</p>}</div></section>
  <aside className="grid content-start gap-3"><Link href="/patient/records" className="onko-card p-5 hover:bg-onko-hover"><ClipboardList size={20} className="text-onko-teal"/><h3 className="mt-3 text-[17px] font-bold">Your records</h3><p className="mt-1 text-[14px] text-onko-muted">{d.reports.length} report{d.reports.length===1?"":"s"} available</p></Link><Link href="/patient/care#milestones" className="onko-card p-5 hover:bg-onko-hover"><Target size={20} className="text-onko-teal"/><h3 className="mt-3 text-[17px] font-bold">Milestones & activities</h3><p className="mt-1 text-[14px] text-onko-muted">Appointments, tests, treatments and milestones</p></Link></aside></div>
 </div></PatientShell>
}