"""Analyzer modules.

Only the lightweight analyzers (``BaseAnalyzer``, ``NLTKAnalyzer``) are imported
eagerly. The transformer-backed analyzers (``GPT2Analyzer``, ``RoBERTaAnalyzer``,
``EnsembleAnalyzer``) pull in ``torch``/``transformers`` and are imported lazily
on first access via :pep:`562`. This keeps the NLTK-only app (``app.py``) free of
the deep-learning stack so it can run — and deploy — without ``torch`` installed,
while ``from src.analyzers import GPT2Analyzer`` continues to work for callers
that need it.
"""

import importlib
from typing import TYPE_CHECKING

from src.analyzers.base_analyzer import BaseAnalyzer
from src.analyzers.nltk_analyzer import NLTKAnalyzer

if TYPE_CHECKING:  # pragma: no cover - import-time typing only
    from src.analyzers.ensemble_analyzer import EnsembleAnalyzer
    from src.analyzers.gpt2_analyzer import GPT2Analyzer
    from src.analyzers.roberta_analyzer import RoBERTaAnalyzer

__all__ = [
    "BaseAnalyzer",
    "NLTKAnalyzer",
    "GPT2Analyzer",
    "RoBERTaAnalyzer",
    "EnsembleAnalyzer",
]

_LAZY_MODULES = {
    "GPT2Analyzer": "src.analyzers.gpt2_analyzer",
    "RoBERTaAnalyzer": "src.analyzers.roberta_analyzer",
    "EnsembleAnalyzer": "src.analyzers.ensemble_analyzer",
}


def __getattr__(name: str):
    """Lazily import heavy (torch/transformers) analyzers on first access."""
    module_path = _LAZY_MODULES.get(name)
    if module_path is not None:
        return getattr(importlib.import_module(module_path), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return sorted(__all__)
