# Codebase Concerns

**Analysis Date:** 2026-04-02

## Tech Debt

**Triplicated Streamlit entrypoints:**
- Issue: Three large, parallel UIs (`app.py`, `test.py`, `ensemble.py`) repeat CSS, layout, verdict mapping, and chart wiring (~544–585 lines each). Changes require editing multiple files.
- Files: `app.py`, `test.py`, `ensemble.py`
- Impact: Higher defect rate, inconsistent UX, harder refactors.
- Fix approach: Extract shared Streamlit components and styling into a small package under `src/ui/` or a single `pages/` multi-page app; keep one analyzer-specific wiring layer.

**Import path mutation:**
- Issue: Each root script does `sys.path.insert(0, ...)` before importing `src.*`, instead of an installable package layout.
- Files: `app.py`, `ensemble.py`, `test.py`
- Impact: Fragile runs from wrong CWD, awkward testing and packaging.
- Fix approach: Install in editable mode via `setup.py` / `pyproject.toml` and use normal imports; document `pip install -e .`.

**Configuration docs vs implementation:**
- Issue: `src/config/settings.py` module docstring references Pydantic; implementation uses `@dataclass` and `os.getenv`. `pydantic` is listed in `requirements.txt` but is not the active settings mechanism.
- Files: `src/config/settings.py`, `requirements.txt`
- Impact: Misleading onboarding; unused or underused dependency.
- Fix approach: Align docstring with dataclasses, or migrate settings to Pydantic v2 and drop redundant prose.

**RoBERTa included in ensemble while “disabled”:**
- Issue: `EnsembleAnalyzer.weights["roberta"]` is `0.0`, but `analyze()` still runs `self.roberta_analyzer.analyze()` every time, which loads `roberta-base` and runs inference (`src/analyzers/ensemble_analyzer.py`). UI copy in `ensemble.py` says RoBERTa is disabled, yet `load_analyzer()` forces `_ = analyzer.roberta_analyzer`.
- Files: `src/analyzers/ensemble_analyzer.py`, `ensemble.py`, `src/analyzers/roberta_analyzer.py`
- Impact: Large download, RAM, and latency for no contribution to the weighted score; contradicts user expectations.
- Fix approach: Skip RoBERTa entirely when weight is 0 (no load, no forward pass); optionally lazy-load only when weight > 0.

**Agreement logic uses RoBERTa vote at zero weight:**
- Issue: `_determine_verdict` uses `result.scores[1:]` for `ai_votes` / `agreement`, which includes the RoBERTa row even when its weight is 0. Random/untrained RoBERTa outputs can still move confidence via agreement.
- Files: `src/analyzers/ensemble_analyzer.py`
- Impact: Confidence and narrative (“mixed signals”) can be polluted by a signal explicitly excluded from the blend.
- Fix approach: Only count analyzers with non-zero weight, or omit RoBERTa scores from the list when disabled.

**Fragile score ordering:**
- Issue: Ensemble logic assumes `result.scores[0]` is the combined “Ensemble AI Score” and `scores[1:]` are individuals (`_determine_verdict`, `_generate_ensemble_explanation`, `ensemble.py` comparison table skips index 0 with `result.scores[1:]`).
- Files: `src/analyzers/ensemble_analyzer.py`, `ensemble.py`
- Impact: Reordering or inserting scores breaks verdict math and UI tables silently.
- Fix approach: Address scores by name or enum, not list index.

## Known Bugs

**Example text injection ordering in ensemble empty state:**
- Issue: `ensemble.py` assigns `text_input = st.session_state.pop("text_example")` after the main `elif not text_input` block; Streamlit’s execution model may not repopulate the text area from that assignment in the same run users expect (pattern differs from a `value=` binding). Risk of confusing or ineffective “Use example” flow.
- Files: `ensemble.py`
- Trigger: Click example buttons when the text area is empty.
- Workaround: Paste examples manually.

**NLTK bootstrap may mark success too early:**
- Issue: `TextProcessor.ensure_nltk_data()` sets `_nltk_initialized = True` after the loop even if some `nltk.download` calls failed (failures are only logged).
- Files: `src/utils/text_processing.py`
- Trigger: Offline or blocked download hosts.
- Workaround: Pre-install corpora; run `nltk.download` manually.

## Security Considerations

**Local Streamlit and error surfaces:**
- Risk: `st.error(f"... {str(e)}")` in `app.py`, `ensemble.py`, and `test.py` exposes exception strings to anyone with UI access.
- Files: `app.py`, `ensemble.py`, `test.py`
- Current mitigation: Typical single-user local use.
- Recommendations: Log full trace server-side; show generic messages in UI for production deployments.

**HTML injection via `unsafe_allow_html`:**
- Risk: Verdict and metrics use fixed templates; warnings rendered as `<div class="warning-box">⚠️ {warning}</div>` could inject HTML if a future code path places unsanitized user-controlled text into `result.warnings`.
- Files: `app.py`, `ensemble.py`, `test.py`
- Current mitigation: Warnings are generated internally today.
- Recommendations: Escape user-derived strings before embedding in HTML, or use Streamlit components without raw HTML.

**Model download trust boundary:**
- Risk: `transformers` loads `gpt2`, `gpt2` tokenizer, and `roberta-base` from the Hugging Face Hub on first run (`src/analyzers/gpt2_analyzer.py`, `src/analyzers/roberta_analyzer.py`).
- Files: `src/analyzers/gpt2_analyzer.py`, `src/analyzers/roberta_analyzer.py`
- Current mitigation: Standard ecosystem defaults; cache dir configurable via `GPT2Config.cache_dir` in settings.
- Recommendations: Pin revisions, verify checksums, or vendor weights for high-assurance environments.

**Deployment and DoS:**
- Risk: No authentication, rate limits, or input size caps at the app layer; very long pasted text increases GPU/CPU time for GPT-2 sliding windows (`max_token_length` 1024, stride 512 in `src/config/settings.py`).
- Files: `src/analyzers/gpt2_analyzer.py`, Streamlit entrypoints
- Current mitigation: Documented as local processing.
- Recommendations: Add max character limits and server-side timeouts if exposed beyond localhost.

## Performance Bottlenecks

**Ensemble cold start and RoBERTa:**
- Problem: First load pulls and initializes RoBERTa, GPT-2, and NLTK-backed models despite RoBERTa having zero ensemble weight.
- Files: `ensemble.py`, `src/analyzers/ensemble_analyzer.py`
- Cause: Eager `roberta_analyzer` property access in `load_analyzer()` and unconditional `roberta_analyzer.analyze()` in `analyze()`.
- Improvement path: Gate RoBERTa on weight > 0; defer downloads until needed.

**GPT-2 perplexity sliding window:**
- Problem: `_compute_perplexity_gpt2` iterates with `stride` over full token length—multiple forward passes per request.
- Files: `src/analyzers/gpt2_analyzer.py`
- Cause: Design for long texts vs 1024-token windows.
- Improvement path: Cap analyzed prefix for interactive UI, batch tuning, or GPU-only paths.

**NLTK model rebuild on n-gram change:**
- Problem: `NLTKAnalyzer.model` rebuilds when `ngram_size` changes (`src/analyzers/nltk_analyzer.py`), which is expensive on the Brown corpus.
- Files: `src/analyzers/nltk_analyzer.py`, `app.py` (sidebar selectbox)
- Cause: Cache key includes n-gram in Streamlit but underlying build still runs when cache misses.
- Improvement path: Precompute or persist models per n.

## Fragile Areas

**RoBERTa “AI detection” head:**
- Files: `src/analyzers/roberta_analyzer.py`
- Why fragile: Uses randomly initialized classification head on `roberta-base` (explicit `logger.warning`); logits are not meaningful for AI vs human until fine-tuned.
- Safe modification: Do not increase `weights["roberta"]` until a trained checkpoint is wired via `from_pretrained` to a real detector model.
- Test coverage: `tests/test_roberta_analyzer.py` exists; treat as unit-level only—behavior is not semantically validated against ground truth.

**Ensemble combination constants:**
- Files: `src/analyzers/ensemble_analyzer.py`
- Why fragile: Hard-coded normalization `1 - (perplexity / 500)` for both GPT-2 and NLTK maps different perplexity scales into `[0,1]` the same way.
- Safe modification: Calibrate per analyzer using held-out data; add tests that lock expected ranges.

**Large presentation modules:**
- Files: `app.py` (544 non-empty lines), `test.py` (585), `ensemble.py` (567), `src/utils/visualization.py` (366), `src/utils/text_processing.py` (346), `src/analyzers/gpt2_analyzer.py` (341)
- Why fragile: High line count concentrates UI, CSS, and orchestration without tests.
- Safe modification: Split files first; add regression tests on analyzers and `AnalysisResult` serialization.

## Scaling Limits

**Memory and concurrent users:**
- Current capacity: Documented ~2–3 GB (sidebar in `ensemble.py`) to ~4–6 GB on error path; multiple Torch models in one process.
- Limit: OOM or severe slowdown on CPU with ensemble enabled.
- Scaling path: Separate analyzer services, model choice per tier, or drop RoBERTa entirely until needed.

## Dependencies at Risk

**NumPy major version pin:**
- Risk: `requirements.txt` caps `numpy<2.0.0` while the ecosystem moves toward NumPy 2.x.
- Impact: Future conflicts with newer `torch` / `pandas` wheels.
- Migration plan: Test against NumPy 2.x and relax the upper bound when compatible.

**Pydantic vs dataclass settings:**
- Risk: Two configuration stories (listed Pydantic, implemented dataclasses) complicate dependency justification.
- Impact: Audit noise and possible version drift.
- Migration plan: Pick one approach and document in `docs/API.md` and README.

## Missing Critical Features

**Documented public API vs code:**
- Problem: `docs/API.md` only demonstrates `NLTKAnalyzer`; no sections for `GPT2Analyzer`, `EnsembleAnalyzer`, `RoBERTaAnalyzer`, or Streamlit entrypoints.
- Files: `docs/API.md`
- Blocks: Integrators cannot rely on docs for ensemble or GPT-2 usage without reading source.

**CI pipeline:**
- Problem: No `.github/workflows` (or equivalent) detected in repo root for automated test runs.
- Blocks: Regressions on `tests/` may go unnoticed.

## Test Coverage Gaps

**Streamlit and end-to-end flows:**
- What’s not tested: User clicks, `st.cache_resource` behavior, and chart rendering.
- Files: `app.py`, `ensemble.py`, `test.py`
- Risk: UI-only regressions ship without detection.
- Priority: Medium

**Cross-analyzer calibration:**
- What’s not tested: Whether ensemble weights and perplexity normalization produce stable verdicts on a fixed golden corpus.
- Files: `src/analyzers/ensemble_analyzer.py`
- Risk: Silent accuracy drift when thresholds change.
- Priority: Medium

---

*Concerns audit: 2026-04-02*
