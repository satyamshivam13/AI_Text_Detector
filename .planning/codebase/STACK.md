# Technology Stack

**Analysis Date:** 2026-07-06

## Languages

**Primary:**
- Python 3 - Entire codebase: analyzers (`src/analyzers/`), evaluation harness (`src/evaluation/`), Streamlit UIs (`app.py`, `gpt2_app.py`, `ensemble.py`), shared UI helpers (`src/ui/`), utilities (`src/utils/`)

**Secondary:**
- Not applicable - No JavaScript/TypeScript; all HTML/CSS is inline strings rendered through Streamlit (`src/ui/styles.py`, `src/ui/components.py`)

**Version note:** `setup.py` declares `python_requires=">=3.8"` with classifiers through 3.11, but CI (`.github/workflows/ci.yml`) tests only 3.9/3.10/3.11 and `src/utils/logging_config.py` uses `list[logging.Handler]` runtime annotations (3.9+ syntax). Treat 3.9 as the effective floor.

## Runtime

**Environment:**
- CPython 3.9+ (Docker image pins `python:3.9-slim` in `Dockerfile`; CI matrix runs 3.9, 3.10, 3.11)
- GPU optional: `GPT2Analyzer.device` auto-selects CUDA when available, else CPU (`src/analyzers/gpt2_analyzer.py`)

**Package Manager:**
- pip (used in `Dockerfile`, `Makefile`, CI)
- Lockfile: Not detected - version ranges only, pinned in `requirements.txt` (no `poetry.lock`/`Pipfile.lock`/`uv.lock`)

## Frameworks

**Core:**
- Streamlit >=1.28,<2 - Sole web/UI framework; three entry points run via `streamlit run`: `app.py` (NLTK), `gpt2_app.py` (GPT-2), `ensemble.py` (ensemble)
- PyTorch (`torch`) >=2.6,<3 - Model inference and device selection in `src/analyzers/gpt2_analyzer.py`, `src/analyzers/roberta_analyzer.py`, `src/analyzers/binoculars_analyzer.py`
- Hugging Face Transformers >=4.48,<5 - `GPT2LMHeadModel`, `GPT2TokenizerFast`, `RobertaTokenizer`, `RobertaForSequenceClassification`; all `from_pretrained` calls pass `use_safetensors=True` and a pinnable `revision` (supply-chain hardening; floors chosen to clear known deserialization advisories per comments in `requirements.txt`)
- NLTK >=3.8.1,<4 - Brown-corpus n-gram language model in `src/analyzers/nltk_analyzer.py`; tokenization/metrics in `src/utils/text_processing.py`

**Testing:**
- pytest >=7.4 with pytest-cov, pytest-mock, pytest-asyncio (`requirements-dev.txt`)
- `pytest.ini` defines a `slow` marker; CI runs `-m "not slow"` with `--cov=src`
- Test suite: `tests/` (23 test modules covering analyzers, evaluation, UI contracts, Streamlit apps)

**Build/Dev:**
- setuptools via `setup.py` - `packages=find_packages(where="src")`, `package_dir={"": "src"}`, version 2.0.0
- black (line length 100), isort (`--profile=black`), flake8 (`.flake8`: max 100, ignores E203/W503, per-file E402 exemptions for the three Streamlit entry points), mypy (`--ignore-missing-imports`), pylint - orchestrated by `Makefile` targets `format`/`lint`
- pre-commit >=3.3.0 declared in `requirements-dev.txt` (no `.pre-commit-config.yaml` detected at repo root)
- Sphinx + sphinx-rtd-theme declared in `requirements-dev.txt` (docs tooling; no `docs/conf.py` build detected)

## Key Dependencies

**Critical:**
- `streamlit` - The only serving layer; configured via `.streamlit/config.toml`
- `torch` + `transformers` - GPT-2 (`gpt2`), DistilGPT-2 (`distilgpt2`, Binoculars performer), RoBERTa (`roberta-base`) loading; safetensors-only weight loading enforced in all three transformer analyzers
- `nltk` - Brown corpus n-gram model; required data packages listed in `NLTKConfig.required_data` (`src/config/settings.py`): punkt, punkt_tab, stopwords, brown, averaged_perceptron_tagger

**Infrastructure:**
- `numpy` >=1.24,<2 / `pandas` >=2,<3 - Numeric/tabular computation in analyzers, evaluation metrics (`src/evaluation/metrics.py`), and charts
- `plotly` >=5.18,<6 - Primary interactive charts (`src/utils/visualization.py`, rendered via `st.plotly_chart`)
- `matplotlib` >=3.7,<4 - Secondary charting with Agg backend (`src/utils/visualization.py`); calibration/ROC images in `docs/benchmarks/`

**Removed (do not reintroduce without cause):**
- `pydantic`, `structlog`, `python-dotenv` are no longer in `requirements.txt`; config/models use stdlib `dataclasses` (`src/config/settings.py`, `src/models/result.py`) and logging uses stdlib `logging` (`src/utils/logging_config.py`)

## Configuration

**Environment:**
- `AI_DETECTOR_DEBUG` (bool, default false) and `AI_DETECTOR_LOG_LEVEL` (default INFO) - read in `Settings.__post_init__` (`src/config/settings.py`)
- All other configuration is code-level frozen dataclasses: `ThresholdConfig`, `NLTKConfig`, `GPT2Config`, `RoBERTaConfig`, `BinocularsConfig`, `EnsembleConfig`, `VisualizationConfig` in `src/config/settings.py`, accessed via the `@lru_cache` singleton `get_settings()`
- Docker/Streamlit env: `PYTHONPATH=/app/src`, `STREAMLIT_SERVER_PORT`, `STREAMLIT_SERVER_ADDRESS`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` (`Dockerfile`, `docker-compose.yml`)
- No `.env` files present; no dotenv loading anywhere

**Build:**
- `setup.py` - package metadata and install
- `requirements.txt` / `requirements-dev.txt` - dependency pins
- `.streamlit/config.toml` - server (headless, port 8501, `maxUploadSize=10`, XSRF on, CORS off), dark theme, telemetry off, logger format
- `Dockerfile` - `python:3.9-slim`, non-root `appuser`, NLTK data pre-download, `ENTRYPOINT ["streamlit", "run"]`, default `CMD ["app.py"]`, health check on `/_stcore/health`
- `docker-compose.yml` - three services (nltk-detector :8501, gpt2-detector :8502, ensemble-detector :8503) sharing one image; named volumes `nltk_data` and `model_cache`; per-service memory/CPU limits (2G/4G/6G)
- `Makefile` - install/run/test/lint/format/docker targets; sets `PYTHONPATH=src` for run/test/lint
- `Procfile` - Heroku-style: `web: streamlit run app.py --server.port=$PORT ...`
- `pytest.ini` - `slow` marker registration

## Platform Requirements

**Development:**
- Python 3.9+ (effective floor; see version note), pip, virtualenv per `docs/DEPLOYMENT.md`
- NLTK data download required post-install (`make install` runs it; CI and Dockerfile do the same)
- First GPT-2/RoBERTa/Binoculars run downloads model weights from Hugging Face Hub (network needed once, then cached)
- Quality gates before commit: `make format && make lint` (Black 100, isort black-profile, flake8 100)

**Production:**
- Container: Linux, port 8501, health check `curl http://localhost:8501/_stcore/health` (`Dockerfile`)
- Resource guidance from `docker-compose.yml`: NLTK app ~2G RAM; GPT-2 app ~4G; ensemble ~6G; GPU optional
- PaaS: `Procfile` supports Heroku-style deployment of the NLTK app
- CI: GitHub Actions (`.github/workflows/ci.yml`) - lint job on 3.11 (flake8/black/isort over `src/ tests/ app.py gpt2_app.py ensemble.py`) plus test matrix 3.9/3.10/3.11 with NLTK data download and coverage

---

*Stack analysis: 2026-07-06*
