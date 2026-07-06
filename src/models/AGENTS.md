# src/models & src/config — Data Models and Settings

## Purpose
`src/models/` owns the serializable result shape (`AnalysisResult`, `TextMetrics`, `DetectionScore`).
`src/config/` owns enums, frozen threshold/subsystem configs, and the `Settings` singleton.
Both directories are intentionally thin — no analysis logic, no I/O, no Streamlit imports.

## Entry Points
- `src/models/result.py` — `AnalysisResult`, `TextMetrics`, `DetectionScore` dataclasses + `to_dict()` / `to_json()`
- `src/config/settings.py` — `Verdict`, `ConfidenceLevel`, `DetectionMethod` enums; `ThresholdConfig`, `NLTKConfig`, `GPT2Config`, `VisualizationConfig` frozen dataclasses; mutable `Settings` + `get_settings()` singleton

## Contracts & Invariants

### AnalysisResult
- Default state is `Verdict.UNCERTAIN`, `confidence=0.0`, `ConfidenceLevel.LOW` — always valid even if analysis fails
- `add_warning(msg)` is idempotent (deduplicates). Use it instead of directly appending to `result.warnings`
- `add_score(DetectionScore)` appends to `result.scores`. The order matters for display — add ensemble/overall score first, then individual analyzer scores
- `to_dict()` / `to_json()` produce stable serialized output consumed by the "Analysis Metadata" expander in the UI. Do not change key names without updating display code
- `is_ai_generated` and `is_human_written` are convenience properties; they do not cover `Verdict.UNCERTAIN` — check explicitly if uncertain handling matters

### TextMetrics
- `lexical_diversity` is a computed `@property` (unique_words / total_words), not stored — do not assign it
- `word_frequencies` is a raw dict; downstream code (e.g. `ChartGenerator`) filters by min frequency — do not pre-filter here

### DetectionScore
- `indicates_ai=True` drives the 🔴/🟢 indicator in the UI score rows — set it accurately
- `weight` should reflect the actual contribution to ensemble fusion if this score is used in weighted averaging

### Settings & Config
- `get_settings()` is `@lru_cache(maxsize=1)` — the single instance is shared process-wide. Never instantiate `Settings()` directly
- Threshold values (`ThresholdConfig`) are `frozen=True` — do not attempt mutation; create a new instance if you need different thresholds in tests
- Environment overrides: `AI_DETECTOR_DEBUG=true` sets `settings.debug`; `AI_DETECTOR_LOG_LEVEL` sets `settings.log_level` — these are the only env vars the app reads
- `NLTKConfig.required_data` tuple is the authoritative list of NLTK corpora to download — update here if adding new NLTK resources

## Patterns
To add a new field to `AnalysisResult`:
1. Add the field with a sensible default to the dataclass in `result.py`
2. Update `to_dict()` to include it (required for JSON export and test assertions)
3. Populate it in the relevant analyzer's `_perform_analysis`

To add a new threshold:
1. Add the field to `ThresholdConfig` with a default value
2. Reference it via `self.thresholds.new_field` in the analyzer
3. Add test assertions in `tests/test_base_analyzer_contract.py` if it affects verdict logic

To add a new verdict level:
1. Add to the `Verdict` enum
2. Update `BaseAnalyzer._determine_verdict` probability branches
3. Update verdict-to-CSS mapping in `app.py` and `ensemble.py`
4. Update `is_ai_generated` / `is_human_written` properties if needed

## Anti-patterns
- Do not add business logic (scoring, thresholds, text analysis) to result dataclasses
- Do not import analyzer modules from `models/` or `config/` — the dependency direction is one-way: analyzers → models/config, never the reverse
- Do not call `get_settings()` inside dataclass `__post_init__` methods — pass config explicitly if needed

## Related Context
- Consumers of these models: `src/analyzers/AGENTS.md`
- Visualization of results: `src/utils/AGENTS.md`
