import type { CareEvent } from "@/lib/types";
import { fmtDate, fmtTime, statusText } from "@/lib/format";

export default function Timeline({ events }: { events: CareEvent[] }) {
  return (
    <ol className="border-l-2 border-onko-line pl-5 grid gap-4">
      {events.map((e) => (
        <li key={e.id} className="relative">
          <span className="absolute -left-[27px] top-1.5 w-3 h-3 rounded-full bg-onko-teal" />
          <div className="text-xs text-onko-ink/60">{fmtDate(e.scheduled_at)} · {fmtTime(e.scheduled_at)} · {e.type.toLowerCase()}</div>
          <div className="font-medium">{e.title}</div>
          <div className="text-sm text-onko-ink/70">{statusText[e.status]}</div>
          {e.details?.instructions && <div className="text-sm mt-1">{e.details.instructions}</div>}
        </li>
      ))}
    </ol>
  );
}
