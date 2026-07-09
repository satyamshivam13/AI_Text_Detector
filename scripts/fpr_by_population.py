"""
Per-population false-positive rate
==================================

Runs an analyzer over a **human-only** corpus and reports the false-positive rate
(fraction of real people accused of using AI) *per population*, with Wilson 95%
confidence intervals.

Why per-population, and why confidence intervals
------------------------------------------------
An aggregate FPR hides who pays for it. Liang et al. (2023) showed commercial GPT
detectors flag non-native English writers far more often than native writers — a
detector can look accurate overall while being unusable for a group of people.
And with n≈90 per population, a point estimate of "5%" is compatible with a true
rate anywhere from ~2% to ~12%; reporting the interval keeps us honest.

Every sample is human-authored, so **any AI verdict is a false positive**.
``toefl_gpt4_polished`` is the exception: human-authored but machine-edited, so it
is reported separately and not treated as a plain false positive.

Usage
-----
    python scripts/fpr_by_population.py --analyzer binoculars
    python scripts/fpr_by_population.py --analyzer gpt2 --output docs/benchmarks/fpr_gpt2.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import Verdict  # noqa: E402
from src.evaluation.benchmark import _build_analyzer  # noqa: E402
from src.evaluation.dataset import load_dataset  # noqa: E402

_AI_VERDICTS = (Verdict.AI_GENERATED, Verdict.LIKELY_AI)

# Human-authored but machine-edited: genuinely ambiguous, not a plain FP.
AMBIGUOUS_POPULATIONS = {"toefl_gpt4_polished"}


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Tuple[float, float]:
    """Wilson score interval — well-behaved at small n and near 0."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, center - margin), min(1.0, center + margin))


def evaluate(analyzer, samples) -> Dict[str, dict]:
    by_pop: Dict[str, dict] = defaultdict(lambda: {"n": 0, "flagged": 0, "ids": []})
    total = len(samples)
    for i, sample in enumerate(samples, 1):
        result = analyzer.analyze(sample.text)
        bucket = by_pop[sample.source]
        bucket["n"] += 1
        if result.verdict in _AI_VERDICTS:
            bucket["flagged"] += 1
            bucket["ids"].append(sample.id)
        if i % 50 == 0:
            print(f"  {i}/{total} analyzed", flush=True)
    return by_pop


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Per-population false-positive rate.")
    parser.add_argument(
        "--analyzer", default="binoculars", choices=["nltk", "gpt2", "binoculars", "ensemble"]
    )
    parser.add_argument("--dataset", default="data/external/fairness_human.jsonl")
    parser.add_argument("--output", default=None)
    args = parser.parse_args(argv)

    samples = load_dataset(args.dataset)
    assert all(s.label == 0 for s in samples), "fairness corpus must be human-only"

    print(f"Analyzing {len(samples)} human samples with '{args.analyzer}' ...")
    by_pop = evaluate(_build_analyzer(args.analyzer), samples)

    rows = []
    for population in sorted(by_pop, key=lambda p: -by_pop[p]["flagged"] / max(by_pop[p]["n"], 1)):
        bucket = by_pop[population]
        n, flagged = bucket["n"], bucket["flagged"]
        fpr = flagged / n if n else 0.0
        lo, hi = wilson_interval(flagged, n)
        rows.append(
            {
                "population": population,
                "n": n,
                "flagged": flagged,
                "fpr": round(fpr, 4),
                "wilson95_lo": round(lo, 4),
                "wilson95_hi": round(hi, 4),
                "ambiguous": population in AMBIGUOUS_POPULATIONS,
            }
        )

    plain = [r for r in rows if not r["ambiguous"]]
    n_total = sum(r["n"] for r in plain)
    flagged_total = sum(r["flagged"] for r in plain)
    overall = flagged_total / n_total if n_total else 0.0
    lo, hi = wilson_interval(flagged_total, n_total)

    width = max(len(r["population"]) for r in rows) + 2
    print(f"\n=== False-positive rate by population — {args.analyzer} ===")
    print(f"{'population':<{width}}{'n':>5}{'flagged':>9}{'FPR':>8}   Wilson 95% CI")
    for r in rows:
        tag = "  (human-authored, GPT-4 edited)" if r["ambiguous"] else ""
        print(
            f"{r['population']:<{width}}{r['n']:>5}{r['flagged']:>9}{r['fpr']:>8.3f}"
            f"   [{r['wilson95_lo']:.3f}, {r['wilson95_hi']:.3f}]{tag}"
        )
    print(
        f"\nOVERALL (excluding ambiguous): {flagged_total}/{n_total} = {overall:.3f}"
        f"   [{lo:.3f}, {hi:.3f}]"
    )

    disparities = [r for r in plain if r["n"] >= 30]
    if len(disparities) >= 2:
        worst = max(disparities, key=lambda r: r["fpr"])
        best = min(disparities, key=lambda r: r["fpr"])
        print(f"\nWorst-served population: {worst['population']} (FPR {worst['fpr']:.3f})")
        print(f"Best-served population : {best['population']} (FPR {best['fpr']:.3f})")
        if best["fpr"] > 0:
            print(f"Disparity ratio        : {worst['fpr'] / best['fpr']:.1f}x")
        elif worst["fpr"] > 0:
            print("Disparity ratio        : infinite (best-served population never flagged)")

    payload = {
        "analyzer": args.analyzer,
        "overall_fpr": round(overall, 4),
        "overall_wilson95": [round(lo, 4), round(hi, 4)],
        "populations": rows,
    }
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
