"""Streamlit dashboard: 'How are our Play Store ratings?' for the MoveInSync employee app."""
import pandas as pd
import streamlit as st

import metrics
from store import load_reviews, load_snapshots, load_tags
from themes import THEMES

st.set_page_config(page_title="MoveInSync · Play Store ratings", layout="wide")
st.title("MoveInSync employee app — Play Store ratings")

reviews, tags, snaps = load_reviews(), load_tags(), load_snapshots()
if reviews.empty:
    st.warning("No reviews yet — run `python run.py` first.")
    st.stop()

last = reviews["at"].max()
sel = st.sidebar.date_input("Reviews from / to", ((last - pd.Timedelta(days=365)).date(), last.date()))
if len(sel) != 2:
    st.stop()
r = reviews[(reviews["at"].dt.date >= sel[0]) & (reviews["at"].dt.date <= sel[1])]
st.sidebar.caption(f"{len(r):,} reviews in range · data as of {last:%d %b %Y}")

overview, themes_tab, versions_tab, replies_tab = st.tabs(["Overview", "Themes", "Versions", "Replies"])

with overview:
    c = st.columns(4)
    if len(snaps):
        s = snaps.iloc[-1]
        c[0].metric("Play Store rating", f"{s['score']:.2f}★", help=f"{int(s['ratings']):,} ratings · {s['date']}")
    for col, days in ((c[1], 30), (c[2], 90)):
        w = metrics.window(reviews, last, days)
        col.metric(f"Avg stars, last {days} days", f"{w['score'].mean():.2f}★" if len(w) else "–",
                   help=f"{len(w):,} reviews")
    c[3].metric("1–2★ share in range", f"{(r['score'] <= metrics.LOW).mean() * 100:.0f}%" if len(r) else "–")
    m = metrics.monthly(r)
    st.subheader("Average stars by month")
    st.line_chart(m, x="month", y="mean_stars", x_label="Month", y_label="Avg stars")
    st.subheader("Reviews per month")
    st.bar_chart(m, x="month", y="reviews", x_label="Month", y_label="Reviews", sort=False)
    st.subheader("Star mix in range")
    mix = r["score"].value_counts().reindex(range(1, 6), fill_value=0).rename_axis("stars").reset_index(name="reviews")
    st.bar_chart(mix, x="stars", y="reviews", x_label="Stars", y_label="Reviews", sort=False)

with themes_tab:
    if tags.empty:
        st.info("No tags yet — run `python run.py` with GEMINI_API_KEY set.")
    else:
        t = metrics.theme_table(r, tags, last)
        st.caption("Impact = 1–2★ reviews weighted by recency (half-life 90 days). "
                   "app = fixable in the app · ops = cab/driver/service.")
        st.bar_chart(t, x="theme", y="impact", x_label="Impact", y_label="Theme",
                     horizontal=True, sort="-impact")
        st.dataframe(t, hide_index=True)
        for theme in t[t["kind"] != "-"]["theme"].head(5):
            with st.expander(f"{theme} — {THEMES[theme]}"):
                for q in metrics.quotes(r, tags, theme).itertuples():
                    st.markdown(f"**{q.score}★** · {q.at:%d %b %Y} · 👍 {q.thumbsUpCount}  \n> {q.content}")

with versions_tab:
    v = metrics.by_version(r)
    if v.empty:
        st.info("Not enough reviews per app version in this range (min 30).")
    else:
        st.caption("Versions in release order (first review seen). Only versions with ≥30 reviews.")
        st.bar_chart(v, x="version", y="mean_stars", x_label="App version", y_label="Avg stars", sort=False)
        st.dataframe(v, hide_index=True)

with replies_tab:
    rep = metrics.replies(r)
    c = st.columns(3)
    c[0].metric("Reviews with a developer reply", f"{rep['reply_rate']}%")
    c[1].metric("1–2★ reviews with a reply", f"{rep['reply_rate_low']}%")
    c[2].metric("Median time to reply",
                f"{rep['median_reply_hours']} h" if rep["median_reply_hours"] is not None else "–")
