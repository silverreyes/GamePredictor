"""NFL data source constants and mappings."""

# Team abbreviation normalization (CLAUDE.md: must be in data/sources.py)
TEAM_ABBREV_MAP: dict[str, str] = {
    "OAK": "LV",
    "SD": "LAC",
    "STL": "LA",
    "WSH": "WAS",
}

# All team columns that need normalization
TEAM_COLUMNS_PBP = ["home_team", "away_team", "posteam", "defteam"]
TEAM_COLUMNS_SCHEDULE = ["home_team", "away_team"]


def normalize_team_abbrev(abbrev: str) -> str:
    """Map historical team abbreviations to current canonical form."""
    return TEAM_ABBREV_MAP.get(abbrev, abbrev)


# Curated PBP columns (~35 columns from the 370+ available)
CURATED_PBP_COLUMNS: list[str] = [
    "play_id", "game_id", "old_game_id", "season", "season_type", "week", "game_date",
    "home_team", "away_team", "posteam", "posteam_type", "defteam",
    "down", "ydstogo", "yardline_100", "quarter_seconds_remaining",
    "half_seconds_remaining", "game_seconds_remaining", "game_half",
    "play_type", "yards_gained", "rush_attempt", "pass_attempt",
    "complete_pass", "incomplete_pass", "interception", "fumble_lost",
    "sack", "touchdown", "safety",
    "epa", "wp", "wpa",
    "score_differential", "posteam_score", "defteam_score",
    "total_home_score", "total_away_score",
    "location",
]

# Curated schedule columns
CURATED_SCHEDULE_COLUMNS: list[str] = [
    "game_id", "season", "game_type", "week", "gameday", "weekday", "gametime",
    "away_team", "away_score", "home_team", "home_score",
    "location", "result", "total", "overtime",
    "away_rest", "home_rest", "div_game",
    "roof", "surface",
]

# Expected regular season game counts per season (CONTEXT.md locked decision)
# 256 games for 16-game seasons (2005-2020), 272 for 17-game seasons (2021-2024)
EXPECTED_REG_SEASON_GAMES: dict[int, int] = {
    year: 256 if year <= 2020 else 272
    for year in range(2005, 2025)
}
