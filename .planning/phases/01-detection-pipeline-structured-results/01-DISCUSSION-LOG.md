# Phase 1: Detection pipeline & structured results - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.  
> Decisions are captured in `01-CONTEXT.md`.

**Date:** 2026-04-02  
**Phase:** 1 — Detection pipeline & structured results  
**Areas discussed:** Result contract, validation behavior, ensemble defaults, timing, error handling  
**Session type:** Non-interactive — defaults applied (no AskUserQuestion / multi-select in environment)

---

## Structured result contract

| Option | Description | Selected |
|--------|-------------|----------|
| Stable `to_dict` keys, additive changes | Preserve API consumers; extend fields if needed | ✓ |
| Allow breaking renames in Phase 1 | Faster internal cleanup | |

**User's choice:** Stable contract with additive preference (brownfield default).  
**Notes:** Aligns with DET-04 and programmatic use in `docs/API.md`.

---

## Short / empty input (QLT-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Empty → early return with warnings; short → warn and still analyze | Current `BaseAnalyzer` behavior | ✓ |
| Short text → block analysis entirely | Stricter gate | |

**User's choice:** Match existing `ThresholdConfig` warning behavior.  
**Notes:** `min_text_length` 50, `recommended_text_length` 200 in `settings.py`.

---

## Ensemble defaults (DET-03)

| Option | Description | Selected |
|--------|-------------|----------|
| RoBERTa weight 0.0 default; GPT-2 / NLTK only | Documented in code comments | ✓ |
| Enable RoBERTa by default in Phase 1 | Would need fine-tuned model | |

**User's choice:** Keep disabled RoBERTa default; weights GPT-2 0.65 / NLTK 0.35.  
**Notes:** README states RoBERTa needs fine-tuning.

---

## Timing visibility

| Option | Description | Selected |
|--------|-------------|----------|
| Single `analysis_time` on `AnalysisResult` | Matches `BaseAnalyzer` and ensemble | ✓ |
| Mandatory per-backend timing fields | Optional future enhancement | |

**User's choice:** Total time only required for Phase 1.  
**Notes:** Left to Claude's discretion to add breakdown later if useful.

---

## Analysis errors

| Option | Description | Selected |
|--------|-------------|----------|
| UNCERTAIN + warning + log exception | Current `BaseAnalyzer` except block | ✓ |
| Re-raise after logging | Would change caller contract | |

**User's choice:** Preserve user-facing soft failure.  
**Notes:** Consistent across NLTK / GPT-2 / ensemble entry paths.

---

## Claude's Discretion

- Optional diagnostic timing metadata, threshold tweaks with test/doc updates, internal refactors without breaking `AnalysisResult` consumers.

## Deferred Ideas

- Phase 2 UI/ethics; Phase 3 tests/docs truth; RoBERTa-first-class later.
