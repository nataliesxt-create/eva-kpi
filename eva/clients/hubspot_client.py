"""
hubspot_client.py — Fetch deals from HubSpot.

Uses the HubSpot Private App token (v3 API).
Returns raw deal list; classification is done in kpi_calculations.py.
"""
from typing import Any

import requests

from eva import config

_BASE = "https://api.hubapi.com"
_HEADERS = {
    "Authorization": f"Bearer {config.HUBSPOT_PRIVATE_APP_TOKEN}",
    "Content-Type": "application/json",
}
_DEAL_PROPS = [
    "dealname",
    "dealstage",
    "amount",
    "closedate",
    "pipeline",
]


def fetchHubSpotDeals() -> list[dict[str, Any]]:
    """
    Fetch all deals from HubSpot (paginated).
    Each deal is returned as a flat dict: {id, dealname, dealstage, amount, ...}.
    Closed Lost deals are included; filtering happens downstream.
    """
    url = f"{_BASE}/crm/v3/objects/deals"
    params: dict[str, Any] = {
        "limit": 100,
        "properties": ",".join(_DEAL_PROPS),
        "archived": False,
    }
    deals: list[dict[str, Any]] = []

    while url:
        resp = requests.get(url, headers=_HEADERS, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        for result in data.get("results", []):
            props = result.get("properties", {})
            deals.append(
                {
                    "id": result.get("id"),
                    "dealname": props.get("dealname") or "",
                    "dealstage": props.get("dealstage") or "",
                    "amount": _parse_amount(props.get("amount")),
                    "closedate": props.get("closedate") or "",
                }
            )
        # Pagination
        paging = data.get("paging", {})
        next_link = paging.get("next", {}).get("link")
        if next_link:
            url = next_link
            params = {}  # link already contains params
        else:
            url = ""

    return deals


def _parse_amount(raw: Any) -> float:
    """Parse a deal amount to float; return 0.0 if missing or invalid."""
    if raw is None or raw == "":
        return 0.0
    try:
        return float(raw)
    except (ValueError, TypeError):
        return 0.0
