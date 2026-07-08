"""Shared Streamlit result-rendering components.

The pure mapping helpers (:func:`verdict_css_class`, :func:`verdict_emoji`) are
unit-tested without Streamlit; the ``render_*`` helpers wrap ``st.markdown`` and
are exercised by the app smoke tests.

All user-derived strings are HTML-escaped before being embedded in the
``unsafe_allow_html`` markup, closing the injection risk the audit flagged.
"""

from __future__ import annotations

import html

import streamlit as st

from src.config.settings import Verdict
from src.models.result import AnalysisResult
from src.utils.logging_config import get_logger

_logger = get_logger(__name__)

_VERDICT_CSS = {
    Verdict.AI_GENERATED: "verdict-ai",
    Verdict.LIKELY_AI: "verdict-likely-ai",
    Verdict.UNCERTAIN: "verdict-uncertain",
    Verdict.LIKELY_HUMAN: "verdict-likely-human",
    Verdict.HUMAN_WRITTEN: "verdict-human",
}

_VERDICT_EMOJI = {
    Verdict.AI_GENERATED: "🤖",
    Verdict.LIKELY_AI: "🤖",
    Verdict.UNCERTAIN: "❓",
    Verdict.LIKELY_HUMAN: "👤",
    Verdict.HUMAN_WRITTEN: "👤",
}


def verdict_css_class(verdict: Verdict) -> str:
    """CSS class for a verdict (falls back to the uncertain style)."""
    return _VERDICT_CSS.get(verdict, "verdict-uncertain")


def verdict_emoji(verdict: Verdict) -> str:
    """Emoji for a verdict (falls back to the uncertain glyph)."""
    return _VERDICT_EMOJI.get(verdict, "❓")


def render_verdict_card(result: AnalysisResult) -> None:
    """Render the verdict card (verdict, confidence, analysis time)."""
    css_class = verdict_css_class(result.verdict)
    emoji = verdict_emoji(result.verdict)
    st.markdown(
        f"""
<div class="verdict-card {css_class}">
    <h2>{emoji} {html.escape(result.verdict.value)}</h2>
    <p>Confidence: {result.confidence:.1f}% ({html.escape(result.confidence_level.value)})
    • Analysis Time: {result.analysis_time:.2f}s</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_error(
    exc: Exception,
    user_message: str = (
        "Something went wrong during analysis. Please try again, "
        "possibly with shorter or different text."
    ),
) -> None:
    """Show a generic error to the user and log the full exception server-side.

    Exception strings are never rendered to the UI (they can leak internal
    detail); the traceback goes to the server log instead.
    """
    _logger.error("Unhandled UI error: %s", exc, exc_info=True)
    st.error(f"❌ {html.escape(user_message)}")


def render_warnings(result: AnalysisResult) -> None:
    """Render each analysis warning in a warning box (HTML-escaped)."""
    for warning in result.warnings:
        st.markdown(
            f'<div class="warning-box">⚠️ {html.escape(warning)}</div>',
            unsafe_allow_html=True,
        )


def render_footer(
    engine_label: str, icon: str = "🛡️", note: str = "", version: str = "2.1.0"
) -> None:
    """Render the shared footer with an app-specific engine label and icon.

    ``note`` renders as an optional small second line (e.g. a disabled-analyzer
    disclaimer); it is HTML-escaped.
    """
    note_html = f"<br><small>⚠️ {html.escape(note)}</small>" if note else ""
    st.markdown(
        f"""
<div class="footer">
    <p>{icon} AI Text Detector v{html.escape(version)} • {html.escape(engine_label)}{note_html}</p>
    <p>⚠️ Results are probabilistic estimates, not definitive classifications.</p>
    <p>No text is stored or transmitted. All processing happens locally.</p>
</div>
""",
        unsafe_allow_html=True,
    )
