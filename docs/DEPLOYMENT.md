# Deployment Guide

## Overview

This guide documents deployment paths that match current repository artifacts:

- Local Streamlit execution
- Docker image execution
- Docker Compose service execution
- Procfile-based web command (Heroku-style process managers)

## Local Deployment

### Prerequisites

- Python 3.8+
- pip
- virtual environment recommended

### Steps

```bash
git clone https://github.com/yourusername/AI_Text_Detector.git
cd AI_Text_Detector
python -m venv venv
source venv/bin/activate  # Windows PowerShell: .\\venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
python -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'stopwords', 'brown'])"
```

Run one Streamlit entrypoint:

```bash
streamlit run app.py
streamlit run test.py
streamlit run ensemble.py
```

## Docker Deployment

Current Dockerfile behavior:

- Base image: python:3.9-slim
- ENTRYPOINT: streamlit run
- Default CMD: app.py
- Exposed port: 8501

### Build and run

```bash
docker build -t ai-text-detector:latest .
docker run -p 8501:8501 ai-text-detector:latest
```

To run a non-default entrypoint script:

```bash
docker run -p 8501:8501 ai-text-detector:latest test.py
docker run -p 8501:8501 ai-text-detector:latest ensemble.py
```

## Docker Compose Deployment

Current compose services in docker-compose.yml:

- nltk-detector (port 8501 -> app.py)
- gpt2-detector (port 8502 -> test.py)
- ensemble-detector (port 8503 -> ensemble.py)

### Commands

```bash
docker-compose up nltk-detector
docker-compose up gpt2-detector
docker-compose up ensemble-detector
```

Bring all services down:

```bash
docker-compose down
```

## Procfile Command

Procfile currently defines:

```text
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

Use this command pattern for process-manager deployment where PORT is injected.

## Verification

After deployment, confirm Streamlit health endpoint:

```bash
curl http://localhost:8501/_stcore/health
```

Expected response contains an OK status payload.
