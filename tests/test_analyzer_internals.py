"""Pure-method tests for analyzer interpretation/explanation/verdict logic.

None of these load transformer or Brown-corpus models — they exercise the
branchy string/verdict helpers directly.
"""

import pytest

from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.config.settings import ConfidenceLevel, Verdict
from src.models.result import AnalysisResult, TextMetrics


@pytest.fixture
def nltk():
    # Construction does NOT build the Brown model (that happens lazily on first
    # perplexity computation), so this is fast.
    return NLTKAnalyzer(ngram_size=3)


# --------------------------------------------------------------------------- #
# BaseAnalyzer._determine_verdict (inherited, exercised via NLTKAnalyzer)
# --------------------------------------------------------------------------- #
class TestVerdictThresholds:
    def _result(self, perplexity, burstiness, ld, sv, text_length=600):
        r = AnalysisResult(
            perplexity=perplexity,
            burstiness=burstiness,
            lexical_diversity=ld,
            sentence_variance=sv,
            text_length=text_length,
        )
        return r

    def test_strong_ai_signals(self, nltk):
        r = self._result(perplexity=10, burstiness=0.05, ld=0.2, sv=0.05)
        nltk._determine_verdict(r)
        assert r.verdict in (Verdict.AI_GENERATED, Verdict.LIKELY_AI)
        assert r.confidence_level in list(ConfidenceLevel)

    def test_strong_human_signals(self, nltk):
        r = self._result(perplexity=500, burstiness=0.6, ld=0.9, sv=0.9)
        nltk._determine_verdict(r)
        assert r.verdict in (Verdict.HUMAN_WRITTEN, Verdict.LIKELY_HUMAN)

    def test_mixed_is_uncertain_ish(self, nltk):
        r = self._result(perplexity=150, burstiness=0.28, ld=0.5, sv=0.3)
        nltk._determine_verdict(r)
        assert r.verdict in list(Verdict)
        assert 0.0 <= r.confidence <= 100.0

    def test_short_text_lowers_reliability(self, nltk):
        long_r = self._result(perplexity=10, burstiness=0.05, ld=0.2, sv=0.05, text_length=600)
        short_r = self._result(perplexity=10, burstiness=0.05, ld=0.2, sv=0.05, text_length=60)
        nltk._determine_verdict(long_r)
        nltk._determine_verdict(short_r)
        assert short_r.confidence <= long_r.confidence


# --------------------------------------------------------------------------- #
# BaseAnalyzer._generate_explanation branches
# --------------------------------------------------------------------------- #
class TestExplanationBranches:
    def test_ai_leaning_explanation(self, nltk):
        r = AnalysisResult(
            perplexity=20, burstiness=0.05, lexical_diversity=0.2, sentence_variance=0.05
        )
        text = nltk._generate_explanation(r)
        assert "perplexity" in text.lower()
        assert "AI" in text or "ai" in text

    def test_human_leaning_explanation(self, nltk):
        r = AnalysisResult(
            perplexity=500, burstiness=0.6, lexical_diversity=0.9, sentence_variance=0.9
        )
        text = nltk._generate_explanation(r)
        assert "human" in text.lower()

    def test_warnings_included(self, nltk):
        r = AnalysisResult(
            perplexity=100, burstiness=0.3, lexical_diversity=0.5, sentence_variance=0.3
        )
        r.add_warning("Text is very short.")
        text = nltk._generate_explanation(r)
        assert "short" in text.lower()


# --------------------------------------------------------------------------- #
# analyze() error path
# --------------------------------------------------------------------------- #
class TestAnalyzeErrorPath:
    def test_perform_analysis_failure_is_contained(self, nltk):
        def boom(text, result):
            raise RuntimeError("synthetic failure")

        nltk._perform_analysis = boom
        result = nltk.analyze("This is a sufficiently long piece of text to analyze fully.")
        assert result.verdict == Verdict.UNCERTAIN
        assert result.confidence == 0.0
        assert any("error" in w.lower() for w in result.warnings)


# --------------------------------------------------------------------------- #
# NLTK interpretation helpers (pure)
# --------------------------------------------------------------------------- #
class TestNLTKInterpretations:
    def test_perplexity_interpretations_cover_ranges(self, nltk):
        outputs = [nltk._interpret_perplexity(v) for v in (10, 45, 100, 200, 5000)]
        assert len(set(outputs)) >= 4  # distinct messages across ranges

    def test_burstiness_interpretations(self, nltk):
        outputs = [nltk._interpret_burstiness(v) for v in (0.05, 0.15, 0.25, 0.4, 0.6)]
        assert len(set(outputs)) >= 4

    def test_lexical_and_sentence_interpretations(self, nltk):
        assert nltk._interpret_lexical_diversity(0.2)
        assert nltk._interpret_lexical_diversity(0.9)
        assert nltk._interpret_sentence_variance(0.05)
        assert nltk._interpret_sentence_variance(0.6)


# --------------------------------------------------------------------------- #
# GPT-2 / RoBERTa interpretation helpers (construction loads no model)
# --------------------------------------------------------------------------- #
class TestTransformerInterpretations:
    def test_gpt2_interpretations(self):
        from src.analyzers.gpt2_analyzer import GPT2Analyzer

        a = GPT2Analyzer()
        assert a._interpret_gpt2_perplexity(10) != a._interpret_gpt2_perplexity(1000)
        assert a._interpret_entropy(2.0) != a._interpret_entropy(9.0)
        assert a._interpret_burstiness(0.05) != a._interpret_burstiness(0.5)

    def test_roberta_interpretations(self):
        from src.analyzers.roberta_analyzer import RoBERTaAnalyzer

        a = RoBERTaAnalyzer()
        assert a._interpret_roberta_score(0.95) != a._interpret_roberta_score(0.1)


# --------------------------------------------------------------------------- #
# Ensemble explanation / interpretation branches (no model load)
# --------------------------------------------------------------------------- #
class TestEnsembleNarrative:
    def _ensemble(self):
        from src.analyzers.ensemble_analyzer import EnsembleAnalyzer

        return EnsembleAnalyzer()

    def test_interpret_ensemble_score_ranges(self):
        a = self._ensemble()
        outs = [a._interpret_ensemble_score(v) for v in (0.9, 0.75, 0.62, 0.5, 0.32, 0.1)]
        assert len(set(outs)) >= 5

    def _combined(self, a, gpt2_ai, nltk_ai):
        base = AnalysisResult(metrics=TextMetrics(total_words=40, unique_words=30))
        roberta = a._disabled_roberta_result()
        gpt2 = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=15.0 if gpt2_ai else 80.0)
        nltk = AnalysisResult(verdict=Verdict.LIKELY_AI, perplexity=3000.0 if nltk_ai else 800.0)
        return a._combine_results(base, roberta, gpt2, nltk), roberta, gpt2, nltk

    def test_all_agree_ai(self):
        a = self._ensemble()
        combined, rob, g, n = self._combined(a, True, True)
        a._determine_verdict(combined)
        text = a._generate_ensemble_explanation(combined, rob, g, n)
        assert "agree" in text.lower()

    def test_all_agree_human(self):
        a = self._ensemble()
        combined, rob, g, n = self._combined(a, False, False)
        a._determine_verdict(combined)
        text = a._generate_ensemble_explanation(combined, rob, g, n)
        assert "human" in text.lower()

    def test_mixed_signals(self):
        a = self._ensemble()
        combined, rob, g, n = self._combined(a, True, False)
        a._determine_verdict(combined)
        text = a._generate_ensemble_explanation(combined, rob, g, n)
        assert "mixed" in text.lower() or "agree" in text.lower()
