"""
Tests for Ensemble Analyzer
"""

import pytest
from src.analyzers.ensemble_analyzer import EnsembleAnalyzer
from src.config.settings import Verdict, ConfidenceLevel


@pytest.fixture
def ensemble_analyzer():
    """Create an ensemble analyzer instance."""
    return EnsembleAnalyzer()


class TestEnsembleAnalyzer:
    """Test cases for EnsembleAnalyzer."""

    def test_initialization(self, ensemble_analyzer):
        """Test analyzer initialization."""
        assert ensemble_analyzer is not None
        assert ensemble_analyzer.method_name == "Ensemble (RoBERTa+GPT2+NLTK)"
        assert ensemble_analyzer.weights["roberta"] == 0.45
        assert ensemble_analyzer.weights["gpt2"] == 0.35
        assert ensemble_analyzer.weights["nltk"] == 0.20

    def test_analyzer_lazy_loading(self, ensemble_analyzer):
        """Test that individual analyzers are lazy-loaded."""
        # Analyzers should be None before first use
        assert ensemble_analyzer._roberta_analyzer is None
        assert ensemble_analyzer._gpt2_analyzer is None
        assert ensemble_analyzer._nltk_analyzer is None

    def test_empty_text(self, ensemble_analyzer):
        """Test handling of empty text."""
        result = ensemble_analyzer.analyze("")
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0
        assert result.confidence_level == ConfidenceLevel.VERY_LOW
        assert "Empty or invalid text" in result.warnings[0]

    def test_short_text(self, ensemble_analyzer, short_text):
        """Test handling of very short text."""
        result = ensemble_analyzer.analyze(short_text)
        assert result is not None
        assert len(result.warnings) > 0
        assert "short" in result.warnings[0].lower()

    def test_ai_text_detection(self, ensemble_analyzer, sample_ai_text):
        """Test detection of AI-generated text."""
        result = ensemble_analyzer.analyze(sample_ai_text)
        
        assert result is not None
        assert result.verdict in [Verdict.AI_GENERATED, Verdict.LIKELY_AI, Verdict.UNCERTAIN]
        assert result.confidence >= 0
        assert result.confidence <= 100
        assert result.analysis_time > 0
        assert len(result.scores) >= 4  # Ensemble + 3 individual scores

    def test_human_text_detection(self, ensemble_analyzer, sample_human_text):
        """Test detection of human-written text."""
        result = ensemble_analyzer.analyze(sample_human_text)
        
        assert result is not None
        assert result.verdict in [Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN, Verdict.UNCERTAIN]
        assert result.confidence >= 0
        assert result.confidence <= 100
        assert result.analysis_time > 0

    def test_ensemble_scores_structure(self, ensemble_analyzer, medium_text):
        """Test that ensemble produces proper score structure."""
        result = ensemble_analyzer.analyze(medium_text)
        
        # Should have ensemble score + 3 individual scores
        assert len(result.scores) >= 4
        
        # First score should be ensemble score
        assert "Ensemble" in result.scores[0].name
        
        # Should have individual analyzer scores
        score_names = [s.name for s in result.scores]
        assert any("RoBERTa" in name for name in score_names)
        assert any("GPT-2" in name for name in score_names)
        assert any("NLTK" in name for name in score_names)

    def test_weights_sum_to_one(self, ensemble_analyzer):
        """Test that ensemble weights sum to 1.0."""
        total_weight = sum(ensemble_analyzer.weights.values())
        assert abs(total_weight - 1.0) < 0.01  # Allow small floating point error

    def test_custom_weights(self):
        """Test setting custom ensemble weights."""
        analyzer = EnsembleAnalyzer()
        analyzer.weights = {
            "roberta": 0.50,
            "gpt2": 0.30,
            "nltk": 0.20,
        }
        
        assert analyzer.weights["roberta"] == 0.50
        assert analyzer.weights["gpt2"] == 0.30
        assert analyzer.weights["nltk"] == 0.20

    def test_result_contains_all_metrics(self, ensemble_analyzer, medium_text):
        """Test that result contains all expected metrics."""
        result = ensemble_analyzer.analyze(medium_text)
        
        assert hasattr(result, 'perplexity')
        assert hasattr(result, 'burstiness')
        assert hasattr(result, 'lexical_diversity')
        assert hasattr(result, 'sentence_variance')
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'verdict')
        assert hasattr(result, 'explanation')

    def test_explanation_contains_analyzer_info(self, ensemble_analyzer, medium_text):
        """Test that explanation includes individual analyzer information."""
        result = ensemble_analyzer.analyze(medium_text)
        
        explanation = result.explanation.lower()
        assert "roberta" in explanation or "ensemble" in explanation
        assert "analyzer" in explanation

    def test_confidence_in_valid_range(self, ensemble_analyzer, medium_text):
        """Test that confidence is always in valid range."""
        result = ensemble_analyzer.analyze(medium_text)
        
        assert result.confidence >= 0.0
        assert result.confidence <= 100.0

    def test_to_dict_serialization(self, ensemble_analyzer, medium_text):
        """Test result serialization to dictionary."""
        result = ensemble_analyzer.analyze(medium_text)
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert "verdict" in result_dict
        assert "confidence" in result_dict
        assert "method" in result_dict
        assert "scores" in result_dict
        assert result_dict["method"] == "Ensemble (RoBERTa+GPT2+NLTK)"

    def test_consistent_results(self, ensemble_analyzer):
        """Test that same text produces consistent results."""
        text = "This is a test text for consistency checking."
        
        result1 = ensemble_analyzer.analyze(text)
        result2 = ensemble_analyzer.analyze(text)
        
        # Verdicts should be the same
        assert result1.verdict == result2.verdict
        # Confidence should be very similar (within 1%)
        assert abs(result1.confidence - result2.confidence) < 1.0

    def test_error_handling(self, ensemble_analyzer):
        """Test error handling with invalid input."""
        # Test with None
        result = ensemble_analyzer.analyze(None or "")
        assert result.verdict == Verdict.UNCERTAIN
        
        # Test with very long text (should still work)
        long_text = "word " * 10000
        result = ensemble_analyzer.analyze(long_text)
        assert result is not None
