"""
test_reports.py — Tests for report_builder formatting.

Covers:
  - Daily / Weekly / Monthly formats are structurally different
  - Each report contains required section headers
  - Correct numbers appear in reports
  - Eva does not fetch or include Google Calendar data
  - OpenAI is mocked so tests don't make real API calls
"""
import pytest
from datetime import date
from unittest.mock import patch, MagicMock

from eva.report_builder import (
    buildDailyReport,
    buildWeeklyReport,
    buildMonthlyReport,
    prepareDailyKpiInput,
    prepareWeeklyKpiInput,
    prepareMonthlyKpiInput,
)


# ─────────────────────────────────────────────────────────────────────────────
# Shared fixture
# ─────────────────────────────────────────────────────────────────────────────

FIXED_DATE = date(2026, 6, 15)  # Monday

BASE_METRICS = {
    "annual_target": 100000.0,
    "monthly_target": 8333.0,
    "ytd": 45000.0,
    "ytd_source": "manual",
    "shortfall": 55000.0,
    "remaining_weeks": 28.0,
    "remaining_months": 7.0,
    "weekly_needed": 55000.0 / 28.0,
    "monthly_needed": 55000.0 / 7.0,
    "weekly_gap": (55000.0 / 28.0) - 8000.0,
    "monthly_gap": (55000.0 / 7.0) - 8000.0,
    "achievement_pct": 45.0,
    "target_incl_pipeline_pct": 72.0,
    "submitted_commission": 8000.0,
    "submitted_count": 3,
    "pipeline_commission": 19000.0,
    "pipeline_count": 5,
    "stalled_count": 2,
    "stalled_amount": 7000.0,
    "proposal_count": 2,
    "proposal_amount": 12000.0,
    "date": FIXED_DATE,
}

DAILY_AI_STUB = "**Eva's read**\nYou are 45% through your target.\n\n**Today's move**\nFollow up on your two stalled cases today."
WEEKLY_AI_STUB = "**Eva's weekly read**\nPace is below par.\n\n**Strategy Suggestions**\n- Move proposals forward\n- Re-engage stalled cases\n- Submit pending underwriting"
MONTHLY_AI_STUB = "**Eva's monthly read**\nA solid mid-year position.\n\n**Next Month's Strategy**\n- Build pipeline through referrals\n- Follow up on all proposals within 48 hours\n- Block two prospecting sessions per week"


# ─────────────────────────────────────────────────────────────────────────────
# prepareDailyKpiInput
# ─────────────────────────────────────────────────────────────────────────────

class TestPrepareDailyKpiInput:
    def test_contains_ytd(self):
        result = prepareDailyKpiInput(BASE_METRICS)
        assert "45,000.00" in result

    def test_contains_shortfall(self):
        result = prepareDailyKpiInput(BASE_METRICS)
        assert "55,000.00" in result

    def test_contains_weekly_needed(self):
        result = prepareDailyKpiInput(BASE_METRICS)
        assert "Weekly Needed" in result

    def test_contains_monthly_needed(self):
        result = prepareDailyKpiInput(BASE_METRICS)
        assert "Monthly Needed" in result

    def test_no_calendar_data(self):
        result = prepareDailyKpiInput(BASE_METRICS)
        assert "calendar" not in result.lower()
        assert "appointment" not in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# prepareWeeklyKpiInput
# ─────────────────────────────────────────────────────────────────────────────

class TestPrepareWeeklyKpiInput:
    def test_contains_weekly_gap(self):
        result = prepareWeeklyKpiInput(BASE_METRICS)
        assert "Weekly Gap" in result

    def test_contains_proposal_data(self):
        result = prepareWeeklyKpiInput(BASE_METRICS)
        assert "Proposal Presented" in result

    def test_no_calendar_data(self):
        result = prepareWeeklyKpiInput(BASE_METRICS)
        assert "calendar" not in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# prepareMonthlyKpiInput
# ─────────────────────────────────────────────────────────────────────────────

class TestPrepareMonthlyKpiInput:
    def test_contains_monthly_target(self):
        result = prepareMonthlyKpiInput(BASE_METRICS)
        assert "Monthly Target" in result

    def test_contains_monthly_gap(self):
        result = prepareMonthlyKpiInput(BASE_METRICS)
        assert "Monthly Gap" in result

    def test_contains_achievement(self):
        result = prepareMonthlyKpiInput(BASE_METRICS)
        assert "Achievement" in result

    def test_no_calendar_data(self):
        result = prepareMonthlyKpiInput(BASE_METRICS)
        assert "calendar" not in result.lower()


# ─────────────────────────────────────────────────────────────────────────────
# buildDailyReport
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildDailyReport:
    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_header_format(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "Eva Daily KPI" in report
        assert "15 June 2026" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_contains_target_pulse_section(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "Today's target pulse" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_contains_movement_section(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "Movement today" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_ytd_in_report(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "45,000.00" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_stalled_count_in_report(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "2 cases" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=DAILY_AI_STUB)
    def test_no_calendar_reference(self, _mock_ai):
        report = buildDailyReport(BASE_METRICS)
        assert "google calendar" not in report.lower()
        assert "calendar event" not in report.lower()


# ─────────────────────────────────────────────────────────────────────────────
# buildWeeklyReport
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildWeeklyReport:
    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=WEEKLY_AI_STUB)
    def test_header_format(self, _mock_ai):
        report = buildWeeklyReport(BASE_METRICS)
        assert "Eva Weekly Review" in report
        assert "Week of" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=WEEKLY_AI_STUB)
    def test_has_weekly_pace_section(self, _mock_ai):
        report = buildWeeklyReport(BASE_METRICS)
        assert "1. Weekly pace" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=WEEKLY_AI_STUB)
    def test_has_pipeline_movement_section(self, _mock_ai):
        report = buildWeeklyReport(BASE_METRICS)
        assert "2. Pipeline movement" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=WEEKLY_AI_STUB)
    def test_weekly_gap_in_report(self, _mock_ai):
        report = buildWeeklyReport(BASE_METRICS)
        assert "Weekly Gap" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=WEEKLY_AI_STUB)
    def test_no_calendar_reference(self, _mock_ai):
        report = buildWeeklyReport(BASE_METRICS)
        assert "google calendar" not in report.lower()


# ─────────────────────────────────────────────────────────────────────────────
# buildMonthlyReport
# ─────────────────────────────────────────────────────────────────────────────

class TestBuildMonthlyReport:
    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_header_format(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "Eva Monthly Review" in report
        assert "June 2026" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_has_scorecard_section(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "1. Month-end scorecard" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_has_monthly_pace_section(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "2. Monthly pace" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_has_business_movement_section(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "3. Business movement" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_monthly_target_in_report(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "8,333.00" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_achievement_pct_in_report(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "45.0%" in report

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI", return_value=MONTHLY_AI_STUB)
    def test_no_calendar_reference(self, _mock_ai):
        report = buildMonthlyReport(BASE_METRICS)
        assert "google calendar" not in report.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Daily vs Weekly vs Monthly are structurally different
# ─────────────────────────────────────────────────────────────────────────────

class TestReportsDiffer:
    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI")
    def test_daily_weekly_monthly_have_different_headers(self, mock_ai):
        mock_ai.side_effect = [DAILY_AI_STUB, WEEKLY_AI_STUB, MONTHLY_AI_STUB]
        daily = buildDailyReport(BASE_METRICS)
        weekly = buildWeeklyReport(BASE_METRICS)
        monthly = buildMonthlyReport(BASE_METRICS)

        assert "Eva Daily KPI" in daily
        assert "Eva Weekly Review" in weekly
        assert "Eva Monthly Review" in monthly

        assert "Eva Daily KPI" not in weekly
        assert "Eva Weekly Review" not in daily
        assert "Eva Monthly Review" not in daily

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI")
    def test_daily_does_not_have_weekly_sections(self, mock_ai):
        mock_ai.return_value = DAILY_AI_STUB
        daily = buildDailyReport(BASE_METRICS)
        assert "Weekly pace" not in daily
        assert "Pipeline movement" not in daily

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI")
    def test_weekly_does_not_have_monthly_scorecard(self, mock_ai):
        mock_ai.return_value = WEEKLY_AI_STUB
        weekly = buildWeeklyReport(BASE_METRICS)
        assert "Month-end scorecard" not in weekly

    @patch("eva.report_builder.openai_client.generateEvaReportWithOpenAI")
    def test_monthly_contains_monthly_target(self, mock_ai):
        mock_ai.return_value = MONTHLY_AI_STUB
        monthly = buildMonthlyReport(BASE_METRICS)
        assert "Monthly Target" in monthly
        # Daily should not have Monthly Target header
        mock_ai.return_value = DAILY_AI_STUB
        daily = buildDailyReport(BASE_METRICS)
        assert "Monthly Target" not in daily


# ─────────────────────────────────────────────────────────────────────────────
# Eva does not fetch Google Calendar data
# ─────────────────────────────────────────────────────────────────────────────

class TestNoGoogleCalendarInReports:
    def test_report_builder_has_no_calendar_import(self):
        import eva.report_builder as module
        import inspect
        source = inspect.getsource(module)
        assert "google.calendar" not in source
        assert "googleapiclient" not in source
        assert "calendar_client" not in source

    def test_kpi_agent_has_no_calendar_import(self):
        import eva.kpi_agent as module
        import inspect
        source = inspect.getsource(module)
        assert "google.calendar" not in source
        assert "calendar_client" not in source
