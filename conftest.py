"""
conftest.py — Set fake environment variables before any Eva module is imported.
This prevents config.py from raising KeyError during test collection.
"""
import os

# Fake credentials — never real values, never committed
_FAKE_ENV = {
    "SLACK_BOT_TOKEN": "xoxb-test-token",
    "SLACK_APP_TOKEN": "xapp-test-token",
    "SLACK_SIGNING_SECRET": "test-signing-secret",
    "SLACK_EVA_KPI_CHANNEL_ID": "C0123TEST",
    "HUBSPOT_PRIVATE_APP_TOKEN": "pat-test-123",
    "OPENAI_API_KEY": "sk-test-key",
    "GOOGLE_SHEETS_CREDENTIALS": '{"type":"service_account"}',
    "EVA_KPI_SETTINGS_SHEET_ID": "test-sheet-id",
}

for k, v in _FAKE_ENV.items():
    os.environ.setdefault(k, v)
