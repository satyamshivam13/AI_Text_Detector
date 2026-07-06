"""Tests for the ChartGenerator visualization layer (no models loaded)."""

import plotly.graph_objects as go
import pytest

from src.models.result import AnalysisResult, DetectionScore, TextMetrics
from src.utils.visualization import ChartGenerator  # sets matplotlib Agg backend


@pytest.fixture
def chart_gen():
    return ChartGenerator()


@pytest.fixture
def sample_result():
    result = AnalysisResult(
        perplexity=45.0,
        burstiness=0.3,
        lexical_diversity=0.6,
        sentence_variance=0.4,
        confidence=72.0,
    )
    result.metrics = TextMetrics(
        total_words=120,
        unique_words=80,
        word_frequencies={"model": 5, "text": 4, "data": 3, "code": 2, "test": 1},
        sentence_lengths=[8, 12, 6, 15, 9],
    )
    result.add_score(DetectionScore(name="Perplexity", value=0.7, weight=0.4, indicates_ai=True))
    result.add_score(DetectionScore(name="Burstiness", value=0.3, weight=0.25, indicates_ai=False))
    return result


class TestWordFrequencyPlotly:
    def test_populated(self, chart_gen):
        fig = chart_gen.create_word_frequency_chart_plotly({"a": 5, "b": 3, "c": 1}, top_n=2)
        assert isinstance(fig, go.Figure)

    def test_empty(self, chart_gen):
        fig = chart_gen.create_word_frequency_chart_plotly({})
        assert isinstance(fig, go.Figure)


class TestWordFrequencyMatplotlib:
    def test_populated(self, chart_gen):
        fig = chart_gen.create_word_frequency_chart_matplotlib({"a": 5, "b": 3}, top_n=2)
        assert fig is not None

    def test_empty(self, chart_gen):
        fig = chart_gen.create_word_frequency_chart_matplotlib({})
        assert fig is not None


class TestResultCharts:
    def test_metrics_gauge(self, chart_gen, sample_result):
        assert isinstance(chart_gen.create_metrics_gauge(sample_result), go.Figure)

    def test_score_breakdown(self, chart_gen, sample_result):
        assert isinstance(chart_gen.create_score_breakdown_chart(sample_result), go.Figure)

    def test_score_breakdown_no_scores(self, chart_gen):
        assert isinstance(chart_gen.create_score_breakdown_chart(AnalysisResult()), go.Figure)


class TestSentenceLengthChart:
    def test_populated(self, chart_gen):
        assert isinstance(chart_gen.create_sentence_length_chart([5, 9, 12, 7]), go.Figure)

    def test_empty(self, chart_gen):
        assert isinstance(chart_gen.create_sentence_length_chart([]), go.Figure)
