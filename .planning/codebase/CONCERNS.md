# Concerns

**Analysis Date:** 2026-07-06

> Context: a large audit-remediation (PR #2) was merged, so most previously-
> documented concerns are **resolved** (MLE→smoothed NLTK, ensemble calibration/
> AI-bias, RoBERTa gating, CI, safetensors, dead deps, UI dedup, input cap,
> error-leakage, `test.py`→`gpt2_app.py`). The items below are what **remains**,
> verified against `main`.

## Validation / ML Credibility (highest priority)

- **No large-benchmark evaluation.** The bundled set is **24 in-distribution
  samples** (`data/benchmark/samples.jsonl`); its perfect scores (AUROC/FPR 0.000)
  are calibration/regression signals, **not** an accuracy claim. No RAID/HC3 run
  exists. The `benchmark.py --dataset` harness is ready; this is the top gap.
- **RoBERTa slot untrained/disabled.** `roberta-base` has a random classification
  head; kept at weight 0. Needs a fine-tuned checkpoint before enabling.
- **Brown-corpus NLTK signal is weak** (1961 corpus; measured AUROC ~0.41
  standalone). Intentionally carries only 0.25 ensemble weight; GPT-2 dominates.

## Fragile Areas

- **Positional `scores[0]` access** in `src/analyzers/ensemble_analyzer.py`
  (2 uses) and `src/analyzers/binoculars_analyzer.py` (1 use). The "index 0 =
  primary score" contract is documented but not enforced — reordering score
  additions would silently break verdict math. Fix: address scores by name.
- **Ensemble weights must sum to 1** by convention; enabling Binoculars/RoBERTa
  requires manual rebalancing. Mitigated by a `[0,1]` clamp on the fused score,
  but no auto-normalization.

## Security / Supply Chain

- **Model Hub revisions default to `None`** (`GPT2Config`, `RoBERTaConfig`,
  `BinocularsConfig`). `use_safetensors=True` mitigates pickle RCE, but weights
  are not pinned to a commit unless a `revision` is set — reproducibility/supply-
  chain gap for high-assurance use.
- **No auth / rate limiting** on the Streamlit apps (documented as local-use).
  Input is capped (50k chars) and errors are generic, so the main residual risk
  is running an app on an untrusted network without a reverse proxy.

## Dependencies / Build

- **`numpy<2.0` pin** (`requirements.txt`) is aging vs the ecosystem.
- **Dockerfile base `python:3.9-slim`** is old relative to the new floors
  (`torch>=2.6`, `transformers>=4.48`); bump to 3.11 recommended.

## CI / Tooling Gaps

- **mypy** documented but **not run in CI**.
- **No coverage gate** (`--cov-fail-under` unset) — 92% can erode silently.
- **Slow model tests never run in CI** (no scheduled full-suite job), so
  transformer compute paths are only verified locally.

## Packaging

- Entry scripts use `sys.path.insert(0, ".../src")`; **no `pyproject.toml`** and
  no editable install. Documented as an invariant (`CLAUDE.md`), but blocks clean
  packaging/distribution.

## Documentation Drift

- **`CLAUDE.md` (repo root) is stale** and has an uncommitted local edit: still
  references `test.py`, 65/35 ensemble weights, and "Pydantic" settings. It is
  read by agents as source-of-truth — regenerate (this map refresh is a step).
- `.planning/codebase/` (this folder) was just refreshed to match post-merge
  reality.

## Missing Portfolio/Product Features (from audit roadmap)

- No Hugging Face Spaces demo, no screenshots/GIF in README, no `examples/`,
  no model card, no CODEOWNERS, no `.pre-commit-config.yaml` (pre-commit is in
  dev deps but unconfigured), empty repo description, no `v2.0.0` release/tag.
- Longer-term: REST API, batch/PDF-DOCX input, export formats, paraphrase/
  humanizer-attack robustness testing, per-language calibration.
