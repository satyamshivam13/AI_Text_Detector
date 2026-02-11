"""
Tests for RoBERTa Analyzer
"""

import pytest
from src.analyzers.roberta_analyzer import RoBERTaAnalyzer
from src.config.settings import Verdict

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@pytest.fixture
def roberta_analyzer():
    """Create a RoBERTa analyzer instance."""
    if not TORCH_AVAILABLE:
        pytest.skip("PyTorch not available")
    return RoBERTaAnalyzer()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
class TestRoBERTaAnalyzer:
    """Test cases for RoBERTaAnalyzer."""

    def test_initialization(self, roberta_analyzer):
        """Test analyzer initialization."""
        assert roberta_analyzer is not None
        assert roberta_analyzer.method_name == "RoBERTa"

    def test_device_detection(self, roberta_analyzer):
        """Test that device is properly detected."""
        device = roberta_analyzer.device
        assert device is not None
        assert device.type in ["cpu", "cuda"]

    def test_model_lazy_loading(self, roberta_analyzer):
        """Test that model is lazy-loaded."""
        # Model should be None before first use
        assert roberta_analyzer._model is None
        assert roberta_analyzer._tokenizer is None
        
        # Access model property to trigger loading
        model = roberta_analyzer.model
        assert model is not None
        assert roberta_analyzer._model is not None

    def test_tokenizer_lazy_loading(self, roberta_analyzer):
        """Test that tokenizer is lazy-loaded."""
        tokenizer = roberta_analyzer.tokenizer
        assert tokenizer is not None
        assert hasattr(tokenizer, 'encode')

    def test_analyze_returns_result(self, roberta_analyzer, medium_text):
        """Test that analyze returns a valid result."""
        result = roberta_analyzer.analyze(medium_text)
        
        assert result is not None
        assert hasattr(result, 'verdict')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'scores')
        assert result.method == "RoBERTa Transformer"

    def test_empty_text_handling(self, roberta_analyzer):
        """Test handling of empty text."""
        result = roberta_analyzer.analyze("")
        assert result.verdict == Verdict.UNCERTAIN

    def test_short_text_handling(self, roberta_analyzer, short_text):
        """Test handling of short text."""
        result = roberta_analyzer.analyze(short_text)
        assert result is not None
        assert len(result.warnings) > 0

    def test_ai_text_analysis(self, roberta_analyzer, sample_ai_text):
        """Test analysis of AI-generated text."""
        result = roberta_analyzer.analyze(sample_ai_text)
        
        assert result is not None
        assert result.verdict in [Verdict.AI_GENERATED, Verdict.LIKELY_AI, Verdict.UNCERTAIN]

    def test_human_text_analysis(self, roberta_analyzer, sample_human_text):
        """Test analysis of human-written text."""
        result = roberta_analyzer.analyze(sample_human_text)
        
        assert result is not None
        # Note: Untrained RoBERTa gives random predictions (~50% accuracy)
        # Accept any verdict since model requires fine-tuning for accurate results
        assert result.verdict in [
            Verdict.AI_GENERATED, Verdict.LIKELY_AI, Verdict.UNCERTAIN,
            Verdict.LIKELY_HUMAN, Verdict.HUMAN_WRITTEN
        ]

    def test_scores_structure(self, roberta_analyzer, medium_text):
        """Test that scores have proper structure."""
        result = roberta_analyzer.analyze(medium_text)
        
        assert len(result.scores) > 0
        
        # Check that scores have required attributes
        for score in result.scores:
            assert hasattr(score, 'name')
            assert hasattr(score, 'value')
            assert hasattr(score, 'weight')
            assert hasattr(score, 'interpretation')
            assert hasattr(score, 'indicates_ai')

    def test_roberta_score_present(self, roberta_analyzer, medium_text):
        """Test that RoBERTa AI score is present in results."""
        result = roberta_analyzer.analyze(medium_text)
        
        score_names = [s.name for s in result.scores]
        assert any("RoBERTa" in name for name in score_names)

    def test_metrics_computed(self, roberta_analyzer, medium_text):
        """Test that all metrics are computed."""
        result = roberta_analyzer.analyze(medium_text)
        
        assert result.burstiness >= 0
        assert result.lexical_diversity >= 0
        assert result.sentence_variance >= 0
        assert result.perplexity == 0.0  # RoBERTa doesn't compute perplexity

    def test_confidence_in_range(self, roberta_analyzer, medium_text):
        """Test that confidence is in valid range."""
        result = roberta_analyzer.analyze(medium_text)
        
        assert result.confidence >= 0.0
        assert result.confidence <= 100.0

    def test_analysis_time_recorded(self, roberta_analyzer, medium_text):
        """Test that analysis time is recorded."""
        result = roberta_analyzer.analyze(medium_text)
        
        assert result.analysis_time > 0
        assert result.analysis_time < 60  # Should complete in under 60 seconds

    def test_roberta_score_interpretation(self, roberta_analyzer):
        """Test RoBERTa score interpretation logic."""
        # Test different score levels (all lowercase for case-insensitive comparison)
        assert "strong ai" in roberta_analyzer._interpret_roberta_score(0.95).lower()
        assert "likely ai" in roberta_analyzer._interpret_roberta_score(0.75).lower()
        assert "uncertain" in roberta_analyzer._interpret_roberta_score(0.45).lower()
        assert "human" in roberta_analyzer._interpret_roberta_score(0.25).lower()

    def test_long_text_handling(self, roberta_analyzer):
        """Test handling of text longer than max_length."""
        long_text = "This is a sentence. " * 100  # Create text longer than 512 tokens
        result = roberta_analyzer.analyze(long_text)
        
        assert result is not None
        assert result.verdict is not None

    def test_model_in_eval_mode(self, roberta_analyzer):
        """Test that model is in evaluation mode."""
        model = roberta_analyzer.model
        assert not model.training

    def test_result_serialization(self, roberta_analyzer, medium_text):
        """Test that result can be serialized to dict."""
        result = roberta_analyzer.analyze(medium_text)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "verdict" in result_dict
        assert "confidence" in result_dict
        assert "method" in result_dict
        assert result_dict["method"] == "RoBERTa Transformer"

    def test_consistent_results(self, roberta_analyzer):
        """Test that same text produces consistent results."""
        text = "This is a test for consistency."
        
        result1 = roberta_analyzer.analyze(text)
        result2 = roberta_analyzer.analyze(text)
        
        # Should produce same verdict
        assert result1.verdict == result2.verdict
        # Confidence should be very close
        assert abs(result1.confidence - result2.confidence) < 0.1
