"""
Shared test fixtures and configuration.
"""

import pytest
import sys
import os

# Ensure src is on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


@pytest.fixture
def sample_ai_text():
    """Sample AI-generated text for testing."""
    return (
        "The advancement of artificial intelligence has fundamentally transformed "
        "the landscape of modern technology. Machine learning algorithms have "
        "demonstrated remarkable capabilities across diverse domains including "
        "natural language processing, computer vision, and autonomous systems. "
        "The integration of these technologies into everyday applications has "
        "created unprecedented opportunities for innovation and efficiency "
        "improvements in virtually every sector of the global economy."
    )


@pytest.fixture
def sample_human_text():
    """Sample human-written text for testing."""
    return (
        "So I was trying to fix my computer yesterday and, well, let me tell "
        "you - it was a disaster! The thing kept crashing every five minutes. "
        "I called my friend Dave (who's supposedly a tech whiz) but even he "
        "was stumped. We ended up ordering pizza and binge-watching Netflix "
        "instead. Sometimes you just gotta know when to give up, right? "
        "Anyway, I'm writing this from my phone because the computer is "
        "still broken. Dave says he'll come back Thursday with some 'special "
        "tools' whatever that means. I'm not holding my breath honestly."
    )


@pytest.fixture
def short_text():
    """Very short text for edge case testing."""
    return "Hello world."


@pytest.fixture
def empty_text():
    """Empty text for edge case testing."""
    return ""


@pytest.fixture
def medium_text():
    """Medium-length text for testing."""
    return (
        "The weather today was absolutely beautiful. I decided to take my dog "
        "for a long walk through the park near our house. We saw several other "
        "dogs playing fetch and my dog wanted to join them so badly. After the "
        "walk we stopped at a cafe and I got coffee while he drank water from "
        "a bowl the barista brought out. It was a really nice afternoon overall."
    )


@pytest.fixture
def repetitive_text():
    """Highly repetitive text for testing edge cases."""
    return "The cat sat. The cat sat. The cat sat. The cat sat. The cat sat. " * 5


@pytest.fixture
def nltk_analyzer():
    """Create an NLTK analyzer instance."""
    from src.analyzers.nltk_analyzer import NLTKAnalyzer
    return NLTKAnalyzer(ngram_size=3)


@pytest.fixture
def text_processor():
    """Create a TextProcessor instance."""
    from src.utils.text_processing import TextProcessor
    return TextProcessor()