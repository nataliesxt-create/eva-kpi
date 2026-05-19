"""
kpi_agent.py — Eva KPI Agent orchestrator.

Pulls settings + deals, calculates metrics, builds and posts reports.
These functions are called by the scheduler and by tests.
"""
import calendar
from datetime import datetime

from zoneinfo import ZoneInfo

from eva import config
from eva.clients import sheets_client, hubspot_client, slack_client
from eva import kpi_calculations, report_builder

SGT = ZoneInfo(config.TIMEZONE)


def _load_metrics() -> dict:
    """Shared helper: fetch settings + deals, return metrics dict."""
    settings = sheets_client.fetchKpiSettings()
    deals = hubspot_client.fetchHubSpotDeals()
    classified = kpi_calculations.classifyDealsByStage(deals)
    metrics = kpi_calculations.calculateKpiMetrics(settings, classified)
    return metrics


def run_daily_kpi() -> None:
    """Post the Daily KPI report to #eva-kpi. Runs Mon-Fri 06:30 SGT."""
    metrics = _load_metrics()
    message = report_builder.buildDailyReport(metrics)
    slack_client.postToSlack(message)
    print(f"[kpi_agent] Daily KPI posted for {metrics['date']}")


def run_weekly_review() -> None:
    """Post the Weekly Review to #eva-kpi. Runs every Sunday 20:00 SGT."""
    metrics = _load_metrics()
    message = report_builder.buildWeeklyReport(metrics)
    slack_client.postToSlack(message)
    print(f"[kpi_agent] Weekly Review posted for week of {metrics['date']}")


def run_monthly_review(force: bool = False) -> None:
    """
    Post the Monthly Review to #eva-kpi.
    Scheduled on 28th–31st at 20:00 SGT; only runs on actual last day of month.
    Pass force=True to bypass the last-day check (for manual triggers).
    """
    now = datetime.now(SGT)
    today = now.date()
    last_day = calendar.monthrange(today.year, today.month)[1]
    if not force and today.day != last_day:
        print(f"[kpi_agent] Monthly review skipped — today ({today.day}) is not the last day ({last_day}) of the month.")
        return
    metrics = _load_metrics()
    message = report_builder.buildMonthlyReport(metrics)
    slack_client.postToSlack(message)
    print(f"[kpi_agent] Monthly Review posted for {metrics['date'].strftime('%B %Y')}")
