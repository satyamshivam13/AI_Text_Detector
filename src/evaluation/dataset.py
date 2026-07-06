"""
Benchmark Dataset Loader
========================

Loads the bundled, labelled benchmark corpus (JSONL) used to measure the
detector. Each line is an object: ``{"id", "label", "source", "text"}`` where
``label`` is ``"human"`` or ``"ai"``.

The bundled corpus is deliberately small and is meant for regression and
calibration checks, not as an authoritative accuracy benchmark. Point the loader
at a larger JSONL of the same shape to evaluate on your own data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# data/benchmark/samples.jsonl relative to the repository root.
DEFAULT_DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "benchmark" / "samples.jsonl"

_LABEL_TO_INT = {"human": 0, "ai": 1}


@dataclass(frozen=True)
class Sample:
    """One labelled benchmark example."""

    id: str
    label: int  # 0 = human, 1 = AI
    source: str
    text: str

    @property
    def is_ai(self) -> bool:
        return self.label == 1


def load_dataset(path: Optional[Path | str] = None) -> List[Sample]:
    """Load labelled samples from a JSONL file.

    Args:
        path: Path to a JSONL dataset. Defaults to the bundled corpus.

    Returns:
        List of :class:`Sample`.

    Raises:
        FileNotFoundError: If the dataset file does not exist.
        ValueError: If a record is malformed or has an unknown label.
    """
    dataset_path = Path(path) if path is not None else DEFAULT_DATASET_PATH
    if not dataset_path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found: {dataset_path}")

    samples: List[Sample] = []
    with dataset_path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc

            label_raw = str(record.get("label", "")).lower()
            if label_raw not in _LABEL_TO_INT:
                raise ValueError(
                    f"Unknown label {record.get('label')!r} on line {line_no}; "
                    f"expected one of {sorted(_LABEL_TO_INT)}"
                )
            text = record.get("text", "")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Empty or non-string text on line {line_no}")

            samples.append(
                Sample(
                    id=str(record.get("id", f"sample-{line_no}")),
                    label=_LABEL_TO_INT[label_raw],
                    source=str(record.get("source", "unknown")),
                    text=text,
                )
            )

    if not samples:
        raise ValueError(f"Dataset {dataset_path} contained no samples")
    return samples
