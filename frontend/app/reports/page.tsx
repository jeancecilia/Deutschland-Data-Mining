import { ReportsView } from "../../components/views/reports-view";
import { loadReportsPageData } from "../../lib/dashboard-data";

export default async function ReportsPage() {
  const data = await loadReportsPageData();

  return <ReportsView data={data} />;
}
