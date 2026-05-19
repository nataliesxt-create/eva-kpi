"""
scheduler.py — APScheduler cron jobs for Eva KPI reports.

Schedules:
  Daily KPI   : Mon–Fri  06:30 SGT
  Weekly Review: Sunday  20:00 SGT
  Monthly Review: 28–31  20:00 SGT (guard inside run_monthly_review)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from eva import config
from eva import kpi_agent


def create_scheduler() -> BackgroundScheduler:
    """
    Build and return a configured APScheduler BackgroundScheduler.
    Call scheduler.start() to activate.
    """
    scheduler = BackgroundScheduler(timezone=config.TIMEZONE)

    # Daily KPI — Mon to Fri, 06:30 SGT
    scheduler.add_job(
        kpi_agent.run_daily_kpi,
        trigger=CronTrigger(
            day_of_week="mon-fri",
            hour=6,
            minute=30,
            timezone=config.TIMEZONE,
        ),
        id="daily_kpi",
        name="Eva Daily KPI",
        replace_existing=True,
    )

    # Weekly Review — every Sunday, 20:00 SGT
    scheduler.add_job(
        kpi_agent.run_weekly_review,
        trigger=CronTrigger(
            day_of_week="sun",
            hour=20,
            minute=0,
            timezone=config.TIMEZONE,
        ),
        id="weekly_review",
        name="Eva Weekly Review",
        replace_existing=True,
    )

    # Monthly Review — 28th, 29th, 30th, 31st at 20:00 SGT
    # Guard inside run_monthly_review ensures it only posts on the actual last day.
    scheduler.add_job(
        kpi_agent.run_monthly_review,
        trigger=CronTrigger(
            day="28-31",
            hour=20,
            minute=0,
            timezone=config.TIMEZONE,
        ),
        id="monthly_review",
        name="Eva Monthly Review",
        replace_existing=True,
    )

    return scheduler
