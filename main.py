"""
main.py — Eva KPI Agent entry point.

Starts:
  1. Slack Bolt app (Socket Mode) — listens for YTD messages in #eva-kpi
  2. APScheduler — posts daily/weekly/monthly reports on schedule
"""
import os
import re

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from eva import config
from eva import ytd_listener
from eva.clients import slack_client
from eva.scheduler import create_scheduler

# ── Slack Bolt app ────────────────────────────────────────────────────────────
app = App(
    token=config.SLACK_BOT_TOKEN,
    signing_secret=config.SLACK_SIGNING_SECRET or None,
)

_YTD_PREFIX = re.compile(r"^ytd\s+", re.IGNORECASE)


@app.message(_YTD_PREFIX)
def handle_ytd_message(message, say, logger):
    """
    Listen for messages starting with 'YTD' in any channel Eva is in.
    Only process messages from #eva-kpi.
    """
    channel = message.get("channel", "")
    print(f"[Eva] YTD handler fired — channel={channel}", flush=True)
    if channel != config.SLACK_EVA_KPI_CHANNEL_ID:
        return  # Ignore other channels

    text = message.get("text", "")
    thread_ts = message.get("ts")

    print(f"[Eva] YTD message received: {text!r}", flush=True)
    reply = ytd_listener.handleYtdMessage(text)

    # Reply in thread so the channel stays clean
    try:
        slack_client.replyInThread(reply, channel=channel, thread_ts=thread_ts)
    except Exception as exc:
        logger.error(f"[Eva] Failed to reply to YTD message: {exc}")


@app.message(re.compile(r"eva.*update\s+(daily|weekly|monthly)", re.IGNORECASE))
def handle_eva_commands(message, say):
    if message.get("channel") != config.SLACK_EVA_KPI_CHANNEL_ID:
        return
    if message.get("bot_id") or message.get("subtype"):
        return

    text = message.get("text", "").lower()
    print(f"[Eva] Command received: {text!r}", flush=True)

    try:
        if "daily" in text:
            say("📊 Running Daily KPI report...")
            from eva.kpi_agent import run_daily_kpi
            run_daily_kpi()
            print("[Eva] Daily KPI posted.", flush=True)
        elif "weekly" in text:
            say("📊 Running Weekly KPI report...")
            from eva.kpi_agent import run_weekly_review
            run_weekly_review()
            print("[Eva] Weekly review posted.", flush=True)
        elif "monthly" in text:
            say("📊 Running Monthly KPI report...")
            from eva.kpi_agent import run_monthly_review
            run_monthly_review(force=True)
            print("[Eva] Monthly review posted.", flush=True)
    except Exception as e:
        print(f"[Eva] ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()


@app.event({"type": "message", "subtype": "message_changed"})
def handle_message_changed(body):
    pass


@app.event({"type": "message", "subtype": "message_deleted"})
def handle_message_deleted(body):
    pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start the scheduler in the background
    scheduler = create_scheduler()
    scheduler.start()
    print("[Eva] Scheduler started.")

    # Start Slack Socket Mode handler (requires SLACK_APP_TOKEN env var)
    slack_app_token = os.environ.get("SLACK_APP_TOKEN")
    if not slack_app_token:
        raise EnvironmentError(
            "SLACK_APP_TOKEN is required for Socket Mode. "
            "Set it in your .env file."
        )

    print("[Eva] Starting Slack Socket Mode listener...")
    handler = SocketModeHandler(app, slack_app_token)
    handler.start()  # Blocks until interrupted
