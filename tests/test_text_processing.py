"""
Tests for text processing utilities.
"""

import pytest
from src.utils.text_processing import TextProcessor


class TestTextCleaning:
    """Tests for text cleaning functionality."""

    def test_clean_empty_text(self):
        assert TextProcessor.clean_text("") == ""

    def test_clean_whitespace_only(self):
        assert TextProcessor.clean_text("   \n\t  ") == ""

    def test_clean_normalizes_whitespace(self):
        result = TextProcessor.clean_text("hello   world\n\ntest")
        assert "  " not in result
        assert result == "hello world test"

    def test_clean_preserves_basic_punctuation(self):
        result = TextProcessor.clean_text("Hello, world! How are you?")
        assert "," in result
        assert "!" in result
        assert "?" in result

    def test_clean_reduces_excessive_punctuation(self):
        result = TextProcessor.clean_text("Wow!!!!! Really?????")
        assert "!!!!!" not in result
        assert "?????" not in result

    def test_clean_normalizes_quotes(self):
        result = TextProcessor.clean_text("He said \u201chello\u201d")
        assert '"' in result


class TestTokenization:
    """Tests for tokenization functionality."""

    def test_sentence_tokenization(self, sample_ai_text):
        sentences = TextProcessor.tokenize_sentences(sample_ai_text)
        assert isinstance(sentences, list)
        assert len(sentences) >= 1
        assert all(isinstance(s, str) for s in sentences)

    def test_sentence_tokenization_empty(self):
        sentences = TextProcessor.tokenize_sentences("")
        assert sentences == [] or sentences == [""]

    def test_word_tokenization(self, sample_ai_text):
        words = TextProcessor.tokenize_words(sample_ai_text)
        assert isinstance(words, list)
        assert len(words) > 0
        assert all(isinstance(w, str) for w in words)

    def test_word_tokenization_lowercase(self):
        words = TextProcessor.tokenize_words("Hello World", lowercase=True)
        assert all(w == w.lower() for w in words)

    def test_word_tokenization_remove_stopwords(self):
        words = TextProcessor.tokenize_words(
            "The cat is on the mat",
            remove_stopwords=True,
            remove_punctuation=True,
        )
        stop_words = TextProcessor.get_stop_words()
        assert not any(w in stop_words for w in words)

    def test_word_tokenization_remove_punctuation(self):
        words = TextProcessor.tokenize_words(
            "Hello, world! Test.",
            remove_punctuation=True,
        )
        assert "," not in words
        assert "!" not in words
        assert "." not in words


class TestMetrics:
    """Tests for text metrics computation."""

    def test_compute_metrics_basic(self, sample_ai_text):
        metrics = TextProcessor.compute_metrics(sample_ai_text)
        assert metrics.total_characters > 0
        assert metrics.total_words > 0
        assert metrics.total_sentences >= 1
        assert metrics.unique_words > 0
        assert metrics.avg_word_length > 0
        assert metrics.avg_sentence_length > 0

    def test_compute_metrics_empty(self):
        metrics = TextProcessor.compute_metrics("")
        assert metrics.total_characters == 0
        assert metrics.total_words == 0

    def test_lexical_diversity(self, sample_ai_text):
        metrics = TextProcessor.compute_metrics(sample_ai_text)
        assert 0.0 <= metrics.lexical_diversity <= 1.0

    def test_lexical_diversity_repetitive(self, repetitive_text):
        metrics = TextProcessor.compute_metrics(repetitive_text)
        assert metrics.lexical_diversity < 0.5

    def test_word_frequencies(self, sample_ai_text):
        metrics = TextProcessor.compute_metrics(sample_ai_text)
        assert isinstance(metrics.word_frequencies, dict)
        assert len(metrics.word_frequencies) > 0
        assert all(isinstance(v, int) and v > 0 for v in metrics.word_frequencies.values())

    def test_sentence_lengths(self, sample_ai_text):
        metrics = TextProcessor.compute_metrics(sample_ai_text)
        assert isinstance(metrics.sentence_lengths, list)
        assert all(isinstance(l, int) and l >= 0 for l in metrics.sentence_lengths)


class TestBurstiness:
    """Tests for burstiness computation."""

    def test_burstiness_range(self, sample_ai_text):
        burstiness, word_burstiness = TextProcessor.compute_burstiness(sample_ai_text)
        assert 0.0 <= burstiness <= 1.0

    def test_burstiness_short_text(self):
        burstiness, _ = TextProcessor.compute_burstiness("Hi")
        assert burstiness == 0.0

    def test_burstiness_returns_word_dict(self, sample_ai_text):
        _, word_burstiness = TextProcessor.compute_burstiness(sample_ai_text)
        assert isinstance(word_burstiness, dict)

    def test_burstiness_empty(self):
        burstiness, word_burstiness = TextProcessor.compute_burstiness("")
        assert burstiness == 0.0
        assert word_burstiness == {}


class TestSentenceVariance:
    """Tests for sentence variance computation."""

    def test_variance_range(self, sample_ai_text):
        variance = TextProcessor.compute_sentence_variance(sample_ai_text)
        assert variance >= 0.0

    def test_variance_single_sentence(self):
        variance = TextProcessor.compute_sentence_variance("Just one sentence here.")
        assert variance == 0.0

    def test_variance_uniform_sentences(self):
        text = "I am here. You are there. We are fine. They are good."
        variance = TextProcessor.compute_sentence_variance(text)
        assert variance < 0.3  # Should be low for uniform sentences

    def test_variance_mixed_sentences(self):
        text = (
            "Short. "
            "This is a much longer sentence with many more words in it that goes on and on. "
            "Medium length here. "
            "Another very very very long sentence that contains a large number of different words and phrases."
        )
        variance = TextProcessor.compute_sentence_variance(text)
        assert variance > 0.3  # Should be higher for mixed lengths