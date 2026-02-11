# API Documentation

## Overview

The AI Text Detector provides a Python API for detecting AI-generated text. The API is organized into modular components that can be used independently or together.

## Installation

### From Source
```bash
git clone https://github.com/yourusername/ai-text-detector.git
cd ai-text-detector
pip install -e .
```

### From PyPI (when published)
```bash
pip install ai-text-detector
```

## Quick Start

```python
from src.analyzers import NLTKAnalyzer, GPT2Analyzer, EnsembleAnalyzer

# Using NLTK-based analyzer
analyzer = NLTKAnalyzer()
result = analyzer.analyze("Your text here...")
print(f"AI-generated: {result['is_ai_generated']}")
print(f"Confidence: {result['confidence']}")

# Using GPT-2-based analyzer
gpt2_analyzer = GPT2Analyzer()
result = gpt2_analyzer.analyze("Your text here...")

# Using ensemble (combines multiple methods)
ensemble = EnsembleAnalyzer()
result = ensemble.analyze("Your text here...")
```

## API Reference

### Analyzers

#### BaseAnalyzer (Abstract)

Base class for all analyzers.

**Methods:**
- `analyze(text: str) -> Dict[str, Any]`: Analyze text and return detection results
- `get_metrics(text: str) -> Dict[str, float]`: Get raw metrics
- `validate_text(text: str) -> bool`: Validate input text

**Return Format:**
```python
{
    'perplexity': float,
    'burstiness': float,
    'is_ai_generated': bool,
    'confidence': float,  # 0-1
    'details': dict
}
```

#### NLTKAnalyzer

NLTK-based analyzer using n-gram language models.

**Constructor:**
```python
NLTKAnalyzer(n: int = 2)
```

**Parameters:**
- `n` (int): N-gram order (default: 2 for bigrams)

**Example:**
```python
analyzer = NLTKAnalyzer(n=3)  # Use trigrams
result = analyzer.analyze(text)
```

#### GPT2Analyzer

GPT-2 model-based analyzer.

**Constructor:**
```python
GPT2Analyzer(model_name: str = 'gpt2')
```

**Parameters:**
- `model_name` (str): GPT-2 model variant ('gpt2', 'gpt2-medium', 'gpt2-large', 'gpt2-xl')

**Example:**
```python
analyzer = GPT2Analyzer(model_name='gpt2-medium')
result = analyzer.analyze(text)
```

#### EnsembleAnalyzer

Combines multiple analyzers for improved accuracy.

**Constructor:**
```python
EnsembleAnalyzer(analyzers: List[BaseAnalyzer] = None)
```

**Parameters:**
- `analyzers` (List[BaseAnalyzer]): List of analyzers to use (default: NLTK + GPT-2)

**Example:**
```python
from src.analyzers import NLTKAnalyzer, GPT2Analyzer, EnsembleAnalyzer

custom_analyzers = [
    NLTKAnalyzer(n=2),
    NLTKAnalyzer(n=3),
    GPT2Analyzer()
]
ensemble = EnsembleAnalyzer(analyzers=custom_analyzers)
result = ensemble.analyze(text)
```

### Text Processing

#### TextProcessor

Text preprocessing and tokenization.

**Constructor:**
```python
TextProcessor(remove_stopwords: bool = True, remove_punctuation: bool = True)
```

**Methods:**
- `tokenize(text: str) -> List[str]`: Tokenize text
- `preprocess(text: str) -> List[str]`: Full preprocessing pipeline
- `clean_text(text: str) -> str`: Clean text
- `get_word_frequency(text: str) -> dict`: Get word frequencies
- `get_most_common(text: str, n: int = 10) -> List[tuple]`: Get most common words

**Example:**
```python
from src.preprocessing import TextProcessor

processor = TextProcessor(remove_stopwords=True)
tokens = processor.preprocess(text)
freq = processor.get_word_frequency(text)
common = processor.get_most_common(text, n=10)
```

### Models

#### NGramModel

N-gram language model.

**Constructor:**
```python
NGramModel(n: int = 2)
```

**Methods:**
- `get_model()`: Get trained model
- `score(word: str, context: tuple) -> float`: Score word given context

#### PerplexityCalculator

Calculate various text metrics.

**Static Methods:**
- `calculate_nltk_perplexity(tokens, model, n) -> float`
- `calculate_burstiness(tokens) -> float`
- `calculate_repetition_score(tokens) -> float`
- `calculate_entropy(tokens) -> float`

**Example:**
```python
from src.models import PerplexityCalculator

calc = PerplexityCalculator()
burstiness = calc.calculate_burstiness(tokens)
entropy = calc.calculate_entropy(tokens)
```

### Utilities

#### TextValidator

Input validation.

**Static Methods:**
- `validate_text(text) -> Tuple[bool, Optional[str]]`
- `sanitize_text(text) -> str`
- `validate_ngram_order(n) -> Tuple[bool, Optional[str]]`
- `validate_confidence(confidence) -> Tuple[bool, Optional[str]]`

**Example:**
```python
from src.utils import TextValidator

is_valid, error = TextValidator.validate_text(text)
if not is_valid:
    print(f"Validation failed: {error}")

clean_text = TextValidator.sanitize_text(text)
```

#### Config

Application configuration.

**Class Attributes:**
- `DEFAULT_NGRAM_ORDER`: Default n-gram order
- `DEFAULT_GPT2_MODEL`: Default GPT-2 model
- `NLTK_PERPLEXITY_THRESHOLD`: Threshold for NLTK analyzer
- `GPT2_PERPLEXITY_THRESHOLD`: Threshold for GPT-2 analyzer
- `MIN_TEXT_LENGTH`: Minimum text length
- `MAX_TEXT_LENGTH`: Maximum text length

**Methods:**
- `get_config() -> Dict`: Get all configuration
- `update_config(**kwargs)`: Update configuration
- `from_env()`: Load from environment variables

**Example:**
```python
from src.utils import Config

# Update configuration
Config.update_config(MIN_TEXT_LENGTH=20)

# Get all config
config = Config.get_config()
```

### Visualization

#### ChartGenerator

Generate charts and visualizations.

**Static Methods:**
- `plot_word_frequency_bar(word_freq, title, use_plotly)`
- `plot_metrics_gauge(confidence, title)`
- `plot_metrics_comparison(metrics)`
- `plot_analyzer_comparison(individual_results)`
- `plot_text_statistics(stats)`

**Example:**
```python
from src.visualization import ChartGenerator

# In Streamlit app
generator = ChartGenerator()
generator.plot_metrics_gauge(result['confidence'])
generator.plot_word_frequency_bar(word_freq)
```

## Error Handling

All analyzers raise `ValueError` for invalid input:

```python
try:
    result = analyzer.analyze(text)
except ValueError as e:
    print(f"Invalid input: {e}")
```

## Configuration via Environment Variables

```bash
export LOG_LEVEL=DEBUG
export NGRAM_ORDER=3
export GPT2_MODEL=gpt2-medium
export MIN_TEXT_LENGTH=20
export MAX_TEXT_LENGTH=100000
```

## Best Practices

1. **Text Length**: Provide at least 50-100 words for reliable results
2. **Ensemble**: Use EnsembleAnalyzer for best accuracy
3. **Validation**: Always validate input before analysis
4. **Caching**: Results can be cached for identical inputs
5. **Error Handling**: Always wrap analysis in try-except blocks

## Performance Considerations

- **NLTK Analyzer**: Fast, suitable for real-time analysis
- **GPT-2 Analyzer**: Slower, more accurate for longer texts
- **Ensemble**: Best accuracy but slower (combines both)

For best performance:
- Use NLTK for quick checks (< 50ms)
- Use GPT-2 for detailed analysis (1-5 seconds)
- Use Ensemble when accuracy is critical (2-10 seconds)
