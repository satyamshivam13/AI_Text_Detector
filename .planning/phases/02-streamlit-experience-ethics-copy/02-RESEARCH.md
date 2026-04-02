# Phase 2: Streamlit experience & ethics copy - Research

**Researched:** 2026-04-02
**Status:** Ready for planning

## Objective

Research how to implement Phase 2 so the three Streamlit entrypoints (`app.py`, `test.py`, `ensemble.py`) launch consistently, show metrics-aligned visualizations, and communicate limitation/ethics copy consistently with project docs.

## Inputs Reviewed

- `.planning/phases/02-streamlit-experience-ethics-copy/02-CONTEXT.md`
- `.planning/ROADMAP.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `app.py`
- `test.py`
- `ensemble.py`
- `src/utils/visualization.py`
- `.streamlit/config.toml`
- `README.md`
- `docs/API.md`
- `docs/DEPLOYMENT.md`

## Requirements Targeted

- `UI-01`: Launch documented Streamlit entrypoints reliably.
- `UI-02`: Visualizations align with analyzer metrics and contract.
- `QLT-03`: User-facing limitation copy reflects README ethical guidance.

## Current State Findings

1. All three apps already have similar structure and duplicated CSS blocks, but wording/sections differ.
2. Each app has analyzer-specific sidebar guidance; limitation/ethics copy is present in varying depth and placement.
3. Chart generation is centralized in `ChartGenerator` (`src/utils/visualization.py`), enabling consistent visualization semantics.
4. Entrypoint docs are present in `README.md` and deployment instructions, but in-app launch/mode guidance is not standardized.
5. Streamlit theme defaults exist in `.streamlit/config.toml`, while app-level CSS overrides are inline and repeated.

## Implementation Recommendations

### standard_stack

- Keep Streamlit as the sole UI layer for this phase.
- Keep existing analyzers and `ChartGenerator`; do not add frontend frameworks.
- Continue using `@st.cache_resource` for heavy analyzer/chart loader consistency.

### architecture_patterns

- Introduce shared UI helper functions for repeated page blocks (header, verdict card, warning rendering, disclaimer panel) to reduce drift across three scripts.
- Keep analyzer-specific behavior in each entry script, but make section order and naming consistent:
  1. Header and mode identity
  2. Input and analyze action
  3. Verdict + confidence + timing summary
  4. Metrics and visualizations
  5. Limitations/ethics reminder
- Map displayed metrics to `AnalysisResult` contract fields (verdict, confidence, confidence_level, analysis_time, scores, key metrics).

### dont_hand_roll

- Do not implement custom chart math in app scripts when `ChartGenerator` already provides gauge/radar/frequency/sentence charts.
- Do not create ad-hoc result schemas in UI code; consume `AnalysisResult` directly.
- Do not duplicate long-form ethics text in three places without a shared source string/helper.

## Consistency Contract for Phase 2

1. **Launch contract (UI-01):**
- `streamlit run app.py`, `streamlit run test.py`, `streamlit run ensemble.py` all start cleanly.
- Each app clearly indicates which analyzer mode is active.

2. **Visualization contract (UI-02):**
- Core metric summary is always visible before deep charts.
- Charts shown are derived from available analyzer output and not synthetic placeholders.
- Empty/no-data chart states remain explicit and non-breaking.

3. **Ethics/copy contract (QLT-03):**
- Every app shows persistent limitations text: probabilistic output, English-first constraints, and not sole proof of authorship.
- Result-level reminder reinforces responsible interpretation.

## common_pitfalls

- Pitfall: Divergent copy across apps causes policy inconsistency.
  - Mitigation: centralize limitation text and reuse in all entrypoints.
- Pitfall: Visual sections differ in order/labels, confusing users switching modes.
  - Mitigation: unify section sequence and heading conventions.
- Pitfall: Ensemble app includes analyzer detail while others omit equivalent transparency.
  - Mitigation: define a shared minimum result panel plus mode-specific extensions.
- Pitfall: README accuracy numbers/weights drift from UI text.
  - Mitigation: avoid hardcoding fragile values in copy unless sourced from code/config.

## Test and Verification Implications

- Add/update lightweight UI behavior tests where feasible (at minimum smoke checks for entry scripts and rendering helpers).
- Validate ethics text presence via deterministic string assertions in app outputs/helpers.
- Verify docs/UI alignment checks for launch commands and mode descriptions.

## Plan Guidance

Recommended planning split for execution quality:

1. Shared UI/copy primitives and app normalization pass.
2. Visualization alignment pass for all three apps.
3. Docs and consistency verification pass (README/API/deployment references and UI wording parity).

## Research Outcome

Research complete. No external dependency research is required for this phase; implementation is primarily codebase-consistency and UX/copy alignment within existing Streamlit architecture.

---

*Phase: 02-streamlit-experience-ethics-copy*
*Research completed: 2026-04-02*
