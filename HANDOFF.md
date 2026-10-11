# Handoff — publish the repo + live dashboard

Everything is built, tested, and committed locally. What's left is putting it on GitHub, deploying the
dashboard, and adding the link to the README and the PDF. That takes about 15 minutes.

## What's in the repo

- `report/recommendations.pdf`: the deliverable (2 pages). Its source is `report/recommendations.md`.
- `app.py`: the Streamlit dashboard. It reads only the committed CSVs in `data/`, so **no secrets are
  needed to deploy it**.
- `run.py`: refreshes everything (scrape → Gemini tagging → metrics). See README.
- `.env` holds the Gemini API key. It is gitignored and **must never be committed**. You don't need it
  for publishing.

## 1. Push to GitHub

```bash
cd ~/Documents/moveinsync-playstore
git checkout main && git merge --ff-only feat/mvp     # skip if main already has everything
git ls-files | grep -c '^.env$'                       # must print 0
gh repo create moveinsync-playstore --public --source . --push
```

No `gh` CLI? Create an empty public repo on github.com, then run
`git remote add origin https://github.com/<you>/moveinsync-playstore.git && git push -u origin main`.

## 2. Deploy on Streamlit Community Cloud

1. Go to https://share.streamlit.io and sign in with GitHub.
2. **Create app** → **Deploy a public app from GitHub**.
3. Repository `<you>/moveinsync-playstore`, branch `main`, main file path `app.py`.
4. **Advanced settings**: Python 3.11 (anything from 3.9 to 3.12 works). Secrets: leave empty.
5. Click **Deploy**. The first build takes 2–4 minutes because it installs `requirements.txt`.

**Check:** the Overview tab should show **4.64★** for the Play Store rating, **3.79★** for the last 30
days and **3.80★** for the last 90 days. The Themes tab should list `app_bugs_crash` as the top app
theme.

## 3. Put the link in the README and the PDF

1. In `README.md`, replace `added after deploy` with the app URL.
2. In `report/recommendations.md`, under *How to keep checking*, replace `link added after deploy` with
   the URL.
3. Rebuild the PDF and push:

```bash
.venv/bin/python make_pdf.py          # needs Google Chrome installed (macOS path set in make_pdf.py)
git add README.md report/recommendations.md report/recommendations.pdf
git commit -m "docs: add live dashboard link" && git push
```

Open the PDF once to confirm it's still 2 pages.

## Later: refreshing the numbers

```bash
.venv/bin/python run.py     # needs GEMINI_API_KEY in .env
git add data/ && git commit -m "data: refresh" && git push    # the dashboard redeploys itself
```

## Known limits (also stated in the report)

- **Gemini free tier:** 20 calls a day per model, with 100 reviews per call. If the quota runs out
  mid-run, `run.py` stops cleanly and the next run resumes. 1,545 five-star reviews from the last
  12 months are still untagged. That doesn't change the complaint numbers.
- **Model:** `gemini-2.5-flash` is closed to new API keys, so the code uses `gemini-3.8-flash`. Override
  it with `GEMINI_MODEL` if that changes.
- **Scope:** English reviews from the India store only.
