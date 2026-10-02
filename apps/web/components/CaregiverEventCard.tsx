import { CalendarClock, ClipboardCheck, Pill, Stethoscope, Target } from "lucide-react";
import type { MinimizedCareEvent } from "@/lib/types";
import { fmtDate, fmtTime, statusText } from "@/lib/format";

const icons = {
  MEDICATION: Pill,
  INVESTIGATION: ClipboardCheck,
  TREATMENT: Stethoscope,
  APPOINTMENT: CalendarClock,
  MILESTONE: Target,
};

export default function CaregiverEventCard({ event }: { event: MinimizedCareEvent }) {
  const Icon = icons[event.type];
  return (
    <article className="rounded-2xl bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-onko-softteal text-onko-teal">
          <Icon size={19} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-start justify-between gap-2">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-wide text-onko-teal">
                {event.type.toLowerCase()} · {fmtTime(event.scheduled_at)}
              </p>
              <h3 className="mt-1 text-[16px] font-bold">{event.title}</h3>
            </div>
            <span className="rounded-full bg-onko-surface px-2.5 py-1 text-[11px] font-semibold text-onko-muted">
              {statusText[event.status]}
            </span>
          </div>
          <p className="mt-2 text-[12px] text-onko-muted">{fmtDate(event.scheduled_at)}</p>
        </div>
      </div>
    </article>
  );
}
