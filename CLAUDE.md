<!-- GSD:project-start source:PROJECT.md -->
## Project

**AI Text Detector**

A Python toolkit and set of Streamlit applications that estimate how likely text is to be machine-generated, using statistical (NLTK), perplexity (GPT-2), optional transformer classification (RoBERTa), and weighted ensemble fusion. It targets developers, educators, and researchers who want **local, explainable** signals—not a single opaque score—and who accept documented accuracy limits.

**Core Value:** Users get a **transparent, multi-signal** AI-likelihood assessment (verdict, confidence, metrics, narrative explanation) they can reason about, with ethical framing that results are probabilistic and not sole proof of authorship.

### Constraints

- **Tech stack**: Python 3.8+, Streamlit, PyTorch, Transformers, NLTK — see `requirements.txt` and `setup.py`
- **Runtime**: Substantial RAM for GPT-2/ensemble; GPU optional
- **Privacy**: Processing is local; no requirement to send user text to third-party APIs for core detection
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3 — Application, analyzers, Streamlit UIs; `setup.py` declares `python_requires=">=3.8"` with classifiers through 3.11; `Dockerfile` pins runtime image `python:3.9-slim`.
- Not applicable — No TypeScript, JavaScript bundles, or separate frontend beyond Streamlit-rendered HTML/CSS in `app.py`, `test.py`, and `ensemble.py`.
## Runtime
- CPython (see Docker: `python:3.9-slim` in `Dockerfile`).
- pip — Used in `Dockerfile` (`pip install -r requirements.txt`).
- Lockfile: Not detected — No `poetry.lock`, `Pipfile.lock`, or `uv.lock` in repo; pin ranges live in `requirements.txt`.
## Frameworks
- Streamlit (>=1.28,<2) — Web UI; entry via `streamlit run` with `app.py` (NLTK), `test.py` (GPT-2), or `ensemble.py` (ensemble). See `docker-compose.yml` service `command` overrides.
- PyTorch (`torch` >=2,<3) — Device selection and model inference in `src/analyzers/gpt2_analyzer.py` and `src/analyzers/roberta_analyzer.py`.
- Hugging Face Transformers (`transformers` >=4.35,<5) — `GPT2LMHeadModel`, `GPT2TokenizerFast`, `RobertaTokenizer`, `RobertaForSequenceClassification` in those analyzers.
- NLTK (>=3.8,<4) — N-gram / Brown corpus analysis in `src/analyzers/nltk_analyzer.py`.
- pytest (>=7.4) — Declared in `requirements-dev.txt` and `setup.py` `extras_require.dev`; tests under `tests/`.
- setuptools — Package layout in `setup.py` with `packages=find_packages(where="src")`, `package_dir={"": "src"}`.
- black, flake8, isort, mypy, pylint, pre-commit — Listed in `requirements-dev.txt`.
- Sphinx + sphinx-rtd-theme — Documentation tooling in `requirements-dev.txt`.
## Key Dependencies
- `streamlit` — Sole HTTP-serving application layer; configuration in `.streamlit/config.toml`.
- `torch` + `transformers` — GPT-2 and RoBERTa model loading (`from_pretrained`) in `src/analyzers/gpt2_analyzer.py`, `src/analyzers/roberta_analyzer.py`.
- `nltk` — Corpus and tokenizer resources; Dockerfile pre-downloads punkt, punkt_tab, stopwords, brown, averaged_perceptron_tagger.
- `numpy`, `pandas` — Numerical/tabular use in analyzers and utilities.
- `matplotlib` (Agg backend in `src/utils/visualization.py`), `plotly` — Charts for Streamlit (`st.plotly_chart` in `app.py`).
- `pydantic` — Listed in `requirements.txt`; `src/config/settings.py` and `src/models/result.py` use `dataclasses` instead. Prefer aligning future config/models with one approach.
- `python-dotenv`, `structlog` — Present in `requirements.txt`; no `load_dotenv` or `structlog` usage detected in application Python files; logging uses stdlib in `src/utils/logging_config.py`.
## Configuration
- Application toggles: `AI_DETECTOR_DEBUG`, `AI_DETECTOR_LOG_LEVEL` — Read in `Settings.__post_init__` in `src/config/settings.py`.
- Docker / Streamlit: `PYTHONPATH=/app/src`, `STREAMLIT_SERVER_PORT`, `STREAMLIT_SERVER_ADDRESS`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS` — Set in `Dockerfile` and `docker-compose.yml`.
- Streamlit server/theme/browser/logger — `.streamlit/config.toml` (e.g. `headless`, `port`, `maxUploadSize`, XSRF).
- `Dockerfile` — Multi-stage base, system `build-essential` + `curl`, NLTK download step, `ENTRYPOINT ["streamlit", "run"]`, default `CMD ["app.py"]`.
- `docker-compose.yml` — Three services sharing the same image build; different ports and commands for NLTK vs GPT-2 vs ensemble; named volumes `nltk_data` and `model_cache`.
## Platform Requirements
- Python >=3.8, pip, virtualenv per `docs/DEPLOYMENT.md`; run `streamlit run app.py` from repo root (see `app.py` docstring). Install from `requirements.txt`; dev extras via `requirements-dev.txt` or `pip install -e ".[dev]"` per `setup.py`.
- Container: Linux image exposing port 8501; health check curls `http://localhost:8501/_stcore/health` in `Dockerfile`. GPT-2/ensemble paths need more RAM/CPU per `docker-compose.yml` `deploy.resources` limits.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- Python modules: `snake_case.py` (e.g. `base_analyzer.py`, `text_processing.py`, `logging_config.py`).
- Streamlit entry scripts at repo root: `app.py`, `test.py`, `ensemble.py` (single-word or short names).
- Tests: `test_<module>.py` under `tests/` (e.g. `tests/test_nltk_analyzer.py`).
- `snake_case` for functions and methods (e.g. `get_settings`, `clean_text`, `compute_metrics`).
- `snake_case` for locals and instance attributes; short aliases in hot paths are acceptable (e.g. `t = self.thresholds` in `src/analyzers/base_analyzer.py`).
- `PascalCase` for classes (e.g. `BaseAnalyzer`, `TextProcessor`, `AnalysisResult`, `NLTKAnalyzer`).
- Prefer `from __future__ import annotations` and typing imports (`Optional`, `List`, `Dict`, `Tuple`) as in `src/models/result.py` and `src/analyzers/base_analyzer.py`.
- Enums for fixed vocabularies: `Verdict`, `ConfidenceLevel`, `DetectionMethod` in `src/config/settings.py`.
- Leading underscore for non-public implementation details (e.g. `_perform_analysis`, `_nltk_initialized`, `_roberta_analyzer` on ensemble).
## Code Style
- **Black** with line length **100** (see `Makefile` target `format`).
- **isort** with **`--profile=black`** alongside Black.
- **flake8** on `src/`, `tests/`, `app.py`, `test.py`, `ensemble.py` with `--max-line-length=100` (`Makefile` target `lint`).
- **mypy** on `src/` with `--ignore-missing-imports`.
- **pylint** on `src/` with `--disable=C0114,C0115,C0116` (docstring-related disables).
## Import Organization
- **Makefile** sets `PYTHONPATH=src` for `run-*`, `test`, and `lint` targets.
- **Streamlit apps** (`app.py`, and same pattern in `test.py` / `ensemble.py`): `sys.path.insert(0, ... "src")` then `from src....`.
- **Tests:** `tests/conftest.py` inserts `../src` on `sys.path` so `from src....` resolves when pytest is run without `PYTHONPATH`.
## Error Handling
- Broad `try`/`except Exception` around analysis: on failure, log with `logger.error(..., exc_info=True)`, set `Verdict.UNCERTAIN`, zero confidence, append warning, set a safe `explanation`.
- Empty or invalid text: early return with structured `AnalysisResult` (no exception).
- `NLTKAnalyzer.set_ngram_size` raises `ValueError` for invalid sizes; tests expect `pytest.raises(ValueError)` (`tests/test_nltk_analyzer.py`).
- Per-package download failures: log warning, continue where possible.
## Logging
- `get_logger(__name__)` at module level; use `logger.info` / `logger.error` / `logger.warning` as in `base_analyzer.py` and `text_processing.py`.
- `setup_logging(level, log_file=None)` configures format `%(asctime) | %(levelname) | %(name)s:%(funcName)s:%(lineno)d | %(message)s` and quiets noisy third-party loggers (`transformers`, `torch`, `urllib3`, `filelock`).
## Comments
- Top-of-file banner style with title lines (`===`) in several modules (e.g. `src/utils/text_processing.py`, `src/config/settings.py`).
- Google-style **Args** / **Returns** blocks on public methods (e.g. `BaseAnalyzer.analyze`, `setup_logging`).
- Section dividers in Streamlit UI code (e.g. `# ─── Setup ───` in `app.py`).
## Function Design
## Module Design
- Package `__init__.py` files under `src/` exist for package structure; import concrete symbols from submodules (e.g. `from src.analyzers.nltk_analyzer import NLTKAnalyzer`).
- Immutable threshold/config blobs: `@dataclass(frozen=True)` (`ThresholdConfig`, `NLTKConfig`, etc.) in `src/config/settings.py`.
- Mutable `Settings` uses `@lru_cache` singleton via `get_settings()`.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Core detection logic lives under `src/` as importable packages; runnable UIs prepend `src` to `sys.path` then import `src.*` explicitly.
- `BaseAnalyzer` centralizes validation, metric computation, verdict scoring, explanations, and timing; concrete analyzers only implement `_perform_analysis`.
- `EnsembleAnalyzer` is a special case: it **overrides** `analyze()` to run multiple backends and fuse outputs instead of using the base `_perform_analysis` hook alone.
- Shared preprocessing and NLTK bootstrap live in `TextProcessor` (`src/utils/text_processing.py`); charts in `ChartGenerator` (`src/utils/visualization.py`).
## Layers
- Purpose: Page config, layout, CSS, widgets, call into analyzers and charts, display `AnalysisResult`.
- Location: repository root — `app.py`, `ensemble.py`, `test.py` (GPT-2 UI; filename is legacy).
- Contains: Procedural Streamlit code, `@st.cache_resource` loaders, verdict-to-CSS mapping.
- Depends on: `src.analyzers.*`, `src.config.settings`, `src.utils.logging_config`, `src.utils.visualization`.
- Used by: End users via `streamlit run <file>.py`.
- Purpose: Turn raw text into `AnalysisResult` (verdict, scores, metrics, warnings).
- Location: `src/analyzers/`
- Contains: `BaseAnalyzer`, `NLTKAnalyzer`, `GPT2Analyzer`, `RoBERTaAnalyzer`, `EnsembleAnalyzer`.
- Depends on: `src.config.settings`, `src.models.result`, `src.utils.text_processing`, `src.utils.logging_config`; transformers stack in GPT-2/RoBERTa paths.
- Used by: Streamlit apps, tests, any programmatic `analyzer.analyze(text)` caller.
- Purpose: Serializable result shapes (`AnalysisResult`, `TextMetrics`, `DetectionScore`).
- Location: `src/models/result.py`
- Contains: `@dataclass` types, `to_dict()` / `to_json()` on `AnalysisResult`.
- Depends on: `Verdict`, `ConfidenceLevel` from `src/config/settings.py`.
- Used by: All analyzers and UI layers that render or export results.
- Purpose: Enums, frozen threshold and subsystem configs, cached `Settings` singleton.
- Location: `src/config/settings.py`
- Contains: `Verdict`, `ConfidenceLevel`, `ThresholdConfig`, `NLTKConfig`, `GPT2Config`, `VisualizationConfig`, `Settings`, `get_settings()` (`@lru_cache`).
- Depends on: `os.environ` for `AI_DETECTOR_DEBUG`, `AI_DETECTOR_LOG_LEVEL`.
- Used by: `BaseAnalyzer`, `ChartGenerator`, apps.
- Purpose: Logging setup, text cleaning/tokenization/metrics, optional NLTK downloads, plotting.
- Location: `src/utils/logging_config.py`, `src/utils/text_processing.py`, `src/utils/visualization.py`
- Contains: `TextProcessor` (classmethods for corpus-safe NLP), `ChartGenerator` (Plotly primary, Matplotlib `Agg` backend).
- Depends on: NLTK, Plotly, Matplotlib, NumPy; `get_settings()` where needed.
- Used by: Analyzers and Streamlit tabs.
## Data Flow
- No server-side session store; Streamlit reruns the script. Heavy objects (analyzer, `ChartGenerator`) are cached with `@st.cache_resource` in each app file.
- Settings are process-wide via `get_settings()` cache.
## Key Abstractions
- Purpose: Uniform pipeline for text-in → `AnalysisResult` out.
- Examples: `src/analyzers/base_analyzer.py`
- Pattern: Template Method — `analyze()` is concrete; `_perform_analysis()` abstract.
- Purpose: Single place for NLTK data guarantees, tokenization, and `TextMetrics` computation.
- Examples: `src/utils/text_processing.py`
- Pattern: Stateful class with class-level caches (`_nltk_initialized`, stopwords).
- Purpose: Stable contract between analysis and presentation/API docs.
- Examples: `src/models/result.py`
- Pattern: Dataclasses with helper methods (`add_warning`, `add_score`, `to_dict`).
- Purpose: Decouple Plotly/Matplotlib construction from Streamlit layout.
- Examples: `src/utils/visualization.py`
- Pattern: Small service class configured from `VisualizationConfig`.
## Entry Points
- Location: `app.py`
- Triggers: `streamlit run app.py`
- Responsibilities: NLTK-only UX; `load_analyzer(ngram_size)` → `NLTKAnalyzer`.
- Location: `ensemble.py`
- Triggers: `streamlit run ensemble.py`
- Responsibilities: `EnsembleAnalyzer` UX; combined GPT-2 + NLTK (+ optional RoBERTa).
- Location: `test.py`
- Triggers: `streamlit run test.py`
- Responsibilities: `GPT2Analyzer`-only UX (despite the name `test.py`).
- Documented in `docs/API.md`; import analyzers from `src.analyzers` and call `.analyze(text)`.
- Location: `setup.py` — `packages=find_packages(where="src")`, `package_dir={"": "src"}` so the installable name maps to the `src` tree.
## Error Handling
- Empty/short text: early return with warnings, no model call.
- NLTK corpus missing: `NLTKAnalyzer._build_model` raises `RuntimeError` with download hint after logging.
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
