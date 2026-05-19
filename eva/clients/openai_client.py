"""
openai_client.py — OpenAI integration for Eva KPI strategy suggestions.

OpenAI is used ONLY for interpretation and strategy suggestions.
All KPI calculations happen in kpi_calculations.py.
"""
from __future__ import annotations
from typing import TYPE_CHECKING

from eva import config

_client = None


def _get_client():
    """Lazy-initialize the OpenAI client to avoid module-load side effects."""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=config.OPENAI_API_KEY)
    return _client


_SYSTEM_PROMPT = """You are Eva, a sharp and precise KPI strategy advisor for Natalie Tan, 
a financial advisor in Singapore. 

Your role:
- Interpret KPI numbers honestly
- Give practical, specific strategy suggestions for a financial advisor
- Never invent fake clients, fake deal amounts, fake meetings, or fake activities
- Never use generic motivational fluff
- Keep language professional and direct

Rules:
- Do not mention Google Calendar, appointments, or any calendar data
- Base all commentary only on the actual numbers provided
- Strategy must be specific to financial advisory work in Singapore
"""


def generateEvaReportWithOpenAI(report_type: str, kpi_input: str) -> str:
    """
    Generate Eva's narrative read and strategy suggestions via OpenAI.

    report_type: "daily" | "weekly" | "monthly"
    kpi_input  : formatted string of KPI data prepared by report_builder.py
    Returns    : the AI-generated text block
    """
    user_prompt = _build_user_prompt(report_type, kpi_input)

    response = _get_client().chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=600,
    )
    return response.choices[0].message.content.strip()


def _build_user_prompt(report_type: str, kpi_input: str) -> str:
    if report_type == "daily":
        return f"""Here is today's KPI data for Natalie:

{kpi_input}

Write two sections using Slack bold formatting (single asterisk, not double):

🧠 *Eva's read*
One short paragraph (2-3 sentences) explaining what these numbers mean today.
Be honest about pace. Reference the specific numbers. Do not be vague.

──────────────────────
🎯 *Today's move*

Structure it exactly as follows:

📌 *Daily target:* $[weekly needed ÷ 5] — state whether Natalie is behind, on pace, or ahead based on submitted commission vs weekly needed.

Then a checklist using ☐ bullets:
☐ [Specific action on the active pipeline — name the deal stage to push e.g. Proposal Presented → submission]
☐ [Follow up on the stalled case(s) — reference the count and dollar amount, say to send a message today]
☐ [One new business action — specific e.g. book X discovery calls or reach out to X cold leads]
☐ By EOD: [one concrete end-of-day commitment]

──────────────────────
🎯 *To reach $100,000:*
Give 2-3 numbered actionable steps for this week. No vague language ("revisit strategy", "enhance conversion", "adjusted approach"). Real executable actions only, with specific numbers.
"""
    elif report_type == "weekly":
        return f"""Here is this week's KPI data for Natalie:

{kpi_input}

Write two sections using Slack bold formatting (single asterisk, not double):

🧠 *Eva's weekly read*
One concise paragraph (3-4 sentences) about weekly pace, bottlenecks,
and what needs movement. Reference specific numbers. Be direct.

💡 *Strategy suggestions*
Exactly 3 bullet points focused on closing the shortfall gap this week.
Each suggestion must:
- Be directly tied to the shortfall or weekly needed figure
- Name a specific action (e.g. follow up on stalled cases, convert pipeline to submitted, book X appointments)
- Be actionable for a financial advisor in Singapore, not generic advice
Format: • [suggestion]
"""
    elif report_type == "monthly":
        return f"""Here is this month's KPI data for Natalie:

{kpi_input}

Write two sections using Slack bold formatting (single asterisk, not double):

🧠 *Eva's monthly read*
One thoughtful but concise paragraph (3-5 sentences).
This should feel like a real business review. Reference the numbers.
Be honest about whether this is a good or concerning month.

🗺️ *Next month's strategy*
Exactly 3 bullet points focused on closing the remaining shortfall next month.
Structure:
- One suggestion on converting existing pipeline deals to submitted (reference the pipeline commission figure)
- One suggestion on clearing or recovering stalled cases (reference stalled count/amount)
- One suggestion on new business activity needed to hit the monthly needed figure
Each must reference the actual numbers. No generic advice.
Format: • [suggestion]
"""
    else:
        return f"KPI data:\n{kpi_input}\n\nProvide a brief analysis and 3 practical strategy suggestions."
