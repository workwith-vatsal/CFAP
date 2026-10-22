import logging
from typing import Any, Dict, List
from collections import Counter

from backend.app.services.ai.sentiment import SentimentResult
from backend.app.services.ai.emotion import EmotionResult
from backend.app.services.ai.topics import TopicDiscoveryResult

logger = logging.getLogger(__name__)


def calculate_analysis_aggregations(
    sentiments: List[SentimentResult],
    emotions: List[EmotionResult],
    topic_result: TopicDiscoveryResult,
) -> Dict[str, Any]:
    """
    Computes deterministic statistical summaries for sentiment, emotion, and topic discoveries.
    """
    total = len(sentiments)
    if total == 0:
        return {
            "sentiment_summary": {
                "total_analyzed": 0,
                "positive_count": 0,
                "positive_percentage": 0.0,
                "neutral_count": 0,
                "neutral_percentage": 0.0,
                "negative_count": 0,
                "negative_percentage": 0.0,
                "net_sentiment_score": 0.0,
                "average_confidence": 0.0,
                "star_distribution": {},
            },
            "emotion_summary": {
                "dominant_emotion": "neutral",
                "emotion_breakdown": {},
                "average_confidence": 0.0,
            },
            "topic_summary": {
                "total_topics": 0,
                "outlier_count": 0,
                "outlier_percentage": 0.0,
                "top_topics": [],
            },
            "topic_info": [],
        }

    # 1. Sentiment Summary
    sent_counts = Counter(s.sentiment_label for s in sentiments)
    raw_star_counts = Counter(s.raw_sentiment_label for s in sentiments)
    pos_count = sent_counts.get("positive", 0)
    neu_count = sent_counts.get("neutral", 0)
    neg_count = sent_counts.get("negative", 0)

    pos_pct = round((pos_count / total) * 100.0, 2)
    neu_pct = round((neu_count / total) * 100.0, 2)
    neg_pct = round((neg_count / total) * 100.0, 2)

    # Net Sentiment Score = ((Positive - Negative) / Total) * 100
    net_sentiment_score = round(((pos_count - neg_count) / total) * 100.0, 2)
    avg_sent_conf = round(sum(s.sentiment_score for s in sentiments) / total, 4)

    sentiment_summary = {
        "total_analyzed": total,
        "positive_count": pos_count,
        "positive_percentage": pos_pct,
        "neutral_count": neu_count,
        "neutral_percentage": neu_pct,
        "negative_count": neg_count,
        "negative_percentage": neg_pct,
        "net_sentiment_score": net_sentiment_score,
        "average_confidence": avg_sent_conf,
        "star_distribution": dict(raw_star_counts),
    }

    # 2. Emotion Summary
    emotion_labels = [e.emotion_label for e in emotions]
    emotion_counts = Counter(emotion_labels)
    dominant_emotion = emotion_counts.most_common(1)[0][0] if emotion_counts else "neutral"

    all_emotions = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
    emotion_breakdown = {}
    for emo in all_emotions:
        cnt = emotion_counts.get(emo, 0)
        pct = round((cnt / total) * 100.0, 2)
        # Average probability of this emotion across all rows
        avg_prob = round(
            sum(e.emotion_scores.get(emo, 0.0) for e in emotions) / total, 4
        )
        emotion_breakdown[emo] = {
            "count": cnt,
            "percentage": pct,
            "average_probability": avg_prob,
        }

    avg_emo_conf = round(sum(e.emotion_score for e in emotions) / total, 4)

    emotion_summary = {
        "dominant_emotion": dominant_emotion,
        "emotion_breakdown": emotion_breakdown,
        "average_confidence": avg_emo_conf,
    }

    # 3. Topic Summary
    # Extract top 5 topics (excluding outlier if possible, or sorted by count)
    sorted_topics = sorted(
        topic_result.topic_info,
        key=lambda t: t["count"],
        reverse=True,
    )
    top_topics = []
    for t in sorted_topics[:5]:
        top_topics.append({
            "topic_id": t["topic_id"],
            "name": t["name"],
            "count": t["count"],
            "percentage": t["percentage"],
            "top_keywords": [kw["word"] for kw in t.get("keywords", [])[:4]],
        })

    topic_summary = {
        "total_topics": topic_result.total_topics,
        "outlier_count": topic_result.outlier_count,
        "outlier_percentage": topic_result.outlier_percentage,
        "top_topics": top_topics,
    }

    return {
        "sentiment_summary": sentiment_summary,
        "emotion_summary": emotion_summary,
        "topic_summary": topic_summary,
        "topic_info": topic_result.topic_info,
    }
