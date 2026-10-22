import logging
import threading
from typing import Any, Dict, List, Optional
import shap
import torch
import numpy as np
from transformers import pipeline

from backend.app.services.ai.model_registry import ModelRegistry

logger = logging.getLogger(__name__)

# CFAP Deterministic 3-Class Sentiment Mapping for 5-star BERT
# (nlptown/bert-base-multilingual-uncased-sentiment)
RAW_STAR_TO_SENTIMENT = {
    "1 star": "Negative",
    "2 stars": "Negative",
    "3 stars": "Neutral",
    "4 stars": "Positive",
    "5 stars": "Positive",
}

STAR_MAPPING_RULES = {
    "1 star": "1★ → Negative",
    "2 stars": "2★ → Negative",
    "3 stars": "3★ → Neutral",
    "4 stars": "4★ → Positive",
    "5 stars": "5★ → Positive",
}


class ExplainabilityService:
    """
    On-demand SHAP Explainer service for the sentiment classifier.

    Provides token-level feature attribution mathematically grounded in the
    real 5-star BERT sequence classification output, mapped deterministically
    to CFAP 3-class sentiment (Positive / Neutral / Negative).
    """
    _instance: Optional["ExplainabilityService"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.registry = ModelRegistry.get_instance()
        self.tokenizer, self.model, self.model_name = (
            self.registry.get_sentiment_pipeline_components()
        )
        device_idx = 0 if self.registry.device.type == "cuda" else -1
        self.pipe = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            top_k=None,
            device=device_idx,
        )
        self.explainer = shap.Explainer(self.pipe)
        self.explainer_name = "PartitionExplainer"
        logger.info(
            f"Initialized ExplainabilityService with model {self.model_name} on device {self.registry.device}"
        )

    @classmethod
    def get_instance(cls) -> "ExplainabilityService":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def explain_text(self, text: str) -> Dict[str, Any]:
        """
        Computes SHAP token feature attribution for a customer feedback text.

        Returns:
            Dict containing:
                - predicted_label: Derived 3-class sentiment (Positive/Neutral/Negative)
                - raw_predicted_label: Real 5-star prediction from BERT model
                - confidence: Model probability score for the winning class
                - base_value: Expected baseline value for the winning class
                - token_contributions: List of token-level SHAP values and directions
                - positive_tokens: Top tokens driving prediction towards target class
                - negative_tokens: Top tokens providing counter-evidence
                - model_name: Real HuggingFace model identifier
                - explainer_name: Explainer algorithm name
                - sentiment_mapping: Transparent mapping metadata
        """
        if not text or not text.strip():
            return {
                "predicted_label": "Neutral",
                "raw_predicted_label": "3 stars",
                "confidence": 0.0,
                "base_value": 0.0,
                "token_contributions": [],
                "positive_tokens": [],
                "negative_tokens": [],
                "model_name": self.model_name,
                "explainer_name": self.explainer_name,
                "sentiment_mapping": {
                    "raw_star_output": "3 stars",
                    "cfap_mapped_sentiment": "Neutral",
                    "mapping_rule": "3★ → Neutral",
                    "explanation_basis": "Empty feedback text provided",
                },
            }

        # 1. Model inference to determine winning raw star class and confidence
        preds = self.pipe(text)[0]
        best_pred = max(preds, key=lambda x: x["score"])
        raw_label = best_pred["label"]  # e.g., "5 stars"
        confidence = float(best_pred["score"])
        mapped_label = RAW_STAR_TO_SENTIMENT.get(raw_label, "Neutral")

        # 2. Run SHAP explainer
        shap_values = self.explainer([text])
        labels = [p["label"] for p in preds]
        star_idx = labels.index(raw_label)

        tokens = shap_values.data[0]
        token_shaps = np.asarray(shap_values.values[0])[:, star_idx]

        base_val_raw = shap_values.base_values[0]
        if hasattr(base_val_raw, "__len__"):
            base_value = float(base_val_raw[star_idx])
        else:
            base_value = float(base_val_raw)

        # 3. Format token contributions
        token_contributions: List[Dict[str, Any]] = []
        for pos, (tok, val) in enumerate(zip(tokens, token_shaps)):
            if not tok:
                continue
            val_f = float(val)
            token_contributions.append({
                "token": tok,
                "shap_value": round(val_f, 4),
                "position": pos,
                "importance": round(abs(val_f), 4),
                "direction": "positive" if val_f > 0 else "negative" if val_f < 0 else "neutral",
            })

        pos_tokens = sorted(
            [t for t in token_contributions if t["shap_value"] > 0],
            key=lambda x: x["shap_value"],
            reverse=True,
        )[:5]

        neg_tokens = sorted(
            [t for t in token_contributions if t["shap_value"] < 0],
            key=lambda x: x["shap_value"],
        )[:5]

        return {
            "predicted_label": mapped_label,
            "raw_predicted_label": raw_label,
            "confidence": round(confidence, 4),
            "base_value": round(base_value, 4),
            "token_contributions": token_contributions,
            "positive_tokens": pos_tokens,
            "negative_tokens": neg_tokens,
            "model_name": self.model_name,
            "explainer_name": self.explainer_name,
            "sentiment_mapping": {
                "raw_star_output": raw_label,
                "cfap_mapped_sentiment": mapped_label,
                "mapping_rule": STAR_MAPPING_RULES.get(raw_label, "Unknown"),
                "explanation_basis": (
                    f"SHAP attribution mathematically computed for raw model output '{raw_label}', "
                    f"mapped deterministically to CFAP '{mapped_label}' sentiment."
                ),
            },
        }
