# Phase 2: Streamlit experience & ethics copy - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Improve the three documented Streamlit entrypoints so they launch reliably, present visuals that map clearly to analyzer metrics, and show consistent limitation messaging (accuracy limits, English focus, non-proof-of-authorship stance) aligned with repository docs.

</domain>

<decisions>
## Implementation Decisions

### Cross-app UI consistency
- **D-01:** Keep each app's analyzer identity (NLTK, GPT-2, ensemble) but align shared page structure: header, input area, analyze action, result summary, metric/visualization sections, and disclaimer placement.
- **D-02:** Reuse shared styling patterns already present in the Streamlit scripts (card containers, verdict styles, sidebar settings blocks) rather than introducing a new design system.

### Visualization contract display
- **D-03:** Standardize result presentation to show core contract fields first (verdict, confidence, timing, key metrics) before detailed charts, ensuring UI-02 traceability.
- **D-04:** Keep analyzer-specific chart content, but present it in a consistent section flow so users can compare outputs across `app.py`, `test.py`, and `ensemble.py` without re-learning layout.

### Ethics and limitation copy
- **D-05:** Use a persistent sidebar limitations block in each app with concise language covering probabilistic output, no sole proof of authorship, and English-first limitations.
- **D-06:** Add a short reminder near final results to reinforce responsible interpretation without overwhelming the main workflow.

### Entry-point and run guidance in-app
- **D-07:** Add lightweight in-app guidance for each entrypoint (what mode this app is running, expected compute/runtime notes, and where to run alternate modes).
- **D-08:** Keep guidance compact and non-blocking (sidebar/help callouts), preserving primary analyze flow.

### the agent's Discretion
- Exact wording polish for limitation copy so tone stays clear and non-alarmist.
- Micro-layout details (spacing, section headers, icon usage) while preserving existing visual language.
- Whether to implement shared helper functions for repeated Streamlit blocks or keep app-local duplication when simpler.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` — Phase 2 goal, requirements, and success criteria.
- `.planning/REQUIREMENTS.md` — UI-01, UI-02, QLT-03 requirement definitions and traceability.
- `.planning/PROJECT.md` — core value and ethical positioning constraints.

### Existing Streamlit entrypoints
- `app.py` — NLTK Streamlit UX baseline and current visual sections.
- `test.py` — GPT-2 Streamlit entrypoint behavior and copy baseline.
- `ensemble.py` — ensemble entrypoint UX and analyzer-combination messaging.
- `.streamlit/config.toml` — current shared Streamlit theme/server defaults.

### Visualization and result contract
- `src/utils/visualization.py` — chart generation patterns and available visual components.
- `src/models/result.py` — `AnalysisResult` fields that visuals/copy must reflect consistently.

### Product-facing guidance
- `README.md` — limitation language and documented run expectations.
- `docs/API.md` — analyzer contract fields relevant for metrics-to-UI consistency.
- `docs/DEPLOYMENT.md` — run/deploy instructions to keep entrypoint guidance aligned.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Streamlit scripts already include reusable UI motifs (header blocks, verdict cards, sidebar controls) that can be normalized across apps.
- `ChartGenerator` in `src/utils/visualization.py` already provides consistent chart creation patterns.
- `AnalysisResult.to_dict()` provides a stable field contract for mapping displayed metrics/copy.

### Established Patterns
- Each app is a root-level Streamlit script with direct analyzer loading and cached resources.
- Visual styling is currently inline CSS within each script; consistency work should reuse and align these patterns rather than replacing architecture.
- Result rendering follows a top-down flow (analyze trigger -> verdict -> metrics -> details/charts).

### Integration Points
- Main integration surface is the three entry scripts (`app.py`, `test.py`, `ensemble.py`).
- Shared copy/visual logic can optionally be factored into `src/utils/` helpers if it reduces duplication without adding complexity.
- Any UX wording changes should stay consistent with `README.md` and Phase 2 ethics constraints.

</code_context>

<specifics>
## Specific Ideas

- Keep analyzer-specific personality cues (icons/labels) while making navigation and interpretation flow consistent.
- Limitation messaging should be visible by default but concise enough not to dominate first-time use.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-streamlit-experience-ethics-copy*
*Context gathered: 2026-04-02*
