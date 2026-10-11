"""Rating metrics as pure functions over the reviews/tags DataFrames."""
from pathlib import Path

import pandas as pd

from store import data_dir, load_reviews, load_snapshots, load_tags
from themes import kind

LOW = 2  # 1–2★ counts as a low rating
HALF_LIFE_DAYS = 90


def window(reviews, now, days):
    return reviews[reviews["at"] >= now - pd.Timedelta(days=days)]


def _mean(df):
    return round(float(df["score"].mean()), 2) if len(df) else None


def monthly(reviews):
    cols = ["month", "reviews", "mean_stars", "pct_low"]
    if reviews.empty:
        return pd.DataFrame(columns=cols)
    g = reviews.assign(month=reviews["at"].dt.to_period("M").astype(str),
                       low=reviews["score"] <= LOW).groupby("month")
    out = pd.DataFrame({"reviews": g.size(), "mean_stars": g["score"].mean().round(2),
                        "pct_low": (g["low"].mean() * 100).round(1)})
    return out.reset_index()[cols]


def by_version(reviews, min_n=30):
    cols = ["version", "reviews", "mean_stars", "pct_low", "first_seen"]
    df = reviews.assign(version=reviews["reviewCreatedVersion"].fillna(reviews["appVersion"]))
    df = df.dropna(subset=["version"])
    if df.empty:
        return pd.DataFrame(columns=cols)
    g = df.assign(low=df["score"] <= LOW).groupby("version")
    out = pd.DataFrame({"reviews": g.size(), "mean_stars": g["score"].mean().round(2),
                        "pct_low": (g["low"].mean() * 100).round(1), "first_seen": g["at"].min()})
    out = out[out["reviews"] >= min_n].sort_values("first_seen")
    return out.reset_index()[cols]


def recency_weight(age_days):
    return 0.5 ** (age_days / HALF_LIFE_DAYS)


def theme_table(reviews, tags, now):
    """Rank themes by impact = sum of recency weights of their 1–2★ reviews."""
    cols = ["theme", "kind", "reviews", "low_reviews", "pct_of_low", "mean_stars", "impact"]
    df = reviews.merge(tags[["reviewId", "theme"]], on="reviewId", how="inner")
    if df.empty:
        return pd.DataFrame(columns=cols)
    df["low"] = df["score"] <= LOW
    df["w"] = recency_weight((now - df["at"]).dt.days.clip(lower=0)) * df["low"]
    g = df.groupby("theme")
    out = pd.DataFrame({"reviews": g.size(), "low_reviews": g["low"].sum(),
                        "mean_stars": g["score"].mean().round(2), "impact": g["w"].sum().round(1)})
    total_low = int(df["low"].sum())
    out["pct_of_low"] = (out["low_reviews"] / total_low * 100).round(1) if total_low else 0.0
    out = out.reset_index()
    out["kind"] = out["theme"].map(kind)
    return out[cols].sort_values("impact", ascending=False, ignore_index=True)


def quotes(reviews, tags, theme, n=5):
    """Most-upvoted, then newest, 1–2★ reviews for one theme — evidence for the report."""
    ids = tags.loc[tags["theme"] == theme, "reviewId"]
    df = reviews[reviews["reviewId"].isin(ids) & (reviews["score"] <= LOW)]
    df = df.sort_values(["thumbsUpCount", "at"], ascending=False)
    return df[["at", "score", "thumbsUpCount", "content"]].head(n)


def replies(reviews):
    if reviews.empty:
        return {"reply_rate": 0.0, "reply_rate_low": 0.0, "median_reply_hours": None}
    replied = reviews["replyContent"].notna()
    low = reviews["score"] <= LOW
    lag = (reviews.loc[replied, "repliedAt"] - reviews.loc[replied, "at"]).dt.total_seconds() / 3600
    return {"reply_rate": round(float(replied.mean()) * 100, 1),
            "reply_rate_low": round(float(replied[low].mean()) * 100, 1) if low.any() else 0.0,
            "median_reply_hours": round(float(lag.median()), 1) if len(lag) else None}


def summary(reviews, tags, snaps, now):
    snap = snaps.iloc[-1].to_dict() if len(snaps) else {}
    last30, last90 = window(reviews, now, 30), window(reviews, now, 90)
    themes = theme_table(window(reviews, now, 365), tags, now)
    top = [(t.theme, t.pct_of_low) for t in themes[themes["kind"] != "-"].head(3).itertuples()]
    return {"snapshot_date": snap.get("date"),
            "play_rating": round(float(snap["score"]), 2) if snap else None,
            "play_ratings_count": int(snap["ratings"]) if snap else None,
            "mean_30d": _mean(last30), "n_30d": len(last30),
            "mean_90d": _mean(last90), "n_90d": len(last90),
            "pct_low_90d": round(float((last90["score"] <= LOW).mean()) * 100, 1) if len(last90) else None,
            "top_themes": top}


def format_summary(s):
    count = f"{s['play_ratings_count']:,}" if s["play_ratings_count"] else "?"
    lines = [f"Play Store rating: {s['play_rating']}★ ({count} ratings, {s['snapshot_date']})",
             f"Last 30 days: {s['mean_30d']}★ avg over {s['n_30d']:,} reviews",
             f"Last 90 days: {s['mean_90d']}★ avg over {s['n_90d']:,} reviews, {s['pct_low_90d']}% are 1–2★",
             "Top complaint themes (share of 1–2★, last 12 months):"]
    lines += [f"  - {theme}: {pct}%" for theme, pct in s["top_themes"]]
    return "\n".join(lines)


def write_all(d=None, now=None):
    d = Path(d or data_dir())
    now = now if now is not None else pd.Timestamp.now()
    reviews, tags, snaps = load_reviews(d), load_tags(d), load_snapshots(d)
    year = window(reviews, now, 365)
    out = d / "metrics"
    out.mkdir(exist_ok=True)
    monthly(reviews).to_csv(out / "monthly.csv", index=False)
    by_version(year).to_csv(out / "versions.csv", index=False)
    theme_table(year, tags, now).to_csv(out / "themes.csv", index=False)
    return summary(reviews, tags, snaps, now)
