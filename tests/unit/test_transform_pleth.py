# tests/unit/test_transform_pleth.py
"""Pruebas sintéticas de Pleth."""

from __future__ import annotations

import pandas as pd

from src.config.pleth import PLETH_SQL_COLUMNS
from src.transform.pleth import transform_pleth


def build_visit_row(
    pat_visit_id: int,
    effort_type_id: int,
    updates: dict[str, object],
) -> dict[str, object]:
    """Construye una fila mínima de pletismografía."""

    row: dict[str, object] = {column: pd.NA for column in PLETH_SQL_COLUMNS}
    row.update(
        {
            "PatientGUID": "patient-guid-1",
            "PatientIDNum": "DOC001",
            "PatientLastName": "Test",
            "PatientFirstName": "Patient",
            "PatientMidName": None,
            "Birthday": "1980-01-01",
            "SexListID": 1,
            "RaceListID": None,
            "PatVisitID": pat_visit_id,
            "PatVisitGUID": f"visit-guid-{pat_visit_id}",
            "VisitDateTime": "2024-01-01 10:00:00",
            "Age": 43,
            "Weight": 70,
            "Height": 170,
            "BMI": 24.2,
            "PredSetName": "Pred",
            "Diagnosis": None,
            "Comments": None,
            "PostComm": None,
            "Signed": 1,
            "SignedDateTime": None,
            "EffortTypeID": effort_type_id,
        }
    )
    row.update(updates)
    return row


def build_transform_input() -> pd.DataFrame:
    """Construye una muestra pequeña con un solo paciente."""

    return pd.DataFrame(
        [
            build_visit_row(
                1,
                1,
                {
                    "TGVPleth": 2.0,
                    "Raw": 100.0,
                },
            ),
            build_visit_row(
                1,
                2,
                {
                    "TGVPleth": 1.0,
                    "Raw": 40.0,
                },
            ),
            build_visit_row(
                1,
                5,
                {
                    "Raw": 10.0,
                },
            ),
            build_visit_row(
                1,
                9,
                {
                    "TGVPleth": 0.25,
                    "Raw": 0.0,
                },
            ),
            build_visit_row(
                1,
                10,
                {
                    "TGVPleth": 1.0,
                    "Raw": 0.0,
                },
            ),
        ]
    )


def test_pleth_percent_predicted_and_zscore_lms() -> None:
    """Verifica porcentaje predicho y z-score LMS."""

    analytical_dataframe = transform_pleth(build_transform_input())

    assert len(analytical_dataframe) == 1
    assert analytical_dataframe.loc[0, "tgv_pleth_percent_predicted_pre"] == 50.0
    assert analytical_dataframe.loc[0, "tgv_pleth_zscore_pre"] == -2.0


def test_pleth_fallback_sd_for_raw_zscore() -> None:
    """Verifica el fallback por SD para Raw."""

    analytical_dataframe = transform_pleth(build_transform_input())

    assert analytical_dataframe.loc[0, "raw_percent_predicted_pre"] == 40.0
    assert analytical_dataframe.loc[0, "raw_zscore_pre"] == -6.0
