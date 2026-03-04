"""
app.py
Handles the Gradio layout and acts as the bridge between backend logic and views.
"""

import gradio as gr

# Import backend resources
from backend import financial_graph, pdf_to_base64, FinancialState
# Import all HTML rendering functions
import views


def analyze_statement(pdf_file):
    """Bridge function connecting UI interaction to backend graph execution & views rendering"""
    if pdf_file is None:
        empty = "<div style='color:#9ca3af;padding:20px;'>Upload a PDF to begin.</div>"
        return empty, empty, empty, empty, "Please upload a PDF bank statement."

    try:
        pdf_b64 = pdf_to_base64(pdf_file.name)
        pdf_path = pdf_file.name
    except Exception as e:
        err = f"<div style='color:#ef4444;'>Error reading PDF: {e}</div>"
        return err, err, err, err, str(e)

    initial: FinancialState = {
        "pdf_base64": pdf_b64,
        "pdf_path":   pdf_path,
        "raw_text": "",
        "transactions": [],
        "macro_buckets": {},
        "sub_categories": {},
        "total_income": 0.0,
        "total_expenses": 0.0,
        "income_tier": "",
        "tier_label": "",
        "recommendations": "",
        "budget_analysis": "",
    }

    # 1. Execute the backend LangGraph logic
    result = financial_graph.invoke(initial)

    # 2. Pass the results to the view layer to generate UI components
    tx_html     = views.transaction_table_html(result["transactions"])
    bar_html    = views.bar_chart_html(result["macro_buckets"], result["sub_categories"])
    budget_html = views.budget_chart_html(result["macro_buckets"], result["total_income"])
    score_html  = views.scorecard_html(result)
    recs_md     = result["recommendations"] # Already Markdown, no view layer needed

    return tx_html, bar_html, budget_html, score_html, recs_md


# ---------------------------------------------------------
# Gradio UI Layout
# ---------------------------------------------------------
CSS = """
body, .gradio-container { background: #0a0a0f !important; }
.gr-panel, .gr-box { background: #0f0f13 !important; border-color: #1f2937 !important; }
h1 { font-family: Georgia, serif; color: #f8fafc; }
.gr-button-primary { background: #6366f1 !important; border: none !important; }
footer { display: none !important; }
"""

with gr.Blocks(css=CSS, title="💰 Financial Statement Analyzer") as demo:
    gr.HTML("""
    <div style="text-align:center;padding:32px 0 16px;font-family:'Georgia',serif;">
      <div style="font-size:2.6rem;font-weight:700;color:#f8fafc;letter-spacing:-.02em;">
        💰 Financial Statement Analyzer
      </div>
      <div style="color:#6b7280;font-size:1rem;margin-top:8px;">
        Upload your bank statement PDF · Get instant insights, budget grading &amp; your personal action plan
      </div>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=1):
            pdf_input = gr.File(label="📄 Upload Bank Statement (PDF)", file_types=[".pdf"], type="filepath")
            analyze_btn = gr.Button("🔍 Analyze Statement", variant="primary", size="lg")
            gr.HTML("""
            <div style="background:#111827;border:1px solid #1f2937;border-radius:10px;padding:14px;
                        font-family:Georgia,serif;color:#9ca3af;font-size:.82rem;margin-top:8px;">
              <strong style="color:#d1d5db;">What this analyzes:</strong><br>
              ✦ Extracts all transactions from your PDF<br>
              ✦ Classifies into 6 macro buckets + subcategories<br>
              ✦ Compares your spend against recommended budgets<br>
              ✦ Grades your income tier (7 levels)<br>
              ✦ Generates a personalized financial action plan
            </div>
            """)

    with gr.Tabs():
        with gr.TabItem("📋 Part 1 — Transactions & Categories"):
            tx_output  = gr.HTML(label="Transactions")
            bar_output = gr.HTML(label="Category Chart")

        with gr.TabItem("🎯 Part 2 — Budget vs Recommended"):
            budget_output = gr.HTML(label="Budget Comparison")

        with gr.TabItem("🏆 Part 3 — Grade & Action Plan"):
            score_output = gr.HTML(label="Scorecard")
            recs_output  = gr.Markdown(label="Personalized Recommendations")

    analyze_btn.click(
        fn=analyze_statement,
        inputs=[pdf_input],
        outputs=[tx_output, bar_output, budget_output, score_output, recs_output],
    )

if __name__ == "__main__":
    demo.launch()