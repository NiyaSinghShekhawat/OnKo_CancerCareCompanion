import Link from "next/link";
import type { AttentionItem } from "@/lib/types";
import { labelText } from "@/lib/format";

const tone: Record<string, string> = {
  SOS: "bg-onko-sos text-white",
  NEEDS_REVIEW: "bg-amber-100 text-onko-amber",
  QUERY: "bg-sky-100 text-sky-800",
  FOLLOW_UP: "bg-onko-mint text-onko-teal",
};

export default function AttentionQueue({ items }: { items: AttentionItem[] }) {
  if (!items.length) return <p className="text-onko-ink/70">Nothing needs attention right now.</p>;
  return (
    <ul className="grid gap-3">
      {items.map((a) => (
        <li key={a.id} className="bg-white border border-onko-line rounded-lg p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className={`text-xs font-medium px-2 py-1 rounded ${tone[a.label]}`}>{labelText[a.label]}</span>
              <span className="font-medium">{a.patient_name}</span>
            </div>
            <Link href={`/doctor/patients/${a.patient_id}`}
              className="text-sm bg-onko-teal text-white px-3 py-1.5 rounded-md hover:bg-onko-tealdark">
              Open Patient 360
            </Link>
          </div>
          <ul className="mt-3 text-sm list-disc pl-5 text-onko-ink/80">
            {a.reasons.map((r) => <li key={r}>{r}</li>)}
          </ul>
        </li>
      ))}
    </ul>
  );
}
