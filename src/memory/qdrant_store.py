"""
Qdrant Vector Store Adapter for Quilltale TRPG Engine.
Supports local persistent disk storage, Docker server mode, and in-memory test mode.
"""
import logging
from typing import Any, Dict, List, Optional
try:
    from qdrant_client.qdrant_client import QdrantClient
except ImportError:
    from qdrant_client import QdrantClient
from qdrant_client.http import models
from .base import BaseVectorStore, SearchResult

logger = logging.getLogger(__name__)


class QdrantVectorStore(BaseVectorStore):
    """
    Qdrant database wrapper providing collection auto-creation,
    point upsertion, and payload metadata filtering.
    """

    _client_cache: Dict[str, Any] = {}

    def __init__(
        self,
        url: Optional[str] = None,
        path: Optional[str] = None,
        in_memory: bool = False,
    ):
        if in_memory:
            self.client = QdrantClient(":memory:", prefer_grpc=False)
        elif url:
            if url not in self._client_cache:
                self._client_cache[url] = QdrantClient(url=url, prefer_grpc=False)
            self.client = self._client_cache[url]
        elif path:
            from pathlib import Path
            norm_path = str(Path(path).resolve())
            if norm_path not in self._client_cache:
                try:
                    self._client_cache[norm_path] = QdrantClient(path=norm_path, prefer_grpc=False)
                except Exception as e:
                    logger.warning(
                        f"Failed to lock Qdrant storage at '{norm_path}' ({e}). "
                        "Falling back to thread-safe in-memory vector store."
                    )
                    self._client_cache[norm_path] = QdrantClient(":memory:", prefer_grpc=False)
            self.client = self._client_cache[norm_path]
        else:
            self.client = QdrantClient(":memory:", prefer_grpc=False)


    def ensure_collection(self, collection_name: str, vector_size: int = 1024) -> None:
        try:
            collections = [c.name for c in self.client.get_collections().collections]
            if collection_name not in collections:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_size,
                        distance=models.Distance.COSINE,
                    ),
                )
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection '{collection_name}': {e}")

    def upsert(
        self,
        collection_name: str,
        id: str,
        vector: List[float],
        payload: Dict[str, Any],
    ) -> bool:
        self.ensure_collection(collection_name, len(vector))
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
            return True
        except Exception as e:
            logger.error(f"Qdrant upsert error: {e}")
            return False

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        self.ensure_collection(collection_name, len(query_vector))

        qdrant_filter = None
        if filters:
            must_conditions = []
            for key, val in filters.items():
                if val is None:
                    continue
                if isinstance(val, list):
                    must_conditions.append(
                        models.FieldCondition(key=key, match=models.MatchAny(any=val))
                    )
                else:
                    must_conditions.append(
                        models.FieldCondition(key=key, match=models.MatchValue(value=val))
                    )
            if must_conditions:
                qdrant_filter = models.Filter(must=must_conditions)

        try:
            if hasattr(self.client, "query_points"):
                res = self.client.query_points(
                    collection_name=collection_name,
                    query=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                )
                hits = res.points
            else:
                hits = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    query_filter=qdrant_filter,
                    limit=limit,
                )

            return [
                SearchResult(
                    id=str(hit.id),
                    text=hit.payload.get("text", "") if hit.payload else "",
                    score=hit.score,
                    payload=hit.payload or {},
                )
                for hit in hits
            ]
        except Exception as e:
            logger.error(f"Qdrant search error: {e}")
            return []
