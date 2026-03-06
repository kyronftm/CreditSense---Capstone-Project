"""
Recommendation Node — Sixth node in the CreditSense LangGraph pipeline.

Responsibilities:
  1. Take structured data, credit tier, bureau, and the generated summary.
  2. Send to Claude Sonnet to produce prioritized, actionable recommendations.
  3. Return a list of recommendations with expected impact and timeframe.

Model: Claude Sonnet 4 (strong reasoning for personalized financial guidance).
"""

import json
import os
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import CreditSenseState

load_dotenv()

RECOMMENDATION_SYSTEM_PROMPT = """You are a credit improvement advisor generating personalized, actionable recommendations for a US consumer based on their credit report data and summary.

GUIDELINES:
- Provide 3-5 specific recommendations, ordered by expected impact on their credit score (highest impact first).
- Each recommendation MUST include:
  1. **Action**: A clear, specific action the consumer can take (not vague advice).
  2. **Reason**: Why this matters and how it connects to their specific credit data.
  3. **Expected Impact**: Estimated score improvement (e.g., "15-30 points") or qualitative impact (e.g., "High", "Medium", "Low").
  4. **Timeframe**: How long before the effect shows on their report (e.g., "1-2 billing cycles", "6-12 months").
  5. **Priority**: "High", "Medium", or "Low".

RULES:
- Base all recommendations on the ACTUAL data provided. Do not make generic suggestions that don't relate to their specific situation.
- Be specific with numbers: if their utilization is 59%, say "Reduce your total balances from $13,650 to below $6,900 (30% of your $23,000 limit)."
- Never recommend closing old accounts (it hurts average account age and total credit limit).
- Never recommend applying for new credit if they already have too many recent inquiries.
- Consider the interplay between factors (e.g., paying down debt improves utilization AND may offset the late payment impact).

OUTPUT FORMAT:
Return a valid JSON array of recommendation objects. Each object must have these fields:
{
  "action": "string — specific action to take",
  "reason": "string — why this matters for their specific situation",
  "expected_impact": "string — estimated score improvement or impact level",
  "timeframe": "string — when they can expect to see results",
  "priority": "string — High, Medium, or Low"
}

Return ONLY the JSON array. No markdown, no code fences, no explanation.

IMPORTANT:
- These recommendations are EDUCATIONAL in nature. A financial advice disclaimer will be added separately.
- Do NOT include any disclaimer text in the recommendations themselves."""


def recommendation_node(state: CreditSenseState) -> CreditSenseState:
    """
    Generates personalized credit improvement recommendations using Claude Sonnet.

    Args:
        state: Pipeline state with 'structured_data', 'credit_tier', 'bureau', and 'summary'.

    Returns:
        Updated state with 'recommendations' list or 'error'.
    """

    # --- Guard: check for structured data ---
    structured_data = state.get("structured_data")
    if not structured_data:
        return {
            "error": "Recommendation generation skipped: no structured data available.",
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
            temperature=0.2,  # Low creativity for precise recommendations
            max_tokens=2048,
        )

        # --- Build context ---
        bureau = state.get("bureau", "unknown")
        credit_tier = state.get("credit_tier", "unknown")
        summary = state.get("summary", "No summary available.")

        # --- Build messages (with optional RAG context) ---
        rag_context = state.get("rag_context_recommendation", "")
        rag_section = ""
        if rag_context:
            rag_section = (
                f"US credit regulations, official improvement strategies, and consumer protections:\n"
                f"{rag_context}\n\n---\n\n"
            )

        messages = [
            SystemMessage(content=RECOMMENDATION_SYSTEM_PROMPT),
            HumanMessage(content=(
                f"{rag_section}"
                f"Generate personalized credit improvement recommendations based on:\n\n"
                f"Credit Bureau: {bureau.title()}\n"
                f"Credit Tier: {credit_tier.replace('_', ' ').title()}\n\n"
                f"Credit Health Summary:\n{summary}\n\n"
                f"Structured Credit Report Data:\n{json.dumps(structured_data, indent=2)}"
            )),
        ]

        # --- Call the LLM ---
        response = llm.invoke(messages)
        response_text = response.content.strip()

        # --- Clean response (remove code fences if present) ---
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            response_text = "\n".join(lines)

        # --- Parse JSON array ---
        try:
            recommendations = json.loads(response_text)
        except json.JSONDecodeError as e:
            return {
                "error": f"Failed to parse recommendations as JSON: {str(e)}. Response: {response_text[:500]}",
            }

        # --- Validate structure ---
        if not isinstance(recommendations, list):
            return {
                "error": "Recommendations response is not a JSON array.",
            }

        required_fields = {"action", "reason", "expected_impact", "timeframe", "priority"}
        for i, rec in enumerate(recommendations):
            if not isinstance(rec, dict):
                return {
                    "error": f"Recommendation {i} is not a JSON object.",
                }
            missing = required_fields - set(rec.keys())
            if missing:
                return {
                    "error": f"Recommendation {i} is missing fields: {missing}",
                }

        if len(recommendations) == 0:
            return {
                "error": "No recommendations were generated.",
            }

        return {
            "recommendations": recommendations,
        }

    except Exception as e:
        return {
            "error": f"Error during recommendation generation: {str(e)}",
        }
