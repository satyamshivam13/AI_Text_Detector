# Integrations

**Analysis Date:** 2026-07-06

The project is **local-first**: core detection requires no third-party API calls
and no user text leaves the machine. The only external dependency at runtime is
the Hugging Face Hub, used to download model weights on first use.

## External Model Downloads (Hugging Face Hub)

- **GPT-2** (`gpt2`) — downloaded by `src/analyzers/gpt2_analyzer.py` via
  `GPT2LMHeadModel.from_pretrained(..., use_safetensors=True, revision=...)`.
  ~500 MB, cached after first run.
- **DistilGPT-2** (`distilgpt2`) — the Binoculars "performer" model in
  `src/analyzers/binoculars_analyzer.py`; observer is `gpt2`. Both share the
  GPT-2 tokenizer.
- **RoBERTa** (`roberta-base`) — `src/analyzers/roberta_analyzer.py`. Loaded
  only when `EnsembleConfig.weight_roberta > 0` (disabled by default: an
  untrained classification head). Uses `use_safetensors=True`.
- Loading is hardened: `use_safetensors=True` avoids pickle deserialization, and
  a configurable `revision` (in `GPT2Config` / `RoBERTaConfig` /
  `BinocularsConfig`) allows pinning a Hub commit. **Revisions default to
  `None`** (tracks the default branch) — pin a commit hash for high-assurance
  deployments.

## NLTK Corpora (downloaded, then local)

`src/utils/text_processing.py::TextProcessor.ensure_nltk_data()` downloads
`punkt`, `punkt_tab`, `stopwords`, `brown`, `averaged_perceptron_tagger` on first
use (retried on failure; only marks initialized when all are present). The
`Dockerfile` pre-downloads these at build time.

## Databases / Auth / Webhooks

- **None.** No database, no authentication provider, no message queue, no
  webhooks, no outbound telemetry. Streamlit's usage stats are disabled
  (`STREAMLIT_BROWSER_GATHER_USAGE_STATS=false` in Docker; `.streamlit/config.toml`).

## CI / Dev-time Integrations

- **GitHub Actions** (`.github/workflows/ci.yml`) — lint (flake8/black/isort) +
  pytest matrix (Python 3.9/3.10/3.11), `pip` cache, NLTK data download step.
- **GitHub** repo `satyamshivam13/AI_Text_Detector` — PR-based workflow; automated
  reviewers (Copilot, GitGuardian) run on PRs.

## Deployment Surfaces

- **Docker** (`Dockerfile`, `docker-compose.yml`) — single image, three Compose
  services (`nltk-detector`, `gpt2-detector`, `ensemble-detector`) differing only
  by the Streamlit entry script and resource limits. Health check curls
  `http://localhost:8501/_stcore/health`.
- **Procfile** — present for PaaS (e.g. Heroku-style) `streamlit run` deploys.
- No cloud provider SDKs, secrets managers, or IaC are wired in.
