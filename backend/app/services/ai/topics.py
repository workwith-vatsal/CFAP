import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from bertopic import BERTopic
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TopicItem:
    topic_id: int
    topic_label: str


@dataclass
class TopicDiscoveryResult:
    row_topics: List[TopicItem]
    topic_info: List[Dict[str, Any]]
    total_topics: int
    outlier_count: int
    outlier_percentage: float


class TopicService:
    """
    Topic Modeling and Discovery Service using BERTopic.
    Discovers themes, extracts c-TF-IDF keyword representations, and assigns topics to feedback rows.
    """

    def discover_topics(
        self,
        texts: List[str],
        embeddings: Optional[np.ndarray] = None,
    ) -> TopicDiscoveryResult:
        """
        Discovers topics from feedback texts and precomputed embeddings.
        Gracefully handles small datasets and outliers.
        """
        n_samples = len(texts)
        if n_samples == 0:
            return TopicDiscoveryResult(
                row_topics=[],
                topic_info=[],
                total_topics=0,
                outlier_count=0,
                outlier_percentage=0.0,
            )

        # Handle very small datasets (< 5 samples) gracefully without HDBSCAN failure
        if n_samples < 5:
            default_label = "General Feedback"
            row_topics = [TopicItem(topic_id=0, topic_label=default_label) for _ in range(n_samples)]
            topic_info = [
                {
                    "topic_id": 0,
                    "name": default_label,
                    "count": n_samples,
                    "percentage": 100.0,
                    "keywords": [{"word": word, "score": 1.0} for word in texts[0].split()[:5]],
                }
            ]
            return TopicDiscoveryResult(
                row_topics=row_topics,
                topic_info=topic_info,
                total_topics=1,
                outlier_count=0,
                outlier_percentage=0.0,
            )

        # Dynamic parameter tuning based on dataset volume
        min_cluster_size = min(settings.bertopic_min_topic_size, max(2, n_samples // 10))
        n_neighbors = min(15, max(2, n_samples - 1))
        n_components = min(5, max(2, n_samples - 1))

        try:
            umap_model = UMAP(
                n_neighbors=n_neighbors,
                n_components=n_components,
                min_dist=0.0,
                metric="cosine",
                random_state=42,
            )
            hdbscan_model = HDBSCAN(
                min_cluster_size=min_cluster_size,
                metric="euclidean",
                cluster_selection_method="eom",
                prediction_data=True,
            )
            vectorizer_model = CountVectorizer(stop_words="english", min_df=1)

            topic_model = BERTopic(
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                vectorizer_model=vectorizer_model,
                calculate_probabilities=False,
                verbose=False,
            )

            topics, _ = topic_model.fit_transform(texts, embeddings=embeddings)

            # Extract topic representation
            topic_info_df = topic_model.get_topic_info()
            topic_dict: Dict[int, Dict[str, Any]] = {}

            formatted_topic_info: List[Dict[str, Any]] = []
            outlier_count = 0

            for _, row in topic_info_df.iterrows():
                t_id = int(row["Topic"])
                count = int(row["Count"])
                pct = round((count / n_samples) * 100.0, 2)

                if t_id == -1:
                    outlier_count = count
                    t_label = "General Feedback / Other"
                    keywords = []
                else:
                    words = topic_model.get_topic(t_id)
                    keywords = (
                        [{"word": w[0], "score": round(float(w[1]), 4)} for w in words[:7]]
                        if words
                        else []
                    )
                    top_words = [kw["word"] for kw in keywords[:3]]
                    t_label = f"Topic {t_id}: {', '.join(top_words)}" if top_words else f"Topic {t_id}"

                t_entry = {
                    "topic_id": t_id,
                    "name": t_label,
                    "count": count,
                    "percentage": pct,
                    "keywords": keywords,
                }
                topic_dict[t_id] = t_entry
                formatted_topic_info.append(t_entry)

            row_topics = []
            for t_id in topics:
                t_id_int = int(t_id)
                t_label = topic_dict.get(t_id_int, {}).get("name", f"Topic {t_id_int}")
                row_topics.append(TopicItem(topic_id=t_id_int, topic_label=t_label))

            total_discovered = len([t for t in topic_dict.keys() if t != -1])
            outlier_pct = round((outlier_count / n_samples) * 100.0, 2)

            return TopicDiscoveryResult(
                row_topics=row_topics,
                topic_info=formatted_topic_info,
                total_topics=total_discovered,
                outlier_count=outlier_count,
                outlier_percentage=outlier_pct,
            )

        except Exception as e:
            logger.warning(f"BERTopic execution encountered an exception, using fallback: {e}")
            default_label = "General Feedback"
            row_topics = [TopicItem(topic_id=0, topic_label=default_label) for _ in range(n_samples)]
            topic_info = [
                {
                    "topic_id": 0,
                    "name": default_label,
                    "count": n_samples,
                    "percentage": 100.0,
                    "keywords": [],
                }
            ]
            return TopicDiscoveryResult(
                row_topics=row_topics,
                topic_info=topic_info,
                total_topics=1,
                outlier_count=0,
                outlier_percentage=0.0,
            )
