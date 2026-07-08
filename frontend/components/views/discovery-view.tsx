import {
  generateDiscoveryCandidatesAction,
  generateReportAction,
  runDiscoveryCycleAction,
  validateDiscoveryCandidateAction
} from "../../app/actions";
import type { DashboardData } from "../../lib/dashboard-data";
import {
  ActionButton,
  Badge,
  CompactList,
  EmptyState,
  MetricBadge,
  MetricTile,
  PageHeader,
  Panel,
  SignalList,
  decisionBadgeStyle,
  formatDateLabel,
  scoreBadgeStyle
} from "../dashboard-ui";

export function DiscoveryView({ data }: { data: DashboardData }) {
  const validatedCount = data.discoveryCandidates.filter((candidate) => candidate.status === "validated").length;
  const goCount = data.discoveryCandidates.filter((candidate) => candidate.decision === "GO").length;
  const runtimeReady = Boolean(
    data.runtimeStatus?.chrome_bridge.reachable && data.runtimeStatus?.chrome_bridge.chrome_debugging_ready
  );

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Zero-Seed Discovery"
        title="Discovery candidates only"
        description="This page is now isolated from raw keyword expansion. Discovery candidates come from the structured niche universe and go through validation, scoring, and report generation."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) minmax(0, 1fr)",
          gap: 24
        }}
      >
        <Panel
          title="Discovery Controls"
          description="Generate new candidates or run the full cycle. This is separate from manual seed expansion on the Keywords page."
          meta={runtimeReady ? "desktop ready" : "desktop attention needed"}
        >
          <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
            <MetricBadge>{data.discoveryUniverse?.topics.length ?? 0} topics</MetricBadge>
            <MetricBadge>{data.discoveryUniverse?.audiences.length ?? 0} audiences</MetricBadge>
            <MetricBadge>{data.discoveryUniverse?.pain_points.length ?? 0} pains</MetricBadge>
            <MetricBadge>{validatedCount} validated</MetricBadge>
            <MetricBadge>{goCount} GO</MetricBadge>
          </div>

          <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
            {runtimeReady
              ? "Authenticated desktop collection is ready."
              : data.runtimeStatus?.chrome_bridge.detail ?? "Desktop Chrome bridge is not ready yet."}
          </div>

          <div style={{ display: "grid", gap: 10 }}>
            <form action={generateDiscoveryCandidatesAction}>
              <input type="hidden" name="limit" value="120" />
              <ActionButton primary>Generate 120 Candidates</ActionButton>
            </form>

            <form action={runDiscoveryCycleAction}>
              <input type="hidden" name="generateLimit" value="120" />
              <input type="hidden" name="validateLimit" value="6" />
              <input type="hidden" name="autoGenerateReports" value="true" />
              <input type="hidden" name="force" value="false" />
              <ActionButton>Run Discovery Cycle</ActionButton>
            </form>
          </div>

          <div style={{ display: "grid", gap: 8 }}>
            <span style={{ color: "var(--muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Priority Topics
            </span>
            <CompactList
              items={(data.discoveryUniverse?.topics ?? []).slice(0, 6).map((item) => item.name)}
              emptyText="No discovery universe loaded yet."
            />
          </div>
        </Panel>

        <Panel
          title="Discovery Candidates"
          description="Candidates are ranked by validated opportunity first. Keyword expansions are intentionally not shown here anymore."
          meta={`${data.discoveryCandidates.length} visible`}
        >
          {data.discoveryCandidates.length === 0 ? (
            <EmptyState text="No discovery candidates exist yet." />
          ) : (
            data.discoveryCandidates.map((candidate) => (
              <article
                key={candidate.id}
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
                    <strong style={{ fontSize: 18 }}>{candidate.candidate_phrase}</strong>
                    <span style={{ color: "var(--muted)", fontSize: 14 }}>
                      {[candidate.topic, candidate.audience, candidate.context, candidate.book_format]
                        .filter(Boolean)
                        .join(" | ")}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 13 }}>
                      {candidate.marketplace} | {candidate.status}
                      {candidate.last_validated_at ? ` | checked ${formatDateLabel(candidate.last_validated_at)}` : ""}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "flex-start" }}>
                    <span style={scoreBadgeStyle(candidate.final_opportunity_score ?? candidate.generation_score)}>
                      {(candidate.final_opportunity_score ?? candidate.generation_score) ?? "n/a"}
                    </span>
                    {candidate.decision ? (
                      <span style={decisionBadgeStyle(candidate.decision)}>{candidate.decision}</span>
                    ) : null}
                    {candidate.validated_book_type || candidate.book_type_hint ? (
                      <Badge>{candidate.validated_book_type ?? candidate.book_type_hint}</Badge>
                    ) : null}
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                  <MetricTile label="Demand" value={candidate.demand_score} />
                  <MetricTile label="Competition" value={candidate.competition_score} />
                  <MetricTile label="Gap" value={candidate.gap_score} />
                  <MetricTile label="Risk" value={candidate.risk_score} />
                </div>

                <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>
                  {candidate.reason_summary ?? candidate.market_summary ?? "No market summary stored yet."}
                </div>

                <SignalList
                  items={candidate.signals.slice(0, 4).map((signal) => ({
                    label: signal.label,
                    summary: signal.summary,
                    score: signal.score,
                    direction: signal.direction
                  }))}
                />

                {candidate.validation_notes ? (
                  <div style={{ color: "var(--muted)", lineHeight: 1.6 }}>{candidate.validation_notes}</div>
                ) : null}

                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <form action={validateDiscoveryCandidateAction}>
                    <input type="hidden" name="candidateId" value={candidate.id} />
                    <input type="hidden" name="autoGenerateReports" value="true" />
                    <input type="hidden" name="force" value="false" />
                    <ActionButton>{candidate.status === "validated" ? "Recheck" : "Validate"}</ActionButton>
                  </form>
                  <form action={validateDiscoveryCandidateAction}>
                    <input type="hidden" name="candidateId" value={candidate.id} />
                    <input type="hidden" name="autoGenerateReports" value="true" />
                    <input type="hidden" name="force" value="true" />
                    <ActionButton>Force Recheck</ActionButton>
                  </form>
                  {candidate.niche_cluster_id ? (
                    <form action={generateReportAction}>
                      <input type="hidden" name="clusterId" value={candidate.niche_cluster_id} />
                      <input type="hidden" name="reportType" value="go_no_go_report" />
                      <ActionButton>Go/No-Go Report</ActionButton>
                    </form>
                  ) : null}
                </div>
              </article>
            ))
          )}
        </Panel>
      </div>
    </div>
  );
}
