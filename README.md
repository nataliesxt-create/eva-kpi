# Eva KPI Agent — CobyOS

Eva answers: **"How am I doing against my target?"**

Posts to `#eva-kpi` on a scheduled cadence, and listens for manual YTD updates.

---

## What Eva does

| Cadence | Schedule (SGT) | Purpose |
|---------|---------------|---------|
| Daily KPI Dashboard | Mon–Fri 06:30 | Today's pulse + one action |
| Weekly KPI Overview | Sunday 20:00 | Pace, bottlenecks, 3 strategies |
| Monthly KPI Overview | Last day of month 20:00 | Business review, next month strategy |
| YTD Listener | Always on | Accepts `YTD 2435.97` messages |

---

## Project structure

```
eva-kpi/
├── main.py                   Entry point (CLI + production mode)
├── requirements.txt
├── .env.example
└── eva/
    ├── config.py             Env vars and constants
    ├── kpi_calculations.py   All deterministic KPI math
    ├── report_builder.py     OpenAI prompt builders + Slack formatters
    ├── kpi_agent.py          Orchestrator (daily/weekly/monthly)
    ├── scheduler.py          APScheduler cron jobs
    ├── ytd_listener.py       Slack message listener for YTD updates
    └── clients/
        ├── hubspot_client.py HubSpot deals
        ├── sheets_client.py  Google Sheets (Eva KPI Settings)
        ├── openai_client.py  OpenAI strategy generation
        └── slack_client.py   Slack posting
tests/
    ├── test_ytd_parser.py
    ├── test_kpi_calculations.py
    └── test_reports.py
```

---

## Environment variables

Copy `.env.example` to `.env`:

```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_EVA_KPI_CHANNEL_ID=C...

HUBSPOT_PRIVATE_APP_TOKEN=pat-...
HUBSPOT_PIPELINE_ID=default

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o

EVA_KPI_SETTINGS_SHEET_ID=1abc...
GOOGLE_SHEETS_CREDENTIALS=/path/to/service-account.json
```

---

## Google Sheet setup

Create a Google Sheet named **Eva KPI Settings** with these columns:

| A (key) | B (value) | C (updated_at) |
|---------|-----------|---------------|
| annual_target | 100000 | |
| monthly_target | 8333 | |
| current_ytd | 0 | |

Share the sheet with your service account email (from the JSON credentials file).

---

## Slack app setup

1. Create a Slack app at api.slack.com
2. Enable **Socket Mode** — generate an App-Level Token (`xapp-...`)
3. Add Bot Token Scopes: `chat:write`, `channels:history`, `groups:history`
4. Subscribe to `message.channels` and `message.groups` events
5. Install the app and invite it to `#eva-kpi`

---

## Local setup

```bash
cd eva-kpi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# fill in .env values
```

### Run tests (no credentials needed)

```bash
pytest tests/ -v
```

### Manual triggers

```bash
python main.py --daily        # Post Daily KPI now
python main.py --weekly       # Post Weekly KPI now
python main.py --monthly      # Post Monthly KPI now (bypasses last-day check)
python main.py --list-stages  # Print HubSpot pipeline stages
```

### Production

```bash
python main.py
```

Eva starts the scheduler and listens for YTD messages on `#eva-kpi`.

---

## YTD update (Slack)

Type in `#eva-kpi`:

```
YTD 2435.97
YTD $2,435.97
YTD 10000
```

Eva replies: `Updated YTD received`

This stored value becomes the source of truth for all reports.

---

## KPI definitions

| Metric | Source |
|--------|--------|
| YTD | Stored manual update (Google Sheets) |
| Annual Target | Google Sheets (default $100,000) |
| Monthly Target | Google Sheets (default $8,333) |
| Submitted Commission | Deals in Submitted / Underwriting / Accepted |
| Pipeline Commission | Deals in earlier active stages |
| Stalled | Deals in "To Follow Up / Stalled" |
| Shortfall | Annual Target − YTD |
| Weekly Needed | Shortfall ÷ remaining weeks |
| Monthly Needed | Shortfall ÷ remaining months |
| Achievement % | YTD ÷ Annual Target |
| Target incl. pipeline % | (YTD + Submitted + Pipeline) ÷ Annual Target |
