# AI Text Detector

## What This Is

A Python toolkit and set of Streamlit applications that estimate how likely text is to be machine-generated, using statistical (NLTK), perplexity (GPT-2), optional transformer classification (RoBERTa), and weighted ensemble fusion. It targets developers, educators, and researchers who want **local, explainable** signals—not a single opaque score—and who accept documented accuracy limits.

## Core Value

Users get a **transparent, multi-signal** AI-likelihood assessment (verdict, confidence, metrics, narrative explanation) they can reason about, with ethical framing that results are probabilistic and not sole proof of authorship.

## Requirements

### Validated

<!-- Inferred from existing codebase — see `.planning/codebase/ARCHITECTURE.md` and `STACK.md`. -->

- ✓ Run NLTK / Brown-corpus–style statistical analysis on input text — existing (`src/analyzers/nltk_analyzer.py`, `app.py`)
- ✓ Run GPT-2 sliding-window perplexity analysis — existing (`src/analyzers/gpt2_analyzer.py`, `test.py`)
- ✓ Run weighted ensemble of RoBERTa, GPT-2, and NLTK with configurable weights — existing (`src/analyzers/ensemble_analyzer.py`, `ensemble.py`; RoBERTa often zero-weight until fine-tuned)
- ✓ Normalize pipeline: validate/clean text, compute shared metrics, verdict and explanation — existing (`src/analyzers/base_analyzer.py`, `src/utils/text_processing.py`)
- ✓ Return structured `AnalysisResult` (scores, metrics, timing, JSON export) — existing (`src/models/result.py`)
- ✓ Plotly/Matplotlib visualizations in Streamlit — existing (`src/utils/visualization.py`, app entry scripts)
- ✓ Centralized settings and thresholds — existing (`src/config/settings.py`)
- ✓ Automated tests for analyzers, ensemble, and utilities — existing (`tests/`)
- ✓ Docker and deployment documentation — existing (`Dockerfile`, `docker-compose.yml`, `docs/DEPLOYMENT.md`)

### Active

- [x] Phase 1 validated in code and tests: structured analyzer outputs, deterministic ensemble weighting coverage, and API contract documentation alignment
- [ ] Keep **documented behavior** in `README.md`, `docs/API.md`, and code aligned as the codebase changes
- [ ] Address high-impact maintainability items called out in `.planning/codebase/CONCERNS.md` (e.g. dependency drift, RoBERTa defaults, validation strategy)
- [ ] Preserve **local-first** processing and clear limitation/ethics messaging in user-facing copy

### Out of Scope

- **Sole legal or academic judgment** — Tool is advisory; human review and multiple signals required (per product stance)
- **Hosted multi-tenant SaaS** — Not part of current repo scope unless explicitly added later
- **Non-English-first optimization** — README documents English focus; other languages remain best-effort unless scoped

## Context

Brownfield monolith: Streamlit scripts at repo root import `src/` analyzers and utilities. Hugging Face and NLTK models download on first use; resource use is significant for transformer paths. A full codebase map lives under `.planning/codebase/` for planning and onboarding.

## Constraints

- **Tech stack**: Python 3.8+, Streamlit, PyTorch, Transformers, NLTK — see `requirements.txt` and `setup.py`
- **Runtime**: Substantial RAM for GPT-2/ensemble; GPU optional
- **Privacy**: Processing is local; no requirement to send user text to third-party APIs for core detection

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Initialize GSD from repo + codebase map (no live interview) | User invoked `/gsd/new-project` on an existing, documented codebase | — Pending |
| Defer parallel domain research agents | Stack and product are already mapped in `.planning/codebase/`; external ecosystem research can be added before major pivots | — Pending |
| Complete Phase 1 with explicit contract coverage | Ensure DET-01..DET-04 and QLT-02 are regression-safe and documented | 2026-04-02: Completed via plans 01-01 through 01-04 |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):

1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):

1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-02 after Phase 1 execution*
