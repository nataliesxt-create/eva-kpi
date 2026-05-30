"""
report_builder.py — Format KPI data for OpenAI and assemble final Slack messages.

Style: matches CobyOS Daily Brief — dividers, emoji headers, bullet points.

Daily  : short, sharp, today-focused, one move only
Weekly : pace-focused, bottlenecks, movement, 3 practical suggestions
Monthly: business review, monthly target + gap matter, pipeline quality
"""
from datetime import date, timedelta
from typing import Any

from eva.clients import openai_client

_DIVIDER = "──────────────────────"


def _fmt(amount: float) -> str:
    return f"${amount:,.2f}"


def _pct(pct: float) -> str:
    return f"{pct:.1f}%"


def _pipeline_funnel(metrics: dict) -> str:
    bd = metrics.get("pipeline_breakdown", {})
    def _line(label: str, key: str, emoji: str) -> str:
        count, amount = bd.get(key, (0, 0.0))
        return f"• {emoji} {label}: {count} case{'s' if count != 1 else ''} / {_fmt(amount)}"

    return (
        f"{_DIVIDER}\n"
        f"🔄 *3. Pipeline funnel*\n\n"
        + _line("Contacted",                 "contacted",               "📞") + "\n"
        + _line("Appt Scheduled",            "appointment_scheduled",   "📅") + "\n"
        + _line("Proposal Appt Scheduled",   "proposal_appt_scheduled", "🗓️") + "\n"
        + _line("Opening",                   "opening",                 "🔓") + "\n"
        + _line("Proposal Presented",        "proposal_presented",      "📋")
    )


# ─────────────────────────────────────────────────────────────────────────────
# KPI input formatters (fed to OpenAI — plain text, no Slack markdown)
# ─────────────────────────────────────────────────────────────────────────────

def prepareDailyKpiInput(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    return (
        f"Date: {d.strftime('%A, %d %B %Y')}\n"
        f"Annual Target: {_fmt(metrics['annual_target'])}\n"
        f"YTD: {_fmt(metrics['ytd'])}\n"
        f"Shortfall: {_fmt(metrics['shortfall'])}\n"
        f"Weekly Needed: {_fmt(metrics['weekly_needed'])}\n"
        f"Monthly Needed: {_fmt(metrics['monthly_needed'])}\n"
        f"Submitted / Underwriting / Accepted: {_fmt(metrics['submitted_commission'])}\n"
        f"Active Pipeline Commission: {_fmt(metrics['pipeline_commission'])}\n"
        f"Stalled Cases: {metrics['stalled_count']} / {_fmt(metrics['stalled_amount'])}\n"
        f"Achievement: {_pct(metrics['achievement_pct'])}\n"
        f"Target incl. pipeline: {_pct(metrics['target_incl_pipeline_pct'])}\n"
    )


def prepareWeeklyKpiInput(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    week_start = d - timedelta(days=d.weekday())
    return (
        f"Week of: {week_start.strftime('%d %B %Y')}\n"
        f"Annual Target: {_fmt(metrics['annual_target'])}\n"
        f"YTD: {_fmt(metrics['ytd'])}\n"
        f"Shortfall: {_fmt(metrics['shortfall'])}\n"
        f"Weekly Needed: {_fmt(metrics['weekly_needed'])}\n"
        f"Weekly Gap: {_fmt(metrics['weekly_gap'])}\n"
        f"Submitted Commission: {_fmt(metrics['submitted_commission'])}\n"
        f"Pipeline Commission: {_fmt(metrics['pipeline_commission'])}\n"
        f"Stalled Deals: {metrics['stalled_count']}\n"
        f"Proposal Presented: {metrics['proposal_count']} cases / {_fmt(metrics['proposal_amount'])}\n"
        f"Submitted / Underwriting / Accepted: {metrics['submitted_count']} cases / {_fmt(metrics['submitted_commission'])}\n"
        f"Achievement: {_pct(metrics['achievement_pct'])}\n"
        f"Target incl. pipeline: {_pct(metrics['target_incl_pipeline_pct'])}\n"
    )


def prepareMonthlyKpiInput(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    return (
        f"Month: {d.strftime('%B %Y')}\n"
        f"Annual Target: {_fmt(metrics['annual_target'])}\n"
        f"Monthly Target: {_fmt(metrics['monthly_target'])}\n"
        f"YTD: {_fmt(metrics['ytd'])}\n"
        f"Shortfall: {_fmt(metrics['shortfall'])}\n"
        f"Achievement: {_pct(metrics['achievement_pct'])}\n"
        f"Target incl. pipeline: {_pct(metrics['target_incl_pipeline_pct'])}\n"
        f"Monthly Needed: {_fmt(metrics['monthly_needed'])}\n"
        f"Monthly Gap: {_fmt(metrics['monthly_gap'])}\n"
        f"Submitted Commission: {_fmt(metrics['submitted_commission'])}\n"
        f"Pipeline Commission: {_fmt(metrics['pipeline_commission'])}\n"
        f"Submitted / Underwriting / Accepted: {metrics['submitted_count']} cases / {_fmt(metrics['submitted_commission'])}\n"
        f"Stalled Deals: {metrics['stalled_count']} / {_fmt(metrics['stalled_amount'])}\n"
        f"Proposal Presented: {metrics['proposal_count']} / {_fmt(metrics['proposal_amount'])}\n"
        f"Active Pipeline: {metrics['pipeline_count']} cases / {_fmt(metrics['pipeline_commission'])}\n"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Report assemblers
# ─────────────────────────────────────────────────────────────────────────────

def buildDailyReport(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    date_str = d.strftime("%d %B %Y")
    day_str = d.strftime("%A")

    kpi_input = prepareDailyKpiInput(metrics)
    ai_narrative = openai_client.generateEvaReportWithOpenAI("daily", kpi_input)

    sections = [
        f"💰 *Eva Daily KPI*\n{day_str}, {date_str}",

        (
            f"{_DIVIDER}\n"
            f"📍 *1. Today's target pulse*\n\n"
            f"• 📈 YTD: {_fmt(metrics['ytd'])} _(+{_fmt(metrics['submitted_commission'])} submitted = {_fmt(metrics['effective_ytd'])} effective)_\n"
            f"• 🎯 Shortfall: {_fmt(metrics['shortfall'])}\n"
            f"• 📅 Weekly Needed: {_fmt(metrics['weekly_needed'])}\n"
            f"• 🗓️ Monthly Needed: {_fmt(metrics['monthly_needed'])}"
        ),

        (
            f"{_DIVIDER}\n"
            f"⚡ *2. Movement today*\n\n"
            f"• ✅ Submitted / Underwriting / Accepted: {_fmt(metrics['submitted_commission'])}\n"
            f"• 🔄 Active Pipeline: {_fmt(metrics['pipeline_commission'])}\n"
            f"• ⏸️ Stalled: {metrics['stalled_count']} cases / {_fmt(metrics['stalled_amount'])}"
        ),

        _pipeline_funnel(metrics),

        f"{_DIVIDER}\n{ai_narrative}",
    ]

    return "\n\n".join(sections)


def buildWeeklyReport(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    week_start = d - timedelta(days=d.weekday())
    week_str = week_start.strftime("%d %B %Y")

    kpi_input = prepareWeeklyKpiInput(metrics)
    ai_narrative = openai_client.generateEvaReportWithOpenAI("weekly", kpi_input)

    sections = [
        f"📊 *Eva Weekly Review*\nWeek of {week_str}",

        (
            f"{_DIVIDER}\n"
            f"🏃 *1. Weekly pace*\n\n"
            f"• 📈 YTD: {_fmt(metrics['ytd'])}\n"
            f"• 🎯 Shortfall: {_fmt(metrics['shortfall'])}\n"
            f"• 📅 Weekly Needed: {_fmt(metrics['weekly_needed'])}\n"
            f"• ⚠️ Weekly Gap: {_fmt(metrics['weekly_gap'])}\n"
            f"• ✅ Submitted Commission: {_fmt(metrics['submitted_commission'])}"
        ),

        (
            f"{_DIVIDER}\n"
            f"🔄 *2. Pipeline movement*\n\n"
            f"• 💼 Pipeline Commission: {_fmt(metrics['pipeline_commission'])}\n"
            f"• ⏸️ Stalled Deals: {metrics['stalled_count']}\n"
            f"• 📋 Proposal Presented: {metrics['proposal_count']} / {_fmt(metrics['proposal_amount'])}\n"
            f"• ✅ Submitted / Underwriting / Accepted: {metrics['submitted_count']} / {_fmt(metrics['submitted_commission'])}"
        ),

        _pipeline_funnel(metrics),

        f"{_DIVIDER}\n{ai_narrative}",
    ]

    return "\n\n".join(sections)


def buildMonthlyReport(metrics: dict[str, Any]) -> str:
    d: date = metrics["date"]
    month_str = d.strftime("%B %Y")

    kpi_input = prepareMonthlyKpiInput(metrics)
    ai_narrative = openai_client.generateEvaReportWithOpenAI("monthly", kpi_input)

    sections = [
        f"🗓️ *Eva Monthly Review*\n{month_str}",

        (
            f"{_DIVIDER}\n"
            f"🏆 *1. Month-end scorecard*\n\n"
            f"• 🎯 Annual Target: {_fmt(metrics['annual_target'])}\n"
            f"• 📅 Monthly Target: {_fmt(metrics['monthly_target'])}\n"
            f"• 📈 YTD: {_fmt(metrics['ytd'])}\n"
            f"• ⚠️ Shortfall: {_fmt(metrics['shortfall'])}\n"
            f"• 💯 Achievement: {_pct(metrics['achievement_pct'])}\n"
            f"• 🔭 Target incl. pipeline: {_pct(metrics['target_incl_pipeline_pct'])}"
        ),

        (
            f"{_DIVIDER}\n"
            f"🏃 *2. Monthly pace*\n\n"
            f"• 📋 Monthly Needed: {_fmt(metrics['monthly_needed'])}\n"
            f"• ⚠️ Monthly Gap: {_fmt(metrics['monthly_gap'])}\n"
            f"• ✅ Submitted Commission: {_fmt(metrics['submitted_commission'])}\n"
            f"• 🔄 Pipeline Commission: {_fmt(metrics['pipeline_commission'])}"
        ),

        (
            f"{_DIVIDER}\n"
            f"💼 *3. Business movement*\n\n"
            f"• ✅ Submitted / Underwriting / Accepted: {metrics['submitted_count']} / {_fmt(metrics['submitted_commission'])}\n"
            f"• ⏸️ Stalled Deals: {metrics['stalled_count']} / {_fmt(metrics['stalled_amount'])}\n"
            f"• 📋 Proposal Presented: {metrics['proposal_count']} / {_fmt(metrics['proposal_amount'])}\n"
            f"• 🔄 Active Pipeline: {metrics['pipeline_count']} / {_fmt(metrics['pipeline_commission'])}"
        ),

        _pipeline_funnel(metrics),

        f"{_DIVIDER}\n{ai_narrative}",
    ]

    return "\n\n".join(sections)
