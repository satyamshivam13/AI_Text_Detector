"""
Visualization Utilities
=======================

Chart generation for analysis results.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

from src.config.settings import get_settings
from src.models.result import AnalysisResult
from src.utils.logging_config import get_logger

matplotlib.use("Agg")
logger = get_logger(__name__)


class ChartGenerator:
    """Generates visualization charts for analysis results."""

    def __init__(self):
        self.settings = get_settings().visualization

    def create_word_frequency_chart_plotly(
        self,
        word_frequencies: Dict[str, int],
        top_n: int = 10,
        title: str = "Top Word Frequencies",
    ) -> go.Figure:
        """
        Create an interactive word frequency bar chart using Plotly.

        Args:
            word_frequencies: Dictionary of word to frequency count.
            top_n: Number of top words to display.
            title: Chart title.

        Returns:
            Plotly Figure object.
        """
        if not word_frequencies:
            fig = go.Figure()
            fig.add_annotation(
                text="No word frequency data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16, color="gray"),
            )
            fig.update_layout(
                title=title,
                height=self.settings.chart_height,
            )
            return fig

        # Sort and take top N
        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:top_n]
        words, counts = zip(*sorted_words)

        # Create gradient colors
        colors = px.colors.sample_colorscale(
            "Viridis", [i / max(len(words) - 1, 1) for i in range(len(words))]
        )

        fig = go.Figure(
            data=[
                go.Bar(
                    x=list(words),
                    y=list(counts),
                    marker=dict(
                        color=colors,
                        line=dict(color="rgba(255,255,255,0.3)", width=1),
                    ),
                    text=list(counts),
                    textposition="auto",
                    textfont=dict(color="white", size=12),
                    hovertemplate="<b>%{x}</b><br>Frequency: %{y}<extra></extra>",
                )
            ]
        )

        fig.update_layout(
            title=dict(text=title, font=dict(size=18, color="white")),
            xaxis=dict(
                title="Words",
                tickangle=-45,
                tickfont=dict(size=11, color="lightgray"),
                titlefont=dict(color="lightgray"),
            ),
            yaxis=dict(
                title="Frequency",
                tickfont=dict(size=11, color="lightgray"),
                titlefont=dict(color="lightgray"),
                gridcolor="rgba(128,128,128,0.2)",
            ),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=self.settings.chart_height,
            margin=dict(l=60, r=30, t=60, b=80),
            hoverlabel=dict(bgcolor="rgba(0,0,0,0.8)", font_size=13),
        )

        return fig

    def create_word_frequency_chart_matplotlib(
        self,
        word_frequencies: Dict[str, int],
        top_n: int = 10,
        title: str = "Top Word Frequencies",
    ) -> plt.Figure:
        """
        Create a word frequency bar chart using Matplotlib.

        Args:
            word_frequencies: Dictionary of word to frequency count.
            top_n: Number of top words to display.
            title: Chart title.

        Returns:
            Matplotlib Figure object.
        """
        fig, ax = plt.subplots(figsize=(10, 5))

        if not word_frequencies:
            ax.text(
                0.5, 0.5, "No word frequency data available",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=14, color="gray",
            )
            ax.set_title(title)
            return fig

        sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)[:top_n]
        words, counts = zip(*sorted_words)

        # Create color gradient
        cmap = plt.cm.viridis
        colors = [cmap(i / max(len(words) - 1, 1)) for i in range(len(words))]

        bars = ax.bar(words, counts, color=colors, edgecolor="white", linewidth=0.5)

        # Add value labels
        for bar, count in zip(bars, counts):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + 0.3,
                str(count),
                ha="center", va="bottom",
                fontsize=9, fontweight="bold",
            )

        ax.set_title(title, fontsize=14, fontweight="bold", pad=15)
        ax.set_xlabel("Words", fontsize=11)
        ax.set_ylabel("Frequency", fontsize=11)
        ax.tick_params(axis="x", rotation=45)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3)

        plt.tight_layout()
        return fig

    def create_metrics_gauge(self, result: AnalysisResult) -> go.Figure:
        """
        Create a gauge chart showing detection confidence.

        Args:
            result: Analysis result object.

        Returns:
            Plotly Figure object.
        """
        confidence = result.confidence

        if result.is_ai_generated:
            bar_color = self.settings.color_ai
            title_text = "AI Detection Confidence"
        elif result.is_human_written:
            bar_color = self.settings.color_human
            title_text = "Human Writing Confidence"
        else:
            bar_color = self.settings.color_uncertain
            title_text = "Detection Confidence"

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=confidence,
                title=dict(text=title_text, font=dict(size=16, color="white")),
                number=dict(suffix="%", font=dict(size=28, color="white")),
                gauge=dict(
                    axis=dict(
                        range=[0, 100],
                        tickwidth=1,
                        tickcolor="gray",
                        tickfont=dict(color="lightgray"),
                    ),
                    bar=dict(color=bar_color),
                    bgcolor="rgba(0,0,0,0)",
                    borderwidth=2,
                    bordercolor="gray",
                    steps=[
                        dict(range=[0, 40], color="rgba(255,75,75,0.15)"),
                        dict(range=[40, 60], color="rgba(255,170,0,0.15)"),
                        dict(range=[60, 80], color="rgba(255,170,0,0.1)"),
                        dict(range=[80, 100], color="rgba(0,204,102,0.15)"),
                    ],
                    threshold=dict(
                        line=dict(color="white", width=3),
                        thickness=0.8,
                        value=confidence,
                    ),
                ),
            )
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=250,
            margin=dict(l=30, r=30, t=60, b=30),
        )

        return fig

    def create_score_breakdown_chart(self, result: AnalysisResult) -> go.Figure:
        """
        Create a radar chart showing score breakdown.

        Args:
            result: Analysis result object.

        Returns:
            Plotly Figure object.
        """
        categories = ["Perplexity", "Burstiness", "Lexical\nDiversity", "Sentence\nVariance"]

        # Normalize scores to 0-100 scale
        settings = get_settings().thresholds

        perplexity_norm = min(100, (result.perplexity / settings.perplexity_high) * 100)
        burstiness_norm = min(100, (result.burstiness / settings.burstiness_high) * 100)
        diversity_norm = min(100, result.lexical_diversity * 100)
        variance_norm = min(100, result.sentence_variance * 100)

        values = [perplexity_norm, burstiness_norm, diversity_norm, variance_norm]
        values.append(values[0])  # Close the radar
        categories_closed = categories + [categories[0]]

        fig = go.Figure()

        fig.add_trace(
            go.Scatterpolar(
                r=values,
                theta=categories_closed,
                fill="toself",
                fillcolor="rgba(102,126,234,0.25)",
                line=dict(color=self.settings.color_primary, width=2),
                marker=dict(size=8, color=self.settings.color_primary),
                name="Scores",
                hovertemplate="%{theta}: %{r:.1f}<extra></extra>",
            )
        )

        fig.update_layout(
            polar=dict(
                bgcolor="rgba(0,0,0,0)",
                radialaxis=dict(
                    visible=True,
                    range=[0, 100],
                    tickfont=dict(size=9, color="lightgray"),
                    gridcolor="rgba(128,128,128,0.3)",
                ),
                angularaxis=dict(
                    tickfont=dict(size=11, color="white"),
                    gridcolor="rgba(128,128,128,0.3)",
                ),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350,
            margin=dict(l=60, r=60, t=40, b=40),
            showlegend=False,
        )

        return fig

    def create_sentence_length_chart(self, sentence_lengths: List[int]) -> go.Figure:
        """
        Create a sentence length distribution chart.

        Args:
            sentence_lengths: List of sentence lengths.

        Returns:
            Plotly Figure object.
        """
        if not sentence_lengths:
            fig = go.Figure()
            fig.add_annotation(
                text="No sentence data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
            )
            return fig

        fig = make_subplots(rows=1, cols=2, subplot_titles=("Distribution", "Trend"))

        # Histogram
        fig.add_trace(
            go.Histogram(
                x=sentence_lengths,
                nbinsx=15,
                marker=dict(
                    color=self.settings.color_primary,
                    line=dict(color="white", width=0.5),
                ),
                name="Distribution",
                hovertemplate="Length: %{x}<br>Count: %{y}<extra></extra>",
            ),
            row=1, col=1,
        )

        # Line chart showing trend
        fig.add_trace(
            go.Scatter(
                x=list(range(1, len(sentence_lengths) + 1)),
                y=sentence_lengths,
                mode="lines+markers",
                line=dict(color=self.settings.color_secondary, width=2),
                marker=dict(size=5, color=self.settings.color_secondary),
                name="Sentence Length",
                hovertemplate="Sentence %{x}: %{y} words<extra></extra>",
            ),
            row=1, col=2,
        )

        # Add mean line
        mean_length = sum(sentence_lengths) / len(sentence_lengths)
        fig.add_hline(
            y=mean_length, row=1, col=2,
            line_dash="dash", line_color="rgba(255,170,0,0.7)",
            annotation_text=f"Mean: {mean_length:.1f}",
            annotation_font_color="rgba(255,170,0,0.9)",
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=300,
            margin=dict(l=50, r=30, t=50, b=40),
            showlegend=False,
        )

        fig.update_xaxes(gridcolor="rgba(128,128,128,0.2)", tickfont=dict(color="lightgray"))
        fig.update_yaxes(gridcolor="rgba(128,128,128,0.2)", tickfont=dict(color="lightgray"))

        return fig