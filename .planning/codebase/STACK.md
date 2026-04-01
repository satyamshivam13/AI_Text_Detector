# Technology Stack

**Analysis Date:** 2026-04-02

## Languages

**Primary:**
- Python 3 — Application, analyzers, Streamlit UIs; `setup.py` declares `python_requires=">=3.8"` with classifiers through 3.11; `Dockerfile` pins runtime image `python:3.9-slim`.

**Secondary:**
- Not applicable — No TypeScript, JavaScript bundles, or separate frontend beyond Streamlit-rendered HTML/CSS in `app.py`, `test.py`, and `ensemble.py`.

## Runtime

**Environment:**
- CPython (see Docker: `python:3.9-slim` in `Dockerfile`).

**Package Manager:**
- pip — Used in `Dockerfile` (`pip install -r requirements.txt`).
- Lockfile: Not detected — No `poetry.lock`, `Pipfile.lock`, or `uv.lock` in repo; pin ranges live in `requirements.txt`.

## Frameworks

**Core:**
- Streamlit (>=1.28,<2) — Web UI; entry via `streamlit run` with `app.py` (NLTK), `test.py` (GPT-2), or `ensemble.py` (ensemble). See `docker-compose.yml` service `command` overrides.
- PyTorch (`torch` >=2,<3) — Device selection and model inference in `src/analyzers/gpt2_analyzer.py` and `src/analyzers/roberta_analyzer.py`.
- Hugging Face Transformers (`transformers` >=4.35,<5) — `GPT2LMHeadModel`, `GPT2TokenizerFast`, `RobertaTokenizer`, `RobertaForSequenceClassification` in those analyzers.
- NLTK (>=3.8,<4) — N-gram / Brown corpus analysis in `src/analyzers/nltk_analyzer.py`.

**Testing:**
- pytest (>=7.4) — Declared in `requirements-dev.txt` and `setup.py` `extras_require.dev`; tests under `tests/`.

**Build/Dev:**
- setuptools — Package layout in `setup.py` with `packages=find_packages(where="src")`, `package_dir={"": "src"}`.
- black, flake8, isort, mypy, pylint, pre-commit — Listed in `requirements-dev.txt`.
- Sphinx + sphinx-rtd-theme — Documentation tooling in `requirements-dev.txt`.

## Key Dependencies

**Critical:**
- `streamlit` — Sole HTTP-serving application layer; configuration in `.streamlit/config.toml`.
- `torch` + `transformers` — GPT-2 and RoBERTa model loading (`from_pretrained`) in `src/analyzers/gpt2_analyzer.py`, `src/analyzers/roberta_analyzer.py`.
- `nltk` — Corpus and tokenizer resources; Dockerfile pre-downloads punkt, punkt_tab, stopwords, brown, averaged_perceptron_tagger.

**Data & visualization:**
- `numpy`, `pandas` — Numerical/tabular use in analyzers and utilities.
- `matplotlib` (Agg backend in `src/utils/visualization.py`), `plotly` — Charts for Streamlit (`st.plotly_chart` in `app.py`).

**Declared but lightly or unused in source:**
- `pydantic` — Listed in `requirements.txt`; `src/config/settings.py` and `src/models/result.py` use `dataclasses` instead. Prefer aligning future config/models with one approach.
- `python-dotenv`, `structlog` — Present in `requirements.txt`; no `load_dotenv` or `structlog` usage detected in application Python files; logging uses stdlib in `src/utils/logging_config.py`.

## Configuration

**Environment:**
- Application toggles: `AI_DETECTOR_DEBUG`, `AI_DETECTOR_LOG_LEVEL` — Read in `Settings.__post_init__` in `src/config/settings.py`.
- Docker / Streamlit: `PYTHONPATH=/app/src`, `STREAMLIT_SERVER_PORT`, `STREAMLIT_SERVER_ADDRESS`, `STREAMLIT_BROWSER_GATHER_USAGE_STATS` — Set in `Dockerfile` and `docker-compose.yml`.
- Streamlit server/theme/browser/logger — `.streamlit/config.toml` (e.g. `headless`, `port`, `maxUploadSize`, XSRF).

**Build:**
- `Dockerfile` — Multi-stage base, system `build-essential` + `curl`, NLTK download step, `ENTRYPOINT ["streamlit", "run"]`, default `CMD ["app.py"]`.
- `docker-compose.yml` — Three services sharing the same image build; different ports and commands for NLTK vs GPT-2 vs ensemble; named volumes `nltk_data` and `model_cache`.

## Platform Requirements

**Development:**
- Python >=3.8, pip, virtualenv per `docs/DEPLOYMENT.md`; run `streamlit run app.py` from repo root (see `app.py` docstring). Install from `requirements.txt`; dev extras via `requirements-dev.txt` or `pip install -e ".[dev]"` per `setup.py`.

**Production:**
- Container: Linux image exposing port 8501; health check curls `http://localhost:8501/_stcore/health` in `Dockerfile`. GPT-2/ensemble paths need more RAM/CPU per `docker-compose.yml` `deploy.resources` limits.

---

*Stack analysis: 2026-04-02*
