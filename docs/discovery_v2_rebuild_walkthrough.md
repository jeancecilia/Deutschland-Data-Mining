# Discovery V2 P0/P1 Fix Walkthrough

This update resolves critical data-destruction bugs (P0) introduced in the previous iteration and significantly improves the robustness of the V2 Rebuild architecture (P1).

## Changes Made

### 1. Data Safety & Dry Run (P0 Fixed)
* **Keyword Cascade Protection**: Before resetting candidates, the pipeline now executes `UPDATE keywords SET source_niche_candidate_id = NULL WHERE source_niche_candidate_id IS NOT NULL`.
* **Safe Table Deletion**: The script now uses `DELETE FROM` instead of `TRUNCATE ... CASCADE`. This prevents accidental deletion of down-stream tables like `search_runs` and `search_results`. The precise order of deletion respects foreign keys: `discovery_entity_aliases` -> `discovery_entity_relations` -> `niche_candidates` -> `discovery_entities` -> `raw_discovery_items`.
* **Execution Plan (Dry Run)**: The `--dry-run` flag now correctly short-circuits the entire pipeline before making *any* mutating calls or imports, printing a calculated plan and immediately returning `0`.

### 2. Catalog Import & Deduplication (P1 Fixed)
* **Scoped Deduplication**: Fixed `import_micro_domain_catalog.py` to only deduplicate incoming raw texts against `RawDiscoveryItem` entries that share the exact same `discovery_source_id`. This correctly allows the micro-domain catalog to supply its structured metadata even if a primitive version of the topic phrase was already loaded from a generic seed manifest.
* **Catalog Size Documentation**: The catalog file has been accurately renamed from `micro_domain_catalog_10000_de_v2.csv` to `micro_domain_catalog_2k_de_v2.csv` to correctly state its capacity of ~2,013 rows.

### 3. Metadata Assertions & Exhaustion Loops (P1 Fixed)
* **Strict Assertion Policy**: Extracted metadata is now rigorously tested. The pipeline will raise a `RuntimeError` if macro domain, audience hint, or format hint properties are present in less than 95% of extracted catalog entities.
* **Exhaustion Queues**: Both the ranker and fast validator operate inside `while True:` loops that strictly monitor `status = 'new'` and `status = 'prevalidation_queued'` respectively, executing batches of 10,000 until the tables are identically zero.

## Pipeline Results

Executing `docker exec deutschland-data-mining-backend-1 python -m app.scripts.run_full_rebuild_v2 --reset --import-seeds` resulted in a perfectly successful pipeline run with safe execution loops.

### Generated Candidate Funnel
The pipeline efficiently processed the structured catalog and yielded the following verified candidate states:

| Stage                                | Count |
| ------------------------------------ | ----: |
| Generated candidates                 | 4,013 |
| Rejected during pre-validation       | 3,811 |
| Sent to pre-validation manual review |   161 |
| Sent to fast validation              |    41 |

Note that while 4,013 candidates were successfully generated and correctly bound to the domain knowledge graph, **only 41** qualified for automated fast validation after the rigorous ranker cutoff (`>=70` threshold).
