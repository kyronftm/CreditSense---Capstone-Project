"""
Text Extraction Node — Second node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Check that the PDF passed validation (pdf_valid == True).
  2. Open the PDF using pdfplumber.
  3. Extract raw text from all pages (including table-aware extraction).
  4. Return raw_text and page_count in the state.
"""

import pdfplumber
from src.state import CreditSenseState


def text_extraction_node(state: CreditSenseState) -> CreditSenseState:
    """
    Extracts raw text content from a validated PDF credit report.

    Uses pdfplumber for text extraction, which handles both regular text
    and tabular data effectively — important for credit report tables.

    Args:
        state: Pipeline state with 'pdf_path' and 'pdf_valid'.

    Returns:
        Updated state with 'raw_text', 'page_count', or 'error'.
    """

    # --- Guard: only proceed if PDF was validated ---
    if not state.get("pdf_valid", False):
        return {
            "error": (
                "Text extraction skipped: PDF validation failed. "
                f"Reason: {state.get('validation_error', 'Unknown')}"
            ),
        }

    pdf_path = state["pdf_path"]

    try:
        extracted_pages = []

        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)

            for i, page in enumerate(pdf.pages):
                page_text_parts = []

                # --- Extract tables first (structured data) ---
                tables = page.extract_tables()
                table_texts = set()  # Track table text to avoid duplication

                for table in tables:
                    table_rows = []
                    for row in table:
                        cleaned_row = [
                            cell.strip() if cell else "" for cell in row
                        ]
                        table_rows.append(" | ".join(cleaned_row))
                        # Track individual cell text for dedup
                        for cell in cleaned_row:
                            if cell:
                                table_texts.add(cell)

                    table_rows_text = "\n".join(table_rows)
                    page_text_parts.append(table_rows_text)

                # --- Extract regular text ---
                regular_text = page.extract_text()
                if regular_text:
                    # Add non-table text lines to avoid duplication
                    for line in regular_text.split("\n"):
                        line_stripped = line.strip()
                        # Only add if this line isn't already captured from a table
                        if line_stripped and line_stripped not in table_texts:
                            page_text_parts.append(line_stripped)

                # Combine page content
                page_content = "\n".join(page_text_parts)
                if page_content.strip():
                    extracted_pages.append(f"--- Page {i + 1} ---\n{page_content}")

        # --- Validate extraction produced content ---
        raw_text = "\n\n".join(extracted_pages)

        if not raw_text.strip():
            return {
                "raw_text": "",
                "page_count": page_count,
                "error": (
                    "No text could be extracted from the PDF. "
                    "The file may be image-based (scanned) or empty. "
                    "Consider using an OCR-enabled PDF for best results."
                ),
            }

        return {
            "raw_text": raw_text,
            "page_count": page_count,
        }

    except pdfplumber.pdfminer.pdfparser.PDFSyntaxError:
        return {
            "error": "The file appears to be corrupted or is not a valid PDF.",
        }
    except Exception as e:
        return {
            "error": f"Unexpected error during text extraction: {str(e)}",
        }
