"""
Text Processing Utilities
=========================

Comprehensive text preprocessing and feature extraction.
"""

from __future__ import annotations

import re
import string
from collections import Counter
from typing import Dict, List, Optional, Tuple

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

from src.models.result import TextMetrics
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


class TextProcessor:
    """Handles all text preprocessing and feature extraction."""

    _nltk_initialized: bool = False
    _stop_words: Optional[set] = None

    @classmethod
    def ensure_nltk_data(cls) -> None:
        """Download required NLTK data if not already present."""
        if cls._nltk_initialized:
            return

        required_packages = [
            "punkt",
            "punkt_tab",
            "stopwords",
            "brown",
            "averaged_perceptron_tagger",
        ]

        for package in required_packages:
            try:
                nltk.data.find(f"tokenizers/{package}" if "punkt" in package else package)
            except LookupError:
                try:
                    logger.info(f"Downloading NLTK package: {package}")
                    nltk.download(package, quiet=True)
                except Exception as e:
                    logger.warning(f"Failed to download {package}: {e}")

        cls._nltk_initialized = True

    @classmethod
    def get_stop_words(cls) -> set:
        """Get cached English stop words."""
        if cls._stop_words is None:
            cls.ensure_nltk_data()
            try:
                cls._stop_words = set(stopwords.words("english"))
            except Exception:
                logger.warning("Could not load stopwords, using default set")
                cls._stop_words = {
                    "the", "a", "an", "is", "are", "was", "were", "be", "been",
                    "being", "have", "has", "had", "do", "does", "did", "will",
                    "would", "could", "should", "may", "might", "can", "shall",
                    "to", "of", "in", "for", "on", "with", "at", "by", "from",
                    "as", "into", "through", "during", "before", "after", "above",
                    "below", "between", "and", "but", "or", "nor", "not", "so",
                    "yet", "both", "either", "neither", "each", "every", "all",
                    "any", "few", "more", "most", "other", "some", "such", "no",
                    "only", "own", "same", "than", "too", "very", "just", "because",
                    "this", "that", "these", "those", "i", "me", "my", "myself",
                    "we", "our", "ours", "you", "your", "he", "him", "his", "she",
                    "her", "it", "its", "they", "them", "their", "what", "which",
                    "who", "whom", "when", "where", "why", "how",
                }
        return cls._stop_words

    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw input text.

        Returns:
            Cleaned text string.
        """
        if not text or not text.strip():
            return ""

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())

        # Remove unusual unicode characters but keep basic punctuation
        text = re.sub(r"[^\x00-\x7F]+", " ", text)

        # Normalize quotes
        text = text.replace("\u2018", "'").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')

        # Remove excessive punctuation
        text = re.sub(r"([!?.]){3,}", r"\1\1", text)

        # Clean up spaces
        text = re.sub(r"\s+", " ", text).strip()

        return text

    @classmethod
    def tokenize_sentences(cls, text: str) -> List[str]:
        """
        Tokenize text into sentences.

        Args:
            text: Input text.

        Returns:
            List of sentence strings.
        """
        cls.ensure_nltk_data()
        try:
            sentences = sent_tokenize(text)
            return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            logger.warning(f"Sentence tokenization failed: {e}, using fallback")
            return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]

    @classmethod
    def tokenize_words(cls, text: str, remove_stopwords: bool = False,
                       remove_punctuation: bool = True, lowercase: bool = True) -> List[str]:
        """
        Tokenize text into words with configurable preprocessing.

        Args:
            text: Input text.
            remove_stopwords: Whether to remove stop words.
            remove_punctuation: Whether to remove punctuation tokens.
            lowercase: Whether to convert to lowercase.

        Returns:
            List of word tokens.
        """
        cls.ensure_nltk_data()

        if lowercase:
            text = text.lower()

        try:
            tokens = word_tokenize(text)
        except Exception as e:
            logger.warning(f"Word tokenization failed: {e}, using fallback")
            tokens = text.split()

        if remove_punctuation:
            tokens = [t for t in tokens if t not in string.punctuation and re.search(r"\w", t)]

        if remove_stopwords:
            stop_words = cls.get_stop_words()
            tokens = [t for t in tokens if t not in stop_words]

        return tokens

    @classmethod
    def compute_metrics(cls, text: str) -> TextMetrics:
        """
        Compute comprehensive text metrics.

        Args:
            text: Input text to analyze.

        Returns:
            TextMetrics object with computed values.
        """
        cleaned = cls.clean_text(text)

        if not cleaned:
            return TextMetrics()

        sentences = cls.tokenize_sentences(cleaned)
        all_words = cls.tokenize_words(cleaned, remove_punctuation=True)
        content_words = cls.tokenize_words(
            cleaned, remove_stopwords=True, remove_punctuation=True
        )

        total_words = len(all_words)
        unique_words = len(set(all_words))

        # Word frequencies (content words only)
        word_freq = Counter(content_words)

        # Sentence lengths
        sentence_lengths = [len(cls.tokenize_words(s, remove_punctuation=True)) for s in sentences]

        # Average word length
        avg_word_length = (
            sum(len(w) for w in all_words) / total_words if total_words > 0 else 0.0
        )

        # Average sentence length
        avg_sentence_length = (
            sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        )

        # Vocabulary richness (Yule's K approximation)
        vocabulary_richness = cls._compute_yules_k(all_words) if total_words > 0 else 0.0

        return TextMetrics(
            total_characters=len(cleaned),
            total_words=total_words,
            total_sentences=len(sentences),
            unique_words=unique_words,
            avg_word_length=round(avg_word_length, 2),
            avg_sentence_length=round(avg_sentence_length, 2),
            vocabulary_richness=round(vocabulary_richness, 4),
            word_frequencies=dict(word_freq.most_common(50)),
            sentence_lengths=sentence_lengths,
        )

    @staticmethod
    def _compute_yules_k(words: List[str]) -> float:
        """
        Compute Yule's K measure of vocabulary richness.

        Lower values indicate richer vocabulary.

        Args:
            words: List of word tokens.

        Returns:
            Yule's K value.
        """
        if not words:
            return 0.0

        freq_spectrum = Counter(Counter(words).values())
        n = len(words)

        if n <= 1:
            return 0.0

        m2 = sum(i * i * freq_spectrum[i] for i in freq_spectrum)

        try:
            k = 10000 * (m2 - n) / (n * n)
        except ZeroDivisionError:
            k = 0.0

        return max(0.0, k)

    @classmethod
    def compute_burstiness(cls, text: str) -> Tuple[float, Dict[str, float]]:
        """
        Compute burstiness score measuring word repetition patterns.

        Human text tends to have higher burstiness (bursty word usage)
        while AI text tends to be more uniform.

        Args:
            text: Input text.

        Returns:
            Tuple of (burstiness_score, word_burstiness_dict).
        """
        words = cls.tokenize_words(text, remove_stopwords=True, remove_punctuation=True)

        if len(words) < 5:
            return 0.0, {}

        word_counts = Counter(words)
        total = len(words)

        if total == 0:
            return 0.0, {}

        # Compute burstiness for each word
        frequencies = list(word_counts.values())
        mean_freq = sum(frequencies) / len(frequencies)

        if mean_freq == 0:
            return 0.0, {}

        # Variance of word frequencies
        variance = sum((f - mean_freq) ** 2 for f in frequencies) / len(frequencies)
        std_dev = variance ** 0.5

        # Burstiness: (std - mean) / (std + mean)
        # Range: [-1, 1], higher = more bursty = more human-like
        if (std_dev + mean_freq) == 0:
            burstiness = 0.0
        else:
            burstiness = (std_dev - mean_freq) / (std_dev + mean_freq)

        # Normalize to [0, 1] range
        normalized_burstiness = (burstiness + 1) / 2

        # Per-word burstiness
        word_burstiness = {}
        for word, count in word_counts.most_common(20):
            expected = total / len(word_counts)
            if expected > 0:
                word_burstiness[word] = count / expected

        return round(normalized_burstiness, 4), word_burstiness

    @classmethod
    def compute_sentence_variance(cls, text: str) -> float:
        """
        Compute variance in sentence lengths.

        AI text tends to have more uniform sentence lengths.

        Args:
            text: Input text.

        Returns:
            Coefficient of variation of sentence lengths.
        """
        sentences = cls.tokenize_sentences(text)

        if len(sentences) < 2:
            return 0.0

        lengths = [len(cls.tokenize_words(s, remove_punctuation=True)) for s in sentences]
        lengths = [l for l in lengths if l > 0]

        if not lengths:
            return 0.0

        mean_length = sum(lengths) / len(lengths)

        if mean_length == 0:
            return 0.0

        variance = sum((l - mean_length) ** 2 for l in lengths) / len(lengths)
        std_dev = variance ** 0.5

        # Coefficient of variation
        cv = std_dev / mean_length

        return round(cv, 4)