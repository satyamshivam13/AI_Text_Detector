"""
Tests for NLTK-based analyzer.
"""

import pytest
from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.config.settings import Verdict, ConfidenceLevel


class TestNLTKAnalyzerInit:
    """Tests for analyzer initialization."""

    def test_default_ngram_size(self):
        analyzer = NLTKAnalyzer()
        assert analyzer.ngram_size == 3

    def test_custom_ngram_size(self):
        analyzer = NLTKAnalyzer(ngram_size=2)
        assert analyzer.ngram_size == 2

    def test_set_ngram_size(self):
        analyzer = NLTKAnalyzer()
        analyzer.set_ngram_size(4)
        assert analyzer.ngram_size == 4

    def test_invalid_ngram_size(self):
        analyzer = NLTKAnalyzer()
        with pytest.raises(ValueError):
            analyzer.set_ngram_size(1)
        with pytest.raises(ValueError):
            analyzer.set_ngram_size(6)


class TestNLTKAnalysis:
    """Tests for NLTK analysis functionality."""

    @pytest.fixture(autouse=True)
    def setup_analyzer(self):
        self.analyzer = NLTKAnalyzer(ngram_size=3)

    def test_analyze_returns_result(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result is not None
        assert result.verdict in list(Verdict)
        assert result.confidence_level in list(ConfidenceLevel)

    def test_analyze_sets_method(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert "NLTK" in result.method

    def test_analyze_computes_perplexity(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.perplexity > 0

    def test_analyze_computes_burstiness(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert 0.0 <= result.burstiness <= 1.0

    def test_analyze_computes_lexical_diversity(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert 0.0 <= result.lexical_diversity <= 1.0

    def test_analyze_computes_sentence_variance(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.sentence_variance >= 0.0

    def test_analyze_has_scores(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert len(result.scores) >= 4
        score_names = [s.name for s in result.scores]
        assert "Perplexity" in score_names
        assert "Burstiness" in score_names
        assert "Lexical Diversity" in score_names
        assert "Sentence Variance" in score_names

    def test_analyze_has_metrics(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.metrics.total_words > 0
        assert result.metrics.total_sentences >= 1

    def test_analyze_has_explanation(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.explanation
        assert len(result.explanation) > 20

    def test_analyze_records_time(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert result.analysis_time > 0

    def test_analyze_empty_text(self, empty_text):
        result = self.analyzer.analyze(empty_text)
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0
        assert len(result.warnings) > 0

    def test_analyze_short_text(self, short_text):
        result = self.analyzer.analyze(short_text)
        assert result is not None
        assert len(result.warnings) > 0  # Should warn about short text

    def test_analyze_confidence_range(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        assert 0.0 <= result.confidence <= 100.0

    def test_analyze_ai_vs_human_text(self, sample_ai_text, sample_human_text):
        """AI text should generally score differently from human text."""
        ai_result = self.analyzer.analyze(sample_ai_text)
        human_result = self.analyzer.analyze(sample_human_text)

        # Both should complete without error
        assert ai_result.verdict in list(Verdict)
        assert human_result.verdict in list(Verdict)

        # They should have different characteristics (not testing exact verdicts
        # since this is heuristic-based)
        assert ai_result.perplexity != human_result.perplexity

    def test_analyze_result_serialization(self, sample_ai_text):
        result = self.analyzer.analyze(sample_ai_text)
        d = result.to_dict()
        assert "verdict" in d
        assert "confidence" in d
        assert "perplexity" in d
        assert "method" in d

        json_str = result.to_json()
        assert isinstance(json_str, str)
        assert len(json_str) > 0