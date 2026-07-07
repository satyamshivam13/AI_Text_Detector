"""
Binoculars Analyzer
===================

Zero-shot AI-text detection via **cross-perplexity** between two language models,
after Hans et al., 2024 ("Spotting LLMs With Binoculars").

Intuition
---------
A single model's perplexity conflates "how machine-like is this text" with "how
surprising is this prompt/topic". Binoculars cancels the prompt effect by
dividing an *observer* model's log-perplexity by the *cross-perplexity* between
the observer and a second *performer* model:

    score = log_perplexity_observer(text) / cross_perplexity(observer, performer)

Human text tends to score **higher**; machine-generated text scores **lower**.
Because it is a ratio of two models, it is far more robust than the single-model
GPT-2 perplexity signal — the modernization recommended by the project audit.

This implementation deliberately uses a small, CPU-friendly observer/performer
pair (``gpt2`` / ``distilgpt2``) that share the GPT-2 tokenizer, so it stays
local and dependency-light. The decision boundary is calibrated on the bundled
benchmark rather than hard-coded to the paper's Falcon-specific threshold.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

import torch
from transformers import GPT2LMHeadModel, GPT2TokenizerFast

from src.analyzers.base_analyzer import BaseAnalyzer
from src.analyzers.calibration import logistic_ai_probability
from src.config.settings import ConfidenceLevel, Verdict
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class BinocularsAnalyzer(BaseAnalyzer):
    """Cross-perplexity (two-model) AI-text detector."""

    # Primary calibrated score, addressed by name (not list position).
    PRIMARY_SCORE_NAME = "Binoculars AI Score"

    def __init__(self):
        super().__init__()
        self.config = self.settings.binoculars
        self.method_name = "Binoculars (cross-perplexity)"
        self._tokenizer: Optional[GPT2TokenizerFast] = None
        self._observer: Optional[GPT2LMHeadModel] = None
        self._performer: Optional[GPT2LMHeadModel] = None
        self._device: Optional[torch.device] = None

    # ------------------------------------------------------------------ #
    # Lazy resources
    # ------------------------------------------------------------------ #
    @property
    def device(self) -> torch.device:
        if self._device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Binoculars using device: {self._device}")
        return self._device

    @property
    def tokenizer(self) -> GPT2TokenizerFast:
        if self._tokenizer is None:
            logger.info("Loading Binoculars tokenizer...")
            self._tokenizer = GPT2TokenizerFast.from_pretrained(
                self.config.observer_model, revision=self.config.revision
            )
        return self._tokenizer

    def _load_model(self, name: str) -> GPT2LMHeadModel:
        logger.info(f"Loading Binoculars model: {name}...")
        model = GPT2LMHeadModel.from_pretrained(
            name, revision=self.config.revision, use_safetensors=True
        )
        model.to(self.device)
        model.eval()
        return model

    @property
    def observer(self) -> GPT2LMHeadModel:
        if self._observer is None:
            self._observer = self._load_model(self.config.observer_model)
        return self._observer

    @property
    def performer(self) -> GPT2LMHeadModel:
        if self._performer is None:
            self._performer = self._load_model(self.config.performer_model)
        return self._performer

    # ------------------------------------------------------------------ #
    # Core computation
    # ------------------------------------------------------------------ #
    def _compute_binoculars(self, text: str) -> Tuple[float, float]:
        """Return ``(binoculars_score, observer_perplexity)``.

        ``binoculars_score`` is log-perplexity(observer) / cross-perplexity;
        lower values indicate machine-generated text.
        """
        enc = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.config.max_token_length,
        )
        input_ids = enc.input_ids.to(self.device)
        if input_ids.size(1) <= 1:
            return 1.0, 100.0  # neutral-ish for degenerate input

        with torch.no_grad():
            obs_logits = self.observer(input_ids).logits[:, :-1, :]
            perf_logits = self.performer(input_ids).logits[:, :-1, :]
            targets = input_ids[:, 1:]

            obs_logp = torch.log_softmax(obs_logits, dim=-1)
            perf_logp = torch.log_softmax(perf_logits, dim=-1)
            obs_p = obs_logp.exp()

            # Observer cross-entropy against the true next token (nats).
            tgt_logp = obs_logp.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
            observer_ce = -tgt_logp.mean().item()

            # Cross-perplexity: mean cross-entropy between observer and performer
            # next-token distributions (nats).
            cross_ce = -(obs_p * perf_logp).sum(dim=-1).mean().item()

        if cross_ce <= 0:
            return 1.0, math.exp(min(observer_ce, 9.0))

        binoculars_score = observer_ce / cross_ce
        observer_ppl = math.exp(min(observer_ce, 9.0))  # cap to avoid overflow
        return binoculars_score, observer_ppl

    def ai_probability(self, text: str) -> float:
        """Calibrated AI-probability in ``[0, 1]`` for ``text`` (lower score => AI)."""
        score, _ = self._compute_binoculars(text)
        return logistic_ai_probability(
            score,
            midpoint=self.config.score_midpoint,
            slope=self.config.score_slope,
            direction="lower_is_ai",
        )

    # ------------------------------------------------------------------ #
    # Analyzer contract
    # ------------------------------------------------------------------ #
    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        result.method = self.method_name

        score, observer_ppl = self._compute_binoculars(text)
        ai_prob = logistic_ai_probability(
            score,
            midpoint=self.config.score_midpoint,
            slope=self.config.score_slope,
            direction="lower_is_ai",
        )
        result.perplexity = observer_ppl

        # Primary calibrated score, addressed by name (not list position).
        result.add_score(
            DetectionScore(
                name=self.PRIMARY_SCORE_NAME,
                value=ai_prob,
                weight=1.0,
                interpretation=self._interpret(score, ai_prob),
                indicates_ai=ai_prob > 0.5,
            )
        )
        result.add_score(
            DetectionScore(
                name="Binoculars Ratio",
                value=score,
                weight=0.0,
                interpretation=f"log-ppl / cross-ppl = {score:.3f} (lower => AI)",
                indicates_ai=score < self.config.score_midpoint,
            )
        )

        # Supporting statistical metrics for transparency.
        burstiness, _ = TextProcessor.compute_burstiness(text)
        result.burstiness = burstiness
        result.lexical_diversity = result.metrics.lexical_diversity
        result.sentence_variance = TextProcessor.compute_sentence_variance(text)
        return result

    def _determine_verdict(self, result: AnalysisResult) -> AnalysisResult:
        """Map the calibrated Binoculars AI-probability to a verdict."""
        primary = result.get_score(self.PRIMARY_SCORE_NAME)
        ai_prob = primary.value if primary else 0.5
        confidence = abs(ai_prob - 0.5) * 200  # 0-100

        if ai_prob >= 0.75:
            result.verdict = Verdict.AI_GENERATED
            result.confidence = min(95.0, 80 + confidence * 0.15)
        elif ai_prob >= 0.55:
            result.verdict = Verdict.LIKELY_AI
            result.confidence = min(85.0, 65 + confidence * 0.2)
        elif ai_prob >= 0.45:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 50.0
        elif ai_prob >= 0.25:
            result.verdict = Verdict.LIKELY_HUMAN
            result.confidence = min(85.0, 65 + (1 - ai_prob) * 50)
        else:
            result.verdict = Verdict.HUMAN_WRITTEN
            result.confidence = min(95.0, 80 + (1 - ai_prob) * 50)

        result.confidence = round(result.confidence, 1)
        if result.confidence >= 80:
            result.confidence_level = ConfidenceLevel.HIGH
        elif result.confidence >= 60:
            result.confidence_level = ConfidenceLevel.MEDIUM
        elif result.confidence >= 40:
            result.confidence_level = ConfidenceLevel.LOW
        else:
            result.confidence_level = ConfidenceLevel.VERY_LOW
        return result

    def _interpret(self, score: float, ai_prob: float) -> str:
        if ai_prob > 0.75:
            return f"Low cross-perplexity ratio ({score:.3f}) — strong AI indicator"
        if ai_prob > 0.55:
            return f"Below-boundary ratio ({score:.3f}) — likely AI-generated"
        if ai_prob > 0.45:
            return f"Borderline ratio ({score:.3f}) — uncertain"
        if ai_prob > 0.25:
            return f"Above-boundary ratio ({score:.3f}) — likely human-written"
        return f"High cross-perplexity ratio ({score:.3f}) — strong human indicator"
