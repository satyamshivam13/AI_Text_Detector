"""Shared Streamlit UI helpers.

The three entry-point apps (``app.py``, ``test.py``, ``ensemble.py``) previously
duplicated their CSS, verdict/emoji mappings, verdict-card, warning, and footer
rendering. Those shared pieces live here so a change is made once and stays
consistent across apps.

- :mod:`src.ui.styles` — common CSS + ``inject_css``.
- :mod:`src.ui.components` — verdict/emoji maps and result-rendering helpers.
"""

from src.ui.components import (
    render_error,
    render_footer,
    render_verdict_card,
    render_warnings,
    verdict_css_class,
    verdict_emoji,
)
from src.ui.styles import BASE_CSS, inject_css

__all__ = [
    "BASE_CSS",
    "inject_css",
    "render_error",
    "render_footer",
    "render_verdict_card",
    "render_warnings",
    "verdict_css_class",
    "verdict_emoji",
]
