"""
Result Data Models
==================

Structured data models for analysis results using dataclasses.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.config.settings import ConfidenceLevel, Verdict


@dataclass
class TextMetrics:
    """Raw text metrics from analysis."""

    total_characters: int = 0
    total_words: int = 0
    total_sentences: int = 0
    unique_words: int = 0
    avg_word_length: float = 0.0
    avg_sentence_length: float = 0.0
    vocabulary_richness: float = 0.0
    word_frequencies: Dict[str, int] = field(default_factory=dict)
    sentence_lengths: List[int] = field(default_factory=list)

    @property
    def lexical_diversity(self) -> float:
        """Calculate lexical diversity (type-token ratio)."""
        if self.total_words == 0:
            return 0.0
        return self.unique_words / self.total_words

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        result = asdict(self)
        result["lexical_diversity"] = self.lexical_diversity
        return result


@dataclass
class DetectionScore:
    """Individual detection score with explanation."""

    name: str
    value: float
    weight: float = 1.0
    interpretation: str = ""
    indicates_ai: bool = False

    @property
    def weighted_value(self) -> float:
        """Get weighted score value."""
        return self.value * self.weight


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    # Core results
    verdict: Verdict = Verdict.UNCERTAIN
    confidence: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.LOW

    # Scores
    perplexity: float = 0.0
    burstiness: float = 0.0
    lexical_diversity: float = 0.0
    sentence_variance: float = 0.0

    # Detailed scores
    scores: List[DetectionScore] = field(default_factory=list)

    # Text metrics
    metrics: TextMetrics = field(default_factory=TextMetrics)

    # Metadata
    method: str = "unknown"
    analysis_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    text_length: int = 0
    warnings: List[str] = field(default_factory=list)
    explanation: str = ""

    @property
    def is_ai_generated(self) -> bool:
        """Check if text is classified as AI-generated."""
        return self.verdict in (Verdict.AI_GENERATED, Verdict.LIKELY_AI)

    @property
    def is_human_written(self) -> bool:
        """Check if text is classified as human-written."""
        return self.verdict in (Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN)

    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def add_score(self, score: DetectionScore) -> None:
        """Add a detection score."""
        self.scores.append(score)

    def get_score(self, name: str) -> Optional[DetectionScore]:
        """Return the first score with the given name, or None.

        Lets callers address scores by name instead of list position, so the
        order in which scores are added is not a load-bearing contract.
        """
        for score in self.scores:
            if score.name == name:
                return score
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "verdict": self.verdict.value,
            "confidence": round(self.confidence, 2),
            "confidence_level": self.confidence_level.value,
            "perplexity": round(self.perplexity, 2),
            "burstiness": round(self.burstiness, 4),
            "lexical_diversity": round(self.lexical_diversity, 4),
            "sentence_variance": round(self.sentence_variance, 4),
            "method": self.method,
            "analysis_time": round(self.analysis_time, 3),
            "timestamp": self.timestamp,
            "text_length": self.text_length,
            "warnings": self.warnings,
            "explanation": self.explanation,
            "metrics": self.metrics.to_dict(),
            "scores": [asdict(s) for s in self.scores],
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)
