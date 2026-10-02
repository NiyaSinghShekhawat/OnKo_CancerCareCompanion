import PatientShell from "@/components/PatientShell";
import PatientQueriesClient from "@/components/PatientQueriesClient";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function QueriesPage() {
  const d = await api.patient360("p_rajesh");
  return (
    <PatientShell patient={d.patient}>
      <PatientQueriesClient
        p={d.patient}
        openQueries={d.open_queries}
        queryHistory={d.query_history ?? d.open_queries}
      />
    </PatientShell>
  );
}
