import { OverviewCard } from "../overview-card";
import { CompactList, EmptyState, MetricBadge, PageHeader, Panel, formatDateLabel, scoreBadgeStyle } from "../dashboard-ui";
import type { DashboardData } from "../../lib/dashboard-data";

export function OverviewView({ data }: { data: DashboardData }) {
  const topCandidates = [...data.discoveryCandidates]
    .sort(
      (left, right) =>
        (right.final_opportunity_score ?? right.generation_score ?? 0) -
        (left.final_opportunity_score ?? left.generation_score ?? 0)
    )
    .slice(0, 5);
  const topClusters = [...data.clusters]
    .sort((left, right) => (right.latest_final_score ?? 0) - (left.latest_final_score ?? 0))
    .slice(0, 5);

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Workspace Overview"
        title="Navigate by workflow, not by one endless page"
        description="The dashboard is now split into separate pages for overview, discovery, keywords, clusters, reports, and runtime so the workspace reads like an operator tool instead of one long mixed feed."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 18
        }}
      >
        <OverviewCard label="API" value={data.health} detail="FastAPI health status." />
        <OverviewCard
          label="Desktop"
          value={data.runtimeStatus?.status ?? "offline"}
          detail="Authenticated Chrome runtime status."
        />
        <OverviewCard label="Clusters" value={`${data.clusters.length}`} detail="Ranked niche clusters." />
        <OverviewCard label="Keywords" value={`${data.keywords.length}`} detail="Tracked seed and expanded keywords." />
        <OverviewCard label="Discovery" value={`${data.discoveryCandidates.length}`} detail="Visible discovery candidates." />
        <OverviewCard label="Reports" value={`${data.reports.length}`} detail="Generated report artifacts." />
        <OverviewCard label="Failures" value={`${data.operations?.failed_job_count ?? 0}`} detail="Recent failed jobs." />
        <OverviewCard label="Top Opp." value={`${data.metrics.topOpportunity}`} detail="Highest visible cluster score." />
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 24
        }}
      >
        <Panel
          title="Desktop Runtime"
          description="The app is healthy, but authenticated Amazon collection only becomes fully operational when the dedicated desktop Chrome bridge is ready."
          meta={data.runtimeStatus?.status ?? "offline"}
        >
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <MetricBadge>mode {data.runtimeStatus?.mode ?? "unknown"}</MetricBadge>
            <MetricBadge>fetch {data.runtimeStatus?.fetch_mode ?? "unknown"}</MetricBadge>
            <MetricBadge>
              bridge {data.runtimeStatus?.chrome_bridge.status ?? "offline"}
            </MetricBadge>
          </div>
          <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {data.runtimeStatus?.chrome_bridge.reachable &&
            data.runtimeStatus?.chrome_bridge.chrome_debugging_ready
              ? "The authenticated Chrome bridge is ready."
              : data.runtimeStatus?.chrome_bridge.detail ?? "Chrome bridge is not ready yet."}
          </div>
        </Panel>

        <Panel
          title="Recent Crawls"
          description="Latest Amazon collection runs and the latest stored BSR refresh point."
          meta={`BSR ${formatDateLabel(data.operations?.last_bsr_snapshot_at)}`}
        >
          {(data.operations?.recent_crawls ?? []).length === 0 ? (
            <EmptyState text="No crawl history available yet." />
          ) : (
            data.operations!.recent_crawls.slice(0, 5).map((crawl) => (
              <article
                key={crawl.run_id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 16,
                  padding: 14,
                  background: "rgba(255,255,255,0.58)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <strong>{crawl.keyword}</strong>
                  <span style={{ color: "var(--muted)", fontSize: 13 }}>{formatDateLabel(crawl.run_at)}</span>
                </div>
                <span style={{ color: "var(--muted)", fontSize: 14 }}>
                  {crawl.status} | {crawl.result_count ?? 0} results
                </span>
              </article>
            ))
          )}
        </Panel>

        <Panel
          title="Top Discovery Candidates"
          description="Real discovery candidates are shown here. Keyword-expansion variants now live on the Keywords page instead of being mixed into discovery."
          meta={`${topCandidates.length} visible`}
        >
          {topCandidates.length === 0 ? (
            <EmptyState text="No discovery candidates exist yet." />
          ) : (
            topCandidates.map((candidate) => (
              <article
                key={candidate.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 16,
                  padding: 14,
                  background: "rgba(255,255,255,0.58)",
                  display: "grid",
                  gap: 8
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <strong>{candidate.candidate_phrase}</strong>
                  <span style={scoreBadgeStyle(candidate.final_opportunity_score ?? candidate.generation_score)}>
                    {(candidate.final_opportunity_score ?? candidate.generation_score) ?? "n/a"}
                  </span>
                </div>
                <span style={{ color: "var(--muted)", fontSize: 14 }}>
                  {candidate.status} | {candidate.marketplace} | {candidate.decision ?? "pending"}
                </span>
                <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                  {candidate.reason_summary ?? candidate.market_summary ?? "No summary stored yet."}
                </span>
              </article>
            ))
          )}
        </Panel>

        <Panel
          title="Top Clusters"
          description="Highest-scoring niches currently visible in the workspace."
          meta={`${topClusters.length} shown`}
        >
          {topClusters.length === 0 ? (
            <EmptyState text="No clusters exist yet." />
          ) : (
            topClusters.map((cluster) => {
              const detail = data.clusterDetails.find((item) => item.niche_cluster_id === cluster.id);

              return (
                <article
                  key={cluster.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 16,
                    padding: 14,
                    background: "rgba(255,255,255,0.58)",
                    display: "grid",
                    gap: 8
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <strong>{cluster.name}</strong>
                    <span style={scoreBadgeStyle(cluster.latest_final_score)}>{cluster.latest_final_score ?? "n/a"}</span>
                  </div>
                  <span style={{ color: "var(--muted)", fontSize: 14 }}>
                    {cluster.book_class ?? "unclassified"} | {cluster.status}
                  </span>
                  <CompactList
                    items={detail?.top_opportunities.slice(0, 3) ?? []}
                    emptyText="No opportunity highlights stored yet."
                  />
                </article>
              );
            })
          )}
        </Panel>
      </div>
    </div>
  );
}
