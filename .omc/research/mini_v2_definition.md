# TeamBench-Mini v2 Definition

**50 tasks · 18 categories · seed 0 · 95% CI ±13.9pp**

## Selection Methodology

Tasks were selected from the full 130-task evaluated pool using a
stratified discrimination-maximizing algorithm:

1. **Proportional category allocation** — each of 18 categories receives
   tasks proportional to its share in the full pool (minimum 2 per category)
2. **Discrimination ranking** — within each category, tasks are ranked by
   `std(oracle, restricted, no_plan, no_eval, full)`. Higher discrimination
   means the task better separates model performance across conditions.
3. **Uplift diversity** — for categories with allocation ≥ 3, the algorithm
   ensures at least one positive-uplift and one negative-uplift task is included.
4. **Degenerate exclusion** — tasks where all five conditions score within
   0.01 of each other are excluded (no signal). Exception: Adversarial category
   tasks are retained even if uniform, as they test robustness rather than uplift.

## Properties

| Metric | Value |
|---|---|
| Tasks | 50 |
| Categories | 18 |
| 95% CI (binary, p=0.5) | ±13.9 pp |
| Positive uplift tasks | 22 (44%) |
| Neutral uplift tasks | 13 (26%) |
| Negative uplift tasks | 15 (30%) |
| Mean difficulty | 0.639 |
| Mean discrimination | 0.319 |

## Category Breakdown

| Category | Tasks | IDs |
|---|---|---|
| Adversarial | 3 | TRAP6_deprecated_api, TRAP7_test_pollution, trap5_security_theater |
| Code Rev. | 2 | CR5_test_coverage, CR6_review_checklist |
| Cross-Sys. | 3 | CROSS5_event_schema, CROSS6_grpc_rest_bridge, cross2_schema_evolution |
| Data Eng. | 3 | D2_data_quality, D4_data_pipeline, D8_csv_cleanup |
| Distributed | 2 | DIST6_distributed_lock, dist3_idempotency |
| Incident | 4 | INC2_data_corruption, INC3_memory_leak, INC5_cert_expiry, INC7_rollback |
| Info. Retr. | 3 | IR5_search_ranking, IR7_doc_clustering, IR8_search_index |
| Long-Hor. | 3 | LH6_audit_trail, LH7_zero_downtime, SYNTH1_distributed_debug |
| Multi-lang. | 3 | MULTI4_monorepo_fix, MULTI5_deploy_pipeline, MULTI8_sdk_mismatch |
| Negotiation | 2 | NEG2_cost_perf, NEG3_tech_debt |
| Operations | 3 | O4_monitoring, O6_perf_tuning, O8_dockerfile_fix |
| Other | 2 | JS2_xss_sanitize, S6_caching |
| Pipeline | 3 | PIPE2_api_gateway, PIPE3_msg_queue, PIPE3_stream_processing |
| Policy | 3 | P2_spec_arbitration, P6_license_check, P7_data_retention |
| SWE | 3 | GO1_concurrency_fix, JS1_api_migration, SQL2_query_optimize |
| Security | 3 | SEC5_secrets_rotation, SEC7_rate_limiting, SEC9_vuln_triage |
| Specification | 2 | SPEC3_data_model, SPEC4_migration |
| Testing | 3 | TEST2_regression, TEST3_integration, TEST9_mock_service |

## Task IDs (full list)

```json
[
  "CR5_test_coverage",
  "CR6_review_checklist",
  "CROSS5_event_schema",
  "CROSS6_grpc_rest_bridge",
  "D2_data_quality",
  "D4_data_pipeline",
  "D8_csv_cleanup",
  "DIST6_distributed_lock",
  "GO1_concurrency_fix",
  "INC2_data_corruption",
  "INC3_memory_leak",
  "INC5_cert_expiry",
  "INC7_rollback",
  "IR5_search_ranking",
  "IR7_doc_clustering",
  "IR8_search_index",
  "JS1_api_migration",
  "JS2_xss_sanitize",
  "LH6_audit_trail",
  "LH7_zero_downtime",
  "MULTI4_monorepo_fix",
  "MULTI5_deploy_pipeline",
  "MULTI8_sdk_mismatch",
  "NEG2_cost_perf",
  "NEG3_tech_debt",
  "O4_monitoring",
  "O6_perf_tuning",
  "O8_dockerfile_fix",
  "P2_spec_arbitration",
  "P6_license_check",
  "P7_data_retention",
  "PIPE2_api_gateway",
  "PIPE3_msg_queue",
  "PIPE3_stream_processing",
  "S6_caching",
  "SEC5_secrets_rotation",
  "SEC7_rate_limiting",
  "SEC9_vuln_triage",
  "SPEC3_data_model",
  "SPEC4_migration",
  "SQL2_query_optimize",
  "SYNTH1_distributed_debug",
  "TEST2_regression",
  "TEST3_integration",
  "TEST9_mock_service",
  "TRAP6_deprecated_api",
  "TRAP7_test_pollution",
  "cross2_schema_evolution",
  "dist3_idempotency",
  "trap5_security_theater"
]
```

## Comparison with Mini v1 (28 tasks)

| Property | Mini v1 | Mini v2 |
|---|---|---|
| Size | 28 | 50 |
| 95% CI | ±18.5 pp | ±13.9 pp |
| Categories | ~21 (undocumented) | 18 (all covered) |
| Selection method | Undocumented | Stratified discrimination |
| Minimum per category | 1 | 2 |
| Score granularity | 3.57% per task | 2% per task |
