# Phase 3: Quality gate & documentation truth - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-02
**Phase:** 03-quality-gate-documentation-truth
**Areas discussed:** Test gate strictness, Source-of-truth command set, Documentation alignment strategy, Deployment doc scope

---

## Test gate strictness

| Option | Description | Selected |
|--------|-------------|----------|
| A | Phase passes when core local suite and targeted contract tests pass; slow model-heavy tests optional but documented | yes |
| B | Phase passes only with full suite including slow GPT-2/RoBERTa paths every run | |
| C | Focus on docs only with minimal smoke tests | |

**User's choice:** A (recommended)
**Notes:** User confirmed "use all recommended".

---

## Source-of-truth command set

| Option | Description | Selected |
|--------|-------------|----------|
| A | Standardize on Makefile commands, with Windows-safe Python equivalents where needed | yes |
| B | Standardize only on raw python and streamlit commands | |
| C | Keep mixed command style with only obvious breakage fixes | |

**User's choice:** A (recommended)
**Notes:** User confirmed "use all recommended".

---

## Documentation alignment strategy

| Option | Description | Selected |
|--------|-------------|----------|
| A | Update docs to match implemented behavior; change code only when clearly broken | yes |
| B | Change code to match current documentation wording | |
| C | Hybrid case-by-case strategy | |

**User's choice:** A (recommended)
**Notes:** User confirmed "use all recommended".

---

## Deployment doc scope

| Option | Description | Selected |
|--------|-------------|----------|
| A | Validate and correct local run plus Docker and docker-compose paths used in this repo | yes |
| B | Include cloud sections for full executable accuracy checks | |
| C | Only local plus default app.py deployment path | |

**User's choice:** A (recommended)
**Notes:** User confirmed "use all recommended".

---

## Claude's Discretion

- Minor wording and structure improvements that do not change requirements intent.

## Deferred Ideas

- None.
