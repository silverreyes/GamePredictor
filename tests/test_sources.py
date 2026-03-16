"""Tests for data/sources.py constants and functions."""


def test_normalize_team_abbrev_oak():
    from data.sources import normalize_team_abbrev
    assert normalize_team_abbrev("OAK") == "LV"


def test_normalize_team_abbrev_sd():
    from data.sources import normalize_team_abbrev
    assert normalize_team_abbrev("SD") == "LAC"


def test_normalize_team_abbrev_stl():
    from data.sources import normalize_team_abbrev
    assert normalize_team_abbrev("STL") == "LA"


def test_normalize_team_abbrev_wsh():
    from data.sources import normalize_team_abbrev
    assert normalize_team_abbrev("WSH") == "WAS"


def test_normalize_team_abbrev_passthrough():
    from data.sources import normalize_team_abbrev
    assert normalize_team_abbrev("KC") == "KC"


def test_curated_pbp_columns_contains_required():
    from data.sources import CURATED_PBP_COLUMNS
    for col in ["epa", "game_id", "play_id", "posteam", "defteam"]:
        assert col in CURATED_PBP_COLUMNS, f"{col} missing from CURATED_PBP_COLUMNS"


def test_curated_schedule_columns_contains_required():
    from data.sources import CURATED_SCHEDULE_COLUMNS
    for col in ["game_id", "home_team", "away_team", "home_score"]:
        assert col in CURATED_SCHEDULE_COLUMNS, f"{col} missing from CURATED_SCHEDULE_COLUMNS"


def test_expected_reg_season_games_2019():
    from data.sources import EXPECTED_REG_SEASON_GAMES
    assert EXPECTED_REG_SEASON_GAMES[2019] == 256


def test_expected_reg_season_games_2021():
    from data.sources import EXPECTED_REG_SEASON_GAMES
    assert EXPECTED_REG_SEASON_GAMES[2021] == 272


def test_expected_reg_season_games_length():
    from data.sources import EXPECTED_REG_SEASON_GAMES
    assert len(EXPECTED_REG_SEASON_GAMES) == 20
