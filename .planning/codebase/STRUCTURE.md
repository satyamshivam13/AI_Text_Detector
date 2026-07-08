# Structure

**Analysis Date:** 2026-07-06

## Directory Layout

```
AI_Text_Detector/
├── app.py                     # Streamlit: NLTK-only UI (torch-free)
├── gpt2_app.py                # Streamlit: GPT-2 UI (renamed from test.py)
├── ensemble.py                # Streamlit: ensemble UI
├── src/
│   ├── analyzers/
│   │   ├── base_analyzer.py       # Template Method: analyze() + _apply_input_cap
│   │   ├── nltk_analyzer.py       # Brown-corpus n-gram (Witten-Bell smoothing, cached)
│   │   ├── gpt2_analyzer.py       # GPT-2 perplexity (safetensors)
│   │   ├── roberta_analyzer.py    # RoBERTa classifier (disabled by default)
│   │   ├── binoculars_analyzer.py # cross-perplexity (gpt2 + distilgpt2)
│   │   ├── calibration.py         # logistic_ai_probability
│   │   ├── ensemble_analyzer.py   # weighted calibrated fusion
│   │   ├── __init__.py            # lazy __getattr__ for torch-backed analyzers
│   │   └── AGENTS.md
│   ├── config/settings.py     # frozen dataclass configs + get_settings() singleton
│   ├── models/result.py       # AnalysisResult / TextMetrics / DetectionScore
│   ├── ui/                    # NEW: shared Streamlit components
│   │   ├── styles.py             # BASE_CSS + inject_css
│   │   ├── components.py         # render_verdict_card/warnings/footer/error, verdict maps
│   │   └── __init__.py
│   ├── evaluation/           # NEW: measurement layer
│   │   ├── metrics.py            # pure-NumPy accuracy/PR/F1/ROC/AUROC/FPR/FNR/ECE
│   │   ├── dataset.py            # JSONL loader
│   │   ├── benchmark.py          # runner + CLI + plots
│   │   └── __init__.py
│   └── utils/
│       ├── text_processing.py    # TextProcessor (clean/tokenize/metrics/NLTK bootstrap)
│       ├── visualization.py      # ChartGenerator (Plotly + Matplotlib Agg)
│       ├── ui_contract.py        # shared UI copy (limitations, mode guidance)
│       ├── logging_config.py     # setup_logging / get_logger
│       └── AGENTS.md
├── data/benchmark/            # samples.jsonl (12 human + 12 AI) + README
├── docs/                     # API.md, DEPLOYMENT.md, benchmarks/ (reports + PNGs)
├── tests/                    # 22 test files, ~231 test functions
├── .github/workflows/ci.yml  # lint + test matrix
├── Dockerfile, docker-compose.yml, Procfile, Makefile
├── requirements.txt, requirements-dev.txt, setup.py, pytest.ini, .flake8
└── README / CONTRIBUTING / SECURITY / CODE_OF_CONDUCT / CHANGELOG / LICENSE
```

## Key Locations

- **Add an analyzer:** new file in `src/analyzers/`, extend `BaseAnalyzer`,
  implement `_perform_analysis`, register in `__init__.py::_LAZY_MODULES` if it
  needs torch.
- **Tune detection:** `src/config/settings.py` (thresholds, calibration
  midpoints/slopes, ensemble weights). Never hardcode thresholds in analyzers.
- **Shared UI change:** `src/ui/` (once, not per app).
- **Evaluate:** `python -m src.evaluation.benchmark`; dataset in `data/benchmark/`.

## Naming Conventions

- Modules `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`.
- Tests `tests/test_<module>.py`. Streamlit entries are short root scripts.
- Package `__init__.py` files exist under `src/`; import concrete symbols from
  submodules.

## Not Tracked (gitignored local artifacts)

`venv/`, `graphify-out/`, `.obsidian/`, `.pytest_cache/`, `__pycache__/`,
`SESSION_AUDIT_LOG.md`, `/models/`, `*.safetensors`, `*.bin`.
