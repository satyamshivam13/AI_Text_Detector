"""
Tests for GPT-2-based analyzer.

Note: These tests require the GPT-2 model to be downloaded.
Mark tests with @pytest.mark.slow for CI/CD filtering.
"""

import pytest
from src.analyzers.gpt2_analyzer import GPT2Analyzer
from src.config.settings import Verdict


# Skip all tests in this module if torch is not available or in CI
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

pytestmark = pytest.mark.skipif(
    not HAS_TORCH,
    reason="PyTorch not available"
)


class TestGPT2AnalyzerInit:
    """Tests for GPT-2 analyzer initialization."""

    def test_creation(self):
        analyzer = GPT2Analyzer()
        assert analyzer.method_name == "GPT-2 Deep Analysis"

    def test_device_detection(self):
        analyzer = GPT2Analyzer()
        device = analyzer.device
        assert device is not None
        assert device.type in ("cpu", "cuda")


@pytest.mark.slow
class TestGPT2Analysis:
    """Tests for GPT-2 analysis (requires model download)."""

    @pytest.fixture(autouse=True)
    def setup_analyzer(self):
        self.analyzer = GPT2Analyzer()

    def test_analyze_returns_result(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result is not None
        assert result.verdict in list(Verdict)

    def test_analyze_sets_method(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert "GPT-2" in result.method

    def test_analyze_computes_perplexity(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.perplexity > 0

    def test_analyze_empty_text(self, empty_text):
        result = self.analyzer.analyze(empty_text)
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0

    def test_analyze_has_scores(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert len(result.scores) >= 4
        score_names = [s.name for s in result.scores]
        assert "GPT-2 Perplexity" in score_names

    def test_analyze_confidence_range(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert 0.0 <= result.confidence <= 100.0

    def test_analyze_records_time(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.analysis_time > 0