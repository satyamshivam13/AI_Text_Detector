# External Integrations

**Analysis Date:** 2026-04-02

## APIs & External Services

**Model & artifact downloads (Hugging Face Hub):**
- GPT-2 — `GPT2TokenizerFast.from_pretrained` and `GPT2LMHeadModel.from_pretrained` in `src/analyzers/gpt2_analyzer.py` using `settings.gpt2.model_name` (default `gpt2` from `src/config/settings.py`). Optional `cache_dir` from `GPT2Config`.
- RoBERTa — `RobertaTokenizer.from_pretrained("roberta-base")` and sequence classification model load in `src/analyzers/roberta_analyzer.py`. Ensemble notes RoBERTa disabled by weight `0.0` in `src/analyzers/ensemble_analyzer.py` until fine-tuning.
- Network: First run (or empty cache) pulls weights from the public Hugging Face Hub; `transformers`/`huggingface_hub` handle HTTP. Docker Compose mounts `model_cache` to `/home/appuser/.cache` for `gpt2-detector` and `ensemble-detector` in `docker-compose.yml`.

**NLTK data:**
- Remote download via `nltk.download(...)` — Dockerfile runs downloads for punkt, punkt_tab, stopwords, brown, averaged_perceptron_tagger. `NLTKConfig.required_data` in `src/config/settings.py` matches expected packages. Compose service `nltk-detector` persists `nltk_data` volume at `/home/appuser/nltk_data`.

**No first-party REST API server:**
- The product is Streamlit apps, not a separate HTTP JSON API. Programmatic use is in-process Python (see `docs/API.md` for analyzer imports). Do not assume OpenAPI routes unless added later.

## Data Storage

**Databases:**
- Not applicable — No SQL/NoSQL clients, ORMs, or connection strings in application code.

**File Storage:**
- Local filesystem and container volumes only — Application code, NLTK data dir, Hugging Face cache under user home (`.cache`) in containers per `docker-compose.yml`.

**Caching:**
- Hugging Face/transformers model cache on disk (path influenced by `cache_dir` in settings and default cache layout).
- Streamlit `@st.cache_resource` in `app.py` (and analogous patterns in other entry files) caches analyzer and chart generator instances in process memory.

## Authentication & Identity

**Auth Provider:**
- Not applicable for core app — Streamlit apps are unauthenticated single-user sessions unless deployed behind a reverse proxy or platform IAM. No OAuth, API keys, or session stores in `src/`.

## Monitoring & Observability

**Error Tracking:**
- None integrated — No Sentry, Rollbar, or similar in `requirements.txt` or imports.

**Logs:**
- Standard library `logging` configured in `src/utils/logging_config.py` (stdout; optional file path). Levels for `transformers`, `torch`, `urllib3`, `filelock` reduced to WARNING to limit noise.

## CI/CD & Deployment

**Hosting:**
- Documented options in `docs/DEPLOYMENT.md` (Docker, Heroku, AWS, Azure, GCP); not wired as code in this repo snapshot.

**CI Pipeline:**
- Not detected — No `.github/workflows/` or similar in workspace.

## Environment Configuration

**Required env vars:**
- None strictly required for local run beyond Python/Streamlit defaults. Optional: `AI_DETECTOR_DEBUG`, `AI_DETECTOR_LOG_LEVEL` in `src/config/settings.py`. Docker sets `PYTHONPATH`, Streamlit server env vars in `Dockerfile` / `docker-compose.yml`.

**Secrets location:**
- No application secrets required for model download of public GPT-2/roberta-base weights. If adding private Hub tokens or paid APIs, use platform secret stores or `.env` (not committed); `docs/DEPLOYMENT.md` mentions a `.env` example with `LOG_LEVEL`, `NGRAM_ORDER`, etc., which may not match `get_settings()` — treat docs as aspirational until aligned with `src/config/settings.py`.

## Webhooks & Callbacks

**Incoming:**
- None — No webhook endpoints; Streamlit exposes UI and internal health URL only.

**Outgoing:**
- None for business logic — Only implicit outbound HTTP from `transformers`/NLTK when fetching models or data.

## Third-Party Python stack notes

**HTTP stack:**
- `urllib3` appears only as a logging noise reducer in `src/utils/logging_config.py` (dependency of libraries that perform downloads).

**Streamlit health:**
- `Dockerfile` `HEALTHCHECK` uses `curl` against `http://localhost:8501/_stcore/health`.

---

*Integration audit: 2026-04-02*
