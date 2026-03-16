"""CLI entry point for feature pipeline: python -m features."""
import sys
import click

from features.build import build_game_features, store_game_features


@click.command()
@click.option(
    "--seasons",
    multiple=True,
    type=int,
    help="Specific seasons to build features for (default: all 2005-2024)",
)
@click.option(
    "--store/--no-store",
    default=False,
    help="Store features in PostgreSQL game_features table (requires DATABASE_URL)",
)
def build(seasons, store):
    """Build game-level features from cached PBP and schedule data.

    Computes rolling EPA/play, point differential, turnover differential,
    and win rate using only prior-game data (shift(1)). Outputs one row
    per regular-season game from the home team perspective.
    """
    season_list = list(seasons) if seasons else None
    label = f"seasons {season_list}" if season_list else "all seasons (2005-2024)"
    click.echo(f"Building features for {label}...")

    df = build_game_features(seasons=season_list)

    click.echo(f"Feature matrix: {len(df)} rows x {len(df.columns)} columns")
    click.echo(f"Seasons: {sorted(df['season'].unique())}")
    click.echo(f"Rolling columns: {[c for c in df.columns if 'rolling' in c]}")

    # Show NaN counts for rolling features (Week 1 expected NaN)
    rolling_cols = [c for c in df.columns if "rolling" in c]
    nan_counts = df[rolling_cols].isna().sum()
    click.echo(f"NaN counts (expected for week 1): {dict(nan_counts)}")

    if store:
        click.echo("Storing features in PostgreSQL...")
        n = store_game_features(df)
        click.echo(f"Stored {n} rows in game_features table.")
    else:
        click.echo("Dry run (use --store to write to PostgreSQL).")

    click.echo("Done.")


if __name__ == "__main__":
    build()
