import {
  analyzeSachbuchAction,
  generateReportAction,
  refreshClusterBsrAction
} from "../../app/actions";
import type { DashboardData } from "../../lib/dashboard-data";
import {
  ActionButton,
  Badge,
  CompactList,
  EmptyState,
  MetricTile,
  PageHeader,
  Panel,
  SignalList,
  decisionBadgeStyle,
  scoreBadgeStyle
} from "../dashboard-ui";

export function ClustersView({ data }: { data: DashboardData }) {
  const detailByClusterId = new Map(data.clusterDetails.map((detail) => [detail.niche_cluster_id, detail]));
  const sachbuchByClusterId = new Map(
    data.sachbuchAnalyses.map((analysis) => [analysis.niche_cluster_id, analysis])
  );
  const rankedClusters = [...data.clusters].sort(
    (left, right) => (right.latest_final_score ?? 0) - (left.latest_final_score ?? 0)
  );

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Cluster Intelligence"
        title="One niche card per cluster"
        description="The repeated competitor and review sections are folded back into the cluster workflow. Each cluster card now carries the key scoring, complaints, opportunities, and actions in one place."
      />

      <div style={{ display: "grid", gap: 24 }}>
        <Panel
          title="Niche Explorer"
          description="Opportunity, demand, saturation, competition, and sachbuch fit per cluster."
          meta={`${rankedClusters.length} clusters`}
        >
          {rankedClusters.length === 0 ? (
            <EmptyState text="Run the pipeline to populate the niche explorer." />
          ) : (
            rankedClusters.map((cluster) => {
              const detail = detailByClusterId.get(cluster.id);
              const sachbuch = sachbuchByClusterId.get(cluster.id);

              return (
                <article
                  key={cluster.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 18,
                    padding: 16,
                    background: "rgba(255,255,255,0.6)",
                    display: "grid",
                    gap: 14
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "grid", gap: 6 }}>
                      <strong style={{ fontSize: 18 }}>{cluster.name}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 14 }}>
                        {cluster.main_keyword ?? cluster.name} | {cluster.status}
                      </span>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-start" }}>
                      <span style={scoreBadgeStyle(cluster.latest_final_score)}>{cluster.latest_final_score ?? "n/a"}</span>
                      {sachbuch ? (
                        <span style={decisionBadgeStyle(sachbuch.go_decision)}>{sachbuch.go_decision}</span>
                      ) : null}
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {cluster.book_class ? <Badge>{cluster.book_class}</Badge> : null}
                    {detail?.recommended_book_class ? <Badge>rec {detail.recommended_book_class}</Badge> : null}
                    {detail ? <Badge>conf {detail.book_classification.confidence}</Badge> : null}
                  </div>

                  {detail ? (
                    <>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                        <MetricTile label="Demand" value={detail.score.demand_score} />
                        <MetricTile label="Sat. Risk" value={detail.score.saturation_risk} />
                        <MetricTile label="Entry" value={detail.score.entry_feasibility_score} />
                        <MetricTile label="Review Wall" value={detail.score.review_wall_risk} />
                      </div>

                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                        <MetricTile label="BSR Coverage" value={detail.competitor_summary.bsr_snapshot_coverage} />
                        <MetricTile label="Listing Q." value={detail.competitor_summary.average_listing_quality} />
                        <MetricTile label="Strong Comp." value={detail.competitor_summary.strong_competitor_count} />
                        <MetricTile label="Weak Comp." value={detail.competitor_summary.weak_competitor_count} />
                      </div>

                      <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
                        {detail.score.explanation ?? "No scoring explanation stored yet."}
                      </div>

                      <SignalList
                        items={detail.signals.slice(0, 4).map((signal) => ({
                          label: signal.label,
                          summary: signal.summary,
                          score: signal.score,
                          direction: signal.direction
                        }))}
                      />

                      <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={{ color: "var(--muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                            Top Complaints
                          </span>
                          <CompactList items={detail.top_complaints} emptyText="No complaints stored." />
                        </div>
                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={{ color: "var(--muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                            Top Opportunities
                          </span>
                          <CompactList items={detail.top_opportunities} emptyText="No opportunities stored." />
                        </div>
                      </div>

                      <div style={{ display: "grid", gap: 8 }}>
                        <span style={{ color: "var(--muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
                          Top Books
                        </span>
                        <CompactList
                          items={detail.top_books.slice(0, 4).map((book) => book.title || book.asin)}
                          emptyText="No books linked yet."
                        />
                      </div>
                    </>
                  ) : (
                    <EmptyState text="Detailed cluster analysis is not available yet for this niche." />
                  )}

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <form action={refreshClusterBsrAction}>
                      <input type="hidden" name="clusterId" value={cluster.id} />
                      <ActionButton>Refresh BSR</ActionButton>
                    </form>
                    <form action={generateReportAction}>
                      <input type="hidden" name="clusterId" value={cluster.id} />
                      <input type="hidden" name="reportType" value="niche_report" />
                      <ActionButton>Niche Report</ActionButton>
                    </form>
                    <form action={generateReportAction}>
                      <input type="hidden" name="clusterId" value={cluster.id} />
                      <input type="hidden" name="reportType" value="go_no_go_report" />
                      <ActionButton>Go/No-Go</ActionButton>
                    </form>
                    <form action={analyzeSachbuchAction}>
                      <input type="hidden" name="clusterId" value={cluster.id} />
                      <ActionButton>Sachbuch Gap</ActionButton>
                    </form>
                  </div>
                </article>
              );
            })
          )}
        </Panel>
      </div>
    </div>
  );
}
