"""
RoBERTa-Based Analyzer
=======================

Text analysis using RoBERTa transformer model for AI detection.
"""

from __future__ import annotations

import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification

from src.analyzers.base_analyzer import BaseAnalyzer
from src.config.settings import get_settings
from src.models.result import AnalysisResult, DetectionScore
from src.utils.logging_config import get_logger
from src.utils.text_processing import TextProcessor

logger = get_logger(__name__)


class RoBERTaAnalyzer(BaseAnalyzer):
    """Analyzer using RoBERTa for AI-generated text detection."""

    def __init__(self):
        super().__init__()
        self._model = None
        self._tokenizer = None
        self._device = None
        self.method_name = "RoBERTa"

    @property
    def device(self) -> torch.device:
        """Get the computation device."""
        if self._device is None:
            if torch.cuda.is_available():
                self._device = torch.device("cuda")
            else:
                self._device = torch.device("cpu")
            logger.info(f"RoBERTa using device: {self._device}")
        return self._device

    @property
    def tokenizer(self) -> RobertaTokenizer:
        """Lazy-load the RoBERTa tokenizer."""
        if self._tokenizer is None:
            logger.info("Loading RoBERTa tokenizer...")
            # Using a pre-trained AI detection model
            # Note: You can replace this with a fine-tuned model for AI detection
            self._tokenizer = RobertaTokenizer.from_pretrained(
                "roberta-base"
            )
        return self._tokenizer

    @property
    def model(self) -> RobertaForSequenceClassification:
        """Lazy-load the RoBERTa model."""
        if self._model is None:
            logger.info("Loading RoBERTa model...")
            logger.warning(
                "Using UNTRAINED roberta-base model. This model has NOT been fine-tuned "
                "for AI detection and will produce random predictions (~50% accuracy). "
                "For production use, fine-tune this model on an AI detection dataset or "
                "use a pre-trained AI detector model."
            )
            # Using base model - REQUIRES FINE-TUNING for accurate AI detection
            # To use a fine-tuned model, replace 'roberta-base' with your model path
            # Example: 'your-username/roberta-ai-detector'
            self._model = RobertaForSequenceClassification.from_pretrained(
                "roberta-base",
                num_labels=2  # Binary classification: AI vs Human
            )
            self._model.to(self.device)
            self._model.eval()
            logger.info("RoBERTa model loaded (UNTRAINED - predictions will be random)")
        return self._model

    def _compute_roberta_score(self, text: str) -> tuple[float, float]:
        """
        Compute AI detection score using RoBERTa.

        Args:
            text: Input text.

        Returns:
            Tuple of (ai_probability, confidence)
        """
        # Tokenize with truncation and padding
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
        # Convert to probabilities
        probs = torch.softmax(logits, dim=1)
        ai_prob = probs[0][1].item()  # Probability of AI class
        confidence = max(probs[0]).item()  # Max probability as confidence

        return ai_prob, confidence

    def _perform_analysis(self, text: str, result: AnalysisResult) -> AnalysisResult:
        """
        Perform RoBERTa-based analysis.

        Args:
            text: Cleaned input text.
            result: Partially populated result.

        Returns:
            Updated result with RoBERTa analysis.
        """
        result.method = "RoBERTa Transformer"

        # 1. Compute RoBERTa AI detection score
        logger.info("Computing RoBERTa classification...")
        ai_prob, confidence = self._compute_roberta_score(text)

        result.add_score(DetectionScore(
            name="RoBERTa AI Score",
            value=ai_prob,
            weight=0.50,
            interpretation=self._interpret_roberta_score(ai_prob),
            indicates_ai=ai_prob > 0.5,
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

        # Store perplexity placeholder (not computed by RoBERTa)
        result.perplexity = 0.0

        return result

    def _interpret_roberta_score(self, value: float) -> str:
        """Generate interpretation for RoBERTa score."""
        if value > 0.90:
            return "Very high AI probability — strong AI indicator"
        elif value > 0.70:
            return "High AI probability — likely AI-generated"
        elif value > 0.60:
            return "Moderate AI probability — possible AI patterns"
        elif value > 0.40:
            return "Uncertain — mixed signals"
        elif value > 0.30:
            return "Low AI probability — likely human-written"
        else:
            return "Very low AI probability — strong human indicator"

    def _interpret_burstiness(self, value: float) -> str:
        """Generate interpretation for burstiness."""
        t = self.thresholds
        if value < t.burstiness_very_low:
            return "Very uniform — strong AI indicator"
        elif value < t.burstiness_low:
            return "Low variation — likely AI"
        elif value < t.burstiness_medium:
            return "Moderate variation — inconclusive"
        elif value < t.burstiness_high:
            return "Natural variation — likely human"
        else:
            return "High variation — strong human indicator"

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
            return "Very uniform — AI indicator"
        elif value < 0.30:
            return "Low variation"
        elif value < 0.50:
            return "Moderate variation"
        else:
            return "High variation — human indicator"
