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
  const validatedCount = data.discoveryCandidates.filter((c) => c.status === "validated").length;
  const goCount = data.discoveryCandidates.filter((c) => c.decision === "GO").length;
  const runtimeReady = Boolean(
    data.runtimeStatus?.chrome_bridge.reachable && data.runtimeStatus?.chrome_bridge.chrome_debugging_ready
  );

  const pipelineOverview = data.discoveryPipelineOverview;
  const pipelineCandidates = data.discoveryPipelineCandidates;

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Discovery Pipeline"
        title="Topic Graph → Niche Candidates → Validation"
        description="Sources feed the entity graph, which generates candidates. Promoted candidates become seed keywords for KDP analysis."
      />

      {/* ── Unified Stats ─────────────────────────────────────────── */}
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
        <MetricBadge>{pipelineOverview?.entity_types?.topic?.toLocaleString() ?? (pipelineOverview?.entity_count?.toLocaleString() ?? 0)} topics</MetricBadge>
        <MetricBadge>{pipelineOverview?.entity_types?.audience?.toLocaleString() ?? 0} audiences</MetricBadge>
        <MetricBadge>{pipelineOverview?.entity_types?.problem?.toLocaleString() ?? 0} problems</MetricBadge>
        <MetricBadge>{pipelineOverview?.domain_count ?? 0} domains</MetricBadge>
        <MetricBadge>{pipelineOverview?.entity_count?.toLocaleString() ?? 0} entities</MetricBadge>
        <MetricBadge>{pipelineOverview?.relation_count?.toLocaleString() ?? 0} relations</MetricBadge>
        <MetricBadge>{pipelineOverview?.candidate_count?.toLocaleString() ?? 0} candidates</MetricBadge>
        <MetricBadge>{pipelineOverview?.promoted_candidate_count ?? 0} promoted</MetricBadge>
        <MetricBadge>{pipelineOverview?.rejected_candidate_count ?? 0} blocked</MetricBadge>
      </div>

      {/* ── Controls ──────────────────────────────────────────────── */}
      <Panel
        title="Discovery Controls"
        description="Generate candidates from the structured niche universe or from the entity graph pipeline."
        meta={runtimeReady ? "desktop ready" : "desktop attention needed"}
      >
        <div style={{ color: "var(--muted)", lineHeight: 1.6, marginBottom: 12 }}>
          {runtimeReady
            ? "Authenticated desktop collection is ready."
            : data.runtimeStatus?.chrome_bridge.detail ?? "Desktop Chrome bridge is not ready yet."}
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <span style={{ color: "var(--muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Universe Composer (legacy)
            </span>
            <form action={generateDiscoveryCandidatesAction}>
              <input type="hidden" name="limit" value="120" />
              <ActionButton primary>Generate 120</ActionButton>
            </form>
            <form action={runDiscoveryCycleAction}>
              <input type="hidden" name="generateLimit" value="120" />
              <input type="hidden" name="validateLimit" value="6" />
              <input type="hidden" name="autoGenerateReports" value="true" />
              <input type="hidden" name="force" value="false" />
              <ActionButton>Run Cycle</ActionButton>
            </form>
          </div>
          <div style={{ display: "grid", gap: 8 }}>
            <span style={{ color: "var(--muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>
              Graph Pipeline (new)
            </span>
            <div style={{ display: "grid", gap: 4 }}>
              <a href="http://localhost:8000/api/v1/discovery-pipeline/overview" target="_blank" style={{ fontSize: 12 }}>
                📊 API Overview
              </a>
              <a href="http://localhost:8000/api/v1/discovery-pipeline/entities" target="_blank" style={{ fontSize: 12 }}>
                🏷️ Entities
              </a>
              <a href="http://localhost:8000/api/v1/discovery-pipeline/graph" target="_blank" style={{ fontSize: 12 }}>
                🔗 Topic Graph
              </a>
              <a href="http://localhost:8000/api/v1/discovery-pipeline/candidates" target="_blank" style={{ fontSize: 12 }}>
                🎯 Pipeline Candidates
              </a>
            </div>
          </div>
        </div>

        <div style={{ display: "grid", gap: 6, marginTop: 12 }}>
          <span style={{ color: "var(--muted)", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.08em" }}>
            Top Domains (from {pipelineOverview?.domain_count ?? 0} total)
          </span>
          <CompactList
            items={(pipelineOverview?.top_domains ?? []).slice(0, 10).map((d) => `${d.domain} (${d.count.toLocaleString()})`)}
            emptyText="No domains loaded yet. Import seed data first."
          />
        </div>
      </Panel>

      {/* ── Unified Candidates List ───────────────────────────────── */}
      <div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 12 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 20 }}>All Candidates</h2>
            <span style={{ color: "var(--muted)", fontSize: 13 }}>
              Unified view of pipeline candidates and validated discovery candidates — ranked by score
            </span>
          </div>
          <span style={{ color: "var(--muted)", fontSize: 13 }}>
            {data.discoveryCandidates.length + pipelineCandidates.length} total
          </span>
        </div>

        <div style={{ display: "grid", gap: 16 }}>
          {/* Pipeline Candidates (new system) */}
          {pipelineCandidates.map((candidate) => (
            <article
              key={`pipeline-${candidate.id}`}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 18,
                padding: 16,
                background: "rgba(255,255,255,0.6)",
                display: "grid",
                gap: 10
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", gap: 8, flexWrap: "wrap" }}>
                <div>
                  <strong style={{ fontSize: 17 }}>{candidate.candidate_name}</strong>
                  <div style={{ color: "var(--muted)", fontSize: 13 }}>
                    {[candidate.main_topic, candidate.audience, candidate.problem, candidate.format]
                      .filter(Boolean)
                      .join(" | ")}
                  </div>
                  <div style={{ color: "var(--muted)", fontSize: 12, marginTop: 2 }}>
                    pipeline | template: {candidate.generation_template ?? "—"} | {candidate.marketplace ?? "amazon.de"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", alignItems: "flex-start" }}>
                  <span style={scoreBadgeStyle(candidate.fast_validation_score)}>
                    {candidate.fast_validation_score ?? "n/a"}
                  </span>
                  <Badge>{candidate.status}</Badge>
                  {candidate.book_class_guess ? <Badge>{candidate.book_class_guess}</Badge> : null}
                  {candidate.risk_level ? <Badge>{candidate.risk_level}</Badge> : null}
                </div>
              </div>
              {candidate.promotion_reason && (
                <div style={{ color: "var(--success)", fontSize: 13 }}>{candidate.promotion_reason}</div>
              )}
              {candidate.rejection_reason && (
                <div style={{ color: "var(--danger)", fontSize: 13 }}>{candidate.rejection_reason}</div>
              )}
            </article>
          ))}

          {/* Legacy Discovery Candidates (validated by KDP pipeline) */}
          {data.discoveryCandidates.map((candidate) => (
            <article
              key={`legacy-${candidate.id}`}
              style={{
                border: "1px solid var(--border)",
                borderRadius: 18,
                padding: 16,
                background: candidate.decision === "GO" ? "rgba(0,200,100,0.06)" : "rgba(255,255,255,0.6)",
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
                    validated | {candidate.marketplace} | {candidate.status}
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
          ))}

          {data.discoveryCandidates.length === 0 && pipelineCandidates.length === 0 ? (
            <EmptyState text="No candidates yet. Run the discovery pipeline or generate universe candidates." />
          ) : null}
        </div>
      </div>
    </div>
  );
}
