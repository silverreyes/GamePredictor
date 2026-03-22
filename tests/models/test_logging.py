"""Unit tests for JSONL logging in models/train.py.

Tests cover:
- JSONL append creates/appends file with correct schema
- JSONL entry contains all 16 required fields
"""

import json
import os

import pytest

from models.train import log_experiment


# Common test parameters for log_experiment calls
SAMPLE_PARAMS = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.3}
SAMPLE_FEATURES = ["feat_a", "feat_b", "feat_c"]
SAMPLE_SHAP_TOP5 = [
    ("feat_a", 0.1234),
    ("feat_b", 0.0987),
    ("feat_c", 0.0765),
    ("feat_d", 0.0543),
    ("feat_e", 0.0321),
]


class TestJsonlLogging:
    """Tests for experiments.jsonl append-only logging."""

    def test_jsonl_append(self, tmp_path):
        """log_experiment creates/appends to experiments.jsonl."""
        jsonl_path = str(tmp_path / "experiments.jsonl")

        log_experiment(
            experiment_id=1,
            params=SAMPLE_PARAMS,
            features_used=SAMPLE_FEATURES,
            val_acc_2023=0.610,
            val_acc_2022=0.620,
            val_acc_2021=0.615,
            baseline_home=0.570,
            baseline_record=0.600,
            log_loss_val=0.680,
            brier_score_val=0.240,
            shap_top5=SAMPLE_SHAP_TOP5,
            keep=True,
            hypothesis="Baseline XGBoost with defaults",
            prev_best_acc=0.0,
            model_path=None,
            jsonl_path=jsonl_path,
        )

        assert os.path.exists(jsonl_path)

        with open(jsonl_path) as f:
            lines = f.readlines()
        assert len(lines) == 1

        # Append a second entry
        log_experiment(
            experiment_id=2,
            params=SAMPLE_PARAMS,
            features_used=SAMPLE_FEATURES,
            val_acc_2023=0.615,
            val_acc_2022=0.625,
            val_acc_2021=0.618,
            baseline_home=0.570,
            baseline_record=0.600,
            log_loss_val=0.675,
            brier_score_val=0.238,
            shap_top5=SAMPLE_SHAP_TOP5,
            keep=True,
            hypothesis="Second experiment",
            prev_best_acc=0.610,
            model_path=None,
            jsonl_path=jsonl_path,
        )

        with open(jsonl_path) as f:
            lines = f.readlines()
        assert len(lines) == 2

    def test_jsonl_schema_fields(self, tmp_path):
        """Logged JSONL entry contains all 16 required schema fields."""
        jsonl_path = str(tmp_path / "experiments.jsonl")

        log_experiment(
            experiment_id=1,
            params=SAMPLE_PARAMS,
            features_used=SAMPLE_FEATURES,
            val_acc_2023=0.610,
            val_acc_2022=0.620,
            val_acc_2021=0.615,
            baseline_home=0.570,
            baseline_record=0.600,
            log_loss_val=0.680,
            brier_score_val=0.240,
            shap_top5=SAMPLE_SHAP_TOP5,
            keep=True,
            hypothesis="Schema test",
            prev_best_acc=0.0,
            model_path=None,
            jsonl_path=jsonl_path,
        )

        with open(jsonl_path) as f:
            entry = json.loads(f.readline())

        required_keys = {
            "experiment_id",
            "timestamp",
            "params",
            "features",
            "val_accuracy_2023",
            "val_accuracy_2022",
            "val_accuracy_2021",
            "baseline_always_home",
            "baseline_better_record",
            "log_loss",
            "brier_score",
            "shap_top5",
            "keep",
            "hypothesis",
            "prev_best_acc",
            "model_path",
        }

        assert set(entry.keys()) == required_keys
        assert entry["experiment_id"] == 1
        assert entry["val_accuracy_2023"] == 0.610
        assert entry["keep"] is True
        assert len(entry["shap_top5"]) == 5
        assert entry["shap_top5"][0]["feature"] == "feat_a"


