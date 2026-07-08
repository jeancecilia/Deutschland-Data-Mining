import type { DashboardData } from "../../lib/dashboard-data";
import { ButtonLink, EmptyState, MetricBadge, PageHeader, Panel, formatDateLabel } from "../dashboard-ui";

const browserApiBaseUrl = process.env.KDP_API_BROWSER_URL ?? "http://localhost:8000";

function reportArtifactHref(reportId: number, format: string): string {
  return `${browserApiBaseUrl}/api/v1/reports/${reportId}/download?format=${encodeURIComponent(format)}`;
}

export function ReportsView({ data }: { data: DashboardData }) {
  const reportTypeCounts = new Map<string, number>();
  for (const report of data.reports) {
    reportTypeCounts.set(report.report_type, (reportTypeCounts.get(report.report_type) ?? 0) + 1);
  }

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Report Output"
        title="Generated artifacts in one place"
        description="Reports are separated from discovery and cluster exploration so the latest artifact set per cluster is easy to scan."
      />

      <Panel title="Report Inventory" description="Markdown, CSV, JSON, and PDF artifacts generated from the current workspace." meta={`${data.reports.length} current reports`}>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {[...reportTypeCounts.entries()].map(([type, count]) => (
            <MetricBadge key={type}>
              {type} {count}
            </MetricBadge>
          ))}
        </div>

        {data.reports.length === 0 ? (
          <EmptyState text="No reports generated yet." />
        ) : (
          data.reports.map((report) => (
            <article
              key={report.id}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 18,
                padding: 16,
                background: "rgba(255,255,255,0.58)",
                display: "grid",
                gap: 10
              }}
            >
              <div style={{ display: "grid", gap: 4 }}>
                <strong>{report.title}</strong>
                <span style={{ color: "var(--muted)", fontSize: 14 }}>
                  Cluster #{report.niche_cluster_id} | {report.report_type} | {report.status}
                </span>
                <span style={{ color: "var(--muted)", fontSize: 13 }}>
                  Updated {formatDateLabel(report.updated_at)}
                </span>
              </div>

              <div style={{ display: "grid", gap: 4, color: "var(--muted)", fontSize: 13 }}>
                <span>Markdown: {report.markdown_path ?? "pending"}</span>
                <span>CSV: {report.csv_path ?? "pending"}</span>
                <span>JSON: {report.json_path ?? "pending"}</span>
                <span>PDF: {report.pdf_path ?? "pending"}</span>
              </div>

              <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {report.markdown_path ? <ButtonLink href={reportArtifactHref(report.id, "markdown")}>Markdown</ButtonLink> : null}
                {report.csv_path ? <ButtonLink href={reportArtifactHref(report.id, "csv")}>CSV</ButtonLink> : null}
                {report.json_path ? <ButtonLink href={reportArtifactHref(report.id, "json")}>JSON</ButtonLink> : null}
                {report.pdf_path ? <ButtonLink href={reportArtifactHref(report.id, "pdf")}>PDF</ButtonLink> : null}
              </div>
            </article>
          ))
        )}
      </Panel>
    </div>
  );
}
