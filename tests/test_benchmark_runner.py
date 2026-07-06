"""Tests for the benchmark runner internals (no model loading)."""

import json

import pytest

from src.config.settings import Verdict
from src.evaluation import benchmark as bench
from src.evaluation.dataset import Sample
from src.models.result import AnalysisResult


class _FakeAnalyzer:
    """Returns AI for even-indexed samples, human otherwise (deterministic)."""

    def __init__(self, samples):
        self._labels = {s.text: s.label for s in samples}

    def analyze(self, text):
        label = self._labels.get(text, 0)
        verdict = Verdict.AI_GENERATED if label == 1 else Verdict.HUMAN_WRITTEN
        return AnalysisResult(verdict=verdict, confidence=90.0)


def _samples():
    return [
        Sample(id="h1", label=0, source="t", text="human one"),
        Sample(id="a1", label=1, source="t", text="ai one"),
        Sample(id="h2", label=0, source="t", text="human two"),
        Sample(id="a2", label=1, source="t", text="ai two"),
    ]


class TestBuildAnalyzer:
    def test_unknown_analyzer_raises(self):
        with pytest.raises(ValueError):
            bench._build_analyzer("does-not-exist")

    def test_known_names_construct_without_model_load(self):
        # NLTK constructs lazily (no Brown build until analyze()).
        analyzer = bench._build_analyzer("nltk")
        assert analyzer.__class__.__name__ == "NLTKAnalyzer"


class TestSummaryAndSerialization:
    def test_format_summary_contains_metrics(self):
        samples = _samples()
        result = bench.run_benchmark(_FakeAnalyzer(samples), samples, analyzer_name="fake")
        text = bench._format_summary(result)
        assert "fake" in text
        assert "Accuracy" in text
        assert "AUROC" in text
        assert "FPR" in text

    def test_result_to_dict_roundtrips(self):
        samples = _samples()
        result = bench.run_benchmark(_FakeAnalyzer(samples), samples, analyzer_name="fake")
        payload = result.to_dict()
        assert payload["analyzer"] == "fake"
        assert payload["n_samples"] == 4
        assert len(payload["predictions"]) == 4
        # Must be JSON-serialisable.
        json.dumps(payload)

    def test_sample_prediction_rounding(self):
        p = bench.SamplePrediction(
            id="x", label=1, source="s", ai_probability=0.123456, verdict="AI", confidence=88.888
        )
        d = p.to_dict()
        assert d["ai_probability"] == 0.1235
        assert d["confidence"] == 88.89


class TestPlots:
    def test_save_plots_writes_files(self, tmp_path):
        samples = _samples()
        result = bench.run_benchmark(_FakeAnalyzer(samples), samples, analyzer_name="fake")
        written = bench.save_plots(result, tmp_path)
        # matplotlib is a project dependency; expect ROC + calibration PNGs.
        assert len(written) == 2
        for path in written:
            assert path.exists()
            assert path.suffix == ".png"


class TestMainCLI:
    def test_main_writes_report_and_plots(self, tmp_path, monkeypatch):
        samples = _samples()
        monkeypatch.setattr(bench, "load_dataset", lambda path=None: samples)
        monkeypatch.setattr(bench, "_build_analyzer", lambda name: _FakeAnalyzer(samples))

        out = tmp_path / "nested" / "report.json"
        plots = tmp_path / "plots"
        rc = bench.main(["--analyzer", "nltk", "--output", str(out), "--plots", str(plots)])
        assert rc == 0
        assert out.exists()  # parent dir auto-created
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["n_samples"] == 4
        assert list(plots.glob("*.png"))
