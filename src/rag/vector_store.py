"""
Vector Store — ChromaDB initialization and management for the CreditSense RAG.
"""

import hashlib
import logging
import math
import os
import re
from collections import Counter
from typing import Optional

import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings

from src.rag.config import RAG_CONFIG, CHROMA_PERSIST_DIR

logger = logging.getLogger(__name__)

# Module-level cache for the embedding function and client
_embedding_fn = None
_chroma_client = None


class HashEmbeddingFunction(EmbeddingFunction):
    """
    Lightweight offline embedding function based on word n-gram hashing.

    Produces deterministic 384-dimensional embeddings by hashing token n-grams
    and projecting them into a fixed-size vector. Works entirely offline without
    any model downloads.

    For production use, replace with SentenceTransformerEmbeddingFunction
    once the model is available locally.
    """

    def __init__(self, dim: int = 384):
        self.dim = dim

    def _tokenize(self, text: str) -> list[str]:
        """Simple whitespace + lowercase tokenization."""
        text = text.lower()
        text = re.sub(r'[^a-z0-9\s]', ' ', text)
        return text.split()

    def _embed_one(self, text: str) -> list[float]:
        """Create a single embedding vector from text."""
        tokens = self._tokenize(text)
        vec = [0.0] * self.dim

        # Unigrams and bigrams
        ngrams = tokens[:]
        for i in range(len(tokens) - 1):
            ngrams.append(tokens[i] + " " + tokens[i + 1])

        # Hash each n-gram into the vector
        for ng in ngrams:
            h = int(hashlib.md5(ng.encode()).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        vec = [v / norm for v in vec]
        return vec

    def __call__(self, input: Documents) -> Embeddings:
        return [self._embed_one(text) for text in input]


def _get_embedding_function():
    """
    Get or create the embedding function (cached).

    Tries SentenceTransformer first (best quality). If unavailable (e.g., no
    network), falls back to a lightweight hash-based embedding function that
    works fully offline.
    """
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn

    # Try SentenceTransformer first
    try:
        from chromadb.utils import embedding_functions
        _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=RAG_CONFIG["embedding_model"]
        )
        # Verify it actually works (model is downloaded and functional)
        _embedding_fn(["test"])
        logger.info(f"Using SentenceTransformer embedding model: {RAG_CONFIG['embedding_model']}")
        return _embedding_fn
    except Exception as e:
        logger.warning(f"SentenceTransformer not available ({e}). Using offline hash embeddings.")

    # Fallback: hash-based embeddings (fully offline)
    _embedding_fn = HashEmbeddingFunction()
    logger.info("Using offline HashEmbeddingFunction (384-dim)")
    return _embedding_fn


def _get_chroma_client():
    """Get or create the ChromaDB persistent client (cached)."""
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        logger.info(f"ChromaDB client initialized at {CHROMA_PERSIST_DIR}")
    return _chroma_client


def get_or_create_collection():
    """
    Get or create the ChromaDB collection for regulatory documents.

    Returns:
        chromadb.Collection instance, or None if initialization fails.
    """
    try:
        client = _get_chroma_client()
        ef = _get_embedding_function()
        collection = client.get_or_create_collection(
            name=RAG_CONFIG["collection_name"],
            embedding_function=ef,
            metadata={"description": "US credit regulatory documents for CreditSense RAG"},
        )
        logger.info(
            f"Collection '{RAG_CONFIG['collection_name']}' ready with {collection.count()} documents"
        )
        return collection

    except Exception as e:
        logger.error(f"Failed to initialize ChromaDB collection: {e}")
        return None


def collection_is_populated() -> bool:
    """
    Check if the ChromaDB collection exists and has documents.

    Returns:
        True if the collection has at least 1 document.
    """
    try:
        collection = get_or_create_collection()
        if collection is None:
            return False
        return collection.count() > 0
    except Exception:
        return False


def add_chunks(chunks: list[dict]) -> int:
    """
    Add text chunks to the ChromaDB collection.

    Args:
        chunks: List of dicts with 'text' and 'metadata' keys.

    Returns:
        Number of chunks successfully added.
    """
    collection = get_or_create_collection()
    if collection is None:
        logger.error("Cannot add chunks: collection not available")
        return 0

    if not chunks:
        logger.warning("No chunks to add")
        return 0

    # ChromaDB requires unique IDs
    ids = [f"chunk_{i}_{chunks[i]['metadata'].get('source', 'unknown')}" for i in range(len(chunks))]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    # Add in batches (ChromaDB handles large batches, but let's be safe)
    batch_size = 100
    total_added = 0

    for i in range(0, len(chunks), batch_size):
        batch_ids = ids[i:i + batch_size]
        batch_docs = documents[i:i + batch_size]
        batch_meta = metadatas[i:i + batch_size]

        try:
            collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
            )
            total_added += len(batch_ids)
            logger.info(f"Added batch {i // batch_size + 1}: {len(batch_ids)} chunks")
        except Exception as e:
            logger.error(f"Failed to add batch {i // batch_size + 1}: {e}")

    logger.info(f"Total chunks added to collection: {total_added}")
    return total_added


def clear_collection() -> bool:
    """
    Delete and recreate the collection (for refreshing the knowledge base).

    Returns:
        True if successful.
    """
    try:
        client = _get_chroma_client()
        ef = _get_embedding_function()

        # Delete existing collection
        try:
            client.delete_collection(RAG_CONFIG["collection_name"])
            logger.info(f"Deleted collection '{RAG_CONFIG['collection_name']}'")
        except Exception:
            pass  # Collection might not exist

        # Recreate
        client.get_or_create_collection(
            name=RAG_CONFIG["collection_name"],
            embedding_function=ef,
            metadata={"description": "US credit regulatory documents for CreditSense RAG"},
        )
        logger.info(f"Recreated collection '{RAG_CONFIG['collection_name']}'")
        return True

    except Exception as e:
        logger.error(f"Failed to clear collection: {e}")
        return False
