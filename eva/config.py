"""
config.py — Eva KPI Agent configuration.
Loads environment variables. No Google Calendar. KPI-only.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Slack ────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN: str = os.environ["SLACK_BOT_TOKEN"]
SLACK_SIGNING_SECRET: str = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_EVA_KPI_CHANNEL_ID: str = os.environ["SLACK_EVA_KPI_CHANNEL_ID"]

# ── HubSpot ──────────────────────────────────────────────────────────────────
# Reads HUBSPOT_API_KEY to match the var name used by Harry and Nilo
HUBSPOT_PRIVATE_APP_TOKEN: str = os.environ.get("HUBSPOT_API_KEY") or os.environ.get("HUBSPOT_PRIVATE_APP_TOKEN", "")

# ── OpenAI ───────────────────────────────────────────────────────────────────
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

# ── Google Sheets ────────────────────────────────────────────────────────────
GOOGLE_SHEETS_CREDENTIALS: str = os.environ["GOOGLE_SHEETS_CREDENTIALS"]  # path or JSON string
EVA_KPI_SETTINGS_SHEET_ID: str = os.environ["EVA_KPI_SETTINGS_SHEET_ID"]
EVA_KPI_SETTINGS_SHEET_NAME: str = os.environ.get("EVA_KPI_SETTINGS_SHEET_NAME", "Eva KPI Settings")

# ── Timezone ─────────────────────────────────────────────────────────────────
TIMEZONE: str = "Asia/Singapore"

# ── KPI defaults ─────────────────────────────────────────────────────────────
DEFAULT_ANNUAL_TARGET: float = 100_000.0
DEFAULT_MONTHLY_TARGET: float = 8_333.0

# ── HubSpot deal stage classifications ───────────────────────────────────────
# Normalise by lowercasing before matching.
SUBMITTED_STAGES: set[str] = {
    "3407359682",  # Submitted
    "3407359683",  # Underwriting
    "3442860748",  # Accepted
}

PIPELINE_STAGES: set[str] = {
    "appointmentscheduled",    # Contacted
    "3407359681",              # Appointment Scheduled
    "decisionmakerboughtin",   # Proposal Appointment Scheduled
    "presentationscheduled",   # Opening
    "contractsent",            # Proposal Presented
}

STALLED_STAGES: set[str] = {
    "stage_0",  # To follow up / Stalled
}

CLOSED_WON_STAGE: str = "closedwon"
CLOSED_LOST_STAGE: str = "closedlost"
