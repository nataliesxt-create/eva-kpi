"""
test_kpi_calculations.py — Tests for classifyDealsByStage and calculateKpiMetrics.

Covers:
  - HubSpot stage classification (all buckets)
  - KPI calculation from stored YTD
  - Weekly needed and weekly gap
  - Monthly needed and monthly gap
  - Closed Won fallback when no manual YTD
  - Closed Lost excluded from calculations
"""
import pytest
from datetime import date
from unittest.mock import patch

from eva.kpi_calculations import (
    classifyDealsByStage,
    calculateKpiMetrics,
    _remaining_weeks_in_year,
    _remaining_months_in_year,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

def make_deal(dealstage: str, amount: float, dealid: str = "1") -> dict:
    return {"id": dealid, "dealname": f"Deal {dealid}", "dealstage": dealstage, "amount": amount}


SAMPLE_DEALS = [
    make_deal("Submitted", 5000.0, "1"),
    make_deal("Accepted", 3000.0, "2"),
    make_deal("Underwriting", 2000.0, "3"),
    make_deal("Contacted", 8000.0, "4"),
    make_deal("Proposal Presented", 12000.0, "5"),
    make_deal("Opening", 4000.0, "6"),
    make_deal("To Follow Up / Stalled", 6000.0, "7"),
    make_deal("closedwon", 15000.0, "8"),
    make_deal("closedlost", 9000.0, "9"),
]


# ─────────────────────────────────────────────────────────────────────────────
# classifyDealsByStage
# ─────────────────────────────────────────────────────────────────────────────

class TestClassifyDealsByStage:
    def test_submitted_stages(self):
        result = classifyDealsByStage(SAMPLE_DEALS)
        submitted_amounts = [d["amount"] for d in result["submitted"]]
        assert 5000.0 in submitted_amounts  # Submitted
        assert 3000.0 in submitted_amounts  # Accepted
        assert 2000.0 in submitted_amounts  # Underwriting

    def test_pipeline_stages(self):
        result = classifyDealsByStage(SAMPLE_DEALS)
        pipeline_amounts = [d["amount"] for d in result["pipeline"]]
        assert 8000.0 in pipeline_amounts   # Contacted
        assert 12000.0 in pipeline_amounts  # Proposal Presented
        assert 4000.0 in pipeline_amounts   # Opening

    def test_stalled_stage(self):
        result = classifyDealsByStage(SAMPLE_DEALS)
        assert len(result["stalled"]) == 1
        assert result["stalled"][0]["amount"] == 6000.0

    def test_closed_won(self):
        result = classifyDealsByStage(SAMPLE_DEALS)
        assert len(result["closed_won"]) == 1
        assert result["closed_won"][0]["amount"] == 15000.0

    def test_closed_lost_excluded_from_active(self):
        result = classifyDealsByStage(SAMPLE_DEALS)
        # closed_lost is captured but not in submitted/pipeline/stalled
        assert len(result["closed_lost"]) == 1
        closed_lost_ids = [d["id"] for d in result["closed_lost"]]
        submitted_ids = [d["id"] for d in result["submitted"]]
        pipeline_ids = [d["id"] for d in result["pipeline"]]
        stalled_ids = [d["id"] for d in result["stalled"]]
        assert "9" in closed_lost_ids
        assert "9" not in submitted_ids
        assert "9" not in pipeline_ids
        assert "9" not in stalled_ids

    def test_case_insensitive_matching(self):
        deals = [
            make_deal("SUBMITTED", 1000.0, "a"),
            make_deal("proposal presented", 2000.0, "b"),
            make_deal("TO FOLLOW UP / STALLED", 3000.0, "c"),
        ]
        result = classifyDealsByStage(deals)
        assert len(result["submitted"]) == 1
        assert len(result["pipeline"]) == 1
        assert len(result["stalled"]) == 1

    def test_unknown_stage_ignored(self):
        deals = [make_deal("some weird stage", 999.0, "z")]
        result = classifyDealsByStage(deals)
        all_deals = (
            result["submitted"] + result["pipeline"] +
            result["stalled"] + result["closed_won"] + result["closed_lost"]
        )
        assert len(all_deals) == 0

    def test_empty_deals(self):
        result = classifyDealsByStage([])
        assert all(len(v) == 0 for v in result.values())


# ─────────────────────────────────────────────────────────────────────────────
# calculateKpiMetrics
# ─────────────────────────────────────────────────────────────────────────────

class TestCalculateKpiMetrics:
    """Use a fixed date (2026-06-01 = 1 June 2026) for deterministic results."""

    FIXED_DATE = date(2026, 6, 1)  # Monday, 1 June 2026

    def _classified(self):
        return classifyDealsByStage(SAMPLE_DEALS)

    def test_ytd_from_manual_setting(self):
        settings = {"current_ytd": 25000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["ytd"] == pytest.approx(25000.0)
        assert metrics["ytd_source"] == "manual"

    def test_ytd_falls_back_to_closed_won(self):
        settings = {"current_ytd": None, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["ytd"] == pytest.approx(15000.0)  # closed_won sum
        assert metrics["ytd_source"] == "closed_won"

    def test_shortfall_calculation(self):
        settings = {"current_ytd": 40000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["shortfall"] == pytest.approx(60000.0)

    def test_shortfall_zero_when_ytd_exceeds_target(self):
        settings = {"current_ytd": 110000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["shortfall"] == pytest.approx(0.0)

    def test_weekly_needed_calculation(self):
        settings = {"current_ytd": 40000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        remaining_weeks = _remaining_weeks_in_year(self.FIXED_DATE)
        expected = 60000.0 / remaining_weeks
        assert metrics["weekly_needed"] == pytest.approx(expected, rel=1e-4)

    def test_monthly_needed_calculation(self):
        settings = {"current_ytd": 40000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        remaining_months = _remaining_months_in_year(self.FIXED_DATE)
        expected = 60000.0 / remaining_months
        assert metrics["monthly_needed"] == pytest.approx(expected, rel=1e-4)

    def test_weekly_gap_calculation(self):
        settings = {"current_ytd": 40000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        # submitted = 5000 + 3000 + 2000 = 10000
        expected_gap = metrics["weekly_needed"] - 10000.0
        assert metrics["weekly_gap"] == pytest.approx(expected_gap, rel=1e-4)

    def test_monthly_gap_calculation(self):
        settings = {"current_ytd": 40000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        expected_gap = metrics["monthly_needed"] - 10000.0
        assert metrics["monthly_gap"] == pytest.approx(expected_gap, rel=1e-4)

    def test_achievement_pct(self):
        settings = {"current_ytd": 50000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["achievement_pct"] == pytest.approx(50.0)

    def test_target_incl_pipeline_pct(self):
        settings = {"current_ytd": 25000.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        # submitted = 10000, pipeline = 8000+12000+4000 = 24000
        expected_pct = (25000.0 + 10000.0 + 24000.0) / 100000.0 * 100
        assert metrics["target_incl_pipeline_pct"] == pytest.approx(expected_pct, rel=1e-4)

    def test_submitted_commission_sum(self):
        settings = {"current_ytd": 0.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["submitted_commission"] == pytest.approx(10000.0)  # 5000+3000+2000

    def test_pipeline_commission_sum(self):
        settings = {"current_ytd": 0.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["pipeline_commission"] == pytest.approx(24000.0)  # 8000+12000+4000

    def test_stalled_count_and_amount(self):
        settings = {"current_ytd": 0.0, "annual_target": 100000.0, "monthly_target": 8333.0}
        metrics = calculateKpiMetrics(settings, self._classified(), today=self.FIXED_DATE)
        assert metrics["stalled_count"] == 1
        assert metrics["stalled_amount"] == pytest.approx(6000.0)

    def test_defaults_used_when_settings_missing(self):
        settings = {}
        metrics = calculateKpiMetrics(settings, {
            "submitted": [], "pipeline": [], "stalled": [],
            "closed_won": [], "closed_lost": [],
        }, today=self.FIXED_DATE)
        assert metrics["annual_target"] == pytest.approx(100000.0)
        assert metrics["monthly_target"] == pytest.approx(8333.0)


# ─────────────────────────────────────────────────────────────────────────────
# Time helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestTimeHelpers:
    def test_remaining_weeks_start_of_year(self):
        weeks = _remaining_weeks_in_year(date(2026, 1, 1))
        assert weeks == pytest.approx(365 / 7, rel=0.01)

    def test_remaining_weeks_end_of_year(self):
        # Dec 31: raw = 1 day / 7 = 0.143 weeks, but clamped to minimum of 1.0
        weeks = _remaining_weeks_in_year(date(2026, 12, 31))
        assert weeks == pytest.approx(1.0)

    def test_remaining_months_january(self):
        months = _remaining_months_in_year(date(2026, 1, 15))
        assert months == pytest.approx(12.0)

    def test_remaining_months_december(self):
        months = _remaining_months_in_year(date(2026, 12, 1))
        assert months == pytest.approx(1.0)

    def test_remaining_months_june(self):
        months = _remaining_months_in_year(date(2026, 6, 1))
        assert months == pytest.approx(7.0)
