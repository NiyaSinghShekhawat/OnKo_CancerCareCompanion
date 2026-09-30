import type { DashboardOverview } from "@/lib/types";

const cards: { key: keyof DashboardOverview; label: string }[] = [
  { key: "active_patients", label: "Active patients" },
  { key: "missed_activities", label: "Missed activities" },
  { key: "open_queries", label: "Open queries" },
  { key: "reports_pending_review", label: "Reports to review" },
  { key: "sos_open", label: "Open SOS" },
];

export default function StatCards({ data }: { data: DashboardOverview }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
      {cards.map((c) => (
        <div key={c.key} className="bg-white border border-onko-line rounded-lg p-4">
          <div className="text-3xl font-semibold">{data[c.key]}</div>
          <div className="text-sm text-onko-ink/70">{c.label}</div>
        </div>
      ))}
    </div>
  );
}
