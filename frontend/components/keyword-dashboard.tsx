import type { CSSProperties } from "react";

import {
  analyzeClusterAction,
  analyzeSachbuchAction,
  collectKeywordAction,
  createKeywordAction,
  expandKeywordAction,
  generateDiscoveryCandidatesAction,
  generateReportAction,
  refreshClusterBsrAction,
  runDiscoveryCycleAction,
  runPipelineAction,
  updateKeywordAction,
  validateDiscoveryCandidateAction
} from "../app/actions";

const browserApiBaseUrl = process.env.KDP_API_BROWSER_URL ?? "http://localhost:8000";

type RuntimeStatus = {
  status: string;
  mode: string;
  requires_authenticated_browser: boolean;
  fetch_mode: string;
  chrome_bridge: {
    enabled: boolean;
    url: string;
    status: string;
    reachable: boolean;
    chrome_debugging_ready: boolean;
    detail: string | null;
    browser?: string | null;
    protocol_version?: string | null;
    user_agent?: string | null;
  };
  browser_automation: {
    enabled: boolean;
    headless: boolean;
    timeout_seconds: number;
    storage_state_path: string;
  };
  recommended_commands: {
    desktop_stack: string;
    bridge_only: string;
  };
};

type Keyword = {
  id: number;
  keyword: string;
  language: string;
  marketplace: string;
  seed_keyword_id: number | null;
  status: string;
  keyword_type: string | null;
  target_audience: string | null;
  category_hint: string | null;
  search_intent_family: string | null;
  specificity_score: number | null;
  intent_score: number | null;
  audience_clarity_score: number | null;
  format_suitability_score: number | null;
  competition_probability_score: number | null;
  production_effort_score: number | null;
  book_type: string | null;
  risk_level: string | null;
  priority: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
};

type Cluster = {
  id: number;
  name: string;
  main_keyword: string | null;
  book_class: string | null;
  status: string;
  latest_final_score: number | null;
};

type Report = {
  id: number;
  niche_cluster_id: number;
  title: string;
  report_type: string;
  markdown_path: string | null;
  pdf_path: string | null;
  csv_path: string | null;
  json_path: string | null;
  status: string;
  created_at: string;
};

type ClusterKeyword = {
  keyword: string;
  relevance_score: number | null;
};

type BookClassInference = {
  book_class: string;
  confidence: number;
  evidence: string[];
  low_content_signal: number;
  medium_content_signal: number;
  high_content_signal: number;
  sachbuch_signal: number;
};

type ClusterTopBook = {
  id: number;
  asin: string;
  title: string | null;
  subtitle: string | null;
  author: string | null;
  publisher: string | null;
  marketplace: string;
  formats: string | null;
  publication_date: string | null;
  page_count: number | null;
  description: string | null;
  cover_url: string | null;
  edition_info: string | null;
  primary_category: string | null;
  secondary_category: string | null;
  tertiary_category: string | null;
  table_of_contents: string | null;
  book_class: string | null;
  created_at: string;
  updated_at: string;
};

type BsrMetrics = {
  snapshot_count: number;
  latest_bsr: number | null;
  average_bsr: number | null;
  median_bsr: number | null;
  volatility: number | null;
  trend: string;
  stability: number | null;
  improvement: number | null;
  decay: number | null;
};

type CompetitorBook = {
  id: number;
  asin: string;
  title: string | null;
  subtitle: string | null;
  author: string | null;
  publisher: string | null;
  cover_url: string | null;
  formats: string | null;
  publication_date: string | null;
  page_count: number | null;
  description: string | null;
  book_class: string | null;
  relevance_score: number | null;
  latest_price: number | null;
  latest_rating: number | null;
  latest_review_count: number | null;
  latest_position: number | null;
  latest_seen_at: string | null;
  edition_info: string | null;
  category_labels: string[];
  listing_target_audience: string | null;
  actual_target_audience: string | null;
  listing_quality_score: number;
  cover_quality_score: number;
  freshness_score: number;
  content_depth_score: number;
  category_fit_score: number;
  publication_age_years: number | null;
  professional_publisher_signal: number;
  series_signal: number;
  sponsored_visibility: number;
  search_observation_count: number;
  review_growth: number | null;
  review_trend: string;
  table_of_contents_excerpt: string | null;
  top_keywords: string[];
  strengths: string[];
  weaknesses: string[];
  semantic_summary: string | null;
  ai_target_audience: string | null;
  ai_core_problem: string | null;
  ai_use_case: string | null;
  ai_promised_outcome: string | null;
  ai_book_format: string | null;
  ai_feature_terms: string[];
  bsr: BsrMetrics;
};

type ReviewInsight = {
  id: number;
  book_id: number;
  cluster_name: string;
  sentiment: string;
  frequency: number | null;
  severity: number | null;
  summary: string | null;
  example_snippets: string | null;
  suggested_improvements: string | null;
  cluster_type: string | null;
  theme_key: string | null;
  semantic_key: string | null;
  source_method: string | null;
  confidence_score: number | null;
  buyer_words: string[] | null;
  audience_hint: string | null;
  missing_feature: string | null;
  evidence_terms: string[] | null;
  created_at: string;
  updated_at: string;
};

type OpportunitySignal = {
  key: string;
  label: string;
  category: string;
  direction: string;
  score: number;
  summary: string;
  evidence: string[];
};

type ClusterDetail = {
  niche_cluster_id: number;
  niche_cluster_name: string;
  main_keyword: string;
  keyword_count: number;
  book_count: number;
  top_keywords: ClusterKeyword[];
  top_complaints: string[];
  top_opportunities: string[];
  positive_review_signals: string[];
  missing_features: string[];
  buyer_words: string[];
  audience_hints: string[];
  recommended_book_class: string | null;
  book_classification: BookClassInference;
  competitor_summary: {
    publisher_concentration: number;
    title_similarity: number;
    low_review_visibility: number;
    new_entrant_visibility: number;
    ad_density: number;
    series_presence: number;
    professional_publisher_share: number;
    strong_competitor_count: number;
    weak_competitor_count: number;
    average_review_count: number;
    average_rating: number | null;
    keyword_repetition: number;
    bsr_snapshot_coverage: number;
    average_listing_quality: number | null;
    average_cover_quality: number | null;
    average_freshness: number | null;
    average_content_depth: number | null;
    average_publication_age_years: number | null;
    category_overlap_score: number | null;
  };
  keyword_strategy: {
    primary_keywords: string[];
    secondary_keywords: string[];
    long_tail_keywords: string[];
    backend_keywords: string[];
    avoid_keywords: string[];
    keyword_clusters: string[];
  };
  category_strategy: {
    possible_categories: string[];
    category_relevance: string[];
    category_risks: string[];
    visibility_opportunities: string[];
  };
  top_books: ClusterTopBook[];
  competitor_books: CompetitorBook[];
  review_insights: ReviewInsight[];
  signals: OpportunitySignal[];
  score: {
    keyword_specificity_score: number | null;
    new_entrant_signal: number | null;
    review_insight_score: number | null;
    demand_score: number | null;
    saturation_risk: number | null;
    entry_feasibility_score: number | null;
    review_wall_risk: number | null;
    differentiation_score: number | null;
    ai_slop_score: number | null;
    brand_dominance_risk: number | null;
    content_complexity_risk: number | null;
    compliance_risk: number | null;
    price_compression_risk: number | null;
    authority_risk: number | null;
    research_effort_score: number | null;
    final_score: number | null;
    explanation: string | null;
  };
};

type SachbuchAnalysis = {
  niche_cluster_id: number;
  niche_cluster_name: string;
  main_keyword: string;
  opportunity_score: number | null;
  sachbuch_score: {
    german_demand_signal: number | null;
    topic_gap_signal: number | null;
    depth_weakness_signal: number | null;
    freshness_need_signal: number | null;
    localization_signal: number | null;
    differentiation_signal: number | null;
    evergreen_potential_signal: number | null;
    monetization_potential_signal: number | null;
    authority_risk: number | null;
    research_effort_risk: number | null;
    liability_risk: number | null;
    update_risk: number | null;
    publisher_dominance_risk: number | null;
    review_wall_risk: number | null;
    final_score: number | null;
    explanation: string | null;
    quality_warnings: string[];
  };
  go_decision: string;
  inferred_book_class: string;
  book_class_confidence: number;
  classification_evidence: string[];
  recommended_target_audience: string;
  reader_problem: string;
  reader_promise: string;
  why_now: string;
  subtitle_ideas: string[];
  positioning_angles: string[];
  differentiation_opportunities: string[];
  chapter_blueprint: string[];
  subchapter_blueprint: string[];
  practice_modules: string[];
  checklist_ideas: string[];
  case_study_ideas: string[];
  glossary_terms: string[];
  research_questions: string[];
  backend_keywords: string[];
  category_strategy: string[];
  source_requirements: string[];
  expert_needs: string[];
  quality_warnings: string[];
  cover_direction: string[];
  target_length: string;
  writing_effort: string;
  signals: OpportunitySignal[];
  topic_gap: {
    id: number;
    niche_cluster_id: number;
    topic_gap_summary: string | null;
    outdated_content_signal: number | null;
    missing_examples_signal: number | null;
    missing_checklists_signal: number | null;
    localization_gap_signal: number | null;
    content_depth_score: number | null;
    authority_required: boolean;
    expert_review_required: boolean;
    created_at: string;
    updated_at: string;
  };
};

type DiscoveryUniverseItem = {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  priority: number;
  active: boolean;
  category_hint?: string | null;
  book_type_hint?: string | null;
  risk_level?: string | null;
};

type DiscoveryUniverse = {
  topics: DiscoveryUniverseItem[];
  audiences: DiscoveryUniverseItem[];
  pain_points: DiscoveryUniverseItem[];
  contexts: DiscoveryUniverseItem[];
  book_formats: DiscoveryUniverseItem[];
};

type DiscoveryCandidate = {
  id: number;
  topic: string;
  audience: string | null;
  pain_point: string | null;
  context: string | null;
  book_format: string | null;
  candidate_phrase: string;
  language: string;
  marketplace: string;
  book_type_hint: string | null;
  validated_book_type: string | null;
  risk_level: string | null;
  status: string;
  generation_score: number | null;
  specificity_score: number | null;
  intent_score: number | null;
  audience_clarity_score: number | null;
  format_suitability_score: number | null;
  competition_probability_score: number | null;
  production_effort_score: number | null;
  pain_clarity_score: number | null;
  validated_target_audience: string | null;
  demand_score: number | null;
  competition_score: number | null;
  gap_score: number | null;
  production_difficulty_score: number | null;
  risk_score: number | null;
  final_opportunity_score: number | null;
  decision: string | null;
  keyword_id: number | null;
  niche_cluster_id: number | null;
  relevant_book_count: number | null;
  related_keyword_count: number | null;
  top_competitor_review_median: number | null;
  bsr_coverage: number | null;
  report_count: number;
  market_summary: string | null;
  gap_summary: string | null;
  reason_summary: string | null;
  recommended_angle: string | null;
  validation_notes: string | null;
  signals: OpportunitySignal[];
  created_at: string;
  updated_at: string;
  last_validated_at: string | null;
};

type KeywordDashboardProps = {
  keywords: Keyword[];
  clusters: Cluster[];
  reports: Report[];
  runtimeStatus: RuntimeStatus | null;
  discoveryUniverse: DiscoveryUniverse | null;
  discoveryCandidates: DiscoveryCandidate[];
  clusterDetails: ClusterDetail[];
  sachbuchAnalyses: SachbuchAnalysis[];
};

export function KeywordDashboard({
  keywords,
  clusters,
  reports,
  runtimeStatus,
  discoveryUniverse,
  discoveryCandidates,
  clusterDetails,
  sachbuchAnalyses
}: KeywordDashboardProps) {
  const seedKeywords = keywords.filter(
    (keyword) => keyword.seed_keyword_id === null && keyword.status !== "ignored"
  );
  const expandedKeywords = keywords.filter(
    (keyword) => keyword.seed_keyword_id !== null && keyword.status !== "ignored"
  );
  const prioritizedKeywords = keywords.filter((keyword) => keyword.priority >= 80).length;
  const ignoredKeywords = keywords.filter((keyword) => keyword.status === "ignored").length;
  const detailByClusterId = new Map(clusterDetails.map((detail) => [detail.niche_cluster_id, detail]));
  const sachbuchByClusterId = new Map(
    sachbuchAnalyses.map((analysis) => [analysis.niche_cluster_id, analysis])
  );
  const competitorEntries = clusterDetails.flatMap((detail) =>
    detail.competitor_books.slice(0, 2).map((book) => ({
      clusterName: detail.niche_cluster_name,
      book
    }))
  );
  const reviewHighlights = clusterDetails.flatMap((detail) =>
    detail.review_insights.slice(0, 2).map((insight) => ({
      clusterName: detail.niche_cluster_name,
      insight
    }))
  );
  const validatedDiscoveryCount = discoveryCandidates.filter(
    (candidate) => candidate.status === "validated"
  ).length;
  const goDiscoveryCount = discoveryCandidates.filter(
    (candidate) => candidate.decision === "GO"
  ).length;
  const runtimeBridgeReady = Boolean(
    runtimeStatus?.chrome_bridge.reachable && runtimeStatus?.chrome_bridge.chrome_debugging_ready
  );
  const runtimeStatusLabel = runtimeBridgeReady
    ? "Desktop ready"
    : runtimeStatus?.status === "degraded"
      ? "Desktop attention needed"
      : "Desktop offline";

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <section
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) minmax(0, 1fr)",
          gap: 24
        }}
      >
        <aside style={panelStyle}>
          <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24 }}>Idea Discovery</h2>
          <p style={{ marginTop: 0, color: "var(--muted)", lineHeight: 1.6 }}>
            Mode 2 creates niche candidates from reusable German building blocks,
            then validates them through the same Amazon.de pipeline and cluster
            scoring stack used for manual ideas.
          </p>

          <div style={desktopRuntimeCardStyle(runtimeBridgeReady)}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div style={{ display: "grid", gap: 6 }}>
                <span style={sectionLabelStyle}>Desktop Runtime</span>
                <strong style={{ fontSize: 18 }}>{runtimeStatusLabel}</strong>
                <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                  Authenticated Amazon collection runs through your local Chrome session via
                  the host bridge. This workflow is intended to run on the desktop.
                </span>
              </div>
              <span style={runtimeBadgeStyle(runtimeStatus?.status ?? "offline")}>
                {runtimeStatus?.status ?? "offline"}
              </span>
            </div>

            <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 14 }}>
              <span style={metricBadgeStyle}>mode {runtimeStatus?.mode ?? "unknown"}</span>
              <span style={metricBadgeStyle}>fetch {runtimeStatus?.fetch_mode ?? "unknown"}</span>
              <span style={metricBadgeStyle}>
                bridge {runtimeStatus?.chrome_bridge.status ?? "offline"}
              </span>
              <span style={metricBadgeStyle}>
                {runtimeStatus?.browser_automation.enabled ? "browser fallback on" : "browser fallback off"}
              </span>
            </div>

            {runtimeBridgeReady ? (
              <div style={{ display: "grid", gap: 6, marginTop: 14 }}>
                <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                  Bridge URL: {runtimeStatus?.chrome_bridge.url}
                </span>
                {runtimeStatus?.chrome_bridge.browser ? (
                  <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                    Browser: {runtimeStatus?.chrome_bridge.browser}
                  </span>
                ) : null}
              </div>
            ) : (
              <div style={{ display: "grid", gap: 8, marginTop: 14 }}>
                <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                  Start the desktop runtime before running discovery or validation:
                </span>
                <code style={commandStyle}>
                  {runtimeStatus?.recommended_commands.desktop_stack ?? ".\\scripts\\start_desktop_stack.ps1 -Build"}
                </code>
                <code style={commandStyle}>
                  {runtimeStatus?.recommended_commands.bridge_only ?? ".\\scripts\\start_chrome_bridge.ps1"}
                </code>
                {runtimeStatus?.chrome_bridge.detail ? (
                  <span style={{ color: "#8a2323", fontSize: 13, lineHeight: 1.5 }}>
                    Bridge detail: {runtimeStatus?.chrome_bridge.detail}
                  </span>
                ) : null}
              </div>
            )}
          </div>

          <div style={{ display: "flex", gap: 10, flexWrap: "wrap", marginTop: 18 }}>
            <span style={metricBadgeStyle}>{discoveryUniverse?.topics.length ?? 0} topics</span>
            <span style={metricBadgeStyle}>{discoveryUniverse?.audiences.length ?? 0} audiences</span>
            <span style={metricBadgeStyle}>{discoveryUniverse?.pain_points.length ?? 0} pains</span>
            <span style={metricBadgeStyle}>{validatedDiscoveryCount} validated</span>
            <span style={metricBadgeStyle}>{goDiscoveryCount} GO</span>
          </div>

          <div style={{ display: "grid", gap: 10, marginTop: 18 }}>
            <form action={generateDiscoveryCandidatesAction}>
              <input type="hidden" name="limit" value="120" />
              <button type="submit" style={primaryButtonStyle}>
                Generate 120 Candidates
              </button>
            </form>
            <form action={runDiscoveryCycleAction}>
              <input type="hidden" name="generateLimit" value="120" />
              <input type="hidden" name="validateLimit" value="6" />
              <input type="hidden" name="autoGenerateReports" value="true" />
              <input type="hidden" name="force" value="false" />
              <button type="submit" style={secondaryButtonStyle}>
                Run Discovery Cycle
              </button>
            </form>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            <div style={{ display: "grid", gap: 8 }}>
              <span style={sectionLabelStyle}>Priority Topics</span>
              <CompactList
                items={(discoveryUniverse?.topics ?? []).slice(0, 5).map((item) => item.name)}
                emptyText="No discovery universe loaded yet."
              />
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              <span style={sectionLabelStyle}>Pain Blocks</span>
              <CompactList
                items={(discoveryUniverse?.pain_points ?? []).slice(0, 5).map((item) => item.name)}
                emptyText="No pain-point blocks loaded yet."
              />
            </div>
            <div style={{ display: "grid", gap: 8 }}>
              <span style={sectionLabelStyle}>Book Formats</span>
              <CompactList
                items={(discoveryUniverse?.book_formats ?? []).slice(0, 5).map((item) => item.name)}
                emptyText="No format blocks loaded yet."
              />
            </div>
          </div>
        </aside>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Discovery Candidates</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Automatically generated ideas ranked by specificity first, then by
                validated demand, beatability, market gap, and risk.
              </p>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <span style={metricBadgeStyle}>{discoveryCandidates.length} visible</span>
              <span style={metricBadgeStyle}>{validatedDiscoveryCount} validated</span>
              <span style={metricBadgeStyle}>{goDiscoveryCount} GO</span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {discoveryCandidates.length === 0 ? (
              <EmptyState text="No discovery candidates exist yet. Generate a batch or run a full discovery cycle." />
            ) : (
              discoveryCandidates.map((candidate) => (
                <article key={candidate.id} style={clusterCardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "grid", gap: 6 }}>
                      <strong style={{ fontSize: 18 }}>{candidate.candidate_phrase}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                        {[candidate.topic, candidate.audience, candidate.context, candidate.book_format]
                          .filter(Boolean)
                          .join(" | ")}
                      </span>
                      <span style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.5 }}>
                        {candidate.marketplace} | {candidate.status} | reports {candidate.report_count}
                        {candidate.last_validated_at
                          ? ` | last checked ${formatDateTime(candidate.last_validated_at)}`
                          : ""}
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
                        <span style={pillStyle}>
                          {candidate.validated_book_type ?? candidate.book_type_hint}
                        </span>
                      ) : null}
                      {candidate.risk_level ? <span style={pillStyle}>{candidate.risk_level}</span> : null}
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(6, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Idea" value={candidate.generation_score} />
                    <MetricTile label="Demand" value={candidate.demand_score} />
                    <MetricTile label="Beatable" value={candidate.competition_score} />
                    <MetricTile label="Gap" value={candidate.gap_score} />
                    <MetricTile label="Risk" value={candidate.risk_score} />
                    <MetricTile label="Final" value={candidate.final_opportunity_score} />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Books" value={candidate.relevant_book_count} />
                    <MetricTile label="Keywords" value={candidate.related_keyword_count} />
                    <MetricTile label="Median Reviews" value={candidate.top_competitor_review_median} />
                    <MetricTile label="BSR Coverage" value={candidate.bsr_coverage} />
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Why It Ranks Here</span>
                    <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.6 }}>
                      {candidate.reason_summary ?? candidate.market_summary ?? "Validation summary not stored yet."}
                    </span>
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Signal Snapshot</span>
                    <SignalSnapshot
                      signals={candidate.signals}
                      emptyText="No validated signals stored yet."
                    />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Market Read</span>
                      <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.6 }}>
                        {candidate.market_summary ?? "No market summary stored yet."}
                      </span>
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Gap / Angle</span>
                      <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.6 }}>
                        {candidate.recommended_angle ?? candidate.gap_summary ?? "No clear angle stored yet."}
                      </span>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <form action={validateDiscoveryCandidateAction}>
                      <input type="hidden" name="candidateId" value={candidate.id} />
                      <input type="hidden" name="autoGenerateReports" value="true" />
                      <input type="hidden" name="force" value="false" />
                      <button type="submit" style={secondaryButtonStyle}>
                        {candidate.status === "validated" ? "Reuse Validation" : "Validate"}
                      </button>
                    </form>
                    <form action={validateDiscoveryCandidateAction}>
                      <input type="hidden" name="candidateId" value={candidate.id} />
                      <input type="hidden" name="autoGenerateReports" value="true" />
                      <input type="hidden" name="force" value="true" />
                      <button type="submit" style={secondaryButtonStyle}>
                        Re-validate
                      </button>
                    </form>
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) minmax(0, 1fr)",
          gap: 24
        }}
      >
        <aside style={panelStyle}>
          <h2 style={{ marginTop: 0, marginBottom: 12, fontSize: 24 }}>Seed Keywords</h2>
          <p style={{ marginTop: 0, color: "var(--muted)", lineHeight: 1.6 }}>
            Add a German niche idea, expand it into long-tail phrases, and run the
            first Amazon.de capture plus cluster analysis.
          </p>

          <form action={createKeywordAction} style={{ display: "grid", gap: 12, marginTop: 18 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Keyword</span>
              <input
                name="keyword"
                type="text"
                placeholder="Blutdrucktagebuch"
                style={inputStyle}
                required
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Target Audience</span>
              <input
                name="targetAudience"
                type="text"
                placeholder="z. B. Senioren, Selbstständige, Eltern"
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Category Hint</span>
              <input
                name="categoryHint"
                type="text"
                placeholder="z. B. Gesundheit und Dokumentation"
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Book Type</span>
              <select name="bookType" style={inputStyle}>
                <option value="">Unclassified</option>
                <option value="low_content">Low Content</option>
                <option value="medium_content">Medium Content</option>
                <option value="sachbuch">Sachbuch</option>
              </select>
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Priority</span>
              <input
                name="priority"
                type="number"
                min="0"
                max="100"
                defaultValue="40"
                style={inputStyle}
              />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Notes</span>
              <textarea
                name="notes"
                rows={3}
                placeholder="Optional niche context, risks, or product angle."
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </label>

            <button type="submit" style={primaryButtonStyle}>
              Add Seed Keyword
            </button>
          </form>

          <div style={{ marginTop: 22, display: "grid", gap: 12 }}>
            {seedKeywords.length === 0 ? (
              <EmptyState text="No fresh seed keywords are waiting." />
            ) : (
              seedKeywords.map((keyword) => (
                <article key={keyword.id} style={keywordCardStyle}>
                  <div style={{ display: "grid", gap: 6 }}>
                    <strong style={{ fontSize: 18 }}>{keyword.keyword}</strong>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <span style={pillStyle}>{keyword.book_type ?? "unclassified"}</span>
                      <span style={pillStyle}>prio: {keyword.priority}</span>
                      {keyword.search_intent_family ? <span style={pillStyle}>{keyword.search_intent_family}</span> : null}
                    </div>
                    <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                      {keyword.target_audience ?? "Audience inferred later"} | {keyword.category_hint ?? "No category hint"}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.5 }}>
                      Specificity {keyword.specificity_score ?? "n/a"} | Intent {keyword.intent_score ?? "n/a"} | Audience {keyword.audience_clarity_score ?? "n/a"}
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    <form action={expandKeywordAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <button type="submit" style={secondaryButtonStyle}>
                        Expand
                      </button>
                    </form>
                    <form action={collectKeywordAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <button type="submit" style={secondaryButtonStyle}>
                        Collect
                      </button>
                    </form>
                    <form action={runPipelineAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <button type="submit" style={secondaryButtonStyle}>
                        Pipeline
                      </button>
                    </form>
                    <form action={analyzeClusterAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <button type="submit" style={secondaryButtonStyle}>
                        Cluster
                      </button>
                    </form>
                    <form action={updateKeywordAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <input type="hidden" name="status" value="prioritized" />
                      <input type="hidden" name="priority" value="100" />
                      <button type="submit" style={secondaryButtonStyle}>
                        Prioritize
                      </button>
                    </form>
                    <form action={updateKeywordAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <input type="hidden" name="status" value="ignored" />
                      <input type="hidden" name="priority" value="0" />
                      <button type="submit" style={secondaryButtonStyle}>
                        Ignore
                      </button>
                    </form>
                  </div>
                </article>
              ))
            )}
          </div>
        </aside>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Keyword Inventory</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Expanded phrases are persisted as child keywords and remain available
                for later clustering and re-runs.
              </p>
            </div>
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <span style={metricBadgeStyle}>{keywords.length} total</span>
              <span style={metricBadgeStyle}>{expandedKeywords.length} expanded</span>
              <span style={metricBadgeStyle}>{prioritizedKeywords} prioritized</span>
              <span style={metricBadgeStyle}>{ignoredKeywords} ignored</span>
            </div>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {keywords.length === 0 ? (
              <EmptyState text="The dashboard is live, but no keyword records exist yet." />
            ) : (
              keywords.map((keyword) => (
                <article key={keyword.id} style={inventoryRowStyle}>
                  <div style={{ display: "grid", gap: 4 }}>
                    <strong>{keyword.keyword}</strong>
                    <span style={{ color: "var(--muted)", fontSize: 14 }}>
                      {keyword.marketplace} | {keyword.language} | {keyword.status} | prio {keyword.priority}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.5 }}>
                      {(keyword.target_audience ?? "No audience")} | {(keyword.category_hint ?? "No category")} | {(keyword.search_intent_family ?? "No intent family")}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.5 }}>
                      Spec {keyword.specificity_score ?? "n/a"} | Intent {keyword.intent_score ?? "n/a"} | Format {keyword.format_suitability_score ?? "n/a"} | Competition {keyword.competition_probability_score ?? "n/a"} | Effort {keyword.production_effort_score ?? "n/a"}
                    </span>
                  </div>
                  <div
                    style={{
                      display: "flex",
                      gap: 8,
                      flexWrap: "wrap",
                      justifyContent: "flex-end"
                    }}
                  >
                    {keyword.keyword_type ? <span style={pillStyle}>{keyword.keyword_type}</span> : null}
                    {keyword.book_type ? <span style={pillStyle}>{keyword.book_type}</span> : null}
                    {keyword.risk_level ? <span style={pillStyle}>{keyword.risk_level}</span> : null}
                    <form action={updateKeywordAction}>
                      <input type="hidden" name="keywordId" value={keyword.id} />
                      <input type="hidden" name="status" value={keyword.seed_keyword_id === null ? "new" : "expanded"} />
                      <input type="hidden" name="priority" value="100" />
                      <button type="submit" style={secondaryButtonStyle}>
                        Prioritize
                      </button>
                    </form>
                    {keyword.status === "ignored" ? (
                      <form action={updateKeywordAction}>
                        <input type="hidden" name="keywordId" value={keyword.id} />
                        <input type="hidden" name="status" value={keyword.seed_keyword_id === null ? "new" : "expanded"} />
                        <input type="hidden" name="priority" value="40" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Restore
                        </button>
                      </form>
                    ) : (
                      <form action={updateKeywordAction}>
                        <input type="hidden" name="keywordId" value={keyword.id} />
                        <input type="hidden" name="status" value="ignored" />
                        <input type="hidden" name="priority" value="0" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Ignore
                        </button>
                      </form>
                    )}
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 24
        }}
      >
        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Niche Explorer</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Opportunity, demand, saturation, competitor pain points, and direct
                report or sachbuch actions per cluster.
              </p>
            </div>
            <span style={metricBadgeStyle}>{clusters.length} clusters</span>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {clusters.length === 0 ? (
              <EmptyState text="Run the pipeline to populate the niche explorer." />
            ) : (
              clusters.map((cluster) => {
                const detail = detailByClusterId.get(cluster.id);
                const sachbuch = sachbuchByClusterId.get(cluster.id);

                return (
                  <article key={cluster.id} style={clusterCardStyle}>
                    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                      <div style={{ display: "grid", gap: 6 }}>
                        <strong style={{ fontSize: 18 }}>{cluster.name}</strong>
                        <span style={{ color: "var(--muted)", fontSize: 14 }}>
                          {(cluster.main_keyword ?? cluster.name)} | {cluster.status}
                        </span>
                      </div>
                      <span style={scoreBadgeStyle(cluster.latest_final_score)}>
                        {cluster.latest_final_score ?? "n/a"}
                      </span>
                    </div>

                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {cluster.book_class ? <span style={pillStyle}>{cluster.book_class}</span> : null}
                      {detail?.recommended_book_class ? (
                        <span style={pillStyle}>rec: {detail.recommended_book_class}</span>
                      ) : null}
                      {detail ? (
                        <span style={pillStyle}>conf: {detail.book_classification.confidence}</span>
                      ) : null}
                      {sachbuch ? <span style={decisionBadgeStyle(sachbuch.go_decision)}>{sachbuch.go_decision}</span> : null}
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
                          <MetricTile label="Pub. Conc." value={detail.competitor_summary.publisher_concentration} />
                          <MetricTile label="Title Sim." value={detail.competitor_summary.title_similarity} />
                          <MetricTile label="New Entrants" value={detail.competitor_summary.new_entrant_visibility} />
                          <MetricTile label="BSR Coverage" value={detail.competitor_summary.bsr_snapshot_coverage} />
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                          <MetricTile label="List. Q." value={detail.competitor_summary.average_listing_quality} />
                          <MetricTile label="Cover Q." value={detail.competitor_summary.average_cover_quality} />
                          <MetricTile label="Freshness" value={detail.competitor_summary.average_freshness} />
                          <MetricTile label="Cat. Overlap" value={detail.competitor_summary.category_overlap_score} />
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                          <MetricTile label="Ads" value={detail.competitor_summary.ad_density} />
                          <MetricTile label="Series" value={detail.competitor_summary.series_presence} />
                          <MetricTile label="Pro Pub." value={detail.competitor_summary.professional_publisher_share} />
                          <MetricTile label="Age (y)" value={detail.competitor_summary.average_publication_age_years} />
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                          <MetricTile label="Specificity" value={detail.score.keyword_specificity_score} />
                          <MetricTile label="Review IQ" value={detail.score.review_insight_score} />
                          <MetricTile label="Brand Risk" value={detail.score.brand_dominance_risk} />
                          <MetricTile label="Compliance" value={detail.score.compliance_risk} />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Signal Snapshot</span>
                          <SignalSnapshot
                            signals={detail.signals}
                            emptyText="No cluster signals stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Classification Evidence</span>
                          <CompactList
                            items={detail.book_classification.evidence}
                            emptyText="No classification evidence stored."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Top Keywords</span>
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            {detail.top_keywords.slice(0, 5).map((keyword) => (
                              <span key={`${cluster.id}-${keyword.keyword}`} style={pillStyle}>
                                {keyword.keyword}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Top Complaints</span>
                          <CompactList
                            items={detail.top_complaints}
                            emptyText="No complaint clusters stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Top Opportunities</span>
                          <CompactList
                            items={detail.top_opportunities}
                            emptyText="No differentiation suggestions stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Buyer Language</span>
                          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                            {detail.buyer_words.length === 0 ? (
                              <span style={{ color: "var(--muted)", fontSize: 14 }}>No buyer vocabulary stored.</span>
                            ) : (
                              detail.buyer_words.map((word) => (
                                <span key={`${cluster.id}-${word}`} style={pillStyle}>
                                  {word}
                                </span>
                              ))
                            )}
                          </div>
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Audience Hints</span>
                          <CompactList
                            items={detail.audience_hints}
                            emptyText="No audience hints stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Keyword Strategy</span>
                          <CompactList
                            items={detail.keyword_strategy.backend_keywords}
                            emptyText="No backend keyword strategy stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Category Strategy</span>
                          <CompactList
                            items={detail.category_strategy.visibility_opportunities}
                            emptyText="No category strategy stored yet."
                          />
                        </div>

                        <div style={{ display: "grid", gap: 8 }}>
                          <span style={sectionLabelStyle}>Top Books</span>
                          <CompactList
                            items={detail.top_books.slice(0, 3).map((book) => book.title || book.asin)}
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
                        <button type="submit" style={secondaryButtonStyle}>
                          Refresh BSR
                        </button>
                      </form>
                      <form action={generateReportAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <input type="hidden" name="reportType" value="niche_report" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Niche Report
                        </button>
                      </form>
                      <form action={generateReportAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <input type="hidden" name="reportType" value="book_concept_report" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Concept
                        </button>
                      </form>
                      <form action={generateReportAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <input type="hidden" name="reportType" value="keyword_report" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Keyword
                        </button>
                      </form>
                      <form action={generateReportAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <input type="hidden" name="reportType" value="competitor_report" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Competitor
                        </button>
                      </form>
                      <form action={generateReportAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <input type="hidden" name="reportType" value="go_no_go_report" />
                        <button type="submit" style={secondaryButtonStyle}>
                          Go/No-Go
                        </button>
                      </form>
                      <form action={analyzeSachbuchAction}>
                        <input type="hidden" name="clusterId" value={cluster.id} />
                        <button type="submit" style={secondaryButtonStyle}>
                          Sachbuch Gap
                        </button>
                      </form>
                    </div>
                  </article>
                );
              })
            )}
          </div>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Report Builder</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Generated artifact inventory from the report pipeline.
              </p>
            </div>
            <span style={metricBadgeStyle}>{reports.length} reports</span>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {reports.length === 0 ? (
              <EmptyState text="No reports generated yet." />
            ) : (
              reports.map((report) => (
                <article key={report.id} style={reportCardStyle}>
                  <div style={{ display: "grid", gap: 4 }}>
                    <strong>{report.title}</strong>
                    <span style={{ color: "var(--muted)", fontSize: 14 }}>
                      Cluster #{report.niche_cluster_id} | {report.report_type} | {report.status}
                    </span>
                  </div>
                  <div style={{ display: "grid", gap: 4, color: "var(--muted)", fontSize: 13 }}>
                    <span>Markdown: {report.markdown_path ?? "pending"}</span>
                    <span>CSV: {report.csv_path ?? "pending"}</span>
                    <span>JSON: {report.json_path ?? "pending"}</span>
                    <span>PDF: {report.pdf_path ?? "pending"}</span>
                  </div>
                  <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                    {report.markdown_path ? (
                      <a href={reportArtifactHref(report.id, "markdown")} style={linkButtonStyle}>
                        Markdown
                      </a>
                    ) : null}
                    {report.csv_path ? (
                      <a href={reportArtifactHref(report.id, "csv")} style={linkButtonStyle}>
                        CSV
                      </a>
                    ) : null}
                    {report.json_path ? (
                      <a href={reportArtifactHref(report.id, "json")} style={linkButtonStyle}>
                        JSON
                      </a>
                    ) : null}
                    {report.pdf_path ? (
                      <a href={reportArtifactHref(report.id, "pdf")} style={linkButtonStyle}>
                        PDF
                      </a>
                    ) : null}
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 24
        }}
      >
        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Competitor View</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Latest visible competitor signals with BSR snapshots, review counts,
                strengths, weaknesses, and keyword overlap.
              </p>
            </div>
            <span style={metricBadgeStyle}>{competitorEntries.length} visible books</span>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {competitorEntries.length === 0 ? (
              <EmptyState text="Competitor snapshots will appear once clusters contain enriched books." />
            ) : (
              competitorEntries.map(({ clusterName, book }) => (
                <article key={`${clusterName}-${book.id}`} style={competitorCardStyle}>
                  <div style={{ display: "grid", gridTemplateColumns: "72px minmax(0, 1fr)", gap: 14 }}>
                    <div style={coverFrameStyle}>
                      {book.cover_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                          src={book.cover_url}
                          alt={book.title ?? book.asin}
                          style={{ width: "100%", height: "100%", objectFit: "cover" }}
                        />
                      ) : (
                        <span style={{ color: "var(--muted)", fontSize: 12 }}>No cover</span>
                      )}
                    </div>
                    <div style={{ display: "grid", gap: 6 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
                        <strong>{book.title ?? book.asin}</strong>
                        <span style={metricBadgeStyle}>#{book.latest_position ?? "n/a"}</span>
                      </div>
                      <span style={{ color: "var(--muted)", fontSize: 13 }}>
                        {clusterName} | {book.author ?? "n/a"} | {book.publisher ?? "n/a"}
                      </span>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
                        <MetricTile label="Reviews" value={book.latest_review_count} />
                        <MetricTile label="BSR" value={book.bsr.latest_bsr} />
                        <MetricTile label="Stability" value={book.bsr.stability} />
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                        <MetricTile label="List. Q." value={book.listing_quality_score} />
                        <MetricTile label="Cover Q." value={book.cover_quality_score} />
                        <MetricTile label="Depth" value={book.content_depth_score} />
                        <MetricTile label="Fresh" value={book.freshness_score} />
                      </div>
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                        <MetricTile label="Ads" value={book.sponsored_visibility} />
                        <MetricTile label="Series" value={book.series_signal} />
                        <MetricTile label="Pro Pub." value={book.professional_publisher_signal} />
                        <MetricTile label="Age (y)" value={book.publication_age_years} />
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {book.top_keywords.map((keyword) => (
                      <span key={`${book.id}-${keyword}`} style={pillStyle}>
                        {keyword}
                      </span>
                    ))}
                    {book.category_labels.map((category) => (
                      <span key={`${book.id}-${category}`} style={metricBadgeStyle}>
                        {category}
                      </span>
                    ))}
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Strengths</span>
                      <CompactList items={book.strengths} emptyText="No positive review signal stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Weaknesses</span>
                      <CompactList items={book.weaknesses} emptyText="No negative review signal stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Price" value={formatPrice(book.latest_price)} />
                    <MetricTile label="Trend" value={book.bsr.trend} />
                    <MetricTile label="Snapshots" value={book.bsr.snapshot_count} />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(3, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Review Trend" value={book.review_trend} />
                    <MetricTile label="Review Growth" value={book.review_growth} />
                    <MetricTile label="Observations" value={book.search_observation_count} />
                  </div>

                  {(book.ai_target_audience || book.ai_core_problem || book.ai_use_case || book.ai_promised_outcome) ? (
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>AI Extraction</span>
                      <div style={{ display: "grid", gap: 4, color: "var(--muted)", fontSize: 14 }}>
                        {book.ai_target_audience ? <span>Audience: {book.ai_target_audience}</span> : null}
                        {book.ai_core_problem ? <span>Problem: {book.ai_core_problem}</span> : null}
                        {book.ai_use_case ? <span>Use case: {book.ai_use_case}</span> : null}
                        {book.ai_promised_outcome ? <span>Promise: {book.ai_promised_outcome}</span> : null}
                        {book.semantic_summary ? <span>Summary: {book.semantic_summary}</span> : null}
                      </div>
                    </div>
                  ) : null}

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Target Audience</span>
                      <CompactList
                        items={[
                          `Listing: ${book.listing_target_audience ?? "n/a"}`,
                          `Reviews: ${book.actual_target_audience ?? "n/a"}`,
                          `AI: ${book.ai_target_audience ?? "n/a"}`,
                          `Edition: ${book.edition_info ?? "n/a"}`
                        ]}
                        emptyText="No audience signals stored."
                      />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>TOC Signal</span>
                      <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                        {book.table_of_contents_excerpt ?? "No table-of-contents excerpt stored."}
                      </span>
                    </div>
                  </div>

                  {book.ai_feature_terms.length > 0 ? (
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>AI Feature Terms</span>
                      <CompactList items={book.ai_feature_terms} emptyText="No extracted feature terms stored." />
                    </div>
                  ) : null}
                </article>
              ))
            )}
          </div>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Review Intelligence</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Positive and negative review clusters, repeated complaints, and
                concrete improvement signals across the active niches.
              </p>
            </div>
            <span style={metricBadgeStyle}>{reviewHighlights.length} signals</span>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {reviewHighlights.length === 0 ? (
              <EmptyState text="Review clusters will appear after review collection and analysis." />
            ) : (
              reviewHighlights.map(({ clusterName, insight }) => (
                <article key={`${clusterName}-${insight.id}`} style={reportCardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong>{insight.cluster_name}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 13 }}>{clusterName}</span>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      <span style={sentimentBadgeStyle(insight.sentiment)}>{insight.sentiment}</span>
                      {insight.cluster_type ? <span style={metricBadgeStyle}>{insight.cluster_type}</span> : null}
                      {insight.confidence_score !== null ? (
                        <span style={metricBadgeStyle}>confidence {insight.confidence_score}</span>
                      ) : null}
                      {insight.frequency !== null ? <span style={metricBadgeStyle}>freq {insight.frequency}</span> : null}
                    </div>
                  </div>
                  <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                    {insight.summary ?? "No summary stored."}
                  </p>
                  {insight.audience_hint || insight.missing_feature ? (
                    <div style={{ display: "grid", gap: 4, color: "var(--muted)", fontSize: 14 }}>
                      {insight.audience_hint ? <span>Audience hint: {insight.audience_hint}</span> : null}
                      {insight.missing_feature ? <span>Missing feature: {insight.missing_feature}</span> : null}
                    </div>
                  ) : null}
                  {insight.buyer_words && insight.buyer_words.length > 0 ? (
                    <div style={{ display: "grid", gap: 6 }}>
                      <span style={sectionLabelStyle}>Buyer Words</span>
                      <CompactList items={insight.buyer_words} emptyText="No buyer wording stored." />
                    </div>
                  ) : null}
                  {insight.suggested_improvements ? (
                    <div style={{ display: "grid", gap: 6 }}>
                      <span style={sectionLabelStyle}>Improvement</span>
                      <span style={{ color: "var(--muted)", fontSize: 14 }}>
                        {insight.suggested_improvements}
                      </span>
                    </div>
                  ) : null}
                </article>
              ))
            )}
          </div>
        </div>
      </section>

      <section
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 24
        }}
      >
        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div>
              <h2 style={{ marginTop: 0, marginBottom: 8, fontSize: 24 }}>Sachbuch Explorer</h2>
              <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                Topic gaps, localization needs, authority risk, research burden, and
                live chapter-blueprint guidance for true sachbuch spaces.
              </p>
            </div>
            <span style={metricBadgeStyle}>{sachbuchAnalyses.length} analyses</span>
          </div>

          <div style={{ display: "grid", gap: 12, marginTop: 22 }}>
            {sachbuchAnalyses.length === 0 ? (
              <EmptyState text="No persisted sachbuch analyses are available yet." />
            ) : (
              sachbuchAnalyses.map((analysis) => (
                <article key={analysis.niche_cluster_id} style={clusterCardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong style={{ fontSize: 18 }}>{analysis.niche_cluster_name}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 14 }}>
                        Audience: {analysis.recommended_target_audience} | {analysis.inferred_book_class} ({analysis.book_class_confidence})
                      </span>
                    </div>
                    <span style={decisionBadgeStyle(analysis.go_decision)}>{analysis.go_decision}</span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Outdated" value={analysis.topic_gap.outdated_content_signal} />
                    <MetricTile label="Examples" value={analysis.topic_gap.missing_examples_signal} />
                    <MetricTile label="Checklists" value={analysis.topic_gap.missing_checklists_signal} />
                    <MetricTile label="Localization" value={analysis.topic_gap.localization_gap_signal} />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10 }}>
                    <MetricTile label="Sachbuch" value={analysis.sachbuch_score.final_score} />
                    <MetricTile label="Liability" value={analysis.sachbuch_score.liability_risk} />
                    <MetricTile label="Update" value={analysis.sachbuch_score.update_risk} />
                    <MetricTile label="Evergreen" value={analysis.sachbuch_score.evergreen_potential_signal} />
                  </div>

                  <p style={{ margin: 0, color: "var(--muted)", lineHeight: 1.6 }}>
                    {analysis.topic_gap.topic_gap_summary ?? "No topic-gap summary stored."}
                  </p>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Signal Snapshot</span>
                    <SignalSnapshot
                      signals={analysis.signals}
                      emptyText="No sachbuch signals stored yet."
                    />
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Reader Promise</span>
                    <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                      {analysis.reader_promise}
                    </span>
                    <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                      {analysis.why_now}
                    </span>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Differentiation</span>
                      <CompactList
                        items={analysis.differentiation_opportunities}
                        emptyText="No differentiation recommendations stored."
                      />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Chapter Blueprint</span>
                      <CompactList
                        items={analysis.chapter_blueprint}
                        emptyText="No blueprint stored."
                      />
                    </div>
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Subchapters</span>
                    <CompactList items={analysis.subchapter_blueprint} emptyText="No subchapter structure stored." />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Subtitles</span>
                      <CompactList items={analysis.subtitle_ideas} emptyText="No subtitle ideas stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Positioning</span>
                      <CompactList items={analysis.positioning_angles} emptyText="No positioning angles stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Practice Modules</span>
                      <CompactList items={analysis.practice_modules} emptyText="No practice modules stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Checklist Ideas</span>
                      <CompactList items={analysis.checklist_ideas} emptyText="No checklist ideas stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Case Studies</span>
                      <CompactList items={analysis.case_study_ideas} emptyText="No case studies stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Glossary</span>
                      <CompactList items={analysis.glossary_terms} emptyText="No glossary terms stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Research Questions</span>
                      <CompactList items={analysis.research_questions} emptyText="No research questions stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Category Strategy</span>
                      <CompactList items={analysis.category_strategy} emptyText="No category strategy stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Source Requirements</span>
                    <CompactList
                      items={analysis.source_requirements}
                      emptyText="No source requirements stored."
                    />
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(2, minmax(0, 1fr))", gap: 12 }}>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Expert Needs</span>
                      <CompactList items={analysis.expert_needs} emptyText="No expert needs stored." />
                    </div>
                    <div style={{ display: "grid", gap: 8 }}>
                      <span style={sectionLabelStyle}>Cover Direction</span>
                      <CompactList items={analysis.cover_direction} emptyText="No cover direction stored." />
                    </div>
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Warnings & Scope</span>
                    <CompactList
                      items={[
                        ...analysis.quality_warnings,
                        `Target length: ${analysis.target_length}`,
                        `Writing effort: ${analysis.writing_effort}`
                      ]}
                      emptyText="No warnings stored."
                    />
                  </div>

                  <div style={{ display: "grid", gap: 8 }}>
                    <span style={sectionLabelStyle}>Backend Keywords</span>
                    <CompactList items={analysis.backend_keywords} emptyText="No backend keywords stored." />
                  </div>
                </article>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div
      style={{
        border: "1px dashed var(--border)",
        borderRadius: 18,
        padding: 18,
        color: "var(--muted)"
      }}
    >
      {text}
    </div>
  );
}

function CompactList({ items, emptyText }: { items: string[]; emptyText: string }) {
  if (items.length === 0) {
    return <span style={{ color: "var(--muted)", fontSize: 14 }}>{emptyText}</span>;
  }

  return (
    <div style={{ display: "grid", gap: 6 }}>
      {items.map((item, index) => (
        <span key={`${item}-${index}`} style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
          {item}
        </span>
      ))}
    </div>
  );
}

function SignalSnapshot({
  signals,
  emptyText
}: {
  signals: OpportunitySignal[];
  emptyText: string;
}) {
  if (signals.length === 0) {
    return <span style={{ color: "var(--muted)", fontSize: 14 }}>{emptyText}</span>;
  }

  return (
    <div style={{ display: "grid", gap: 8 }}>
      {signals.slice(0, 6).map((signal) => (
        <div
          key={`${signal.key}-${signal.label}`}
          style={{
            border: "1px solid var(--border)",
            borderRadius: 14,
            padding: "12px 14px",
            display: "grid",
            gap: 6,
            background:
              signal.direction === "negative"
                ? "rgba(179, 64, 24, 0.08)"
                : "rgba(40, 92, 77, 0.08)"
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 10, flexWrap: "wrap" }}>
            <strong style={{ fontSize: 14 }}>{signal.label}</strong>
            <span style={metricBadgeStyle}>
              {signal.direction} {signal.score}
            </span>
          </div>
          <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
            {signal.summary}
          </span>
          {signal.evidence.length > 0 ? (
            <span style={{ color: "var(--muted)", fontSize: 13, lineHeight: 1.5 }}>
              {signal.evidence.slice(0, 2).join(" | ")}
            </span>
          ) : null}
        </div>
      ))}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: number | string | null }) {
  return (
    <div style={metricTileStyle}>
      <span style={{ color: "var(--muted)", fontSize: 12, textTransform: "uppercase", letterSpacing: "0.08em" }}>
        {label}
      </span>
      <strong style={{ fontSize: 18 }}>{value ?? "n/a"}</strong>
    </div>
  );
}

function formatPrice(value: number | null): string | null {
  if (value === null) {
    return null;
  }

  return `€${value.toFixed(2)}`;
}

function reportArtifactHref(reportId: number, format: string): string {
  return `${browserApiBaseUrl}/api/v1/reports/${reportId}/download?format=${encodeURIComponent(format)}`;
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString("de-DE", {
    dateStyle: "short",
    timeStyle: "short"
  });
}

const inputStyle = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid var(--border)",
  padding: "12px 14px",
  background: "rgba(255,255,255,0.7)",
  font: "inherit"
} satisfies CSSProperties;

const primaryButtonStyle = {
  border: 0,
  borderRadius: 14,
  padding: "12px 16px",
  background: "var(--accent)",
  color: "#fff",
  font: "inherit",
  cursor: "pointer"
} satisfies CSSProperties;

const secondaryButtonStyle = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "10px 14px",
  background: "#fff",
  font: "inherit",
  cursor: "pointer"
} satisfies CSSProperties;

const linkButtonStyle = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "10px 14px",
  background: "#fff",
  color: "inherit",
  font: "inherit",
  textDecoration: "none"
} satisfies CSSProperties;

const panelStyle = {
  background: "var(--surface)",
  border: "1px solid var(--border)",
  borderRadius: 24,
  padding: 24,
  backdropFilter: "blur(10px)"
} satisfies CSSProperties;

const panelHeaderStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  flexWrap: "wrap"
} satisfies CSSProperties;

const keywordCardStyle = {
  display: "grid",
  gap: 14,
  border: "1px solid var(--border)",
  borderRadius: 18,
  padding: 16,
  background: "rgba(255,255,255,0.6)"
} satisfies CSSProperties;

const inventoryRowStyle = {
  display: "flex",
  justifyContent: "space-between",
  gap: 16,
  flexWrap: "wrap",
  alignItems: "center",
  border: "1px solid var(--border)",
  borderRadius: 18,
  padding: 16,
  background: "rgba(255,255,255,0.58)"
} satisfies CSSProperties;

const clusterCardStyle = {
  display: "grid",
  gap: 14,
  border: "1px solid var(--border)",
  borderRadius: 18,
  padding: 16,
  background: "rgba(255,255,255,0.6)"
} satisfies CSSProperties;

const reportCardStyle = {
  display: "grid",
  gap: 10,
  border: "1px solid var(--border)",
  borderRadius: 18,
  padding: 16,
  background: "rgba(255,255,255,0.58)"
} satisfies CSSProperties;

const competitorCardStyle = {
  display: "grid",
  gap: 14,
  border: "1px solid var(--border)",
  borderRadius: 18,
  padding: 16,
  background: "rgba(255,255,255,0.62)"
} satisfies CSSProperties;

const coverFrameStyle = {
  width: 72,
  height: 104,
  borderRadius: 12,
  overflow: "hidden",
  border: "1px solid var(--border)",
  background: "#fff",
  display: "grid",
  placeItems: "center"
} satisfies CSSProperties;

const pillStyle = {
  display: "inline-flex",
  alignItems: "center",
  gap: 6,
  width: "fit-content",
  borderRadius: 999,
  background: "var(--accent-soft)",
  color: "var(--accent)",
  padding: "6px 10px",
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.06em"
} satisfies CSSProperties;

const metricBadgeStyle = {
  borderRadius: 999,
  border: "1px solid var(--border)",
  padding: "8px 12px",
  background: "#fff",
  color: "var(--muted)",
  fontSize: 13
} satisfies CSSProperties;

const commandStyle = {
  borderRadius: 12,
  border: "1px solid var(--border)",
  padding: "10px 12px",
  background: "rgba(255,255,255,0.82)",
  color: "inherit",
  fontFamily: "ui-monospace, SFMono-Regular, Consolas, monospace",
  fontSize: 13,
  overflowWrap: "anywhere"
} satisfies CSSProperties;

const metricTileStyle = {
  display: "grid",
  gap: 6,
  borderRadius: 16,
  border: "1px solid var(--border)",
  padding: 12,
  background: "#fff"
} satisfies CSSProperties;

const sectionLabelStyle = {
  color: "var(--muted)",
  fontSize: 12,
  textTransform: "uppercase",
  letterSpacing: "0.08em"
} satisfies CSSProperties;

function desktopRuntimeCardStyle(isReady: boolean): CSSProperties {
  return {
    marginTop: 18,
    padding: 16,
    borderRadius: 18,
    border: "1px solid var(--border)",
    background: isReady ? "rgba(40, 92, 77, 0.08)" : "rgba(179, 64, 24, 0.08)"
  };
}

function runtimeBadgeStyle(status: string): CSSProperties {
  if (status === "ready") {
    return {
      ...pillStyle,
      background: "#dcefd8",
      color: "#2d6b2f"
    };
  }

  if (status === "degraded") {
    return {
      ...pillStyle,
      background: "#f4ebc8",
      color: "#8a6500"
    };
  }

  return {
    ...pillStyle,
    background: "#f5d7d7",
    color: "#8a2323"
  };
}

function scoreBadgeStyle(score: number | null): CSSProperties {
  const background =
    score === null ? "#fff" : score >= 65 ? "#dcefd8" : score >= 40 ? "#f4ebc8" : "#f5d7d7";
  const color =
    score === null ? "var(--muted)" : score >= 65 ? "#2d6b2f" : score >= 40 ? "#8a6500" : "#8a2323";

  return {
    borderRadius: 999,
    padding: "8px 12px",
    background,
    color,
    fontSize: 13,
    fontWeight: 700
  };
}

function sentimentBadgeStyle(sentiment: string): CSSProperties {
  if (sentiment === "positive") {
    return {
      ...pillStyle,
      background: "#dcefd8",
      color: "#2d6b2f"
    };
  }

  return {
    ...pillStyle,
    background: "#f5d7d7",
    color: "#8a2323"
  };
}

function decisionBadgeStyle(decision: string): CSSProperties {
  if (decision === "GO") {
    return {
      ...pillStyle,
      background: "#dcefd8",
      color: "#2d6b2f"
    };
  }
  if (decision === "MAYBE") {
    return {
      ...pillStyle,
      background: "#f4ebc8",
      color: "#8a6500"
    };
  }

  return {
    ...pillStyle,
    background: "#f5d7d7",
    color: "#8a2323"
  };
}
