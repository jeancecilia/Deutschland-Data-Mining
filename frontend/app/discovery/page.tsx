import { DiscoveryView } from "../../components/views/discovery-view";
import { loadDiscoveryPageData } from "../../lib/dashboard-data";

export default async function DiscoveryPage() {
  const data = await loadDiscoveryPageData();

  return <DiscoveryView data={data} />;
}
