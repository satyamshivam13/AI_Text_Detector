"""
AI Text Detector — NLTK-Based Analysis
========================================

Streamlit application using NLTK n-gram language models
for detecting AI-generated text content.

Usage:
    streamlit run app.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

from src.analyzers.nltk_analyzer import NLTKAnalyzer
from src.config.settings import Verdict, get_settings
from src.utils.logging_config import get_logger, setup_logging
from src.utils.ui_contract import (
    build_limitations_markdown,
    build_mode_guidance_markdown,
    build_result_reminder_markdown,
)
from src.utils.visualization import ChartGenerator

# ─── Setup ───────────────────────────────────────────────────────────────────

setup_logging("INFO")
logger = get_logger(__name__)
settings = get_settings()

# ─── Page Configuration ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Text Detector — NLTK",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header p {
        color: rgba(255, 255, 255, 0.85);
        margin: 0.5rem 0 0 0;
        font-size: 1.05rem;
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

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Cached Resources ───────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading NLTK language model...")
def load_analyzer(ngram_size: int) -> NLTKAnalyzer:
    """Load and cache the NLTK analyzer."""
    analyzer = NLTKAnalyzer(ngram_size=ngram_size)
    # Force model loading
    _ = analyzer.model
    return analyzer


@st.cache_resource
def load_chart_generator() -> ChartGenerator:
    """Load and cache the chart generator."""
    return ChartGenerator()


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    ngram_size = st.selectbox(
        "N-gram Model Size",
        options=[2, 3, 4],
        index=1,
        help="Higher values capture longer patterns but need more data. "
             "Trigram (3) is recommended for best balance.",
    )

    st.markdown("---")
    st.markdown("### 📊 Visualization")

    top_words = st.slider(
        "Words in Chart",
        min_value=5,
        max_value=20,
        value=10,
        help="Number of top frequent words to display.",
    )

    min_word_count = st.slider(
        "Min Word Frequency",
        min_value=1,
        max_value=5,
        value=2,
        help="Minimum frequency for a word to appear in analysis.",
    )

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        """
        **NLTK-Based Detector** uses n-gram language models
        trained on the Brown corpus to analyze text patterns.

        **Best for:**
        - Quick analysis
        - Statistical pattern detection
        - Lower resource usage

        **Version:** 2.0.0
        """
    )

    st.markdown("---")
    st.markdown(
        build_mode_guidance_markdown(
            mode_label="NLTK",
            launch_command="streamlit run app.py",
            speed_hint="<1s",
            memory_hint="<1 GB",
        )
    )

    st.markdown("---")
    st.markdown("### ?? Interpretation Guide")

    with st.expander("Perplexity Scores"):
        st.markdown("""
        | Score | Meaning |
        |-------|---------|
        | < 30 | Very likely AI |
        | 30-60 | Likely AI |
        | 60-150 | Uncertain |
        | 150-300 | Likely human |
        | > 300 | Very likely human |
        """)

    with st.expander("Burstiness Scores"):
        st.markdown("""
        | Score | Meaning |
        |-------|---------|
        | < 0.10 | Very likely AI |
        | 0.10-0.20 | Likely AI |
        | 0.20-0.30 | Uncertain |
        | 0.30-0.45 | Likely human |
        | > 0.45 | Very likely human |
        """)

    st.markdown("---")
    st.markdown(build_limitations_markdown())

# ─── Main Content ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header">
    <h1>🛡️ AI Text Detector</h1>
    <p>NLTK-Based Analysis • N-gram Language Models • Statistical Pattern Detection</p>
</div>
""", unsafe_allow_html=True)

# Text Input
st.markdown("### 📝 Enter Text for Analysis")

text_input = st.text_area(
    label="Paste or type the text you want to analyze",
    height=200,
    placeholder=(
        "Enter the text you want to analyze here...\n\n"
        "For best results:\n"
        "• Provide at least 200 characters\n"
        "• Longer texts give more accurate results\n"
        "• English text is recommended"
    ),
    label_visibility="collapsed",
)

# Character count
if text_input:
    char_count = len(text_input)
    word_count = len(text_input.split())
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.caption(f"📏 {char_count} characters")
    with col_info2:
        st.caption(f"📝 {word_count} words")
    with col_info3:
        quality = "🟢 Good" if char_count >= 200 else "🟡 Short" if char_count >= 50 else "🔴 Very short"
        st.caption(f"Quality: {quality}")

# Analyze button
analyze_clicked = st.button(
    "🔍 Analyze Text",
    type="primary",
    use_container_width=True,
    disabled=not text_input or len(text_input.strip()) < 10,
)

# ─── Analysis ────────────────────────────────────────────────────────────────

if analyze_clicked and text_input:
    with st.spinner("🔄 Analyzing text patterns..."):
        try:
            # Load analyzer with selected n-gram size
            analyzer = load_analyzer(ngram_size)
            charts = load_chart_generator()

            # Run analysis
            result = analyzer.analyze(text_input)

            # ── Verdict Display ──
            st.markdown("---")
            st.markdown("### 🎯 Detection Result")

            verdict_class = {
                Verdict.AI_GENERATED: "verdict-ai",
                Verdict.LIKELY_AI: "verdict-likely-ai",
                Verdict.UNCERTAIN: "verdict-uncertain",
                Verdict.LIKELY_HUMAN: "verdict-likely-human",
                Verdict.HUMAN_WRITTEN: "verdict-human",
            }

            verdict_emoji = {
                Verdict.AI_GENERATED: "🤖",
                Verdict.LIKELY_AI: "🤖",
                Verdict.UNCERTAIN: "❓",
                Verdict.LIKELY_HUMAN: "👤",
                Verdict.HUMAN_WRITTEN: "👤",
            }

            css_class = verdict_class.get(result.verdict, "verdict-uncertain")
            emoji = verdict_emoji.get(result.verdict, "❓")

            st.markdown(f"""
            <div class="verdict-card {css_class}">
                <h2>{emoji} {result.verdict.value}</h2>
                <p>Confidence: {result.confidence:.1f}% ({result.confidence_level.value})
                � Analysis Time: {result.analysis_time:.2f}s</p>
            </div>
            """, unsafe_allow_html=True)

            st.caption(build_result_reminder_markdown())

            # -- Warnings -- ──
            if result.warnings:
                for warning in result.warnings:
                    st.markdown(f"""
                    <div class="warning-box">⚠️ {warning}</div>
                    """, unsafe_allow_html=True)

            # ── Key Metrics ──
            st.markdown("### 📊 Key Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{result.perplexity:.1f}</div>
                    <div class="metric-label">Perplexity</div>
                    <div class="metric-interpretation">
                        {"Lower = more AI-like" if result.perplexity < 150 else "Higher = more human-like"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{result.burstiness:.3f}</div>
                    <div class="metric-label">Burstiness</div>
                    <div class="metric-interpretation">
                        {"Uniform usage" if result.burstiness < 0.25 else "Varied usage"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{result.lexical_diversity:.1%}</div>
                    <div class="metric-label">Lexical Diversity</div>
                    <div class="metric-interpretation">
                        {"Low variety" if result.lexical_diversity < 0.5 else "Good variety"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with col4:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{result.sentence_variance:.3f}</div>
                    <div class="metric-label">Sentence Variance</div>
                    <div class="metric-interpretation">
                        {"Uniform" if result.sentence_variance < 0.25 else "Varied"}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            # ── Explanation ──
            st.markdown("### 💡 Analysis Explanation")
            st.info(result.explanation)

            # ── Detailed Scores ──
            st.markdown("### 🔬 Detailed Score Breakdown")

            for score in result.scores:
                indicator = "🔴" if score.indicates_ai else "🟢"
                st.markdown(f"""
                <div class="score-row">
                    {indicator} <strong>{score.name}</strong>: {score.value:.4f}
                    (Weight: {score.weight:.0%}) — <em>{score.interpretation}</em>
                </div>
                """, unsafe_allow_html=True)

            # ── Visualizations ──
            st.markdown("### 📈 Visualizations")

            tab1, tab2, tab3 = st.tabs([
                "📊 Word Frequencies",
                "📐 Score Radar",
                "📏 Sentence Lengths",
            ])

            with tab1:
                # Filter by min word count
                filtered_freq = {
                    word: count
                    for word, count in result.metrics.word_frequencies.items()
                    if count >= min_word_count
                }
                fig = charts.create_word_frequency_chart_plotly(
                    filtered_freq, top_n=top_words,
                    title=f"Top {top_words} Content Words (min freq: {min_word_count})",
                )
                st.plotly_chart(fig, use_container_width=True)

            with tab2:
                fig_radar = charts.create_score_breakdown_chart(result)
                st.plotly_chart(fig_radar, use_container_width=True)

            with tab3:
                if result.metrics.sentence_lengths:
                    fig_sent = charts.create_sentence_length_chart(
                        result.metrics.sentence_lengths
                    )
                    st.plotly_chart(fig_sent, use_container_width=True)
                else:
                    st.info("Not enough sentences for length analysis.")

            # ── Text Text ──
            st.markdown("### 📋 Text Statistics")

            stat_col1, stat_col2, stat_col3 = st.columns(3)

            with stat_col1:
                st.metric("Total Characters", f"{result.metrics.total_characters:,}")
                st.metric("Total Words", f"{result.metrics.total_words:,}")

            with stat_col2:
                st.metric("Total Sentences", f"{result.metrics.total_sentences:,}")
                st.metric("Unique Words", f"{result.metrics.unique_words:,}")

            with stat_col3:
                st.metric("Avg Word Length", f"{result.metrics.avg_word_length:.1f}")
                st.metric("Avg Sentence Length", f"{result.metrics.avg_sentence_length:.1f}")

            # ── Analysis Metadata ──
            with st.expander("🔧 Analysis Metadata"):
                st.json(result.to_dict())

            logger.info(f"Analysis displayed: {result.verdict.value}")

        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            st.error(f"❌ An error occurred during analysis: {str(e)}")
            st.info("💡 Try refreshing the page or using a different text.")

# ─── Empty State ─────────────────────────────────────────────────────────────

elif not text_input:
    st.markdown("---")

    col_demo1, col_demo2 = st.columns(2)

    with col_demo1:
        st.markdown("#### 🤖 AI-Generated Example")
        st.code(
            "Artificial intelligence has revolutionized numerous industries "
            "by providing innovative solutions to complex problems. The integration "
            "of machine learning algorithms enables organizations to process vast "
            "amounts of data efficiently and effectively. Furthermore, the development "
            "of natural language processing has significantly enhanced human-computer "
            " communication, making technology more accessible to a broader audience.",
            language=None,
        )

    with col_demo2:
        st.markdown("#### 👤 Human-Written Example")
        st.code(
            "So I was trying to fix my computer yesterday and, well, let me tell "
            "you - it was a disaster! The thing kept crashing every five minutes. "
            "I called my friend Dave (who's supposedly a tech whiz) but even he "
            "was stumped. We ended up ordering pizza and binge-watching Netflix "
            "instead. Sometimes you just gotta know when to give up, we?",
            language=None,
        )

    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);">
        👆 Paste some text above and click <strong>Analyze Text</strong> to get started
    </div>
    """, unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="footer">
    <p>🛡️ AI Text Detector v2.0.0 • NLTK Analysis Engine</p>
    <p>⚠️ Results are probabilistic estimates, not definitive classifications.</p>
    <p>No text is stored or transmitted. All processing happens locally.</p>
</div>
""", unsafe_allow_html=True)









