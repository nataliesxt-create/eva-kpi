"""
test_ytd_parser.py — Tests for parseYtdCommand and handleYtdMessage.

Covers all required scenarios:
  - YTD 2435.97
  - YTD $2,435.97
  - YTD 10000
  - YTD abc (invalid)
  - Negative YTD rejection
  - Exact acknowledgement: "Updated YTD received"
  - Eva does not interact with Google Calendar
"""
import pytest
from unittest.mock import patch, MagicMock

from eva.ytd_listener import (
    parseYtdCommand,
    handleYtdMessage,
    SUCCESS_REPLY,
    ERROR_REPLY,
)


# ─────────────────────────────────────────────────────────────────────────────
# parseYtdCommand — valid inputs
# ─────────────────────────────────────────────────────────────────────────────

class TestParseYtdCommandValid:
    def test_plain_number(self):
        assert parseYtdCommand("YTD 2435.97") == pytest.approx(2435.97)

    def test_dollar_with_commas(self):
        assert parseYtdCommand("YTD $2,435.97") == pytest.approx(2435.97)

    def test_integer(self):
        assert parseYtdCommand("YTD 10000") == pytest.approx(10000.0)

    def test_lowercase(self):
        assert parseYtdCommand("ytd 5000") == pytest.approx(5000.0)

    def test_mixed_case(self):
        assert parseYtdCommand("Ytd 1234.56") == pytest.approx(1234.56)

    def test_zero(self):
        assert parseYtdCommand("YTD 0") == pytest.approx(0.0)

    def test_large_amount_with_commas(self):
        assert parseYtdCommand("YTD $100,000.00") == pytest.approx(100000.0)

    def test_extra_whitespace(self):
        # Leading/trailing space should still parse
        assert parseYtdCommand("  YTD 2435.97  ") == pytest.approx(2435.97)


# ─────────────────────────────────────────────────────────────────────────────
# parseYtdCommand — invalid / rejected inputs
# ─────────────────────────────────────────────────────────────────────────────

class TestParseYtdCommandInvalid:
    def test_text_amount_returns_none(self):
        assert parseYtdCommand("YTD abc") is None

    def test_missing_amount_returns_none(self):
        assert parseYtdCommand("YTD") is None

    def test_empty_string_returns_none(self):
        assert parseYtdCommand("") is None

    def test_none_returns_none(self):
        assert parseYtdCommand(None) is None

    def test_negative_value_rejected(self):
        assert parseYtdCommand("YTD -500") is None

    def test_negative_with_dollar_rejected(self):
        assert parseYtdCommand("YTD $-500") is None

    def test_unrelated_message_returns_none(self):
        assert parseYtdCommand("Hello Eva") is None

    def test_partial_prefix_returns_none(self):
        assert parseYtdCommand("YT 1000") is None

    def test_amount_before_ytd_returns_none(self):
        assert parseYtdCommand("2435.97 YTD") is None


# ─────────────────────────────────────────────────────────────────────────────
# handleYtdMessage — success path
# ─────────────────────────────────────────────────────────────────────────────

class TestHandleYtdMessageSuccess:
    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_returns_exact_success_reply(self, mock_update):
        reply = handleYtdMessage("YTD 2435.97")
        assert reply == "Updated YTD received"

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_calls_update_with_correct_value(self, mock_update):
        handleYtdMessage("YTD 2435.97")
        mock_update.assert_called_once_with(pytest.approx(2435.97))

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_dollar_comma_format_saves_correctly(self, mock_update):
        reply = handleYtdMessage("YTD $2,435.97")
        assert reply == SUCCESS_REPLY
        mock_update.assert_called_once_with(pytest.approx(2435.97))

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_no_extra_text_in_success_reply(self, mock_update):
        reply = handleYtdMessage("YTD 10000")
        # Must be exactly this string — no emoji, no extra words
        assert reply == "Updated YTD received"
        assert "emoji" not in reply.lower()

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_reply_only_after_save(self, mock_update):
        """Verify update is called before we get the reply."""
        call_order = []
        mock_update.side_effect = lambda v: call_order.append("saved")
        reply = handleYtdMessage("YTD 5000")
        assert call_order == ["saved"]
        assert reply == SUCCESS_REPLY


# ─────────────────────────────────────────────────────────────────────────────
# handleYtdMessage — error path
# ─────────────────────────────────────────────────────────────────────────────

class TestHandleYtdMessageError:
    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_invalid_returns_error_reply(self, mock_update):
        reply = handleYtdMessage("YTD abc")
        assert reply == ERROR_REPLY
        mock_update.assert_not_called()

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_negative_returns_error_reply(self, mock_update):
        reply = handleYtdMessage("YTD -500")
        assert reply == ERROR_REPLY
        mock_update.assert_not_called()

    @patch("eva.ytd_listener.sheets_client.updateCurrentYtd")
    def test_error_reply_contains_format_hint(self, mock_update):
        reply = handleYtdMessage("YTD ???")
        assert "YTD 2435.97" in reply


# ─────────────────────────────────────────────────────────────────────────────
# Eva does not touch Google Calendar
# ─────────────────────────────────────────────────────────────────────────────

class TestNoGoogleCalendar:
    def test_ytd_listener_has_no_calendar_import(self):
        import eva.ytd_listener as module
        import inspect
        source = inspect.getsource(module)
        assert "google.calendar" not in source
        assert "googleapiclient" not in source
        assert "calendar_client" not in source
