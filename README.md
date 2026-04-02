# AI Text Detector

A local, explainable toolkit for estimating how likely text is machine-generated using NLTK statistics, GPT-2 perplexity, and an optional ensemble mode.

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
git clone https://github.com/yourusername/AI_Text_Detector.git
cd AI_Text_Detector
python -m venv venv
source venv/bin/activate  # Windows PowerShell: .\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'stopwords', 'brown'])"
```

## Run Modes

```bash
streamlit run app.py
streamlit run test.py
streamlit run ensemble.py
```

- app.py: NLTK analyzer UI
- test.py: GPT-2 analyzer UI
- ensemble.py: ensemble analyzer UI

## Testing and Quality Gate

Primary quality gate:

```bash
make test
```

Windows-safe equivalent:

```powershell
$env:PYTHONPATH='src'; C:/Users/Asus/AppData/Local/Programs/Python/Python310/python.exe -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing
```

Optional slow-model verification only:

```bash
pytest -m slow -v
```

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

## Limitations and Ethics

- Results are probabilistic and not certainty claims.
- The toolkit is optimized for English text; results for other languages may be less reliable.
- Output should never be used as sole evidence of authorship.
- Use results as one signal alongside human review and context.

## Documentation

- API reference: docs/API.md
- Deployment guide: docs/DEPLOYMENT.md
