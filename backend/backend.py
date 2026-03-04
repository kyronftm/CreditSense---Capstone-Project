"""
backend.py
Handles data state, PDF extraction, LLM parsing, and LangGraph workflow.
"""

import os, json, base64, textwrap
from typing import TypedDict, List, Dict
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

load_dotenv()

MACRO_BUCKETS = ["Income", "Living Expenses", "Lifestyle", "Debt", "Savings", "Investments"]

RECOMMENDED = {
    "Living Expenses": (40, 50),
    "Lifestyle":       (15, 25),
    "Debt":            (0,  10),
    "Savings":         (5,  10),
    "Investments":     (15, 20),
}

INCOME_TIERS = [
    (0,     1_000,  "Tier 1 — Survival Mode",      "🟢"),
    (1_000, 2_500,  "Tier 2 — Basic Stability",     "🟡"),
    (2_500, 3_500,  "Tier 3 — Emerging Professional","🟠"),
    (3_500, 6_000,  "Tier 4 — Solid Middle Income", "🔵"),
    (6_000, 10_000, "Tier 5 — Upper Middle",        "🟣"),
    (10_000,20_000, "Tier 6 — High Income",         "🔴"),
    (20_000,999_999,"Tier 7 — Executive / Wealth Builder","🟤"),
]

class FinancialState(TypedDict):
    pdf_base64: str
    pdf_path: str
    raw_text: str
    transactions: List[Dict]
    macro_buckets: Dict[str, float]
    sub_categories: Dict[str, float]
    total_income: float
    total_expenses: float
    income_tier: str
    tier_label: str
    recommendations: str
    budget_analysis: str


def pdf_to_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")

def _try_local_extract(path: str) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(path)
        return "\n".join(p.extract_text() or "" for p in reader.pages)
    except Exception:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        pass
    return ""

def extract_text_from_pdf(pdf_b64: str, pdf_path: str = "") -> str:
    if pdf_path:
        text = _try_local_extract(pdf_path)
        if text.strip():
            return text

    try:
        import anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            client = anthropic.Anthropic(api_key=key)
            msg = client.messages.create(
                model="claude-opus-4-5", max_tokens=4096,
                messages=[{"role": "user", "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                    {"type": "text", "text": "Extract ALL text from this bank statement. Plain text only."},
                ]}],
            )
            return msg.content[0].text
    except Exception:
        pass

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": (
            "This is a base64-encoded PDF bank statement. "
            "Extract every transaction: date, description, amount. Plain text.\n\n"
            f"BASE64:\n{pdf_b64[:12000]}"
        )}],
        max_tokens=4096,
    )
    return resp.choices[0].message.content

def classify_income_tier(monthly_income: float) -> tuple:
    for lo, hi, label, emoji in INCOME_TIERS:
        if lo <= monthly_income < hi:
            return label, emoji
    return INCOME_TIERS[-1][2], INCOME_TIERS[-1][3]

def make_graph():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    parser = StrOutputParser()

    def extract_node(state: FinancialState) -> FinancialState:
        raw = extract_text_from_pdf(state["pdf_base64"], state.get("pdf_path", ""))
        return {**state, "raw_text": raw}

    def parse_transactions_node(state: FinancialState) -> FinancialState:
        prompt = ChatPromptTemplate.from_messages([
            ("system", textwrap.dedent("""
                You are a financial data extraction expert.
                Given raw bank statement text, extract every transaction as a JSON array.
                Each object must have:
                  date (string), description (string), amount (float, always positive),
                  direction ("in" | "out"),
                  macro_bucket (one of: Income | Living Expenses | Lifestyle | Debt | Savings | Investments),
                  category (specific subcategory, e.g. Groceries / Rent / Salary / etc.),
                  fixed_variable ("fixed" | "variable"),
                  essential_optional ("essential" | "optional"),
                  recurring (true | false),
                  tax_deductible (true | false),
                  business_personal ("business" | "personal")

                Return ONLY a valid JSON array. No commentary, no markdown fences.
            """)),
            ("human", "Bank statement text:\n\n{raw_text}"),
        ])
        raw_json = (prompt | llm | parser).invoke({"raw_text": state["raw_text"]})
        raw_json = raw_json.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        try:
            transactions = json.loads(raw_json)
        except Exception:
            transactions = []
        return {**state, "transactions": transactions}

    def aggregate_node(state: FinancialState) -> FinancialState:
        macro: Dict[str, float] = {b: 0.0 for b in MACRO_BUCKETS}
        sub: Dict[str, float] = {}
        total_income = 0.0
        total_expenses = 0.0

        for t in state["transactions"]:
            bucket = t.get("macro_bucket", "Lifestyle")
            cat    = t.get("category", "Other")
            amt    = float(t.get("amount", 0))
            direction = t.get("direction", "out")

            if bucket in macro:
                macro[bucket] += amt
            sub[cat] = sub.get(cat, 0.0) + amt

            if direction == "in":
                total_income += amt
            else:
                total_expenses += amt

        tier_label, tier_emoji = classify_income_tier(total_income)
        return {
            **state,
            "macro_buckets": macro,
            "sub_categories": sub,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "income_tier": tier_emoji,
            "tier_label": tier_label,
        }

    def budget_analysis_node(state: FinancialState) -> FinancialState:
        income = state["total_income"] or 1
        actual_pct = {
            k: round(v / income * 100, 1)
            for k, v in state["macro_buckets"].items()
            if k != "Income"
        }
        lines = ["ACTUAL vs RECOMMENDED BUDGET\n"]
        for bucket, (lo, hi) in RECOMMENDED.items():
            actual = actual_pct.get(bucket, 0)
            status = "✅" if lo <= actual <= hi else ("⚠️ HIGH" if actual > hi else "⚠️ LOW")
            lines.append(f"{bucket}: {actual}%  (recommended {lo}–{hi}%)  {status}")

        return {**state, "budget_analysis": "\n".join(lines)}

    def recommendations_node(state: FinancialState) -> FinancialState:
        prompt = ChatPromptTemplate.from_messages([
            ("system", textwrap.dedent("""
                You are a world-class personal finance advisor.
                You have been given a full analysis of someone's bank statement.
                Produce a concise, actionable financial improvement plan.
                
                Structure your response exactly as:
                ## Income Tier
                State the tier, what it means, and 2-3 focused goals.
                ## Top 3 Financial Issues
                List the most critical problems found.
                ## Action Plan
                Number 8-10 specific, prioritised actions.
                ## Quick Wins (This Month)
                3 things they can do TODAY.
                
                Be direct, specific, and data-driven. Reference actual amounts where possible.
            """)),
            ("human", textwrap.dedent("""
                Income Tier: {tier_label} {income_tier}
                Total Monthly Income: ${total_income:.2f}
                Total Monthly Expenses: ${total_expenses:.2f}
                Net Cash Flow: ${net:.2f}

                Macro Bucket Breakdown:
                {macro_breakdown}

                Top Spending Sub-Categories:
                {sub_breakdown}

                Budget Analysis:
                {budget_analysis}

                Transaction count: {tx_count}
            """)),
        ])
        macro_lines = "\n".join(f"  {k}: ${v:.2f}" for k, v in state["macro_buckets"].items())
        sub_sorted = sorted(state["sub_categories"].items(), key=lambda x: x[1], reverse=True)[:10]
        sub_lines = "\n".join(f"  {k}: ${v:.2f}" for k, v in sub_sorted)

        recs = (prompt | llm | parser).invoke({
            "tier_label": state["tier_label"],
            "income_tier": state["income_tier"],
            "total_income": state["total_income"],
            "total_expenses": state["total_expenses"],
            "net": state["total_income"] - state["total_expenses"],
            "macro_breakdown": macro_lines,
            "sub_breakdown": sub_lines,
            "budget_analysis": state["budget_analysis"],
            "tx_count": len(state["transactions"]),
        })
        return {**state, "recommendations": recs}

    builder = StateGraph(FinancialState)
    builder.add_node("extract",      extract_node)
    builder.add_node("parse",        parse_transactions_node)
    builder.add_node("aggregate",    aggregate_node)
    builder.add_node("budget",       budget_analysis_node)
    builder.add_node("recommend",    recommendations_node)

    builder.set_entry_point("extract")
    builder.add_edge("extract",   "parse")
    builder.add_edge("parse",     "aggregate")
    builder.add_edge("aggregate", "budget")
    builder.add_edge("budget",    "recommend")
    builder.add_edge("recommend", END)

    return builder.compile()
    
financial_graph = make_graph()