import { RuntimeView } from "../../components/views/runtime-view";
import { loadRuntimePageData } from "../../lib/dashboard-data";

export default async function RuntimePage() {
  const data = await loadRuntimePageData();

  return <RuntimeView data={data} />;
}
