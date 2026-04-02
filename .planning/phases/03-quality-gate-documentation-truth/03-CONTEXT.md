# Phase 3: Quality gate & documentation truth - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish a reliable regression quality gate and align public documentation with current repository behavior for install, run modes, API usage, and deployment instructions, without adding new product capabilities.

</domain>

<decisions>
## Implementation Decisions

### Test gate strictness
- **D-01:** Phase 3 passes when the core local test suite and targeted contract tests pass, while slow model-heavy tests remain optional but explicitly documented as optional verification steps.

### Source-of-truth command set
- **D-02:** Documentation should standardize on Makefile commands as the primary path, with Windows-safe Python command equivalents included where needed.

### Documentation alignment strategy
- **D-03:** Documentation is updated to match implemented behavior in code and repository artifacts. Code changes are only made when behavior is clearly broken.

### Deployment documentation scope
- **D-04:** Validate and correct local run, Docker, and docker-compose documentation paths used by this repository for this phase.

### Claude's Discretion
- Exact wording updates for consistency and readability while preserving technical meaning.
- Selection of the most practical command examples when multiple equivalent commands exist.
- Minor non-behavioral doc structure improvements (section order, headings, quick-start emphasis).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirement anchors
- `.planning/ROADMAP.md` - Phase 3 goal, dependencies, requirements, and success criteria.
- `.planning/REQUIREMENTS.md` - Requirement definitions for QLT-01 and DOC-01.
- `.planning/PROJECT.md` - Core value, local-first constraints, and ethical positioning.

### Test and quality conventions
- `.planning/codebase/TESTING.md` - Current pytest and Makefile testing patterns.
- `.planning/codebase/CONVENTIONS.md` - Formatting/linting/test command conventions and import patterns.
- `Makefile` - Canonical local test/lint/format command targets.
- `pytest.ini` - Registered markers (including slow) used by the test suite.

### Documentation truth targets
- `README.md` - Install/run/limitations guidance and testing command references.
- `docs/API.md` - Programmatic usage contract and analyzer behavior documentation.
- `docs/DEPLOYMENT.md` - Local and container deployment instructions.

### Runtime and deployment artifacts
- `Dockerfile` - Container runtime assumptions and default app launch behavior.
- `docker-compose.yml` - Multi-service launch commands and mode-specific ports.
- `Procfile` - Process launch command used in process-based deployment targets.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Test suite modules under `tests/` already cover analyzers, ensemble behavior, text processing, and result models.
- Static contract-test pattern from Phase 2 (`tests/test_*_streamlit_contract.py`) can be reused for lightweight doc/behavior truth checks.
- Makefile targets (`test`, `lint`, `format`) provide a central command contract for local quality gate execution.

### Established Patterns
- Pytest is the canonical runner with optional slow marker usage for model-heavy tests.
- Streamlit entrypoints are root scripts (`app.py`, `test.py`, `ensemble.py`) and are documented as explicit run modes.
- Documentation has historically drifted from code in some areas, so this phase should treat repository files as source of truth and update docs accordingly.

### Integration Points
- Documentation edits must stay synchronized across `README.md`, `docs/API.md`, and `docs/DEPLOYMENT.md`.
- Quality-gate verification connects to both lightweight contract tests and core analyzer tests under `tests/`.
- Deployment truth checks connect directly to `Dockerfile`, `docker-compose.yml`, and `Procfile`.

</code_context>

<specifics>
## Specific Ideas

No additional custom variants requested beyond the recommended defaults selected in discuss mode.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 03-quality-gate-documentation-truth*
*Context gathered: 2026-04-02*
