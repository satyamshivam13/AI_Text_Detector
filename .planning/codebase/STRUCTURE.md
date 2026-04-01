# Codebase Structure

**Analysis Date:** 2026-04-02

## Directory Layout

```
AI_Text_Detector/
├── app.py                 # Streamlit: NLTK-only detector UI
├── ensemble.py            # Streamlit: ensemble (GPT-2 + NLTK, RoBERTa optional)
├── test.py                # Streamlit: GPT-2-only UI (not pytest)
├── setup.py               # setuptools: package_dir src, requirements.txt install_requires
├── requirements.txt       # Runtime dependencies (referenced by setup.py)
├── docker-compose.yml     # Container orchestration (not expanded here)
├── README.md              # Project overview
├── .streamlit/
│   └── config.toml        # Streamlit theme/config
├── docs/
│   ├── API.md             # Programmatic analyzer usage examples
│   └── DEPLOYMENT.md      # Deployment notes
├── tests/
│   ├── conftest.py        # pytest path fix + shared fixtures
│   ├── test_nltk_analyzer.py
│   ├── test_gpt2_analyzer.py
│   ├── test_roberta_analyzer.py
│   ├── test_ensemble_analyzer.py
│   ├── test_result_model.py
│   └── test_text_processing.py
└── src/                   # Main Python package root (on sys.path in apps/tests)
    ├── __init__.py
    ├── analyzers/
    │   ├── __init__.py    # Re-exports analyzer classes
    │   ├── base_analyzer.py
    │   ├── nltk_analyzer.py
    │   ├── gpt2_analyzer.py
    │   ├── roberta_analyzer.py
    │   └── ensemble_analyzer.py
    ├── models/
    │   ├── __init__.py
    │   └── result.py      # AnalysisResult, TextMetrics, DetectionScore
    ├── config/
    │   ├── __init__.py
    │   └── settings.py    # Verdict, thresholds, get_settings()
    └── utils/
        ├── __init__.py
        ├── logging_config.py
        ├── text_processing.py
        └── visualization.py
```

## Directory Purposes

**Repository root:**
- Purpose: Operator entrypoints and packaging metadata.
- Contains: Streamlit scripts, `setup.py`, `requirements.txt`, compose file, top-level docs.
- Key files: `app.py`, `ensemble.py`, `test.py`, `setup.py`

**`src/`:**
- Purpose: Installable library code; all business logic for detection and shared utilities.
- Contains: Analyzers, models, config, utils.
- Key files: `src/analyzers/base_analyzer.py`, `src/models/result.py`, `src/config/settings.py`

**`src/analyzers/`:**
- Purpose: Pluggable detection backends and ensemble orchestration.
- Contains: One module per analyzer + package `__init__.py` exposing `__all__`.
- Key files: `src/analyzers/__init__.py`, `src/analyzers/ensemble_analyzer.py`

**`src/models/`:**
- Purpose: Data transfer objects for analysis output.
- Contains: Dataclasses only in current tree.
- Key files: `src/models/result.py`

**`src/config/`:**
- Purpose: Centralized enums and configuration objects.
- Key files: `src/config/settings.py`

**`src/utils/`:**
- Purpose: Cross-cutting helpers (no UI).
- Key files: `src/utils/text_processing.py`, `src/utils/visualization.py`, `src/utils/logging_config.py`

**`tests/`:**
- Purpose: Pytest suites mirroring analyzer and utility modules.
- Contains: `conftest.py` prepends `../src` to `sys.path` for imports like `src.analyzers...`.
- Key files: `tests/conftest.py`, `tests/test_ensemble_analyzer.py`

**`docs/`:**
- Purpose: Human-facing API and deployment documentation.
- Key files: `docs/API.md`, `docs/DEPLOYMENT.md`

## Key File Locations

**Entry Points:**
- `app.py`: NLTK Streamlit application.
- `ensemble.py`: Ensemble Streamlit application.
- `test.py`: GPT-2 Streamlit application.

**Configuration:**
- `src/config/settings.py`: Thresholds, NLTK/GPT-2/visualization knobs, `get_settings()`.
- `.streamlit/config.toml`: Streamlit UI configuration.

**Core Logic:**
- `src/analyzers/base_analyzer.py`: Shared analysis pipeline and verdict logic.
- `src/analyzers/nltk_analyzer.py`, `gpt2_analyzer.py`, `roberta_analyzer.py`, `ensemble_analyzer.py`: Concrete detectors.

**Testing:**
- `tests/*.py`: Mirror modules under `src/`; shared fixtures in `tests/conftest.py`.

## Naming Conventions

**Files:**
- Streamlit apps: short top-level names (`app.py`, `ensemble.py`) — except `test.py` which is a Streamlit GPT-2 app, not a pytest file.
- Library modules: `snake_case.py` under `src/`.
- Tests: `test_<module_basename>.py` in `tests/`.

**Directories:**
- Package names: lowercase (`analyzers`, `utils`, `config`, `models`).

**Classes:**
- Analyzers: `*Analyzer` suffix (`NLTKAnalyzer` in `src/analyzers/nltk_analyzer.py`).
- Utilities: `TextProcessor`, `ChartGenerator` in `src/utils/`.

## Where to Add New Code

**New detection backend:**
- Implementation: `src/analyzers/<name>_analyzer.py` subclassing `BaseAnalyzer` from `src/analyzers/base_analyzer.py`.
- Registration: Export in `src/analyzers/__init__.py` `__all__`.
- Tests: `tests/test_<name>_analyzer.py`.
- Optional UI: New Streamlit file at repo root following `app.py` pattern (path insert + imports).

**New feature on existing pipeline (e.g. extra metric):**
- Extend `AnalysisResult` / `TextMetrics` in `src/models/result.py` if the contract changes.
- Compute in `TextProcessor` or inside `_perform_analysis` depending on whether it is model-agnostic.
- Update `_determine_verdict` / `_generate_explanation` in `src/analyzers/base_analyzer.py` if verdict logic should use it globally.

**New shared helper:**
- Add to `src/utils/` with a focused module name; import via `src.utils.<module>`.

**New Streamlit-only behavior:**
- Keep in the relevant root script (`app.py`, `ensemble.py`, `test.py`) or extract small pure functions into `src/utils/` if reused.

## Special Directories

**`.planning/codebase/`:**
- Purpose: GSD / planner-oriented codebase maps (this file and siblings).
- Generated: No — maintained by mapping workflow.
- Committed: Yes (typical for GSD projects).

**`src/` as package root:**
- Purpose: `setup.py` uses `package_dir={"": "src"}` so installed import paths match development imports (`from src.analyzers...`).
- When running Streamlit from repo root, scripts also insert `src` into `sys.path` so the same `src.*` imports resolve.

---

*Structure analysis: 2026-04-02*
