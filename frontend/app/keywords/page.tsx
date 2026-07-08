import { KeywordsView } from "../../components/views/keywords-view";
import { loadKeywordsPageData } from "../../lib/dashboard-data";

export default async function KeywordsPage() {
  const data = await loadKeywordsPageData();

  return <KeywordsView data={data} />;
}
