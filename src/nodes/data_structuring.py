"""
Data Structuring Node — Third node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Take the raw extracted text from the Text Extraction Node.
  2. Send it to Claude Haiku with a structured extraction prompt.
  3. Parse the LLM response into a validated CreditReportData schema.
  4. Return the structured data in the pipeline state.

Model: Claude 3.5 Haiku (fast, cost-effective for extraction tasks).
"""

import json
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import CreditSenseState
from src.schemas import CreditReportData

# Load environment variables
load_dotenv()

# System prompt for structured data extraction
EXTRACTION_SYSTEM_PROMPT = """You are a credit report data extraction specialist. Your job is to extract structured data from raw credit report text.

IMPORTANT RULES:
- Extract ONLY information that is explicitly present in the text. Do NOT infer or fabricate data.
- For monetary values, extract as numbers without currency symbols (e.g., 8500 not "$8,500").
- For masked account numbers, extract only the last 4 digits shown (e.g., "4521").
- For dates, preserve the format as shown in the report.
- If a field is not found in the text, use null.
- For public_records and collections, use empty lists if none are found (e.g., "No public records found" means []).
- Pay close attention to payment statuses — distinguish between "Current" and any late payments.

You MUST return a valid JSON object matching this exact schema:

{
  "report_bureau": "string or null — credit bureau name (Experian, TransUnion, Equifax)",
  "report_date": "string or null — date of the report",
  "report_number": "string or null — report reference number",
  "personal_info": {
    "full_name": "string — full name",
    "date_of_birth": "string or null",
    "current_address": "string or null — full current address",
    "previous_address": "string or null — full previous address",
    "employer": "string or null",
    "ssn_last_four": "string or null — last 4 digits only"
  },
  "credit_score": {
    "score": integer (300-850),
    "score_model": "string or null — e.g., FICO Score 8",
    "score_range": "string or null — e.g., 300-850",
    "risk_level": "string or null — e.g., Fair",
    "score_date": "string or null",
    "key_factors": ["list of strings — key factors affecting the score"]
  },
  "accounts": [
    {
      "account_name": "string — creditor name",
      "account_number_masked": "string or null — last 4 digits",
      "account_type": "string — e.g., Revolving Credit Card",
      "date_opened": "string or null",
      "credit_limit": number or null (in USD, no symbols),
      "current_balance": number or null,
      "monthly_payment": number or null,
      "payment_status": "string — e.g., Current - Paid as Agreed, 30 Days Late",
      "high_balance": number or null,
      "account_status": "string — e.g., Open / Current, Closed by Consumer",
      "date_closed": "string or null",
      "last_reported": "string or null"
    }
  ],
  "inquiries": [
    {
      "date": "string — inquiry date",
      "creditor": "string — creditor name",
      "inquiry_type": "string — e.g., Credit Card"
    }
  ],
  "public_records": [],
  "collections": [],
  "account_summary": {
    "total_accounts": integer,
    "open_accounts": integer,
    "closed_accounts": integer,
    "total_balance": number,
    "total_credit_limit": number,
    "overall_utilization": number (0-100, percentage),
    "oldest_account_date": "string or null",
    "average_account_age": "string or null",
    "on_time_payment_percentage": number or null (0-100),
    "total_late_payments": integer,
    "hard_inquiries_count": integer
  }
}

Return ONLY the JSON object. No markdown, no code fences, no explanation."""


def data_structuring_node(state: CreditSenseState) -> CreditSenseState:
    """
    Structures raw credit report text into a validated schema using Claude Haiku.

    Args:
        state: Pipeline state with 'raw_text' from the extraction node.

    Returns:
        Updated state with 'structured_data' dict or 'error'.
    """

    # --- Guard: check for raw text ---
    raw_text = state.get("raw_text", "")
    if not raw_text.strip():
        return {
            "error": "Data structuring skipped: no extracted text available.",
        }

    # --- Guard: check for prior errors ---
    if state.get("error"):
        return {"error": state["error"]}

    # --- Initialize the LLM ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        return {
            "error": (
                "ANTHROPIC_API_KEY is not configured. "
                "Please set it in the .env file."
            ),
        }

    try:
        llm = ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=api_key,
            temperature=0,
            max_tokens=4096,
        )

        # --- Build the messages (with optional RAG context) ---
        rag_context = state.get("rag_context_structuring", "")
        if rag_context:
            human_content = (
                f"Relevant US credit reporting regulations and standards:\n"
                f"{rag_context}\n\n"
                f"---\n\n"
                f"Extract structured data from this credit report:\n\n{raw_text}"
            )
        else:
            human_content = f"Extract structured data from this credit report:\n\n{raw_text}"

        messages = [
            SystemMessage(content=EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=human_content),
        ]

        # --- Call the LLM ---
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # --- Clean response (remove code fences if present) ---
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            # Remove first and last lines (code fences)
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)

        # --- Parse JSON ---
        try:
            parsed_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse LLM response as JSON: {str(e)}. Response: {response_text[:500]}",
            }

        # --- Validate with Pydantic schema ---
        try:
            validated = CreditReportData(**parsed_data)
            structured_dict = validated.model_dump()
        except Exception as e:
            return {
                "error": f"LLM output failed schema validation: {str(e)}",
            }

        return {
            "structured_data": structured_dict,
        }

    except Exception as e:
        return {
            "error": f"Error during data structuring: {str(e)}",
        }
