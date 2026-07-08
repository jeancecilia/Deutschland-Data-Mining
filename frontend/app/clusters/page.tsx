import { ClustersView } from "../../components/views/clusters-view";
import { loadClustersPageData } from "../../lib/dashboard-data";

export default async function ClustersPage() {
  const data = await loadClustersPageData();

  return <ClustersView data={data} />;
}
