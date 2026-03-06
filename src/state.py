"""
CreditSense State Definition.
Defines the shared state schema used across all LangGraph nodes.
"""

from typing import Optional
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class CreditSenseState(TypedDict, total=False):
    """Shared state that flows through the LangGraph pipeline."""

    # --- PDF Upload Node ---
    pdf_path: str                     # Input file path provided by the user
    pdf_valid: bool                   # Whether the PDF passed validation
    validation_error: Optional[str]   # Error message if validation failed

    # --- Text Extraction Node ---
    raw_text: str                     # Raw text extracted from the PDF
    page_count: int                   # Number of pages in the PDF

    # --- Data Structuring Node (Haiku) ---
    structured_data: dict             # Parsed credit report fields as structured JSON

    # --- Classification Gate ---
    bureau: str                       # Detected bureau: "experian", "transunion", "equifax", "unknown"
    credit_tier: str                  # "excellent", "good", "fair", "poor"

    # --- Summary Generation Node (Sonnet) ---
    summary: str                      # Plain-language credit health summary

    # --- Recommendation Node (Sonnet) ---
    recommendations: list             # List of actionable recommendations

    # --- Output Formatting ---
    final_report: dict                # The complete structured output report

    # --- RAG Context ---
    rag_context_structuring: str      # Regulatory context for data structuring node
    rag_context_summary: str          # Regulatory context for summary generation node
    rag_context_recommendation: str   # Regulatory context for recommendation node

    # --- Metadata ---
    error: Optional[str]              # Global error field for pipeline failures
