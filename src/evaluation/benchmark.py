"""
Benchmark Runner
================

Runs an analyzer over a labelled dataset and produces a reproducible report:
per-sample AI-probabilities, classification metrics at the default and
F1-optimal thresholds, ROC points and reliability bins.

Usage (CLI)::

    python -m src.evaluation.benchmark --analyzer nltk
    python -m src.evaluation.benchmark --analyzer ensemble --output report.json --plots out/

The analyzer is addressed by name so the heavy transformer analyzers are only
imported when actually requested.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol

from src.config.settings import Verdict
from src.evaluation import metrics
from src.evaluation.dataset import Sample, load_dataset
from src.models.result import AnalysisResult
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Continuous AI-probability contributed by verdict direction, scaled by
# confidence. Kept monotone so ROC/AUROC are meaningful even for analyzers that
# do not expose an explicit probability.
_AI_VERDICTS = (Verdict.AI_GENERATED, Verdict.LIKELY_AI)
_HUMAN_VERDICTS = (Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN)


class _Analyzer(Protocol):
    def analyze(self, text: str) -> AnalysisResult: ...


def result_to_ai_probability(result: AnalysisResult) -> float:
    """Map an :class:`AnalysisResult` to a single AI-probability in ``[0, 1]``.

    Prefers an explicit ensemble AI score; otherwise derives a monotone score
    from the verdict direction and confidence.
    """
    for score in result.scores:
        if score.name == "Ensemble AI Score":
            return max(0.0, min(1.0, float(score.value)))

    conf = max(0.0, min(1.0, result.confidence / 100.0))
    if result.verdict in _AI_VERDICTS:
        return 0.5 + 0.5 * conf
    if result.verdict in _HUMAN_VERDICTS:
        return 0.5 - 0.5 * conf
    return 0.5  # UNCERTAIN


@dataclass
class SamplePrediction:
    id: str
    label: int
    source: str
    ai_probability: float
    verdict: str
    confidence: float

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "label": self.label,
            "source": self.source,
            "ai_probability": round(self.ai_probability, 4),
            "verdict": self.verdict,
            "confidence": round(self.confidence, 2),
        }


@dataclass
class BenchmarkResult:
    analyzer_name: str
    n_samples: int
    predictions: List[SamplePrediction]
    report_default: metrics.BinaryClassificationReport
    report_best_f1: metrics.BinaryClassificationReport
    best_f1_threshold: float
    calibration_bins: List[Dict[str, float]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "analyzer": self.analyzer_name,
            "n_samples": self.n_samples,
            "metrics_at_0.5": self.report_default.to_dict(),
            "best_f1_threshold": round(self.best_f1_threshold, 4),
            "metrics_at_best_f1": self.report_best_f1.to_dict(),
            "calibration_bins": self.calibration_bins,
            "predictions": [p.to_dict() for p in self.predictions],
        }


def run_benchmark(
    analyzer: _Analyzer,
    samples: List[Sample],
    analyzer_name: str = "analyzer",
    threshold: float = 0.5,
) -> BenchmarkResult:
    """Run ``analyzer`` over ``samples`` and compute metrics."""
    predictions: List[SamplePrediction] = []
    for sample in samples:
        result = analyzer.analyze(sample.text)
        predictions.append(
            SamplePrediction(
                id=sample.id,
                label=sample.label,
                source=sample.source,
                ai_probability=result_to_ai_probability(result),
                verdict=result.verdict.value,
                confidence=result.confidence,
            )
        )

    labels = [p.label for p in predictions]
    scores = [p.ai_probability for p in predictions]

    report_default = metrics.binary_report(labels, scores, threshold=threshold)
    best_t, _ = metrics.best_threshold_by_f1(labels, scores)
    report_best = metrics.binary_report(labels, scores, threshold=best_t)

    return BenchmarkResult(
        analyzer_name=analyzer_name,
        n_samples=len(samples),
        predictions=predictions,
        report_default=report_default,
        report_best_f1=report_best,
        best_f1_threshold=best_t,
        calibration_bins=metrics.calibration_bins(labels, scores),
    )


def _build_analyzer(name: str) -> _Analyzer:
    """Construct an analyzer by name (heavy analyzers imported lazily)."""
    name = name.lower()
    if name == "nltk":
        from src.analyzers.nltk_analyzer import NLTKAnalyzer

        return NLTKAnalyzer(ngram_size=3)
    if name == "gpt2":
        from src.analyzers.gpt2_analyzer import GPT2Analyzer

        return GPT2Analyzer()
    if name == "ensemble":
        from src.analyzers.ensemble_analyzer import EnsembleAnalyzer

        return EnsembleAnalyzer()
    raise ValueError(f"Unknown analyzer {name!r}; expected nltk, gpt2, or ensemble")


def save_plots(result: BenchmarkResult, output_dir: Path) -> List[Path]:
    """Save ROC and reliability-diagram PNGs. Requires matplotlib.

    Returns the list of written files (empty if matplotlib is unavailable).
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - optional dependency path
        logger.warning("matplotlib unavailable; skipping plots: %s", exc)
        return []

    output_dir.mkdir(parents=True, exist_ok=True)
    labels = [p.label for p in result.predictions]
    scores = [p.ai_probability for p in result.predictions]
    written: List[Path] = []

    # ROC curve.
    fpr, tpr, _ = metrics.roc_curve(labels, scores)
    auc = result.report_default.roc_auc
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot(fpr, tpr, label=f"AUROC = {auc:.3f}")
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="chance")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title(f"ROC — {result.analyzer_name}")
    ax.legend(loc="lower right")
    roc_path = output_dir / f"roc_{result.analyzer_name}.png"
    fig.savefig(roc_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    written.append(roc_path)

    # Reliability diagram.
    bins = [b for b in result.calibration_bins if b["count"] > 0]
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="perfect")
    if bins:
        ax.plot(
            [b["mean_predicted"] for b in bins],
            [b["observed_fraction"] for b in bins],
            marker="o",
            label=f"ECE = {result.report_default.expected_calibration_error:.3f}",
        )
    ax.set_xlabel("Mean predicted AI-probability")
    ax.set_ylabel("Observed AI fraction")
    ax.set_title(f"Calibration — {result.analyzer_name}")
    ax.legend(loc="upper left")
    cal_path = output_dir / f"calibration_{result.analyzer_name}.png"
    fig.savefig(cal_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    written.append(cal_path)

    return written


def _format_summary(result: BenchmarkResult) -> str:
    r = result.report_default
    return (
        f"\n=== Benchmark: {result.analyzer_name} ({result.n_samples} samples) ===\n"
        f"Accuracy   : {r.accuracy:.3f}\n"
        f"Precision  : {r.precision:.3f}\n"
        f"Recall     : {r.recall:.3f}\n"
        f"F1         : {r.f1:.3f}\n"
        f"AUROC      : {r.roc_auc:.3f}\n"
        f"FPR (human flagged as AI): {r.false_positive_rate:.3f}\n"
        f"FNR (AI missed)          : {r.false_negative_rate:.3f}\n"
        f"ECE (calibration error)  : {r.expected_calibration_error:.3f}\n"
        f"Best-F1 threshold        : {result.best_f1_threshold:.3f} "
        f"(F1 ={result.report_best_f1.f1:.3f})\n"
    )


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark an AI-text detector.")
    parser.add_argument("--analyzer", default="nltk", choices=["nltk", "gpt2", "ensemble"])
    parser.add_argument("--dataset", default=None, help="Path to a JSONL dataset")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--output", default=None, help="Write full report JSON here")
    parser.add_argument("--plots", default=None, help="Directory for ROC/calibration PNGs")
    args = parser.parse_args(argv)

    samples = load_dataset(args.dataset)
    analyzer = _build_analyzer(args.analyzer)
    result = run_benchmark(analyzer, samples, analyzer_name=args.analyzer, threshold=args.threshold)

    print(_format_summary(result))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
        print(f"Wrote report to {args.output}")
    if args.plots:
        written = save_plots(result, Path(args.plots))
        for path in written:
            print(f"Wrote plot {path}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
