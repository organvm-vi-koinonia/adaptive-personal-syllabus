# Integration-Observability-CI Milestone

## Objective
Establish a repeatable execution system for roadmap delivery with:
- measurable KPIs,
- scoped integration checkpoints,
- feature-priority criteria,
- CI-backed verification.

## Minimum Viable Platform Criteria
The milestone is considered operational when all criteria are met:
- `corpus ingestion completeness` is `100%` for the selected docs root.
- `ledger integrity` verifies cleanly with `syllabus ledger verify`.
- `docs audit` emits both JSON and Markdown reports in a deterministic schema.
- `milestone execution plan` can be generated and exported in JSON and Markdown.
- CI validates CLI surface including `syllabus docs --help`.

## Feature Prioritization Framework
Use weighted priority scores for roadmap execution:
- `Impact` (1-5): expected improvement to delivery quality or risk reduction.
- `Urgency` (1-5): dependency pressure from other milestones.
- `Evidence Gap` (1-5): lack of metrics, observability, or tests.
- `Effort` (1-5): implementation cost (inverse in final score).

Priority score formula:
`priority = (impact * 2) + urgency + evidence_gap - effort`

Execution policy:
- prioritize items with score `>= 7` first,
- limit active implementation scope to top `20` selected items per run,
- defer low-score items with explicit rationale in milestone status files.

## Integration Milestone Checkpoints
- Checkpoint 1: KPI catalog and measurement contract committed.
- Checkpoint 2: CI-quality gate and audit generation command operational.
- Checkpoint 3: Milestone status overrides map implemented suggestion IDs to evidence.

## KPI Catalog
- `ingest_coverage_pct`: `snapshot_doc_count / expected_file_count * 100`.
- `suggestion_burn_down`: `planned_count` trend per audit snapshot.
- `implemented_coverage`: `implemented_count / suggestions_count * 100`.
- `milestone_completion_pct`: `implemented_count / total_count` per milestone bucket.
- `audit_runtime_stability`: command duration trend in CI/local runs.
- `test_pass_rate`: passed tests / total tests per run.

Additional required KPI outputs for this milestone:
- `adoption_rate`: number of contributors using docs-audit workflow per sprint.
- `cross_discipline_outcome_count`: count of artifacts mapped to technical + humanities outcomes.
- `time_saved_docs_minutes`: estimated documentation hours saved via automated audit and reporting.
- `proposal_metric_coverage`: percentage of grant/proposal sections with quantified metrics.

## Module Interconnection Protocols
- Define stable data contracts between phases:
  - `snapshot` output from corpus ingestion feeds plan generation and milestone reporting.
  - `suggestion IDs` are canonical references across roadmap, status, and execution plans.
  - `milestone status` files are the authoritative implementation override source.
- Define schema evolution policy:
  - keep `schema_version` on all generated artifacts,
  - add fields backward-compatibly,
  - never remove top-level keys without migration note.
- Require dependency map updates whenever checkpoint boundaries change.

## CI Gate Contract
- Run `syllabus docs audit` for target docs root.
- Export JSON + Markdown artifacts for inspection.
- Fail build if:
  - ingestion completeness is false,
  - tests fail,
  - ledger verification fails.

## Phase Milestones
- Phase A (`baseline`): metrics + scope + objective alignment complete.
- Phase B (`verification`): CI gates and reliability KPIs active.
- Phase C (`publication`): outcomes packaged for capstone, grants, and public reporting.

## Capstone Alignment
- Every integration metric must map to capstone readiness criteria.
- Every workflow change must retain a traceable relation to capstone integration.
- Each sprint closes with an explicit capstone-impact note.

## Cross-Discipline Outcomes
- Technical: reproducible quality gates and integration metrics.
- Social/public process: publishable execution narrative and checkpoints.
- Research/grants: quantifiable impact statements and repeatable evidence model.

## Grant/Proposal Metrics Contract
- Include quantified KPIs in all proposal narratives.
- Include societal benefit language tied to measurable outcomes.
- Include explicit simulation/research relevance where applicable.
- Include adoption and documentation time-saved metrics as evidence.

## Public Narrative Contract
- Maintain a public summary stream for milestone progress.
- Frame updates as technical execution plus reflective methodology.
- Keep metrics and checkpoint results publishable.

## Dependency Map (Execution Order)
- Tier 1: integration-observability-ci
- Tier 2: systems-kernel-runtime, pedagogy-scaffolding
- Tier 3: ui-xr-accessibility, dsl-neural-symbolic-verification
- Tier 4: wings-community-governance
- Tier 5: general-backlog triage

## Debug/Recovery Procedure
- If audit generation fails:
  - run `syllabus corpus ingest` manually with explicit snapshot name.
  - rerun `syllabus docs audit` and compare snapshot metadata.
- If milestone status appears stale:
  - verify status-file IDs still exist in current report.
  - remove obsolete IDs and rerun audit.
- If CI breaks on docs commands:
  - run local CLI smoke tests and `pytest` before pushing fixes.

## Implemented Suggestion IDs Covered
This milestone artifact explicitly implements the following roadmap suggestions:
- `feat-00edc0765630`
- `feat-855f100f3900`
- `feat-15d19c085e54`
- `feat-ffea4a7f1db1`
- `feat-cb539293ca37`
- `feat-2f2e93a62079`
- `feat-c44ce4013f55`
- `feat-5ba9a6fe7c9c`
- `feat-d9d025eea02c`

Additional prioritized items implemented in this execution slice:
- `feat-877c7607ca0b`
- `feat-6b106e5b235b`
- `feat-3c32f39c49cd`
- `feat-3fe373d691ed`
- `feat-1f6030b916fa`
- `feat-0179c667b65d`
- `feat-5f42112ad978`
- `feat-74740c05b737`
- `feat-91ea2930eea1`
- `feat-194d6286cce9`
- `feat-a17388d1d615`
- `feat-e9c71ea2a6f8`
- `feat-8ff94565c317`
- `feat-cfccffcf438b`
- `feat-a747d74d9f54`
- `feat-9f6bf385f44b`
- `feat-976396e01283`
- `feat-a001e05bef28`
- `feat-7bb3eeabbb20`
- `feat-084bced806d6`
