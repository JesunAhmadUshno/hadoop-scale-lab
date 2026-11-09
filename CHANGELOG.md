# Changelog

All notable changes to this project. Format: Keep a Changelog 1.1.
Versions follow Semantic Versioning; no release is tagged yet.

## [Unreleased]

### Added
- 2026-11-09: Phase 2 complete. The timed matrix ran on the R610:
  H1 CONFIRMED, H2 INCONCLUSIVE (small-file cell stopped
  unmeasured, DECISIONS.md D11), H3 INCONCLUSIVE, H4 REFUTED.
  RESULTS.md generated from results/raw_runs.jsonl (65 records).
  DECISIONS.md D4 to D14 record the Phase 2 environment
  completions and the ladder re-anchor; the Phase 2 entries were
  renumbered one up in the standard-v2 merge (see the numbering
  note in DECISIONS.md). Jev claim_check at close: REVIEW (noul
  0.24), hand-verified, recorded in AUDIT.md.

### Changed
- 2026-11-08: Adopted the portfolio standard v2. README opens with the
  question, headline, field, job family and verdict. AUDIT.md is the
  report; its grade moved out of the public repo (grades are
  internal). The lock is tagged proposal-v1 on d06513e, and a test
  fails if PREREGISTRATION.md changes by one byte. CI checks that
  RESULTS.md regenerates unchanged. CodeQL and Dependabot added; main
  protected.

### Added
- 2026-11-08: DECISIONS.md D3: timed cells avoid the R610's scheduled
  jobs from the P23 recovery tests.
- 2026-11-08: Study harness, corpus pipeline, DuckDB baseline, capped
  Compose cluster, Phase 2 driver; byte-equivalence of both jobs on a
  210 MB real-corpus slice.
- 2026-11-08: Pre-registration (d06513e), before any code or run.
