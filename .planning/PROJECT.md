# AI Text Detector

## What This Is

A Python toolkit and set of Streamlit applications that estimate how likely text is to be machine-generated, using statistical (NLTK), perplexity (GPT-2), optional transformer classification (RoBERTa), and weighted ensemble fusion. It targets developers, educators, and researchers who want local, explainable signals rather than a single opaque score and who accept documented accuracy limits.

## Core Value

Users get a transparent, multi-signal AI-likelihood assessment (verdict, confidence, metrics, narrative explanation) they can reason about, with ethical framing that results are probabilistic and not sole proof of authorship.

## Current State

- v1.0 shipped on 2026-04-02.
- Phase 1 established structured analyzer outputs and contract coverage.
- Phase 2 aligned Streamlit apps with shared ethics and mode-guidance copy.
- Phase 3 locked the quality-gate command contract and aligned documentation to executable repo truth.

## Requirements

### Validated

- ✓ Run NLTK-based statistical analysis on input text.
- ✓ Run GPT-2 sliding-window perplexity analysis.
- ✓ Run weighted ensemble of RoBERTa, GPT-2, and NLTK with configurable weights.
- ✓ Normalize pipeline: validate and clean text, compute shared metrics, verdict, and explanation.
- ✓ Return structured AnalysisResult output with scores, metrics, timing, and JSON export.
- ✓ Plotly/Matplotlib visualizations in Streamlit.
- ✓ Centralized settings and thresholds.
- ✓ Automated tests for analyzers, ensemble, and utilities.
- ✓ Docker and deployment documentation.
- ✓ Documented Streamlit run modes and user-facing limitation copy.
- ✓ Deterministic quality-gate command contract and optional slow-test policy.
- ✓ Repository docs match actual entrypoints and deployment artifacts.

### Active

- [ ] MDL-01: Fine-tuned or hub-hosted RoBERTa support with documented accuracy expectations.
- [ ] MDL-02: Optional batch / CLI interface for non-Streamlit automation.
- [ ] ENG-01: Continuous integration running lint + tests on push.
- [ ] ENG-02: Dependency alignment work for long-term maintainability.

### Out of Scope

- Sole legal or academic judgment - tool is advisory; human review and multiple signals required.
- Hosted multi-tenant SaaS - not part of current repo scope unless explicitly added later.
- Non-English-first optimization - README documents English focus; other languages remain best-effort unless scoped.

## Context

Brownfield monolith: Streamlit scripts at repo root import src analyzers and utilities. Hugging Face and NLTK models download on first use; resource use is significant for transformer paths. A full codebase map lives under .planning/codebase/ for planning and onboarding.

## Constraints

- Tech stack: Python 3.8+, Streamlit, PyTorch, Transformers, NLTK.
- Runtime: Substantial RAM for GPT-2/ensemble; GPU optional.
- Privacy: Processing is local; no requirement to send user text to third-party APIs for core detection.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Initialize GSD from repo + codebase map | Existing codebase was already documented and mapped | Completed |
| Defer parallel domain research agents | Stack and product were already mapped; no external pivot was needed | Completed |
| Complete Phase 1 with explicit contract coverage | Ensure DET-01..DET-04 and QLT-02 are regression-safe and documented | Completed |
| Use shared UI copy helpers for all Streamlit entrypoints | Prevent copy drift across app.py, test.py, and ensemble.py | Completed |
| Keep quality-gate verification deterministic and file-content based | Avoid environment flakiness and hidden runtime dependencies | Completed |
| Align docs to executable repository truth | Reduce mismatch between README, API, deployment, and code | Completed |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition**:

1. Requirements invalidated? Move to Out of Scope with reason.
2. Requirements validated? Move to Validated with phase reference.
3. New requirements emerged? Add to Active.
4. Decisions to log? Add to Key Decisions.
5. What This Is still accurate? Update if drifted.

**After each milestone**:

1. Full review of all sections.
2. Core Value check - still the right priority.
3. Audit Out of Scope - reasons still valid.
4. Update Context with current state.

---
*Last updated: 2026-04-02 after v1.0 milestone archive*
