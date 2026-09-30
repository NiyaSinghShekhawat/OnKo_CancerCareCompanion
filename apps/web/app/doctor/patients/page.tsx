import Link from "next/link";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Registry() {
  const patients = await api.patients();
  return (
    <DoctorShell>
      <h1 className="text-2xl font-semibold mb-6">Patients</h1>
      <div className="bg-white border border-onko-line rounded-lg overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-left text-onko-ink/60">
            <tr><th className="p-3">Name</th><th className="p-3">Regimen</th><th className="p-3">Cycle</th><th className="p-3">Journey state</th><th /></tr>
          </thead>
          <tbody>
            {patients.map((p) => (
              <tr key={p.id} className="border-t border-onko-line">
                <td className="p-3 font-medium">{p.name}</td>
                <td className="p-3">{p.regimen_label || "—"}</td>
                <td className="p-3">{p.cycle_total ? `${p.cycle_current} of ${p.cycle_total}` : "—"}</td>
                <td className="p-3">{p.journey_state.replaceAll("_", " ").toLowerCase()}</td>
                <td className="p-3 text-right">
                  <Link className="text-onko-teal underline" href={`/doctor/patients/${p.id}`}>Patient 360</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DoctorShell>
  );
}
