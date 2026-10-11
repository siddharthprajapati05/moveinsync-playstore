"""Pull MoveInSync employee-app reviews + headline stats from Google Play into data/."""
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from store import REVIEW_COLS, data_dir, load_reviews

APP_ID, LANG, COUNTRY = "com.moveinsync.ets", "en", "in"


def clean(raw):
    """Scraper dicts -> DataFrame with only REVIEW_COLS (drops userName/userImage)."""
    df = pd.DataFrame(raw, columns=REVIEW_COLS)
    df["at"] = pd.to_datetime(df["at"])
    df["repliedAt"] = pd.to_datetime(df["repliedAt"])
    return df


def merge(existing, new):
    """Union on reviewId; the newer fetch wins (reviews can be edited). Newest first."""
    out = pd.concat([existing, new], ignore_index=True).drop_duplicates("reviewId", keep="last")
    return out.sort_values("at", ascending=False, ignore_index=True)


def fetch_new(known_ids, full=False):
    """Page newest-first; stop at the first page that is entirely already-saved (unless full)."""
    from google_play_scraper import Sort, reviews

    out, token = [], None
    while True:
        for attempt in range(3):
            try:
                page, token = reviews(APP_ID, lang=LANG, country=COUNTRY, sort=Sort.NEWEST,
                                      count=200, continuation_token=token)
                break
            except Exception as e:  # network hiccup / throttling
                print(f"  page failed ({e}); retry {attempt + 1}/3")
                time.sleep(5 * (attempt + 1))
        else:
            break
        out.extend(page)
        if len(out) % 2000 < 200:
            print(f"  fetched {len(out):,}")
        if not page or token is None or token.token is None:
            break
        if not full and all(r["reviewId"] in known_ids for r in page):
            break
        time.sleep(1)
    return out


def snapshot():
    """Headline Play Store stats right now — one row per run = rating history."""
    from google_play_scraper import app

    a = app(APP_ID, lang=LANG, country=COUNTRY)
    h = a.get("histogram") or [None] * 5
    row = {"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "score": a.get("score"),
           "ratings": a.get("ratings"), "reviews": a.get("reviews"),
           "installs": a.get("realInstalls"), "version": a.get("version")}
    row.update({f"stars_{i + 1}": h[i] for i in range(5)})
    return row


def run(d=None, full=False):
    d = Path(d or data_dir())
    d.mkdir(parents=True, exist_ok=True)
    existing = load_reviews(d)
    new = clean(fetch_new(set(existing["reviewId"]), full=full))
    merged = merge(existing, new)
    merged.to_csv(d / "reviews.csv", index=False)
    snap = d / "app_snapshot.csv"
    pd.DataFrame([snapshot()]).to_csv(snap, mode="a", header=not snap.exists(), index=False)
    print(f"reviews: {len(merged):,} total ({len(merged) - len(existing):,} new)")
    return merged
