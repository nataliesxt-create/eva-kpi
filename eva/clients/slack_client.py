"""
slack_client.py — Thin wrapper around slack_sdk for posting to Slack.
Client is lazy-initialised to avoid module-load side effects during testing.
"""
from eva import config

_client = None


def _get_client():
    global _client
    if _client is None:
        from slack_sdk import WebClient
        _client = WebClient(token=config.SLACK_BOT_TOKEN)
    return _client


def postToSlack(text: str, channel: str | None = None) -> None:
    """
    Post a message to a Slack channel.
    Defaults to SLACK_EVA_KPI_CHANNEL_ID if no channel is provided.
    """
    from slack_sdk.errors import SlackApiError
    target = channel or config.SLACK_EVA_KPI_CHANNEL_ID
    try:
        _get_client().chat_postMessage(channel=target, text=text, mrkdwn=True)
    except SlackApiError as exc:
        print(f"[slack_client] Error posting to {target}: {exc.response['error']}")
        raise


def replyInThread(text: str, channel: str, thread_ts: str) -> None:
    """Reply to a specific message thread."""
    from slack_sdk.errors import SlackApiError
    try:
        _get_client().chat_postMessage(
            channel=channel,
            text=text,
            thread_ts=thread_ts,
            mrkdwn=True,
        )
    except SlackApiError as exc:
        print(f"[slack_client] Error replying in thread: {exc.response['error']}")
        raise
