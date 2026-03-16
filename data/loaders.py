"""Cached data loading from nfl_data_py."""
import pandas as pd
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential

CACHE_DIR = Path("data/cache")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download_pbp(season: int) -> pd.DataFrame:
    """Download PBP data from nfl_data_py with retry logic."""
    import nfl_data_py as nfl
    return nfl.import_pbp_data([season])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def _download_schedules(season: int) -> pd.DataFrame:
    """Download schedule data from nfl_data_py with retry logic."""
    import nfl_data_py as nfl
    return nfl.import_schedules([season])


def load_pbp_cached(season: int) -> pd.DataFrame:
    """Load PBP data for a season, using Parquet cache if available.

    Cache path: data/cache/pbp_{season}.parquet
    If cache exists, reads from parquet. Otherwise downloads via nfl_data_py,
    saves to parquet, and returns the DataFrame.
    """
    cache_path = CACHE_DIR / f"pbp_{season}.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = _download_pbp(season)
    df.to_parquet(cache_path)
    return df


def load_schedules_cached(season: int) -> pd.DataFrame:
    """Load schedule data for a season, using Parquet cache if available.

    Cache path: data/cache/schedules_{season}.parquet
    If cache exists, reads from parquet. Otherwise downloads via nfl_data_py,
    saves to parquet, and returns the DataFrame.
    """
    cache_path = CACHE_DIR / f"schedules_{season}.parquet"
    if cache_path.exists():
        return pd.read_parquet(cache_path)

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    df = _download_schedules(season)
    df.to_parquet(cache_path)
    return df
