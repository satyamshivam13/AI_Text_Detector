"""Contract tests for the shared BaseAnalyzer pipeline behavior."""

import re

from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.config.settings import ConfidenceLevel, Verdict


def test_analyze_empty_text_contract():
    """Empty input should return a structured result with timing metadata."""
    analyzer = NLTKAnalyzer()

    result = analyzer.analyze("")

    assert result.verdict == Verdict.UNCERTAIN
    assert result.confidence == 0.0
    assert result.confidence_level == ConfidenceLevel.VERY_LOW
    assert any("Empty or invalid text" in warning for warning in result.warnings)
    assert "No text" in result.explanation
    assert result.analysis_time >= 0
    assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", result.timestamp)
    assert result.scores == []


def test_analyze_short_text_contract(short_text):
    """Short non-empty input should still run and keep full result contract."""
    analyzer = NLTKAnalyzer()

    result = analyzer.analyze(short_text)
    serialized = result.to_dict()

    assert len(result.warnings) > 0
    assert any(
        "short" in warning.lower() or "minimum" in warning.lower() or "accuracy" in warning.lower()
        for warning in result.warnings
    )
    assert result.analysis_time > 0

    expected_keys = {
        "verdict",
        "confidence",
        "confidence_level",
        "metrics",
        "scores",
        "explanation",
        "analysis_time",
        "warnings",
    }
    assert expected_keys.issubset(set(serialized.keys()))
