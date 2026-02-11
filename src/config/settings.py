"""
Application Settings
====================

Centralized configuration management using Pydantic.
All settings can be overridden via environment variables.
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
    smoothing_discount: float = 0.75
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
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)

    def __post_init__(self):
        """Load overrides from environment variables."""
        self.debug = os.getenv("AI_DETECTOR_DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("AI_DETECTOR_LOG_LEVEL", self.log_level)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()