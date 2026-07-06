"""
Ensemble Analyzer
==================

Combines RoBERTa, GPT-2, and NLTK analyzers for maximum accuracy.
"""

from __future__ import annotations

import time

from src.analyzers.base_analyzer import BaseAnalyzer
from src.analyzers.calibration import logistic_ai_probability
from src.analyzers.gpt2_analyzer import GPT2Analyzer
from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.analyzers.roberta_analyzer import RoBERTaAnalyzer
from src.config.settings import ConfidenceLevel, Verdict
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class EnsembleAnalyzer(BaseAnalyzer):
    """Ensemble analyzer combining multiple detection methods.

    Each backend contributes a **calibrated** AI-probability in ``[0, 1]``; the
    ensemble is their weighted average::

        ensemble_ai_score = sum(weight_i * ai_probability_i)

    GPT-2 and NLTK perplexity are mapped to probabilities with a per-analyzer
    logistic (see :mod:`src.analyzers.calibration`) whose midpoint is the
    decision boundary, rather than the previous single ``1 - perplexity / 500``
    formula that scored ordinary human text as ~88% AI. Weights and calibration
    parameters come from :class:`~src.config.settings.EnsembleConfig`.

    RoBERTa is disabled by default (weight 0) and is *not loaded or run* in that
    state — its classification head is untrained, so it would only add cost and
    noise until a fine-tuned checkpoint is wired in.
    """

    def __init__(self):
        super().__init__()
        self.method_name = "Ensemble (GPT2+NLTK)"
        self.ensemble_config = self.settings.ensemble

        # Initialize analyzers
        logger.info("Initializing ensemble components...")
        self._roberta_analyzer = None
        self._gpt2_analyzer = None
        self._nltk_analyzer = None

        # Fusion weights, sourced from config so calibration lives in one place.
        cfg = self.ensemble_config
        self.weights = {
            "roberta": cfg.weight_roberta,
            "gpt2": cfg.weight_gpt2,
            "nltk": cfg.weight_nltk,
        }

    @property
    def roberta_analyzer(self) -> RoBERTaAnalyzer:
        """Lazy-load RoBERTa analyzer."""
        if self._roberta_analyzer is None:
            logger.info("Loading RoBERTa analyzer...")
            self._roberta_analyzer = RoBERTaAnalyzer()
        return self._roberta_analyzer

    @property
    def gpt2_analyzer(self) -> GPT2Analyzer:
        """Lazy-load GPT-2 analyzer."""
        if self._gpt2_analyzer is None:
            logger.info("Loading GPT-2 analyzer...")
            self._gpt2_analyzer = GPT2Analyzer()
        return self._gpt2_analyzer

    @property
    def nltk_analyzer(self) -> NLTKAnalyzer:
        """Lazy-load NLTK analyzer."""
        if self._nltk_analyzer is None:
            logger.info("Loading NLTK analyzer...")
            self._nltk_analyzer = NLTKAnalyzer(ngram_size=3)
        return self._nltk_analyzer

    def analyze(self, text: str) -> AnalysisResult:
        """
        Analyze text using ensemble of all three methods.

        Args:
            text: Input text to analyze.

        Returns:
            Combined AnalysisResult from ensemble.
        """
        start_time = time.time()
        result = AnalysisResult()

        # Validate input
        cleaned_text = TextProcessor.clean_text(text)
        cleaned_text = self._apply_input_cap(cleaned_text, result)
        result.text_length = len(cleaned_text)

        if not cleaned_text:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 0.0
            result.confidence_level = ConfidenceLevel.VERY_LOW
            result.add_warning("Empty or invalid text provided.")
            result.explanation = "No text to analyze."
            result.analysis_time = round(time.time() - start_time, 3)
            result.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
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
            # Compute text metrics once
            result.metrics = TextProcessor.compute_metrics(cleaned_text)

            # Run the analyzers. RoBERTa is skipped entirely when its weight is
            # 0 (the default): loading and running an untrained roberta-base
            # contributes nothing to the blend but costs a large download, RAM
            # and latency. A neutral placeholder keeps the result shape stable.
            logger.info("Running ensemble analysis...")

            if self.weights.get("roberta", 0.0) > 0:
                logger.info("Running RoBERTa analysis...")
                roberta_result = self.roberta_analyzer.analyze(cleaned_text)
            else:
                logger.info("Skipping RoBERTa (weight=0, not loaded).")
                roberta_result = self._disabled_roberta_result()

            logger.info("Running GPT-2 analysis...")
            gpt2_result = self.gpt2_analyzer.analyze(cleaned_text)

            logger.info("Running NLTK analysis...")
            nltk_result = self.nltk_analyzer.analyze(cleaned_text)

            # Combine results
            result = self._combine_results(result, roberta_result, gpt2_result, nltk_result)

            # Determine final verdict
            result = self._determine_verdict(result)

            # Generate explanation
            result.explanation = self._generate_ensemble_explanation(
                result, roberta_result, gpt2_result, nltk_result
            )

        except Exception as e:
            logger.error(f"Ensemble analysis failed: {e}", exc_info=True)
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 0.0
            result.confidence_level = ConfidenceLevel.VERY_LOW
            result.add_warning(f"Analysis error: {str(e)}")
            result.explanation = "An error occurred during ensemble analysis."

        result.analysis_time = round(time.time() - start_time, 3)
        result.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        result.method = self.method_name

        logger.info(
            f"Ensemble analysis complete: verdict={result.verdict.value}, "
            f"confidence={result.confidence:.1f}%, "
            f"time={result.analysis_time}s"
        )

        return result

    def _combine_results(
        self,
        result: AnalysisResult,
        roberta_result: AnalysisResult,
        gpt2_result: AnalysisResult,
        nltk_result: AnalysisResult,
    ) -> AnalysisResult:
        """
        Combine results from all three analyzers.

        Args:
            result: Base result to populate.
            roberta_result: Result from RoBERTa.
            gpt2_result: Result from GPT-2.
            nltk_result: Result from NLTK.

        Returns:
            Combined result.
        """
        cfg = self.ensemble_config

        # RoBERTa AI score (from its scores); 0.5 (neutral) when disabled.
        roberta_ai_score = 0.5
        for score in roberta_result.scores:
            if "RoBERTa" in score.name:
                roberta_ai_score = score.value
                break

        # Calibrated per-analyzer AI-probabilities. Each analyzer uses its own
        # logistic (midpoint = decision boundary, correct direction) instead of
        # one linear map that scored human text as ~88% AI.
        gpt2_perplexity = gpt2_result.perplexity
        gpt2_ai_score = logistic_ai_probability(
            gpt2_perplexity,
            midpoint=cfg.gpt2_ppl_midpoint,
            slope=cfg.gpt2_ppl_slope,
            direction="lower_is_ai",
        )

        nltk_perplexity = nltk_result.perplexity
        nltk_ai_score = logistic_ai_probability(
            nltk_perplexity,
            midpoint=cfg.nltk_ppl_midpoint,
            slope=cfg.nltk_ppl_slope,
            direction="higher_is_ai",
        )

        # Weighted ensemble vote (roberta weight is 0 by default => no effect).
        ensemble_ai_score = (
            self.weights["roberta"] * roberta_ai_score
            + self.weights["gpt2"] * gpt2_ai_score
            + self.weights["nltk"] * nltk_ai_score
        )

        logger.info(
            f"Ensemble scores - RoBERTa: {roberta_ai_score:.3f}, "
            f"GPT-2: {gpt2_ai_score:.3f}, NLTK: {nltk_ai_score:.3f}, "
            f"Combined: {ensemble_ai_score:.3f}"
        )

        # Add ensemble score (always index 0 by contract).
        result.add_score(
            DetectionScore(
                name="Ensemble AI Score",
                value=ensemble_ai_score,
                weight=1.0,
                interpretation=self._interpret_ensemble_score(ensemble_ai_score),
                indicates_ai=ensemble_ai_score > 0.5,
            )
        )

        # Individual analyzer scores for transparency. The RoBERTa row carries
        # weight 0 when disabled so downstream agreement logic can exclude it.
        roberta_note = (
            f"RoBERTa: {roberta_result.verdict.value}"
            if self.weights["roberta"] > 0
            else "RoBERTa: disabled (weight 0, not run)"
        )
        result.add_score(
            DetectionScore(
                name="RoBERTa Score",
                value=roberta_ai_score,
                weight=self.weights["roberta"],
                interpretation=roberta_note,
                indicates_ai=roberta_ai_score > 0.5,
            )
        )

        result.add_score(
            DetectionScore(
                name="GPT-2 Perplexity Score",
                value=gpt2_ai_score,
                weight=self.weights["gpt2"],
                interpretation=f"GPT-2: {gpt2_result.verdict.value} (PPL: {gpt2_perplexity:.1f})",
                indicates_ai=gpt2_ai_score > 0.5,
            )
        )

        result.add_score(
            DetectionScore(
                name="NLTK Statistical Score",
                value=nltk_ai_score,
                weight=self.weights["nltk"],
                interpretation=f"NLTK: {nltk_result.verdict.value} (PPL: {nltk_perplexity:.1f})",
                indicates_ai=nltk_ai_score > 0.5,
            )
        )

        # Aggregate reported metrics from the analyzers that actually run
        # (GPT-2 + NLTK), so a disabled RoBERTa placeholder cannot skew them.
        result.perplexity = (gpt2_perplexity + nltk_perplexity) / 2
        result.burstiness = (gpt2_result.burstiness + nltk_result.burstiness) / 2
        result.lexical_diversity = result.metrics.lexical_diversity
        result.sentence_variance = (
            gpt2_result.sentence_variance + nltk_result.sentence_variance
        ) / 2

        return result

    def _determine_verdict(self, result: AnalysisResult) -> AnalysisResult:
        """
        Determine final verdict based on ensemble score.

        Args:
            result: Result with ensemble scores.

        Returns:
            Result with verdict and confidence.
        """
        cfg = self.ensemble_config

        # Get ensemble AI score (index 0 by contract).
        ensemble_score = result.scores[0].value if result.scores else 0.5

        # Agreement only over analyzers that actually contribute (weight > 0):
        # a disabled/zero-weight RoBERTa must not sway confidence or narrative.
        voters = [s for s in result.scores[1:] if s.weight > 0]
        ai_votes = sum(1 for s in voters if s.indicates_ai)
        total_votes = len(voters)
        agreement = ai_votes / total_votes if total_votes > 0 else 0.5

        # Base confidence on distance from the 0.5 boundary and voter agreement.
        base_confidence = abs(ensemble_score - 0.5) * 200  # 0-100 scale
        agreement_boost = agreement if ensemble_score > 0.5 else (1 - agreement)
        confidence = base_confidence * (0.7 + 0.3 * agreement_boost)

        # Determine verdict against calibrated, configurable thresholds.
        if ensemble_score >= cfg.ai_threshold:
            result.verdict = Verdict.AI_GENERATED
            result.confidence = min(95, 80 + confidence * 0.15)
        elif ensemble_score >= cfg.likely_ai_threshold:
            result.verdict = Verdict.LIKELY_AI
            result.confidence = min(85, 65 + confidence * 0.2)
        elif ensemble_score >= cfg.likely_human_threshold:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 50.0
        elif ensemble_score >= cfg.human_threshold:
            result.verdict = Verdict.LIKELY_HUMAN
            result.confidence = min(85, 65 + (1 - ensemble_score) * 50)
        else:
            result.verdict = Verdict.HUMAN_WRITTEN
            result.confidence = min(95, 80 + (1 - ensemble_score) * 50)

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

    def _interpret_ensemble_score(self, score: float) -> str:
        """Generate interpretation for ensemble score."""
        if score > 0.85:
            return "Very strong AI consensus — extremely likely AI-generated"
        elif score > 0.70:
            return "Strong AI consensus — likely AI-generated"
        elif score > 0.60:
            return "Moderate AI indication — possible AI patterns"
        elif score > 0.40:
            return "Uncertain — mixed signals from analyzers"
        elif score > 0.30:
            return "Moderate human indication — likely human-written"
        else:
            return "Strong human consensus — extremely likely human-written"

    def _generate_ensemble_explanation(
        self,
        result: AnalysisResult,
        roberta_result: AnalysisResult,
        gpt2_result: AnalysisResult,
        nltk_result: AnalysisResult,
    ) -> str:
        """Generate comprehensive ensemble explanation."""
        parts = []

        # Ensemble verdict
        ensemble_score = result.scores[0].value if result.scores else 0.5
        parts.append(
            f"🎯 **Ensemble Analysis**: Combined score of {ensemble_score:.1%} "
            f"indicates **{result.verdict.value}** with {result.confidence:.1f}% confidence."
        )

        # Individual verdicts
        parts.append(
            f"\n📊 **Individual Analyzers**:\n"
            f"• RoBERTa: {roberta_result.verdict.value} ({roberta_result.confidence:.1f}%)\n"
            f"• GPT-2: {gpt2_result.verdict.value} ({gpt2_result.confidence:.1f}%)\n"
            f"• NLTK: {nltk_result.verdict.value} ({nltk_result.confidence:.1f}%)"
        )

        parts.append(
            f"\n⚖️ **Weights**: RoBERTa {self.weights['roberta'] * 100:.0f}%, "
            f"GPT-2 {self.weights['gpt2'] * 100:.0f}%, "
            f"NLTK {self.weights['nltk'] * 100:.0f}%."
        )

        # Key metrics
        parts.append(
            f"\n📈 **Key Metrics**:\n"
            f"• Average Perplexity: {result.perplexity:.1f}\n"
            f"• Burstiness: {result.burstiness:.3f}\n"
            f"• Lexical Diversity: {result.lexical_diversity:.1%}"
        )

        # Agreement analysis over contributing analyzers only (weight > 0).
        voters = [s for s in result.scores[1:] if s.weight > 0]
        ai_votes = sum(1 for s in voters if s.indicates_ai)
        total_votes = len(voters)
        if total_votes and ai_votes == total_votes:
            parts.append("\n✅ **All contributing analyzers agree** on AI detection.")
        elif ai_votes == 0:
            parts.append("\n✅ **All contributing analyzers agree** on human authorship.")
        else:
            parts.append(
                f"\n⚖️ **Mixed signals**: {ai_votes}/{total_votes} contributing "
                f"analyzers indicate AI-generated content."
            )

        return " ".join(parts)

    def _disabled_roberta_result(self) -> AnalysisResult:
        """Neutral placeholder used when RoBERTa is disabled (weight 0).

        Returns a result carrying a neutral (0.5) RoBERTa score without loading
        or running the model, so the ensemble result shape stays stable while
        avoiding a needless download, memory and latency.
        """
        placeholder = AnalysisResult(verdict=Verdict.UNCERTAIN, confidence=0.0)
        placeholder.add_score(
            DetectionScore(
                name="RoBERTa AI Probability",
                value=0.5,
                weight=0.0,
                interpretation="RoBERTa disabled (weight 0, not run)",
                indicates_ai=False,
            )
        )
        return placeholder

    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """Not used in ensemble - override analyze() instead."""
        return result
