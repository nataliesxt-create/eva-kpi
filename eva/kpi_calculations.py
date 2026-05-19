"""
kpi_calculations.py — All KPI math. No OpenAI here.

Uses Asia/Singapore timezone for all date calculations.
"""
import math
from datetime import date, datetime
from typing import Any

from zoneinfo import ZoneInfo

from eva import config

SGT = ZoneInfo(config.TIMEZONE)


# ─────────────────────────────────────────────────────────────────────────────
# Deal classification
# ─────────────────────────────────────────────────────────────────────────────

def _normalise_stage(stage: str) -> str:
    """Lowercase and strip the stage label for comparison."""
    return stage.lower().strip()


def classifyDealsByStage(deals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Classify HubSpot deals into buckets.

    Returns:
    {
        "submitted": [...],   # Submitted / Accepted / Underwriting
        "pipeline":  [...],   # Active pipeline stages
        "stalled":   [...],   # To Follow Up / Stalled
        "closed_won": [...],  # Closed Won (used only when no manual YTD)
        "closed_lost": [...], # Excluded from KPI calculations
    }
    """
    result: dict[str, list[dict[str, Any]]] = {
        "submitted": [],
        "pipeline": [],
        "stalled": [],
        "closed_won": [],
        "closed_lost": [],
    }
    for deal in deals:
        stage = _normalise_stage(deal.get("dealstage", ""))
        if stage in config.SUBMITTED_STAGES:
            result["submitted"].append(deal)
        elif stage in config.PIPELINE_STAGES:
            result["pipeline"].append(deal)
        elif stage in config.STALLED_STAGES:
            result["stalled"].append(deal)
        elif stage == config.CLOSED_WON_STAGE:
            result["closed_won"].append(deal)
        elif stage == config.CLOSED_LOST_STAGE:
            result["closed_lost"].append(deal)
        # Unknown stages are silently ignored
    return result


def _sum_amounts(deals: list[dict[str, Any]]) -> float:
    return sum(d.get("amount", 0.0) for d in deals)


# ─────────────────────────────────────────────────────────────────────────────
# Time helpers (Singapore timezone)
# ─────────────────────────────────────────────────────────────────────────────

def _today_sgt() -> date:
    return datetime.now(SGT).date()


def _remaining_weeks_in_year(today: date | None = None) -> float:
    """
    Remaining ISO weeks from today (inclusive) to end of year.
    Uses a simple day-based calculation: remaining_days / 7.
    Returns at least 1 to avoid division by zero.
    """
    d = today or _today_sgt()
    year_end = date(d.year, 12, 31)
    remaining_days = (year_end - d).days + 1
    weeks = remaining_days / 7.0
    return max(weeks, 1.0)


def _remaining_months_in_year(today: date | None = None) -> float:
    """
    Remaining calendar months from the current month (inclusive) to December.
    Returns at least 1 to avoid division by zero.
    """
    d = today or _today_sgt()
    remaining = 13 - d.month  # e.g., January → 12, December → 1
    return max(float(remaining), 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# Core KPI calculations
# ─────────────────────────────────────────────────────────────────────────────

def calculateKpiMetrics(
    settings: dict[str, Any],
    classified_deals: dict[str, list[dict[str, Any]]],
    today: date | None = None,
) -> dict[str, Any]:
    """
    Compute all KPI metrics from settings and classified deals.

    settings keys expected: current_ytd, annual_target, monthly_target
    classified_deals keys: submitted, pipeline, stalled, closed_won, closed_lost

    Returns a flat metrics dict.
    """
    d = today or _today_sgt()

    annual_target: float = float(settings.get("annual_target") or config.DEFAULT_ANNUAL_TARGET)
    monthly_target: float = float(settings.get("monthly_target") or config.DEFAULT_MONTHLY_TARGET)

    # YTD source of truth: manual entry preferred; fall back to Closed Won sum
    manual_ytd = settings.get("current_ytd")
    if manual_ytd is not None:
        ytd: float = float(manual_ytd)
    else:
        ytd = _sum_amounts(classified_deals.get("closed_won", []))

    submitted_commission: float = _sum_amounts(classified_deals.get("submitted", []))
    pipeline_commission: float = _sum_amounts(classified_deals.get("pipeline", []))
    stalled_deals = classified_deals.get("stalled", [])
    stalled_count: int = len(stalled_deals)
    stalled_amount: float = _sum_amounts(stalled_deals)
    proposal_deals = [
        d_ for d_ in classified_deals.get("pipeline", [])
        if _normalise_stage(d_.get("dealstage", "")) == "proposal presented"
    ]
    proposal_count: int = len(proposal_deals)
    proposal_amount: float = _sum_amounts(proposal_deals)
    submitted_deals = classified_deals.get("submitted", [])
    submitted_count: int = len(submitted_deals)

    remaining_weeks: float = _remaining_weeks_in_year(d)
    remaining_months: float = _remaining_months_in_year(d)

    shortfall: float = max(annual_target - ytd, 0.0)
    weekly_needed: float = shortfall / remaining_weeks
    monthly_needed: float = shortfall / remaining_months
    weekly_gap: float = weekly_needed - submitted_commission
    monthly_gap: float = monthly_needed - submitted_commission

    achievement_pct: float = (ytd / annual_target * 100) if annual_target > 0 else 0.0
    target_incl_pipeline_pct: float = (
        (ytd + submitted_commission + pipeline_commission) / annual_target * 100
        if annual_target > 0 else 0.0
    )

    return {
        # Targets
        "annual_target": annual_target,
        "monthly_target": monthly_target,
        # YTD
        "ytd": ytd,
        "ytd_source": "manual" if manual_ytd is not None else "closed_won",
        # Shortfall & pace
        "shortfall": shortfall,
        "remaining_weeks": remaining_weeks,
        "remaining_months": remaining_months,
        "weekly_needed": weekly_needed,
        "monthly_needed": monthly_needed,
        "weekly_gap": weekly_gap,
        "monthly_gap": monthly_gap,
        # Achievement
        "achievement_pct": achievement_pct,
        "target_incl_pipeline_pct": target_incl_pipeline_pct,
        # Deal breakdown
        "submitted_commission": submitted_commission,
        "submitted_count": submitted_count,
        "pipeline_commission": pipeline_commission,
        "pipeline_count": len(classified_deals.get("pipeline", [])),
        "stalled_count": stalled_count,
        "stalled_amount": stalled_amount,
        "proposal_count": proposal_count,
        "proposal_amount": proposal_amount,
        # Date context
        "date": d,
    }
