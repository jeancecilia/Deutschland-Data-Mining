import {
  analyzeClusterAction,
  collectKeywordAction,
  createKeywordAction,
  expandKeywordAction,
  runPipelineAction,
  updateKeywordAction
} from "../../app/actions";
import type { DashboardData, Keyword } from "../../lib/dashboard-data";
import {
  ActionButton,
  Badge,
  CompactList,
  EmptyState,
  MetricBadge,
  PageHeader,
  Panel,
  primaryButtonStyle,
  secondaryButtonStyle
} from "../dashboard-ui";

type KeywordFamily = {
  seed: Keyword | null;
  variants: Keyword[];
};

function normalizePhrase(value: string): string {
  return value
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

function buildKeywordFamilies(keywords: Keyword[]): KeywordFamily[] {
  const keywordById = new Map(keywords.map((keyword) => [keyword.id, keyword]));
  const familyMap = new Map<number, KeywordFamily>();

  for (const keyword of keywords.filter((item) => item.seed_keyword_id !== null)) {
    const familyId = keyword.seed_keyword_id!;
    const family = familyMap.get(familyId) ?? {
      seed: keywordById.get(familyId) ?? null,
      variants: []
    };
    family.variants.push(keyword);
    familyMap.set(familyId, family);
  }

  return [...familyMap.values()]
    .map((family) => {
      const seen = new Set<string>();
      const variants = family.variants.filter((variant) => {
        const key = normalizePhrase(variant.keyword);
        if (seen.has(key)) {
          return false;
        }

        seen.add(key);
        return true;
      });

      return {
        ...family,
        variants
      };
    })
    .sort((left, right) => right.variants.length - left.variants.length);
}

export function KeywordsView({ data }: { data: DashboardData }) {
  const seedKeywords = data.keywords.filter(
    (keyword) => keyword.seed_keyword_id === null && keyword.status !== "ignored"
  );
  const prioritizedKeywords = data.keywords.filter((keyword) => keyword.priority >= 80);
  const expandedFamilies = buildKeywordFamilies(data.keywords);

  return (
    <div style={{ display: "grid", gap: 24 }}>
      <PageHeader
        eyebrow="Manual Keyword Workflow"
        title="Seed keywords and grouped expansion families"
        description="Raw expanded phrases are now grouped by family so near-duplicate variants stop overwhelming the UI. Discovery candidates remain on the Discovery page."
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(320px, 420px) minmax(0, 1fr)",
          gap: 24
        }}
      >
        <Panel
          title="Seed Keywords"
          description="Add a manual niche idea, expand it into long-tail phrases, and run the first collection pipeline."
          meta={`${seedKeywords.length} active`}
        >
          <form action={createKeywordAction} style={{ display: "grid", gap: 12 }}>
            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Keyword</span>
              <input name="keyword" type="text" placeholder="Blutdrucktagebuch" style={inputStyle} required />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Target Audience</span>
              <input name="targetAudience" type="text" placeholder="z. B. Senioren, Eltern" style={inputStyle} />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Category Hint</span>
              <input name="categoryHint" type="text" placeholder="z. B. Gesundheit" style={inputStyle} />
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
              <input name="priority" type="number" min="0" max="100" defaultValue="40" style={inputStyle} />
            </label>

            <label style={{ display: "grid", gap: 6 }}>
              <span style={{ fontSize: 13, color: "var(--muted)" }}>Notes</span>
              <textarea
                name="notes"
                rows={3}
                placeholder="Optional niche context, risk, or product angle."
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </label>

            <button type="submit" style={primaryButtonStyle}>
              Add Seed Keyword
            </button>
          </form>

          {seedKeywords.length === 0 ? (
            <EmptyState text="No manual seed keywords are waiting." />
          ) : (
            seedKeywords.map((keyword) => (
              <article
                key={keyword.id}
                style={{
                  border: "1px solid var(--border)",
                  borderRadius: 18,
                  padding: 16,
                  background: "rgba(255,255,255,0.6)",
                  display: "grid",
                  gap: 12
                }}
              >
                <div style={{ display: "grid", gap: 6 }}>
                  <strong style={{ fontSize: 18 }}>{keyword.keyword}</strong>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {keyword.book_type ? <Badge>{keyword.book_type}</Badge> : null}
                    <Badge>prio {keyword.priority}</Badge>
                    {keyword.search_intent_family ? <Badge>{keyword.search_intent_family}</Badge> : null}
                  </div>
                  <span style={{ color: "var(--muted)", fontSize: 14, lineHeight: 1.5 }}>
                    {keyword.target_audience ?? "Audience inferred later"} | {keyword.category_hint ?? "No category hint"}
                  </span>
                </div>

                <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                  <form action={expandKeywordAction}>
                    <input type="hidden" name="keywordId" value={keyword.id} />
                    <ActionButton>Expand</ActionButton>
                  </form>
                  <form action={collectKeywordAction}>
                    <input type="hidden" name="keywordId" value={keyword.id} />
                    <ActionButton>Collect</ActionButton>
                  </form>
                  <form action={runPipelineAction}>
                    <input type="hidden" name="keywordId" value={keyword.id} />
                    <ActionButton>Pipeline</ActionButton>
                  </form>
                  <form action={analyzeClusterAction}>
                    <input type="hidden" name="keywordId" value={keyword.id} />
                    <ActionButton>Cluster</ActionButton>
                  </form>
                  <form action={updateKeywordAction}>
                    <input type="hidden" name="keywordId" value={keyword.id} />
                    <input type="hidden" name="status" value="prioritized" />
                    <input type="hidden" name="priority" value="100" />
                    <ActionButton>Prioritize</ActionButton>
                  </form>
                </div>
              </article>
            ))
          )}
        </Panel>

        <div style={{ display: "grid", gap: 24 }}>
          <Panel
            title="Expanded Variant Families"
            description="Child keywords are grouped by parent seed so you see the family shape instead of a noisy flat list of minor wording variants."
            meta={`${expandedFamilies.length} families`}
          >
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
              <MetricBadge>{data.keywords.length} total keywords</MetricBadge>
              <MetricBadge>{expandedFamilies.reduce((sum, family) => sum + family.variants.length, 0)} visible variants</MetricBadge>
              <MetricBadge>{prioritizedKeywords.length} prioritized</MetricBadge>
            </div>

            {expandedFamilies.length === 0 ? (
              <EmptyState text="No expanded keyword families exist yet." />
            ) : (
              expandedFamilies.map((family, index) => (
                <article
                  key={`${family.seed?.id ?? "family"}-${index}`}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 18,
                    padding: 16,
                    background: "rgba(255,255,255,0.6)",
                    display: "grid",
                    gap: 10
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
                    <div style={{ display: "grid", gap: 4 }}>
                      <strong style={{ fontSize: 18 }}>{family.seed?.keyword ?? `Seed family #${index + 1}`}</strong>
                      <span style={{ color: "var(--muted)", fontSize: 14 }}>
                        {family.variants.length} unique visible variants
                      </span>
                    </div>
                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                      {family.seed?.book_type ? <Badge>{family.seed.book_type}</Badge> : null}
                      <Badge>seed {family.seed?.priority ?? 0}</Badge>
                    </div>
                  </div>

                  <CompactList
                    items={family.variants.slice(0, 6).map((variant) => variant.keyword)}
                    emptyText="No variants stored."
                  />
                  {family.variants.length > 6 ? (
                    <span style={{ color: "var(--muted)", fontSize: 14 }}>
                      + {family.variants.length - 6} more variants hidden
                    </span>
                  ) : null}
                </article>
              ))
            )}
          </Panel>

          <Panel
            title="Priority Queue"
            description="Most urgent keywords across manual seeds and child phrases."
            meta={`${prioritizedKeywords.length} prioritized`}
          >
            {prioritizedKeywords.length === 0 ? (
              <EmptyState text="No prioritized keywords yet." />
            ) : (
              prioritizedKeywords.slice(0, 12).map((keyword) => (
                <article
                  key={keyword.id}
                  style={{
                    border: "1px solid var(--border)",
                    borderRadius: 16,
                    padding: 14,
                    background: "rgba(255,255,255,0.58)",
                    display: "grid",
                    gap: 6
                  }}
                >
                  <strong>{keyword.keyword}</strong>
                  <span style={{ color: "var(--muted)", fontSize: 14 }}>
                    {keyword.seed_keyword_id === null ? "seed" : "expanded"} | prio {keyword.priority}
                  </span>
                  <span style={{ color: "var(--muted)", fontSize: 13 }}>
                    Spec {keyword.specificity_score ?? "n/a"} | Intent {keyword.intent_score ?? "n/a"} | Competition {keyword.competition_probability_score ?? "n/a"}
                  </span>
                </article>
              ))
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}

const inputStyle = {
  width: "100%",
  borderRadius: 14,
  border: "1px solid var(--border)",
  padding: "12px 14px",
  background: "rgba(255,255,255,0.7)",
  font: "inherit"
} as const;
