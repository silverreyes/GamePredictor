"""Feature column definitions and rolling window configuration.

WARNING: Do NOT modify during autoresearch experiment loop (CLAUDE.md).
Only models/train.py may be modified during experiments.
"""

# Rolling features computed per team per season using shift(1) + expanding mean
ROLLING_FEATURES = [
    "off_epa_per_play",      # Offensive EPA/play
    "def_epa_per_play",      # Defensive EPA/play (allowed)
    "point_diff",            # Point differential
    "turnovers_committed",   # Turnovers committed by team
    "turnovers_forced",      # Turnovers forced (opponent committed)
    "turnover_diff",         # Turnover differential (forced - committed)
    "win",                   # Win (1) / Loss (0) / Tie (0.5)
]

# Situational features (direct lookup, no rolling)
SITUATIONAL_FEATURES = [
    "is_home",          # Always 1 in home-perspective table (feature is implicit)
    "home_rest_days",   # Days since home team's last game
    "away_rest_days",   # Days since away team's last game
    "week",             # Week of season (1-18)
    "div_game",         # 1 if divisional game, 0 otherwise
]

# Target variable (for reference, not used as feature)
TARGET = "home_win"  # 1 if home team won, 0 otherwise, None for tie

# Columns that must NEVER be features (CLAUDE.md)
FORBIDDEN_FEATURES = ["result", "home_score", "away_score"]

# Play types used for EPA calculation (pass and run only)
EPA_PLAY_TYPES = ["pass", "run"]
