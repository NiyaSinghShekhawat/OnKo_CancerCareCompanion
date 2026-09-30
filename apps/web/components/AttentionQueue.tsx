import Link from "next/link";
import { ArrowUpRight, CircleAlert, MessageSquareText, Siren } from "lucide-react";
import type { AttentionItem } from "@/lib/types";
import { labelText } from "@/lib/format";

const tone: Record<string, string> = {
  SOS: "bg-red-50 text-onko-sos border-red-100",
  NEEDS_REVIEW: "bg-onko-amberbg text-onko-amber border-amber-200",
  QUERY: "bg-sky-50 text-sky-800 border-sky-100",
  FOLLOW_UP: "bg-onko-softteal text-onko-teal border-onko-softteal",
};

const icons = { SOS: Siren, NEEDS_REVIEW: CircleAlert, QUERY: MessageSquareText, FOLLOW_UP: CircleAlert };

export default function AttentionQueue({ items }: { items: AttentionItem[] }) {
  if (!items.length) return <div className="onko-card p-5 text-sm text-onko-muted">Nothing needs attention right now.</div>;
  return (
    <div className="onko-card overflow-hidden">
      <div className="divide-y divide-onko-line">
        {items.map((a) => {
          const Icon = icons[a.label];
          return (
            <div key={a.id} className="group grid gap-4 p-4 transition hover:bg-onko-surface md:grid-cols-[160px_1fr_auto] md:items-center md:p-5">
              <div><span className={"inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold " + tone[a.label]}><Icon size={13} /> {labelText[a.label]}</span></div>
              <div className="min-w-0"><p className="font-semibold">{a.patient_name}</p><p className="mt-1 line-clamp-2 text-sm text-onko-muted">{a.reasons.join(" · ")}</p></div>
              <Link href={"/doctor/patients/" + a.patient_id} className="inline-flex items-center gap-1.5 text-sm font-semibold text-onko-teal">Patient 360 <ArrowUpRight size={15} /></Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
