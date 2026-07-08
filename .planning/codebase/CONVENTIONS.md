# Conventions

**Analysis Date:** 2026-07-06

## Code Style & Tooling

- **Black**, line length **100** (`Makefile`, CI).
- **isort** with `--profile=black`.
- **flake8** `--max-line-length=100` on `src/`, `tests/`, `app.py`,
  `gpt2_app.py`, `ensemble.py`. Config in `.flake8`: `extend-ignore = E203, W503`
  (Black-compatible) and `per-file-ignores` granting `E402` to the three entry
  scripts (they must `sys.path.insert` before importing `src.*`).
- **mypy** documented (`make lint` / README) with `--ignore-missing-imports`, but
  **not currently enforced in CI**.
- The **whole tree passes** black + isort + flake8 (enforced by CI on every push/PR).

## Naming

- `snake_case` modules/functions/vars; `PascalCase` classes; leading underscore
  for non-public methods (`_perform_analysis`, `_apply_input_cap`,
  `_combine_results`).
- Enums for fixed vocabularies (`Verdict`, `ConfidenceLevel`, `DetectionMethod`).

## Patterns

- `from __future__ import annotations` + `typing` imports across modules.
- **Config:** frozen `@dataclass(frozen=True)` blobs; mutable `Settings` behind
  `get_settings()` `@lru_cache` singleton. **Never** instantiate `Settings()`
  directly; **never** hardcode threshold values — use `self.thresholds.*`.
- **Analyzer contract:** only implement `_perform_analysis`; `analyze()` is
  inherited (except `EnsembleAnalyzer`, which overrides it). Populate
  `result.perplexity/burstiness/lexical_diversity/sentence_variance` and add
  `DetectionScore`s.
- **Lazy imports:** torch-backed analyzers are loaded via
  `src/analyzers/__init__.py::__getattr__` — keep them out of the eager block so
  `app.py` stays torch-free.
- **Intent layer:** `AGENTS.md` files under `src/analyzers/`, `src/models/`,
  `src/utils/` document local invariants — read before editing.

## Error Handling

- Broad `try/except Exception` around analysis; on failure log with
  `exc_info=True`, set `Verdict.UNCERTAIN`, zero confidence, and append a
  **generic** warning (exception strings are never surfaced to the UI).
- Empty/short input: early structured return with warnings, no model call.
- UIs use `src.ui.render_error(exc)` — logs full trace, shows a generic escaped
  message. `NLTKAnalyzer.set_ngram_size` raises `ValueError` for invalid sizes.

## Security-conscious conventions

- Model weights load with `use_safetensors=True`; Hub `revision` is pinnable via
  config. All user-derived strings are `html.escape`d before `unsafe_allow_html`.
  Input is capped at `ThresholdConfig.max_input_chars` (50000).

## Comments & Docstrings

- Google-style Args/Returns on public methods; top-of-file banner docstrings;
  section dividers (`# ─── ... ───`) in Streamlit code. Comments explain
  constraints/rationale, not narration.

## Commits

- Small, focused, Conventional-Commit style (`fix(ensemble): ...`,
  `refactor(ui): ...`), often referencing an audit finding (C1/H3/M4). PRs
  include benchmark numbers when detection behaviour changes
  (`.github/PULL_REQUEST_TEMPLATE.md`).
