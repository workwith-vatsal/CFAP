import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
import torch
import torch.nn.functional as F

from backend.app.core.config import settings
from backend.app.services.ai.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


@dataclass
class EmotionResult:
    emotion_label: str             # Dominant emotion (e.g., "joy", "anger", "neutral")
    emotion_score: float           # Probability of dominant emotion (0.0 - 1.0)
    emotion_scores: Dict[str, float]  # Full probability distribution for all 7 emotions


class EmotionService:
    """
    Batched Emotion Classification Service using DistilRoBERTa.
    Supported emotions: anger, disgust, fear, joy, neutral, sadness, surprise.

    LIMITATION NOTICE:
    The underlying model (j-hartmann/emotion-english-distilroberta-base) is English-oriented.
    Non-English text may pass through the pipeline but is not validated multilingual emotion classification.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry.get_instance()

    def analyze_batch(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> List[EmotionResult]:
        """
        Runs batched emotion classification on cleaned feedback texts.
        Returns an EmotionResult with dominant emotion and full probability distribution.
        """
        if not texts:
            return []

        tokenizer, model, _ = self.registry.get_emotion_pipeline_components()
        device = self.registry.device
        effective_batch_size = batch_size or settings.ai_batch_size

        results: List[EmotionResult] = []

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

            batch_probs = probabilities.cpu().tolist()

            for row_probs in batch_probs:
                # Map probabilities to class names
                scores_dict: Dict[str, float] = {}
                max_score = -1.0
                dominant_label = "neutral"

                for class_idx, score in enumerate(row_probs):
                    label = model.config.id2label.get(class_idx, str(class_idx)).lower()
                    rounded_score = round(float(score), 4)
                    scores_dict[label] = rounded_score
                    if rounded_score > max_score:
                        max_score = rounded_score
                        dominant_label = label

                results.append(
                    EmotionResult(
                        emotion_label=dominant_label,
                        emotion_score=max_score,
                        emotion_scores=scores_dict,
                    )
                )

        return results
