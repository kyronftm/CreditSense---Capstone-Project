"""
Output Formatting Node — Seventh (final) node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Assemble all prior outputs into a single structured report.
  2. Add metadata (timestamp, bureau, tier).
  3. Inject the required financial advice disclaimer.
  4. Produce the final_report dict ready for delivery to the user.

This is a deterministic node — no LLM call needed.
"""

from datetime import datetime, timezone
from src.state import CreditSenseState

FINANCIAL_DISCLAIMER = (
    "DISCLAIMER: The information and recommendations provided by CreditSense are for "
    "educational purposes only and do not constitute financial, legal, or professional advice. "
    "Credit improvement results may vary based on individual circumstances. "
    "Please consult a certified financial advisor or credit counselor for personalized guidance. "
    "CreditSense does not guarantee any specific credit score changes or outcomes."
)


def output_formatting_node(state: CreditSenseState) -> CreditSenseState:
    """
    Assembles all pipeline outputs into a final structured report.

    Args:
        state: Pipeline state with all prior node outputs.

    Returns:
        Updated state with 'final_report' dict or 'error'.
    """

    # --- Guard: check for prior errors ---
    if state.get("error"):
        return {
            "final_report": {
                "status": "error",
                "error_message": state["error"],
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "disclaimer": FINANCIAL_DISCLAIMER,
            },
        }

    # --- Guard: check minimum required data ---
    structured_data = state.get("structured_data")
    summary = state.get("summary")
    recommendations = state.get("recommendations")

    if not structured_data:
        return {
            "final_report": {
                "status": "error",
                "error_message": "No structured data available for report generation.",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "disclaimer": FINANCIAL_DISCLAIMER,
            },
        }

    # --- Extract key info for the report header ---
    credit_score_data = structured_data.get("credit_score", {})
    personal_info = structured_data.get("personal_info", {})
    account_summary = structured_data.get("account_summary", {})

    # --- Build the final report ---
    final_report = {
        "status": "success",
        "generated_at": datetime.now(timezone.utc).isoformat(),

        # Report metadata
        "metadata": {
            "bureau": state.get("bureau", "unknown"),
            "credit_tier": state.get("credit_tier", "unknown"),
            "report_date": structured_data.get("report_date"),
            "report_number": structured_data.get("report_number"),
            "pages_processed": state.get("page_count", 0),
        },

        # Consumer overview (PII-safe: no SSN, no full account numbers)
        "consumer": {
            "name": personal_info.get("full_name", "Unknown"),
            "credit_score": credit_score_data.get("score"),
            "score_model": credit_score_data.get("score_model"),
            "risk_level": credit_score_data.get("risk_level"),
            "key_factors": credit_score_data.get("key_factors", []),
        },

        # Account overview
        "account_overview": {
            "total_accounts": account_summary.get("total_accounts", 0),
            "open_accounts": account_summary.get("open_accounts", 0),
            "closed_accounts": account_summary.get("closed_accounts", 0),
            "total_balance": account_summary.get("total_balance", 0),
            "total_credit_limit": account_summary.get("total_credit_limit", 0),
            "overall_utilization": account_summary.get("overall_utilization", 0),
            "on_time_payment_percentage": account_summary.get("on_time_payment_percentage"),
            "total_late_payments": account_summary.get("total_late_payments", 0),
            "hard_inquiries": account_summary.get("hard_inquiries_count", 0),
        },

        # Generated content
        "summary": summary or "Summary could not be generated.",
        "recommendations": recommendations or [],

        # Compliance
        "disclaimer": FINANCIAL_DISCLAIMER,
    }

    return {
        "final_report": final_report,
    }
