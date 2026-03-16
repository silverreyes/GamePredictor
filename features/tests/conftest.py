"""Shared fixtures for feature pipeline tests.

Provides synthetic PBP and schedule DataFrames with known values
for deterministic testing of rolling computations and leakage detection.
"""
import pytest
import pandas as pd
import numpy as np


@pytest.fixture
def synthetic_schedule():
    """Synthetic schedule for one team (KC) across 4 games in one season.

    Game results: KC wins games 1,2,3 (scores 24-17, 30-20, 21-14)
    and loses game 4 (10-27).

    Schedule columns match CURATED_SCHEDULE_COLUMNS from data/sources.py.
    """
    return pd.DataFrame({
        "game_id": ["2023_01_KC_DET", "2023_02_JAX_KC", "2023_03_KC_CHI", "2023_04_NYJ_KC"],
        "season": [2023, 2023, 2023, 2023],
        "game_type": ["REG", "REG", "REG", "REG"],
        "week": [1, 2, 3, 4],
        "gameday": ["2023-09-07", "2023-09-17", "2023-09-24", "2023-10-01"],
        "weekday": ["Thursday", "Sunday", "Sunday", "Sunday"],
        "gametime": ["20:20", "13:00", "13:00", "13:00"],
        "away_team": ["DET", "JAX", "KC", "NYJ"],
        "away_score": [17, 20, 21, 27],
        "home_team": ["KC", "KC", "CHI", "KC"],
        "home_score": [24, 30, 14, 10],
        "location": ["Home", "Home", "Home", "Home"],
        "result": [7, 10, -7, -17],  # home_score - away_score
        "total": [41, 50, 35, 37],
        "overtime": [0, 0, 0, 0],
        "away_rest": [7, 7, 7, 7],
        "home_rest": [7, 7, 7, 7],
        "div_game": [0, 0, 0, 0],
        "roof": ["outdoors", "outdoors", "dome", "outdoors"],
        "surface": ["grass", "grass", "fieldturf", "grass"],
    })


@pytest.fixture
def synthetic_pbp():
    """Synthetic PBP data matching the synthetic_schedule fixture.

    Creates 10 plays per game (5 pass, 5 run) with controlled EPA values.
    Game 1 (KC home vs DET): KC offense epa=0.2, DET offense epa=-0.1
    Game 2 (KC home vs JAX): KC offense epa=0.3, JAX offense epa=-0.2
    Game 3 (KC away at CHI): KC offense epa=0.1, CHI offense epa=0.0
    Game 4 (KC home vs NYJ): KC offense epa=-0.3, NYJ offense epa=0.4

    Turnovers: KC commits 1 INT per game, opponents commit 0.
    """
    rows = []
    games = [
        {"game_id": "2023_01_KC_DET", "home": "KC", "away": "DET",
         "game_date": "2023-09-07", "week": 1,
         "home_epa": 0.2, "away_epa": -0.1, "home_int": 1, "away_int": 0},
        {"game_id": "2023_02_JAX_KC", "home": "KC", "away": "JAX",
         "game_date": "2023-09-17", "week": 2,
         "home_epa": 0.3, "away_epa": -0.2, "home_int": 1, "away_int": 0},
        {"game_id": "2023_03_KC_CHI", "home": "CHI", "away": "KC",
         "game_date": "2023-09-24", "week": 3,
         "home_epa": 0.0, "away_epa": 0.1, "home_int": 0, "away_int": 1},
        {"game_id": "2023_04_NYJ_KC", "home": "KC", "away": "NYJ",
         "game_date": "2023-10-01", "week": 4,
         "home_epa": -0.3, "away_epa": 0.4, "home_int": 1, "away_int": 0},
    ]
    play_id = 1
    for g in games:
        for team_role in ["home", "away"]:
            posteam = g[team_role]
            defteam = g["away"] if team_role == "home" else g["home"]
            epa_val = g[f"{team_role}_epa"]
            int_val = g[f"{team_role}_int"]
            for i in range(5):
                rows.append({
                    "play_id": play_id,
                    "game_id": g["game_id"],
                    "season": 2023,
                    "season_type": "REG",
                    "week": g["week"],
                    "game_date": g["game_date"],
                    "home_team": g["home"],
                    "away_team": g["away"],
                    "posteam": posteam,
                    "posteam_type": "home" if team_role == "home" else "away",
                    "defteam": defteam,
                    "down": (i % 4) + 1,
                    "ydstogo": 10,
                    "yardline_100": 50,
                    "quarter_seconds_remaining": 900,
                    "half_seconds_remaining": 1800,
                    "game_seconds_remaining": 3600,
                    "game_half": "Half1",
                    "play_type": "pass" if i < 3 else "run",
                    "yards_gained": 5,
                    "rush_attempt": 0 if i < 3 else 1,
                    "pass_attempt": 1 if i < 3 else 0,
                    "complete_pass": 1 if i < 2 else 0,
                    "incomplete_pass": 0,
                    "interception": int_val if i == 0 else 0,
                    "fumble_lost": 0,
                    "sack": 0,
                    "touchdown": 0,
                    "safety": 0,
                    "epa": epa_val,
                    "wp": 0.5,
                    "wpa": 0.01,
                    "score_differential": 0,
                    "posteam_score": 0,
                    "defteam_score": 0,
                    "total_home_score": 0,
                    "total_away_score": 0,
                    "location": "Home",
                })
                play_id += 1
    return pd.DataFrame(rows)


@pytest.fixture
def synthetic_two_season_schedule():
    """Schedule data spanning 2 seasons (2022 week 18 + 2023 weeks 1-2).

    For testing per-season rolling reset: 2023 week 1 should have NaN
    rolling features even though 2022 data exists.
    """
    return pd.DataFrame({
        "game_id": ["2022_18_KC_LV", "2023_01_KC_DET", "2023_02_JAX_KC"],
        "season": [2022, 2023, 2023],
        "game_type": ["REG", "REG", "REG"],
        "week": [18, 1, 2],
        "gameday": ["2023-01-07", "2023-09-07", "2023-09-17"],
        "weekday": ["Saturday", "Thursday", "Sunday"],
        "gametime": ["16:30", "20:20", "13:00"],
        "away_team": ["KC", "DET", "JAX"],
        "away_score": [31, 17, 20],
        "home_team": ["LV", "KC", "KC"],
        "home_score": [13, 24, 30],
        "location": ["Home", "Home", "Home"],
        "result": [-18, 7, 10],
        "total": [44, 41, 50],
        "overtime": [0, 0, 0],
        "away_rest": [7, 7, 7],
        "home_rest": [7, 7, 7],
        "div_game": [1, 0, 0],
        "roof": ["dome", "outdoors", "outdoors"],
        "surface": ["grass", "grass", "grass"],
    })


@pytest.fixture
def synthetic_two_season_pbp():
    """PBP data matching synthetic_two_season_schedule.

    Game 2022_18: KC offense epa=0.5 (dominant game)
    Game 2023_01: KC offense epa=0.2
    Game 2023_02: KC offense epa=0.3
    """
    rows = []
    games = [
        {"game_id": "2022_18_KC_LV", "home": "LV", "away": "KC",
         "season": 2022, "game_date": "2023-01-07", "week": 18,
         "home_epa": -0.3, "away_epa": 0.5, "home_int": 2, "away_int": 0},
        {"game_id": "2023_01_KC_DET", "home": "KC", "away": "DET",
         "season": 2023, "game_date": "2023-09-07", "week": 1,
         "home_epa": 0.2, "away_epa": -0.1, "home_int": 1, "away_int": 0},
        {"game_id": "2023_02_JAX_KC", "home": "KC", "away": "JAX",
         "season": 2023, "game_date": "2023-09-17", "week": 2,
         "home_epa": 0.3, "away_epa": -0.2, "home_int": 1, "away_int": 0},
    ]
    play_id = 1
    for g in games:
        for team_role in ["home", "away"]:
            posteam = g[team_role]
            defteam = g["away"] if team_role == "home" else g["home"]
            epa_val = g[f"{team_role}_epa"]
            int_val = g[f"{team_role}_int"]
            for i in range(5):
                rows.append({
                    "play_id": play_id,
                    "game_id": g["game_id"],
                    "season": g["season"],
                    "season_type": "REG",
                    "week": g["week"],
                    "game_date": g["game_date"],
                    "home_team": g["home"],
                    "away_team": g["away"],
                    "posteam": posteam,
                    "posteam_type": "home" if team_role == "home" else "away",
                    "defteam": defteam,
                    "down": (i % 4) + 1,
                    "ydstogo": 10,
                    "yardline_100": 50,
                    "quarter_seconds_remaining": 900,
                    "half_seconds_remaining": 1800,
                    "game_seconds_remaining": 3600,
                    "game_half": "Half1",
                    "play_type": "pass" if i < 3 else "run",
                    "yards_gained": 5,
                    "rush_attempt": 0 if i < 3 else 1,
                    "pass_attempt": 1 if i < 3 else 0,
                    "complete_pass": 1 if i < 2 else 0,
                    "incomplete_pass": 0,
                    "interception": int_val if i == 0 else 0,
                    "fumble_lost": 0,
                    "sack": 0,
                    "touchdown": 0,
                    "safety": 0,
                    "epa": epa_val,
                    "wp": 0.5,
                    "wpa": 0.01,
                    "score_differential": 0,
                    "posteam_score": 0,
                    "defteam_score": 0,
                    "total_home_score": 0,
                    "total_away_score": 0,
                    "location": "Home",
                })
                play_id += 1
    return pd.DataFrame(rows)
