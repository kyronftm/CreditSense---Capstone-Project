"""
Document Processor — Downloads, extracts text from, and chunks regulatory documents.
"""

import os
import json
import logging
from datetime import datetime
from typing import Optional

import requests
from pypdf import PdfReader

from src.rag.config import (
    RAG_CONFIG,
    DOCUMENTS_DIR,
    KNOWLEDGE_BASE_DIR,
    DOCUMENT_SOURCES,
)

logger = logging.getLogger(__name__)


def download_document(url: str, save_path: str, timeout: int = 60) -> bool:
    """
    Download a PDF document from a URL and save it locally.

    Args:
        url: The URL to download from.
        save_path: Local file path to save the document.
        timeout: Request timeout in seconds.

    Returns:
        True if download succeeded, False otherwise.
    """
    try:
        logger.info(f"Downloading: {url}")
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()

        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        file_size = os.path.getsize(save_path)
        logger.info(f"Downloaded: {save_path} ({file_size:,} bytes)")
        return True

    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file using pypdf.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Extracted text as a single string.
    """
    try:
        reader = PdfReader(pdf_path)
        pages_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages_text.append(text.strip())

        full_text = "\n\n".join(pages_text)
        logger.info(f"Extracted {len(pages_text)} pages from {pdf_path} ({len(full_text):,} chars)")
        return full_text

    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


def extract_text_from_txt(txt_path: str) -> str:
    """
    Read text from a .txt or .md file.

    Args:
        txt_path: Path to the text file.

    Returns:
        File contents as string.
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception as e:
        logger.error(f"Failed to read {txt_path}: {e}")
        return ""


def chunk_text(
    text: str,
    metadata: dict,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
) -> list[dict]:
    """
    Split text into overlapping chunks with metadata.

    Args:
        text: The text to chunk.
        metadata: Metadata to attach to each chunk (source, category, etc.).
        chunk_size: Characters per chunk (default from config).
        chunk_overlap: Overlap between chunks (default from config).

    Returns:
        List of dicts with 'text' and 'metadata' keys.
    """
    chunk_size = chunk_size or RAG_CONFIG["chunk_size"]
    chunk_overlap = chunk_overlap or RAG_CONFIG["chunk_overlap"]

    if not text.strip():
        return []

    # Split on paragraph boundaries first, then recombine into chunks
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph exceeds chunk_size, save current and start new
        if len(current_chunk) + len(para) + 2 > chunk_size and current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": {
                    **metadata,
                    "chunk_index": len(chunks),
                },
            })
            # Keep overlap from end of previous chunk
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                current_chunk = current_chunk[-chunk_overlap:] + "\n\n" + para
            else:
                current_chunk = para
        else:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para

    # Don't forget the last chunk
    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "metadata": {
                **metadata,
                "chunk_index": len(chunks),
            },
        })

    return chunks


def process_all_documents() -> list[dict]:
    """
    Process all documents in the knowledge_base/documents/ directory.
    Handles both PDF and text files.

    Returns:
        List of all chunks from all documents.
    """
    all_chunks = []

    if not os.path.exists(DOCUMENTS_DIR):
        logger.warning(f"Documents directory not found: {DOCUMENTS_DIR}")
        return all_chunks

    for filename in sorted(os.listdir(DOCUMENTS_DIR)):
        filepath = os.path.join(DOCUMENTS_DIR, filename)

        if not os.path.isfile(filepath):
            continue

        # Determine file type and extract text
        if filename.lower().endswith(".pdf"):
            text = extract_text_from_pdf(filepath)
        elif filename.lower().endswith((".txt", ".md")):
            text = extract_text_from_txt(filepath)
        else:
            logger.info(f"Skipping unsupported file: {filename}")
            continue

        if not text:
            logger.warning(f"No text extracted from {filename}")
            continue

        # Build metadata
        metadata = {
            "source": filename,
            "file_path": filepath,
            "processed_at": datetime.now().isoformat(),
        }

        # Try to match with known document sources for richer metadata
        for key, source_info in DOCUMENT_SOURCES.items():
            if key in filename.lower() or source_info["name"].lower() in filename.lower():
                metadata["official_name"] = source_info["name"]
                metadata["category"] = source_info["category"]
                break

        # If no category found, infer from filename
        if "category" not in metadata:
            metadata["category"] = "curated"

        chunks = chunk_text(text, metadata)
        all_chunks.extend(chunks)
        logger.info(f"Processed {filename}: {len(chunks)} chunks")

    logger.info(f"Total chunks from all documents: {len(all_chunks)}")
    return all_chunks


def download_all_official_documents() -> dict:
    """
    Download all official regulatory documents defined in DOCUMENT_SOURCES.

    Returns:
        Dict with download results {doc_key: {"success": bool, "path": str}}.
    """
    os.makedirs(DOCUMENTS_DIR, exist_ok=True)
    results = {}

    for doc_key, source_info in DOCUMENT_SOURCES.items():
        filename = f"{doc_key}.pdf"
        save_path = os.path.join(DOCUMENTS_DIR, filename)

        # Skip if already downloaded
        if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
            logger.info(f"Already downloaded: {filename}")
            results[doc_key] = {"success": True, "path": save_path, "skipped": True}
            continue

        success = download_document(source_info["url"], save_path)
        results[doc_key] = {"success": success, "path": save_path, "skipped": False}

    return results


def save_manifest(download_results: dict) -> None:
    """
    Save a manifest file with metadata about downloaded/processed documents.

    Args:
        download_results: Results from download_all_official_documents().
    """
    manifest = {
        "created_at": datetime.now().isoformat(),
        "documents": {},
    }

    for doc_key, result in download_results.items():
        source_info = DOCUMENT_SOURCES.get(doc_key, {})
        manifest["documents"][doc_key] = {
            "name": source_info.get("name", doc_key),
            "url": source_info.get("url", ""),
            "category": source_info.get("category", "unknown"),
            "downloaded": result["success"],
            "path": result["path"],
        }

    manifest_path = os.path.join(KNOWLEDGE_BASE_DIR, "manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"Manifest saved to {manifest_path}")
