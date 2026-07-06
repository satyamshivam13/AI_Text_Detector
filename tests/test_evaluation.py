"""Tests for the evaluation/benchmark layer (fast, no model loading)."""

import pytest

from src.config.settings import Verdict
from src.evaluation import metrics
from src.evaluation.benchmark import result_to_ai_probability, run_benchmark
from src.evaluation.dataset import load_dataset
from src.models.result import AnalysisResult, DetectionScore


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
class TestMetrics:
    def test_perfect_classifier(self):
        labels = [0, 0, 1, 1]
        scores = [0.1, 0.2, 0.8, 0.9]
        rep = metrics.binary_report(labels, scores)
        assert rep.accuracy == 1.0
        assert rep.precision == 1.0
        assert rep.recall == 1.0
        assert rep.f1 == 1.0
        assert rep.roc_auc == 1.0
        assert rep.false_positive_rate == 0.0
        assert rep.false_negative_rate == 0.0

    def test_inverted_classifier_auroc(self):
        labels = [0, 0, 1, 1]
        scores = [0.9, 0.8, 0.2, 0.1]  # perfectly wrong
        assert metrics.roc_auc(labels, scores) == 0.0

    def test_chance_auroc_with_ties(self):
        labels = [0, 1, 0, 1]
        scores = [0.5, 0.5, 0.5, 0.5]
        assert metrics.roc_auc(labels, scores) == pytest.approx(0.5)

    def test_confusion_counts(self):
        labels = [1, 1, 0, 0]
        scores = [0.9, 0.4, 0.6, 0.1]  # threshold 0.5
        tp, fp, tn, fn = metrics.confusion_counts(labels, scores, threshold=0.5)
        assert (tp, fp, tn, fn) == (1, 1, 1, 1)

    def test_false_positive_rate_definition(self):
        # All human, half wrongly flagged as AI -> FPR 0.5
        labels = [0, 0, 0, 0]
        scores = [0.9, 0.9, 0.1, 0.1]
        rep = metrics.binary_report(labels, scores)
        assert rep.false_positive_rate == 0.5
        assert rep.n_positive == 0

    def test_expected_calibration_error_perfect(self):
        # Predicted probs exactly match observed frequencies within bins.
        labels = [0, 0, 1, 1]
        scores = [0.0, 0.0, 1.0, 1.0]
        assert metrics.expected_calibration_error(labels, scores) == pytest.approx(0.0)

    def test_ece_detects_miscalibration(self):
        labels = [0, 0, 0, 0]
        scores = [0.9, 0.9, 0.9, 0.9]  # confident but always wrong
        assert metrics.expected_calibration_error(labels, scores) == pytest.approx(0.9)

    def test_best_threshold_by_f1(self):
        labels = [0, 0, 1, 1]
        scores = [0.2, 0.3, 0.6, 0.7]
        t, f1 = metrics.best_threshold_by_f1(labels, scores)
        assert f1 == 1.0
        assert 0.3 < t <= 0.6

    def test_roc_curve_monotone(self):
        labels = [0, 1, 0, 1, 0, 1]
        scores = [0.2, 0.8, 0.4, 0.6, 0.1, 0.9]
        fpr, tpr, _ = metrics.roc_curve(labels, scores)
        assert fpr[0] == 0.0 and tpr[0] == 0.0
        assert fpr[-1] == pytest.approx(1.0)
        assert tpr[-1] == pytest.approx(1.0)
        assert all(fpr[i] <= fpr[i + 1] + 1e-9 for i in range(len(fpr) - 1))

    def test_rejects_out_of_range_scores(self):
        with pytest.raises(ValueError):
            metrics.binary_report([0, 1], [0.5, 1.5])

    def test_rejects_bad_labels(self):
        with pytest.raises(ValueError):
            metrics.binary_report([0, 2], [0.5, 0.5])

    def test_rejects_empty(self):
        with pytest.raises(ValueError):
            metrics.binary_report([], [])


# --------------------------------------------------------------------------- #
# Probability extraction
# --------------------------------------------------------------------------- #
class TestAiProbability:
    def test_prefers_ensemble_score(self):
        result = AnalysisResult(verdict=Verdict.LIKELY_HUMAN, confidence=90)
        result.add_score(DetectionScore(name="Ensemble AI Score", value=0.73))
        assert result_to_ai_probability(result) == pytest.approx(0.73)

    def test_ai_verdict_maps_above_half(self):
        result = AnalysisResult(verdict=Verdict.AI_GENERATED, confidence=80)
        assert result_to_ai_probability(result) == pytest.approx(0.9)

    def test_human_verdict_maps_below_half(self):
        result = AnalysisResult(verdict=Verdict.HUMAN_WRITTEN, confidence=80)
        assert result_to_ai_probability(result) == pytest.approx(0.1)

    def test_uncertain_maps_to_half(self):
        result = AnalysisResult(verdict=Verdict.UNCERTAIN, confidence=0)
        assert result_to_ai_probability(result) == pytest.approx(0.5)

    def test_probability_bounds(self):
        result = AnalysisResult(verdict=Verdict.AI_GENERATED, confidence=100)
        p = result_to_ai_probability(result)
        assert 0.0 <= p <= 1.0


# --------------------------------------------------------------------------- #
# Dataset + runner
# --------------------------------------------------------------------------- #
class TestDatasetAndRunner:
    def test_bundled_dataset_loads(self):
        samples = load_dataset()
        assert len(samples) >= 20
        assert {s.label for s in samples} == {0, 1}
        assert all(s.text.strip() for s in samples)

    def test_dataset_balanced_enough(self):
        samples = load_dataset()
        n_ai = sum(s.label for s in samples)
        n_human = len(samples) - n_ai
        assert n_ai > 0 and n_human > 0

    def test_run_benchmark_with_fake_analyzer(self):
        class _FakeAnalyzer:
            """Oracle: returns the ground truth so the harness math is testable."""

            def __init__(self, samples):
                self._by_text = {s.text: s.label for s in samples}

            def analyze(self, text):
                label = self._by_text[text]
                verdict = Verdict.AI_GENERATED if label == 1 else Verdict.HUMAN_WRITTEN
                return AnalysisResult(verdict=verdict, confidence=90.0)

        samples = load_dataset()
        result = run_benchmark(_FakeAnalyzer(samples), samples, analyzer_name="oracle")
        assert result.n_samples == len(samples)
        assert result.report_default.accuracy == 1.0
        assert result.report_default.roc_auc == 1.0
        d = result.to_dict()
        assert d["analyzer"] == "oracle"
        assert len(d["predictions"]) == len(samples)
