"""Tests for the perplexity -> AI-probability calibration."""

import pytest

from src.analyzers.calibration import logistic_ai_probability


class TestLogisticCalibration:
    def test_midpoint_maps_to_half(self):
        assert logistic_ai_probability(30, midpoint=30, slope=0.15) == pytest.approx(0.5)

    def test_lower_is_ai_direction(self):
        # Below the midpoint => more AI-like (higher probability).
        low = logistic_ai_probability(15, midpoint=30, slope=0.15, direction="lower_is_ai")
        high = logistic_ai_probability(60, midpoint=30, slope=0.15, direction="lower_is_ai")
        assert low > 0.5 > high

    def test_higher_is_ai_direction(self):
        low = logistic_ai_probability(600, midpoint=1550, slope=0.0015, direction="higher_is_ai")
        high = logistic_ai_probability(3000, midpoint=1550, slope=0.0015, direction="higher_is_ai")
        assert high > 0.5 > low

    def test_output_bounded(self):
        for ppl in (0, 1, 50, 500, 10000):
            p = logistic_ai_probability(ppl, midpoint=30, slope=0.5)
            assert 0.0 <= p <= 1.0

    def test_human_typical_gpt2_perplexity_below_half(self):
        # The C2 regression: human GPT-2 perplexity (~58) must NOT read as AI.
        assert logistic_ai_probability(58, midpoint=30, slope=0.15) < 0.5

    def test_ai_typical_gpt2_perplexity_above_half(self):
        assert logistic_ai_probability(17, midpoint=30, slope=0.15) > 0.5

    def test_invalid_slope(self):
        with pytest.raises(ValueError):
            logistic_ai_probability(30, midpoint=30, slope=0.0)

    def test_invalid_direction(self):
        with pytest.raises(ValueError):
            logistic_ai_probability(30, midpoint=30, slope=0.1, direction="sideways")

    def test_numerical_stability_extremes(self):
        # lower_is_ai: perplexity far above midpoint => ~0 (human).
        assert logistic_ai_probability(1e6, midpoint=30, slope=1.0) == pytest.approx(0.0)
        # lower_is_ai: perplexity far below midpoint => ~1 (AI).
        assert logistic_ai_probability(0, midpoint=1e6, slope=1.0) == pytest.approx(1.0)
