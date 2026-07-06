# src/utils — Shared Utilities

## Purpose
Cross-cutting helpers consumed by analyzers, Streamlit apps, and tests.
Four distinct responsibilities: text processing, chart generation, UI copy contracts,
and logging setup. Does **not** own analysis logic or data models.

## Entry Points
- `text_processing.py` — `TextProcessor`: text cleaning, tokenization, `TextMetrics` computation, NLTK bootstrap
- `visualization.py` — `ChartGenerator`: Plotly (primary) + Matplotlib Agg (fallback) chart factories
- `ui_contract.py` — Shared markdown strings for sidebar limitations, result reminders, mode guidance
- `logging_config.py` — `setup_logging()`, `get_logger()`, third-party log quieting

## Contracts & Invariants

### TextProcessor
- `TextProcessor.clean_text(text)` and `TextProcessor.compute_metrics(text)` are **classmethods** — call them without instantiation
- `compute_metrics` returns a `TextMetrics` dataclass; it always populates `word_frequencies`, `sentence_lengths`, and all scalar fields — never assume optional fields are absent
- NLTK data bootstrap is guarded by `_nltk_initialized` class-level flag — it runs once per process. Do not call `nltk.download()` elsewhere in the codebase
- `TextProcessor` uses class-level `_stopwords` cache; do not pass stopwords around manually

### ChartGenerator
- All chart methods return a Plotly `Figure` (or Matplotlib `Figure` for Agg methods) — callers pass it to `st.plotly_chart()` or `st.pyplot()`
- `ChartGenerator` is configured from `VisualizationConfig` — color constants and default sizes live there, not in the chart methods
- `create_metrics_gauge(result)` expects a full `AnalysisResult`; `create_word_frequency_chart_plotly(freq_dict, top_n)` expects a pre-filtered dict

### ui_contract.py
- All Streamlit entry points **must** use `build_limitations_markdown()`, `build_result_reminder_markdown()`, and `build_mode_guidance_markdown()` — do not inline the copy
- `LIMITATIONS_BULLETS` and `RESULT_LEVEL_REMINDER` are the single source of truth for ethical framing copy; update here, not in individual apps

### logging_config.py
- Always call `get_logger(__name__)` at module level — never pass logger instances around
- `setup_logging()` suppresses `transformers`, `torch`, `urllib3`, `filelock` loggers — call it once at app startup (already done in each Streamlit entrypoint)

## Patterns
To add a new chart type:
1. Add a method to `ChartGenerator` in `visualization.py`
2. Accept an `AnalysisResult` or specific data dict as input
3. Use color constants from `self.config` (`VisualizationConfig`)
4. Return a Plotly `Figure`; use Matplotlib only if Plotly can't handle the chart type

To add new UI copy (e.g. a new sidebar section):
1. Add the string constant or builder function to `ui_contract.py`
2. Import and call it in the relevant Streamlit app — do not inline strings

## Anti-patterns
- Do not import `streamlit` inside `text_processing.py`, `visualization.py`, or `logging_config.py` — they must remain importable without Streamlit
- Do not call `setup_logging()` more than once per process; it's already called in each app's setup block
- Do not store per-request state on `TextProcessor` class attributes — they are shared across all calls

## Related Context
- Data models used by TextProcessor output: `src/models/AGENTS.md`
- Callers of ChartGenerator and ui_contract: `app.py`, `ensemble.py`, `test.py` at repo root
