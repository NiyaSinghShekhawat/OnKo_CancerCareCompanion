import { CalendarDays, ClipboardCheck, FileText, MessageSquareText, Siren, Users } from "lucide-react";
import type { DashboardOverview } from "@/lib/types";

const cards: { key: keyof DashboardOverview; label: string; helper: string; icon: typeof Users; tone?: "warning" | "danger" }[] = [
  { key: "active_patients", label: "Active patients", helper: "Under active care", icon: Users },
  { key: "consultations_today", label: "Consultations today", helper: "Scheduled today", icon: CalendarDays },
  { key: "missed_activities", label: "Missed activities", helper: "Recorded workflow events", icon: ClipboardCheck, tone: "warning" },
  { key: "open_queries", label: "Open queries", helper: "Awaiting care-team action", icon: MessageSquareText },
  { key: "reports_pending_review", label: "Reports to review", helper: "New patient records", icon: FileText },
  { key: "sos_open", label: "Open SOS", helper: "Patient-triggered", icon: Siren, tone: "danger" },
];

export default function StatCards({ data }: { data: DashboardOverview }) {
  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-6">
      {cards.map((c) => {
        const Icon = c.icon;
        const iconTone = c.tone === "danger" ? "bg-red-50 text-onko-sos" : c.tone === "warning" ? "bg-onko-amberbg text-onko-amber" : "bg-onko-softteal text-onko-teal";
        return (
          <div key={c.key} className="onko-card min-h-[142px] p-4">
            <div className={"grid h-9 w-9 place-items-center rounded-xl " + iconTone}><Icon size={18} /></div>
            <div className="mt-4 text-3xl font-bold tracking-tight">{data[c.key]}</div>
            <div className="mt-1 text-sm font-semibold">{c.label}</div>
            <div className="mt-1 text-xs text-onko-muted">{c.helper}</div>
          </div>
        );
      })}
    </div>
  );
}
