"""
ytd_listener.py — Slack YTD command handler.

Listens for messages starting with "YTD" in #eva-kpi.
Parses the amount, validates it, persists it, and replies with
an LLM-generated confirmation.
If invalid, replies:
  "I couldn't read the YTD amount. Please use format: YTD 2435.97"
"""
import re
from typing import Optional

from eva.clients import sheets_client

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
    return f"✅ YTD locked in at ${amount:,.2f} — you're at the start of the climb, Natalie. Let's move those pipeline deals. 💪"
