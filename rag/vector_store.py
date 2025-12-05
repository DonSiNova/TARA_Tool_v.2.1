# rag/vector_store.py
"""
FAISS-based vector store for AutoTARA-RAG (local-only).

Responsibilities:
- Maintain a FAISS index on disk (L2 similarity).
- Maintain a metadata store (JSON) for each document.
- Provide a similarity_search interface with optional metadata filters.
- Use OpenAI embeddings (text-embedding-3-small) for encoding.

NOTE:
- This implementation is intentionally simple and local-only.
- It persists:
    - <index_path>.faiss  : FAISS index
    - <index_path>.meta.json : list of Document metadata dicts
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

import faiss
import numpy as np
from openai import OpenAI

from config.settings import settings

# Constants for embeddings
EMBED_MODEL = "text-embedding-3-small"


@dataclass
class Document:
    """
    Represents a single document entry in the vector store.

    Fields:
    - id:     logical identifier (e.g., CVE ID, CWE ID, filename).
    - source: logical source (NVD, CWE, CAPEC, ATTCK, ATM, STANDARD).
    - type:   document type (CVE, CWE, CAPEC, TECHNIQUE, AUTOMOTIVE_THREAT, TEXT).
    - title:  short title.
    - body:   main textual body for embedding.
    - metadata: free-form dictionary with additional attributes.
    """

    id: str
    source: str
    type: str
    title: str
    body: str
    metadata: Dict[str, Any]


class VectorStore:
    """
    Simple FAISS-based vector store, backed by:
    - FAISS index (.faiss file)
    - JSON metadata (.meta.json file)

    It uses OpenAI embeddings to represent texts as vectors.

    Usage:
        vs = VectorStore("data/vector_store.index")
        vs.add_documents([...])
        docs = vs.similarity_search("ABS ECU vulnerabilities", k=5, filters={"source": "NVD"})
    """

    def __init__(self, index_path: str):
        self.index_path = index_path
        self.faiss_path = index_path + ".faiss"
        self.meta_path = index_path + ".meta.json"

        self.client = OpenAI()

        self.dim: Optional[int] = None
        self.index: Optional[faiss.IndexFlatL2] = None
        self.docs: List[Document] = []

        self._load()

    # ------------------------------------------------------------------
    # Initialization & persistence
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """
        Load FAISS index and metadata if they exist.
        """
        if os.path.exists(self.faiss_path) and os.path.exists(self.meta_path):
            # Load metadata first
            with open(self.meta_path, "r", encoding="utf-8") as f:
                meta_list = json.load(f)
            self.docs = [
                Document(
                    id=m["id"],
                    source=m["source"],
                    type=m["type"],
                    title=m["title"],
                    body=m["body"],
                    metadata=m.get("metadata", {}),
                )
                for m in meta_list
            ]

            # Load FAISS index
            self.index = faiss.read_index(self.faiss_path)
            self.dim = self.index.d

    def _save(self) -> None:
        """
        Persist FAISS index and metadata to disk.
        """
        if self.index is not None:
            os.makedirs(os.path.dirname(self.faiss_path), exist_ok=True)
            faiss.write_index(self.index, self.faiss_path)

        meta_list = [asdict(d) for d in self.docs]
        os.makedirs(os.path.dirname(self.meta_path), exist_ok=True)
        with open(self.meta_path, "w", encoding="utf-8") as f:
            json.dump(meta_list, f, indent=2, ensure_ascii=False)

    # ------------------------------------------------------------------
    # Embedding helpers
    # ------------------------------------------------------------------

    def _embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        Embed a list of texts using OpenAI embeddings.

        Returns:
            np.ndarray of shape (len(texts), dim) with dtype float32.
        """
        if not texts:
            return np.zeros((0, self.dim or 1536), dtype="float32")

        # OpenAI v1-style client
        response = self.client.embeddings.create(model=EMBED_MODEL, input=texts)
        vectors = [item.embedding for item in response.data]
        arr = np.array(vectors, dtype="float32")
        return arr

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_documents(self, docs: List[Document]) -> None:
        """
        Add a batch of documents to the vector store.
        """
        if not docs:
            return

        # Filter out docs that already exist by id
        existing_ids = {d.id for d in self.docs}
        new_docs = [d for d in docs if d.id not in existing_ids]

        if not new_docs:
            return

        texts = [f"{d.title}\n\n{d.body}" for d in new_docs]
        vectors = self._embed_texts(texts)

        if self.index is None:
            # Initialize index
            self.dim = vectors.shape[1]
            self.index = faiss.IndexFlatL2(self.dim)

        if self.dim != vectors.shape[1]:
            raise ValueError(
                f"Vector dimension {vectors.shape[1]} does not match index dim {self.dim}"
            )

        self.index.add(vectors)
        self.docs.extend(new_docs)
        self._save()

    def similarity_search(
        self,
        query: str,
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Perform similarity search with optional metadata filtering.

        Args:
            query:   query text.
            k:       number of desired results (after filtering).
            filters: {key: value} to match in Document.metadata or top-level fields.

        Returns:
            List[Document] of length <= k.
        """
        if self.index is None or not self.docs:
            return []

        filters = filters or {}

        # Embed query
        q_vec = self._embed_texts([query])
        if q_vec.shape[0] == 0:
            return []

        # Search more than k to allow filtering
        search_k = max(k * 5, k)
        search_k = min(search_k, len(self.docs))
        distances, indices = self.index.search(q_vec, search_k)

        results: List[Document] = []
        for idx in indices[0]:
            if idx < 0 or idx >= len(self.docs):
                continue
            doc = self.docs[idx]
            if self._matches_filters(doc, filters):
                results.append(doc)
                if len(results) >= k:
                    break

        return results

    # ------------------------------------------------------------------
    # Helper: metadata filtering
    # ------------------------------------------------------------------

    @staticmethod
    def _matches_filters(doc: Document, filters: Dict[str, Any]) -> bool:
        """
        Check if a document matches the given filters.

        Filters can match:
        - Top-level fields: id, source, type
        - Metadata fields: doc.metadata[key]

        Equality match only.
        """
        if not filters:
            return True

        for key, value in filters.items():
            if key in ("id", "source", "type"):
                if getattr(doc, key) != value:
                    return False
            else:
                if doc.metadata.get(key) != value:
                    return False

        return True
