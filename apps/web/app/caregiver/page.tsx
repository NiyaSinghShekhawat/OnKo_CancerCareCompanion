import Timeline from "@/components/Timeline";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

// TODO(Niya): filter by caregiver.permissions from the backend
export default async function CaregiverHome() {
  const d = await api.patient360("p_rajesh");
  const upcoming = d.timeline.filter((e) => ["UPCOMING", "CURRENT"].includes(e.status));
  return (
    <main className="max-w-xl mx-auto px-5 py-8">
      <h1 className="text-2xl font-semibold">Supporting {d.patient.name}</h1>
      <p className="text-onko-ink/70 mt-1">You can see what {d.patient.name.split(" ")[0]} has shared with you.</p>
      <h2 className="font-semibold mt-8 mb-3">Coming up</h2>
      <Timeline events={upcoming} />
    </main>
  );
}
