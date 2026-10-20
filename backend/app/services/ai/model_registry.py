import logging
import threading
from typing import Optional, Tuple, Any
import bertopic
import torch
from sentence_transformers import SentenceTransformer
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizerBase,
)

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


def get_torch_device() -> torch.device:
    """
    Determines optimal torch device based on config and hardware availability.
    """
    configured = (settings.ai_device or "auto").lower().strip()
    if configured == "cuda" and torch.cuda.is_available():
        return torch.device("cuda")
    elif configured == "mps" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    elif configured == "cpu":
        return torch.device("cpu")
    elif configured == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")
    return torch.device("cpu")


class ModelRegistry:
    """
    Thread-safe Singleton model registry and cache for CFAP AI models.
    Loads models on-demand and caches them in worker process memory.
    """
    _instance: Optional["ModelRegistry"] = None
    _lock = threading.Lock()

    def __init__(self):
        self.device = get_torch_device()
        logger.info(f"Initialized ModelRegistry on device: {self.device}")

        # Sentiment model & tokenizer
        self._sentiment_tokenizer: Optional[PreTrainedTokenizerBase] = None
        self._sentiment_model: Optional[PreTrainedModel] = None
        self._sentiment_model_name: str = settings.sentiment_model

        # Emotion model & tokenizer
        self._emotion_tokenizer: Optional[PreTrainedTokenizerBase] = None
        self._emotion_model: Optional[PreTrainedModel] = None
        self._emotion_model_name: str = settings.emotion_model

        # Embedding model
        self._embedding_model: Optional[SentenceTransformer] = None
        self._embedding_model_name: str = settings.embedding_model

    @classmethod
    def get_instance(cls) -> "ModelRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_sentiment_pipeline_components(
        self,
    ) -> Tuple[PreTrainedTokenizerBase, PreTrainedModel, str]:
        if self._sentiment_model is None or self._sentiment_tokenizer is None:
            with self._lock:
                if self._sentiment_model is None or self._sentiment_tokenizer is None:
                    logger.info(
                        f"Loading sentiment model: {self._sentiment_model_name} onto {self.device}"
                    )
                    tokenizer = AutoTokenizer.from_pretrained(
                        self._sentiment_model_name
                    )
                    model = AutoModelForSequenceClassification.from_pretrained(
                        self._sentiment_model_name
                    )
                    model.to(self.device)
                    model.eval()
                    self._sentiment_tokenizer = tokenizer
                    self._sentiment_model = model
        return self._sentiment_tokenizer, self._sentiment_model, self._sentiment_model_name

    def get_emotion_pipeline_components(
        self,
    ) -> Tuple[PreTrainedTokenizerBase, PreTrainedModel, str]:
        if self._emotion_model is None or self._emotion_tokenizer is None:
            with self._lock:
                if self._emotion_model is None or self._emotion_tokenizer is None:
                    logger.info(
                        f"Loading emotion model: {self._emotion_model_name} onto {self.device}"
                    )
                    tokenizer = AutoTokenizer.from_pretrained(
                        self._emotion_model_name
                    )
                    model = AutoModelForSequenceClassification.from_pretrained(
                        self._emotion_model_name
                    )
                    model.to(self.device)
                    model.eval()
                    self._emotion_tokenizer = tokenizer
                    self._emotion_model = model
        return self._emotion_tokenizer, self._emotion_model, self._emotion_model_name

    def get_embedding_model(self) -> Tuple[SentenceTransformer, str]:
        if self._embedding_model is None:
            with self._lock:
                if self._embedding_model is None:
                    logger.info(
                        f"Loading sentence embedding model: {self._embedding_model_name} onto {self.device}"
                    )
                    model = SentenceTransformer(
                        self._embedding_model_name,
                        device=str(self.device),
                    )
                    self._embedding_model = model
        return self._embedding_model, self._embedding_model_name

    @staticmethod
    def get_bertopic_version() -> str:
        return getattr(bertopic, "__version__", "0.16.0")
