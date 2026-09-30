import DoctorShell from "@/components/DoctorShell";
import StatCards from "@/components/StatCards";
import AttentionQueue from "@/components/AttentionQueue";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DoctorHome() {
  const [overview, attention] = await Promise.all([api.overview(), api.attention()]);
  return (
    <DoctorShell>
      <h1 className="text-3xl font-semibold">Good morning, Dr. Mehta</h1>
      <p className="text-onko-ink/70 mt-1">Here is what needs your attention across your patients.</p>
      <div className="mt-6"><StatCards data={overview} /></div>
      <h2 className="text-xl font-semibold mt-10 mb-1">Attention queue</h2>
      <p className="text-sm text-onko-ink/70 mb-4">Surfaced from recorded activity, each with its reason.</p>
      <AttentionQueue items={attention} />
    </DoctorShell>
  );
}
