---
phase: 02-streamlit-experience-ethics-copy
plan: 02
subsystem: ui
tags: [streamlit, gpt2, nltk, ui-consistency]
requires:
  - phase: 02-streamlit-experience-ethics-copy
    provides: shared UI contract helpers from 02-01
provides:
  - NLTK and GPT-2 apps consume shared mode guidance, limitations, and reminder helpers
  - static entrypoint contract tests for app.py and test.py
affects: [app.py, test.py, tests, phase-02-cross-app-parity]
tech-stack:
  added: []
  patterns: [shared-sidebar-contract, static-entrypoint-contract-tests]
key-files:
  created:
    - tests/test_nltk_gpt2_streamlit_contract.py
  modified:
    - app.py
    - test.py
key-decisions:
  - "Used static source contract tests for Streamlit scripts to keep verification fast and deterministic."
patterns-established:
  - "Each app sidebar now includes mode guidance + shared limitations helper blocks."
requirements-completed: [UI-01, UI-02, QLT-03]
duration: 29min
completed: 2026-04-02
---

# Phase 02 Plan 02: NLTK/GPT-2 UX Contract Summary

**Aligned the NLTK and GPT-2 Streamlit entrypoints around shared ethics/mode guidance copy and added source-level contract tests to prevent UI drift.**

## Performance

- Duration: 29 min
- Started: 2026-04-02T08:30:00Z
- Completed: 2026-04-02T08:59:00Z
- Tasks: 2
- Files modified: 3

## Accomplishments
- Integrated shared UI contract helpers in `app.py` and `test.py`.
- Added sidebar mode guidance and shared limitations blocks to both entrypoints.
- Added verdict-level reminder caption and corrected NLTK metric field access to `avg_word_length`.
- Added static contract tests to lock launch hints, helper usage, and core analyze labels.

## Task Commits

1. Task 1: Integrate shared UI contract into NLTK and GPT-2 apps - 76cd1e4 (feat)
2. Task 2: Add static entrypoint contract tests for NLTK and GPT-2 apps - 34d0326 (test)

## Files Created/Modified
- app.py - Shared helper imports, mode guidance, limitation block, reminder caption, and metric field correction.
- test.py - Shared helper imports, mode guidance, limitation block, and reminder caption.
- tests/test_nltk_gpt2_streamlit_contract.py - Static source contract checks for NLTK/GPT-2 entrypoints.

## Decisions Made
- Kept verification lightweight by checking source-level contract markers instead of booting Streamlit runtime in tests.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- NLTK and GPT-2 UI contracts are stable and ready for ensemble parity updates in Plan 02-03.

## Self-Check: PASSED
- Verified key files exist on disk.
- Verified task commits are present in git log.
