# MoveInSync — Play Store Ratings Analyzer

A data pipeline and interactive dashboard for analysing Google Play Store reviews of the **MoveInSync employee commute app** (`com.moveinsync.ets`). It scrapes reviews, classifies complaints using Gemini AI, computes actionable metrics, and presents everything through a Streamlit dashboard — answering *"how are our ratings?"* with a single command.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Language** | Python 3.10+ | Core runtime |
| **Web Scraping** | [google-play-scraper](https://pypi.org/project/google-play-scraper/) ≥ 1.2 | Pulls reviews & app metadata from Google Play |
| **AI / LLM** | [Google Gemini](https://pypi.org/project/google-genai/) ≥ 1.0 (Gemini 3.8 Flash) | Classifies each review into a theme with severity |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) ≥ 2.0 | DataFrames, aggregation, metrics computation |
| **Dashboard** | [Streamlit](https://streamlit.io/) ≥ 1.30 | Interactive web dashboard with charts & tables |
| **PDF Generation** | [markdown](https://pypi.org/project/Markdown/) ≥ 3.5 + headless Chrome | Converts recommendation reports to PDF |
| **Config** | [python-dotenv](https://pypi.org/project/python-dotenv/) ≥ 1.0 | Loads API keys from `.env` |
| **Testing** | [pytest](https://docs.pytest.org/) ≥ 7 | Unit test suite |
| **Schema Validation** | [Pydantic](https://docs.pydantic.dev/) | Validates Gemini response structure |

---

## Project Structure

```
moveinsync-playstore/
├── app.py              # Streamlit dashboard — the main UI
├── run.py              # One-command pipeline: scrape → tag → metrics → summary
├── scrape.py           # Pulls Play Store reviews & headline stats
├── tag.py              # Gemini-powered review classification (cached, resumable)
├── themes.py           # Fixed theme taxonomy (app-fixable vs ops)
├── metrics.py          # Monthly trends, version analysis, theme impact scoring
├── store.py            # Data I/O layer — CSV load/save helpers
├── make_pdf.py         # Markdown → styled PDF via headless Chrome
├── requirements.txt    # Python dependencies
├── pytest.ini          # Test configuration
├── data/
│   ├── reviews.csv     # All scraped reviews
│   ├── tags.csv        # AI-generated theme tags per review
│   ├── app_snapshot.csv# Headline rating snapshots (one row per run)
│   └── metrics/        # Pre-computed CSVs (monthly, versions, themes)
├── report/
│   └── recommendations.md  # Analysis report
├── tests/
│   ├── test_app.py
│   ├── test_metrics.py
│   ├── test_scrape.py
│   ├── test_tag.py
│   └── test_make_pdf.py
└── docs/               # Additional documentation & plans
```

---

## Prerequisites

- **Python 3.10+** installed
- **(Optional) Gemini API key** — free from [aistudio.google.com](https://aistudio.google.com) for AI-powered review tagging
- **(Optional) Google Chrome** — only needed for PDF generation via `make_pdf.py`

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd moveinsync-playstore
```

### 2. Create a virtual environment & install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

> [!IMPORTANT]
> **Always activate the venv** before running any command (`python`, `streamlit`, `pytest`).
> Using the system or Anaconda Python will cause `ModuleNotFoundError` since dependencies are installed inside `.venv`.
>
> ```bash
> # ✅ Correct — activate first
> source .venv/bin/activate
> python run.py
>
> # ✅ Also correct — call the venv binary directly
> .venv/bin/python run.py
>
> # ❌ Wrong — uses system Python, missing packages
> python run.py
> ```

> [!WARNING]
> If you move or rename the project folder after creating the venv, the venv will break
> (hard-coded paths). Recreate it with `python3 -m venv .venv` and reinstall dependencies.

### 3. Set up environment variables

Create a `.env` file in the project root (it's git-ignored):

```bash
echo "GEMINI_API_KEY=<your-key>" > .env
```

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | For tagging | API key from [AI Studio](https://aistudio.google.com) |
| `GEMINI_MODEL` | No | Override the default model (`gemini-3.8-flash`) |
| `DATA_DIR` | No | Custom data directory (default: `data/`) |

### 4. Run the full pipeline

```bash
source .venv/bin/activate
python run.py
```

This will:
1. **Scrape** all new Play Store reviews → `data/reviews.csv`
2. **Tag** untagged reviews with Gemini AI → `data/tags.csv`
3. **Compute** metrics and print a summary to the console

**Pipeline flags:**

| Flag | Effect |
|---|---|
| `--skip-scrape` | Skip scraping, use existing `data/reviews.csv` |
| `--skip-tag` | Skip AI tagging (useful without an API key) |
| `--tag-limit N` | Tag at most N reviews (low stars first) |

### 5. Launch the Streamlit dashboard

```bash
source .venv/bin/activate
streamlit run app.py
```

Open the URL shown in your terminal (default: `http://localhost:8501`).

The dashboard provides four tabs:
- **Overview** — Play Store rating, 30/90-day averages, monthly trends, star distribution
- **Themes** — Complaint themes ranked by impact (recency-weighted)
- **Versions** — Average rating per app version
- **Replies** — Developer reply rate and response time stats

### 6. Run tests

```bash
source .venv/bin/activate
pytest -q
```

---

## How It Works

```
┌──────────┐     ┌──────────┐     ┌───────────┐     ┌───────────┐
│ scrape.py│────▶│  tag.py   │────▶│ metrics.py│────▶│  app.py   │
│          │     │ (Gemini)  │     │           │     │(Streamlit)│
└──────────┘     └──────────┘     └───────────┘     └───────────┘
   reviews.csv     tags.csv        metrics/*.csv      Dashboard
```

| Module | Responsibility |
|---|---|
| `scrape.py` | Pulls every Play Store review (newest first, incremental) + today's headline rating → `data/reviews.csv`, `data/app_snapshot.csv`. Reviewer names are **not** stored. |
| `tag.py` | Gemini 3.8 Flash tags each review from the last 12 months with one theme, a severity (1–3), and a short issue summary → `data/tags.csv`. Cached and resumable — a stopped run picks up where it left off. |
| `themes.py` | The fixed theme taxonomy — 10 complaint categories + praise/other. Each theme is marked as `app` (fixable in code) or `ops` (cab/driver/service). |
| `metrics.py` | Monthly trend, rating per app version, theme impact (1–2★ reviews weighted by recency with 90-day half-life), developer reply stats. |
| `store.py` | Data I/O abstraction — loads/saves CSVs with proper dtypes. `DATA_DIR` env var overrides the default path. |
| `app.py` | Streamlit dashboard over `data/`. Date-range picker in the sidebar, four tabs with charts and tables. |
| `make_pdf.py` | Converts `report/recommendations.md` → styled PDF via headless Chrome. |

---

## Gemini Free Tier Notes

- The free tier allows **~20 calls/day** per model (~100 reviews per call).
- A stopped run **resumes** from `data/tags.csv` on the next execution — no work is lost.
- Override the model with the `GEMINI_MODEL` environment variable.

---

## Generate the PDF Report

```bash
python make_pdf.py                                         # uses defaults
python make_pdf.py report/recommendations.md report/out.pdf  # custom paths
```

> Requires Google Chrome installed at the default macOS path.

---

## License
Internal project — MoveInSync.
