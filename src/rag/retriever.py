"""
RAG Retriever — Retrieves relevant regulatory context from ChromaDB
for each LLM node in the CreditSense pipeline.
"""

import logging
from typing import Optional

from src.rag.config import RAG_CONFIG
from src.rag.vector_store import get_or_create_collection, collection_is_populated

logger = logging.getLogger(__name__)


class CreditRAGRetriever:
    """
    Retrieves relevant US credit regulatory context from the ChromaDB
    knowledge base. Each method builds tailored queries for different
    pipeline nodes.
    """

    def __init__(self, top_k: Optional[int] = None):
        """
        Initialize the retriever.

        Args:
            top_k: Number of documents to retrieve per query (default from config).
        """
        self.top_k = top_k or RAG_CONFIG["top_k"]
        self._collection = None
        self._available = None

    def _get_collection(self):
        """Lazy-load the ChromaDB collection."""
        if self._collection is None:
            self._collection = get_or_create_collection()
        return self._collection

    def is_available(self) -> bool:
        """
        Check if the RAG system is operational (ChromaDB has documents).

        Returns:
            True if the knowledge base is populated and accessible.
        """
        if self._available is not None:
            return self._available

        try:
            self._available = collection_is_populated()
        except Exception:
            self._available = False

        return self._available

    def retrieve(self, query: str, n_results: Optional[int] = None) -> str:
        """
        Retrieve relevant documents for a query and format them as context.

        Args:
            query: The search query.
            n_results: Override for number of results.

        Returns:
            Formatted context string, or empty string if unavailable.
        """
        if not self.is_available():
            return ""

        n = n_results or self.top_k

        try:
            collection = self._get_collection()
            if collection is None:
                return ""

            results = collection.query(
                query_texts=[query],
                n_results=n,
            )

            if not results or not results.get("documents") or not results["documents"][0]:
                return ""

            # Format retrieved documents into context
            context_parts = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                source = metadata.get("source", "Unknown source")
                category = metadata.get("category", "")

                header = f"[Source: {source}"
                if category:
                    header += f" | Category: {category}"
                header += "]"

                context_parts.append(f"{header}\n{doc}")

            formatted = "\n\n---\n\n".join(context_parts)
            logger.info(f"Retrieved {len(context_parts)} documents for query: {query[:80]}...")
            return formatted

        except Exception as e:
            logger.error(f"RAG retrieval failed: {e}")
            return ""

    def retrieve_for_data_structuring(self, raw_text_snippet: str) -> str:
        """
        Retrieve regulatory context relevant to credit report data extraction.

        Focuses on: FCRA data accuracy requirements, field definitions,
        reporting standards, and bureau-specific formatting.

        Args:
            raw_text_snippet: First ~500 chars of raw text for context.

        Returns:
            Formatted regulatory context string.
        """
        queries = [
            "FCRA requirements for credit report data accuracy and completeness",
            "credit report fields definitions accounts inquiries public records format",
            "consumer credit reporting standards bureau data requirements",
        ]

        all_context = []
        for q in queries:
            ctx = self.retrieve(q, n_results=2)
            if ctx:
                all_context.append(ctx)

        return "\n\n---\n\n".join(all_context) if all_context else ""

    def retrieve_for_summary(self, credit_tier: str) -> str:
        """
        Retrieve regulatory context relevant to credit health summarization.

        Focuses on: credit score interpretation, tier meanings, CFPB guidance
        on communicating credit information to consumers.

        Args:
            credit_tier: The consumer's credit tier (excellent, good, fair, poor).

        Returns:
            Formatted regulatory context string.
        """
        tier_context = {
            "excellent": "excellent credit score benefits advantages top tier lending rates",
            "very_good": "very good credit score characteristics lending eligibility",
            "good": "good credit score meaning average consumer credit profile",
            "fair": "fair credit score risks subprime lending utilization improvement",
            "poor": "poor credit score rebuilding strategies consumer rights protections",
        }

        tier_query = tier_context.get(credit_tier, "credit score interpretation consumer guidance")

        queries = [
            f"CFPB guidance on {tier_query}",
            "credit score factors payment history utilization length of credit mix inquiries",
            "consumer rights under Fair Credit Reporting Act credit report review",
        ]

        all_context = []
        for q in queries:
            ctx = self.retrieve(q, n_results=2)
            if ctx:
                all_context.append(ctx)

        return "\n\n---\n\n".join(all_context) if all_context else ""

    def retrieve_for_recommendation(self, credit_tier: str, key_issues: Optional[list] = None) -> str:
        """
        Retrieve regulatory context for generating credit improvement recommendations.

        Focuses on: legal credit improvement strategies, FDCPA dispute procedures,
        CFPB best practices, and tier-specific guidance.

        Args:
            credit_tier: The consumer's credit tier.
            key_issues: List of key credit issues (e.g., ["high utilization", "late payments"]).

        Returns:
            Formatted regulatory context string.
        """
        queries = [
            "credit improvement strategies best practices CFPB official guidance",
            "consumer rights dispute errors credit report FCRA procedures",
            "credit utilization payment history improvement timeline expectations",
        ]

        # Add issue-specific queries
        if key_issues:
            issue_str = " ".join(key_issues[:3])  # Limit to top 3 issues
            queries.append(
                f"credit improvement for {issue_str} regulatory guidance consumer protection"
            )

        # Add tier-specific query
        if credit_tier in ("fair", "poor"):
            queries.append("rebuilding credit after negative items consumer protections FDCPA")
        elif credit_tier in ("good", "very_good"):
            queries.append("maintaining good credit score optimization strategies")

        all_context = []
        seen = set()  # Avoid duplicate context
        for q in queries:
            ctx = self.retrieve(q, n_results=2)
            if ctx and ctx not in seen:
                all_context.append(ctx)
                seen.add(ctx)

        return "\n\n---\n\n".join(all_context) if all_context else ""
