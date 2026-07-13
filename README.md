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

This project ships **three independent Streamlit apps** — one per detection engine. Run whichever one matches your needs (they do not run together). The automated tests live in `tests/` (see [Testing and Quality Gate](#testing-and-quality-gate)).

| Mode | Entry file | Launch command | Purpose | Intended user | Speed¹ | Memory |
|------|-----------|----------------|---------|---------------|--------|--------|
| **NLTK** | `app.py` | `streamlit run app.py` | Statistical detection via NLTK n-gram language models (Brown corpus). No deep-learning model download. | Quick checks; low-resource machines; default starting point | `<1s` | `<1 GB` |
| **GPT-2** | `gpt2_app.py` | `streamlit run gpt2_app.py` | Perplexity-based detection using the GPT-2 transformer. | Users wanting a deep-learning signal | `2–5s` | `2–3 GB` |
| **Ensemble** | `ensemble.py` | `streamlit run ensemble.py` | Verdict is **Binoculars-driven by default** (the fairest signal); GPT-2/NLTK sub-scores are shown but weight 0. | Multi-signal view with a fair default verdict | `5–10s` | `2–3 GB` |

¹ Per-analysis time after models are loaded. The first run is slower: the NLTK mode builds its n-gram model from the Brown corpus, and the GPT-2/Ensemble modes download model weights on first launch (cached thereafter).

**Not sure which to use?** Start with `app.py` (NLTK) — it is the lightest and needs no model download.

### Binoculars (cross-perplexity) — the most accurate analyzer

A two-model detector (`gpt2` + `distilgpt2`) after Hans et al., 2024. It scores
text by the ratio of an observer model's log-perplexity to the observer/performer
cross-perplexity, which cancels the prompt/topic bias that makes single-model
perplexity brittle. **On real human-vs-ChatGPT text (HC3) it scores accuracy
1.000 with FPR 0.000**, with its decision boundary fitted on a held-out split.
See [docs/benchmarks/](docs/benchmarks/).

It is available standalone and via the benchmark CLI (`--analyzer binoculars`);
it is **not** in the default ensemble (it needs a second model). To fuse it, give
`EnsembleConfig.weight_binoculars` a non-zero weight and rebalance.

```python
from src.analyzers.binoculars_analyzer import BinocularsAnalyzer
result = BinocularsAnalyzer().analyze("Your text here")
```

## Testing and Quality Gate

These commands are portable and behave identically on Windows (PowerShell or cmd), Linux, and macOS. `tests/conftest.py` adds `src/` to the path, so no `PYTHONPATH` setup is required.

Primary quality gate (tests with coverage):

```bash
python -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

Linters and formatters:

```bash
python -m flake8 src/ tests/ app.py gpt2_app.py ensemble.py --max-line-length=100
python -m black src/ tests/ app.py gpt2_app.py ensemble.py --line-length=100 --check
python -m isort src/ tests/ app.py gpt2_app.py ensemble.py --profile=black --check-only
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
on faith. Reproduce it yourself against **real human text vs real ChatGPT output**
(the public HC3 corpus):

```bash
python scripts/prepare_hc3.py                    # downloads + samples HC3
python -m src.evaluation.benchmark --analyzer binoculars \
    --dataset data/external/hc3_sample.jsonl
```

**Measured on HC3 (n=200, balanced):**

| Analyzer | Accuracy | AUROC | **FPR** (human flagged AI) |
|----------|---------:|------:|---------------------------:|
| **Binoculars** | **1.000** | 1.000 | **0.000** |
| Ensemble (GPT-2 + NLTK) | 0.950 | 0.998 | 0.100 |
| GPT-2 alone | 0.750 | 0.756 | **0.500** |
| NLTK alone | 0.500 | 0.420 | 0.000 |

**Use Binoculars.** GPT-2 alone flags *half of real human text as AI* — single-model
perplexity is as brittle as the literature says. Full report, plots, and the
held-out calibration procedure: [docs/benchmarks/](docs/benchmarks/).

### ⚠️ Fairness — false-positive rate by population (human-only)

The number that matters ethically is not overall accuracy, it is who gets falsely
accused. Measured on 785 **human-authored** samples (any flag is a false positive):

| Population | **Binoculars** | GPT-2 | Ensemble |
|-----------|---------------:|------:|---------:|
| **Non-native English writers (TOEFL)** | **5.5%** | 26.4% | **71.4%** |
| Native-speaker student essays | 0.0% | ~1% | 10–24% |
| Overall (human) | **1.0%** | 13.5% | 27.1% |

- **GPT-2 reproduces [Liang et al. 2023](https://github.com/Weixin-Liang/ChatGPT-Detector-Bias):**
  non-native writers are flagged ~26× more than native writers.
- **A GPT-2-weighted ensemble was the *worst*** — 71% of non-native writers — because
  it inherited GPT-2's bias. **The default ensemble verdict is now Binoculars-driven**
  (GPT-2/NLTK weight 0), so it inherits Binoculars' fairness instead; the table's
  "Ensemble" column above reflects the old GPT-2-weighted blend, kept as a warning.
- **Binoculars is the fairest** (the cross-perplexity ratio cancels the effect),
  but still not perfect: 5.5% for non-native writers vs 0% for native speakers.

**Do not use any analyzer here to accuse a specific person.** Full breakdown with
confidence intervals: [docs/benchmarks/FAIRNESS.md](docs/benchmarks/FAIRNESS.md).

> ⚠️ **Limits of these numbers.** HC3 is ChatGPT-era output; edited, paraphrased,
> and human/AI-mixed text are harder and unmeasured. 200 samples means wide
> confidence intervals. There is no evaluation on adversarial "humanizer" attacks,
> non-English text, or human sub-populations (ESL writers, students) where false
> positives do real harm. The bundled `data/benchmark/` set is a **pipeline
> regression fixture only** — its "AI" samples are hand-written imitations, not
> model output, so its scores are not accuracy.

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
