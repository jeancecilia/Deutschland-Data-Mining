# Discovery V2 Full Rebuild Walkthrough

## Overview

The Celery pipeline task `discovery_full_pipeline` has a hardcoded processing limit of 500 items per cycle. Because the initial database queue contained 10,000 raw imported discovery items, running a single cycle was insufficient to populate the graph with enough density to form relations and candidates. 

To perform a full rebuild at scale, a custom orchestration script `backend/app/scripts/run_full_rebuild_v2.py` was created to iteratively batch process the entire pipeline until the queue was exhausted.

## Execution Checklist

- `[x]` Create `run_full_rebuild_v2.py` in `backend/app/scripts/` to bypass the celery batch limits.
- `[x]` Execute the rebuild script via docker exec (`docker exec deutschland-data-mining-backend-1 python -m app.scripts.run_full_rebuild_v2`).
- `[x]` Monitor pipeline logs across multiple iterations (processed 1000 entities per batch for 10 iterations).
- `[x]` Capture final live funnel JSON and evaluate the output.

## Final Pipeline JSON Output

After fully processing all 10,000 items, the live funnel from `/api/v1/discovery-pipeline/overview` is:

```json
{
  "source_count": 56,
  "active_source_count": 56,
  "raw_item_count": 10000,
  "unprocessed_raw_count": 0,
  "entity_count": 10000,
  "entity_types": {
    "topic": 10000
  },
  "domain_count": 0,
  "entity_domain_count": 0,
  "top_domains": [],
  "candidate_domain_count": 0,
  "top_candidate_domains": [],
  "relation_count": 0,
  "candidate_count": 0,
  "new_candidate_count": 0,
  "promoted_candidate_count": 0,
  "rejected_candidate_count": 0
}
```

## Explanation of Results

1. **10,000 / 10,000 Raw Items** were successfully processed.
2. **10,000 Topic Entities** were correctly normalized and extracted.
3. **0 Relations and 0 Candidates:** The `micro_domain_catalog_10000_de.csv` catalog imported all 10,000 items purely as standalone `topic` entities without assigning them to specific domains or including corresponding target audiences/formats. The `build_entity_relations` logic relies on either:
   - **Strategy 2:** Domain-based clustering (e.g. topic + audience within the same domain).
   - **Strategy 3:** Cross-type mapping (e.g. topic mapped to profession, exam, etc.).
   
Because the graph only contains isolated `topic` entities with no domains or cross-type connections, the relation builder found no intersecting nodes to link. Without relations (edges), the `niche_candidate_composer` had no paths to traverse, resulting in 0 generated candidates.

**Conclusion:** The database pipeline and custom scaling script are working perfectly, but the seed data needs to include target audiences, formats, or domain assignments for the graph to wire itself together and generate candidates.
