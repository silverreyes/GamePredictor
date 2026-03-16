-- sql/init.sql
CREATE TABLE IF NOT EXISTS raw_pbp (
    play_id INTEGER NOT NULL,
    game_id VARCHAR(20) NOT NULL,
    season SMALLINT NOT NULL,
    season_type VARCHAR(4) NOT NULL,
    week SMALLINT NOT NULL,
    game_date DATE,
    home_team VARCHAR(3) NOT NULL,
    away_team VARCHAR(3) NOT NULL,
    posteam VARCHAR(3),
    posteam_type VARCHAR(4),
    defteam VARCHAR(3),
    down SMALLINT,
    ydstogo SMALLINT,
    yardline_100 SMALLINT,
    quarter_seconds_remaining SMALLINT,
    half_seconds_remaining SMALLINT,
    game_seconds_remaining SMALLINT,
    game_half VARCHAR(10),
    play_type VARCHAR(20),
    yards_gained SMALLINT,
    rush_attempt SMALLINT,
    pass_attempt SMALLINT,
    complete_pass SMALLINT,
    incomplete_pass SMALLINT,
    interception SMALLINT,
    fumble_lost SMALLINT,
    sack SMALLINT,
    touchdown SMALLINT,
    safety SMALLINT,
    epa REAL,
    wp REAL,
    wpa REAL,
    score_differential SMALLINT,
    posteam_score SMALLINT,
    defteam_score SMALLINT,
    total_home_score SMALLINT,
    total_away_score SMALLINT,
    location VARCHAR(10),
    PRIMARY KEY (game_id, play_id)
);

CREATE TABLE IF NOT EXISTS schedules (
    game_id VARCHAR(20) PRIMARY KEY,
    season SMALLINT NOT NULL,
    game_type VARCHAR(4) NOT NULL,
    week SMALLINT NOT NULL,
    gameday DATE,
    weekday VARCHAR(10),
    gametime VARCHAR(5),
    away_team VARCHAR(3) NOT NULL,
    away_score SMALLINT,
    home_team VARCHAR(3) NOT NULL,
    home_score SMALLINT,
    location VARCHAR(10),
    result SMALLINT,
    total SMALLINT,
    overtime SMALLINT,
    away_rest SMALLINT,
    home_rest SMALLINT,
    div_game SMALLINT,
    roof VARCHAR(10),
    surface VARCHAR(20),
    games_in_season SMALLINT NOT NULL DEFAULT 16
);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id SERIAL PRIMARY KEY,
    season SMALLINT NOT NULL,
    table_name VARCHAR(20) NOT NULL,
    rows_inserted INTEGER NOT NULL,
    rows_updated INTEGER NOT NULL,
    expected_games INTEGER,
    actual_games INTEGER,
    status VARCHAR(20) NOT NULL,
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (season, table_name, ingested_at)
);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_pbp_season ON raw_pbp (season);
CREATE INDEX IF NOT EXISTS idx_pbp_game_id ON raw_pbp (game_id);
CREATE INDEX IF NOT EXISTS idx_pbp_posteam ON raw_pbp (posteam);
CREATE INDEX IF NOT EXISTS idx_schedules_season ON schedules (season);
CREATE INDEX IF NOT EXISTS idx_schedules_game_type ON schedules (game_type);
