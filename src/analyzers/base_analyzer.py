"""
Base Analyzer
=============

Abstract base class for all text analyzers.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Optional

from src.config.settings import (
    ConfidenceLevel,
    ThresholdConfig,
    Verdict,
    get_settings,
)
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class BaseAnalyzer(ABC):
    """Abstract base class for text analyzers."""

    def __init__(self):
        self.settings = get_settings()
        self.thresholds = self.settings.thresholds
        self.processor = TextProcessor()

    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyze text for AI-generated content.

        Args:
            text: Input text to analyze.

        Returns:
            AnalysisResult with detection results.
        """
        start_time = time.time()
        result = AnalysisResult()

        # Validate input
        cleaned_text = TextProcessor.clean_text(text)
        result.text_length = len(cleaned_text)

        if not cleaned_text:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 0.0
            result.confidence_level = ConfidenceLevel.VERY_LOW
            result.add_warning("Empty or invalid text provided.")
            result.explanation = "No text to analyze."
            return result

        if len(cleaned_text) < self.thresholds.min_text_length:
            result.add_warning(
                f"Text is very short ({len(cleaned_text)} chars). "
                f"Minimum {self.thresholds.min_text_length} characters recommended."
            )

        if len(cleaned_text) < self.thresholds.recommended_text_length:
            result.add_warning(
                f"For better accuracy, provide at least "
                f"{self.thresholds.recommended_text_length} characters."
            )

        try:
            # Compute text metrics
            result.metrics = TextProcessor.compute_metrics(cleaned_text)

            # Perform analysis
            result = self._perform_analysis(cleaned_text, result)

            # Determine verdict and confidence
            result = self._determine_verdict(result)

            # Generate explanation
            result.explanation = self._generate_explanation(result)

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 0.0
            result.confidence_level = ConfidenceLevel.VERY_LOW
            result.add_warning(f"Analysis error: {str(e)}")
            result.explanation = "An error occurred during analysis."

        result.analysis_time = round(time.time() - start_time, 3)
        result.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")

        logger.info(
            f"Analysis complete: verdict={result.verdict.value}, "
            f"confidence={result.confidence:.1f}%, "
            f"time={result.analysis_time}s"
        )

        return result

    @abstractmethod
    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """
        Perform the actual analysis. Must be implemented by subclasses.

        Args:
            text: Cleaned input text.
            result: Partially populated result object.

        Returns:
            Updated AnalysisResult.
        """
        ...

    def _determine_verdict(self, result: AnalysisResult) -> AnalysisResult:
        """
        Determine the overall verdict based on computed scores.

        Uses a weighted scoring system combining multiple factors.

        Args:
            result: Result with computed scores.

        Returns:
            Result with verdict and confidence.
        """
        t = self.thresholds
        scores = []

        # Score perplexity (lower = more likely AI)
        perp = result.perplexity
        if perp < t.perplexity_very_low:
            scores.append(("perplexity", 1.0, True))
        elif perp < t.perplexity_low:
            scores.append(("perplexity", 0.8, True))
        elif perp < t.perplexity_medium:
            scores.append(("perplexity", 0.4, True))
        elif perp < t.perplexity_high:
            scores.append(("perplexity", 0.2, False))
        else:
            scores.append(("perplexity", 0.0, False))

        # Score burstiness (lower = more likely AI)
        burst = result.burstiness
        if burst < t.burstiness_very_low:
            scores.append(("burstiness", 0.9, True))
        elif burst < t.burstiness_low:
            scores.append(("burstiness", 0.7, True))
        elif burst < t.burstiness_medium:
            scores.append(("burstiness", 0.4, True))
        elif burst < t.burstiness_high:
            scores.append(("burstiness", 0.15, False))
        else:
            scores.append(("burstiness", 0.0, False))

        # Score lexical diversity (lower = more likely AI, generally)
        ld = result.lexical_diversity
        if ld < t.lexical_diversity_low:
            scores.append(("lexical_diversity", 0.6, True))
        elif ld < t.lexical_diversity_medium:
            scores.append(("lexical_diversity", 0.35, True))
        elif ld < t.lexical_diversity_high:
            scores.append(("lexical_diversity", 0.15, False))
        else:
            scores.append(("lexical_diversity", 0.0, False))

        # Score sentence variance (lower = more likely AI)
        sv = result.sentence_variance
        if sv < 0.15:
            scores.append(("sentence_variance", 0.7, True))
        elif sv < 0.30:
            scores.append(("sentence_variance", 0.4, True))
        elif sv < 0.50:
            scores.append(("sentence_variance", 0.15, False))
        else:
            scores.append(("sentence_variance", 0.0, False))

        # Weighted average
        weights = {"perplexity": 0.40, "burstiness": 0.25,
                    "lexical_diversity": 0.15, "sentence_variance": 0.20}

        weighted_sum = sum(
            score * weights.get(name, 0.25) for name, score, _ in scores
        )
        total_weight = sum(weights.get(name, 0.25) for name, _, _ in scores)
        ai_probability = weighted_sum / total_weight if total_weight > 0 else 0.5

        # Apply text length penalty (short texts are less reliable)
        length_factor = min(1.0, result.text_length / self.thresholds.optimal_text_length)
        reliability = 0.4 + (0.6 * length_factor)

        # Determine verdict
        if ai_probability > 0.75:
            result.verdict = Verdict.AI_GENERATED
            result.confidence = min(95, ai_probability * 100 * reliability)
        elif ai_probability > 0.55:
            result.verdict = Verdict.LIKELY_AI
            result.confidence = min(85, ai_probability * 100 * reliability)
        elif ai_probability > 0.40:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 50.0 * reliability
        elif ai_probability > 0.25:
            result.verdict = Verdict.LIKELY_HUMAN
            result.confidence = min(85, (1 - ai_probability) * 100 * reliability)
        else:
            result.verdict = Verdict.HUMAN_WRITTEN
            result.confidence = min(95, (1 - ai_probability) * 100 * reliability)

        result.confidence = round(result.confidence, 1)

        # Confidence level
        if result.confidence >= 80:
            result.confidence_level = ConfidenceLevel.HIGH
        elif result.confidence >= 60:
            result.confidence_level = ConfidenceLevel.MEDIUM
        elif result.confidence >= 40:
            result.confidence_level = ConfidenceLevel.LOW
        else:
            result.confidence_level = ConfidenceLevel.VERY_LOW

        return result

    def _generate_explanation(self, result: AnalysisResult) -> str:
        """
        Generate a human-readable explanation of the results.

        Args:
            result: Complete analysis result.

        Returns:
            Explanation string.
        """
        t = self.thresholds
        parts = []

        # Perplexity explanation
        if result.perplexity < t.perplexity_low:
            parts.append(
                f"The text has very low perplexity ({result.perplexity:.1f}), "
                f"indicating highly predictable patterns typical of AI-generated content."
            )
        elif result.perplexity < t.perplexity_medium:
            parts.append(
                f"The text has moderate perplexity ({result.perplexity:.1f}), "
                f"showing somewhat predictable patterns."
            )
        else:
            parts.append(
                f"The text has high perplexity ({result.perplexity:.1f}), "
                f"showing natural variation typical of human writing."
            )

        # Burstiness explanation
        if result.burstiness < t.burstiness_low:
            parts.append(
                f"Word usage is very uniform (burstiness: {result.burstiness:.3f}), "
                f"which is characteristic of AI text."
            )
        elif result.burstiness > t.burstiness_high:
            parts.append(
                f"Word usage shows natural burstiness ({result.burstiness:.3f}), "
                f"consistent with human writing patterns."
            )

        # Lexical diversity
        ld = result.lexical_diversity
        if ld < t.lexical_diversity_low:
            parts.append(
                f"Vocabulary diversity is low ({ld:.2%}), "
                f"suggesting repetitive or formulaic language."
            )
        elif ld > t.lexical_diversity_high:
            parts.append(
                f"Vocabulary diversity is high ({ld:.2%}), "
                f"indicating rich and varied language use."
            )

        # Sentence variance
        if result.sentence_variance < 0.15:
            parts.append(
                "Sentence lengths are very uniform, a common AI characteristic."
            )
        elif result.sentence_variance > 0.50:
            parts.append(
                "Sentence lengths show high variation, typical of natural writing."
            )

        # Warnings
        if result.warnings:
            parts.append("⚠️ Note: " + " ".join(result.warnings))

        return " ".join(parts)