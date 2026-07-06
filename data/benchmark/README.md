# Benchmark Dataset

A small, honestly-labelled corpus used to **measure** the detector — the
evaluation layer the project previously lacked.

## Format

`samples.jsonl` — one JSON object per line:

```json
{"id": "human-01", "label": "human", "source": "handwritten-casual", "text": "..."}
{"id": "ai-01",    "label": "ai",    "source": "llm-formal",        "text": "..."}
```

- `label` is `"human"` or `"ai"` (the positive/AI class is `1`).
- `source` is a free-text provenance tag.

## Provenance and honesty

- **Human** samples are original casual/idiosyncratic prose written for this
  repository (personal notes, reviews, rants, journal entries).
- **AI** samples are representative of the formal, hedged, list-structured style
  produced by general-purpose LLMs.

This set is **intentionally small (24 samples)** and stylistically clean. It is
designed for:

- **regression testing** — catching accuracy/calibration drift when thresholds
  or fusion weights change, and
- **calibration checks** — is a "70% AI" score right ~70% of the time?

It is **not** an authoritative accuracy benchmark and must not be cited as one.
Real-world text (edited AI, paraphrased, mixed, ESL, technical) is far harder.
For meaningful numbers, evaluate on a large public benchmark (e.g. RAID, HC3) by
pointing the runner at a JSONL of the same shape:

```bash
python -m src.evaluation.benchmark --analyzer ensemble --dataset path/to/your.jsonl
```

## Running

```bash
python -m src.evaluation.benchmark --analyzer nltk
python -m src.evaluation.benchmark --analyzer ensemble --output report.json --plots out/
```

Reported metrics: accuracy, precision, recall, F1, AUROC, false-positive rate
(human wrongly flagged as AI), false-negative rate, and expected calibration
error, plus the F1-optimal threshold and a reliability diagram.
