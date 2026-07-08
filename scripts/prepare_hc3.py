"""
Prepare an HC3 evaluation set
=============================

Downloads a slice of the public **HC3** corpus (Human ChatGPT Comparison Corpus,
``Hello-SimpleAI/HC3``) and converts it into the JSONL schema this project's
benchmark runner expects::

    {"id": ..., "label": "human"|"ai", "source": ..., "text": ...}

Why this exists
---------------
The bundled ``data/benchmark/samples.jsonl`` is 24 clean, in-distribution
samples — useful for regression/calibration checks, useless as an accuracy
claim. HC3 is a large, real, out-of-distribution corpus (real human answers from
Reddit/finance/medicine/open-QA vs. ChatGPT answers), so it gives the detector an
honest test.

The downloaded corpus is **not committed** (third-party data, own licence). Only
this script and the resulting metrics live in the repo, so anyone can reproduce.

Usage
-----
    python scripts/prepare_hc3.py                       # 100 per class
    python scripts/prepare_hc3.py --per-class 250 --split reddit_eli5

Then benchmark against it:

    python -m src.evaluation.benchmark --analyzer ensemble \
        --dataset data/external/hc3_sample.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import urllib.request
from pathlib import Path
from typing import Iterator, List

HC3_BASE = "https://huggingface.co/datasets/Hello-SimpleAI/HC3/resolve/main"
DEFAULT_OUT = Path("data/external/hc3_sample.jsonl")

# Splits available upstream. "all" mixes every domain.
SPLITS = ("all", "reddit_eli5", "open_qa", "finance", "medicine")


def _stream_lines(url: str) -> Iterator[str]:
    """Stream a remote JSONL file line by line (so we can stop early)."""
    request = urllib.request.Request(url, headers={"User-Agent": "ai-text-detector/2.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        for raw in response:
            yield raw.decode("utf-8", errors="replace")


def _clean(text: str) -> str:
    """Collapse whitespace; HC3 answers contain newlines and stray spacing."""
    return " ".join(text.split()).strip()


def build_samples(split: str, per_class: int, min_chars: int, seed: int) -> List[dict]:
    """Collect a balanced human/AI sample from the HC3 split."""
    url = f"{HC3_BASE}/{split}.jsonl"
    human: List[dict] = []
    ai: List[dict] = []

    for line in _stream_lines(url):
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue

        source = record.get("source", split)

        if len(human) < per_class:
            for answer in record.get("human_answers") or []:
                text = _clean(answer)
                if len(text) >= min_chars:
                    human.append({"label": "human", "source": f"hc3-{source}", "text": text})
                    break

        if len(ai) < per_class:
            for answer in record.get("chatgpt_answers") or []:
                text = _clean(answer)
                if len(text) >= min_chars:
                    ai.append({"label": "ai", "source": f"hc3-{source}", "text": text})
                    break

        if len(human) >= per_class and len(ai) >= per_class:
            break

    if len(human) < per_class or len(ai) < per_class:
        raise RuntimeError(
            f"Only collected {len(human)} human / {len(ai)} ai samples "
            f"(wanted {per_class} each). Try a different --split or lower --min-chars."
        )

    samples = []
    for i, record in enumerate(human):
        samples.append({"id": f"hc3-human-{i:04d}", **record})
    for i, record in enumerate(ai):
        samples.append({"id": f"hc3-ai-{i:04d}", **record})

    random.Random(seed).shuffle(samples)
    return samples


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build an HC3 evaluation JSONL.")
    parser.add_argument("--split", default="all", choices=SPLITS)
    parser.add_argument("--per-class", type=int, default=100)
    parser.add_argument(
        "--min-chars", type=int, default=200, help="matches the tool's recommended minimum"
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    print(f"Streaming HC3 split={args.split} ...")
    samples = build_samples(args.split, args.per_class, args.min_chars, args.seed)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")

    n_ai = sum(1 for s in samples if s["label"] == "ai")
    print(f"Wrote {len(samples)} samples ({len(samples) - n_ai} human / {n_ai} ai) to {out_path}")
    print(
        f"Benchmark it:\n  python -m src.evaluation.benchmark --analyzer ensemble --dataset {out_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
