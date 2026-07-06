"""
Application Settings
====================

Centralized configuration using frozen ``dataclasses`` with an ``lru_cache``
singleton (:func:`get_settings`). A few runtime values can be overridden via
environment variables (see :meth:`Settings.__post_init__`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from functools import lru_cache
from typing import Optional


class DetectionMethod(str, Enum):
    """Available detection methods."""

    NLTK = "nltk"
    GPT2 = "gpt2"


class ConfidenceLevel(str, Enum):
    """Confidence level categories."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    VERY_LOW = "Very Low"


class Verdict(str, Enum):
    """Detection verdict categories."""

    AI_GENERATED = "AI-Generated"
    LIKELY_AI = "Likely AI-Generated"
    UNCERTAIN = "Uncertain"
    LIKELY_HUMAN = "Likely Human-Written"
    HUMAN_WRITTEN = "Human-Written"


@dataclass(frozen=True)
class ThresholdConfig:
    """Threshold configuration for detection decisions."""

    # Perplexity thresholds
    perplexity_very_low: float = 30.0
    perplexity_low: float = 60.0
    perplexity_medium: float = 150.0
    perplexity_high: float = 300.0

    # Burstiness thresholds
    burstiness_very_low: float = 0.10
    burstiness_low: float = 0.20
    burstiness_medium: float = 0.30
    burstiness_high: float = 0.45

    # Lexical diversity thresholds
    lexical_diversity_low: float = 0.30
    lexical_diversity_medium: float = 0.50
    lexical_diversity_high: float = 0.70

    # Minimum text length for reliable analysis
    min_text_length: int = 50
    recommended_text_length: int = 200
    optimal_text_length: int = 500


@dataclass(frozen=True)
class NLTKConfig:
    """Configuration for NLTK-based analyzer."""

    corpus_name: str = "brown"
    default_ngram_size: int = 3
    max_ngram_size: int = 5
    # Smoothing for the n-gram language model. ``wittenbell`` (interpolated
    # back-off) is the default: it discriminates well and scores in
    # milliseconds. ``kneserney`` gives slightly better modelling but is far
    # slower in NLTK; ``lidstone`` is additive add-k smoothing.
    smoothing_method: str = "wittenbell"  # one of: wittenbell, kneserney, lidstone
    smoothing_discount: float = 0.75  # used when smoothing_method == "kneserney"
    smoothing_gamma: float = 0.1  # used when smoothing_method == "lidstone"
    unk_cutoff: int = 2  # tokens seen fewer times fold into the <UNK> class
    vocabulary_size: int = 50000
    required_data: tuple = (
        "punkt",
        "punkt_tab",
        "stopwords",
        "brown",
        "averaged_perceptron_tagger",
    )


@dataclass(frozen=True)
class GPT2Config:
    """Configuration for GPT-2-based analyzer."""

    model_name: str = "gpt2"
    max_token_length: int = 1024
    stride: int = 512
    device: Optional[str] = None
    batch_size: int = 1
    cache_dir: Optional[str] = None


@dataclass(frozen=True)
class VisualizationConfig:
    """Configuration for visualization settings."""

    default_top_words: int = 10
    min_top_words: int = 5
    max_top_words: int = 20
    chart_height: int = 400
    chart_width: int = 700
    color_ai: str = "#ff4b4b"
    color_human: str = "#00cc66"
    color_uncertain: str = "#ffaa00"
    color_primary: str = "#667eea"
    color_secondary: str = "#764ba2"


@dataclass(frozen=True)
class EnsembleConfig:
    """Calibration and fusion configuration for the ensemble analyzer.

    Perplexity is mapped to a calibrated AI-probability with a per-analyzer
    logistic (see :mod:`src.analyzers.calibration`). The midpoint is the
    perplexity at which AI-probability is 0.5 — i.e. the decision boundary —
    and was chosen from the observed human/AI perplexity separation on the
    bundled benchmark. Re-run ``python -m src.evaluation.benchmark`` after
    changing these.
    """

    # GPT-2: lower perplexity => more AI. Human ~40-106, AI ~10-25 on benchmark.
    gpt2_ppl_midpoint: float = 30.0
    gpt2_ppl_slope: float = 0.15

    # Brown-corpus NLTK: higher perplexity => more AI (formal/atypical text).
    # Human median ~1200, AI median ~1900 on the benchmark, with overlap — a
    # deliberately weak signal, so it carries a smaller weight below.
    nltk_ppl_midpoint: float = 1550.0
    nltk_ppl_slope: float = 0.0015

    # Fusion weights. RoBERTa stays disabled until a fine-tuned checkpoint is
    # wired in; GPT-2 is the strongest signal and dominates the blend.
    weight_roberta: float = 0.0
    weight_gpt2: float = 0.75
    weight_nltk: float = 0.25

    # Verdict thresholds on the fused, calibrated AI-probability.
    ai_threshold: float = 0.70
    likely_ai_threshold: float = 0.55
    likely_human_threshold: float = 0.45
    human_threshold: float = 0.30


@dataclass
class Settings:
    """Main application settings."""

    app_name: str = "AI Text Detector"
    app_version: str = "2.0.0"
    debug: bool = False
    log_level: str = "INFO"

    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    nltk: NLTKConfig = field(default_factory=NLTKConfig)
    gpt2: GPT2Config = field(default_factory=GPT2Config)
    ensemble: EnsembleConfig = field(default_factory=EnsembleConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

    def __post_init__(self):
        """Load overrides from environment variables."""
        self.debug = os.getenv("AI_DETECTOR_DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("AI_DETECTOR_LOG_LEVEL", self.log_level)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
