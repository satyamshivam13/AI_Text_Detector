"""
Ensemble Analyzer
==================

Combines RoBERTa, GPT-2, and NLTK analyzers for maximum accuracy.
"""

from __future__ import annotations

import time
from typing import List, Dict

from src.analyzers.base_analyzer import BaseAnalyzer
from src.analyzers.gpt2_analyzer import GPT2Analyzer
from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.analyzers.roberta_analyzer import RoBERTaAnalyzer
from src.config.settings import ConfidenceLevel, Verdict, get_settings
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class EnsembleAnalyzer(BaseAnalyzer):
    """Ensemble analyzer combining multiple detection methods."""

    def __init__(self):
        super().__init__()
        self.method_name = "Ensemble (GPT2+NLTK)"
        
        # Initialize analyzers
        logger.info("Initializing ensemble components...")
        self._roberta_analyzer = None
        self._gpt2_analyzer = None
        self._nltk_analyzer = None
        
        # Weights for ensemble voting
        # RoBERTa is disabled (0.0) by default as it requires fine-tuning
        # To enable: fine-tune the model, then set weight to 0.45 and adjust others
        self.weights = {
            "roberta": 0.0,   # RoBERTa (DISABLED - requires fine-tuning)
            "gpt2": 0.65,     # GPT-2 perplexity (increased weight)
            "nltk": 0.35,     # NLTK statistical (increased weight)
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

        try:
            # Compute text metrics once
            result.metrics = TextProcessor.compute_metrics(cleaned_text)

            # Run all three analyzers in parallel (conceptually)
            logger.info("Running ensemble analysis...")
            
            logger.info("1/3: Running RoBERTa analysis...")
            roberta_result = self.roberta_analyzer.analyze(cleaned_text)
            
            logger.info("2/3: Running GPT-2 analysis...")
            gpt2_result = self.gpt2_analyzer.analyze(cleaned_text)
            
            logger.info("3/3: Running NLTK analysis...")
            nltk_result = self.nltk_analyzer.analyze(cleaned_text)

            # Combine results
            result = self._combine_results(
                result, roberta_result, gpt2_result, nltk_result
            )

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
        # Extract key metrics with fallback defaults
        # RoBERTa AI score (from its scores)
        roberta_ai_score = 0.5
        for score in roberta_result.scores:
            if "RoBERTa" in score.name:
                roberta_ai_score = score.value
                break

        # GPT-2 perplexity (normalized to 0-1, inverted so high = AI)
        gpt2_perplexity = gpt2_result.perplexity
        # Normalize: low perplexity = high AI probability
        gpt2_ai_score = max(0, min(1, 1 - (gpt2_perplexity / 500)))

        # NLTK perplexity (normalized similarly)
        nltk_perplexity = nltk_result.perplexity
        nltk_ai_score = max(0, min(1, 1 - (nltk_perplexity / 500)))

        # Weighted ensemble vote
        ensemble_ai_score = (
            self.weights["roberta"] * roberta_ai_score +
            self.weights["gpt2"] * gpt2_ai_score +
            self.weights["nltk"] * nltk_ai_score
        )

        logger.info(
            f"Ensemble scores - RoBERTa: {roberta_ai_score:.3f}, "
            f"GPT-2: {gpt2_ai_score:.3f}, NLTK: {nltk_ai_score:.3f}, "
            f"Combined: {ensemble_ai_score:.3f}"
        )

        # Add ensemble score
        result.add_score(DetectionScore(
            name="Ensemble AI Score",
            value=ensemble_ai_score,
            weight=1.0,
            interpretation=self._interpret_ensemble_score(ensemble_ai_score),
            indicates_ai=ensemble_ai_score > 0.5,
        ))

        # Add individual analyzer scores for transparency
        result.add_score(DetectionScore(
            name="RoBERTa Score",
            value=roberta_ai_score,
            weight=self.weights["roberta"],
            interpretation=f"RoBERTa: {roberta_result.verdict.value}",
            indicates_ai=roberta_ai_score > 0.5,
        ))

        result.add_score(DetectionScore(
            name="GPT-2 Perplexity Score",
            value=gpt2_ai_score,
            weight=self.weights["gpt2"],
            interpretation=f"GPT-2: {gpt2_result.verdict.value} (PPL: {gpt2_perplexity:.1f})",
            indicates_ai=gpt2_ai_score > 0.5,
        ))

        result.add_score(DetectionScore(
            name="NLTK Statistical Score",
            value=nltk_ai_score,
            weight=self.weights["nltk"],
            interpretation=f"NLTK: {nltk_result.verdict.value} (PPL: {nltk_perplexity:.1f})",
            indicates_ai=nltk_ai_score > 0.5,
        ))

        # Combine other metrics (averages)
        result.perplexity = (gpt2_perplexity + nltk_perplexity) / 2
        result.burstiness = (
            roberta_result.burstiness + 
            gpt2_result.burstiness + 
            nltk_result.burstiness
        ) / 3
        result.lexical_diversity = result.metrics.lexical_diversity
        result.sentence_variance = (
            roberta_result.sentence_variance + 
            gpt2_result.sentence_variance + 
            nltk_result.sentence_variance
        ) / 3

        return result

    def _determine_verdict(self, result: AnalysisResult) -> AnalysisResult:
        """
        Determine final verdict based on ensemble score.

        Args:
            result: Result with ensemble scores.

        Returns:
            Result with verdict and confidence.
        """
        # Get ensemble AI score
        ensemble_score = result.scores[0].value if result.scores else 0.5

        # Agreement level (check if analyzers agree)
        ai_votes = sum(1 for s in result.scores[1:] if s.indicates_ai)
        total_votes = len(result.scores) - 1  # Exclude ensemble score itself
        agreement = ai_votes / total_votes if total_votes > 0 else 0.5

        # Base confidence on ensemble score and agreement
        base_confidence = abs(ensemble_score - 0.5) * 200  # 0-100 scale
        agreement_boost = agreement if ensemble_score > 0.5 else (1 - agreement)
        confidence = base_confidence * (0.7 + 0.3 * agreement_boost)

        # Determine verdict
        if ensemble_score > 0.75:
            result.verdict = Verdict.AI_GENERATED
            result.confidence = min(95, 80 + confidence * 0.15)
        elif ensemble_score > 0.60:
            result.verdict = Verdict.LIKELY_AI
            result.confidence = min(85, 65 + confidence * 0.2)
        elif ensemble_score > 0.40:
            result.verdict = Verdict.UNCERTAIN
            result.confidence = 50.0
        elif ensemble_score > 0.25:
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

        # Key metrics
        parts.append(
            f"\n📈 **Key Metrics**:\n"
            f"• Average Perplexity: {result.perplexity:.1f}\n"
            f"• Burstiness: {result.burstiness:.3f}\n"
            f"• Lexical Diversity: {result.lexical_diversity:.1%}"
        )

        # Agreement analysis
        ai_votes = sum(1 for s in result.scores[1:] if s.indicates_ai)
        total_votes = len(result.scores) - 1
        if ai_votes == total_votes:
            parts.append("\n✅ **All analyzers agree** on AI detection.")
        elif ai_votes == 0:
            parts.append("\n✅ **All analyzers agree** on human authorship.")
        else:
            parts.append(
                f"\n⚖️ **Mixed signals**: {ai_votes}/{total_votes} analyzers "
                f"indicate AI-generated content."
            )

        return " ".join(parts)

    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """Not used in ensemble - override analyze() instead."""
        return result
