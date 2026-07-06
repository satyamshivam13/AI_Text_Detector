"""Tests for the Binoculars cross-perplexity analyzer.

These mock the two-model computation so no weights are loaded.
"""

import pytest

from src.analyzers.binoculars_analyzer import BinocularsAnalyzer
from src.config.settings import Verdict


@pytest.fixture
def analyzer():
    return BinocularsAnalyzer()


def _patch_score(analyzer, score, observer_ppl=50.0):
    analyzer._compute_binoculars = lambda text: (score, observer_ppl)


class TestBinocularsContract:
    def test_method_name(self, analyzer):
        assert "Binoculars" in analyzer.method_name

    def test_low_ratio_is_ai(self, analyzer):
        # Ratio well below the midpoint => AI-leaning verdict.
        _patch_score(analyzer, analyzer.config.score_midpoint - 0.1)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        assert result.scores[0].name == "Binoculars AI Score"
        assert result.scores[0].value > 0.5
        assert result.verdict in (Verdict.AI_GENERATED, Verdict.LIKELY_AI)

    def test_high_ratio_is_human(self, analyzer):
        _patch_score(analyzer, analyzer.config.score_midpoint + 0.1)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        assert result.scores[0].value < 0.5
        assert result.verdict in (Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN)

    def test_midpoint_is_uncertain(self, analyzer):
        _patch_score(analyzer, analyzer.config.score_midpoint)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        assert result.scores[0].value == pytest.approx(0.5, abs=1e-6)
        assert result.verdict == Verdict.UNCERTAIN

    def test_ratio_score_row_present(self, analyzer):
        _patch_score(analyzer, 0.8)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        names = [s.name for s in result.scores]
        assert "Binoculars Ratio" in names

    def test_confidence_bounded(self, analyzer):
        _patch_score(analyzer, 0.5)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        assert 0.0 <= result.confidence <= 100.0

    def test_empty_text_uncertain(self, analyzer):
        result = analyzer.analyze("")
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0

    def test_serialization(self, analyzer):
        _patch_score(analyzer, 0.85)
        result = analyzer.analyze("Some sufficiently long text " * 10)
        payload = result.to_dict()
        assert payload["method"] == analyzer.method_name
        assert "scores" in payload


@pytest.mark.slow
class TestBinocularsRealModels:
    """Exercises the real two-model computation (downloads gpt2 + distilgpt2)."""

    def test_compute_binoculars_returns_ratio(self, analyzer):
        score, observer_ppl = analyzer._compute_binoculars(
            "The mitochondria is the powerhouse of the cell, and cellular "
            "respiration produces the energy currency of the organism."
        )
        assert score > 0
        assert observer_ppl > 0

    def test_end_to_end_analyze(self, analyzer):
        from src.config.settings import Verdict

        result = analyzer.analyze(
            "So anyway I went to the store and forgot my wallet, classic me, "
            "had to walk all the way back home in the rain. Great day."
        )
        assert result.verdict in list(Verdict)
        assert result.scores[0].name == "Binoculars AI Score"
        assert 0.0 <= result.scores[0].value <= 1.0
