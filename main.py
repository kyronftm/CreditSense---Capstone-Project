"""
CreditSense — AI-Powered Credit Report Analysis & Recommendation Agent.

Usage:
    python main.py <path_to_credit_report.pdf>

Example:
    python main.py data/sample_reports/sample_credit_report.pdf
"""

import json
import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.graph import credit_sense_graph
from src.rag.vector_store import collection_is_populated
from src.views import build_dashboard_html


def run_analysis(pdf_path: str) -> tuple[dict, dict]:
    """
    Run the full CreditSense analysis pipeline on a credit report PDF.

    Args:
        pdf_path: Path to the credit report PDF file.

    Returns:
        Tuple of (final_report dict, structured_data dict).
    """
    initial_state = {"pdf_path": pdf_path}
    result = credit_sense_graph.invoke(initial_state)
    report = result.get("final_report", {"status": "error", "error_message": "No report generated."})
    structured_data = result.get("structured_data", {})
    return report, structured_data


def print_report(report: dict):
    """Pretty-print the final report to the console."""

    if report["status"] == "error":
        print("\n" + "=" * 60)
        print("  CREDITSENSE — ERROR")
        print("=" * 60)
        print(f"\n  Error: {report.get('error_message', 'Unknown error')}")
        print(f"\n  {report.get('disclaimer', '')}")
        print("=" * 60)
        return

    print("\n" + "=" * 60)
    print("  CREDITSENSE — CREDIT REPORT ANALYSIS")
    print("=" * 60)

    # Metadata
    meta = report.get("metadata", {})
    print(f"\n  Bureau: {meta.get('bureau', 'N/A').title()}")
    print(f"  Report Date: {meta.get('report_date', 'N/A')}")
    print(f"  Credit Tier: {meta.get('credit_tier', 'N/A').replace('_', ' ').title()}")
    print(f"  Pages Processed: {meta.get('pages_processed', 0)}")

    # Consumer
    consumer = report.get("consumer", {})
    print(f"\n  Name: {consumer.get('name', 'N/A')}")
    print(f"  Credit Score: {consumer.get('credit_score', 'N/A')} ({consumer.get('risk_level', 'N/A')})")
    print(f"  Score Model: {consumer.get('score_model', 'N/A')}")

    # Account Overview
    overview = report.get("account_overview", {})
    print(f"\n  --- Account Overview ---")
    print(f"  Total Accounts: {overview.get('total_accounts', 0)} (Open: {overview.get('open_accounts', 0)}, Closed: {overview.get('closed_accounts', 0)})")
    print(f"  Total Balance: ${overview.get('total_balance', 0):,.2f}")
    print(f"  Credit Limit: ${overview.get('total_credit_limit', 0):,.2f}")
    print(f"  Utilization: {overview.get('overall_utilization', 0):.1f}%")
    print(f"  On-Time Payments: {overview.get('on_time_payment_percentage', 'N/A')}%")
    print(f"  Late Payments: {overview.get('total_late_payments', 0)}")
    print(f"  Hard Inquiries: {overview.get('hard_inquiries', 0)}")

    # Summary
    print(f"\n  --- Credit Health Summary ---")
    print(f"\n{report.get('summary', 'No summary available.')}")

    # Recommendations
    recs = report.get("recommendations", [])
    if recs:
        print(f"\n  --- Recommendations ({len(recs)}) ---")
        for i, rec in enumerate(recs, 1):
            print(f"\n  {i}. [{rec.get('priority', 'N/A')}] {rec.get('action', 'N/A')}")
            print(f"     Why: {rec.get('reason', 'N/A')}")
            print(f"     Impact: {rec.get('expected_impact', 'N/A')}")
            print(f"     Timeframe: {rec.get('timeframe', 'N/A')}")

    # Disclaimer
    print(f"\n{'=' * 60}")
    print(f"  {report.get('disclaimer', '')}")
    print(f"{'=' * 60}")
    print(f"  Generated: {report.get('generated_at', 'N/A')}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_credit_report.pdf>")
        print("Example: python main.py data/sample_reports/sample_credit_report.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]
    print(f"Analyzing credit report: {pdf_path}")

    # Check RAG availability
    try:
        if collection_is_populated():
            print("[RAG] Regulatory knowledge base: ACTIVE")
        else:
            print("[RAG] Regulatory knowledge base: NOT INITIALIZED")
            print("      Run 'python -m scripts.initialize_rag' to enable RAG-enhanced analysis.")
    except Exception:
        print("[RAG] Regulatory knowledge base: UNAVAILABLE")

    print("This may take 30-45 seconds...\n")

    report, structured_data = run_analysis(pdf_path)

    # Print to console
    print_report(report)

    # Save JSON output
    project_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(project_dir, "output_report.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Full JSON report saved to: {output_path}")

    # Generate HTML dashboard
    if report.get("status") == "success":
        dashboard_path = os.path.join(project_dir, "dashboard.html")
        html = build_dashboard_html(report, structured_data=structured_data)
        with open(dashboard_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"  Interactive dashboard saved to: {dashboard_path}")


if __name__ == "__main__":
    main()
