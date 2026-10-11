from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_renders_with_no_data(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=30)
    assert not at.exception
    assert at.warning


def test_app_renders_without_tags(tmp_path, monkeypatch):
    pd.DataFrame({"reviewId": ["r1"], "content": ["late cab"], "score": [1], "thumbsUpCount": [0],
                  "at": ["2026-10-01"], "reviewCreatedVersion": ["10.42"], "appVersion": ["10.42"],
                  "replyContent": [None], "repliedAt": [None]}).to_csv(tmp_path / "reviews.csv", index=False)
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    at = AppTest.from_file(APP).run(timeout=30)
    assert not at.exception
    assert any("python run.py" in i.value for i in at.info)
