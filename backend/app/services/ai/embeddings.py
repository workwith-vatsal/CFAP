import logging
from typing import List, Optional, Union
import numpy as np

from backend.app.core.config import settings
from backend.app.services.ai.model_registry import ModelRegistry

logger = logging.getLogger(__name__)


class EmbeddingStorage:
    """
    Abstraction layer for vector embedding serialization and deserialization.

    Current implementation: Stores 384-dimensional float32 arrays as binary buffers (PostgreSQL BYTEA).
    Future extensibility point: Allows dropping in pgvector / remote vector storage without modifying
    the embedding generation, BERTopic, analysis tasks, or result aggregation pipeline.
    """

    @staticmethod
    def serialize(embedding: Union[np.ndarray, List[float]]) -> bytes:
        """
        Serializes a 1D vector (numpy array or float list) into a raw float32 byte buffer.
        """
        if isinstance(embedding, list):
            arr = np.array(embedding, dtype=np.float32)
        elif isinstance(embedding, np.ndarray):
            arr = embedding.astype(np.float32)
        else:
            raise TypeError(f"Unsupported embedding type: {type(embedding)}")
        return arr.tobytes()

    @staticmethod
    def deserialize(data: bytes) -> np.ndarray:
        """
        Deserializes a raw float32 byte buffer back into a 1D numpy array.
        """
        if not data:
            return np.empty((0,), dtype=np.float32)
        return np.frombuffer(data, dtype=np.float32)


class EmbeddingService:
    """
    Sentence Embedding Service using SentenceTransformers (e.g. all-MiniLM-L6-v2).
    Generates 384-dimensional semantic embeddings for feedback texts.
    """

    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or ModelRegistry.get_instance()

    def generate_embeddings(
        self,
        texts: List[str],
        batch_size: Optional[int] = None,
    ) -> np.ndarray:
        """
        Encodes a list of clean feedback texts into a 2D numpy array of shape (N, 384).
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        model, _ = self.registry.get_embedding_model()
        effective_batch_size = batch_size or settings.ai_batch_size

        embeddings = model.encode(
            texts,
            batch_size=effective_batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

        return embeddings.astype(np.float32)
