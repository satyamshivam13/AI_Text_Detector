.PHONY: help install install-dev run-nltk run-gpt2 test lint format clean docker-build docker-run

PYTHON := python3
PIP := pip
STREAMLIT := streamlit

help: ## Show this help message
	@echo "AI Text Detector - Available Commands:"
	@echo "======================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON) -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'stopwords', 'brown'])"

install-dev: ## Install development dependencies
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	$(PYTHON) -c "import nltk; nltk.download(['punkt', 'punkt_tab', 'stopwords', 'brown'])"

run-nltk: ## Run NLTK-based detector
	PYTHONPATH=src $(STREAMLIT) run app.py

run-gpt2: ## Run GPT-2-based detector
	PYTHONPATH=src $(STREAMLIT) run test.py

run-ensemble: ## Run Ensemble detector (RoBERTa+GPT2+NLTK)
	PYTHONPATH=src $(STREAMLIT) run ensemble.py

test: ## Run tests with coverage
	PYTHONPATH=src $(PYTHON) -m pytest tests/ -v --cov=src --cov-report=html --cov-report=term-missing

lint: ## Run linters
	flake8 src/ tests/ app.py test.py ensemble.py --max-line-length=100
	mypy src/ --ignore-missing-imports
	pylint src/ --disable=C0114,C0115,C0116

format: ## Format code
	black src/ tests/ app.py test.py ensemble.py --line-length=100
	isort src/ tests/ app.py test.py ensemble.py --profile=black

clean: ## Clean build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache .coverage htmlcov dist build *.egg-info

docker-build: ## Build Docker image
	docker build -t ai-text-detector:latest .

docker-run: ## Run Docker container
	docker run -p 8501:8501 --name ai-detector ai-text-detector:latest

docker-compose-up: ## Start all services with Docker Compose
	docker-compose up -d --build

docker-compose-down: ## Stop all services
	docker-compose down