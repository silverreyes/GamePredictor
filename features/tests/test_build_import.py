"""Minimal import test for TDD RED phase -- verifies build.py exists and is importable."""


def test_build_module_importable():
    from features.build import (
        aggregate_game_stats,
        compute_rolling_features,
        build_home_perspective,
        build_game_features,
        store_game_features,
    )
    assert callable(aggregate_game_stats)
    assert callable(compute_rolling_features)
    assert callable(build_home_perspective)
    assert callable(build_game_features)
    assert callable(store_game_features)
