"""
NLTK-Based Analyzer
====================

Text analysis using NLTK n-gram language models and statistical methods.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import List, Optional, Tuple

import nltk
from nltk.corpus import brown
from nltk.lm import MLE
from nltk.lm.preprocessing import padded_everygram_pipeline
from nltk.util import ngrams

from src.analyzers.base_analyzer import BaseAnalyzer
from src.config.settings import get_settings
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class NLTKAnalyzer(BaseAnalyzer):
    """Analyzer using NLTK n-gram language models."""

    def __init__(self, ngram_size: int = 3):
        super().__init__()
        self.ngram_size = ngram_size
        self._model: Optional[MLE] = None
        self._model_ngram_size: Optional[int] = None
        self.method_name = "NLTK N-gram"

    @property
    def model(self) -> MLE:
        """Lazy-load the language model."""
        if self._model is None or self._model_ngram_size != self.ngram_size:
            self._model = self._build_model(self.ngram_size)
            self._model_ngram_size = self.ngram_size
        return self._model

    def _build_model(self, n: int) -> MLE:
        """
        Build an n-gram language model from the Brown corpus.

        Args:
            n: N-gram size.

        Returns:
            Trained MLE model.
        """
        logger.info(f"Building {n}-gram language model from Brown corpus...")

        TextProcessor.ensure_nltk_data()

        try:
            corpus_sents = brown.sents()
        except Exception as e:
            logger.error(f"Failed to load Brown corpus: {e}")
            raise RuntimeError("Could not load Brown corpus. Run: nltk.download('brown')") from e

        # Preprocess corpus sentences
        processed_sents = [
            [word.lower() for word in sent]
            for sent in corpus_sents
        ]

        # Build padded n-gram pipeline
        train_data, padded_vocab = padded_everygram_pipeline(n, processed_sents)

        # Train model
        model = MLE(n)
        model.fit(train_data, padded_vocab)

        logger.info(
            f"Model built successfully. Vocabulary size: {len(model.vocab)}"
        )

        return model

    def set_ngram_size(self, n: int) -> None:
        """
        Update the n-gram size (triggers model rebuild on next use).

        Args:
            n: New n-gram size (2-5).
        """
        if n < 2 or n > 5:
            raise ValueError("N-gram size must be between 2 and 5")
        self.ngram_size = n

    def _compute_perplexity(self, text: str) -> float:
        """
        Compute perplexity of text using the n-gram model.

        Args:
            text: Input text.

        Returns:
            Perplexity score.
        """
        words = TextProcessor.tokenize_words(
            text, remove_punctuation=True, lowercase=True
        )

        if len(words) < self.ngram_size:
            return 100.0  # Default for very short texts

        model = self.model
        n = self.ngram_size

        # Generate n-grams from input text
        text_ngrams = list(ngrams(
            words,
            n,
            pad_left=True,
            pad_right=True,
            left_pad_symbol="<s>",
            right_pad_symbol="</s>",
        ))

        if not text_ngrams:
            return 100.0

        # Calculate cross-entropy
        total_log_prob = 0.0
        count = 0

        for ngram_tuple in text_ngrams:
            context = ngram_tuple[:-1]
            word = ngram_tuple[-1]

            try:
                prob = model.score(word, context)
                if prob > 0:
                    total_log_prob += math.log2(prob)
                    count += 1
                else:
                    # Small probability for unseen n-grams
                    total_log_prob += math.log2(1e-10)
                    count += 1
            except Exception:
                total_log_prob += math.log2(1e-10)
                count += 1

        if count == 0:
            return 100.0

        # Cross-entropy
        cross_entropy = -total_log_prob / count

        # Perplexity = 2^cross_entropy
        try:
            perplexity = math.pow(2, cross_entropy)
        except OverflowError:
            perplexity = float("inf")

        # Cap at reasonable maximum
        return min(perplexity, 10000.0)

    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """
        Perform NLTK-based analysis.

        Args:
            text: Cleaned input text.
            result: Partially populated result.

        Returns:
            Updated result with NLTK analysis.
        """
        result.method = f"NLTK {self.ngram_size}-gram"

        # 1. Compute perplexity
        logger.info("Computing perplexity...")
        result.perplexity = self._compute_perplexity(text)

        result.add_score(DetectionScore(
            name="Perplexity",
            value=result.perplexity,
            weight=0.40,
            interpretation=self._interpret_perplexity(result.perplexity),
            indicates_ai=result.perplexity < self.thresholds.perplexity_medium,
        ))

        # 2. Compute burstiness
        logger.info("Computing burstiness...")
        burstiness, word_burstiness = TextProcessor.compute_burstiness(text)
        result.burstiness = burstiness

        result.add_score(DetectionScore(
            name="Burstiness",
            value=result.burstiness,
            weight=0.25,
            interpretation=self._interpret_burstiness(result.burstiness),
            indicates_ai=result.burstiness < self.thresholds.burstiness_medium,
        ))

        # 3. Compute lexical diversity
        logger.info("Computing lexical diversity...")
        result.lexical_diversity = result.metrics.lexical_diversity

        result.add_score(DetectionScore(
            name="Lexical Diversity",
            value=result.lexical_diversity,
            weight=0.15,
            interpretation=self._interpret_lexical_diversity(result.lexical_diversity),
            indicates_ai=result.lexical_diversity < self.thresholds.lexical_diversity_medium,
        ))

        # 4. Compute sentence variance
        logger.info("Computing sentence variance...")
        result.sentence_variance = TextProcessor.compute_sentence_variance(text)

        result.add_score(DetectionScore(
            name="Sentence Variance",
            value=result.sentence_variance,
            weight=0.20,
            interpretation=self._interpret_sentence_variance(result.sentence_variance),
            indicates_ai=result.sentence_variance < 0.25,
        ))

        return result

    def _interpret_perplexity(self, value: float) -> str:
        """Generate interpretation for perplexity score."""
        t = self.thresholds
        if value < t.perplexity_very_low:
            return "Extremely predictable — strong AI indicator"
        elif value < t.perplexity_low:
            return "Very predictable — likely AI-generated"
        elif value < t.perplexity_medium:
            return "Moderately predictable — possible AI patterns"
        elif value < t.perplexity_high:
            return "Natural variation — likely human-written"
        else:
            return "Highly unpredictable — strong human indicator"

    def _interpret_burstiness(self, value: float) -> str:
        """Generate interpretation for burstiness score."""
        t = self.thresholds
        if value < t.burstiness_very_low:
            return "Very uniform word usage — strong AI indicator"
        elif value < t.burstiness_low:
            return "Low burstiness — likely AI-generated"
        elif value < t.burstiness_medium:
            return "Moderate burstiness — inconclusive"
        elif value < t.burstiness_high:
            return "Natural burstiness — likely human"
        else:
            return "High burstiness — strong human indicator"

    def _interpret_lexical_diversity(self, value: float) -> str:
        """Generate interpretation for lexical diversity."""
        t = self.thresholds
        if value < t.lexical_diversity_low:
            return "Very repetitive vocabulary"
        elif value < t.lexical_diversity_medium:
            return "Moderate vocabulary variety"
        elif value < t.lexical_diversity_high:
            return "Good vocabulary diversity"
        else:
            return "Very rich vocabulary"

    def _interpret_sentence_variance(self, value: float) -> str:
        """Generate interpretation for sentence variance."""
        if value < 0.15:
            return "Very uniform sentence structure — AI indicator"
        elif value < 0.30:
            return "Low variation in sentence length"
        elif value < 0.50:
            return "Moderate variation — natural range"
        else:
            return "High variation — human writing pattern"