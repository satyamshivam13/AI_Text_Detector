# Architecture

**Analysis Date:** 2026-07-06

## Pattern Overview

Layered Python package (`src/`) behind three thin Streamlit UIs. Core detection
uses the **Template Method** pattern: `BaseAnalyzer.analyze()` is concrete and
orchestrates the pipeline; subclasses implement only `_perform_analysis()`.
`EnsembleAnalyzer` is the exception — it **overrides `analyze()`** to run and fuse
multiple sub-analyzers.

## Layers

1. **Presentation** — `app.py` (NLTK), `gpt2_app.py` (GPT-2; renamed from
   `test.py`), `ensemble.py`. Each prepends `src/` to `sys.path`, configures the
   page, injects shared CSS, wires a specific analyzer, and renders an
   `AnalysisResult`. Shared UI lives in **`src/ui/`** (styles + components).
2. **Analyzers** — `src/analyzers/`: `BaseAnalyzer`, `NLTKAnalyzer`,
   `GPT2Analyzer`, `RoBERTaAnalyzer`, `BinocularsAnalyzer`, `EnsembleAnalyzer`,
   plus `calibration.py` (perplexity → AI-probability logistic).
3. **Models/Contract** — `src/models/result.py`: `AnalysisResult`, `TextMetrics`,
   `DetectionScore` dataclasses with `to_dict()`/`to_json()`.
4. **Config** — `src/config/settings.py`: frozen dataclasses (`ThresholdConfig`,
   `NLTKConfig`, `GPT2Config`, `RoBERTaConfig`, `BinocularsConfig`,
   `EnsembleConfig`, `VisualizationConfig`) + `get_settings()` `@lru_cache`
   singleton; enums `Verdict`, `ConfidenceLevel`, `DetectionMethod`.
5. **Utils** — `src/utils/`: `text_processing.py` (`TextProcessor`),
   `visualization.py` (`ChartGenerator`), `ui_contract.py` (shared UI copy),
   `logging_config.py`.
6. **Evaluation** — `src/evaluation/`: `metrics.py` (pure-NumPy accuracy/PR/F1/
   ROC-AUROC/FPR-FNR/ECE), `dataset.py` (JSONL loader over `data/benchmark/`),
   `benchmark.py` (runner + `--analyzer {nltk,gpt2,binoculars,ensemble}` CLI +
   ROC/calibration plots).

## Data Flow

`text → TextProcessor.clean_text → _apply_input_cap (max 50k chars) →
compute_metrics → _perform_analysis (per analyzer) → _determine_verdict →
_generate_explanation → AnalysisResult`. The ensemble instead runs GPT-2 + NLTK
(+ optionally RoBERTa/Binoculars when weighted), maps each to a **calibrated**
AI-probability via `logistic_ai_probability` (per-analyzer midpoint = decision
boundary), and fuses them by weight (clamped to `[0,1]`).

## Key Abstractions

- **BaseAnalyzer** (Template Method) — one abstract hook, shared validation/
  scoring/explanation/timing; input-size cap in `_apply_input_cap`.
- **AnalysisResult** — stable serializable contract between analysis and UI/eval.
- **EnsembleConfig calibration** — decision boundaries and fusion weights live in
  config, derived empirically from benchmark perplexity separation (GPT-2
  0.75 / NLTK 0.25; RoBERTa & Binoculars 0.0, gated).
- **Lazy transformer imports** — `src/analyzers/__init__.py::__getattr__` defers
  `GPT2Analyzer`/`RoBERTaAnalyzer`/`BinocularsAnalyzer`/`EnsembleAnalyzer` so
  `app.py` runs without `torch`.
- **Shared UI** — `src/ui/components.py` (`render_verdict_card`,
  `render_warnings`, `render_footer`, `render_error`, verdict maps; HTML-escaped)
  and `src/ui/styles.py` (`BASE_CSS` + `inject_css`).

## Entry Points

- `streamlit run app.py` → `NLTKAnalyzer` (lightest, torch-free).
- `streamlit run gpt2_app.py` → `GPT2Analyzer`.
- `streamlit run ensemble.py` → `EnsembleAnalyzer`.
- `python -m src.evaluation.benchmark ...` → benchmark CLI.
- Programmatic: `from src.analyzers.<x> import <Analyzer>; analyzer.analyze(text)`.

## Error Handling Contract

All analysis exceptions are caught inside `analyze()`: set `Verdict.UNCERTAIN`,
zero confidence, log full traceback (`exc_info=True`), and append a **generic**
warning (no exception strings). UIs render errors via `src.ui.render_error`
(generic message to user, full trace to server log).
