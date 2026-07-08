import { OverviewView } from "../components/views/overview-view";
import { loadOverviewData } from "../lib/dashboard-data";

export default async function Home() {
  const data = await loadOverviewData();

  return <OverviewView data={data} />;
}
