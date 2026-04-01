# Phase 1: Detection pipeline & structured results - Context

**Gathered:** 2026-04-02  
**Status:** Ready for planning

**Note:** Interactive gray-area selection was not available in-session. Decisions below are **brownfield-aligned defaults** (current code + ROADMAP success criteria). Revise this file before `/gsd:plan-phase 1` if you want different locks.

<domain>
## Phase Boundary

Callers (programmatic or via existing Streamlit apps) receive **consistent, validated** output from NLTK, GPT-2, and ensemble analysis paths: shared preprocessing, `AnalysisResult` shape, verdict/confidence/metrics/explanation, warnings for bad input, and total `analysis_time`. **No new user-facing UI** in this phase (`**UI hint**`: no). Streamlit-specific polish is Phase 2.

</domain>

<decisions>
## Implementation Decisions

### Structured result contract

- **D-01:** `AnalysisResult` (`src/models/result.py`) is the **canonical** programmatic contract; `to_dict()` / `to_json()` field names and meanings must remain stable for this milestone—prefer **additive** fields over renames/removals.
- **D-02:** Verdict and confidence semantics stay aligned with `Verdict` / `ConfidenceLevel` in `src/config/settings.py`—do not introduce parallel enum systems in this phase.

### Input validation and warnings (QLT-02)

- **D-03:** **Empty** cleaned input: return immediately with `Verdict.UNCERTAIN`, zero confidence, explicit warning and explanation (existing `BaseAnalyzer.analyze` behavior)—**no** silent empty analysis.
- **D-04:** **Short** text (below `ThresholdConfig.min_text_length` / `recommended_text_length`): **warn** via `result.add_warning` but **still run** analysis when non-empty—matches current `src/analyzers/base_analyzer.py` and README “minimum length” guidance.

### Ensemble behavior (DET-03)

- **D-05:** Default weights remain **RoBERTa 0.0**, **GPT-2 0.65**, **NLTK 0.35** in `EnsembleAnalyzer` until fine-tuned RoBERTa is explicitly supported in a later scope; enabling RoBERTa is **opt-in** via weight configuration, not default behavior change in Phase 1.
- **D-06:** Documented weighting behavior in Phase 1 means: fused verdict/explanation must **reflect** active weights and which backends ran; tests or docstrings should make non-zero RoBERTa paths explicit when touched.

### Timing and errors

- **D-07:** Expose **total** wall-clock time per `analyze()` call as `AnalysisResult.analysis_time` (seconds, rounded to 3 decimals)—consistent with `BaseAnalyzer` and `EnsembleAnalyzer` today. **Per-sub-analyzer** timings are **not** required for Phase 1 success unless already present (Claude may add later under discretion).
- **D-08:** On uncaught exceptions in analysis: **UNCERTAIN** verdict, **VERY_LOW** confidence, user-facing warning string, logged exception with `exc_info`—match existing `BaseAnalyzer` try/except block.

### Claude's Discretion

- Whether to add optional `timing_breakdown` or extend `DetectionScore` metadata for ensemble diagnostics.
- Minor threshold tuning in `ThresholdConfig` if tests and docs are updated together.
- Internal refactors that do not change the external `AnalysisResult` contract.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Planning and requirements

- `.planning/ROADMAP.md` — Phase 1 goal, success criteria, requirements DET-01–04, QLT-02
- `.planning/REQUIREMENTS.md` — v1 requirement IDs and traceability
- `.planning/PROJECT.md` — core value, constraints, validated capabilities

### Architecture and risks

- `.planning/codebase/ARCHITECTURE.md` — analyzer hierarchy, data flow, ensemble path
- `.planning/codebase/CONCERNS.md` — known debt (RoBERTa, pydantic vs dataclass, etc.)

### Code entry points

- `src/analyzers/base_analyzer.py` — template method, validation, timing, error handling
- `src/analyzers/ensemble_analyzer.py` — weighting and fusion
- `src/analyzers/nltk_analyzer.py` — NLTK path
- `src/analyzers/gpt2_analyzer.py` — GPT-2 path
- `src/analyzers/roberta_analyzer.py` — RoBERTa path (optional / zero weight default)
- `src/models/result.py` — `AnalysisResult`, serialization
- `src/config/settings.py` — thresholds, enums, `get_settings()`
- `src/utils/text_processing.py` — cleaning and metrics
- `docs/API.md` — public usage expectations (keep aligned when contract changes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable assets

- **`BaseAnalyzer`**: Central pipeline for clean → metrics → `_perform_analysis` → verdict → explanation → timing.
- **`TextProcessor`**: Shared cleaning and `compute_metrics` across analyzers.
- **`EnsembleAnalyzer`**: Overrides `analyze()` to compose NLTK/GPT-2/RoBERTa with configured weights.

### Established patterns

- **Template Method** for single analyzers; ensemble is a **composition** special case.
- **Settings**: `get_settings()` / `ThresholdConfig` drive min/recommended length warnings.
- **Result shape**: Flat `AnalysisResult` plus `scores: List[DetectionScore]` and nested `metrics`.

### Integration points

- Streamlit apps (`app.py`, `test.py`, `ensemble.py`) call `analyzer.analyze(text)` and consume `AnalysisResult`—Phase 1 changes must keep those calls working.

</code_context>

<specifics>
## Specific Ideas

No user-supplied product references in this session—defaults driven by existing implementation and README limitations (English, probabilistic, not legal proof).

</specifics>

<deferred>
## Deferred Ideas

- Streamlit copy, charts, and ethics messaging — **Phase 2**
- CI, full doc-audit sweep — **Phase 3**
- Fine-tuned RoBERTa as default signal — future milestone / backlog (see `README.md` fine-tuning section)

### Reviewed Todos (not folded)

None — `todo match-phase 1` returned no matches.

</deferred>

---

*Phase: 01-detection-pipeline-structured-results*  
*Context gathered: 2026-04-02*
