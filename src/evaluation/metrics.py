"""
Evaluation Metrics
==================

Pure-NumPy classification and calibration metrics for AI-text detection.

The positive class is **AI-generated** (label ``1``); the negative class is
**human-written** (label ``0``). Scores are AI-probabilities in ``[0, 1]``.

No scikit-learn dependency is introduced — every metric here is implemented
directly so the evaluation layer stays lightweight and auditable.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict, List, Sequence, Tuple

import numpy as np


@dataclass
class BinaryClassificationReport:
    """Structured metrics for a binary detector at a fixed threshold."""

    threshold: float
    n_samples: int
    n_positive: int
    n_negative: int

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int

    accuracy: float
    precision: float
    recall: float  # a.k.a. true positive rate / sensitivity
    f1: float
    specificity: float  # true negative rate

    false_positive_rate: float  # human text wrongly flagged as AI
    false_negative_rate: float  # AI text missed

    roc_auc: float
    expected_calibration_error: float

    def to_dict(self) -> Dict:
        return asdict(self)


def _as_arrays(labels: Sequence[int], scores: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
    y = np.asarray(labels, dtype=int)
    s = np.asarray(scores, dtype=float)
    if y.shape != s.shape:
        raise ValueError("labels and scores must have the same length")
    if y.size == 0:
        raise ValueError("cannot compute metrics on an empty dataset")
    if not np.all((y == 0) | (y == 1)):
        raise ValueError("labels must be 0 (human) or 1 (AI)")
    if np.any((s < 0) | (s > 1)):
        raise ValueError("scores must be AI-probabilities in [0, 1]")
    return y, s


def confusion_counts(
    labels: Sequence[int], scores: Sequence[float], threshold: float = 0.5
) -> Tuple[int, int, int, int]:
    """Return (tp, fp, tn, fn) for ``score >= threshold`` => predicted AI."""
    y, s = _as_arrays(labels, scores)
    pred = (s >= threshold).astype(int)
    tp = int(np.sum((pred == 1) & (y == 1)))
    fp = int(np.sum((pred == 1) & (y == 0)))
    tn = int(np.sum((pred == 0) & (y == 0)))
    fn = int(np.sum((pred == 0) & (y == 1)))
    return tp, fp, tn, fn


def roc_curve(
    labels: Sequence[int], scores: Sequence[float]
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute the ROC curve.

    Returns ``(fpr, tpr, thresholds)`` with points sorted by decreasing
    threshold, suitable for plotting or AUROC integration.
    """
    y, s = _as_arrays(labels, scores)
    # Sort by score descending.
    order = np.argsort(-s, kind="mergesort")
    y = y[order]
    s = s[order]

    p = np.sum(y == 1)
    n = np.sum(y == 0)
    if p == 0 or n == 0:
        # Degenerate: only one class present. ROC is undefined; return trivial.
        return np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([1.0, 0.0])

    tps = np.cumsum(y == 1)
    fps = np.cumsum(y == 0)

    # Keep the last index of each distinct score (threshold boundaries).
    distinct = np.where(np.diff(s) != 0)[0]
    idx = np.r_[distinct, s.size - 1]

    tpr = np.r_[0.0, tps[idx] / p]
    fpr = np.r_[0.0, fps[idx] / n]
    thresholds = np.r_[np.inf, s[idx]]
    return fpr, tpr, thresholds


def roc_auc(labels: Sequence[int], scores: Sequence[float]) -> float:
    """Area under the ROC curve via the Mann-Whitney U statistic.

    Robust to ties. Returns ``0.5`` when only one class is present (undefined).
    """
    y, s = _as_arrays(labels, scores)
    pos = s[y == 1]
    neg = s[y == 0]
    if pos.size == 0 or neg.size == 0:
        return 0.5
    # Rank-based AUROC (handles ties via average ranks).
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(s.size, dtype=float)
    sorted_scores = s[order]
    i = 0
    while i < s.size:
        j = i
        while j + 1 < s.size and sorted_scores[j + 1] == sorted_scores[i]:
            j += 1
        avg_rank = (i + j) / 2.0 + 1.0  # 1-based average rank
        ranks[order[i : j + 1]] = avg_rank
        i = j + 1
    sum_ranks_pos = np.sum(ranks[y == 1])
    n_pos = pos.size
    n_neg = neg.size
    auc = (sum_ranks_pos - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg)
    return float(auc)


def calibration_bins(
    labels: Sequence[int], scores: Sequence[float], n_bins: int = 10
) -> List[Dict[str, float]]:
    """Reliability-diagram bins.

    Each bin reports mean predicted AI-probability vs observed AI fraction.
    """
    y, s = _as_arrays(labels, scores)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    bins: List[Dict[str, float]] = []
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        if b == n_bins - 1:
            mask = (s >= lo) & (s <= hi)
        else:
            mask = (s >= lo) & (s < hi)
        count = int(np.sum(mask))
        if count == 0:
            bins.append(
                {
                    "bin_lower": float(lo),
                    "bin_upper": float(hi),
                    "count": 0,
                    "mean_predicted": float("nan"),
                    "observed_fraction": float("nan"),
                }
            )
            continue
        bins.append(
            {
                "bin_lower": float(lo),
                "bin_upper": float(hi),
                "count": count,
                "mean_predicted": float(np.mean(s[mask])),
                "observed_fraction": float(np.mean(y[mask])),
            }
        )
    return bins


def expected_calibration_error(
    labels: Sequence[int], scores: Sequence[float], n_bins: int = 10
) -> float:
    """Expected Calibration Error (weighted |confidence - accuracy|)."""
    y, s = _as_arrays(labels, scores)
    total = y.size
    ece = 0.0
    for b in calibration_bins(labels, scores, n_bins=n_bins):
        if b["count"] == 0:
            continue
        ece += (b["count"] / total) * abs(b["mean_predicted"] - b["observed_fraction"])
    return float(ece)


def binary_report(
    labels: Sequence[int], scores: Sequence[float], threshold: float = 0.5
) -> BinaryClassificationReport:
    """Compute a full metrics report at a fixed decision threshold."""
    y, _ = _as_arrays(labels, scores)
    tp, fp, tn, fn = confusion_counts(labels, scores, threshold)

    n = tp + fp + tn + fn
    n_pos = tp + fn
    n_neg = tn + fp

    def _safe(numer: float, denom: float) -> float:
        return float(numer / denom) if denom else 0.0

    accuracy = _safe(tp + tn, n)
    precision = _safe(tp, tp + fp)
    recall = _safe(tp, tp + fn)
    specificity = _safe(tn, tn + fp)
    f1 = _safe(2 * precision * recall, precision + recall)

    return BinaryClassificationReport(
        threshold=float(threshold),
        n_samples=int(n),
        n_positive=int(n_pos),
        n_negative=int(n_neg),
        true_positives=tp,
        false_positives=fp,
        true_negatives=tn,
        false_negatives=fn,
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        specificity=specificity,
        false_positive_rate=_safe(fp, fp + tn),
        false_negative_rate=_safe(fn, fn + tp),
        roc_auc=roc_auc(labels, scores),
        expected_calibration_error=expected_calibration_error(labels, scores),
    )


def best_threshold_by_f1(labels: Sequence[int], scores: Sequence[float]) -> Tuple[float, float]:
    """Return ``(threshold, f1)`` maximising F1 over candidate thresholds."""
    _as_arrays(labels, scores)
    candidates = sorted(set([0.0] + list(np.asarray(scores, dtype=float)) + [1.0]))
    best_t, best_f1 = 0.5, -1.0
    for t in candidates:
        rep = binary_report(labels, scores, threshold=t)
        if rep.f1 > best_f1:
            best_f1, best_t = rep.f1, t
    return float(best_t), float(best_f1)
