"""Pruebas sintéticas del análisis temporal GX, sin datos clínicos."""

import pandas as pd
import pytest

from scripts.analyze_ergoespirometry_windows import (
    calculate_scores,
    get_patient_query_time,
    get_target_time,
    summarize_at_time,
)
from scripts.analyze_ergoespirometry_calibration import select_best_candidates


def test_rest_uses_exact_sql_marker_and_keeps_rounded_pq_time() -> None:
    """Evita tratar el minuto exportado como si tuviera precisión de segundos."""

    record = pd.Series(
        {
            "StartExerciseTime": 185.0,
            "GX Rest Time (min)": 3.0,
        }
    )

    assert get_target_time(record, "rest") == 185.0
    assert get_patient_query_time(record, "rest") == 180.0


def test_summarize_at_time_distinguishes_window_positions() -> None:
    """Comprueba límites pre, centrados y post con una serie construida."""

    signals = pd.DataFrame(
        {
            "elapsed_time_s": [0.0, 5.0, 10.0, 15.0, 20.0],
            "synthetic_metric": [0.0, 5.0, 10.0, 15.0, 20.0],
        }
    )
    summaries = pd.DataFrame(summarize_at_time(signals, target_time=10.0))
    selected = summaries[
        summaries["raw_metric"].eq("synthetic_metric")
        & summaries["window_seconds"].eq(10)
        & summaries["statistic"].eq("mean")
    ].set_index("window_position")

    assert selected.loc["pre", "raw_value"] == pytest.approx(5.0)
    assert selected.loc["centered", "raw_value"] == pytest.approx(10.0)
    assert selected.loc["post", "raw_value"] == pytest.approx(15.0)


def test_scores_respect_deterministic_evaluation_partition() -> None:
    """Verifica que las métricas finales usan solo GXTestID múltiplos de cinco."""

    rows = []
    for gx_test_id in range(1, 101):
        value = float(gx_test_id)
        row = {
            "gx_test_id": gx_test_id,
            "moment": "at",
            "raw_metric": "synthetic_metric",
            "window_seconds": 10,
            "window_position": "pre",
            "statistic": "mean",
            "raw_value": value,
            "evaluation_set": gx_test_id % 5 == 0,
        }
        for target in (
            "vo2",
            "vco2",
            "rq",
            "heart_rate",
            "work",
            "tidal_volume",
            "ventilation",
            "respiratory_rate",
            "ve_vo2",
            "ve_vco2",
            "vo2_hr",
            "petco2",
            "peto2",
        ):
            row[f"pq_{target}"] = value
        rows.append(row)

    scores = calculate_scores(pd.DataFrame(rows))
    score = scores[scores["target_metric"].eq("vo2")].iloc[0]

    assert score["train_size"] == 80
    assert score["test_size"] == 20
    assert score["train_r2"] == pytest.approx(1.0)
    assert score["test_r2"] == pytest.approx(1.0)


def test_candidate_selection_uses_training_and_requires_coverage() -> None:
    """Evita seleccionar hiperparámetros por evaluación o por pocos casos."""

    common = {
        "moment": "at",
        "target_metric": "respiratory_rate",
        "raw_metric": "rr_from_breath_duration",
        "window_position": "pre",
        "statistic": "mean",
        "model_type": "proportional",
        "train_median_absolute_percentage_error": 3.0,
        "test_median_absolute_percentage_error": 3.0,
    }
    scores = pd.DataFrame(
        [
            {
                **common,
                "window_seconds": 10,
                "train_size": 80,
                "test_size": 20,
                "train_r2": 0.90,
                "test_r2": 0.80,
            },
            {
                **common,
                "window_seconds": 20,
                "train_size": 80,
                "test_size": 20,
                "train_r2": 0.80,
                "test_r2": 0.99,
            },
            {
                **common,
                "window_seconds": 30,
                "train_size": 20,
                "test_size": 5,
                "train_r2": 0.99,
                "test_r2": 1.00,
            },
        ]
    )

    selected = select_best_candidates(scores)

    assert len(selected) == 1
    assert selected.iloc[0]["window_seconds"] == 10
