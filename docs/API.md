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

## Notes

- Empty or invalid text is handled with warnings and an UNCERTAIN verdict.
- Consumers should treat scores as probabilistic signals, not proof of authorship.
