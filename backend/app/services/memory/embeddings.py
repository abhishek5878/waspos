from typing import Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Generate vector embeddings for text content."""

    _instance: Optional["EmbeddingService"] = None
    _model: Optional[SentenceTransformer] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        self.logger = logger.bind(service="embeddings")
        if self._model is None:
            self._load_model()

    def _load_model(self):
        """Load the embedding model."""
        self.logger.info("loading_embedding_model", model=settings.EMBEDDING_MODEL)
        self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.logger.info("embedding_model_loaded")

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text."""
        if not text:
            return [0.0] * settings.EMBEDDING_DIMENSION

        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []

        # Filter empty texts
        valid_texts = [(i, t) for i, t in enumerate(texts) if t]
        if not valid_texts:
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]

        indices, valid_text_list = zip(*valid_texts)
        embeddings = self._model.encode(list(valid_text_list), convert_to_numpy=True)

        # Rebuild result with zeros for empty texts
        result = [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
        for i, embedding in zip(indices, embeddings):
            result[i] = embedding.tolist()

        return result

    def compute_similarity(
        self,
        embedding1: list[float],
        embedding2: list[float],
    ) -> float:
        """Compute cosine similarity between two embeddings."""
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))
