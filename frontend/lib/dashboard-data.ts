const apiBaseUrl = process.env.KDP_API_BASE_URL ?? "http://backend:8000";

export type RuntimeStatus = {
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

export type Keyword = {
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

export type Cluster = {
  id: number;
  name: string;
  main_keyword: string | null;
  book_class: string | null;
  status: string;
  latest_final_score: number | null;
};

export type Report = {
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
  updated_at: string;
};

export type DiscoveryUniverseItem = {
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

export type DiscoveryUniverse = {
  topics: DiscoveryUniverseItem[];
  audiences: DiscoveryUniverseItem[];
  pain_points: DiscoveryUniverseItem[];
  contexts: DiscoveryUniverseItem[];
  book_formats: DiscoveryUniverseItem[];
};

export type OpportunitySignal = {
  key: string;
  label: string;
  category: string;
  direction: string;
  score: number;
  summary: string;
  evidence: string[];
};

export type DiscoveryCandidate = {
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

export type DiscoveryPipelineOverview = {
  source_count: number;
  active_source_count: number;
  raw_item_count: number;
  unprocessed_raw_count: number;
  entity_count: number;
  relation_count: number;
  candidate_count: number;
  new_candidate_count: number;
  promoted_candidate_count: number;
  rejected_candidate_count: number;
};

export type PipelineEntity = {
  id: number;
  name: string;
  normalized_name: string;
  entity_type: string;
  language: string;
  confidence: number;
  source_count: number;
  metadata_json: Record<string, unknown> | null;
  created_at: string;
};

export type PipelineCandidate = {
  id: number;
  candidate_name: string;
  normalized_name: string;
  main_topic: string | null;
  audience: string | null;
  problem: string | null;
  format: string | null;
  book_class_guess: string | null;
  language: string;
  marketplace: string;
  generation_template: string | null;
  confidence: number;
  risk_level: string | null;
  status: string;
  fast_validation_score: number | null;
  rejection_reason: string | null;
  promotion_reason: string | null;
  created_at: string;
  updated_at: string;
};

export type PipelineCandidateKeyword = {
  id: number;
  niche_candidate_id: number;
  keyword: string;
  keyword_type: string | null;
  language: string;
  confidence: number;
};

export type RecentCrawl = {
  run_id: number;
  keyword_id: number;
  keyword: string;
  run_at: string;
  status: string;
  result_count: number | null;
  notes: string | null;
};

export type FailedJob = {
  job_type: string;
  reference: string;
  occurred_at: string;
  status: string;
  notes: string | null;
};

export type OperationsSummary = {
  last_crawl_at: string | null;
  last_bsr_snapshot_at: string | null;
  failed_job_count: number;
  recent_crawls: RecentCrawl[];
  failed_jobs: FailedJob[];
};

export type ClusterKeyword = {
  keyword: string;
  relevance_score: number | null;
};

export type ClusterTopBook = {
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

export type ClusterDetail = {
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
  book_classification: {
    book_class: string;
    confidence: number;
    evidence: string[];
    low_content_signal: number;
    medium_content_signal: number;
    high_content_signal: number;
    sachbuch_signal: number;
  };
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

export type SachbuchAnalysis = {
  niche_cluster_id: number;
  niche_cluster_name: string;
  main_keyword: string;
  opportunity_score: number | null;
  sachbuch_score: {
    final_score: number | null;
    liability_risk: number | null;
    update_risk: number | null;
    evergreen_potential_signal: number | null;
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
    topic_gap_summary: string | null;
    outdated_content_signal: number | null;
    missing_examples_signal: number | null;
    missing_checklists_signal: number | null;
    localization_gap_signal: number | null;
  };
};

export type DashboardData = {
  health: string;
  runtimeStatus: RuntimeStatus | null;
  keywords: Keyword[];
  clusters: Cluster[];
  reports: Report[];
  discoveryUniverse: DiscoveryUniverse | null;
  discoveryCandidates: DiscoveryCandidate[];
  discoveryPipelineOverview: DiscoveryPipelineOverview | null;
  discoveryPipelineCandidates: PipelineCandidate[];
  operations: OperationsSummary | null;
  clusterDetails: ClusterDetail[];
  sachbuchAnalyses: SachbuchAnalysis[];
  metrics: {
    totalBooks: number;
    riskAlerts: number;
    goSachbuchs: number;
    topOpportunity: number;
  };
};

const EMPTY_METRICS: DashboardData["metrics"] = {
  totalBooks: 0,
  riskAlerts: 0,
  goSachbuchs: 0,
  topOpportunity: 0
};

const MAX_OVERVIEW_CLUSTER_DETAILS = 5;
const MAX_CLUSTER_PAGE_DETAILS = 6;

async function getHealth(): Promise<string> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/health`, { cache: "no-store" });
    if (!response.ok) {
      return "degraded";
    }

    const payload = (await response.json()) as { status?: string };
    return payload.status ?? "unknown";
  } catch {
    return "offline";
  }
}

async function getRuntimeStatus(): Promise<RuntimeStatus | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/health/runtime`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }

    return (await response.json()) as RuntimeStatus;
  } catch {
    return null;
  }
}

async function getKeywords(): Promise<Keyword[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/keywords`, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }

    return (await response.json()) as Keyword[];
  } catch {
    return [];
  }
}

async function getClusters(): Promise<Cluster[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/clusters`, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }

    return (await response.json()) as Cluster[];
  } catch {
    return [];
  }
}

async function getReports(): Promise<Report[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/reports`, { cache: "no-store" });
    if (!response.ok) {
      return [];
    }

    return (await response.json()) as Report[];
  } catch {
    return [];
  }
}

async function getDiscoveryUniverse(): Promise<DiscoveryUniverse | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/discovery/universe`, { cache: "no-store" });
    if (!response.ok) {
      return null;
    }

    return (await response.json()) as DiscoveryUniverse;
  } catch {
    return null;
  }
}

async function getDiscoveryCandidates(): Promise<DiscoveryCandidate[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/discovery/candidates?limit=24`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return [];
    }

    return (await response.json()) as DiscoveryCandidate[];
  } catch {
    return [];
  }
}

async function getOperationsSummary(): Promise<OperationsSummary | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/operations/summary`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }

    return (await response.json()) as OperationsSummary;
  } catch {
    return null;
  }
}

async function getDiscoveryPipelineOverview(): Promise<DiscoveryPipelineOverview | null> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/discovery-pipeline/overview`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as DiscoveryPipelineOverview;
  } catch {
    return null;
  }
}

async function getDiscoveryPipelineCandidates(): Promise<PipelineCandidate[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/discovery-pipeline/candidates?limit=24`, {
      cache: "no-store"
    });
    if (!response.ok) {
      return [];
    }
    return (await response.json()) as PipelineCandidate[];
  } catch {
    return [];
  }
}

async function getClusterDetails(clusters: Cluster[]): Promise<ClusterDetail[]> {
  const responses = await Promise.all(
    clusters.map(async (cluster) => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/clusters/${cluster.id}`, {
          cache: "no-store"
        });
        if (!response.ok) {
          return null;
        }

        return (await response.json()) as ClusterDetail;
      } catch {
        return null;
      }
    })
  );

  return responses.filter((detail): detail is ClusterDetail => detail !== null);
}

async function getSachbuchAnalyses(clusters: Cluster[]): Promise<SachbuchAnalysis[]> {
  const sachbuchClusters = clusters.filter((cluster) => cluster.book_class === "sachbuch");
  const responses = await Promise.all(
    sachbuchClusters.map(async (cluster) => {
      try {
        const response = await fetch(`${apiBaseUrl}/api/v1/clusters/${cluster.id}/sachbuch`, {
          cache: "no-store"
        });
        if (!response.ok) {
          return null;
        }

        return (await response.json()) as SachbuchAnalysis;
      } catch {
        return null;
      }
    })
  );

  return responses.filter((analysis): analysis is SachbuchAnalysis => analysis !== null);
}

function buildDashboardData(
  partial: Omit<Partial<DashboardData>, "metrics"> & {
    metrics?: Partial<DashboardData["metrics"]>;
  }
): DashboardData {
  const base: DashboardData = {
    health: "offline",
    runtimeStatus: null,
    keywords: [],
    clusters: [],
    reports: [],
    discoveryUniverse: null,
    discoveryCandidates: [],
    discoveryPipelineOverview: null,
    discoveryPipelineCandidates: [],
    operations: null,
    clusterDetails: [],
    sachbuchAnalyses: [],
    metrics: { ...EMPTY_METRICS }
  };

  return {
    ...base,
    ...partial,
    metrics: {
      ...EMPTY_METRICS,
      ...(partial.metrics ?? {})
    }
  };
}

function rankClusters(clusters: Cluster[]): Cluster[] {
  return [...clusters].sort((left, right) => (right.latest_final_score ?? 0) - (left.latest_final_score ?? 0));
}

function topOpportunityScore(clusters: Cluster[]): number {
  return Math.max(0, ...clusters.map((cluster) => cluster.latest_final_score ?? 0));
}

export async function loadOverviewData(): Promise<DashboardData> {
  const [
    health,
    runtimeStatus,
    keywords,
    clusters,
    reports,
    discoveryCandidates,
    operations
  ] = await Promise.all([
    getHealth(),
    getRuntimeStatus(),
    getKeywords(),
    getClusters(),
    getReports(),
    getDiscoveryCandidates(),
    getOperationsSummary()
  ]);

  const clusterDetails = await getClusterDetails(rankClusters(clusters).slice(0, MAX_OVERVIEW_CLUSTER_DETAILS));

  return buildDashboardData({
    health,
    runtimeStatus,
    keywords,
    clusters,
    reports,
    discoveryCandidates,
    operations,
    clusterDetails,
    metrics: {
      topOpportunity: topOpportunityScore(clusters)
    }
  });
}

export async function loadDiscoveryPageData(): Promise<DashboardData> {
  const [
    runtimeStatus,
    discoveryUniverse,
    discoveryCandidates,
    discoveryPipelineOverview,
    discoveryPipelineCandidates
  ] = await Promise.all([
    getRuntimeStatus(),
    getDiscoveryUniverse(),
    getDiscoveryCandidates(),
    getDiscoveryPipelineOverview(),
    getDiscoveryPipelineCandidates()
  ]);

  return buildDashboardData({
    runtimeStatus,
    discoveryUniverse,
    discoveryCandidates,
    discoveryPipelineOverview,
    discoveryPipelineCandidates
  });
}

export async function loadReportsPageData(): Promise<DashboardData> {
  return buildDashboardData({
    reports: await getReports()
  });
}

export async function loadKeywordsPageData(): Promise<DashboardData> {
  return buildDashboardData({
    keywords: await getKeywords()
  });
}

export async function loadRuntimePageData(): Promise<DashboardData> {
  const [runtimeStatus, operations] = await Promise.all([getRuntimeStatus(), getOperationsSummary()]);

  return buildDashboardData({
    runtimeStatus,
    operations
  });
}

export async function loadClustersPageData(): Promise<DashboardData> {
  const clusters = await getClusters();
  const rankedClusters = rankClusters(clusters);
  const focusClusters = rankedClusters.slice(0, MAX_CLUSTER_PAGE_DETAILS);
  const [clusterDetails, sachbuchAnalyses] = await Promise.all([
    getClusterDetails(focusClusters),
    getSachbuchAnalyses(focusClusters)
  ]);

  return buildDashboardData({
    clusters,
    clusterDetails,
    sachbuchAnalyses,
    metrics: {
      goSachbuchs: sachbuchAnalyses.filter((analysis) => analysis.go_decision === "GO").length,
      topOpportunity: topOpportunityScore(clusters)
    }
  });
}

export async function loadDashboardData(): Promise<DashboardData> {
  return loadClustersPageData();
}
