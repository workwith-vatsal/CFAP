"""
Server-side chart generation engine for CFAP PDF reports.
Uses Matplotlib (Agg headless backend) to render vector-quality charts
directly into in-memory Byte streams for ReportLab flowable embedding.
"""

import io
import logging
from typing import Any, Dict, List, Optional
import matplotlib

# Set headless backend before importing pyplot
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
from reportlab.platypus import Image

logger = logging.getLogger(__name__)

# Chart Color Tokens
HEX_PRIMARY = "#4338CA"
HEX_POSITIVE = "#10B981"
HEX_NEUTRAL = "#94A3B8"
HEX_NEGATIVE = "#EF4444"
HEX_TEXT_DARK = "#1E293B"
HEX_TEXT_MUTED = "#64748B"
HEX_GRID = "#F1F5F9"
HEX_BG = "#FFFFFF"

EMOTION_COLORS = {
    "joy": "#10B981",
    "surprise": "#3B82F6",
    "neutral": "#94A3B8",
    "sadness": "#6366F1",
    "fear": "#F59E0B",
    "anger": "#EF4444",
    "disgust": "#D97706",
}


class ReportChartGenerator:
    """Generates server-side analytics charts as ReportLab Image Flowables."""

    @staticmethod
    def _create_fig(figsize=(5, 2.5), dpi=200):
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        fig.patch.set_facecolor(HEX_BG)
        ax.set_facecolor(HEX_BG)
        return fig, ax

    @staticmethod
    def _to_flowable(fig, width_pt: float, height_pt: float) -> Image:
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close(fig)
        buf.seek(0)
        return Image(buf, width=width_pt, height=height_pt)

    @classmethod
    def generate_sentiment_donut_chart(
        cls,
        sentiment_dist: Dict[str, Any],
        width_pt: float = 240,
        height_pt: float = 140,
    ) -> Optional[Image]:
        def _extract(val: Any) -> int:
            if isinstance(val, dict):
                return int(val.get("count", 0))
            if isinstance(val, (int, float)):
                return int(val)
            return 0

        pos = _extract(sentiment_dist.get("positive"))
        neu = _extract(sentiment_dist.get("neutral"))
        neg = _extract(sentiment_dist.get("negative"))

        total = pos + neu + neg
        if total == 0:
            return None

        labels = ["Positive", "Neutral", "Negative"]
        sizes = [pos, neu, neg]
        colors = [HEX_POSITIVE, HEX_NEUTRAL, HEX_NEGATIVE]

        # Filter out 0 sizes for clean labels
        filtered = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
        if not filtered:
            return None

        f_labels, f_sizes, f_colors = zip(*filtered)

        fig, ax = cls._create_fig(figsize=(4.0, 2.3), dpi=200)

        wedges, texts, autotexts = ax.pie(
            f_sizes,
            labels=f_labels,
            autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct * total / 100.0))})" if pct >= 5 else "",
            pctdistance=0.75,
            startangle=140,
            colors=f_colors,
            wedgeprops=dict(width=0.45, edgecolor="#FFFFFF", linewidth=2),
            textprops=dict(color=HEX_TEXT_DARK, fontsize=8),
        )

        for autotext in autotexts:
            autotext.set_color(HEX_TEXT_DARK)
            autotext.set_fontsize(7.5)
            autotext.set_weight("bold")

        ax.axis("equal")
        return cls._to_flowable(fig, width_pt, height_pt)

    @classmethod
    def generate_emotion_bar_chart(
        cls,
        top_emotions: List[Dict[str, Any]],
        width_pt: float = 260,
        height_pt: float = 140,
    ) -> Optional[Image]:
        """Generates a clean horizontal bar chart of discrete emotion distribution."""
        if not top_emotions:
            return None

        # Take up to top 6 emotions and reverse for top-down display
        items = list(reversed(top_emotions[:6]))
        names = [item.get("emotion", "").capitalize() for item in items]
        counts = [item.get("count", 0) for item in items]
        pcts = [item.get("percentage", 0.0) for item in items]
        colors = [EMOTION_COLORS.get(item.get("emotion", "").lower(), HEX_PRIMARY) for item in items]

        if not any(counts):
            return None

        fig, ax = cls._create_fig(figsize=(4.5, 2.3), dpi=200)

        y_pos = np.arange(len(names))
        bars = ax.barh(y_pos, counts, height=0.55, color=colors, edgecolor="none")

        ax.set_yticks(y_pos)
        ax.set_yticklabels(names, fontsize=8, color=HEX_TEXT_DARK, fontweight="medium")
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=4))
        ax.tick_params(axis="x", labelsize=7.5, colors=HEX_TEXT_MUTED)

        # Remove spines
        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#E2E8F0")

        # Value annotations
        max_val = max(counts) if counts else 1
        for i, (bar, pct, count) in enumerate(zip(bars, pcts, counts)):
            ax.text(
                count + max_val * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}% ({count})",
                va="center",
                ha="left",
                fontsize=7.5,
                color=HEX_TEXT_MUTED,
                fontweight="bold",
            )

        ax.set_xlim(0, max_val * 1.35)
        ax.grid(axis="x", linestyle="--", alpha=0.5, color=HEX_GRID)
        ax.set_axisbelow(True)

        return cls._to_flowable(fig, width_pt, height_pt)

    @classmethod
    def generate_topic_distribution_chart(
        cls,
        top_topics: List[Dict[str, Any]],
        width_pt: float = 480,
        height_pt: float = 160,
    ) -> Optional[Image]:
        """Generates a horizontal bar chart displaying top discovered topic clusters."""
        valid_topics = [t for t in top_topics if t.get("topic_id") != -1]
        if not valid_topics:
            return None

        items = list(reversed(valid_topics[:8]))
        labels = []
        for t in items:
            raw_lbl = t.get("label", f"Topic {t.get('topic_id')}")
            # Truncate long topic names cleanly
            if len(raw_lbl) > 28:
                raw_lbl = raw_lbl[:25] + "..."
            labels.append(raw_lbl)

        counts = [t.get("count", 0) for t in items]

        if not any(counts):
            return None

        fig, ax = cls._create_fig(figsize=(7.5, 2.5), dpi=200)
        y_pos = np.arange(len(labels))

        bars = ax.barh(y_pos, counts, height=0.6, color=HEX_PRIMARY, alpha=0.9)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8, color=HEX_TEXT_DARK)
        ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True, nbins=5))
        ax.tick_params(axis="x", labelsize=7.5, colors=HEX_TEXT_MUTED)

        for spine in ["top", "right", "left"]:
            ax.spines[spine].set_visible(False)
        ax.spines["bottom"].set_color("#E2E8F0")

        max_val = max(counts) if counts else 1
        for bar, count in zip(bars, counts):
            ax.text(
                count + max_val * 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{count}",
                va="center",
                ha="left",
                fontsize=7.5,
                color=HEX_TEXT_MUTED,
                fontweight="bold",
            )

        ax.set_xlim(0, max_val * 1.15)
        ax.grid(axis="x", linestyle="--", alpha=0.5, color=HEX_GRID)
        ax.set_axisbelow(True)

        return cls._to_flowable(fig, width_pt, height_pt)

    @classmethod
    def generate_temporal_trend_chart(
        cls,
        trends: Dict[str, Any],
        width_pt: float = 480,
        height_pt: float = 150,
    ) -> Optional[Image]:
        """Generates volume and sentiment trend line chart over temporal buckets."""
        if not trends or not trends.get("has_temporal_data"):
            return None

        points = trends.get("data_points", [])
        if not points or len(points) < 2:
            return None

        periods = [p.get("period", "") for p in points]
        volumes = [p.get("total_count", 0) for p in points]
        nss_scores = [p.get("nss", 0.0) for p in points]

        fig, ax1 = cls._create_fig(figsize=(7.5, 2.3), dpi=200)

        # Volume Bar
        x = np.arange(len(periods))
        ax1.bar(x, volumes, width=0.4, color="#CBD5E1", alpha=0.7, label="Feedback Volume")
        ax1.set_ylabel("Volume", fontsize=8, color=HEX_TEXT_MUTED)
        ax1.tick_params(axis="y", labelsize=7.5, colors=HEX_TEXT_MUTED)

        # NSS Line
        ax2 = ax1.twinx()
        ax2.plot(x, nss_scores, color=HEX_PRIMARY, marker="o", linewidth=2, markersize=4, label="NSS Trend")
        ax2.set_ylabel("Net Sentiment Score", fontsize=8, color=HEX_PRIMARY)
        ax2.tick_params(axis="y", labelsize=7.5, colors=HEX_PRIMARY)
        ax2.set_ylim(-105, 105)
        ax2.axhline(0, color=HEX_TEXT_MUTED, linestyle=":", linewidth=0.8, alpha=0.6)

        ax1.set_xticks(x)
        # Format labels if too many
        step = max(1, len(periods) // 8)
        formatted_labels = [periods[i] if i % step == 0 else "" for i in range(len(periods))]
        ax1.set_xticklabels(formatted_labels, fontsize=7.5, color=HEX_TEXT_DARK, rotation=0)

        for ax in [ax1, ax2]:
            for spine in ["top", "left", "right"]:
                ax.spines[spine].set_visible(False)
            ax.spines["bottom"].set_color("#E2E8F0")

        ax1.grid(axis="y", linestyle="--", alpha=0.4, color=HEX_GRID)

        return cls._to_flowable(fig, width_pt, height_pt)
