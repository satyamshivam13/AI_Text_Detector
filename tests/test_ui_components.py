"""Tests for the shared UI component helpers (pure mapping functions)."""

from src.config.settings import Verdict
from src.ui.components import render_error, verdict_css_class, verdict_emoji
from src.ui.styles import BASE_CSS


class TestVerdictMappings:
    def test_every_verdict_has_a_css_class(self):
        for verdict in Verdict:
            css = verdict_css_class(verdict)
            assert css.startswith("verdict-")

    def test_every_verdict_has_an_emoji(self):
        for verdict in Verdict:
            assert verdict_emoji(verdict)

    def test_ai_and_human_map_distinctly(self):
        assert verdict_css_class(Verdict.AI_GENERATED) == "verdict-ai"
        assert verdict_css_class(Verdict.HUMAN_WRITTEN) == "verdict-human"
        assert verdict_css_class(Verdict.LIKELY_AI) == "verdict-likely-ai"
        assert verdict_css_class(Verdict.LIKELY_HUMAN) == "verdict-likely-human"
        assert verdict_css_class(Verdict.UNCERTAIN) == "verdict-uncertain"


class TestBaseCss:
    def test_base_css_defines_shared_classes(self):
        for cls in (".verdict-card", ".metric-card", ".warning-box", ".footer"):
            assert cls in BASE_CSS


class TestRenderError:
    def test_render_error_does_not_raise_or_leak(self, caplog):
        # Should log the exception (server-side) and not propagate it.
        with caplog.at_level("ERROR"):
            render_error(ValueError("secret internal detail"))
        # The exception text is logged, not returned/raised.
        assert any("secret internal detail" in r.message or r.exc_info for r in caplog.records)
