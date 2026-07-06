# Contributing to AI Text Detector

Thanks for your interest in improving this project. It aims to be a
**transparent, explainable, local** AI-text-likelihood toolkit — contributions
that strengthen that mission (better calibration, clearer explanations, honest
evaluation) are especially welcome.

## Development setup

```bash
git clone https://github.com/satyamshivam13/AI_Text_Detector.git
cd AI_Text_Detector
python -m venv venv
# Linux/macOS: source venv/bin/activate
# Windows PowerShell: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
python -c "import nltk; nltk.download(['punkt','punkt_tab','stopwords','brown','averaged_perceptron_tagger'])"
```

## Quality gate (run before every PR)

These mirror the CI checks in `.github/workflows/ci.yml`:

```bash
python -m pytest tests/ -m "not slow" -q          # tests
python -m flake8 src/ tests/ app.py gpt2_app.py ensemble.py --max-line-length=100
python -m black --check --line-length=100 src/ tests/ app.py gpt2_app.py ensemble.py
python -m isort --check-only --profile=black src/ tests/ app.py gpt2_app.py ensemble.py
```

Auto-format with `python -m black ... --line-length=100` and
`python -m isort ... --profile=black` (no `--check`).

## Architecture invariants

Before changing code, read the local `AGENTS.md` in the subdirectory you are
touching. Key invariants:

- All analysis flows through `analyzer.analyze(text) -> AnalysisResult`. Never
  call `_perform_analysis` directly.
- `AnalysisResult`, `TextMetrics`, `DetectionScore` are plain dataclasses.
- `get_settings()` is the single cached settings entry point; never instantiate
  `Settings()` directly.
- Subclasses use `self.thresholds` — never hardcode threshold values.
- Transformer analyzers are lazily imported so `app.py` runs without `torch`.
- On any analysis failure: set `Verdict.UNCERTAIN`, zero confidence, append a
  warning — never let exceptions reach the UI.

## Changing detection behaviour

If you change thresholds, smoothing, calibration, or fusion weights, **re-run
the benchmark and include the numbers** in your PR:

```bash
python -m src.evaluation.benchmark --analyzer ensemble
```

New calibration must not regress the false-positive rate on human text.

## Commit and PR style

- Small, focused commits with a clear subject line (`area: summary`).
- Reference the audit finding or issue where relevant.
- Describe what you changed, why, and how you validated it.

## Reporting bugs / requesting features

Use the issue templates under `.github/ISSUE_TEMPLATE/`.
