#!/usr/bin/env python3
"""
Initialize RAG Knowledge Base — Downloads official regulatory documents,
processes them into chunks, and populates the ChromaDB vector store.

Usage:
    python -m scripts.initialize_rag
    python -m scripts.initialize_rag --refresh    # Re-download and reindex all documents
    python -m scripts.initialize_rag --curated-only  # Only process curated (local) documents
"""

import argparse
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag.config import KNOWLEDGE_BASE_DIR, DOCUMENTS_DIR, CHROMA_PERSIST_DIR
from src.rag.document_processor import (
    download_all_official_documents,
    process_all_documents,
    save_manifest,
)
from src.rag.vector_store import (
    get_or_create_collection,
    add_chunks,
    clear_collection,
    collection_is_populated,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("initialize_rag")


def main():
    parser = argparse.ArgumentParser(description="Initialize the CreditSense RAG knowledge base.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Clear existing index and re-download/reprocess all documents.",
    )
    parser.add_argument(
        "--curated-only",
        action="store_true",
        help="Only process curated (local) documents, skip downloads.",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  CreditSense RAG — Knowledge Base Initialization")
    print("=" * 60)

    # --- Step 1: Create directories ---
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
    print(f"\n[1/5] Directories ready:")
    print(f"  Documents: {DOCUMENTS_DIR}")
    print(f"  ChromaDB:  {CHROMA_PERSIST_DIR}")

    # --- Step 2: Check if already initialized ---
    if not args.refresh and collection_is_populated():
        print(f"\n[INFO] Knowledge base is already populated.")
        print(f"  Use --refresh to re-download and reindex all documents.")

        collection = get_or_create_collection()
        if collection:
            print(f"  Current document count: {collection.count()}")
        return

    # --- Step 3: Clear existing index if refreshing ---
    if args.refresh:
        print(f"\n[2/5] Clearing existing index...")
        clear_collection()
        print("  Index cleared.")
    else:
        print(f"\n[2/5] Fresh initialization (no existing index).")

    # --- Step 4: Download official documents ---
    download_results = {}
    if not args.curated_only:
        print(f"\n[3/5] Downloading official regulatory documents...")
        download_results = download_all_official_documents()

        success_count = sum(1 for r in download_results.values() if r["success"])
        skip_count = sum(1 for r in download_results.values() if r.get("skipped"))
        fail_count = sum(1 for r in download_results.values() if not r["success"])

        print(f"  Downloaded: {success_count - skip_count}")
        print(f"  Already existed: {skip_count}")
        if fail_count > 0:
            print(f"  Failed: {fail_count}")
            for key, result in download_results.items():
                if not result["success"]:
                    print(f"    - {key}")
    else:
        print(f"\n[3/5] Skipping downloads (curated-only mode).")

    # --- Step 5: Process all documents into chunks ---
    print(f"\n[4/5] Processing documents into chunks...")
    all_chunks = process_all_documents()

    if not all_chunks:
        print("  [WARNING] No chunks generated. Check documents directory.")
        print(f"  Documents directory: {DOCUMENTS_DIR}")
        print(f"  Files present: {os.listdir(DOCUMENTS_DIR) if os.path.exists(DOCUMENTS_DIR) else 'N/A'}")
        return

    print(f"  Total chunks: {len(all_chunks)}")

    # Show chunk statistics
    sources = set()
    categories = {}
    for chunk in all_chunks:
        src = chunk["metadata"].get("source", "unknown")
        cat = chunk["metadata"].get("category", "unknown")
        sources.add(src)
        categories[cat] = categories.get(cat, 0) + 1

    print(f"  Sources: {len(sources)}")
    for cat, count in sorted(categories.items()):
        print(f"    {cat}: {count} chunks")

    # --- Step 6: Add chunks to ChromaDB ---
    print(f"\n[5/5] Indexing chunks in ChromaDB...")
    added = add_chunks(all_chunks)
    print(f"  Chunks indexed: {added}")

    # --- Save manifest ---
    if download_results:
        save_manifest(download_results)
        print(f"\n  Manifest saved to {os.path.join(KNOWLEDGE_BASE_DIR, 'manifest.json')}")

    # --- Summary ---
    collection = get_or_create_collection()
    total_in_db = collection.count() if collection else 0

    print("\n" + "=" * 60)
    print("  Initialization Complete!")
    print("=" * 60)
    print(f"  Documents processed: {len(sources)}")
    print(f"  Total chunks in DB:  {total_in_db}")
    print(f"  ChromaDB location:   {CHROMA_PERSIST_DIR}")
    print(f"\n  The RAG system is now ready for use with CreditSense.")
    print(f"  Run: python main.py <credit_report.pdf>")


if __name__ == "__main__":
    main()
