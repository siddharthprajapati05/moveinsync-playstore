# Raising MoveInSync's Play Store rating

Employee app `com.moveinsync.ets` · Google Play (India, English) · data to 9 Oct 2026 · prepared 11 Oct 2026

## TL;DR

- **The headline 4.64★ hides the problem.** 85% of the 114,872 ratings are 5★, mostly with no written review. The people who *write* a review are much unhappier: in the last 12 months written reviews average **3.83★, and 27% are 1–2★** (3.80★ / 29% in the last 90 days). The current release, 12.19.0, sits at **3.58★**.
- **At least half of the anger is fixable inside the app.** 52% of 1–2★ reviews are about app issues: bugs and intrusive screens (21%), login/OTP and sessions (13%), booking (10%) and tracking (7%). Another 21% are ops issues like routing, late cabs and the helpdesk. The remaining 26% are vague, mostly one-liners like "worst app".
- **Do first:** start replying to reviews again (it went from 98% in 2023 to 0.8% in 2026), strip the blocking popups out of 12.19, and make sure an employee can never lose their cab number and OTP at pickup.

## What's pulling the rating down (1–2★ reviews, last 12 months, n = 769)

| Theme | Fix owner | Share of 1–2★ | Trend (quarterly share) |
|---|---|---|---|
| App bugs, crashes, intrusive screens | App | 20.7% | 19% → 18% → 17% → **28%** → 24%* |
| Login, OTP, forced logouts | App | 12.5% | 17% → 14% → 14% → 6% → 12%* |
| Booking can't be done or changed | App | 9.6% | flat, about 10% |
| Live tracking / ETA wrong | App | 7.0% | flat, about 7% |
| Routing, late cabs, helpdesk, drivers, safety | Ops | 21.4% | flat |
| Vague or uncategorised ("worst app", UI redesign) | — | 26.0% | 129 of 200 are ≤4 words |

\*Quarters run Q4 2025 → Q4 2026; Q4 2026 is only to 9 Oct (n = 25), so read its value loosely.

The 2026 releases are getting worse, not better. The bug share jumped in Q3 2026. The weakest versions with at least 30 reviews are 12.14.0 (June 2026, 3.37★), 12.16.1 (3.53★) and the current 12.19.0 (3.58★, 35% 1–2★).

## Fixes, ranked

**1. Stop the app getting in the way (App · Eng).** This is 21% of 1–2★ and rising.

- Users report a full-screen banner on every launch, a ride-rating popup that blocks route details, a policy agreement that keeps reappearing, and crashes on *Track*.
- Quotes: *"Loading and showing full screen banner on every app launch is terrible. I am opening the app to see my cab timing."* · *"please remove your annoying popups… I am not able to schedule my ride."*
- **Fix:** no blocking screen before the trip card; the rating prompt becomes a dismissable card; the agreement is asked once per version; fix the crash on *Track*.
- **First step tomorrow:** pull Android Vitals (crash and ANR) for 12.14–12.19, and list every modal shown on launch.
- **Success:** the bug theme drops below 15% of 1–2★, and 12.20 rates ≥ 4.0★ in written reviews.

**2. Never lose the trip at the kerb (App · Eng).** This is 13% of 1–2★, plus 24 reviews about losing the OTP or cab details at pickup.

- Users get logged out ("session expired") while the cab waits, OTPs don't arrive, and the app forgets the driver and OTP when the signal drops.
- Quote: *"when cab is waiting for you and you are in hurry, you will be logged out with no access to cab number/otp/call option to helpdesk."*
- **Fix:** never force a logout on a day with a booked trip; cache today's trip card (cab number, OTP, driver phone, pickup time) offline and in a persistent notification; when an OTP fails, say whether the number or email is registered.
- **First step tomorrow:** count forced logouts on trip days in the auth logs, and ship the offline trip card.
- **Success:** the login/OTP theme drops below 6% of 1–2★.

**3. Undo the booking regression (App · Product).** This is 10% of 1–2★.

- The July 2026 redesign made booking a two-step flow, and users think they've booked when they haven't.
- Users also can't see the month's schedule, have to cancel a booking to edit it, and are blocked from booking or scanning the QR code when location accuracy is low.
- Quote: *"Booking a shuttle is now a 2 step process… I thought I had booked a cab while I hadn't."*
- **First step tomorrow:** compare the booking funnel (start → confirmed) before and after the July release.
- **Fix:** a single confirm step with a clear "Booked ✓" state, a month view, edit in place, and no location gate for booking.
- **Success:** the booking theme drops below 6%, and the booking completion rate recovers to its pre-July level.

**4. Make tracking trustworthy (App · Eng).** This is 7% of 1–2★. The most-upvoted complaint has 10 👍.

- The map re-zooms every 30 seconds to show the destination, GPS and ETA are off, and co-passengers aren't visible.
- **Fix:** keep the user's zoom while they're waiting, add an "X min · Y km away" line, and fix the sequence mismatch between the employee app and the driver app.
- **Success:** the tracking theme drops below 4%.

**5. Send ops complaints back to the people who own them (Ops · Account managers).** This is 21% of 1–2★.

- Complaints include pickups from the same building scheduled 5 minutes apart, cabs 30–40 minutes late, and a helpdesk that is "always busy" or hangs up. These hit *our* rating even though the client's transport desk owns them.
- **First step tomorrow:** send each enterprise client a monthly theme report from the dashboard.
- **Success:** the ops themes drop below 15% of 1–2★.

## Quick wins (this week)

- **Reply to reviews again.** The reply rate went 98% (2023) → 37% (2024) → 4% (2025) → 0.8% (2026), and the last reply was on 18 Aug 2026. Reply to every 1–2★ review within 48 h, with the fix or a route to the helpdesk; templates follow the themes above. Play notifies the reviewer and shows the reply to everyone who reads the review.
- **Ask happy riders at the right moment.** Show Google's In-App Review prompt after a completed trip, with no "do you like us?" question first (Play policy). Remove the current blocking feedback popup: 20 recent 1–2★ reviews complain about it.

## How to keep checking

**Live dashboard:** link added after deploy. **Refresh:** `python run.py` pulls new reviews, tags them and prints this summary; once the 1,545 untagged 5★ reviews are cleared (about 16 calls, one day of free quota), a week of new reviews takes about one Gemini call.

## How I got there

- **Data:** I scraped all 24,314 public Play Store reviews (2014 → 9 Oct 2026) with `google-play-scraper`, plus today's rating and its star histogram. Reviewer names were not stored.
- **Tagging:** Gemini 3.8 Flash (free tier) tagged each review from the last 12 months with one of 12 themes, a severity and a one-line issue. It processes 100 reviews per call and resumes where it stopped.
- **Accuracy:** I hand-checked 50 random tags and agreed with **48 (96%)**. The check is in `report/tag_check.csv`.
- **Impact score:** each 1–2★ review counts once, weighted by recency with a 90-day half-life. Themes are then split into what the app team can fix vs ops.
- **Tools:** Python, pandas, Streamlit, Gemini API, headless Chrome for this PDF, and Claude Code as a pair-programmer. 24 automated tests.

## Assumptions

English reviews from the India store only. Star ratings without text can't be themed. The Gemini free tier allows 20 calls a day: every 1–4★ review from the last 12 months was tagged, and 1,545 five-star reviews were left untagged, which doesn't change the complaint shares. "Fix owner" is my judgement per theme. Success targets are starting points to calibrate after the first month.
