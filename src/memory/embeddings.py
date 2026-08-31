"""
Embeddings Adapter for Quilltale TRPG Engine.
Provides local BAAI/bge-m3 embedding support via FastEmbed / SentenceTransformers,
with Jina Embeddings API compatibility and automated fallback handling.
"""
import os
import hashlib
import logging
import math
from typing import List, Optional
import requests
from .base import BaseEmbedder
from src.core.config import EMBEDDING_MODEL_NAME, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)


def generate_deterministic_vector(text: str, dimension: int = 1024) -> List[float]:
    """
    Deterministic pseudo-embedding for testing or offline fallback mode.
    Produces normalized unit vectors of length `dimension`.
    """
    vec = [0.0] * dimension
    if not text:
        return vec

    seed_bytes = hashlib.sha256(text.encode("utf-8")).digest()
    for i in range(dimension):
        byte_idx = i % len(seed_bytes)
        val = (seed_bytes[byte_idx] - 128) / 128.0
        vec[i] = val

    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    return vec


class BGEM3Embedder(BaseEmbedder):
    """
    High-performance BAAI/bge-m3 local embedding adapter.
    Uses FastEmbed / SentenceTransformers with automatic fallback handling.
    """

    def __init__(
        self,
        model_name: str = EMBEDDING_MODEL_NAME,
        dimension: int = EMBEDDING_DIMENSION,
    ):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None
        self._backend = None  # 'fastembed' | 'sentence_transformers' | 'fallback'
        self._init_model()

    def _init_model(self) -> None:
        """Initialize the local embedding model engine."""
        # 1. Try FastEmbed first (fast ONNX runtime)
        try:
            from fastembed import TextEmbedding
            self._model = TextEmbedding(model_name=self.model_name)
            self._backend = "fastembed"
            logger.info(f"Loaded {self.model_name} via FastEmbed engine.")
            return
        except Exception as e:
            logger.debug(f"FastEmbed engine init skipped/failed: {e}")

        # 2. Try SentenceTransformers
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
            self._backend = "sentence_transformers"
            logger.info(f"Loaded {self.model_name} via SentenceTransformers engine.")
            return
        except Exception as e:
            logger.debug(f"SentenceTransformers engine init skipped/failed: {e}")

        # 3. Graceful fallback
        self._backend = "fallback"
        logger.warning(
            f"Local BGE-M3 model engine not available on this system. "
            f"Using deterministic fallback vectors (dim={self.dimension})."
        )

    def embed_query(self, text: str) -> List[float]:
        """Convert a search query into an embedding vector."""
        if not text or not text.strip():
            return [0.0] * self.dimension

        if self._backend == "fastembed" and self._model is not None:
            try:
                embeddings = list(self._model.embed([text]))
                if embeddings:
                    return embeddings[0].tolist() if hasattr(embeddings[0], "tolist") else list(embeddings[0])
            except Exception as e:
                logger.warning(f"FastEmbed query inference failed: {e}")

        elif self._backend == "sentence_transformers" and self._model is not None:
            try:
                emb = self._model.encode(text, convert_to_numpy=True)
                return emb.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformers query inference failed: {e}")

        return generate_deterministic_vector(text, self.dimension)

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple text passages into embedding vectors."""
        if not texts:
            return []

        if self._backend == "fastembed" and self._model is not None:
            try:
                embeddings = list(self._model.embed(texts))
                return [e.tolist() if hasattr(e, "tolist") else list(e) for e in embeddings]
            except Exception as e:
                logger.warning(f"FastEmbed passage inference failed: {e}")

        elif self._backend == "sentence_transformers" and self._model is not None:
            try:
                embs = self._model.encode(texts, convert_to_numpy=True)
                return embs.tolist()
            except Exception as e:
                logger.warning(f"SentenceTransformers passage inference failed: {e}")

        return [generate_deterministic_vector(t, self.dimension) for t in texts]


class JinaEmbedder(BaseEmbedder):
    """
    Jina Embeddings client adapter (REST API).
    Kept for backward compatibility.
    """

    def __init__(
        self,
        model: str = "jina-embeddings-v3",
        api_key: Optional[str] = None,
        dimension: int = 1024,
    ):
        self.model = model
        self.api_key = api_key if api_key is not None else os.getenv("JINA_API_KEY", "")
        self.dimension = dimension
        self.url = "https://api.jina.ai/v1/embeddings"

    def embed_query(self, text: str) -> List[float]:
        return self._call_api([text], task="retrieval.query")[0]

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        return self._call_api(texts, task="retrieval.passage")

    def _call_api(self, texts: List[str], task: str) -> List[List[float]]:
        if not self.api_key:
            return [generate_deterministic_vector(t, self.dimension) for t in texts]

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        data = {
            "model": self.model,
            "task": task,
            "dimensions": self.dimension,
            "late_chunking": False,
            "input": texts,
        }

        try:
            res = requests.post(self.url, headers=headers, json=data, timeout=12)
            res.raise_for_status()
            result_json = res.json()
            return [item["embedding"] for item in result_json["data"]]
        except Exception as e:
            logger.warning(f"Jina API call failed ({e}). Falling back to deterministic vectors.")
            return [generate_deterministic_vector(t, self.dimension) for t in texts]


def get_default_embedder() -> BaseEmbedder:
    """Return the default configured embedding model instance."""
    return BGEM3Embedder(model_name=EMBEDDING_MODEL_NAME, dimension=EMBEDDING_DIMENSION)
