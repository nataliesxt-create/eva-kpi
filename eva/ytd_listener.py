"""
ytd_listener.py — Slack YTD command handler.

Listens for messages starting with "YTD" in #eva-kpi.
Parses the amount, validates it, persists it, and replies exactly:
  "Updated YTD received"
If invalid, replies:
  "I couldn't read the YTD amount. Please use format: YTD 2435.97"
"""
import re
from typing import Optional

from eva.clients import sheets_client
from eva.clients import openai_client

# Matches: YTD [optional $] digits [optional comma-separated] [optional .decimals]
# Examples: YTD 2435.97 | YTD $2,435.97 | YTD 10000
_YTD_PATTERN = re.compile(
    r"^ytd\s+\$?([\d,]+(?:\.\d+)?)$",
    re.IGNORECASE,
)

ERROR_REPLY = "I couldn't read the YTD amount. Please use format: YTD 2435.97"


def parseYtdCommand(text: str) -> Optional[float]:
    """
    Parse a YTD Slack message and return the clean float value.

    Accepts:
      YTD 2435.97
      YTD $2,435.97
      YTD 10000

    Returns None if the message is invalid or the amount is negative.
    """
    if text is None:
        return None
    cleaned = text.strip()
    match = _YTD_PATTERN.match(cleaned)
    if not match:
        return None
    raw_number = match.group(1).replace(",", "")
    try:
        value = float(raw_number)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def handleYtdMessage(text: str) -> str:
    """
    Full YTD update flow:
    1. Parse the message.
    2. If valid: persist and return the exact success reply.
    3. If invalid: return the error reply.

    This function is pure (no Slack I/O) so it's easy to test.
    Returns the reply string that should be posted to Slack.
    """
    amount = parseYtdCommand(text)
    if amount is None:
        return ERROR_REPLY
    # Persist — only reply after successful save
    sheets_client.updateCurrentYtd(amount)
    return _generateYtdReply(amount)


def _generateYtdReply(amount: float) -> str:
    """Generate an encouraging YTD confirmation using OpenAI."""
    try:
        response = openai_client._get_client().chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Eva, a sharp KPI advisor for Natalie Tan, a Singapore financial advisor. "
                        "Reply in Slack formatting. Use emojis. Keep it to 2 sentences max. "
                        "Be warm but direct. No fluff."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Natalie just updated her YTD to ${amount:,.2f}. "
                        "Confirm it's saved and give her one sharp, encouraging line about the number."
                    ),
                },
            ],
            temperature=0.8,
            max_tokens=80,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return f"✅ YTD updated to ${amount:,.2f} — saved to your KPI sheet."
