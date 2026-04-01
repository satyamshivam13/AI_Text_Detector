# Architecture

**Analysis Date:** 2026-04-02

## Pattern Overview

**Overall:** Layered monolith with a **Template Method** analyzer hierarchy, optional **ensemble composition**, and **Streamlit scripts as thin presentation shells**.

**Key Characteristics:**
- Core detection logic lives under `src/` as importable packages; runnable UIs prepend `src` to `sys.path` then import `src.*` explicitly.
- `BaseAnalyzer` centralizes validation, metric computation, verdict scoring, explanations, and timing; concrete analyzers only implement `_perform_analysis`.
- `EnsembleAnalyzer` is a special case: it **overrides** `analyze()` to run multiple backends and fuse outputs instead of using the base `_perform_analysis` hook alone.
- Shared preprocessing and NLTK bootstrap live in `TextProcessor` (`src/utils/text_processing.py`); charts in `ChartGenerator` (`src/utils/visualization.py`).

## Layers

**Presentation (Streamlit):**
- Purpose: Page config, layout, CSS, widgets, call into analyzers and charts, display `AnalysisResult`.
- Location: repository root — `app.py`, `ensemble.py`, `test.py` (GPT-2 UI; filename is legacy).
- Contains: Procedural Streamlit code, `@st.cache_resource` loaders, verdict-to-CSS mapping.
- Depends on: `src.analyzers.*`, `src.config.settings`, `src.utils.logging_config`, `src.utils.visualization`.
- Used by: End users via `streamlit run <file>.py`.

**Analysis (domain services):**
- Purpose: Turn raw text into `AnalysisResult` (verdict, scores, metrics, warnings).
- Location: `src/analyzers/`
- Contains: `BaseAnalyzer`, `NLTKAnalyzer`, `GPT2Analyzer`, `RoBERTaAnalyzer`, `EnsembleAnalyzer`.
- Depends on: `src.config.settings`, `src.models.result`, `src.utils.text_processing`, `src.utils.logging_config`; transformers stack in GPT-2/RoBERTa paths.
- Used by: Streamlit apps, tests, any programmatic `analyzer.analyze(text)` caller.

**Models:**
- Purpose: Serializable result shapes (`AnalysisResult`, `TextMetrics`, `DetectionScore`).
- Location: `src/models/result.py`
- Contains: `@dataclass` types, `to_dict()` / `to_json()` on `AnalysisResult`.
- Depends on: `Verdict`, `ConfidenceLevel` from `src/config/settings.py`.
- Used by: All analyzers and UI layers that render or export results.

**Configuration:**
- Purpose: Enums, frozen threshold and subsystem configs, cached `Settings` singleton.
- Location: `src/config/settings.py`
- Contains: `Verdict`, `ConfidenceLevel`, `ThresholdConfig`, `NLTKConfig`, `GPT2Config`, `VisualizationConfig`, `Settings`, `get_settings()` (`@lru_cache`).
- Depends on: `os.environ` for `AI_DETECTOR_DEBUG`, `AI_DETECTOR_LOG_LEVEL`.
- Used by: `BaseAnalyzer`, `ChartGenerator`, apps.

**Infrastructure utilities:**
- Purpose: Logging setup, text cleaning/tokenization/metrics, optional NLTK downloads, plotting.
- Location: `src/utils/logging_config.py`, `src/utils/text_processing.py`, `src/utils/visualization.py`
- Contains: `TextProcessor` (classmethods for corpus-safe NLP), `ChartGenerator` (Plotly primary, Matplotlib `Agg` backend).
- Depends on: NLTK, Plotly, Matplotlib, NumPy; `get_settings()` where needed.
- Used by: Analyzers and Streamlit tabs.

## Data Flow

**Single-analyzer (NLTK / GPT-2) path:**

1. UI collects `text` and calls `analyzer.analyze(text)` (e.g. `NLTKAnalyzer` from `app.py` via `load_analyzer`).
2. `BaseAnalyzer.analyze()` in `src/analyzers/base_analyzer.py` cleans with `TextProcessor.clean_text()`, sets `text_length`, handles empty/short input warnings.
3. `TextProcessor.compute_metrics()` fills `result.metrics` (`TextMetrics`).
4. Subclass `_perform_analysis()` computes model-specific signals and populates perplexity, burstiness, lexical diversity, sentence variance, and `DetectionScore` entries.
5. `_determine_verdict()` maps weighted feature scores to `Verdict` and `ConfidenceLevel`; `_generate_explanation()` builds the narrative string.
6. UI reads `AnalysisResult` fields and passes word frequencies / scores to `ChartGenerator` for Plotly figures.

**Ensemble path:**

1. `EnsembleAnalyzer.analyze()` in `src/analyzers/ensemble_analyzer.py` duplicates early validation/metrics steps then lazy-loads `RoBERTaAnalyzer`, `GPT2Analyzer`, `NLTKAnalyzer` via properties.
2. Component analyzers run (RoBERTa weight may be zeroed by default); scores are fused using configured weights.
3. Returns a single `AnalysisResult` consistent with the shared model type.

**State Management:**
- No server-side session store; Streamlit reruns the script. Heavy objects (analyzer, `ChartGenerator`) are cached with `@st.cache_resource` in each app file.
- Settings are process-wide via `get_settings()` cache.

## Key Abstractions

**`BaseAnalyzer`:**
- Purpose: Uniform pipeline for text-in → `AnalysisResult` out.
- Examples: `src/analyzers/base_analyzer.py`
- Pattern: Template Method — `analyze()` is concrete; `_perform_analysis()` abstract.

**`TextProcessor`:**
- Purpose: Single place for NLTK data guarantees, tokenization, and `TextMetrics` computation.
- Examples: `src/utils/text_processing.py`
- Pattern: Stateful class with class-level caches (`_nltk_initialized`, stopwords).

**`AnalysisResult` / `DetectionScore`:**
- Purpose: Stable contract between analysis and presentation/API docs.
- Examples: `src/models/result.py`
- Pattern: Dataclasses with helper methods (`add_warning`, `add_score`, `to_dict`).

**`ChartGenerator`:**
- Purpose: Decouple Plotly/Matplotlib construction from Streamlit layout.
- Examples: `src/utils/visualization.py`
- Pattern: Small service class configured from `VisualizationConfig`.

## Entry Points

**NLTK Streamlit app:**
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: NLTK-only UX; `load_analyzer(ngram_size)` → `NLTKAnalyzer`.

**Ensemble Streamlit app:**
- Location: `ensemble.py`
- Triggers: `streamlit run ensemble.py`
- Responsibilities: `EnsembleAnalyzer` UX; combined GPT-2 + NLTK (+ optional RoBERTa).

**GPT-2 Streamlit app:**
- Location: `test.py`
- Triggers: `streamlit run test.py`
- Responsibilities: `GPT2Analyzer`-only UX (despite the name `test.py`).

**Library / programmatic use:**
- Documented in `docs/API.md`; import analyzers from `src.analyzers` and call `.analyze(text)`.

**Packaging:**
- Location: `setup.py` — `packages=find_packages(where="src")`, `package_dir={"": "src"}` so the installable name maps to the `src` tree.

## Error Handling

**Strategy:** Defensive defaults inside `BaseAnalyzer.analyze()`: exceptions in the try-block set `Verdict.UNCERTAIN`, zero confidence, append warning, generic explanation; logged with `logger.error(..., exc_info=True)`. Streamlit layers wrap display paths in `try/except` and call `st.error`.

**Patterns:**
- Empty/short text: early return with warnings, no model call.
- NLTK corpus missing: `NLTKAnalyzer._build_model` raises `RuntimeError` with download hint after logging.

## Cross-Cutting Concerns

**Logging:** `setup_logging` / `get_logger` from `src/utils/logging_config.py` at app startup and in analyzers.

**Validation:** Length thresholds from `ThresholdConfig` in `src/config/settings.py`; cleaning in `TextProcessor.clean_text()`.

**Authentication:** Not applicable — local Streamlit apps, no auth layer in repo.

---

*Architecture analysis: 2026-04-02*
