import logging
from dataclasses import dataclass
from typing import List, Optional
import torch
import torch.nn.functional as F

from backend.app.core.config import settings
from backend.app.services.ai.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class SentimentResult:
    sentiment_label: str       # "positive" | "neutral" | "negative"
    raw_sentiment_label: str   # e.g., "1 star", "2 stars", "3 stars", "4 stars", "5 stars"
    sentiment_score: float     # Confidence score (0.0 - 1.0)


# Deterministic Star to 3-class Sentiment Mapping
# nlptown/bert-base-multilingual-uncased-sentiment produces 5 rating classes: 1 to 5 stars.
# 1 star / 2 stars -> Negative
# 3 stars          -> Neutral
# 4 stars / 5 stars -> Positive
STAR_TO_SENTIMENT_MAP = {
    "1 star": "negative",
    "2 stars": "negative",
    "3 stars": "neutral",
    "4 stars": "positive",
    "5 stars": "positive",
    "1": "negative",
    "2": "negative",
    "3": "neutral",
    "4": "positive",
    "5": "positive",
}


def map_star_to_sentiment(raw_label: str) -> str:
    """
    Maps raw star rating prediction (1-5 stars) to standard 3-class sentiment:
    1-2 stars -> negative
    3 stars   -> neutral
    4-5 stars -> positive
    """
    normalized = raw_label.strip().lower()
    return STAR_TO_SENTIMENT_MAP.get(normalized, "neutral")


class SentimentService:
    """
    Batched Sentiment Analysis Service using BERT.
    Uses ModelRegistry for model reuse across requests.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry.get_instance()

    def analyze_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[SentimentResult]:
        """
        Runs batched inference on cleaned feedback texts.
        Returns a SentimentResult for each input text.
        """
        if not texts:
            return []

        tokenizer, model, _ = self.registry.get_sentiment_pipeline_components()
        device = self.registry.device
        effective_batch_size = batch_size or settings.ai_batch_size

        results: List[SentimentResult] = []

        for i in range(0, len(texts), effective_batch_size):
            batch_texts = texts[i : i + effective_batch_size]

            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=settings.ai_max_text_length,
                return_tensors="pt",
            )
            encoded = {k: v.to(device) for k, v in encoded.items()}

            with torch.no_grad():
                outputs = model(**encoded)
                probabilities = F.softmax(outputs.logits, dim=-1)

            # Map predictions to labels
            max_probs, preds = torch.max(probabilities, dim=-1)

            for raw_idx, prob in zip(preds.cpu().tolist(), max_probs.cpu().tolist()):
                raw_label = model.config.id2label.get(raw_idx, f"{raw_idx + 1} star")
                sentiment_label = map_star_to_sentiment(raw_label)

                results.append(
                    SentimentResult(
                        sentiment_label=sentiment_label,
                        raw_sentiment_label=raw_label,
                        sentiment_score=round(float(prob), 4),
                    )
                )

        return results
