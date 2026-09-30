import Timeline from "@/components/Timeline";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

// TODO(Niya): filter by caregiver.permissions from the backend
export default async function CaregiverHome() {
  const d = await api.patient360("p_rajesh");
  const upcoming = d.timeline.filter((e) => ["UPCOMING", "CURRENT"].includes(e.status));
  return (
    <main className="max-w-4xl mx-auto px-6 py-10 md:px-8">
      <h1 className="text-4xl font-semibold">Supporting {d.patient.name}</h1>
      <p className="text-[17px] leading-7 text-onko-ink/70 mt-2">You can see what {d.patient.name.split(" ")[0]} has shared with you.</p>
      <h2 className="text-2xl font-semibold mt-10 mb-4">Coming up</h2>
      <Timeline events={upcoming} />
    </main>
  );
}
