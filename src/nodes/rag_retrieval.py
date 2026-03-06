"""
RAG Retrieval Node — Retrieves regulatory context from the knowledge base
for all downstream LLM nodes in the CreditSense pipeline.

Responsibilities:
  1. Initialize the RAG retriever.
  2. Retrieve tailored regulatory context for each LLM node:
     - Data Structuring: FCRA data accuracy requirements
     - Summary Generation: Credit score interpretation guidance
     - Recommendation: Credit improvement strategies and regulations
  3. Graceful degradation: if RAG is unavailable, pipeline continues normally.

This node runs after Text Extraction and before Data Structuring.
"""

import logging
from src.state import CreditSenseState
from src.rag.retriever import CreditRAGRetriever

logger = logging.getLogger(__name__)


def rag_retrieval_node(state: CreditSenseState) -> CreditSenseState:
    """
    Retrieves regulatory context from the ChromaDB knowledge base
    and stores it in the pipeline state for downstream LLM nodes.

    Args:
        state: Pipeline state with 'raw_text' from extraction.

    Returns:
        Updated state with 'rag_context_*' fields populated.
    """

    # --- Guard: check for prior errors ---
    if state.get("error"):
        return {"error": state["error"]}

    # --- Guard: check for raw text ---
    raw_text = state.get("raw_text", "")
    if not raw_text.strip():
        return {
            "rag_context_structuring": "",
            "rag_context_summary": "",
            "rag_context_recommendation": "",
        }

    try:
        retriever = CreditRAGRetriever()

        if not retriever.is_available():
            logger.info("RAG knowledge base not available. Continuing without regulatory context.")
            return {
                "rag_context_structuring": "",
                "rag_context_summary": "",
                "rag_context_recommendation": "",
            }

        logger.info("RAG knowledge base available. Retrieving regulatory context...")

        # --- Retrieve context for Data Structuring ---
        # Use first 500 chars of raw text as context hint
        snippet = raw_text[:500]
        context_structuring = retriever.retrieve_for_data_structuring(snippet)
        logger.info(f"Data structuring context: {len(context_structuring)} chars")

        # --- Retrieve context for Summary Generation ---
        # We don't have credit_tier yet (comes from classification), so use general query
        context_summary = retriever.retrieve_for_summary("general")
        logger.info(f"Summary context: {len(context_summary)} chars")

        # --- Retrieve context for Recommendation ---
        context_recommendation = retriever.retrieve_for_recommendation(
            credit_tier="general",
            key_issues=["credit utilization", "payment history", "credit mix"],
        )
        logger.info(f"Recommendation context: {len(context_recommendation)} chars")

        return {
            "rag_context_structuring": context_structuring,
            "rag_context_summary": context_summary,
            "rag_context_recommendation": context_recommendation,
        }

    except Exception as e:
        # RAG failure is non-fatal — log and continue
        logger.warning(f"RAG retrieval failed (non-fatal): {e}")
        return {
            "rag_context_structuring": "",
            "rag_context_summary": "",
            "rag_context_recommendation": "",
        }
