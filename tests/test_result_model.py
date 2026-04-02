"""
Tests for result data models.
"""

import json
import pytest
from src.models.result import AnalysisResult, TextMetrics, DetectionScore
from src.config.settings import Verdict, ConfidenceLevel


class TestTextMetrics:
    """Tests for TextMetrics model."""

    def test_default_values(self):
        metrics = TextMetrics()
        assert metrics.total_characters == 0
        assert metrics.total_words == 0
        assert metrics.total_sentences == 0
        assert metrics.lexical_diversity == 0.0

    def test_lexical_diversity_calculation(self):
        metrics = TextMetrics(total_words=100, unique_words=60)
        assert metrics.lexical_diversity == 0.6

    def test_lexical_diversity_zero_words(self):
        metrics = TextMetrics(total_words=0, unique_words=0)
        assert metrics.lexical_diversity == 0.0

    def test_to_dict(self):
        metrics = TextMetrics(total_words=50, unique_words=30)
        d = metrics.to_dict()
        assert isinstance(d, dict)
        assert "total_words" in d
        assert "lexical_diversity" in d
        assert d["lexical_diversity"] == 0.6


class TestDetectionScore:
    """Tests for DetectionScore model."""

    def test_creation(self):
        score = DetectionScore(
            name="Perplexity",
            value=45.2,
            weight=0.4,
            interpretation="Low perplexity",
            indicates_ai=True,
        )
        assert score.name == "Perplexity"
        assert score.value == 45.2
        assert score.indicates_ai is True

    def test_weighted_value(self):
        score = DetectionScore(name="Test", value=100.0, weight=0.5)
        assert score.weighted_value == 50.0

    def test_default_weight(self):
        score = DetectionScore(name="Test", value=50.0)
        assert score.weight == 1.0
        assert score.weighted_value == 50.0


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_default_values(self):
        result = AnalysisResult()
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0
        assert result.is_ai_generated is False
        assert result.is_human_written is False

    def test_is_ai_generated(self):
        result = AnalysisResult(verdict=Verdict.AI_GENERATED)
        assert result.is_ai_generated is True
        assert result.is_human_written is False

    def test_is_likely_ai(self):
        result = AnalysisResult(verdict=Verdict.LIKELY_AI)
        assert result.is_ai_generated is True

    def test_is_human_written(self):
        result = AnalysisResult(verdict=Verdict.HUMAN_WRITTEN)
        assert result.is_human_written is True
        assert result.is_ai_generated is False

    def test_is_likely_human(self):
        result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN)
        assert result.is_human_written is True

    def test_add_warning(self):
        result = AnalysisResult()
        result.add_warning("Test warning")
        assert "Test warning" in result.warnings

    def test_add_duplicate_warning(self):
        result = AnalysisResult()
        result.add_warning("Same warning")
        result.add_warning("Same warning")
        assert len(result.warnings) == 1

    def test_add_score(self):
        result = AnalysisResult()
        score = DetectionScore(name="Test", value=50.0)
        result.add_score(score)
        assert len(result.scores) == 1
        assert result.scores[0].name == "Test"

    def test_to_dict(self):
        result = AnalysisResult(
            verdict=Verdict.AI_GENERATED,
            confidence=85.5,
            perplexity=30.0,
            burstiness=0.15,
        )
        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["verdict"] == "AI-Generated"
        assert d["confidence"] == 85.5
        assert d["perplexity"] == 30.0

    def test_to_json(self):
        result = AnalysisResult(verdict=Verdict.UNCERTAIN, confidence=50.0)
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["verdict"] == "Uncertain"
        assert parsed["confidence"] == 50.0

    def test_to_dict_includes_scores(self):
        result = AnalysisResult()
        result.add_score(DetectionScore(name="Test", value=42.0, weight=0.5))
        d = result.to_dict()
        assert "scores" in d
        assert len(d["scores"]) == 1
        assert d["scores"][0]["name"] == "Test"

    def test_to_dict_includes_metrics(self):
        result = AnalysisResult()
        result.metrics = TextMetrics(total_words=100, unique_words=50)
        d = result.to_dict()
        assert "metrics" in d
        assert d["metrics"]["total_words"] == 100

    def test_to_dict_canonical_keys(self):
        result = AnalysisResult(
            verdict=Verdict.LIKELY_AI,
            confidence=73.4,
            confidence_level=ConfidenceLevel.MEDIUM,
            perplexity=88.1,
            burstiness=0.24,
            lexical_diversity=0.61,
            sentence_variance=0.37,
            method="unit-test",
            analysis_time=0.321,
            timestamp="2026-04-02T10:30:00",
            text_length=123,
            explanation="Contract test payload",
            metrics=TextMetrics(total_words=20, unique_words=12),
            warnings=["test warning"],
        )
        result.add_score(
            DetectionScore(
                name="Test score",
                value=0.7,
                weight=0.5,
                interpretation="mock",
                indicates_ai=True,
            )
        )

        payload = result.to_dict()

        expected_keys = frozenset(
            {
                "verdict",
                "confidence",
                "confidence_level",
                "perplexity",
                "burstiness",
                "lexical_diversity",
                "sentence_variance",
                "method",
                "analysis_time",
                "timestamp",
                "text_length",
                "warnings",
                "explanation",
                "metrics",
                "scores",
            }
        )

        assert frozenset(payload.keys()) == expected_keys