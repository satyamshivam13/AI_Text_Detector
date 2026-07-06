"""Shared CSS for the Streamlit apps.

``BASE_CSS`` holds the styling common to all three entry points (verdict cards,
metric cards, warning box, footer, layout, hidden branding). App-specific styles
(e.g. a page header gradient) are passed to :func:`inject_css` as ``extra_css``.
"""

from __future__ import annotations

import streamlit as st

BASE_CSS = """
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Result cards */
    .verdict-card {
        padding: 1.5rem 2rem;
        border-radius: 12px;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    .verdict-ai {
        background: linear-gradient(135deg, #ff416c, #ff4b2b);
        border: 2px solid #ff416c;
    }
    .verdict-likely-ai {
        background: linear-gradient(135deg, #f7971e, #ffd200);
        border: 2px solid #f7971e;
    }
    .verdict-uncertain {
        background: linear-gradient(135deg, #a8a8a8, #6c6c6c);
        border: 2px solid #a8a8a8;
    }
    .verdict-likely-human {
        background: linear-gradient(135deg, #56ab2f, #a8e063);
        border: 2px solid #56ab2f;
    }
    .verdict-human {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        border: 2px solid #11998e;
    }
    .verdict-card h2 {
        color: white;
        margin: 0;
        font-size: 1.6rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    .verdict-card p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }

    /* Metric cards */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.2rem;
        border-radius: 10px;
        text-align: center;
        transition: transform 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(102, 126, 234, 0.5);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #667eea;
    }
    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.3rem;
    }
    .metric-interpretation {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.45);
        margin-top: 0.2rem;
        font-style: italic;
    }

    /* Score detail */
    .score-row {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: rgba(255, 255, 255, 0.3);
        font-size: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 3rem;
    }

    /* Warning box */
    .warning-box {
        background: rgba(255, 170, 0, 0.1);
        border: 1px solid rgba(255, 170, 0, 0.3);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        padding-top: 1rem;
    }

    /* Loading info box */
    .loading-info {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
"""


def inject_css(extra_css: str = "") -> None:
    """Inject the shared CSS (plus any app-specific ``extra_css``)."""
    st.markdown(f"<style>{BASE_CSS}{extra_css}</style>", unsafe_allow_html=True)
