"""
Local FAISS vector store management

Provides the file-based FAISS vector database that stores tweet/link embeddings.
This replaces the prior PostgreSQL persistence layer for semantic vectors.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import faiss  # type: ignore
import numpy as np

from src.config.settings import settings
from src.utils.logger import logger


class LocalVectorStore:
    """Thin wrapper around a FAISS index plus on-disk metadata."""

    def __init__(self, store_dir: Path, dimension: int, id_field: str):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.dimension = dimension
        self.id_field = id_field
        self.index_path = self.store_dir / "index.faiss"
        self.metadata_path = self.store_dir / "metadata.json"
        self._lock = threading.Lock()
        self.index = self._load_index()
        self.metadata: List[Dict] = self._load_metadata()
        self.id_lookup = {
            str(item.get(self.id_field)): idx for idx, item in enumerate(self.metadata) if item.get(self.id_field)
        }
        logger.info(
            f"Loaded vector store at {self.store_dir} "
            f"(items={len(self.metadata)}, dimension={self.dimension})"
        )

    def _load_index(self) -> faiss.Index:
        if self.index_path.exists():
            try:
                return faiss.read_index(str(self.index_path))
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Failed to load FAISS index from {self.index_path}: {exc}")
        # Default to cosine similarity via normalized inner product
        return faiss.IndexFlatIP(self.dimension)

    def _load_metadata(self) -> List[Dict]:
        if self.metadata_path.exists():
            try:
                return json.loads(self.metadata_path.read_text())
            except Exception as exc:  # pragma: no cover - defensive
                logger.error(f"Failed to load metadata store {self.metadata_path}: {exc}")
        return []

    def _persist(self) -> None:
        faiss.write_index(self.index, str(self.index_path))
        self.metadata_path.write_text(json.dumps(self.metadata, ensure_ascii=False))

    def add_items(self, embeddings: Iterable[np.ndarray], metadatas: Iterable[Dict]) -> int:
        """Add new vectors + metadata to the store if they are not already present."""
        to_add_vectors: List[np.ndarray] = []
        to_add_metadata: List[Dict] = []

        for embedding, metadata in zip(embeddings, metadatas):
            if embedding is None or metadata is None:
                continue
            unique_id = metadata.get(self.id_field)
            if unique_id is None:
                logger.warning("Metadata missing %s, skipping vector", self.id_field)
                continue
            unique_id = str(unique_id)
            if unique_id in self.id_lookup:
                continue
            to_add_vectors.append(np.asarray(embedding, dtype="float32"))
            to_add_metadata.append(self._sanitize_metadata(metadata))

        if not to_add_vectors:
            return 0

        vectors = np.vstack(to_add_vectors).astype("float32")
        faiss.normalize_L2(vectors)

        with self._lock:
            self.index.add(vectors)
            base_idx = len(self.metadata)
            for offset, metadata in enumerate(to_add_metadata):
                self.metadata.append(metadata)
                unique_id = str(metadata[self.id_field])
                self.id_lookup[unique_id] = base_idx + offset
            self._persist()

        logger.info(f"Added {len(to_add_vectors)} items to vector store {self.store_dir}")
        return len(to_add_vectors)

    def search(self, embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Return metadata + similarity scores for the nearest neighbors."""
        if self.index.ntotal == 0:
            return []

        query_vector = np.asarray(embedding, dtype="float32").reshape(1, -1)
        faiss.normalize_L2(query_vector)

        with self._lock:
            top_k = min(top_k, self.index.ntotal)
            distances, indices = self.index.search(query_vector, top_k)

        results: List[Dict] = []
        for idx, score in zip(indices[0], distances[0]):
            if idx < 0 or idx >= len(self.metadata):
                continue
            item = dict(self.metadata[idx])
            item["similarity"] = float(score)
            results.append(item)

        return results

    @staticmethod
    def _sanitize_metadata(metadata: Dict) -> Dict:
        sanitized = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)) or value is None:
                sanitized[key] = value
            elif isinstance(value, list):
                sanitized[key] = value
            elif isinstance(value, dict):
                sanitized[key] = value
            else:
                sanitized[key] = str(value)
        return sanitized


class VectorStoreManager:
    """Convenience facade for tweet/link vector stores."""

    def __init__(self):
        base_dir = Path(settings.VECTOR_STORE_PATH)
        base_dir.mkdir(parents=True, exist_ok=True)
        dimension = settings.EMBEDDING_DIMENSION
        self.tweet_store = LocalVectorStore(base_dir / "tweets", dimension, "tweet_id")
        self.link_store = LocalVectorStore(base_dir / "links", dimension, "link_id")

    def add_tweet_embeddings(self, embeddings: Iterable[np.ndarray], metadatas: Iterable[Dict]) -> int:
        return self.tweet_store.add_items(embeddings, metadatas)

    def add_link_embeddings(self, embeddings: Iterable[np.ndarray], metadatas: Iterable[Dict]) -> int:
        return self.link_store.add_items(embeddings, metadatas)

    def search_tweets(self, embedding: np.ndarray, top_k: int) -> List[Dict]:
        return self.tweet_store.search(embedding, top_k)

    def search_links(self, embedding: np.ndarray, top_k: int) -> List[Dict]:
        return self.link_store.search(embedding, top_k)


# Global manager instance
vector_store_manager = VectorStoreManager()
