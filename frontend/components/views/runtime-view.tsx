import type { DashboardData } from "../../lib/dashboard-data";
import { EmptyState, MetricBadge, PageHeader, Panel, formatDateLabel } from "../dashboard-ui";

export function RuntimeView({ data }: { data: DashboardData }) {
  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Runtime and Operations"
        title="Desktop readiness and job health"
        description="This page is for the local runtime itself: authenticated Chrome bridge state, recent crawls, failures, and the exact desktop commands the operator needs."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 24
        }}
      >
        <Panel
          title="Desktop Runtime"
          description="Authenticated Amazon collection depends on the desktop Chrome bridge."
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
              ? "Authenticated Chrome bridge is ready."
              : data.runtimeStatus?.chrome_bridge.detail ?? "Chrome bridge is not ready."}
          </div>
          <code
            style={{
              borderRadius: 12,
              border: "1px solid var(--border)",
              padding: "10px 12px",
              background: "rgba(255,255,255,0.82)",
              fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
              fontSize: 13,
              overflowWrap: "anywhere"
            }}
          >
            {data.runtimeStatus?.recommended_commands.desktop_stack ?? ".\\scripts\\start_desktop_stack.ps1 -Build"}
          </code>
          <code
            style={{
              borderRadius: 12,
              border: "1px solid var(--border)",
              padding: "10px 12px",
              background: "rgba(255,255,255,0.82)",
              fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
              fontSize: 13,
              overflowWrap: "anywhere"
            }}
          >
            {data.runtimeStatus?.recommended_commands.bridge_only ?? ".\\scripts\\start_chrome_bridge.ps1"}
          </code>
        </Panel>

        <Panel
          title="Recent Crawls"
          description="Latest collection runs and crawl notes."
          meta={formatDateLabel(data.operations?.last_crawl_at)}
        >
          {(data.operations?.recent_crawls ?? []).length === 0 ? (
            <EmptyState text="No crawl history available yet." />
          ) : (
            data.operations!.recent_crawls.map((crawl) => (
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
                {crawl.notes ? (
                  <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 6 }}>{crawl.notes}</div>
                ) : null}
              </article>
            ))
          )}
        </Panel>

        <Panel
          title="Failed Jobs"
          description="Recent failed search or report jobs for operator follow-up."
          meta={`${data.operations?.failed_job_count ?? 0} failures`}
        >
          {(data.operations?.failed_jobs ?? []).length === 0 ? (
            <EmptyState text="No failed jobs recorded." />
          ) : (
            data.operations!.failed_jobs.map((job, index) => (
              <article
                key={`${job.job_type}-${job.reference}-${index}`}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 16,
                  padding: 14,
                  background: "rgba(255,255,255,0.58)"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                  <strong>{job.reference}</strong>
                  <span style={{ color: "var(--muted)", fontSize: 13 }}>{formatDateLabel(job.occurred_at)}</span>
                </div>
                <span style={{ color: "var(--muted)", fontSize: 14 }}>
                  {job.job_type} | {job.status}
                </span>
                {job.notes ? (
                  <div style={{ color: "var(--muted)", fontSize: 13, marginTop: 6 }}>{job.notes}</div>
                ) : null}
              </article>
            ))
          )}
        </Panel>
      </div>
    </div>
  );
}
