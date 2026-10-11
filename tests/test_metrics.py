import pandas as pd

import metrics

NOW = pd.Timestamp("2026-10-11")


def rv(rows):
    df = pd.DataFrame(rows, columns=["reviewId", "score", "at", "reviewCreatedVersion",
                                     "appVersion", "replyContent", "repliedAt"])
    df["at"] = pd.to_datetime(df["at"])
    df["repliedAt"] = pd.to_datetime(df["repliedAt"])
    return df


REVIEWS = rv([
    ("r1", 1, "2026-10-01", "10.42", "10.42", "Sorry!", "2026-10-02"),
    ("r2", 5, "2026-10-05", "10.42", "10.42", None, None),
    ("r3", 2, "2026-09-10", "10.41", "10.41", None, None),
    ("r4", 1, "2026-03-01", None, None, None, None),
])
TAGS = pd.DataFrame({"reviewId": ["r1", "r2", "r3", "r4"],
                     "theme": ["cab_late_noshow", "praise", "app_bugs_crash", "app_bugs_crash"],
                     "severity": [2, 1, 2, 2], "issue": ["", "", "", ""]})


def test_monthly():
    m = metrics.monthly(REVIEWS).set_index("month")
    assert m.loc["2026-10", "reviews"] == 2
    assert m.loc["2026-10", "mean_stars"] == 3.0
    assert m.loc["2026-10", "pct_low"] == 50.0


def test_by_version_drops_missing_and_small():
    assert metrics.by_version(REVIEWS, min_n=1)["version"].tolist() == ["10.41", "10.42"]
    assert metrics.by_version(REVIEWS, min_n=2)["version"].tolist() == ["10.42"]


def test_recency_weight_halves_every_90_days():
    assert metrics.recency_weight(0) == 1.0
    assert metrics.recency_weight(90) == 0.5


def test_theme_table_impact_and_shares():
    # bugs: two low reviews 31 and 224 days old (0.79 + 0.18 ≈ 1.0); cab: one, 10 days old (0.93)
    t = metrics.theme_table(REVIEWS, TAGS, NOW).set_index("theme")
    assert list(t.index) == ["app_bugs_crash", "cab_late_noshow", "praise"]
    assert t.loc["app_bugs_crash", "low_reviews"] == 2
    assert t.loc["app_bugs_crash", "pct_of_low"] == 66.7
    assert t.loc["app_bugs_crash", "kind"] == "app"
    assert t.loc["cab_late_noshow", "kind"] == "ops"
    assert t.loc["cab_late_noshow", "impact"] == 0.9
    assert t.loc["praise", "impact"] == 0.0


def test_quotes_picks_most_upvoted_low_star():
    r = REVIEWS.assign(content=["a", "b", "c", "d"], thumbsUpCount=[1, 50, 2, 9])
    assert metrics.quotes(r, TAGS, "app_bugs_crash")["content"].tolist() == ["d", "c"]


def test_replies():
    r = metrics.replies(REVIEWS)
    assert r == {"reply_rate": 25.0, "reply_rate_low": 33.3, "median_reply_hours": 24.0}


def test_empty_frames_do_not_crash():
    e = REVIEWS.iloc[0:0]
    assert metrics.monthly(e).empty
    assert metrics.by_version(e).empty
    assert metrics.theme_table(e, TAGS, NOW).empty
    assert metrics.replies(e)["reply_rate"] == 0.0


def test_write_all_writes_files_and_summary(tmp_path):
    REVIEWS.assign(content="x", thumbsUpCount=0).to_csv(tmp_path / "reviews.csv", index=False)
    TAGS.to_csv(tmp_path / "tags.csv", index=False)
    pd.DataFrame([{"date": "2026-10-11", "score": 4.64, "ratings": 114866}]).to_csv(
        tmp_path / "app_snapshot.csv", index=False)
    s = metrics.write_all(tmp_path, NOW)
    for f in ["monthly", "versions", "themes"]:
        assert (tmp_path / "metrics" / f"{f}.csv").exists()
    assert s["play_rating"] == 4.64
    assert s["n_30d"] == 2  # r1 + r2; r3 is 31 days old
    assert s["top_themes"][0][0] == "app_bugs_crash"
    assert "4.64" in metrics.format_summary(s)
