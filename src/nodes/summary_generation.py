"""
Summary Generation Node — Fifth node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Take the structured credit report data, bureau, and credit tier.
  2. Send it to Claude Sonnet with a summary generation prompt.
  3. Return a clear, plain-language credit health summary.

Model: Claude Sonnet 4 (strong reasoning for nuanced financial analysis).
"""

import json
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import CreditSenseState

load_dotenv()

SUMMARY_SYSTEM_PROMPT = """You are a credit health analyst writing a plain-language summary for a US consumer. Your job is to take structured credit report data and produce a clear, helpful summary that any adult can understand.

GUIDELINES:
- Write in second person ("Your credit score is...", "You have...").
- Use plain language — avoid financial jargon. When you must use a term (e.g., "credit utilization"), briefly explain it.
- Be factual and neutral in tone — do not be alarmist or overly optimistic.
- Structure the summary with these sections:
  1. **Credit Score Overview**: State the score, what tier it falls into, and what that means practically (e.g., loan eligibility, typical interest rates).
  2. **Key Strengths**: Identify 1-3 positive aspects of the credit profile.
  3. **Areas of Concern**: Identify the top 2-4 factors dragging the score down, ordered by impact.
  4. **Account Snapshot**: Brief overview of account composition (how many open/closed, types, total debt vs. available credit).
  5. **Recent Activity**: Note any recent inquiries or changes worth mentioning.

FORMATTING:
- Use markdown formatting with ## headers for each section.
- Keep the total summary between 300-500 words.
- Use bullet points for strengths and concerns.
- Include specific numbers from the data (scores, percentages, dollar amounts).

IMPORTANT:
- Only reference data that exists in the provided structured data. Do NOT fabricate any numbers or details.
- Do NOT provide recommendations or advice in this summary — that comes in the next step.
- End with a single-sentence overall assessment.

DISCLAIMER:
- Do NOT include any financial advice disclaimer in the summary itself (it will be added in the output formatting step)."""


def summary_generation_node(state: CreditSenseState) -> CreditSenseState:
    """
    Generates a plain-language credit health summary using Claude Sonnet.

    Args:
        state: Pipeline state with 'structured_data', 'bureau', and 'credit_tier'.

    Returns:
        Updated state with 'summary' or 'error'.
    """

    # --- Guard: check for structured data ---
    structured_data = state.get("structured_data")
    if not structured_data:
        return {
            "error": "Summary generation skipped: no structured data available.",
        }

    # --- Guard: check for prior errors ---
    if state.get("error"):
        return {"error": state["error"]}

    # --- Initialize the LLM ---
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        return {
            "error": "ANTHROPIC_API_KEY is not configured. Please set it in the .env file.",
        }

    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=api_key,
            temperature=0.3,  # Slight creativity for natural language
            max_tokens=2048,
        )

        # --- Build context for the LLM ---
        bureau = state.get("bureau", "unknown")
        credit_tier = state.get("credit_tier", "unknown")

        context = {
            "bureau": bureau,
            "credit_tier": credit_tier,
            "structured_data": structured_data,
        }

        # --- Build messages (with optional RAG context) ---
        rag_context = state.get("rag_context_summary", "")
        rag_section = ""
        if rag_context:
            rag_section = (
                f"Official US credit guidelines and regulations for reference:\n"
                f"{rag_context}\n\n---\n\n"
            )

        messages = [
            SystemMessage(content=SUMMARY_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"{rag_section}"
                f"Generate a credit health summary for this consumer based on the following data.\n\n"
                f"Credit Bureau: {bureau.title()}\n"
                f"Credit Tier: {credit_tier.replace('_', ' ').title()}\n\n"
                f"Structured Credit Report Data:\n{json.dumps(structured_data, indent=2)}"
            )),
        ]

        # --- Call the LLM ---
        response = llm.invoke(messages)
        summary = response.content.strip()

        if not summary:
            return {
                "error": "Summary generation returned an empty response.",
            }

        return {
            "summary": summary,
        }

    except Exception as e:
        return {
            "error": f"Error during summary generation: {str(e)}",
        }
