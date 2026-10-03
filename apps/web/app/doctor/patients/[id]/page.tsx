import Link from "next/link";
import { ClipboardList, FileText, MessageSquareText, UserRound, Users } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import JourneyStateControl from "@/components/JourneyStateControl";
import CareJourneyCalendar from "@/components/CareJourneyCalendar";
import MarkPatientReviewedButton from "@/components/MarkPatientReviewedButton";
import ReportReviewControl from "@/components/ReportReviewControl";
import { serverApi } from "@/lib/server-api";
import { fmtDate } from "@/lib/format";
export const dynamic="force-dynamic";
const tabs=[
 ["Overview","overview"],["Care Journey","care-journey"],["Care Plan","care-plan"],["Medications","medications"],["Treatments","treatments"],["Investigations","investigations"],["Reports","reports"],["Appointments","appointments"],["Milestones","milestones"],["Engagement","engagement"],["Attention History","attention-history"],["Queries","queries"],["Caregiver & Consent","caregiver-consent"]
] as const;
export default async function Patient360Page({params}:{params:{id:string}}){
 const d=await serverApi.patient360(params.id),p=d.patient;
 const byType=(type:string)=>d.timeline.filter(e=>e.type===type);
 const appointments=byType("APPOINTMENT"),treatments=byType("TREATMENT"),investigations=byType("INVESTIGATION"),milestones=byType("MILESTONE");
 const engagement=d.timeline.filter(e=>e.response_state||["REPORTED_MISSED","NO_RESPONSE","CONFLICTING","COMPLETED"].includes(e.status)); const pending=d.timeline.filter(e=>["UPCOMING","CURRENT","NO_RESPONSE","REPORTED_MISSED","CONFLICTING"].includes(e.status)); const upcoming=d.timeline.filter(e=>["UPCOMING","CURRENT"].includes(e.status)).slice(0,3); 
 const activeAttention=d.attention.filter(a=>a.status==="PENDING"||a.status==="ACKNOWLEDGED");
 const queryHistory = d.query_history ?? d.open_queries;
 return <DoctorShell>

  <section className="onko-card overflow-hidden"><div className="flex flex-wrap items-start justify-between gap-5 p-6"><div className="flex gap-4"><div className="grid h-16 w-16 place-items-center rounded-full bg-onko-softteal text-onko-teal"><UserRound size={30}/></div><div><div className="flex flex-wrap items-center gap-2"><h1 className="text-[30px] font-bold tracking-tight sm:text-[34px]">{p.name}</h1><span className="onko-chip bg-onko-teal text-white">{p.journey_state.replaceAll("_"," ").toLowerCase()}</span></div><p className="mt-1 text-[15px] text-onko-muted">{p.age} yrs · {p.gender} · {p.diagnosis_label}</p><p className="mt-2 text-[15px] font-semibold">{p.regimen_label} · Cycle {p.cycle_current} of {p.cycle_total}</p></div></div><Link href={"/doctor/careplan/"+p.id} className="onko-button-primary"><ClipboardList size={16}/>Edit Care Plan</Link></div>
   <nav className="flex gap-1 overflow-x-auto border-t border-onko-line px-5 py-2 text-[14px] font-semibold">{tabs.map(([label,id],i)=><a key={id} href={"#"+id} className={"whitespace-nowrap rounded-lg px-3 py-2 "+(i===0?"bg-onko-teal text-white":"text-onko-muted hover:bg-onko-softteal")}>{label}</a>)}</nav>
  </section>
  <section id="overview" className="mt-5 grid gap-5 xl:grid-cols-[1.35fr_.65fr]"><div className="grid gap-5"><div className="onko-card p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><p className="onko-eyebrow">Since your last review</p><h2 className="mt-1 text-[24px] font-bold">Recorded changes</h2></div><MarkPatientReviewedButton patientId={p.id}/></div><div className="mt-4 grid gap-2">{d.since_last_review.bullets.length?d.since_last_review.bullets.map(b=><div key={b} className="rounded-xl bg-onko-softteal/60 px-4 py-3 text-[15px]">{b}</div>):<p className="rounded-xl bg-onko-surface px-4 py-3 text-[14px] text-onko-muted">No new recorded changes since the last review.</p>}</div></div><section id="care-journey" className="onko-card scroll-mt-24 p-5"><CareJourneyCalendar events={d.timeline} title="Care Journey Calendar"/></section></div>
   <aside className="grid content-start gap-4"><div className="onko-card p-5"><p className="onko-eyebrow">Pre-consultation brief</p><h2 className="mt-1 text-[20px] font-bold">Review before consultation</h2><div className="mt-4 grid grid-cols-2 gap-2"><Brief label="Changes" value={d.since_last_review.bullets.length}/><Brief label="Open queries" value={d.open_queries.length}/><Brief label="New reports" value={d.reports.filter(r=>!r.reviewed).length}/><Brief label="Pending activities" value={pending.length}/></div><div className="mt-4 rounded-xl bg-onko-surface p-4"><p className="text-[11px] font-bold uppercase text-onko-muted">Upcoming</p>{upcoming.length?upcoming.map(e=><p key={e.id} className="mt-2 text-[13px]"><strong>{e.title}</strong> · {fmtDate(e.scheduled_at)}</p>):<p className="mt-2 text-[13px] text-onko-muted">No upcoming recorded activity.</p>}</div><div className="mt-3 rounded-xl border border-onko-line p-4"><p className="text-[11px] font-bold uppercase text-onko-muted">Unresolved attention</p>{activeAttention.length?activeAttention.slice(0,3).map(a=><p key={a.id} className="mt-2 text-[13px]">{a.label.replaceAll("_"," ")} · {a.reasons.join("; ")}</p>):<p className="mt-2 text-[13px] text-onko-muted">No open attention items.</p>}</div><p className="mt-3 text-[12px] leading-5 text-onko-muted">Compiled from recorded activity only. No diagnosis, risk score or clinical interpretation is generated.</p></div><div className="grid grid-cols-3 gap-2"><div className="onko-card p-4"><FileText size={17} className="text-onko-teal"/><p className="mt-2 text-[30px] font-bold">{d.reports.length}</p><p className="text-[13px] text-onko-muted">Reports</p></div><div className="onko-card p-4"><MessageSquareText size={17} className="text-onko-teal"/><p className="mt-2 text-[30px] font-bold">{d.open_queries.length}</p><p className="text-[13px] text-onko-muted">Queries</p></div><div className="onko-card p-4"><Users size={17} className="text-onko-teal"/><p className="mt-2 text-[30px] font-bold">{d.caregivers.length}</p><p className="text-[13px] text-onko-muted">Caregivers</p></div></div></aside></section>
  <section id="care-plan" className="onko-card mt-5 scroll-mt-24 p-5"><div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="text-[24px] font-bold">Approved Care Plan</h2><p className="mt-1 text-[14px] text-onko-muted">Clinician-approved care-plan items recorded for this patient.</p></div><Link href={"/doctor/careplan/"+p.id} className="onko-button-secondary">Open Care Plan</Link></div><div className="mt-4 grid gap-3 md:grid-cols-2">{d.care_plan.length?d.care_plan.map(x=><div key={x.id} className="rounded-xl bg-onko-surface p-4"><div className="flex justify-between gap-3"><strong>{x.title}</strong><span className="onko-chip bg-white text-onko-muted">{x.type.toLowerCase()}</span></div><p className="mt-2 text-[13px] text-onko-muted">{fmtDate(x.start_date)}{x.end_date?" → "+fmtDate(x.end_date):""}</p></div>):<Empty/>}</div></section><div className="mt-5 grid gap-5 xl:grid-cols-2">
   <section id="engagement" className="onko-card scroll-mt-24 p-5 xl:col-span-2"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-[20px] font-bold">Engagement & Response History</h2><p className="mt-1 text-[13px] text-onko-muted">Observable response states from patient interactions. No-response is not treated as a confirmed missed medication.</p></div><span className="onko-chip bg-onko-softteal text-onko-teal">{engagement.length} recorded responses</span></div><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{engagement.length?engagement.map(e=><div key={e.id} className="rounded-xl bg-onko-surface p-4"><div className="flex items-start justify-between gap-3"><strong className="text-[14px]">{e.title}</strong><span className={"rounded-full px-2 py-1 text-[11px] font-semibold "+(e.status==="CONFLICTING"?"bg-red-50 text-onko-sos":e.status==="NO_RESPONSE"||e.status==="REPORTED_MISSED"?"bg-onko-amberbg text-onko-amber":"bg-white text-onko-muted")}>{(e.response_state||e.status).replaceAll("_"," ").toLowerCase()}</span></div><p className="mt-2 text-[12px] text-onko-muted">{fmtDate(e.scheduled_at)} · {e.type.toLowerCase()}</p>{e.responded_at&&<p className="mt-1 text-[12px] text-onko-muted">Responded: {fmtDate(e.responded_at)}</p>}</div>):<Empty/>}</div></section><MedicationCourses items={d.care_plan.filter(x=>x.type==="MEDICATION")} events={byType("MEDICATION")}/><EventSection id="treatments" title="Treatments" items={treatments}/><EventSection id="investigations" title="Investigations" items={investigations}/><EventSection id="appointments" title="Appointments" items={appointments}/><EventSection id="milestones" title="Milestones" items={milestones}/>
   <section id="reports" className="onko-card scroll-mt-24 p-5"><h2 className="text-[20px] font-bold">Reports</h2><div className="mt-3 grid gap-3">{d.reports.length?d.reports.map(r=><div key={r.id} className="rounded-xl bg-onko-surface p-4 text-[15px]"><div className="flex flex-wrap items-start justify-between gap-2"><div><strong>{r.title}</strong><p className="mt-1 text-[13px] text-onko-muted">{fmtDate(r.uploaded_at)}</p></div><ReportReviewControl reportId={r.id} reviewed={r.reviewed}/></div>{r.extracted_values.map(v=><p key={v.name} className="mt-2 text-onko-muted">{v.name}: {v.value} {v.unit}</p>)}</div>):<Empty/>}</div></section>
   <section id="attention-history" className="onko-card scroll-mt-24 p-5 xl:col-span-2"><div className="flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-[20px] font-bold">Attention History</h2><p className="mt-1 text-[13px] text-onko-muted">Workflow items remain recorded after they are handled or closed.</p></div><span className="onko-chip bg-onko-softteal text-onko-teal">{activeAttention.length} active</span></div><div className="mt-4 grid gap-3 md:grid-cols-2">{d.attention.length?d.attention.map(a=><article key={a.id} className="rounded-xl bg-onko-surface p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-[12px] font-bold uppercase tracking-wide text-onko-muted">{a.label.replaceAll("_"," ")}</p><p className="mt-1 text-[12px] text-onko-muted">{fmtDate(a.created_at)}{a.assigned_to?" · "+a.assigned_to:""}</p></div><span className={"onko-chip "+(a.status==="PENDING"||a.status==="ACKNOWLEDGED"?"bg-onko-amberbg text-onko-amber":"bg-onko-softteal text-onko-teal")}>{a.status.toLowerCase()}</span></div><ul className="mt-3 grid gap-1.5 text-[13px] leading-5 text-onko-muted">{a.reasons.map(r=><li key={r}>• {r}</li>)}</ul></article>):<Empty/>}</div></section>
   {/* <section id="queries" className="onko-card scroll-mt-24 p-5"><h2 className="text-[20px] font-bold">Open Queries</h2><div className="mt-3 grid gap-3">{d.open_queries.length?d.open_queries.map(q=><div key={q.id} className="rounded-xl bg-onko-surface p-4"><p className="text-[12px] font-semibold uppercase text-onko-muted">{q.category.replaceAll("_"," ").toLowerCase()} · {q.channel}</p><p className="mt-2 text-[15px]">{q.summary}</p><p className="mt-2 text-[12px] text-onko-muted">Status: {q.status}</p></div>):<Empty/>}</div></section> */}
   <section id="queries" className="onko-card scroll-mt-24 p-5">
  <div className="flex flex-wrap items-end justify-between gap-3">
    <div>
      <h2 className="text-[20px] font-bold">
        Query History
      </h2>

      <p className="mt-1 text-[13px] text-onko-muted">
        Open and resolved patient conversations, including the recorded
        care-team response.
      </p>
    </div>

    <span className="onko-chip bg-onko-softteal text-onko-teal">
      {d.open_queries.length} open
    </span>
  </div>

  <div className="mt-3 grid gap-3">
    {queryHistory.length ? (
      queryHistory.map(q => (
        <div
          key={q.id}
          className="rounded-xl bg-onko-surface p-4"
        >
          <div className="flex flex-wrap items-start justify-between gap-2">
            <p className="text-[12px] font-semibold uppercase text-onko-muted">
              {q.category.replaceAll("_", " ").toLowerCase()} · {q.channel}
            </p>

            <span
              className={
                "onko-chip " +
                (q.status === "RESOLVED"
                  ? "bg-onko-softteal text-onko-teal"
                  : "bg-white text-onko-muted")
              }
            >
              {q.status.toLowerCase()}
            </span>
          </div>

          <div className="mt-3 rounded-lg bg-white p-3">
            <p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">
              Patient message
            </p>

            <p className="mt-1 text-[14px] leading-6">
              {q.text}
            </p>
          </div>

          <div className="mt-3">
            <p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">
              Organized summary
            </p>

            <p className="mt-1 text-[14px] leading-6">
              {q.summary}
            </p>
          </div>

          {q.response && (
            <div className="mt-3 rounded-lg bg-onko-softteal/70 p-3">
              <p className="text-[11px] font-bold uppercase tracking-wide text-onko-muted">
                Care-team response
              </p>

              <p className="mt-1 text-[14px] leading-6">
                {q.response}
              </p>
            </div>
          )}

          <p className="mt-3 text-[12px] text-onko-muted">
            {fmtDate(q.created_at)}
          </p>
        </div>
      ))
    ) : (
      <Empty />
    )}
  </div>
</section>
   <section id="caregiver-consent" className="onko-card scroll-mt-24 p-5 xl:col-span-2"><h2 className="text-[20px] font-bold">Caregiver & Consent</h2><div className="mt-3 grid gap-3 md:grid-cols-2">{d.caregivers.length?d.caregivers.map(c=><div key={c.id} className="rounded-xl bg-onko-surface p-4"><div className="flex flex-wrap items-center justify-between gap-2"><strong>{c.name}</strong><span className="onko-chip bg-onko-softteal text-onko-teal">{c.consent_status.toLowerCase()}</span></div><p className="mt-1 text-[13px] text-onko-muted">{c.relation} · {c.type}</p><div className="mt-3 flex flex-wrap gap-2 text-[12px] text-onko-muted">{c.permissions.view_journey&&<span className="rounded-full bg-white px-2 py-1">View journey</span>}{c.permissions.upload_reports&&<span className="rounded-full bg-white px-2 py-1">Upload reports</span>}{c.permissions.receive_escalations&&<span className="rounded-full bg-white px-2 py-1">Receive escalations</span>}</div></div>):<Empty/>}</div></section>
  </div>
 </DoctorShell>
}
function Brief({label,value}:{label:string;value:number}){return <div className="rounded-xl bg-onko-softteal/60 p-3"><p className="text-[12px] text-onko-muted">{label}</p><p className="mt-1 text-[22px] font-bold">{value}</p></div>}
function MedicationCourses({items,events}:{items:any[];events:any[]}){return <section id="medications" className="onko-card scroll-mt-24 p-5"><div className="flex flex-wrap items-end justify-between gap-2"><div><h2 className="text-[20px] font-bold">Medications</h2><p className="mt-1 text-[13px] text-onko-muted">Approved medication courses. Individual scheduled doses remain available to daily check-ins and reminders.</p></div><span className="onko-chip bg-onko-softteal text-onko-teal">{items.length} {items.length===1?"course":"courses"}</span></div><div className="mt-3 grid gap-3">{items.length?items.map(item=>{const occurrences=events.filter(e=>e.care_plan_item_id===item.id);const next=occurrences.find(e=>["UPCOMING","CURRENT"].includes(e.status));return <div key={item.id} className="rounded-xl bg-onko-surface p-4"><div className="flex flex-wrap items-start justify-between gap-3"><div><strong className="text-[15px]">{item.title}</strong><p className="mt-1 text-[13px] text-onko-muted">{fmtDate(item.start_date)}{item.end_date?" → "+fmtDate(item.end_date):""}{item.recurrence?" · "+item.recurrence:""}</p></div><span className="onko-chip bg-white text-onko-muted">{occurrences.length} scheduled {occurrences.length===1?"dose":"doses"}</span></div>{next&&<p className="mt-3 text-[13px] text-onko-muted">Next recorded dose: <strong className="text-onko-text">{fmtDate(next.scheduled_at)}</strong></p>}</div>}):<Empty/>}</div></section>}
function EventSection({id,title,items}:{id:string;title:string;items:any[]}){return <section id={id} className="onko-card scroll-mt-24 p-5"><h2 className="text-[20px] font-bold">{title}</h2><div className="mt-3 grid gap-2">{items.length?items.map(e=><div key={e.id} className="rounded-xl bg-onko-surface p-4"><div className="flex items-start justify-between gap-3"><strong className="text-[15px]">{e.title}</strong><span className="text-[12px] text-onko-muted">{fmtDate(e.scheduled_at)}</span></div><p className="mt-1 text-[13px] text-onko-muted">{e.status.replaceAll("_"," ").toLowerCase()}</p></div>):<Empty/>}</div></section>}
function Empty(){return <p className="text-[14px] text-onko-muted">No recorded items.</p>}
