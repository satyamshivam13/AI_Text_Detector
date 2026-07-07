# Testing

**Analysis Date:** 2026-07-06

## Framework & Layout

- **pytest** (`requirements-dev.txt`, `setup.py extras_require[dev]`).
- `pytest.ini` registers the `slow` marker (`-m "not slow"` deselects
  model-heavy tests).
- `tests/conftest.py` prepends `../src` to `sys.path` (no `PYTHONPATH` needed)
  and provides shared text fixtures (`sample_ai_text`, `sample_human_text`,
  `short_text`, `empty_text`, `medium_text`, `repetitive_text`).
- **22 test files, ~231 test functions.** Full-suite coverage ~**92%** of `src/`.

## Test Areas

- **Analyzer unit/contract:** `test_nltk_analyzer.py`, `test_gpt2_analyzer.py`
  (slow, torch-gated), `test_roberta_analyzer.py`, `test_binoculars_analyzer.py`
  (mocked + slow real-model), `test_base_analyzer_contract.py`,
  `test_analyzer_internals.py` (pure verdict/explanation/interpret/input-cap/
  error-path — no model load).
- **Calibration/eval:** `test_calibration.py` (logistic mapping),
  `test_evaluation.py`, `test_metrics`-style cases, `test_dataset_loader.py`
  (error branches), `test_benchmark_runner.py` (factory, summary, plots, CLI).
- **Ensemble:** `test_ensemble_analyzer.py` (mocked sub-analyzers),
  `test_ensemble_weighted_fusion.py` (calibrated fusion, binoculars gating,
  human-scale-not-flagged regression).
- **UI:** `test_streamlit_apps.py` (Streamlit **AppTest** headless smoke tests
  for all 3 entry scripts), `test_ui_components.py`, `test_ui_contract.py`,
  `test_visualization.py` (ChartGenerator), `test_infra.py` (logging + lazy
  imports), `test_*_streamlit_contract.py` (static source contracts).
- **Data model:** `test_result_model.py`.

## Mocking Strategy

- Sub-analyzers are replaced with lightweight fakes (`EnsembleAnalyzer`) or the
  `_compute_*` method is monkeypatched (`BinocularsAnalyzer`) so most tests run
  **without loading transformer or Brown-corpus models**.
- Genuinely model-dependent paths (`_compute_perplexity_gpt2`,
  `_compute_binoculars`, real RoBERTa/GPT-2 `analyze`) are marked
  `@pytest.mark.slow` and excluded from the default/CI run.
- `NLTKAnalyzer` uses a process-wide model cache, so the Brown model builds once
  per test process (NLTK suite ~30s instead of ~6min).

## Running

```bash
python -m pytest tests/ -m "not slow" -q            # fast (CI default)
python -m pytest tests/ -q --cov=src --cov-report=term-missing  # full + coverage
python -m pytest -m slow -v                          # model-backed only
```

## CI

`.github/workflows/ci.yml`: **lint** job (flake8 + black --check + isort --check)
and **test** job over Python 3.9/3.10/3.11 — installs deps, downloads NLTK data,
runs `pytest -m "not slow" --cov=src`.

## Gaps / Notes

- Coverage is **not gated** (`--cov-fail-under` not set) — it can silently erode.
- Slow model tests **never run in CI** (no scheduled full-suite job).
- Bundled benchmark (`data/benchmark/samples.jsonl`) is 24 clean in-distribution
  samples — used for regression/calibration, **not** an accuracy claim.
