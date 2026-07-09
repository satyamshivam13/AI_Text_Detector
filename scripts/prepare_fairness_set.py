"""
Build a human-only corpus for per-population false-positive-rate evaluation
===========================================================================

Every sample here is **written by a human**. Therefore *any* AI verdict is a
false positive, by construction. This is the measurement that matters ethically:
a detector can be 100% accurate on a balanced benchmark and still systematically
accuse one group of people.

Populations
-----------
Essay populations come from Liang et al., 2023, *"GPT detectors are biased
against non-native English writers"* (github.com/Weixin-Liang/ChatGPT-Detector-Bias):

* ``toefl_nonnative``   — 91 TOEFL essays by **non-native** English writers.
                          The canonical harm case.
* ``student_us_8th``    — 88 US 8th-grade student essays (native, young writers).
* ``college_admission`` — 70 US college admission essays.
* ``cs224n_student``    — 145 Stanford CS224N final essays (technical writing).
* ``toefl_gpt4_polished`` — the same 91 TOEFL essays, **polished by GPT-4**.
                          Human-authored content, machine-edited: a genuinely
                          ambiguous case, reported separately and NOT counted as
                          a plain false positive.

Domain populations come from HC3 (real human answers, no LLM involvement):
``hc3_reddit_eli5``, ``hc3_open_qa``, ``hc3_finance``, ``hc3_medicine``,
``hc3_wiki_csai``.

Neither corpus is redistributed — only this script and the resulting metrics.

Usage
-----
    python scripts/prepare_fairness_set.py
    python scripts/fpr_by_population.py --analyzer binoculars
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path
from typing import Dict, List

BIAS_BASE = (
    "https://raw.githubusercontent.com/Weixin-Liang/ChatGPT-Detector-Bias/main/"
    "Data_and_Results/Human_Data"
)
HC3_BASE = "https://huggingface.co/datasets/Hello-SimpleAI/HC3/resolve/main"
DEFAULT_OUT = Path("data/external/fairness_human.jsonl")

# population -> upstream folder (Liang et al.)
ESSAY_POPULATIONS: Dict[str, str] = {
    "toefl_nonnative": "TOEFL_real_91",
    "student_us_8th": "HewlettStudentEssay_real_88",
    "college_admission": "CollegeEssay_real_70",
    "cs224n_student": "CS224N_real_145",
    "toefl_gpt4_polished": "TOEFL_gpt4polished_91",
}

HC3_DOMAINS = ("reddit_eli5", "open_qa", "finance", "medicine", "wiki_csai")


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ai-text-detector/2.1"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def _clean(text: str) -> str:
    return " ".join(text.split()).strip()


def fetch_essays(min_chars: int) -> List[dict]:
    samples: List[dict] = []
    for population, folder in ESSAY_POPULATIONS.items():
        raw = json.loads(_get(f"{BIAS_BASE}/{folder}/data.json"))
        kept = 0
        for i, record in enumerate(raw):
            text = _clean(record.get("document", ""))
            if len(text) < min_chars:
                continue
            samples.append(
                {
                    "id": f"{population}-{kept:04d}",
                    "label": "human",
                    "source": population,
                    "text": text,
                }
            )
            kept += 1
        print(f"  {population:22s} {kept:4d} essays")
    return samples


def fetch_hc3_humans(per_domain: int, min_chars: int) -> List[dict]:
    samples: List[dict] = []
    for domain in HC3_DOMAINS:
        request = urllib.request.Request(
            f"{HC3_BASE}/{domain}.jsonl", headers={"User-Agent": "ai-text-detector/2.1"}
        )
        kept = 0
        with urllib.request.urlopen(request, timeout=60) as response:
            for raw in response:
                if kept >= per_domain:
                    break
                try:
                    record = json.loads(raw.decode("utf-8", errors="replace"))
                except json.JSONDecodeError:
                    continue
                for answer in record.get("human_answers") or []:
                    text = _clean(answer)
                    if len(text) >= min_chars:
                        samples.append(
                            {
                                "id": f"hc3_{domain}-{kept:04d}",
                                "label": "human",
                                "source": f"hc3_{domain}",
                                "text": text,
                            }
                        )
                        kept += 1
                        break
        print(f"  hc3_{domain:18s} {kept:4d} answers")
    return samples


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the human-only fairness corpus.")
    parser.add_argument("--per-domain", type=int, default=60, help="HC3 humans per domain")
    parser.add_argument("--min-chars", type=int, default=200)
    parser.add_argument("--output", default=str(DEFAULT_OUT))
    args = parser.parse_args(argv)

    print("Fetching essay populations (Liang et al. 2023) ...")
    samples = fetch_essays(args.min_chars)
    print("Fetching HC3 human answers by domain ...")
    samples += fetch_hc3_humans(args.per_domain, args.min_chars)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for sample in samples:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")

    print(
        f"\nWrote {len(samples)} human samples across "
        f"{len({s['source'] for s in samples})} populations -> {out_path}"
    )
    print("All samples are human-authored: any AI verdict is a false positive.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
