# AI Text Detector

![CI](https://github.com/satyamshivam13/AI_Text_Detector/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Code style](https://img.shields.io/badge/code%20style-black-000000)

A local, explainable toolkit for estimating how likely text is machine-generated using NLTK statistics, GPT-2 perplexity, and an optional ensemble mode. It reports a **verdict, confidence, per-signal metrics, and a narrative explanation** — not a single opaque score — and is honest about its limits.

## Features

- Multiple analyzers: NLTK, GPT-2, and ensemble
- Structured output contract via AnalysisResult
- Streamlit entrypoints for each mode
- Local-first processing with no required external API calls
- Quality-gate command for deterministic regression checks

## Quick Start

### Prerequisites

- Python 3.8+
- Recommended RAM:
  - NLTK mode: about 1 GB
  - GPT-2 and ensemble modes: 2-6 GB

### Install

```bash
git clone https://github.com/satyamshivam13/AI_Text_Detector.git
cd AI_Text_Detector
python -m venv venv
# Activate the virtual environment:
#   Linux / macOS:        source venv/bin/activate
#   Windows (PowerShell): .\venv\Scripts\Activate.ps1
#   Windows (cmd):        venv\Scripts\activate.bat
source venv/bin/activate
pip install -r requirements.txt
python -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'stopwords', 'brown'])"
```

## Application Modes

This project ships **three independent Streamlit apps** — one per detection engine. Run whichever one matches your needs (they do not run together).

> ⚠️ **Note on `test.py`:** despite its name, `test.py` is **not** a test suite — it is the GPT-2 application. The automated tests live in `tests/` (see [Testing and Quality Gate](#testing-and-quality-gate)).

| Mode | Entry file | Launch command | Purpose | Intended user | Speed¹ | Memory |
|------|-----------|----------------|---------|---------------|--------|--------|
| **NLTK** | `app.py` | `streamlit run app.py` | Statistical detection via NLTK n-gram language models (Brown corpus). No deep-learning model download. | Quick checks; low-resource machines; default starting point | `<1s` | `<1 GB` |
| **GPT-2** | `test.py` | `streamlit run test.py` | Perplexity-based detection using the GPT-2 transformer. | Users wanting a deep-learning signal | `2–5s` | `2–3 GB` |
| **Ensemble** | `ensemble.py` | `streamlit run ensemble.py` | Weighted fusion of GPT-2 + NLTK signals into one verdict (RoBERTa is present but disabled — it is not fine-tuned). | Users wanting the most robust multi-signal verdict | `5–10s` | `2–3 GB` |

¹ Per-analysis time after models are loaded. The first run is slower: the NLTK mode builds its n-gram model from the Brown corpus, and the GPT-2/Ensemble modes download model weights on first launch (cached thereafter).

**Not sure which to use?** Start with `app.py` (NLTK) — it is the lightest and needs no model download.

## Testing and Quality Gate

These commands are portable and behave identically on Windows (PowerShell or cmd), Linux, and macOS. `tests/conftest.py` adds `src/` to the path, so no `PYTHONPATH` setup is required.

Primary quality gate (tests with coverage):

```bash
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

Linters and formatters:

```bash
python -m flake8 src/ tests/ app.py test.py ensemble.py --max-line-length=100
python -m black src/ tests/ app.py test.py ensemble.py --line-length=100 --check
python -m isort src/ tests/ app.py test.py ensemble.py --profile=black --check-only
python -m mypy src/ --ignore-missing-imports
```

Optional slow-model verification only:

```bash
python -m pytest -m slow -v
```

On Linux/macOS with `make` installed, the `Makefile` wraps these as convenience targets (`make test`, `make lint`, `make format`). `make` is not available on Windows by default, so use the `python -m ...` commands above there.

## Docker and Compose

```bash
docker build -t ai-text-detector:latest .
docker run -p 8501:8501 ai-text-detector:latest

docker-compose up nltk-detector
docker-compose up gpt2-detector
docker-compose up ensemble-detector
```

## Programmatic Usage

```python
from src.analyzers.nltk_analyzer import NLTKAnalyzer

analyzer = NLTKAnalyzer(ngram_size=3)
result = analyzer.analyze("Your text here")
print(result.to_dict())
```

## Accuracy and Evaluation

This project ships a real evaluation layer instead of asking you to take accuracy
on faith. Run it yourself:

```bash
python -m src.evaluation.benchmark --analyzer ensemble --plots out/
```

On the small bundled benchmark (`data/benchmark/`), the **calibrated ensemble**
scores Accuracy/F1/AUROC 1.000 with a **false-positive rate of 0.000** (human
text is not flagged as AI). See [docs/benchmarks/](docs/benchmarks/) for the full
report and ROC/calibration plots.

> ⚠️ Those numbers are on a small, in-distribution set — a regression/calibration
> check, **not** an authoritative accuracy claim. Real-world text (edited,
> paraphrased, mixed, ESL, technical) is much harder. Evaluate on a large public
> benchmark (RAID, HC3) via `--dataset` before making any external claim. The
> NLTK-only signal, in particular, is weak (Brown corpus, 1961) and carries a
> small ensemble weight for that reason.

## Limitations and Ethics

- Results are probabilistic and not certainty claims.
- The toolkit is optimized for English text; results for other languages may be less reliable.
- Output should never be used as sole evidence of authorship.
- Use results as one signal alongside human review and context.

## Contributing and Security

- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- Security policy: [SECURITY.md](SECURITY.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)

## Documentation

- API reference: [docs/API.md](docs/API.md)
- Benchmarks: [docs/benchmarks/](docs/benchmarks/)
- Deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
