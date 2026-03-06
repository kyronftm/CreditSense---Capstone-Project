"""
CreditSense RAG Module — Retrieval-Augmented Generation for credit regulations.

Provides regulatory context from official US credit laws and guidelines
(FCRA, CFPB, FTC, etc.) to enhance LLM-based credit report analysis.
"""

from src.rag.retriever import CreditRAGRetriever
from src.rag.vector_store import get_or_create_collection, collection_is_populated
from src.rag.config import RAG_CONFIG

__all__ = [
    "CreditRAGRetriever",
    "get_or_create_collection",
    "collection_is_populated",
    "RAG_CONFIG",
]
