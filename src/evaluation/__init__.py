"""Evaluation and benchmarking for AI-text detectors.

This package provides the measurement layer the detector previously lacked:

* :mod:`src.evaluation.metrics` — classification and calibration metrics
  (accuracy, precision/recall/F1, ROC/AUROC, false-positive/negative rates,
  reliability bins and expected calibration error), implemented in pure NumPy.
* :mod:`src.evaluation.dataset` — loader for the bundled, honestly-labelled
  benchmark corpus under ``data/benchmark/``.
* :mod:`src.evaluation.benchmark` — runs an analyzer over a labelled dataset and
  produces a structured, reproducible report.

The bundled dataset is intentionally small and is meant for regression and
calibration checks, not as an authoritative accuracy claim. See
``data/benchmark/README.md``.
"""

from src.evaluation.metrics import (
    BinaryClassificationReport,
    binary_report,
    expected_calibration_error,
    roc_auc,
)

__all__ = [
    "BinaryClassificationReport",
    "binary_report",
    "expected_calibration_error",
    "roc_auc",
]
