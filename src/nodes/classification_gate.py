"""
Classification Gate Node — Fourth node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Detect the credit bureau from the structured data (Experian, TransUnion, Equifax).
  2. Classify the credit tier based on the FICO score (Excellent, Good, Fair, Poor).
  3. This is a deterministic node — no LLM call needed.

FICO Score Tiers (US Standard):
  - Excellent: 800-850
  - Very Good: 740-799
  - Good: 670-739
  - Fair: 580-669
  - Poor: 300-579
"""

from src.state import CreditSenseState

# FICO Score tier boundaries
CREDIT_TIERS = [
    (800, 850, "excellent"),
    (740, 799, "very_good"),
    (670, 739, "good"),
    (580, 669, "fair"),
    (300, 579, "poor"),
]

# Known bureau identifiers (case-insensitive matching)
KNOWN_BUREAUS = {
    "experian": "experian",
    "transunion": "transunion",
    "trans union": "transunion",
    "equifax": "equifax",
}


def _classify_credit_tier(score: int) -> str:
    """
    Classify a FICO score into a credit tier.

    Args:
        score: FICO score (300-850).

    Returns:
        Credit tier string: excellent, very_good, good, fair, or poor.
    """
    for low, high, tier in CREDIT_TIERS:
        if low <= score <= high:
            return tier

    # Edge cases: score outside expected range
    if score > 850:
        return "excellent"
    return "poor"


def _detect_bureau(structured_data: dict) -> str:
    """
    Detect the credit bureau from structured report data.

    Checks the report_bureau field first, then falls back to
    scanning account names and report metadata for bureau identifiers.

    Args:
        structured_data: The structured credit report dictionary.

    Returns:
        Bureau identifier string or "unknown".
    """
    # Check explicit report_bureau field
    bureau_field = (structured_data.get("report_bureau") or "").strip().lower()
    for keyword, bureau_id in KNOWN_BUREAUS.items():
        if keyword in bureau_field:
            return bureau_id

    # Fallback: check report_number for bureau codes
    report_number = (structured_data.get("report_number") or "").upper()
    if "EXP" in report_number:
        return "experian"
    if "TU" in report_number or "TRU" in report_number:
        return "transunion"
    if "EFX" in report_number or "EQ" in report_number:
        return "equifax"

    return "unknown"


def classification_gate_node(state: CreditSenseState) -> CreditSenseState:
    """
    Classifies the credit report by bureau and credit tier.

    This is a deterministic gate — no LLM call. It reads the structured
    data and applies rule-based classification.

    Args:
        state: Pipeline state with 'structured_data'.

    Returns:
        Updated state with 'bureau' and 'credit_tier', or 'error'.
    """

    # --- Guard: check for structured data ---
    structured_data = state.get("structured_data")
    if not structured_data:
        return {
            "error": "Classification skipped: no structured data available.",
        }

    # --- Guard: check for prior errors ---
    if state.get("error"):
        return {"error": state["error"]}

    # --- Detect bureau ---
    bureau = _detect_bureau(structured_data)

    # --- Extract and classify credit score ---
    credit_score_data = structured_data.get("credit_score", {})
    score = credit_score_data.get("score")

    if score is None:
        return {
            "error": "Classification failed: no credit score found in structured data.",
        }

    if not isinstance(score, (int, float)):
        return {
            "error": f"Classification failed: invalid credit score type ({type(score).__name__}).",
        }

    score = int(score)
    credit_tier = _classify_credit_tier(score)

    return {
        "bureau": bureau,
        "credit_tier": credit_tier,
    }
