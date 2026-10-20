import numpy as np
import pytest

from backend.app.services.ai.aggregation import calculate_analysis_aggregations
from backend.app.services.ai.embeddings import EmbeddingStorage
from backend.app.services.ai.emotion import EmotionResult
from backend.app.services.ai.sentiment import SentimentResult, map_star_to_sentiment
from backend.app.services.ai.topics import TopicDiscoveryResult, TopicItem


def test_star_to_sentiment_mapping():
    # 1 and 2 stars -> negative
    assert map_star_to_sentiment("1 star") == "negative"
    assert map_star_to_sentiment("2 stars") == "negative"
    assert map_star_to_sentiment("1") == "negative"
    assert map_star_to_sentiment("2") == "negative"

    # 3 stars -> neutral
    assert map_star_to_sentiment("3 stars") == "neutral"
    assert map_star_to_sentiment("3") == "neutral"

    # 4 and 5 stars -> positive
    assert map_star_to_sentiment("4 stars") == "positive"
    assert map_star_to_sentiment("5 stars") == "positive"
    assert map_star_to_sentiment("4") == "positive"
    assert map_star_to_sentiment("5") == "positive"

    # Unknown -> default neutral
    assert map_star_to_sentiment("unknown") == "neutral"


def test_embedding_storage_serialization_and_deserialization():
    # Vector of 384 dimensions
    original_vec = np.random.randn(384).astype(np.float32)

    # Serialize to bytes
    serialized_bytes = EmbeddingStorage.serialize(original_vec)
    assert isinstance(serialized_bytes, bytes)
    assert len(serialized_bytes) == 384 * 4  # 4 bytes per float32 = 1536 bytes

    # Deserialize back
    deserialized_vec = EmbeddingStorage.deserialize(serialized_bytes)
    assert isinstance(deserialized_vec, np.ndarray)
    assert deserialized_vec.shape == (384,)
    np.testing.assert_allclose(original_vec, deserialized_vec, rtol=1e-6)


def test_calculate_analysis_aggregations():
    sentiments = [
        SentimentResult(sentiment_label="positive", raw_sentiment_label="5 stars", sentiment_score=0.95),
        SentimentResult(sentiment_label="positive", raw_sentiment_label="4 stars", sentiment_score=0.85),
        SentimentResult(sentiment_label="neutral", raw_sentiment_label="3 stars", sentiment_score=0.60),
        SentimentResult(sentiment_label="negative", raw_sentiment_label="1 star", sentiment_score=0.90),
    ]

    emotions = [
        EmotionResult(emotion_label="joy", emotion_score=0.88, emotion_scores={"joy": 0.88, "anger": 0.02, "fear": 0.01, "neutral": 0.05, "sadness": 0.02, "surprise": 0.01, "disgust": 0.01}),
        EmotionResult(emotion_label="joy", emotion_score=0.80, emotion_scores={"joy": 0.80, "anger": 0.05, "fear": 0.01, "neutral": 0.10, "sadness": 0.02, "surprise": 0.01, "disgust": 0.01}),
        EmotionResult(emotion_label="neutral", emotion_score=0.70, emotion_scores={"joy": 0.10, "anger": 0.05, "fear": 0.05, "neutral": 0.70, "sadness": 0.05, "surprise": 0.03, "disgust": 0.02}),
        EmotionResult(emotion_label="anger", emotion_score=0.92, emotion_scores={"joy": 0.01, "anger": 0.92, "fear": 0.02, "neutral": 0.02, "sadness": 0.01, "surprise": 0.01, "disgust": 0.01}),
    ]

    topic_res = TopicDiscoveryResult(
        row_topics=[
            TopicItem(topic_id=0, topic_label="Topic 0: great, app"),
            TopicItem(topic_id=0, topic_label="Topic 0: great, app"),
            TopicItem(topic_id=1, topic_label="Topic 1: billing, charge"),
            TopicItem(topic_id=1, topic_label="Topic 1: billing, charge"),
        ],
        topic_info=[
            {
                "topic_id": 0,
                "name": "Topic 0: great, app",
                "count": 2,
                "percentage": 50.0,
                "keywords": [{"word": "great", "score": 0.8}, {"word": "app", "score": 0.7}],
            },
            {
                "topic_id": 1,
                "name": "Topic 1: billing, charge",
                "count": 2,
                "percentage": 50.0,
                "keywords": [{"word": "billing", "score": 0.9}, {"word": "charge", "score": 0.85}],
            },
        ],
        total_topics=2,
        outlier_count=0,
        outlier_percentage=0.0,
    )

    agg = calculate_analysis_aggregations(sentiments, emotions, topic_res)

    # Verify sentiment summary
    sent_summary = agg["sentiment_summary"]
    assert sent_summary["total_analyzed"] == 4
    assert sent_summary["positive_count"] == 2
    assert sent_summary["positive_percentage"] == 50.0
    assert sent_summary["neutral_count"] == 1
    assert sent_summary["neutral_percentage"] == 25.0
    assert sent_summary["negative_count"] == 1
    assert sent_summary["negative_percentage"] == 25.0
    # Net sentiment = ((2 - 1) / 4) * 100 = 25.0
    assert sent_summary["net_sentiment_score"] == 25.0

    # Verify emotion summary
    emo_summary = agg["emotion_summary"]
    assert emo_summary["dominant_emotion"] == "joy"
    assert emo_summary["emotion_breakdown"]["joy"]["count"] == 2
    assert emo_summary["emotion_breakdown"]["anger"]["count"] == 1

    # Verify topic summary
    top_summary = agg["topic_summary"]
    assert top_summary["total_topics"] == 2
    assert len(top_summary["top_topics"]) == 2
