"""Where the data lives and how to load it. DATA_DIR env var overrides (used by tests)."""
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
REVIEW_COLS = ["reviewId", "content", "score", "thumbsUpCount", "at",
               "reviewCreatedVersion", "appVersion", "replyContent", "repliedAt"]
TAG_COLS = ["reviewId", "theme", "severity", "issue"]
_STR = {"reviewId": str, "content": str, "reviewCreatedVersion": str, "appVersion": str,
        "replyContent": str}


def data_dir():
    return Path(os.environ.get("DATA_DIR", ROOT / "data"))


def load_reviews(d=None):
    p = Path(d or data_dir()) / "reviews.csv"
    if not p.exists():
        empty = pd.DataFrame(columns=REVIEW_COLS)
        return empty.astype({"at": "datetime64[ns]", "repliedAt": "datetime64[ns]"})
    df = pd.read_csv(p, dtype=_STR)
    for c in ("at", "repliedAt"):  # explicit: an all-empty repliedAt column must still be datetime
        df[c] = pd.to_datetime(df[c])
    return df


def load_tags(d=None):
    p = Path(d or data_dir()) / "tags.csv"
    if not p.exists():
        return pd.DataFrame(columns=TAG_COLS)
    return pd.read_csv(p, dtype={"reviewId": str}).drop_duplicates("reviewId", keep="last")


def load_snapshots(d=None):
    p = Path(d or data_dir()) / "app_snapshot.csv"
    return pd.read_csv(p) if p.exists() else pd.DataFrame()
