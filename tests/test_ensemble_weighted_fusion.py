"""Deterministic weighted-fusion tests for EnsembleAnalyzer."""

from src.analyzers.ensemble_analyzer import EnsembleAnalyzer
from src.config.settings import Verdict
from src.models.result import AnalysisResult, DetectionScore, TextMetrics


def test_combine_results_uses_documented_default_weights():
    analyzer = EnsembleAnalyzer()

    base_result = AnalysisResult(metrics=TextMetrics(total_words=10, unique_words=7))

    roberta_result = AnalysisResult(verdict=Verdict.UNCERTAIN, confidence=55.0)
    roberta_result.add_score(
        DetectionScore(name="RoBERTa AI Probability", value=0.8, indicates_ai=True)
    )

    gpt2_result = AnalysisResult(
        verdict=Verdict.LIKELY_AI,
        confidence=70.0,
        perplexity=100.0,
        burstiness=0.2,
        sentence_variance=0.3,
    )

    nltk_result = AnalysisResult(
        verdict=Verdict.LIKELY_HUMAN,
        confidence=60.0,
        perplexity=200.0,
        burstiness=0.4,
        sentence_variance=0.5,
    )

    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)

    gpt2_ai_score = max(0, min(1, 1 - (100.0 / 500)))
    nltk_ai_score = max(0, min(1, 1 - (200.0 / 500)))
    expected = (0.0 * 0.8) + (0.65 * gpt2_ai_score) + (0.35 * nltk_ai_score)

    assert combined.scores
    assert combined.scores[0].name == "Ensemble AI Score"
    assert abs(combined.scores[0].value - expected) < 1e-6
