import Link from "next/link";
import { ArrowRight, CircleAlert, Clock3, MessageSquareText, Siren, UserRoundCheck } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import DoctorAttentionActions from "@/components/DoctorAttentionActions";
import { NURSE_ACTOR, serverApi } from "@/lib/server-api";
import { labelText } from "@/lib/format";

export const dynamic = "force-dynamic";

const icon={SOS:Siren,NEEDS_REVIEW:CircleAlert,QUERY:MessageSquareText,FOLLOW_UP:Clock3};
const tone={SOS:"bg-red-50 text-onko-sos",NEEDS_REVIEW:"bg-onko-amberbg text-onko-amber",QUERY:"bg-violet-50 text-violet-700",FOLLOW_UP:"bg-onko-softteal text-onko-teal"};
const assigneeName:Record<string,string>={doc_mehta:"Dr. Mehta",nurse_anita:"Nurse Anita"};

export default async function AttentionPage({
  searchParams,
}: {
  searchParams?: { mine?: string; label?: string; patient_id?: string; assigned_to?: string; status?: string };
}) {
  const mine=searchParams?.mine==="1";
  const filters={
    label:searchParams?.label,
    patient_id:searchParams?.patient_id,
    assigned_to:searchParams?.assigned_to,
    status:searchParams?.status,
  };
  const raw=mine?await serverApi.attentionMine(NURSE_ACTOR):await serverApi.attention(filters);
  const items=searchParams?.status?raw:raw.filter(i=>i.status==="PENDING"||i.status==="ACKNOWLEDGED");
  const actorRole=mine?"care_team" as const:"doctor" as const;
  const actorId=mine?"nurse_anita":"doc_mehta";

  return <DoctorShell>
    <div className="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p className="onko-eyebrow text-onko-teal">Doctor workflow</p>
        <h1 className="mt-2 text-[44px] font-bold tracking-tight">Attention Queue</h1>
        <p className="mt-2 max-w-3xl text-[16px] leading-7 text-onko-muted">
          Active workflow items surfaced with factual reasons. Labels describe why an item is here; they are not clinical risk scores.
        </p>
      </div>
      <span className="onko-chip bg-white text-onko-teal shadow-sm">{items.length} active</span>
    </div>

    <div className="mt-6 flex flex-wrap gap-2">
      <Link href="/doctor/attention" className={"onko-button-secondary "+(!mine&&!searchParams?.label&&!searchParams?.status?"border-onko-teal text-onko-teal":"")}>All active</Link>
      <Link href="/doctor/attention?mine=1" className={"onko-button-secondary "+(mine?"border-onko-teal bg-onko-softteal text-onko-teal":"")}><UserRoundCheck size={16}/>Nurse Anita · My items</Link>
      {Object.keys(labelText).map(label=><Link key={label} href={"/doctor/attention?label="+label} className={"onko-button-secondary "+(searchParams?.label===label?"border-onko-teal text-onko-teal":"")}>{labelText[label as keyof typeof labelText]}</Link>)}
    </div>

    <form className="onko-card mt-4 grid gap-3 p-4 md:grid-cols-4">
      <input name="patient_id" defaultValue={searchParams?.patient_id??""} placeholder="Patient id, e.g. p_arjun" className="rounded-xl border border-onko-line bg-white px-3 py-2.5 text-[13px]"/>
      <select name="assigned_to" defaultValue={searchParams?.assigned_to??""} className="rounded-xl border border-onko-line bg-white px-3 py-2.5 text-[13px]">
        <option value="">Any assignee</option><option value="doc_mehta">Dr. Mehta</option><option value="nurse_anita">Nurse Anita</option>
      </select>
      <select name="status" defaultValue={searchParams?.status??""} className="rounded-xl border border-onko-line bg-white px-3 py-2.5 text-[13px]">
        <option value="">Active only</option><option value="PENDING">Pending</option><option value="ACKNOWLEDGED">Acknowledged</option><option value="HANDLED">Handled</option><option value="CLOSED">Closed</option>
      </select>
      <button className="onko-button-primary">Apply filters</button>
    </form>

    <div className="mt-5 grid gap-4">
      {items.length?items.map(a=>{const Icon=icon[a.label];return <article key={a.id} className="onko-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <span className={"onko-chip "+tone[a.label]}><Icon size={15}/>{labelText[a.label]}</span>
            <h2 className="mt-3 text-[22px] font-bold">{a.patient_name}</h2>
            <p className="mt-1 text-[13px] font-semibold uppercase tracking-wide text-onko-muted">
              {a.status.toLowerCase()} · {a.assigned_to?"Assigned to "+(assigneeName[a.assigned_to]??a.assigned_to):"Unassigned"}
            </p>
          </div>
          <Link href={"/doctor/patients/"+a.patient_id} className="onko-button-secondary">Patient 360 <ArrowRight size={16}/></Link>
        </div>
        <div className="mt-5 rounded-xl bg-onko-surface p-5">
          <p className="text-[12px] font-bold uppercase tracking-[.1em] text-onko-muted">Why this was surfaced</p>
          <ul className="mt-3 grid gap-2 text-[15px] leading-6">{a.reasons.map(r=><li key={r} className="flex gap-3"><span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-onko-teal"/>{r}</li>)}</ul>
        </div>
        <DoctorAttentionActions attentionId={a.id} initialStatus={a.status} assignedTo={a.assigned_to} actorRole={actorRole} actorId={actorId}/>
      </article>}):<div className="onko-card p-6 text-[15px] text-onko-muted">No attention items match this view.</div>}
    </div>
  </DoctorShell>;
}
