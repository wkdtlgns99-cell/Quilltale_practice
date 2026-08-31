"""
Abstract base classes for Memory & Vector Store components.
Enables pluggable backend replacements (e.g. Qdrant -> LanceDB / ChromaDB) with minimal code changes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    id: str
    text: str
    score: float
    payload: Dict[str, Any] = field(default_factory=dict)


class BaseEmbedder(ABC):
    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Convert a search query into an embedding vector."""
        pass

    @abstractmethod
    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        """Convert multiple text passages/events into embedding vectors."""
        pass


class BaseVectorStore(ABC):
    @abstractmethod
    def ensure_collection(self, collection_name: str, vector_size: int = 1024) -> None:
        """Create collection if it does not already exist."""
        pass

    @abstractmethod
    def upsert(
        self,
        collection_name: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> bool:
        """Insert or update a vector point with metadata payload."""
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """Search similar vectors with optional metadata payload filters."""
        pass
