"""CLI entry point for full NFL data ingestion pipeline."""
import sys
import click
import pandas as pd
from sqlalchemy.dialects.postgresql import insert as pg_insert

from data.loaders import load_pbp_cached, load_schedules_cached
from data.transforms import (
    normalize_teams_in_df,
    filter_preseason,
    select_pbp_columns,
    select_schedule_columns,
)
from data.sources import TEAM_COLUMNS_PBP, TEAM_COLUMNS_SCHEDULE
from data.db import get_engine, get_table
from data.validators import validate_game_count, print_validation_summary


def upsert_dataframe(engine, table, df, conflict_columns, chunk_size=5000):
    """Upsert DataFrame rows into PostgreSQL table in chunks.

    Uses PostgreSQL ON CONFLICT DO UPDATE for idempotent inserts.
    Processes in chunks to avoid memory issues with large DataFrames.
    """
    records = df.to_dict(orient="records")
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = pg_insert(table).values(chunk)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in table.columns
            if c.name not in conflict_columns
        }
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=conflict_columns,
            set_=update_cols,
        )
        with engine.begin() as conn:
            conn.execute(upsert_stmt)


def _log_ingestion(engine, season, table_name, row_count, expected, actual, status):
    """Log ingestion result to ingestion_log table."""
    log_table = get_table("ingestion_log", engine)
    stmt = pg_insert(log_table).values(
        season=season,
        table_name=table_name,
        rows_inserted=row_count,
        rows_updated=0,
        expected_games=expected,
        actual_games=actual,
        status=status,
    )
    with engine.begin() as conn:
        conn.execute(stmt)


@click.command()
@click.option(
    "--seasons",
    multiple=True,
    type=int,
    help="Specific seasons to load (default: all 2005-2024)",
)
def ingest(seasons):
    """Ingest NFL play-by-play and schedule data into PostgreSQL.

    Downloads data from nflreadpy, normalizes team abbreviations,
    filters preseason, and upserts into the database. Validates
    game counts after ingestion and exits non-zero on mismatch.
    """
    season_list = list(seasons) if seasons else list(range(2005, 2025))
    engine = get_engine()

    # Reflect tables once
    raw_pbp_table = get_table("raw_pbp", engine)
    schedules_table = get_table("schedules", engine)

    validation_results = []

    for season in season_list:
        click.echo(f"\n--- Season {season} ---")

        # --- PBP ingestion ---
        click.echo(f"  Loading PBP data for {season}...")
        pbp_df = load_pbp_cached(season)
        pbp_df = filter_preseason(pbp_df, "season_type")
        pbp_df = select_pbp_columns(pbp_df)
        pbp_df = normalize_teams_in_df(pbp_df, TEAM_COLUMNS_PBP)

        click.echo(f"  Upserting {len(pbp_df)} PBP rows...")
        upsert_dataframe(engine, raw_pbp_table, pbp_df, ["game_id", "play_id"])

        # Count regular season games for validation (distinct game_id where season_type == REG)
        reg_pbp = pbp_df[pbp_df["season_type"] == "REG"]
        pbp_reg_game_count = reg_pbp["game_id"].nunique()
        pbp_result = validate_game_count(season, pbp_reg_game_count, "raw_pbp")
        validation_results.append(pbp_result)

        _log_ingestion(
            engine, season, "raw_pbp", len(pbp_df),
            pbp_result.expected_games, pbp_result.actual_games, pbp_result.status,
        )

        # --- Schedule ingestion ---
        click.echo(f"  Loading schedule data for {season}...")
        sched_df = load_schedules_cached(season)
        # Filter: exclude preseason (game_type != 'PRE'), keep REG + playoff types
        sched_df = sched_df[sched_df["game_type"] != "PRE"].reset_index(drop=True)
        sched_df = select_schedule_columns(sched_df)
        sched_df = normalize_teams_in_df(sched_df, TEAM_COLUMNS_SCHEDULE)
        # Add games_in_season column: 16 for <=2020, 17 for 2021+
        sched_df["games_in_season"] = 16 if season <= 2020 else 17

        click.echo(f"  Upserting {len(sched_df)} schedule rows...")
        upsert_dataframe(engine, schedules_table, sched_df, ["game_id"])

        # Count regular season games for validation
        sched_reg_game_count = len(sched_df[sched_df["game_type"] == "REG"])
        sched_result = validate_game_count(season, sched_reg_game_count, "schedules")
        validation_results.append(sched_result)

        _log_ingestion(
            engine, season, "schedules", len(sched_df),
            sched_result.expected_games, sched_result.actual_games, sched_result.status,
        )

        click.echo(f"  Season {season} complete.")

    # Print validation summary and exit non-zero on failure
    all_ok = print_validation_summary(validation_results)
    if not all_ok:
        click.echo("\nValidation FAILED. See summary above.", err=True)
        sys.exit(1)
    else:
        click.echo("\nAll validations passed.")


if __name__ == "__main__":
    ingest()
