# Coding Conventions

**Analysis Date:** 2026-04-02

## Naming Patterns

**Files:**
- Python modules: `snake_case.py` (e.g. `base_analyzer.py`, `text_processing.py`, `logging_config.py`).
- Streamlit entry scripts at repo root: `app.py`, `test.py`, `ensemble.py` (single-word or short names).
- Tests: `test_<module>.py` under `tests/` (e.g. `tests/test_nltk_analyzer.py`).

**Functions:**
- `snake_case` for functions and methods (e.g. `get_settings`, `clean_text`, `compute_metrics`).

**Variables:**
- `snake_case` for locals and instance attributes; short aliases in hot paths are acceptable (e.g. `t = self.thresholds` in `src/analyzers/base_analyzer.py`).

**Classes:**
- `PascalCase` for classes (e.g. `BaseAnalyzer`, `TextProcessor`, `AnalysisResult`, `NLTKAnalyzer`).

**Types:**
- Prefer `from __future__ import annotations` and typing imports (`Optional`, `List`, `Dict`, `Tuple`) as in `src/models/result.py` and `src/analyzers/base_analyzer.py`.
- Enums for fixed vocabularies: `Verdict`, `ConfidenceLevel`, `DetectionMethod` in `src/config/settings.py`.

**Private / internal:**
- Leading underscore for non-public implementation details (e.g. `_perform_analysis`, `_nltk_initialized`, `_roberta_analyzer` on ensemble).

## Code Style

**Formatting:**
- **Black** with line length **100** (see `Makefile` target `format`).
- **isort** with **`--profile=black`** alongside Black.

**Linting:**
- **flake8** on `src/`, `tests/`, `app.py`, `test.py`, `ensemble.py` with `--max-line-length=100` (`Makefile` target `lint`).
- **mypy** on `src/` with `--ignore-missing-imports`.
- **pylint** on `src/` with `--disable=C0114,C0115,C0116` (docstring-related disables).

**Declared dev stack:** `requirements-dev.txt` lists black, flake8, isort, mypy, pylint, pre-commit (no committed `pyproject.toml` or `.pre-commit-config.yaml` detected in repo root).

## Import Organization

**Order (observed):**
1. Standard library (`from __future__`, `abc`, `typing`, `os`, etc.).
2. Third-party (`nltk`, `streamlit`, `pytest` in tests).
3. First-party: `from src....` (package layout under `src/`).

**Path resolution for `src`:**
- **Makefile** sets `PYTHONPATH=src` for `run-*`, `test`, and `lint` targets.
- **Streamlit apps** (`app.py`, and same pattern in `test.py` / `ensemble.py`): `sys.path.insert(0, ... "src")` then `from src....`.
- **Tests:** `tests/conftest.py` inserts `../src` on `sys.path` so `from src....` resolves when pytest is run without `PYTHONPATH`.

**Prescriptive rule:** Prefer running tests and apps the way `Makefile` documents (`PYTHONPATH=src` or path insert) so `import src` remains consistent.

## Error Handling

**Analyzer pipeline (`src/analyzers/base_analyzer.py`):**
- Broad `try`/`except Exception` around analysis: on failure, log with `logger.error(..., exc_info=True)`, set `Verdict.UNCERTAIN`, zero confidence, append warning, set a safe `explanation`.
- Empty or invalid text: early return with structured `AnalysisResult` (no exception).

**Validation-style errors:**
- `NLTKAnalyzer.set_ngram_size` raises `ValueError` for invalid sizes; tests expect `pytest.raises(ValueError)` (`tests/test_nltk_analyzer.py`).

**NLTK downloads (`src/utils/text_processing.py`):**
- Per-package download failures: log warning, continue where possible.

**Prescriptive pattern for new analyzers:** Subclass `BaseAnalyzer`, implement `_perform_analysis`; do not bypass `analyze()` validation and error envelope unless there is a strong reason.

## Logging

**Framework:** Standard library `logging`, wrapped by `src/utils/logging_config.py`.

**Patterns:**
- `get_logger(__name__)` at module level; use `logger.info` / `logger.error` / `logger.warning` as in `base_analyzer.py` and `text_processing.py`.
- `setup_logging(level, log_file=None)` configures format `%(asctime) | %(levelname) | %(name)s:%(funcName)s:%(lineno)d | %(message)s` and quiets noisy third-party loggers (`transformers`, `torch`, `urllib3`, `filelock`).

**Settings:** `Settings.log_level` and `debug` can be driven by env vars `AI_DETECTOR_LOG_LEVEL` and `AI_DETECTOR_DEBUG` (`src/config/settings.py`).

## Comments

**Module docstrings:**
- Top-of-file banner style with title lines (`===`) in several modules (e.g. `src/utils/text_processing.py`, `src/config/settings.py`).

**Class/method docstrings:**
- Google-style **Args** / **Returns** blocks on public methods (e.g. `BaseAnalyzer.analyze`, `setup_logging`).

**Inline:**
- Section dividers in Streamlit UI code (e.g. `# ─── Setup ───` in `app.py`).

## Function Design

**Size:** `BaseAnalyzer` centralizes orchestration; subclasses focus on `_perform_analysis`. Prefer keeping verdict logic in the base class unless the method differs fundamentally.

**Parameters:** Explicit typed parameters; dataclass/`field(default_factory=...)` for mutable defaults (`src/models/result.py`).

**Return values:** `AnalysisResult` (or domain dataclasses) rather than loose dicts for core API; `to_dict()` / `to_json()` for serialization.

## Module Design

**Exports:**
- Package `__init__.py` files under `src/` exist for package structure; import concrete symbols from submodules (e.g. `from src.analyzers.nltk_analyzer import NLTKAnalyzer`).

**Configuration:**
- Immutable threshold/config blobs: `@dataclass(frozen=True)` (`ThresholdConfig`, `NLTKConfig`, etc.) in `src/config/settings.py`.
- Mutable `Settings` uses `@lru_cache` singleton via `get_settings()`.

**Barrel files:** Not heavily used; prefer explicit imports from feature modules.

---

*Convention analysis: 2026-04-02*
