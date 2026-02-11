"""
GPT-2 Based Analyzer
=====================

Advanced text analysis using GPT-2 language model for perplexity computation.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

from src.analyzers.base_analyzer import BaseAnalyzer
from src.config.settings import get_settings
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class GPT2Analyzer(BaseAnalyzer):
    """Analyzer using GPT-2 for advanced perplexity-based detection."""

    def __init__(self):
        super().__init__()
        self._model: Optional[GPT2LMHeadModel] = None
        self._tokenizer: Optional[GPT2TokenizerFast] = None
        self._device: Optional[torch.device] = None
        self.method_name = "GPT-2 Deep Analysis"

    @property
    def device(self) -> torch.device:
        """Get the computation device."""
        if self._device is None:
            if self.settings.gpt2.device:
                self._device = torch.device(self.settings.gpt2.device)
            elif torch.cuda.is_available():
                self._device = torch.device("cuda")
            else:
                self._device = torch.device("cpu")
            logger.info(f"Using device: {self._device}")
        return self._device

    @property
    def tokenizer(self) -> GPT2TokenizerFast:
        """Lazy-load the GPT-2 tokenizer."""
        if self._tokenizer is None:
            logger.info("Loading GPT-2 tokenizer...")
            self._tokenizer = GPT2TokenizerFast.from_pretrained(
                self.settings.gpt2.model_name,
                cache_dir=self.settings.gpt2.cache_dir,
            )
        return self._tokenizer

    @property
    def model(self) -> GPT2LMHeadModel:
        """Lazy-load the GPT-2 model."""
        if self._model is None:
            logger.info("Loading GPT-2 model...")
            self._model = GPT2LMHeadModel.from_pretrained(
                self.settings.gpt2.model_name,
                cache_dir=self.settings.gpt2.cache_dir,
            )
            self._model.to(self.device)
            self._model.eval()
            logger.info("GPT-2 model loaded successfully")
        return self._model

    def _compute_perplexity_gpt2(self, text: str) -> float:
        """
        Compute perplexity using GPT-2 model.

        Uses a sliding window approach for texts longer than model's max length.

        Args:
            text: Input text.

        Returns:
            Perplexity score.
        """
        max_length = self.settings.gpt2.max_token_length
        stride = self.settings.gpt2.stride

        encodings = self.tokenizer(text, return_tensors="pt")
        input_ids = encodings.input_ids

        seq_len = input_ids.size(1)

        if seq_len <= 1:
            return 100.0

        nlls = []
        prev_end_loc = 0

        for begin_loc in range(0, seq_len, stride):
            end_loc = min(begin_loc + max_length, seq_len)
            trg_len = end_loc - prev_end_loc

            input_chunk = input_ids[:, begin_loc:end_loc].to(self.device)

            target_ids = input_chunk.clone()
            target_ids[:, :-trg_len] = -100  # Mask non-target tokens

            with torch.no_grad():
                outputs = self.model(input_chunk, labels=target_ids)
                neg_log_likelihood = outputs.loss

            if not torch.isnan(neg_log_likelihood) and not torch.isinf(neg_log_likelihood):
                nlls.append(neg_log_likelihood.item())

            prev_end_loc = end_loc

            if end_loc == seq_len:
                break

        if not nlls:
            return 100.0

        avg_nll = sum(nlls) / len(nlls)

        try:
            perplexity = math.exp(avg_nll)
        except OverflowError:
            perplexity = float("inf")

        return min(perplexity, 10000.0)

    def _compute_token_entropy(self, text: str) -> float:
        """
        Compute average token-level entropy from GPT-2.

        Args:
            text: Input text.

        Returns:
            Average entropy value.
        """
        max_length = self.settings.gpt2.max_token_length

        encodings = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=max_length
        )
        input_ids = encodings.input_ids.to(self.device)

        if input_ids.size(1) <= 1:
            return 0.0

        with torch.no_grad():
            outputs = self.model(input_ids)
            logits = outputs.logits

        # Compute probabilities
        probs = torch.softmax(logits[:, :-1, :], dim=-1)

        # Compute entropy for each position
        log_probs = torch.log2(probs + 1e-10)
        entropy = -torch.sum(probs * log_probs, dim=-1)

        avg_entropy = entropy.mean().item()

        return round(avg_entropy, 4)

    def _compute_probability_variance(self, text: str) -> float:
        """
        Compute variance in token prediction probabilities.

        AI text tends to have lower variance (more uniform predictions).

        Args:
            text: Input text.

        Returns:
            Probability variance score.
        """
        max_length = self.settings.gpt2.max_token_length

        encodings = self.tokenizer(
            text, return_tensors="pt", truncation=True, max_length=max_length
        )
        input_ids = encodings.input_ids.to(self.device)

        if input_ids.size(1) <= 2:
            return 0.0

        with torch.no_grad():
            outputs = self.model(input_ids)
            logits = outputs.logits

        # Get probability of actual next tokens
        probs = torch.softmax(logits[:, :-1, :], dim=-1)
        actual_next_tokens = input_ids[:, 1:]

        # Gather probabilities for actual tokens
        token_probs = probs.gather(2, actual_next_tokens.unsqueeze(-1)).squeeze(-1)

        # Compute variance
        variance = token_probs.var().item()

        return round(variance, 6)

    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """
        Perform GPT-2-based analysis.

        Args:
            text: Cleaned input text.
            result: Partially populated result.

        Returns:
            Updated result with GPT-2 analysis.
        """
        result.method = "GPT-2 Deep Analysis"

        # 1. Compute GPT-2 perplexity
        logger.info("Computing GPT-2 perplexity...")
        result.perplexity = self._compute_perplexity_gpt2(text)

        result.add_score(DetectionScore(
            name="GPT-2 Perplexity",
            value=result.perplexity,
            weight=0.40,
            interpretation=self._interpret_gpt2_perplexity(result.perplexity),
            indicates_ai=result.perplexity < self.thresholds.perplexity_medium,
        ))

        # 2. Compute burstiness
        logger.info("Computing burstiness...")
        burstiness, _ = TextProcessor.compute_burstiness(text)
        result.burstiness = burstiness

        result.add_score(DetectionScore(
            name="Burstiness",
            value=result.burstiness,
            weight=0.20,
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
            weight=0.15,
            interpretation=self._interpret_sentence_variance(result.sentence_variance),
            indicates_ai=result.sentence_variance < 0.25,
        ))

        # 5. Compute token-level entropy (GPT-2 specific)
        logger.info("Computing token entropy...")
        try:
            entropy = self._compute_token_entropy(text)
            result.add_score(DetectionScore(
                name="Token Entropy",
                value=entropy,
                weight=0.10,
                interpretation=self._interpret_entropy(entropy),
                indicates_ai=entropy < 6.0,
            ))
        except Exception as e:
            logger.warning(f"Token entropy computation failed: {e}")

        return result

    def _interpret_gpt2_perplexity(self, value: float) -> str:
        """Generate interpretation for GPT-2 perplexity."""
        if value < 20:
            return "Extremely low — very strong AI indicator"
        elif value < 50:
            return "Very low — strong AI indicator"
        elif value < 100:
            return "Low — likely AI-generated"
        elif value < 200:
            return "Moderate — inconclusive"
        elif value < 500:
            return "High — likely human-written"
        else:
            return "Very high — strong human indicator"

    def _interpret_burstiness(self, value: float) -> str:
        """Generate interpretation for burstiness."""
        if value < 0.15:
            return "Very uniform — strong AI indicator"
        elif value < 0.25:
            return "Low variation — likely AI"
        elif value < 0.40:
            return "Moderate variation — inconclusive"
        else:
            return "High variation — likely human"

    def _interpret_lexical_diversity(self, value: float) -> str:
        """Generate interpretation for lexical diversity."""
        if value < 0.30:
            return "Very repetitive vocabulary"
        elif value < 0.50:
            return "Below average diversity"
        elif value < 0.70:
            return "Good vocabulary diversity"
        else:
            return "Excellent vocabulary diversity"

    def _interpret_sentence_variance(self, value: float) -> str:
        """Generate interpretation for sentence variance."""
        if value < 0.15:
            return "Very uniform — AI indicator"
        elif value < 0.30:
            return "Low variation"
        elif value < 0.50:
            return "Natural variation"
        else:
            return "High variation — human indicator"

    def _interpret_entropy(self, value: float) -> str:
        """Generate interpretation for token entropy."""
        if value < 4.0:
            return "Very low entropy — highly predictable"
        elif value < 6.0:
            return "Low entropy — predictable patterns"
        elif value < 8.0:
            return "Moderate entropy — natural range"
        else:
            return "High entropy — unpredictable patterns"