# API Documentation

## Analyzer Call Pattern

All analyzers expose the same call pattern:

```python
result = analyzer.analyze(text)
```

Each call returns an AnalysisResult instance.

## Analyzer Modules

### NLTKAnalyzer

```python
from src.analyzers.nltk_analyzer import NLTKAnalyzer

analyzer = NLTKAnalyzer(ngram_size=3)
result = analyzer.analyze("Your text here")
```

### GPT2Analyzer

```python
from src.analyzers.gpt2_analyzer import GPT2Analyzer

analyzer = GPT2Analyzer()
result = analyzer.analyze("Your text here")
```

### EnsembleAnalyzer

```python
from src.analyzers.ensemble_analyzer import EnsembleAnalyzer

analyzer = EnsembleAnalyzer()
result = analyzer.analyze("Your text here")
```

Default ensemble weights in current implementation:

- RoBERTa: 0.0 (disabled by default)
- GPT-2: 0.65
- NLTK: 0.35

## AnalysisResult Contract

AnalysisResult is defined in src/models/result.py and serializes through to_dict() and to_json().

### Core fields

- verdict
- confidence
- confidence_level
- method
- analysis_time
- timestamp
- text_length
- warnings
- explanation

### Score and metric fields

- perplexity
- burstiness
- lexical_diversity
- sentence_variance
- metrics (TextMetrics payload)
- scores (list of DetectionScore payloads)

### Serialization example

```python
payload = result.to_dict()
```

Serialized keys include:

- verdict
- confidence
- confidence_level
- perplexity
- burstiness
- lexical_diversity
- sentence_variance
- method
- analysis_time
- timestamp
- text_length
- warnings
- explanation
- metrics
- scores

## Ensemble Calibration

Each backend contributes a **calibrated AI-probability** in `[0, 1]`; the
ensemble is their weighted average. Perplexity is mapped with a per-analyzer
logistic (`src/analyzers/calibration.py`) whose midpoint is the decision
boundary. Parameters live in `EnsembleConfig`:

```python
from src.config.settings import get_settings

cfg = get_settings().ensemble
cfg.gpt2_ppl_midpoint   # 30.0  (GPT-2: lower perplexity => more AI)
cfg.nltk_ppl_midpoint   # 1550  (Brown NLTK: higher perplexity => more AI)
cfg.weight_gpt2         # 0.75
cfg.weight_nltk         # 0.25
cfg.weight_roberta      # 0.0   (disabled: not loaded or run)
cfg.weight_binoculars   # 0.0   (optional; not loaded unless > 0)
```

To fuse the Binoculars cross-perplexity signal into the ensemble, give it a
non-zero `weight_binoculars` and rebalance the other weights so they sum to 1.
It is off by default because it needs a second model; when enabled it is loaded
lazily and contributes a "Binoculars Score" row.

NLTK smoothing is configurable via `NLTKConfig.smoothing_method`
(`wittenbell` default, `kneserney`, `lidstone`).

## Evaluation API

`src/evaluation/` provides the measurement layer.

```python
from src.evaluation.dataset import load_dataset
from src.evaluation.benchmark import run_benchmark
from src.analyzers.nltk_analyzer import NLTKAnalyzer

samples = load_dataset()                       # bundled labelled corpus
result = run_benchmark(NLTKAnalyzer(), samples, analyzer_name="nltk")
print(result.report_default.to_dict())         # accuracy, F1, AUROC, FPR, FNR, ECE
```

Metrics are also usable directly:

```python
from src.evaluation import metrics
rep = metrics.binary_report(labels, scores, threshold=0.5)  # labels: 0=human,1=AI
auc = metrics.roc_auc(labels, scores)
ece = metrics.expected_calibration_error(labels, scores)
```

CLI:

```bash
python -m src.evaluation.benchmark --analyzer {nltk,gpt2,ensemble} \
    --dataset path/to/data.jsonl --output report.json --plots out/
```

## Notes

- Empty or invalid text is handled with warnings and an UNCERTAIN verdict.
- Consumers should treat scores as probabilistic signals, not proof of authorship.
