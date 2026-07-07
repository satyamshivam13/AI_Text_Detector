"""Deterministic calibrated-fusion tests for EnsembleAnalyzer."""

from src.analyzers.calibration import logistic_ai_probability
from src.analyzers.ensemble_analyzer import EnsembleAnalyzer
from src.config.settings import Verdict, get_settings
from src.models.result import AnalysisResult, DetectionScore, TextMetrics


def test_combine_results_uses_calibrated_logistic_fusion():
    analyzer = EnsembleAnalyzer()
    cfg = get_settings().ensemble

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
        perplexity=2000.0,
        burstiness=0.4,
        sentence_variance=0.5,
    )

    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)

    gpt2_ai = logistic_ai_probability(
        100.0, midpoint=cfg.gpt2_ppl_midpoint, slope=cfg.gpt2_ppl_slope, direction="lower_is_ai"
    )
    nltk_ai = logistic_ai_probability(
        2000.0, midpoint=cfg.nltk_ppl_midpoint, slope=cfg.nltk_ppl_slope, direction="higher_is_ai"
    )
    # RoBERTa weight is 0, so it drops out of the blend.
    expected = (cfg.weight_gpt2 * gpt2_ai) + (cfg.weight_nltk * nltk_ai)

    assert combined.scores
    assert combined.scores[0].name == "Ensemble AI Score"
    assert abs(combined.scores[0].value - expected) < 1e-6


def test_human_scale_perplexity_is_not_flagged_ai():
    """Regression for the C2 bias: human-typical GPT-2 perplexity must map below 0.5."""
    analyzer = EnsembleAnalyzer()

    base_result = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
    roberta_result = analyzer._disabled_roberta_result()
    # Human-typical perplexities from the benchmark (GPT-2 ~58, Brown ~1200).
    gpt2_result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, perplexity=58.0)
    nltk_result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, perplexity=1200.0)

    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)
    ensemble_score = combined.scores[0].value

    # Under the old `1 - ppl/500` map this was ~0.88 (flagged AI). It must now
    # sit on the human side of the 0.5 boundary.
    assert ensemble_score < 0.5

    analyzer._determine_verdict(combined)
    assert combined.verdict in (Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN, Verdict.UNCERTAIN)


def test_binoculars_off_by_default_no_row_no_effect():
    analyzer = EnsembleAnalyzer()
    assert analyzer.weights["binoculars"] == 0.0

    base_result = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
    roberta_result = analyzer._disabled_roberta_result()
    gpt2_result = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=58.0)
    nltk_result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, perplexity=1200.0)

    # binoculars_ai defaults to None -> no term, no row.
    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)
    names = [s.name for s in combined.scores]
    assert "Binoculars Score" not in names


def test_binoculars_contributes_when_weighted():
    analyzer = EnsembleAnalyzer()
    # Enable Binoculars and rebalance so weights still sum to 1.
    analyzer.weights = {"roberta": 0.0, "gpt2": 0.5, "nltk": 0.2, "binoculars": 0.3}

    base_result = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
    roberta_result = analyzer._disabled_roberta_result()
    gpt2_result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, perplexity=58.0)
    nltk_result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, perplexity=1200.0)

    combined = analyzer._combine_results(
        base_result, roberta_result, gpt2_result, nltk_result, binoculars_ai=0.9
    )
    names = [s.name for s in combined.scores]
    assert "Binoculars Score" in names
    # The strong AI binoculars signal (0.9) at 0.3 weight lifts the ensemble
    # score above what GPT-2+NLTK (both human-leaning here) would give alone.
    ensemble_score = combined.scores[0].value
    assert ensemble_score >= 0.3 * 0.9


def test_verdict_is_robust_to_score_reordering():
    """The fused score is addressed by name, so inserting scores before it (or
    reordering) must not change the verdict — guards the old scores[0] contract."""
    analyzer = EnsembleAnalyzer()
    base_result = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
    roberta_result = analyzer._disabled_roberta_result()
    gpt2_result = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=15.0)
    nltk_result = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=3000.0)

    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)
    analyzer._determine_verdict(combined)
    verdict_before = combined.verdict

    # Move the primary "Ensemble AI Score" out of index 0.
    primary = combined.get_score(analyzer.ENSEMBLE_SCORE_NAME)
    combined.scores.remove(primary)
    combined.scores.append(primary)
    analyzer._determine_verdict(combined)

    assert combined.verdict == verdict_before


def test_disabled_roberta_excluded_from_agreement():
    analyzer = EnsembleAnalyzer()
    base_result = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
    roberta_result = analyzer._disabled_roberta_result()
    gpt2_result = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=15.0)
    nltk_result = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=3000.0)

    combined = analyzer._combine_results(base_result, roberta_result, gpt2_result, nltk_result)
    # RoBERTa row carries weight 0 so it is not a voter.
    voters = [s for s in combined.scores[1:] if s.weight > 0]
    assert all("RoBERTa" not in v.name for v in voters)
    assert len(voters) == 2  # GPT-2 + NLTK
