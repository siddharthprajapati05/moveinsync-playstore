import pandas as pd

from scrape import clean, merge
from store import REVIEW_COLS, load_reviews


def raw(rid, at, content="ok", score=5, version="10.42.4"):
    return {"reviewId": rid, "userName": "Someone", "userImage": "http://x/img", "content": content,
            "score": score, "thumbsUpCount": 0, "at": pd.Timestamp(at).to_pydatetime(),
            "reviewCreatedVersion": version, "appVersion": version,
            "replyContent": None, "repliedAt": None}


def test_clean_drops_personal_fields():
    df = clean([raw("a", "2026-10-01")])
    assert list(df.columns) == REVIEW_COLS


def test_merge_dedupes_and_newer_fetch_wins():
    old = clean([raw("a", "2026-10-01", content="bad", score=1), raw("b", "2026-09-01")])
    new = clean([raw("a", "2026-10-01", content="fixed now", score=4), raw("c", "2026-10-05")])
    out = merge(old, new)
    assert list(out["reviewId"]) == ["c", "a", "b"]  # newest first, no duplicates
    assert out.set_index("reviewId").loc["a", "score"] == 4


def test_versions_round_trip_as_strings(tmp_path):
    clean([raw("a", "2026-10-01", version="10.40")]).to_csv(tmp_path / "reviews.csv", index=False)
    df = load_reviews(tmp_path)
    assert df.loc[0, "reviewCreatedVersion"] == "10.40"
    assert df["at"].dtype.kind == "M"


def test_load_reviews_missing_file_is_empty(tmp_path):
    df = load_reviews(tmp_path)
    assert df.empty and list(df.columns) == REVIEW_COLS
