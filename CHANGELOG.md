# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project aims
to follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (behaviour — ethics)
- **The default ensemble verdict is now Binoculars-driven** (`weight_binoculars=1.0`,
  GPT-2/NLTK/RoBERTa weight 0). The fairness evaluation showed the old
  GPT-2-weighted blend flagged 71% of non-native English writers; Binoculars-only
  is 5.5%. GPT-2/NLTK still run and their sub-scores display for transparency, but
  they no longer drive the verdict. `method_name` is now
  "Ensemble (Binoculars-weighted)". Raise the GPT-2/NLTK weights only if you accept
  the fairness cost. Ensemble now loads a second small model (distilgpt2).

### Added
- **Per-population fairness evaluation** (`scripts/prepare_fairness_set.py`,
  `scripts/fpr_by_population.py`, `docs/benchmarks/FAIRNESS.md`): false-positive
  rate on 785 human-authored samples across 10 populations, with Wilson 95% CIs.
  Data (Liang et al. 2023 essays + HC3 human answers) is not redistributed.

### Fixed
- **NLTK data was re-downloaded on every call and never cached.**
  `ensure_nltk_data()` passed bare package names (`"brown"`) to `nltk.data.find`,
  which needs resource paths (`"corpora/brown"`); the lookup always raised, so a
  fresh download was attempted every time and initialization never stuck. Fixed
  with an explicit package→path map and a regression test. (Latent since the v2.0
  bootstrap-retry change; exposed by the fairness run.)

### Changed / Ethics
- **The README no longer recommends the ensemble as "most robust".** The fairness
  evaluation shows the default ensemble has a 27.1% false-positive rate on human
  text and **71.4% on non-native English writers** — the worst of the three,
  because it inherits GPT-2's bias. GPT-2 alone flags 26.4% of non-native writers
  (reproducing Liang et al. 2023). **Binoculars is both the most accurate and the
  fairest** (1.0% overall, 5.5% for non-native writers) and is now the
  recommended analyzer. A fairness caveat was added to all three apps' UI.

## [2.1.0] - 2026-07-08

**Corrects an accuracy claim made in v2.0.0.** v2.0.0 headlined "FPR 0.000" from
the bundled 24-sample set. That set's "AI" class turned out to be hand-written
imitations of LLM style, not real model output, so it could not falsify the
detector. Measured against real ChatGPT text (HC3), the picture is different —
and the Binoculars decision boundary was badly miscalibrated. See below.

### Added
- **HC3 evaluation.** `scripts/prepare_hc3.py` builds a balanced sample of the
  public HC3 corpus (real human text vs real ChatGPT output); the corpus itself is
  not committed. First out-of-distribution measurement of this detector.
- `scripts/calibrate_binoculars.py` — fits the Binoculars decision boundary on a
  calibration half and validates it on a **held-out** half.

### Changed
- **Binoculars `score_midpoint` recalibrated on real LLM output**: 0.863 → 0.7625.
  The old value was fitted on the bundled set and sat inside the *real* human
  cluster, flagging **46% of real human text as AI**. On HC3 the new boundary gives
  accuracy 1.000 / FPR 0.000, validated on a held-out half.
- Documentation now leads with HC3 numbers, not the bundled set's.

### Fixed
- The benchmark harness ignored an analyzer's own calibrated probability unless it
  was named `"Ensemble AI Score"`, so Binoculars was evaluated through a coarse
  verdict/confidence step function (distorting ECE and threshold sweeps). It now
  prefers any calibrated primary score.

### Honesty
- The bundled `data/benchmark/` "AI" samples are **hand-written imitations of LLM
  style, not real model output**, and are not machine-like when measured against
  real ChatGPT text. That set is a pipeline regression fixture only; its scores are
  **not** accuracy. Documented in `data/benchmark/README.md`.
- Measured on HC3: **GPT-2 alone flags 50% of real human text as AI**; NLTK alone
  is below chance (AUROC 0.420).

## [2.0.0] - 2026-07-08

Remediation of the project audit. Highlights: the ensemble no longer flags
ordinary human text as AI, the statistical model is now smoothed and
discriminating, and there is a real evaluation layer.

### Added
- **Binoculars analyzer** (`src/analyzers/binoculars_analyzer.py`): zero-shot
  cross-perplexity detection (observer `gpt2` + performer `distilgpt2`) after
  Hans et al., 2024 — the modern, prompt-robust signal recommended by the audit.
  Available standalone and via the benchmark (`--analyzer binoculars`);
  benchmark AUROC 1.000, FPR 0.000, ECE 0.066. Can also be fused into the
  ensemble via `EnsembleConfig.weight_binoculars` (off by default; loaded only
  when weighted, mirroring the RoBERTa gating).
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
- Detection scores are addressed **by name** (`AnalysisResult.get_score`) rather
  than by list position, so reordering scores can no longer silently break
  ensemble/Binoculars verdict math.
- CI enforces a coverage floor (`--cov-fail-under=80`; fast suite is at 85%).

### Security
- Safe (non-pickle) model loading via safetensors; patched dependency floors;
  reproducible Hub revision pinning. See `SECURITY.md`.
