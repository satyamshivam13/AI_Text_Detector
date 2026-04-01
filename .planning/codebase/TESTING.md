# Testing Patterns

**Analysis Date:** 2026-04-02

## Test Framework

**Runner:**
- **pytest** (>=7.4.0 per `requirements-dev.txt`).
- No committed `pytest.ini`, `pyproject.toml`, or `tox.ini` in repo root; behavior is default pytest discovery.

**Assertion Library:**
- Plain `assert` statements (pytest style).

**Plugins (declared):**
- `pytest-cov` — coverage.
- `pytest-mock` — available but **not used** in current test modules (no `mock` / `patch` / `mocker` references under `tests/`).

**Run Commands:**
```bash
# Recommended (matches Makefile): PYTHONPATH set for src package
make test

# Equivalent manual invocation from repo root
PYTHONPATH=src python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

On Windows PowerShell, set env then run pytest, or use `make test` if GNU Make is available.

**README** also documents: `pytest tests/ -v --cov=src --cov-report=html` and single-file runs (e.g. `pytest tests/test_ensemble_analyzer.py -v`).

## Test File Organization

**Location:**
- All tests under `tests/` (not co-located with `src/`).

**Naming:**
- `test_<area>.py` (e.g. `tests/test_text_processing.py`, `tests/test_result_model.py`).

**Package:**
- `tests/__init__.py` present (package layout).

**Structure:**
```
tests/
├── __init__.py
├── conftest.py              # shared fixtures, path bootstrap
├── test_ensemble_analyzer.py
├── test_gpt2_analyzer.py
├── test_nltk_analyzer.py
├── test_result_model.py
├── test_roberta_analyzer.py
└── test_text_processing.py
```

## Test Structure

**Suite organization:**
- **Classes** group related cases: `TestTextCleaning`, `TestNLTKAnalyzerInit`, `TestEnsembleAnalyzer`, etc.

**Example pattern (class + methods):**
```python
class TestTextCleaning:
    def test_clean_empty_text(self):
        assert TextProcessor.clean_text("") == ""
```

**Fixtures:**
- **Shared:** `tests/conftest.py` — `sample_ai_text`, `sample_human_text`, `short_text`, `empty_text`, `medium_text`, `repetitive_text`, `nltk_analyzer`, `text_processor`.
- **Local:** `@pytest.fixture` in module (e.g. `ensemble_analyzer` in `tests/test_ensemble_analyzer.py`).
- **Autouse setup:** `autouse=True` fixture on test class for analyzer instance (`tests/test_nltk_analyzer.py`, `tests/test_gpt2_analyzer.py`).

**Parametrization:** Not heavily used; prefer explicit methods per edge case in current codebase.

## Mocking

**Framework:** `pytest-mock` is a dev dependency only; **current tests are integration-style** against real `NLTKAnalyzer`, `GPT2Analyzer`, `EnsembleAnalyzer`, and `TextProcessor`.

**Prescriptive guidance:**
- Use `pytest-mock`’s `mocker` fixture or `unittest.mock.patch` for Hugging Face / torch downloads, slow I/O, or nondeterministic model output when adding CI-friendly unit tests.
- Keep heavy model tests behind markers (see below).

## Fixtures and Factories

**Test data:**
- Long representative strings in `conftest.py` for “AI-like” vs “human-like” prose and edge cases (short, empty, repetitive).

**Factory-style fixtures:**
- `nltk_analyzer` → `NLTKAnalyzer(ngram_size=3)`.
- `text_processor` → `TextProcessor()`.

**No separate `fixtures/` directory**; everything lives in `conftest.py` or inline fixtures.

## Coverage

**Requirements:** No enforced coverage threshold in repo config; `Makefile` `test` target runs coverage with HTML + terminal missing-line report.

**View coverage:**
```bash
make test
# Open htmlcov/index.html after run
```

**Scope:** `--cov=src` limits reporting to the installable package under `src/`.

## Test Types

**Unit tests:**
- `tests/test_text_processing.py` — pure utilities, fast, no GPU.

**Model / analyzer tests:**
- `tests/test_nltk_analyzer.py`, `tests/test_result_model.py` — logic close to domain.

**Heavy / ML tests:**
- `tests/test_gpt2_analyzer.py` — module-level `pytestmark = pytest.mark.skipif(not HAS_TORCH, ...)`; class `TestGPT2Analysis` uses `@pytest.mark.slow` (documented for CI filtering in module docstring).
- `tests/test_roberta_analyzer.py` and `tests/test_ensemble_analyzer.py` exercise transformers stack (slow, network/model cache dependent).

**E2E / UI:** Streamlit apps are not covered by automated browser tests in `tests/`.

## Common Patterns

**Enum membership:**
```python
assert result.verdict in list(Verdict)
```

**Exception testing:**
```python
with pytest.raises(ValueError):
    analyzer.set_ngram_size(1)
```

**Structural assertions on results:**
- `result.to_dict()`, `hasattr` checks, score name substring checks (`"RoBERTa" in name`, etc.) in `tests/test_ensemble_analyzer.py`.

## CI / Automation

**Repository:** No `.github/workflows` or other CI config detected in workspace; quality gates are **local** via `Makefile` (`test`, `lint`, `format`).

**Pre-commit:** Listed in `requirements-dev.txt`; no committed hook config found — treat as optional local setup unless added later.

---

*Testing analysis: 2026-04-02*
