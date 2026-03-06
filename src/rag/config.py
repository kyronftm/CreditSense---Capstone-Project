"""
RAG Configuration — Central configuration for the CreditSense RAG system.
"""

import os

# Base paths
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_DIR = os.path.join(_PROJECT_ROOT, "knowledge_base")
DOCUMENTS_DIR = os.path.join(KNOWLEDGE_BASE_DIR, "documents")

# ChromaDB persist directory — configurable via environment variable.
# ChromaDB uses SQLite internally; if the project directory doesn't
# support full SQLite locking (e.g., some network/FUSE mounts), set
# CREDITSENSE_CHROMA_DIR to a local filesystem path.
_default_chroma_dir = os.path.join(KNOWLEDGE_BASE_DIR, "chroma_db")
CHROMA_PERSIST_DIR = os.environ.get("CREDITSENSE_CHROMA_DIR", _default_chroma_dir)

RAG_CONFIG = {
    # ChromaDB settings
    "collection_name": "creditsense_regulatory",
    "persist_directory": CHROMA_PERSIST_DIR,

    # Embedding model (sentence-transformers)
    "embedding_model": "all-MiniLM-L6-v2",

    # Chunking settings
    "chunk_size": 500,        # characters per chunk
    "chunk_overlap": 50,      # overlap between chunks

    # Retrieval settings
    "top_k": 4,               # number of documents to retrieve per query
    "min_relevance_score": 0.3,  # minimum cosine similarity threshold
}

# Official regulatory document sources for download
DOCUMENT_SOURCES = {
    "cfpb_fcra_procedures": {
        "url": "https://files.consumerfinance.gov/f/documents/102012_cfpb_fair-credit-reporting-act-fcra_procedures.pdf",
        "name": "CFPB FCRA Examination Procedures",
        "category": "regulation",
    },
    "ftc_fcra_full_text": {
        "url": "https://www.ftc.gov/system/files/ftc_gov/pdf/fcra-may2023-508.pdf",
        "name": "Fair Credit Reporting Act - Full Text (FTC)",
        "category": "statute",
    },
    "fed_reserve_credit_tips": {
        "url": "https://www.federalreserve.gov/pubs/creditscore/creditscoretips_2.pdf",
        "name": "Federal Reserve - 5 Tips for Improving Your Credit Score",
        "category": "guidance",
    },
    "occ_fair_credit_reporting": {
        "url": "https://www.occ.gov/publications-and-resources/publications/comptrollers-handbook/files/fair-credit-reporting/pub-ch-fair-credit-reporting.pdf",
        "name": "OCC Comptroller's Handbook - Fair Credit Reporting",
        "category": "examination",
    },
}

# Categories for curated documents (created locally, not downloaded)
CURATED_DOCUMENT_CATEGORIES = [
    "fcra_consumer_rights",
    "ecoa_overview",
    "fdcpa_overview",
    "tila_overview",
    "fact_act_overview",
    "credit_score_factors",
    "credit_improvement_strategies",
    "cfpb_consumer_guidance",
]
