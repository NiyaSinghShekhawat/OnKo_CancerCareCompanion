import Link from "next/link";
import { ArrowUpRight, Search, Users } from "lucide-react";
import DoctorShell from "@/components/DoctorShell";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function Registry() {
  const patients = await api.patients();
  return (
    <DoctorShell>
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="onko-eyebrow">Patient registry</p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight">Patients</h1>
          <p className="mt-2 text-sm text-onko-muted">Longitudinal care records across your active patient panel.</p>
        </div>
        <div className="onko-chip bg-onko-softteal text-onko-teal"><Users size={14} className="mr-1.5" />{patients.length} patients</div>
      </div>

      <div className="onko-card mt-7 overflow-hidden">
        <div className="flex flex-wrap items-center gap-3 border-b border-onko-line p-4">
          <div className="relative min-w-[240px] flex-1">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-onko-muted" />
            <input placeholder="Search the patient registry..." className="w-full rounded-xl border border-onko-line bg-onko-surface py-2.5 pl-9 pr-3 text-sm outline-none focus:border-onko-teal" />
          </div>
          <span className="rounded-xl border border-onko-line bg-white px-3 py-2.5 text-xs font-semibold text-onko-muted">All journey states</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[850px] text-sm">
            <thead className="bg-onko-surface text-left">
              <tr className="text-xs font-semibold uppercase tracking-wide text-onko-muted">
                <th className="px-5 py-3">Patient</th><th className="px-5 py-3">Regimen</th><th className="px-5 py-3">Cycle</th><th className="px-5 py-3">Journey state</th><th className="px-5 py-3">Preferred language</th><th className="px-5 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-onko-line">
              {patients.map((p) => (
                <tr key={p.id} className="transition hover:bg-onko-surface">
                  <td className="px-5 py-4"><div className="font-semibold">{p.name}</div><div className="mt-0.5 text-xs text-onko-muted">{p.age} years · {p.gender}</div></td>
                  <td className="px-5 py-4 text-onko-muted">{p.regimen_label || "—"}</td>
                  <td className="px-5 py-4 font-medium">{p.cycle_total ? p.cycle_current + " of " + p.cycle_total : "—"}</td>
                  <td className="px-5 py-4"><span className="onko-chip bg-onko-softteal text-onko-teal">{p.journey_state.replaceAll("_", " ").toLowerCase()}</span></td>
                  <td className="px-5 py-4 text-onko-muted">{p.preferred_language}</td>
                  <td className="px-5 py-4 text-right"><Link className="inline-flex items-center gap-1 font-semibold text-onko-teal" href={"/doctor/patients/" + p.id}>Patient 360 <ArrowUpRight size={14} /></Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </DoctorShell>
  );
}
