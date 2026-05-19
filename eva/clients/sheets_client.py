"""
sheets_client.py — Google Sheets persistence for Eva KPI Settings.

Sheet name: "Eva KPI Settings"
Columns   : key | value | updated_at
Rows      : current_ytd | annual_target | monthly_target
"""
import json
import os
from datetime import datetime, timezone
from typing import Any

import gspread
from google.oauth2.service_account import Credentials

from eva import config


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]


def _get_client() -> gspread.Client:
    """Return an authenticated gspread client."""
    creds_val = config.GOOGLE_SHEETS_CREDENTIALS
    # Accept either a file path or a raw JSON string
    if os.path.isfile(creds_val):
        creds = Credentials.from_service_account_file(creds_val, scopes=_SCOPES)
    else:
        info = json.loads(creds_val)
        creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    return gspread.authorize(creds)


def _get_sheet() -> gspread.Worksheet:
    client = _get_client()
    spreadsheet = client.open_by_key(config.EVA_KPI_SETTINGS_SHEET_ID)
    return spreadsheet.worksheet(config.EVA_KPI_SETTINGS_SHEET_NAME)


def fetchKpiSettings() -> dict[str, Any]:
    """
    Read Eva KPI Settings from Google Sheet.
    Returns a dict with keys: current_ytd, annual_target, monthly_target.
    Falls back to defaults if a row is missing.

    Uses raw row matching so it works whether or not the sheet has a header row.
    """
    defaults: dict[str, Any] = {
        "annual_target": config.DEFAULT_ANNUAL_TARGET,
        "monthly_target": config.DEFAULT_MONTHLY_TARGET,
        "current_ytd": None,  # None means no manual YTD has been saved yet
    }
    try:
        sheet = _get_sheet()
        rows = sheet.get_all_values()  # raw list of rows, no header assumption
        for row in rows:
            if len(row) < 2:
                continue
            k = str(row[0]).strip()
            v = str(row[1]).strip()
            if k in defaults and v:
                try:
                    defaults[k] = float(v)
                except (ValueError, TypeError):
                    pass
    except Exception as exc:  # noqa: BLE001
        print(f"[sheets_client] Warning: could not fetch KPI settings — falling back to defaults. Error: {exc}")
    else:
        print(f"[sheets_client] KPI settings loaded: {defaults}")
    return defaults


def updateKpiSetting(key: str, value: float) -> None:
    """
    Upsert a single KPI setting row in the sheet.
    Writes: key | value | updated_at (ISO 8601 UTC)

    Uses raw row matching so it works whether or not the sheet has a header row.
    """
    now_str = datetime.now(timezone.utc).isoformat()
    sheet = _get_sheet()
    rows = sheet.get_all_values()
    # Find existing row by key (1-based index)
    for i, row in enumerate(rows, start=1):
        if len(row) > 0 and str(row[0]).strip() == key:
            sheet.update(f"A{i}:C{i}", [[key, str(value), now_str]])
            print(f"[sheets_client] Updated row {i}: {key} = {value}")
            return
    # Key not found — append a new row
    sheet.append_row([key, str(value), now_str])
    print(f"[sheets_client] Appended new row: {key} = {value}")


def updateCurrentYtd(amount: float) -> None:
    """Persist the new YTD value. This is the source of truth for all reports."""
    updateKpiSetting("current_ytd", amount)
