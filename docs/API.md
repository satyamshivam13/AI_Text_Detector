# API Documentation

## Analyzer Usage

All analyzers expose the same call pattern:

```python
result = analyzer.analyze(text)
```

Each call returns an AnalysisResult object with a stable programmatic contract.

### NLTKAnalyzer

```python
from src.analyzers.nltk_analyzer import NLTKAnalyzer

analyzer = NLTKAnalyzer(ngram_size=3)
result = analyzer.analyze("Your text here...")

print(result.verdict)
print(result.confidence)
print(result.perplexity)
print(result.analysis_time)
```

### GPT2Analyzer

```python
from src.analyzers.gpt2_analyzer import GPT2Analyzer

analyzer = GPT2Analyzer()
result = analyzer.analyze("Your text here...")

print(result.verdict)
print(result.confidence_level)
print(result.perplexity)
print(result.warnings)
```

### EnsembleAnalyzer

```python
from src.analyzers.ensemble_analyzer import EnsembleAnalyzer

analyzer = EnsembleAnalyzer()
result = analyzer.analyze("Your text here...")

print(result.verdict)
print(result.confidence)
print(result.scores[0].name)
print(result.explanation)
```

Default ensemble weights:
- RoBERTa: 0.0 (disabled by default)
- GPT-2: 0.65
- NLTK: 0.35

Weighted fusion formula:

```text
ensemble_ai_score = sum(weight_i * ai_score_i)
```

Where GPT-2 and NLTK AI scores are derived from normalized perplexity:

```text
ai_score = max(0, min(1, 1 - (perplexity / 500)))
```

## AnalysisResult Contract

Use AnalysisResult.to_dict() for API-safe serialization:

```python
payload = result.to_dict()
```

Contract fields in the serialized result include:
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

metrics contains text statistics (word/sentence counts and lexical diversity), and
scores contains detailed per-signal entries (name, value, weight, interpretation,
indicates_ai) for transparent analysis output.
