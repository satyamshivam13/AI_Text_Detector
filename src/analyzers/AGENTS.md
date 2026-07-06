# src/analyzers — Detection Pipeline

## Purpose
Owns all text-to-`AnalysisResult` logic. Provides `BaseAnalyzer` (abstract template),
three concrete backends (NLTK, GPT-2, RoBERTa), and `EnsembleAnalyzer` (multi-model fusion).
Does **not** own UI rendering, chart generation, or settings — those live in `utils/` and `config/`.

## Entry Points
- `base_analyzer.py` — Abstract base; `analyze()` is the only public method callers use
- `nltk_analyzer.py` — Brown-corpus n-gram perplexity; fast, no GPU needed
- `gpt2_analyzer.py` — GPT-2 token-loss perplexity; requires `torch` + `transformers`
- `roberta_analyzer.py` — RoBERTa sequence classifier; currently disabled (needs fine-tuning)
- `ensemble_analyzer.py` — Fuses GPT-2 (65%) + NLTK (35%), with optional RoBERTa slot
- `__init__.py` — Eagerly exports `BaseAnalyzer`, `NLTKAnalyzer`; lazily exports the torch-backed three

## Contracts & Invariants
- **Only** call `analyzer.analyze(text: str) → AnalysisResult`. Never call `_perform_analysis` directly from outside this package.
- `_perform_analysis(text, result)` is the single hook subclasses implement — it receives cleaned text and a partially-populated result, and must return the same result object with `perplexity`, `burstiness`, `lexical_diversity`, `sentence_variance`, and `scores` populated.
- `BaseAnalyzer._determine_verdict` is the shared scoring engine. Do not duplicate its logic in subclasses — call `super()` or override with care.
- `EnsembleAnalyzer` **overrides** `analyze()` entirely (not just `_perform_analysis`) to run sub-analyzers in sequence and fuse. The weights are in `EnsembleAnalyzer` itself — change them there, not in individual analyzers.
- Lazy import contract in `__init__.py`: `GPT2Analyzer`, `RoBERTaAnalyzer`, `EnsembleAnalyzer` are loaded via `__getattr__` using `_LAZY_MODULES`. Do not add them to the eager import block — `app.py` must stay torch-free.
- Error contract: all analysis exceptions must be caught inside `BaseAnalyzer.analyze()`. Subclasses should let exceptions bubble up from `_perform_analysis` — the base catches them and sets `Verdict.UNCERTAIN`.

## Patterns
To add a new analyzer backend:
1. Create `src/analyzers/my_analyzer.py` with a class extending `BaseAnalyzer`
2. Implement `_perform_analysis(text, result) → AnalysisResult` only
3. Populate `result.perplexity`, `result.burstiness`, `result.lexical_diversity`, `result.sentence_variance`
4. Use `result.add_score(DetectionScore(...))` for per-signal scores
5. Add to `_LAZY_MODULES` in `__init__.py` if it requires torch/transformers
6. Add a `@st.cache_resource` loader in any Streamlit entry point that uses it

To extend the ensemble:
1. Add sub-analyzer instance in `EnsembleAnalyzer.__init__`
2. Run it in `analyze()` alongside existing sub-analyzers
3. Adjust weights in the fusion section (currently GPT-2: 0.65, NLTK: 0.35)

## Anti-patterns
- Never hardcode threshold values (like `0.30`, `150.0`) in analyzer logic — always use `self.thresholds.*` from `ThresholdConfig`
- Never call `TextProcessor()` to instantiate per analysis — `self.processor` is set in `BaseAnalyzer.__init__`; use `TextProcessor.clean_text()` / `TextProcessor.compute_metrics()` as classmethods
- Don't add Streamlit imports or `st.*` calls here — analyzers are UI-agnostic

## Related Context
- Result model: `src/models/AGENTS.md`
- Settings & thresholds: `src/models/AGENTS.md`
- Shared text utilities: `src/utils/AGENTS.md`
