"""
Calibrate the Binoculars decision boundary on a labelled corpus
===============================================================

The Binoculars *ratio* (observer log-perplexity / cross-perplexity) ranks
human vs machine text extremely well, but the value of the decision boundary is
corpus-dependent. ``BinocularsConfig.score_midpoint`` was originally fit on the
tiny bundled benchmark and does not transfer to real-world text.

This script fits the boundary **honestly**:

1. Compute the raw ratio for every sample (cached to JSON so re-runs are free).
2. Split the corpus 50/50, stratified by label, with a fixed seed.
3. Sweep candidate midpoints on the **calibration half** and pick the one with
   the best balanced accuracy.
4. Report performance on the **held-out half** — the number you can trust.

Usage
-----
    python scripts/calibrate_binoculars.py --dataset data/external/hc3_sample.jsonl
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.evaluation.dataset import load_dataset  # noqa: E402


def compute_ratios(dataset: str, cache_path: Path) -> List[Dict]:
    """Compute (or load cached) Binoculars ratios for every sample."""
    if cache_path.exists():
        print(f"Using cached ratios: {cache_path}")
        return json.loads(cache_path.read_text(encoding="utf-8"))

    from src.analyzers.binoculars_analyzer import BinocularsAnalyzer

    analyzer = BinocularsAnalyzer()
    rows = []
    samples = load_dataset(dataset)
    for i, sample in enumerate(samples, 1):
        ratio, _ = analyzer._compute_binoculars(sample.text)
        rows.append({"id": sample.id, "label": sample.label, "ratio": ratio})
        if i % 25 == 0:
            print(f"  {i}/{len(samples)} scored")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"Cached ratios -> {cache_path}")
    return rows


def stratified_split(rows: List[Dict], seed: int) -> Tuple[List[Dict], List[Dict]]:
    """Split 50/50 preserving class balance."""
    import random

    rng = random.Random(seed)
    calib, held = [], []
    for label in (0, 1):
        group = [r for r in rows if r["label"] == label]
        rng.shuffle(group)
        mid = len(group) // 2
        calib.extend(group[:mid])
        held.extend(group[mid:])
    return calib, held


def balanced_accuracy(rows: List[Dict], midpoint: float) -> float:
    """Lower ratio => AI. Balanced accuracy at a candidate midpoint."""
    tp = sum(1 for r in rows if r["label"] == 1 and r["ratio"] < midpoint)
    fn = sum(1 for r in rows if r["label"] == 1 and r["ratio"] >= midpoint)
    tn = sum(1 for r in rows if r["label"] == 0 and r["ratio"] >= midpoint)
    fp = sum(1 for r in rows if r["label"] == 0 and r["ratio"] < midpoint)
    tpr = tp / (tp + fn) if (tp + fn) else 0.0
    tnr = tn / (tn + fp) if (tn + fp) else 0.0
    return (tpr + tnr) / 2


def report(rows: List[Dict], midpoint: float, name: str) -> None:
    tp = sum(1 for r in rows if r["label"] == 1 and r["ratio"] < midpoint)
    fn = sum(1 for r in rows if r["label"] == 1 and r["ratio"] >= midpoint)
    tn = sum(1 for r in rows if r["label"] == 0 and r["ratio"] >= midpoint)
    fp = sum(1 for r in rows if r["label"] == 0 and r["ratio"] < midpoint)
    n = len(rows)
    print(
        f"\n{name} (n={n}, midpoint={midpoint:.4f}):\n"
        f"  accuracy = {(tp + tn) / n:.3f}\n"
        f"  FPR (human flagged AI) = {fp / (fp + tn) if (fp + tn) else 0:.3f}\n"
        f"  FNR (AI missed)        = {fn / (fn + tp) if (fn + tp) else 0:.3f}"
    )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fit the Binoculars decision boundary.")
    parser.add_argument("--dataset", default="data/external/hc3_sample.jsonl")
    parser.add_argument("--cache", default="data/external/hc3_binoculars_ratios.json")
    parser.add_argument("--seed", type=int, default=13)
    args = parser.parse_args(argv)

    rows = compute_ratios(args.dataset, Path(args.cache))
    human = sorted(r["ratio"] for r in rows if r["label"] == 0)
    ai = sorted(r["ratio"] for r in rows if r["label"] == 1)
    print(f"\nratio  human: min={human[0]:.4f} med={human[len(human)//2]:.4f} max={human[-1]:.4f}")
    print(f"ratio  ai   : min={ai[0]:.4f} med={ai[len(ai)//2]:.4f} max={ai[-1]:.4f}")

    calib, held = stratified_split(rows, args.seed)

    # Sweep candidate midpoints between the observed extremes.
    lo, hi = min(r["ratio"] for r in rows), max(r["ratio"] for r in rows)
    candidates = [lo + (hi - lo) * i / 2000 for i in range(2001)]
    best_mid = max(candidates, key=lambda m: balanced_accuracy(calib, m))

    print(f"\nFitted on calibration half (n={len(calib)}): midpoint = {best_mid:.4f}")
    report(calib, best_mid, "CALIBRATION half")
    report(held, best_mid, "HELD-OUT half  <-- trust this")
    print(f"\nSet BinocularsConfig.score_midpoint = {best_mid:.3f}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
