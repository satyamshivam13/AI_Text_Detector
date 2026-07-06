# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims
to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Remediation of the project audit. Highlights: the ensemble no longer flags
ordinary human text as AI, the statistical model is now smoothed and
discriminating, and there is a real evaluation layer.

### Added
- **Binoculars analyzer** (`src/analyzers/binoculars_analyzer.py`): zero-shot
  cross-perplexity detection (observer `gpt2` + performer `distilgpt2`) after
  Hans et al., 2024 — the modern, prompt-robust signal recommended by the audit.
  Available standalone and via the benchmark (`--analyzer binoculars`);
  benchmark AUROC 1.000, FPR 0.000, ECE 0.066.
- **Evaluation layer** (`src/evaluation/`): metrics (accuracy, precision,
  recall, F1, ROC/AUROC, false-positive/negative rates, expected calibration
  error), a labelled benchmark dataset + loader, and a benchmark runner with a
  CLI (`python -m src.evaluation.benchmark`).
- **Perplexity calibration** (`src/analyzers/calibration.py`): per-analyzer
  logistic mapping from perplexity to a calibrated AI-probability.
- **Benchmark results and plots** under `docs/benchmarks/`.
- **CI pipeline** (`.github/workflows/ci.yml`): lint + test matrix (3.9–3.11).
- Community health files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`,
  `SECURITY.md`, issue/PR templates.
- Configurable NLTK smoothing (`smoothing_method`) and a process-wide model
  cache.
- Substantially expanded test suite (121 → 219 tests; ~92% coverage of `src/`
  with the full suite), covering the evaluation layer, calibration, dataset
  loader, visualization, analyzer verdict/explanation logic, and the Binoculars
  compute path.
- Pinnable Hub `revision` for GPT-2/RoBERTa loading (`GPT2Config`,
  `RoBERTaConfig`).

### Changed
- **Renamed the GPT-2 Streamlit app `test.py` → `gpt2_app.py`** so it no longer
  looks like a pytest module. Updated Docker Compose, Makefile, CI, docs, and
  the input-size cap / generic UI error handling below.
- **Ensemble fusion is now calibrated.** Replaced `1 - perplexity/500` (which
  scored human text ~88% AI) with a per-analyzer logistic whose midpoint is the
  decision boundary. On the bundled benchmark, false-positive rate dropped to
  0.000. Weights rebalanced to GPT-2 0.75 / NLTK 0.25.
- **NLTK model** uses Witten-Bell interpolation (configurable) instead of an
  unsmoothed MLE that collapsed to the perplexity ceiling.
- Dependency floors raised to patched releases (`torch>=2.6`,
  `transformers>=4.48`); model weights loaded with `use_safetensors=True`.
- Corrected package metadata and removed unused dependencies.

### Fixed
- RoBERTa (disabled by default) is no longer downloaded or run, and no longer
  pollutes ensemble agreement/confidence.
- Whole codebase now passes `black`, `isort`, and `flake8`.
- Benchmark `--output` no longer fails when the parent directory is missing.

### Security
- Safe (non-pickle) model loading via safetensors; patched dependency floors;
  reproducible Hub revision pinning. See `SECURITY.md`.
