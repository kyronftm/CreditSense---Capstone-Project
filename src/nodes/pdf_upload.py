"""
PDF Upload Node — First node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Validate that the provided file path exists.
  2. Validate that the file is a PDF (by extension and magic bytes).
  3. Validate file size (max 10 MB).
  4. Set pdf_valid = True on success, or populate validation_error on failure.
"""

import os
from src.state import CreditSenseState

# Constants
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
PDF_MAGIC_BYTES = b"%PDF"


def pdf_upload_node(state: CreditSenseState) -> CreditSenseState:
    """
    Validates the uploaded PDF file path and prepares it for downstream processing.

    Args:
        state: The current pipeline state containing 'pdf_path'.

    Returns:
        Updated state with 'pdf_valid' and optionally 'validation_error'.
    """
    pdf_path = state.get("pdf_path", "")

    # --- Check 1: Path is provided ---
    if not pdf_path or not pdf_path.strip():
        return {
            "pdf_valid": False,
            "validation_error": "No file path provided. Please provide a path to a credit report PDF.",
        }

    pdf_path = pdf_path.strip()

    # --- Check 2: File exists ---
    if not os.path.exists(pdf_path):
        return {
            "pdf_valid": False,
            "validation_error": f"File not found: '{pdf_path}'. Please check the path and try again.",
        }

    # --- Check 3: Is a file (not a directory) ---
    if not os.path.isfile(pdf_path):
        return {
            "pdf_valid": False,
            "validation_error": f"Path is not a file: '{pdf_path}'. Please provide a path to a PDF file.",
        }

    # --- Check 4: File extension is .pdf ---
    _, ext = os.path.splitext(pdf_path)
    if ext.lower() != ".pdf":
        return {
            "pdf_valid": False,
            "validation_error": f"Invalid file type: '{ext}'. Only PDF files (.pdf) are accepted.",
        }

    # --- Check 5: File size within limit ---
    file_size = os.path.getsize(pdf_path)
    if file_size == 0:
        return {
            "pdf_valid": False,
            "validation_error": "The file is empty (0 bytes). Please provide a valid credit report PDF.",
        }

    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        return {
            "pdf_valid": False,
            "validation_error": (
                f"File size ({size_mb:.1f} MB) exceeds the maximum allowed size "
                f"of {MAX_FILE_SIZE_MB} MB. Please provide a smaller file."
            ),
        }

    # --- Check 6: PDF magic bytes validation ---
    try:
        with open(pdf_path, "rb") as f:
            header = f.read(4)
        if header != PDF_MAGIC_BYTES:
            return {
                "pdf_valid": False,
                "validation_error": (
                    "The file does not appear to be a valid PDF. "
                    "The file header does not match the PDF format."
                ),
            }
    except PermissionError:
        return {
            "pdf_valid": False,
            "validation_error": f"Permission denied: cannot read '{pdf_path}'.",
        }
    except OSError as e:
        return {
            "pdf_valid": False,
            "validation_error": f"Error reading file: {str(e)}",
        }

    # --- All checks passed ---
    return {
        "pdf_path": pdf_path,
        "pdf_valid": True,
        "validation_error": None,
    }
