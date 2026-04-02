# Roadmap: AI Text Detector

## Overview

This milestone closes the loop on the brownfield product: **analysis paths** return a consistent, validated structured contract; **Streamlit entrypoints** match docs and show honest limitation messaging with working visuals; **tests and published docs** stay aligned so developers and educators can trust local runs.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions via `/gsd-insert-phase`

- [x] **Phase 1: Detection pipeline & structured results** â€” NLTK, GPT-2, and ensemble paths return validated `AnalysisResult` with verdict, metrics, explanation, and timing (completed 2026-04-02)
- [ ] **Phase 2: Streamlit experience & ethics copy** â€” Documented apps launch; charts match metrics; user-facing text states limitations
- [ ] **Phase 3: Quality gate & documentation truth** â€” Core tests pass; README, API, and deployment docs match behavior

## Phase Details

### Phase 1: Detection pipeline & structured results
**Goal**: Callers (programmatic or via apps) get consistent, validated analysis output across NLTK, GPT-2, and ensemble modes with documented weighting behavior.
**Depends on**: Nothing (first phase)
**Requirements**: DET-01, DET-02, DET-03, DET-04, QLT-02
**Success Criteria** (what must be TRUE):
  1. A caller can run NLTK analysis on supplied text and receive scores, verdict metadata, and timing where applicable.
  2. A caller can run GPT-2 perplexity analysis on supplied text and receive scores, verdict metadata, and timing where applicable.
  3. A caller can run ensemble analysis combining GPT-2 and NLTK (and optional RoBERTa when enabled) with behavior that matches documented weighting.
  4. Every analysis path returns a structured result including verdict, confidence, key metrics, human-readable explanation, and timing where applicable.
  5. Short, empty, or invalid input produces validation warnings rather than silent failure.
**Plans**: 4 plans
Plans:
- [x] 01-01-PLAN.md â€” BaseAnalyzer early-return timing + contract tests (DET-04, QLT-02)
- [x] 01-02-PLAN.md â€” Ensemble validation parity + documented weighting (DET-03, DET-04, QLT-02)
- [x] 01-03-PLAN.md â€” Ensemble tests, fusion unit test, API.md (DET-03, DET-04, QLT-02)
- [x] 01-04-PLAN.md â€” NLTK/GPT-2/result contract tests (DET-01, DET-02, DET-04, QLT-02)
**UI hint**: no

### Phase 2: Streamlit experience & ethics copy
**Goal**: Users running the documented Streamlit apps see metrics-consistent visuals and copy that reflects accuracy limits and non-proof-of-authorship stance.
**Depends on**: Phase 1
**Requirements**: UI-01, UI-02, QLT-03
**Success Criteria** (what must be TRUE):
  1. User can launch documented Streamlit entrypoints for NLTK, GPT-2, and ensemble modes (`app.py`, `test.py`, `ensemble.py`) as described in project docs.
  2. User can view visualizations (charts, gauges, comparison views) that align with the metrics returned for the selected analyzer.
  3. User-facing copy in the apps states limitations (accuracy, English focus, no sole proof of authorship) consistent with README ethical guidance.
**Plans**: 3 plans
Plans:
- [ ] 02-01-PLAN.md — Shared UI copy contract + tests (UI-02, QLT-03)
- [ ] 02-02-PLAN.md — NLTK/GPT-2 Streamlit normalization + contract tests (UI-01, UI-02, QLT-03)
- [ ] 02-03-PLAN.md — Ensemble Streamlit normalization + contract tests (UI-01, UI-02, QLT-03)
**UI hint**: yes

### Phase 3: Quality gate & documentation truth
**Goal**: Regression safety and single source of truth for install, run modes, API usage, and deployment match the repo.
**Depends on**: Phase 2
**Requirements**: QLT-01, DOC-01
**Success Criteria** (what must be TRUE):
  1. Automated tests pass for core analyzers, ensemble behavior, text processing, and result models (`tests/`).
  2. `README.md` accurately describes install, run modes, and limitations; `docs/API.md` and `docs/DEPLOYMENT.md` match actual entrypoints and deployment artifacts (Docker, compose, commands).
**Plans**: TBD

## Progress

**Execution Order:** 1 â†’ 2 â†’ 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Detection pipeline & structured results | 4/4 | Complete | 2026-04-02 |
| 2. Streamlit experience & ethics copy | 0/3 | Planned | - |
| 3. Quality gate & documentation truth | 0/TBD | Not started | - |

