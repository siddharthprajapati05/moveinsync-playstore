"""Tag reviews with one theme each using Gemini (free tier). Cached in data/tags.csv, resumable."""
import json
import os
import time
from pathlib import Path

import pandas as pd
from pydantic import BaseModel

from store import ROOT, TAG_COLS, data_dir, load_reviews, load_tags
from themes import THEMES

DEFAULT_MODEL = "gemini-3.8-flash"  # override with GEMINI_MODEL (env or .env)
BATCH = 100
PACE_SECONDS = 7.5  # <= 8 calls/min on the free tier
WINDOW_DAYS = 365
MAX_CHARS = 500

PROMPT = """You label Google Play reviews of MoveInSync, an employee commute app: employees book office cab rides for their shift, get a pickup time, track the cab live, board with an OTP, and raise complaints.

For EACH review return one object {{"reviewId", "theme", "severity", "issue"}}.
theme — exactly one of:
{themes}
Pick the single main complaint. Use "praise" only for purely positive reviews, "other" if nothing fits.
severity — 1 = minor annoyance, 2 = a ride was affected, 3 = missed shift, safety risk, or app unusable.
issue — the concrete problem in at most 12 plain words (e.g. "cab 40 min late, driver not answering").

Reviews (JSON):
{reviews}"""


class TagOut(BaseModel):
    reviewId: str
    theme: str
    severity: int
    issue: str


class DailyQuotaHit(Exception):
    pass


class CallFailed(Exception):
    """Gemini never answered usefully — leave the batch untagged so the next run retries it."""


def current_model():
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def select_untagged(reviews, tags, now):
    """Reviews in the window with text and no tag yet — worst stars first, then newest."""
    text = reviews["content"].fillna("").str.strip()
    mask = ((reviews["at"] >= now - pd.Timedelta(days=WINDOW_DAYS)) & (text != "")
            & ~reviews["reviewId"].isin(tags["reviewId"]))
    return reviews[mask].sort_values(["score", "at"], ascending=[True, False])


def build_prompt(batch):
    items = [{"reviewId": r.reviewId, "stars": int(r.score), "text": str(r.content)[:MAX_CHARS]}
             for r in batch.itertuples()]
    themes = "\n".join(f"- {k}: {v}" for k, v in THEMES.items())
    return PROMPT.format(themes=themes, reviews=json.dumps(items, ensure_ascii=False))


def normalize(items, batch_ids):
    """One row per id in this batch; unknown theme -> other; severity clamped to 1..3."""
    rows = {}
    for it in items if isinstance(items, list) else []:
        if not isinstance(it, dict):
            continue
        rid = it.get("reviewId")
        if rid not in batch_ids or rid in rows:
            continue
        theme = it.get("theme") if it.get("theme") in THEMES else "other"
        try:
            sev = min(3, max(1, int(it.get("severity", 1))))
        except (TypeError, ValueError):
            sev = 1
        rows[rid] = {"reviewId": rid, "theme": theme, "severity": sev,
                     "issue": str(it.get("issue") or "")[:120]}
    return pd.DataFrame(list(rows.values()), columns=TAG_COLS)


def tag_batch(batch, call, pause=PACE_SECONDS):
    """Tag one batch; ids the model skipped are retried once, then marked other/untagged."""
    ids = set(batch["reviewId"])
    got = normalize(call(build_prompt(batch)), ids)
    missing = batch[~batch["reviewId"].isin(got["reviewId"])]
    if len(missing):
        time.sleep(pause)
        got = pd.concat([got, normalize(call(build_prompt(missing)), set(missing["reviewId"]))],
                        ignore_index=True)
    still = sorted(ids - set(got["reviewId"]))
    filler = pd.DataFrame({"reviewId": still, "theme": "other", "severity": 1, "issue": "untagged"},
                          columns=TAG_COLS)
    return pd.concat([got, filler], ignore_index=True)


def call_gemini(client, prompt, sleep=time.sleep):
    from google.genai import errors, types

    cfg = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=list[TagOut], temperature=0,
        thinking_config=types.ThinkingConfig(thinking_budget=0))
    bad_json = 0
    for attempt in range(4):
        try:
            resp = client.models.generate_content(model=current_model(), contents=prompt, config=cfg)
            return json.loads(resp.text or "[]")
        except json.JSONDecodeError:
            bad_json += 1
            if bad_json > 1:
                break
            sleep(PACE_SECONDS)
        except errors.APIError as e:
            if e.code == 429 and "PerDay" in str(e):
                raise DailyQuotaHit(str(e)) from e
            if e.code in (429, 500, 503):
                sleep(15 * 2 ** attempt)
                continue
            raise
    raise CallFailed("Gemini gave no usable answer after retries")


def run(d=None, limit=None):
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    if not os.environ.get("GEMINI_API_KEY"):
        print("GEMINI_API_KEY not set (.env) — skipping tagging")
        return
    from google import genai

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    d = Path(d or data_dir())
    todo = select_untagged(load_reviews(d), load_tags(d), pd.Timestamp.now())
    if limit:
        todo = todo.head(limit)
    path = d / "tags.csv"
    print(f"tagging {len(todo):,} reviews with {current_model()}, {BATCH} per call")
    for i in range(0, len(todo), BATCH):
        batch = todo.iloc[i:i + BATCH]
        try:
            out = tag_batch(batch, lambda p: call_gemini(client, p))
        except DailyQuotaHit:
            print("daily Gemini quota reached — re-run later; it resumes from data/tags.csv")
            break
        except CallFailed as e:
            print(f"{e} — stopping; re-run later, untagged reviews are retried")
            break
        out.to_csv(path, mode="a", header=not path.exists(), index=False)
        print(f"  {i + len(batch):,}/{len(todo):,}")
        time.sleep(PACE_SECONDS)
