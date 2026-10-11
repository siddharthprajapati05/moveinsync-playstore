"""The fixed review themes and whether engineering can fix them in the app."""
THEMES = {
    "login_otp": "login, registration, OTP/verification, account problems",
    "booking_fails": "can't book/cancel/change a ride, booking cutoff, roster/shift problems",
    "cab_late_noshow": "cab late or never came, long waits, wrong pickup time",
    "driver_behaviour": "rude or unsafe driver, driver misconduct, driver calls",
    "tracking_eta": "live tracking wrong, GPS/ETA inaccurate, can't see the cab",
    "routing": "long routes, too many pickups, wrong pickup/drop location",
    "app_bugs_crash": "crashes, freezes, slow, bugs after an update, broken screens",
    "notifications": "missing, late or spammy notifications/SMS",
    "support_unresolved": "complaint or feedback ignored, helpline doesn't respond",
    "safety_sos": "safety concern, SOS, night drops, escort",
    "praise": "purely positive review",
    "other": "none of the above",
}
APP_THEMES = {"login_otp", "booking_fails", "tracking_eta", "app_bugs_crash", "notifications"}
OPS_THEMES = {"cab_late_noshow", "driver_behaviour", "routing", "support_unresolved", "safety_sos"}


def kind(theme):
    return "app" if theme in APP_THEMES else "ops" if theme in OPS_THEMES else "-"
