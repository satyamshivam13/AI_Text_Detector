"""
AI Text Detector — GPT-2 Deep Analysis
========================================

Streamlit application using GPT-2 transformer model
for advanced AI-generated text detection.

Usage:
    streamlit run test.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

from src.analyzers.gpt2_analyzer import GPT2Analyzer
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
    page_title="AI Text Detector — GPT-2",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .main-header-gpt2 {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(240, 147, 251, 0.3);
    }
    .main-header-gpt2 h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header-gpt2 p {
        color: rgba(255, 255, 255, 0.85);
        margin: 0.5rem 0 0 0;
        font-size: 1.05rem;
    }

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
    }

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
        border-color: rgba(240, 147, 251, 0.5);
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f093fb;
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

    .score-row {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    .loading-info {
        background: rgba(240, 147, 251, 0.1);
        border: 1px solid rgba(240, 147, 251, 0.3);
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }

    .warning-box {
        background: rgba(255, 170, 0, 0.1);
        border: 1px solid rgba(255, 170, 0, 0.3);
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0;
    }

    .footer {
        text-align: center;
        padding: 2rem 0 1rem 0;
        color: rgba(255, 255, 255, 0.3);
        font-size: 0.8rem;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 3rem;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ─── Cached Resources ───────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading GPT-2 model... (this may take a minute on first run)")
def load_analyzer() -> GPT2Analyzer:
    """Load and cache the GPT-2 analyzer."""
    analyzer = GPT2Analyzer()
    # Force model loading
    _ = analyzer.model
    _ = analyzer.tokenizer
    return analyzer


@st.cache_resource
def load_chart_generator() -> ChartGenerator:
    """Load and cache the chart generator."""
    return ChartGenerator()


# ─── Sidebar ─────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("---")

    st.markdown("### 📊 Visualization")

    top_words = st.slider(
        "Words in Chart",
        min_value=5,
        max_value=20,
        value=10,
        help="Number of top frequent words to display.",
    )

    show_gauge = st.checkbox("Show Confidence Gauge", value=True)
    show_radar = st.checkbox("Show Score Radar", value=True)
    show_sentence_chart = st.checkbox("Show Sentence Analysis", value=True)

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        """
        **GPT-2 Deep Analyzer** uses the GPT-2 transformer model
        (124M parameters) for advanced perplexity-based detection.

        **Best for:**
        - Deep pattern analysis
        - Higher accuracy detection
        - Longer text analysis

        **Note:** First run downloads the GPT-2 model (~500MB).

        **Version:** 2.0.0
        """
    )

    st.markdown("---")
    st.markdown(
        build_mode_guidance_markdown(
            mode_label="GPT-2",
            launch_command="streamlit run test.py",
            speed_hint="2-5s",
            memory_hint="2-3 GB",
        )
    )

    st.markdown("---")
    st.markdown("### ?? Interpretation Guide")

    with st.expander("GPT-2 Perplexity"):
        st.markdown("""
        | Score | Meaning |
        |-------|---------|
        | < 20 | Very strong AI indicator |
        | 20-50 | Strong AI indicator |
        | 50-100 | Likely AI |
        | 100-200 | Uncertain |
        | 200-500 | Likely human |
        | > 500 | Strong human indicator |
        """)

    with st.expander("How GPT-2 Detection Works"):
        st.markdown("""
        GPT-2 calculates how "surprised" it is by each word in the text.

        - **AI text**: GPT-2 is NOT surprised → Low perplexity
        - **Human text**: GPT-2 IS surprised → High perplexity

        This works because AI models produce text that
        other AI models find very predictable.
        """)

    st.markdown("---")
    st.markdown(build_limitations_markdown())

# ─── Main Content ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header-gpt2">
    <h1>🧠 AI Text Detector</h1>
    <p>GPT-2 Deep Analysis • Transformer-Based Detection • Advanced Pattern Recognition</p>
</div>
""", unsafe_allow_html=True)

# Model loading notice
st.markdown("""
<div class="loading-info">
    💡 <strong>First-time setup:</strong> The GPT-2 model (~500MB) will be downloaded
    and cached automatically. Subsequent runs will be much faster.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Text Input
st.markdown("### 📝 Enter Text for Analysis")

text_input = st.text_area(
    label="Paste or type the text you want to analyze",
    height=200,
    placeholder=(
        "Enter the text you want to analyze here...\n\n"
        "For best results with GPT-2 analysis:\n"
        "• Provide at least 200 characters (500+ recommended)\n"
        "• Longer texts significantly improve accuracy\n"
        "• English text works best"
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
        if char_count >= 500:
            quality = "🟢 Optimal"
        elif char_count >= 200:
            quality = "🟢 Good"
        elif char_count >= 50:
            quality = "🟡 Short"
        else:
            quality = "🔴 Very short"
        st.caption(f"Quality: {quality}")

# Analyze button
analyze_clicked = st.button(
    "🧠 Deep Analyze with GPT-2",
    type="primary",
    use_container_width=True,
    disabled=not text_input or len(text_input.strip()) < 10,
)

# ─── Analysis ────────────────────────────────────────────────────────────────

if analyze_clicked and text_input:
    progress_bar = st.progress(0, text="Initializing GPT-2 model...")

    try:
        progress_bar.progress(10, text="Loading GPT-2 model...")
        analyzer = load_analyzer()
        charts = load_chart_generator()

        progress_bar.progress(30, text="Tokenizing text...")
        progress_bar.progress(50, text="Computing deep perplexity...")

        # Run analysis
        result = analyzer.analyze(text_input)

        progress_bar.progress(90, text="Generating visualizations...")

        # ── Verdict Display ──
        progress_bar.progress(100, text="Analysis complete!")
        progress_bar.empty()

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
            • Analysis Time: {result.analysis_time:.2f}s</p>
        </div>
        """, unsafe_allow_html=True)

        st.caption(build_result_reminder_markdown())

        # -- Confidence Gauge -- ──
        if show_gauge:
            fig_gauge = charts.create_metrics_gauge(result)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # ── Warnings ──
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
                <div class="metric-label">GPT-2 Perplexity</div>
                <div class="metric-interpretation">
                    {"Low = AI-like" if result.perplexity < 200 else "High = Human-like"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{result.burstiness:.3f}</div>
                <div class="metric-label">Burstiness</div>
                <div class="metric-interpretation">
                    {"Uniform" if result.burstiness < 0.25 else "Natural variation"}
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{result.lexical_diversity:.1%}</div>
                <div class="metric-label">Lexical Diversity</div>
                <div class="metric-interpretation">
                    {"Low" if result.lexical_diversity < 0.5 else "Good"} vocabulary variety
                </div>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{result.sentence_variance:.3f}</div>
                <div class="metric-label">Sentence Variance</div>
                <div class="metric-interpretation">
                    {"Uniform" if result.sentence_variance < 0.25 else "Varied"} structure
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

        tabs = ["📊 Word Frequencies"]
        if show_radar:
            tabs.append("📐 Score Radar")
        if show_sentence_chart:
            tabs.append("📏 Sentence Analysis")

        tab_objects = st.tabs(tabs)

        # Word Frequencies tab
        with tab_objects[0]:
            fig = charts.create_word_frequency_chart_plotly(
                result.metrics.word_frequencies,
                top_n=top_words,
                title=f"Top {top_words} Content Words",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Score Radar tab
        tab_idx = 1
        if show_radar:
            with tab_objects[tab_idx]:
                fig_radar = charts.create_score_breakdown_chart(result)
                st.plotly_chart(fig_radar, use_container_width=True)
            tab_idx += 1

        # Sentence Analysis tab
        if show_sentence_chart:
            with tab_objects[tab_idx]:
                if result.metrics.sentence_lengths:
                    fig_sent = charts.create_sentence_length_chart(
                        result.metrics.sentence_lengths
                    )
                    st.plotly_chart(fig_sent, use_container_width=True)
                else:
                    st.info("Not enough sentences for length analysis.")

        # ── Text Statistics ──
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

        # ── Raw Data ──
        with st.expander("🔧 Full Analysis Data (JSON)"):
            st.json(result.to_dict())

        logger.info(f"GPT-2 analysis displayed: {result.verdict.value}")

    except Exception as e:
        progress_bar.empty()
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"❌ An error occurred: {str(e)}")
        st.info(
            "💡 This might be due to:\n"
            "- Insufficient memory for GPT-2 model\n"
            "- Network issues during model download\n"
            "- Try the NLTK-based detector (`streamlit run app.py`) as an alternative"
        )

# ─── Empty State ─────────────────────────────────────────────────────────────

elif not text_input:
    st.markdown("---")

    st.markdown("### 🧪 Try These Examples")

    col_demo1, col_demo2 = st.columns(2)

    with col_demo1:
        st.markdown("#### 🤖 Typical AI-Generated Text")
        example_ai = (
            "The advancement of artificial intelligence has fundamentally transformed "
            "the landscape of modern technology. Machine learning algorithms, particularly "
            "deep neural networks, have demonstrated remarkable capabilities across diverse "
            "domains including natural language processing, computer vision, and autonomous "
            "systems. The integration of these technologies into everyday applications has "
            "created unprecedented opportunities for innovation and efficiency improvements. "
            "Furthermore, the continuous evolution of transformer architectures has enabled "
            "significant breakthroughs in language understanding and generation tasks."
        )
        st.code(example_ai, language=None)
        if st.button("📋 Use AI Example", key="ai_example"):
            st.session_state["text_example"] = example_ai
            st.rerun()

    with col_demo2:
        st.markdown("#### 👤 Typical Human-Written Text")
        example_human = (
            "OK so here's the thing about my neighbor's cat - this little furball "
            "has been sneaking into my yard EVERY single morning at like 5am. And "
            "I'm not even a morning person! Last Tuesday it knocked over my entire "
            "herb garden. Basil everywhere. My wife thinks it's hilarious but I spent "
            "three weekends building those raised beds. The cat's name is Mr. Whiskers "
            "which honestly makes it harder to be mad. I tried talking to Janet next "
            "door but she just laughed and gave me cookies. So now I have cookies "
            "and a destroyed herb garden. Life's weird sometimes, you know?"
        )
        st.code(example_human, language=None)
        if st.button("📋 Use Human Example", key="human_example"):
            st.session_state["text_example"] = example_human
            st.rerun()

    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);">
        👆 Paste text above or use an example, then click <strong>Deep Analyze with GPT-2</strong>
    </div>
    """, unsafe_allow_html=True)

# Handle example text injection
if "text_example" in st.session_state:
    text_input = st.session_state.pop("text_example")

# ─── Footer ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="footer">
    <p>🧠 AI Text Detector v2.0.0 • GPT-2 Deep Analysis Engine</p>
    <p>⚠️ Results are probabilistic estimates, not definitive classifications.</p>
    <p>No text is stored or transmitted. All processing happens locally.</p>
</div>
""", unsafe_allow_html=True)







