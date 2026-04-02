"""  
AI Text Detector â€” Ensemble Analysis
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
from src.utils.ui_contract import (
    build_limitations_markdown,
    build_mode_guidance_markdown,
    build_result_reminder_markdown,
)
from src.utils.visualization import ChartGenerator

# â”€â”€â”€ Setup â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

setup_logging("INFO")
logger = get_logger(__name__)
settings = get_settings()

# â”€â”€â”€ Page Configuration â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

st.set_page_config(
    page_title="AI Text Detector â€” Ensemble",
    page_icon="ðŸŽ¯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# â”€â”€â”€ Custom CSS â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€â”€ Cached Resources â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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


# â”€â”€â”€ Sidebar â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

with st.sidebar:
    st.markdown("## âš™ï¸ Settings")
    st.markdown("---")

    st.markdown("### ðŸ“Š Visualization")

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
    st.markdown("### â„¹ï¸ About")
    st.markdown(
        """
        **Ensemble Analyzer** combines two powerful detection methods:
        
        ðŸ§  **GPT-2** (65% weight)
        - Deep perplexity analysis
        - Transformer-based patterns
        
        ðŸ“Š **NLTK** (35% weight)
        - Statistical n-gram models
        - Linguistic features
        
        âš ï¸ **Note**: RoBERTa is disabled (requires fine-tuning).
        See README for fine-tuning guide.
        
        **Accuracy:** ~78-82%
        
        **Processing:** 5-10 seconds
        
        **Memory:** 2-3 GB RAM
        
        **Version:** 2.0.0
        """
    )

    st.markdown("---")
    st.markdown(
        build_mode_guidance_markdown(
            mode_label="Ensemble",
            launch_command="streamlit run ensemble.py",
            speed_hint="5-10s",
            memory_hint="2-3 GB",
        )
    )

    st.markdown("---")
    st.markdown("### 🎯 Why Ensemble?")
    
    st.markdown("""
    Combining multiple models provides:
    
    âœ… **Higher Accuracy** - Each model's strengths compensate for others' weaknesses
    
    âœ… **More Reliable** - Reduces false positives/negatives
    
    âœ… **Transparent** - See how each analyzer votes
    
    âœ… **Robust** - Works across different text styles
    """)

    st.markdown("---")
    st.markdown(build_limitations_markdown())

# â”€â”€â”€ Main Content â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

# Header
st.markdown("""
<div class="main-header-ensemble">
    <h1>ðŸŽ¯ AI Text Detector â€” Ensemble</h1>
    <p>
        <span class="analyzer-badge badge-roberta">RoBERTa</span>
        <span class="analyzer-badge badge-gpt2">GPT-2</span>
        <span class="analyzer-badge badge-nltk">NLTK</span>
        â€¢ Maximum Accuracy â€¢ Multi-Model Consensus â€¢ Production Ready
    </p>
</div>
""", unsafe_allow_html=True)

# Model loading notice
st.markdown("""
<div class="loading-info">
    ðŸ’¡ <strong>First-time setup:</strong> The ensemble will download RoBERTa (~500MB), 
    GPT-2 (~500MB), and NLTK data (~50MB). Subsequent runs will be much faster.
</div>
""", unsafe_allow_html=True)

st.markdown("")

# Text Input
st.markdown("### ðŸ“ Enter Text for Analysis")

text_input = st.text_area(
    label="Paste or type the text you want to analyze",
    height=200,
    placeholder=(
        "Enter the text you want to analyze here...\n\n"
        "For best results with Ensemble analysis:\n"
        "â€¢ Provide at least 200 characters (500+ recommended)\n"
        "â€¢ Longer texts significantly improve accuracy\n"
        "â€¢ English text works best"
    ),
    label_visibility="collapsed",
)

# Character count
if text_input:
    char_count = len(text_input)
    word_count = len(text_input.split())
    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.caption(f"ðŸ“ {char_count} characters")
    with col_info2:
        st.caption(f"ðŸ“ {word_count} words")
    with col_info3:
        if char_count >= 500:
            quality = "ðŸŸ¢ Optimal"
        elif char_count >= 200:
            quality = "ðŸŸ¢ Good"
        elif char_count >= 50:
            quality = "ðŸŸ¡ Short"
        else:
            quality = "ðŸ”´ Very short"
        st.caption(f"Quality: {quality}")

# Analyze button
analyze_clicked = st.button(
    "ðŸŽ¯ Analyze with Ensemble",
    type="primary",
    use_container_width=True,
    disabled=not text_input or len(text_input.strip()) < 10,
)

# â”€â”€â”€ Analysis â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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

        # â”€â”€ Verdict Display â”€â”€
        st.markdown("---")
        st.markdown("### ðŸŽ¯ Detection Result")

        verdict_class = {
            Verdict.AI_GENERATED: "verdict-ai",
            Verdict.LIKELY_AI: "verdict-likely-ai",
            Verdict.UNCERTAIN: "verdict-uncertain",
            Verdict.LIKELY_HUMAN: "verdict-likely-human",
            Verdict.HUMAN_WRITTEN: "verdict-human",
        }

        verdict_emoji = {
            Verdict.AI_GENERATED: "ðŸ¤–",
            Verdict.LIKELY_AI: "ðŸ¤–",
            Verdict.UNCERTAIN: "â“",
            Verdict.LIKELY_HUMAN: "ðŸ‘¤",
            Verdict.HUMAN_WRITTEN: "ðŸ‘¤",
        }

        css_class = verdict_class.get(result.verdict, "verdict-uncertain")
        emoji = verdict_emoji.get(result.verdict, "â“")

        st.markdown(f"""
        <div class="verdict-card {css_class}">
            <h2>{emoji} {result.verdict.value}</h2>
            <p>Confidence: {result.confidence:.1f}% ({result.confidence_level.value})
            â€¢ Analysis Time: {result.analysis_time:.2f}s</p>
        </div>
        """, unsafe_allow_html=True)

        st.caption(build_result_reminder_markdown())

        # ── Confidence Gauge ── â”€â”€
        if show_gauge:
            fig_gauge = charts.create_metrics_gauge(result)
            st.plotly_chart(fig_gauge, use_container_width=True)

        # â”€â”€ Warnings â”€â”€
        if result.warnings:
            for warning in result.warnings:
                st.markdown(f"""
                <div class="warning-box">âš ï¸ {warning}</div>
                """, unsafe_allow_html=True)

        # â”€â”€ Explanation â”€â”€
        st.markdown("### ðŸ’¡ Analysis Explanation")
        st.info(result.explanation)

        # â”€â”€ Detailed Scores â”€â”€
        st.markdown("### ðŸ”¬ Ensemble Score Breakdown")

        for score in result.scores:
            indicator = "ðŸ”´" if score.indicates_ai else "ðŸŸ¢"
            st.markdown(f"""
            <div class="score-row">
                {indicator} <strong>{score.name}</strong>: {score.value:.4f}
                (Weight: {score.weight:.0%}) â€” <em>{score.interpretation}</em>
            </div>
            """, unsafe_allow_html=True)

        # â”€â”€ Visualizations â”€â”€
        st.markdown("### ðŸ“ˆ Visualizations")

        tabs = ["ðŸ“Š Word Frequencies"]
        if show_radar:
            tabs.append("ðŸ“ Score Radar")
        if show_comparison:
            tabs.append("ðŸ” Analyzer Comparison")

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

        # â”€â”€ Text Statistics â”€â”€
        st.markdown("### ðŸ“‹ Text Statistics")

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

        # â”€â”€ Raw Data â”€â”€
        with st.expander("ðŸ”§ Full Analysis Data (JSON)"):
            st.json(result.to_dict())

        logger.info(f"Ensemble analysis displayed: {result.verdict.value}")

    except Exception as e:
        progress_bar.empty()
        logger.error(f"Application error: {e}", exc_info=True)
        st.error(f"âŒ An error occurred: {str(e)}")
        st.info(
            "ðŸ’¡ This might be due to:\n"
            "- Insufficient memory (ensemble requires 4-6GB RAM)\n"
            "- Network issues during model download\n"
            "- Try individual analyzers (`streamlit run app.py` or `streamlit run test.py`) as alternatives"
        )

# â”€â”€â”€ Empty State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

elif not text_input:
    st.markdown("---")

    st.markdown("### ðŸ§ª Try These Examples")

    col_demo1, col_demo2 = st.columns(2)

    with col_demo1:
        st.markdown("#### ðŸ¤– Typical AI-Generated Text")
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
        if st.button("ðŸ“‹ Use AI Example", key="ai_example"):
            st.session_state["text_example"] = example_ai
            st.rerun()

    with col_demo2:
        st.markdown("#### ðŸ‘¤ Typical Human-Written Text")
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
        if st.button("ðŸ“‹ Use Human Example", key="human_example"):
            st.session_state["text_example"] = example_human
            st.rerun()

    st.markdown("""
    <div style="text-align: center; padding: 2rem; color: rgba(255,255,255,0.4);">
        ðŸ‘† Paste text above or use an example, then click <strong>Analyze with Ensemble</strong>
    </div>
    """, unsafe_allow_html=True)

# Handle example text injection
if "text_example" in st.session_state:
    text_input = st.session_state.pop("text_example")

# â”€â”€â”€ Footer â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

st.markdown("""
<div class="footer">
    <p>ðŸŽ¯ AI Text Detector v2.0.0 â€¢ Ensemble Analysis Engine (GPT-2 + NLTK)<br>
    <small>âš ï¸ RoBERTa disabled (requires fine-tuning)</small></p>
    <p>âš ï¸ Results are probabilistic estimates, not definitive classifications.</p>
    <p>No text is stored or transmitted. All processing happens locally.</p>
</div>
""", unsafe_allow_html=True)






