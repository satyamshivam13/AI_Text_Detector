# Requirements: AI Text Detector

**Defined:** 2026-04-02  
**Core Value:** Transparent, multi-signal AI-likelihood assessment with explanations—not a single opaque claim of certainty.

## v1 Requirements

Maintained capabilities and quality bars for the current brownfield product. Each item maps to roadmap phases.

### Detection & analysis

- [x] **DET-01**: User or API consumer can run NLTK-based statistical analysis on pasted or supplied text and receive scores and verdict metadata.
- [x] **DET-02**: User or API consumer can run GPT-2 perplexity-based analysis on supplied text and receive scores and verdict metadata.
- [x] **DET-03**: User or API consumer can run ensemble analysis combining GPT-2 and NLTK (and optional RoBERTa when enabled) with documented weighting behavior.
- [x] **DET-04**: Every analysis path returns a structured result including verdict, confidence, key metrics, human-readable explanation, and timing where applicable.

### User interface

- [ ] **UI-01**: User can launch documented Streamlit entrypoints for NLTK, GPT-2, and ensemble modes (`app.py`, `test.py`, `ensemble.py`).
- [ ] **UI-02**: User can view visualizations (e.g. charts, gauges, comparison views) consistent with implemented metrics for the selected analyzer.

### Quality, safety, and ethics

- [ ] **QLT-01**: Automated tests pass for core analyzers, ensemble behavior, text processing, and result models (`tests/`).
- [x] **QLT-02**: Short, empty, or invalid input is handled with validation warnings rather than silent failure.
- [ ] **QLT-03**: User-facing copy states limitations (accuracy, English focus, no sole proof of authorship) in line with README ethical guidance.

### Documentation & operations

- [ ] **DOC-01**: `README.md` describes install, run modes, and limitations; `docs/API.md` and `docs/DEPLOYMENT.md` remain consistent with actual entrypoints and deployment artifacts.

## v2 Requirements

Deferred enhancements—not in the initial GSD roadmap unless promoted.

### Models & accuracy

- **MDL-01**: First-class support for fine-tuned or hub-hosted RoBERTa (or successor) with documented accuracy expectations.
- **MDL-02**: Optional batch / CLI interface for non-Streamlit automation.

### Engineering

- **ENG-01**: Continuous integration running lint + tests on push.
- **ENG-02**: Dependency alignment (e.g. `pydantic` vs dataclasses) per `.planning/codebase/CONCERNS.md`.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Guaranteed correct authorship determination | Statistically impossible; product is advisory |
| Multi-language optimization in v1 | Explicitly English-first today |
| Managed cloud inference product | Not in repo scope unless added deliberately |

## Traceability

Which phases cover which requirements. Populated when `ROADMAP.md` is created.

| Requirement | Phase | Status |
|-------------|-------|--------|
| DET-01 | 1 | Complete |
| DET-02 | 1 | Complete |
| DET-03 | 1 | Complete |
| DET-04 | 1 | Complete |
| QLT-02 | 1 | Complete |
| UI-01 | 2 | Pending |
| UI-02 | 2 | Pending |
| QLT-03 | 2 | Pending |
| QLT-01 | 3 | Pending |
| DOC-01 | 3 | Pending |

**Coverage:**

- v1 requirements: 10 total  
- Mapped to phases: 10  
- Unmapped: 0

---
*Requirements defined: 2026-04-02*  
*Last updated: 2026-04-02 — Phase 1 requirements validated and traceability updated*
