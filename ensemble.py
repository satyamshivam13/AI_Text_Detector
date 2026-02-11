"""  
AI Text Detector — Ensemble Analysis
======================================

Streamlit application using ensemble of GPT-2 and NLTK
for enhanced AI-generated text detection.

Note: RoBERTa is currently disabled (requires fine-tuning).

Usage:
    streamlit run ensemble.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st

from src.analyzers.ensemble_analyzer import EnsembleAnalyzer
from src.config.settings import Verdict, get_settings
from src.utils.logging_config import get_logger, setup_logging
from src.utils.visualization import ChartGenerator

# ─── Setup ───────────────────────────────────────────────────────────────────

setup_logging("INFO")
logger = get_logger(__name__)
settings = get_settings()

# ─── Page Configuration ─────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Text Detector — Ensemble",
    page_icon="🎯",
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

    .main-header-ensemble {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
    }
    .main-header-ensemble h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .main-header-ensemble p {
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

    .score-row {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        padding: 0.8rem 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
    }

    .loading-info {
        background: rgba(102, 126, 234, 0.1);
        border: 1px solid rgba(102, 126, 234, 0.3);
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

    .analyzer-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        margin: 0.2rem;
        font-weight: 600;
    }
    .badge-roberta {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    .badge-gpt2 {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
    }
    .badge-nltk {
        background: linear-gradient(135deg, #56ab2f, #a8e063);
        color: white;
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

@st.cache_resource(show_spinner="Loading ensemble models... (this may take 2-3 minutes on first run)")
def load_analyzer() -> EnsembleAnalyzer:
    """Load and cache the Ensemble analyzer."""
    analyzer = EnsembleAnalyzer()
    # Force model loading
    _ = analyzer.roberta_analyzer
    _ = analyzer.gpt2_analyzer
    _ = analyzer.nltk_analyzer
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
    show_comparison = st.checkbox("Show Analyzer Comparison", value=True)

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown(
        """
        **Ensemble Analyzer** combines two powerful detection methods:
        
        🧠 **GPT-2** (65% weight)
        - Deep perplexity analysis
        - Transformer-based patterns
        
        📊 **NLTK** (35% weight)
        - Statistical n-gram models
        - Linguistic features
        
        ⚠️ **Note**: RoBERTa is disabled (requires fine-tuning).
        See README for fine-tuning guide.
        
        **Accuracy:** ~78-82%
        
        **Processing:** 5-10 seconds
        
        **Memory:** 2-3 GB RAM
        
        **Version:** 2.0.0
        """
    )

    st.markdown("---")
    st.markdown("### 🎯 Why Ensemble?")
    
    st.markdown("""
    Combining multiple models provides:
    
    ✅ **Higher Accuracy** - Each model's strengths compensate for others' weaknesses
    
    ✅ **More Reliable** - Reduces false positives/negatives
    
    ✅ **Transparent** - See how each analyzer votes
    
    ✅ **Robust** - Works across different text styles
    """)

# ─── Main Content ────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="main-header-ensemble">
    <h1>🎯 AI Text Detector — Ensemble</h1>
    <p>
        <span class="analyzer-badge badge-roberta">RoBERTa</span>
        <span class="analyzer-badge badge-gpt2">GPT-2</span>
        <span class="analyzer-badge badge-nltk">NLTK</span>
        • Maximum Accuracy • Multi-Model Consensus • Production Ready
    </p>
</div>
""", unsafe_allow_html=True)

# Model loading notice
st.markdown("""
<div class="loading-info">
    💡 <strong>First-time setup:</strong> The ensemble will download RoBERTa (~500MB), 
    GPT-2 (~500MB), and NLTK data (~50MB). Subsequent runs will be much faster.
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
        "For best results with Ensemble analysis:\n"
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
    "🎯 Analyze with Ensemble",
    type="primary",
    width="stretch",
    disabled=not text_input or len(text_input.strip()) < 10,
)

# ─── Analysis ────────────────────────────────────────────────────────────────

if analyze_clicked and text_input:
    progress_bar = st.progress(0, text="Initializing ensemble models...")

    try:
        progress_bar.progress(10, text="Loading analyzers...")
        analyzer = load_analyzer()
        charts = load_chart_generator()

        progress_bar.progress(30, text="Running RoBERTa analysis...")
        progress_bar.progress(50, text="Running GPT-2 analysis...")
        progress_bar.progress(70, text="Running NLTK analysis...")
        progress_bar.progress(85, text="Combining results...")

        # Run ensemble analysis
        result = analyzer.analyze(text_input)

        progress_bar.progress(100, text="Analysis complete!")
        progress_bar.empty()

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
            • Analysis Time: {result.analysis_time:.2f}s</p>
        </div>
        """, unsafe_allow_html=True)

        # ── Confidence Gauge ──
        if show_gauge:
            fig_gauge = charts.create_metrics_gauge(result)
            st.plotly_chart(fig_gauge, width="stretch")

        # ── Warnings ──
        if result.warnings:
            for warning in result.warnings:
                st.markdown(f"""
                <div class="warning-box">⚠️ {warning}</div>
                """, unsafe_allow_html=True)

        # ── Explanation ──
        st.markdown("### 💡 Analysis Explanation")
        st.info(result.explanation)

        # ── Detailed Scores ──
        st.markdown("### 🔬 Ensemble Score Breakdown")

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
        if show_comparison:
            tabs.append("🔍 Analyzer Comparison")

        tab_objects = st.tabs(tabs)

        # Word Frequencies tab
        with tab_objects[0]:
            fig = charts.create_word_frequency_chart_plotly(
                result.metrics.word_frequencies,
                top_n=top_words,
                title=f"Top {top_words} Content Words",
            )
            st.plotly_chart(fig, width="stretch")

        # Score Radar tab
        tab_idx = 1
        if show_radar:
            with tab_objects[tab_idx]:
                fig_radar = charts.create_score_breakdown_chart(result)
                st.plotly_chart(fig_radar, width="stretch")
            tab_idx += 1

        # Analyzer Comparison tab
        if show_comparison:
            with tab_objects[tab_idx]:
                st.markdown("#### Individual Analyzer Results")
                
                # Extract individual scores
                scores_data = []
                for score in result.scores[1:]:  # Skip ensemble score
                    scores_data.append({
                        "Analyzer": score.name.replace(" Score", "").replace(" Perplexity Score", "").replace(" Statistical Score", ""),
                        "Value": f"{score.value:.2%}",
                        "Weight": f"{score.weight:.0%}",
                        "Verdict": score.interpretation
                    })
                
                if scores_data:
                    import pandas as pd
                    df = pd.DataFrame(scores_data)
                    st.dataframe(df, hide_index=True, use_container_width=True)

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
            st.metric("Lexical Diversity", f"{result.lexical_diversity:.1%}")
            st.metric("Avg Perplexity", f"{result.perplexity:.1f}")

        # ── Raw Data ──
        with st.expander("🔧 Full Analysis Data (JSON)"):
            st.json(result.to_dict())

        logger.info(f"Ensemble analysis displayed: {result.verdict.value}")

    except Exception as e:
        progress_bar.empty()
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"❌ An error occurred: {str(e)}")
        st.info(
            "💡 This might be due to:\n"
            "- Insufficient memory (ensemble requires 4-6GB RAM)\n"
            "- Network issues during model download\n"
            "- Try individual analyzers (`streamlit run app.py` or `streamlit run test.py`) as alternatives"
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
        👆 Paste text above or use an example, then click <strong>Analyze with Ensemble</strong>
    </div>
    """, unsafe_allow_html=True)

# Handle example text injection
if "text_example" in st.session_state:
    text_input = st.session_state.pop("text_example")

# ─── Footer ──────────────────────────────────────────────────────────────────

st.markdown("""
<div class="footer">
    <p>🎯 AI Text Detector v2.0.0 • Ensemble Analysis Engine (GPT-2 + NLTK)<br>
    <small>⚠️ RoBERTa disabled (requires fine-tuning)</small></p>
    <p>⚠️ Results are probabilistic estimates, not definitive classifications.</p>
    <p>No text is stored or transmitted. All processing happens locally.</p>
</div>
""", unsafe_allow_html=True)
