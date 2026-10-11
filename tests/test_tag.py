import pandas as pd

from store import TAG_COLS
from tag import build_prompt, normalize, select_untagged, tag_batch
from themes import THEMES

NOW = pd.Timestamp("2026-10-11")


def test_select_skips_empty_old_and_tagged_worst_first():
    reviews = pd.DataFrame({
        "reviewId": ["new_high", "new_low", "empty", "old", "done", "blank"],
        "content": ["great app", "cab never came", None, "too old", "already tagged", "   "],
        "score": [5, 1, 1, 1, 2, 3],
        "at": pd.to_datetime(["2026-10-02", "2026-10-01", "2026-10-01", "2025-01-01",
                              "2026-10-01", "2026-10-01"]),
    })
    tags = pd.DataFrame({"reviewId": ["done"], "theme": ["other"], "severity": [1], "issue": [""]})
    assert list(select_untagged(reviews, tags, NOW)["reviewId"]) == ["new_low", "new_high"]


def test_normalize_drops_foreign_and_duplicate_ids_and_fixes_bad_values():
    items = [
        {"reviewId": "a", "theme": "cab_late_noshow", "severity": 3, "issue": "cab 40 min late"},
        {"reviewId": "a", "theme": "praise", "severity": 1, "issue": "duplicate"},
        {"reviewId": "zzz", "theme": "praise", "severity": 1, "issue": "not in batch"},
        {"reviewId": "b", "theme": "made_up_theme", "severity": "9", "issue": None},
        "garbage",
    ]
    out = normalize(items, {"a", "b", "c"}).set_index("reviewId")
    assert list(out.index) == ["a", "b"]
    assert out.loc["a", "theme"] == "cab_late_noshow"
    assert out.loc["b", "theme"] == "other"
    assert out.loc["b", "severity"] == 3
    assert out.loc["b", "issue"] == ""


def test_normalize_non_list_is_empty():
    out = normalize({"oops": 1}, {"a"})
    assert out.empty and list(out.columns) == TAG_COLS


def test_prompt_lists_every_theme_and_truncates_text():
    p = build_prompt(pd.DataFrame({"reviewId": ["a"], "score": [1], "content": ["x" * 2000]}))
    assert all(t in p for t in THEMES)
    assert "x" * 501 not in p


def test_tag_batch_retries_missing_once_then_marks_other():
    batch = pd.DataFrame({"reviewId": ["a", "b"], "score": [1, 2], "content": ["late cab", "crashes"]})
    prompts = []

    def fake(prompt):
        prompts.append(prompt)
        if len(prompts) == 1:
            return [{"reviewId": "a", "theme": "cab_late_noshow", "severity": 2, "issue": "late"}]
        return []

    out = tag_batch(batch, fake, pause=0).set_index("reviewId")
    assert len(prompts) == 2 and '"b"' in prompts[1] and '"a"' not in prompts[1]
    assert out.loc["a", "theme"] == "cab_late_noshow"
    assert out.loc["b", "theme"] == "other" and out.loc["b", "issue"] == "untagged"


# --- final-review fixes -------------------------------------------------------
from types import SimpleNamespace

import pytest
from google.genai import errors

import tag


def fake_client(fn):
    return SimpleNamespace(models=SimpleNamespace(generate_content=fn))


def test_call_gemini_raises_after_server_errors_instead_of_returning_empty():
    calls = []

    def boom(**kw):
        calls.append(kw)
        raise errors.ServerError(503, {"error": {"code": 503, "message": "overloaded", "status": "UNAVAILABLE"}})

    with pytest.raises(tag.CallFailed):
        tag.call_gemini(fake_client(boom), "p", sleep=lambda s: None)
    assert len(calls) == 4


def test_call_gemini_retries_bad_json_once_then_raises():
    calls = []

    def garbage(**kw):
        calls.append(kw)
        return SimpleNamespace(text="[{not json")

    with pytest.raises(tag.CallFailed):
        tag.call_gemini(fake_client(garbage), "p", sleep=lambda s: None)
    assert len(calls) == 2


def test_tag_batch_writes_nothing_when_the_call_fails():
    batch = pd.DataFrame({"reviewId": ["a"], "score": [1], "content": ["late cab"]})

    def dead(prompt):
        raise tag.CallFailed("down")

    with pytest.raises(tag.CallFailed):
        tag_batch(batch, dead, pause=0)


def test_model_comes_from_env_at_call_time(monkeypatch):
    seen = []

    def ok(**kw):
        seen.append(kw["model"])
        return SimpleNamespace(text="[]")

    monkeypatch.setenv("GEMINI_MODEL", "gemini-test-model")
    tag.call_gemini(fake_client(ok), "p", sleep=lambda s: None)
    assert seen == ["gemini-test-model"]
