"""
CreditSense LangGraph Pipeline — Iteration 1 (Workflow Agent).

Wires all nodes into a deterministic StateGraph:
  PDF Upload → Text Extraction → Data Structuring (Haiku) →
  Classification Gate → Summary Generation (Sonnet) →
  Recommendation (Sonnet) → Output Formatting → END

Each node reads from and writes to the shared CreditSenseState.
"""

from langgraph.graph import StateGraph, END
from src.state import CreditSenseState
from src.nodes.pdf_upload import pdf_upload_node
from src.nodes.text_extraction import text_extraction_node
from src.nodes.data_structuring import data_structuring_node
from src.nodes.classification_gate import classification_gate_node
from src.nodes.summary_generation import summary_generation_node
from src.nodes.recommendation import recommendation_node
from src.nodes.output_formatting import output_formatting_node
from src.nodes.rag_retrieval import rag_retrieval_node


def _should_continue_after_upload(state: CreditSenseState) -> str:
    """Route after PDF upload: continue if valid, skip to output if not."""
    if state.get("pdf_valid", False):
        return "text_extraction"
    return "output_formatting"


def _should_continue_after_extraction(state: CreditSenseState) -> str:
    """Route after text extraction: continue to RAG retrieval if text found, skip to output if error."""
    if state.get("error"):
        return "output_formatting"
    if state.get("raw_text", "").strip():
        return "rag_retrieval"
    return "output_formatting"


def _should_continue_after_rag(state: CreditSenseState) -> str:
    """Route after RAG retrieval: always continue to data structuring (RAG failure is non-fatal)."""
    if state.get("error"):
        return "output_formatting"
    return "data_structuring"


def _should_continue_after_structuring(state: CreditSenseState) -> str:
    """Route after data structuring: continue if data structured, skip to output if error."""
    if state.get("error"):
        return "output_formatting"
    if state.get("structured_data"):
        return "classification_gate"
    return "output_formatting"


def _should_continue_after_classification(state: CreditSenseState) -> str:
    """Route after classification: continue if classified, skip to output if error."""
    if state.get("error"):
        return "output_formatting"
    return "summary_generation"


def _should_continue_after_summary(state: CreditSenseState) -> str:
    """Route after summary: continue if summary generated, skip to output if error."""
    if state.get("error"):
        return "output_formatting"
    return "recommendation"


def _should_continue_after_recommendation(state: CreditSenseState) -> str:
    """Route after recommendation: always go to output formatting."""
    return "output_formatting"


def build_graph() -> StateGraph:
    """
    Build and compile the CreditSense workflow graph.

    Returns:
        A compiled LangGraph StateGraph ready to invoke.
    """

    # --- Create the graph ---
    graph = StateGraph(CreditSenseState)

    # --- Add nodes ---
    graph.add_node("pdf_upload", pdf_upload_node)
    graph.add_node("text_extraction", text_extraction_node)
    graph.add_node("rag_retrieval", rag_retrieval_node)
    graph.add_node("data_structuring", data_structuring_node)
    graph.add_node("classification_gate", classification_gate_node)
    graph.add_node("summary_generation", summary_generation_node)
    graph.add_node("recommendation", recommendation_node)
    graph.add_node("output_formatting", output_formatting_node)

    # --- Set entry point ---
    graph.set_entry_point("pdf_upload")

    # --- Add conditional edges (error routing) ---
    graph.add_conditional_edges(
        "pdf_upload",
        _should_continue_after_upload,
        {"text_extraction": "text_extraction", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "text_extraction",
        _should_continue_after_extraction,
        {"rag_retrieval": "rag_retrieval", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "rag_retrieval",
        _should_continue_after_rag,
        {"data_structuring": "data_structuring", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "data_structuring",
        _should_continue_after_structuring,
        {"classification_gate": "classification_gate", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "classification_gate",
        _should_continue_after_classification,
        {"summary_generation": "summary_generation", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "summary_generation",
        _should_continue_after_summary,
        {"recommendation": "recommendation", "output_formatting": "output_formatting"},
    )
    graph.add_conditional_edges(
        "recommendation",
        _should_continue_after_recommendation,
        {"output_formatting": "output_formatting"},
    )

    # --- Output formatting → END ---
    graph.add_edge("output_formatting", END)

    # --- Compile ---
    return graph.compile()


# Singleton compiled graph
credit_sense_graph = build_graph()
