import PatientShell from "@/components/PatientShell";
import PatientQueriesClient from "@/components/PatientQueriesClient";
import { serverApi } from "@/lib/server-api";

export const dynamic = "force-dynamic";

export default async function QueriesPage() {
  const d = await serverApi.patient360("p_rajesh");
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
