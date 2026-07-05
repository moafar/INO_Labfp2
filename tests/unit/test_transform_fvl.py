# tests/unit/test_transform_fvl.py
"""Pruebas sintéticas de FVL."""

from __future__ import annotations

import pandas as pd

from src.config.fvl import FVL_SQL_COLUMNS
from src.transform.fvl import transform_fvl


def build_visit_row(
    pat_visit_id: int,
    effort_type_id: int,
    updates: dict[str, object],
) -> dict[str, object]:
    """Construye una fila mínima de espirometría."""

    row: dict[str, object] = {column: pd.NA for column in FVL_SQL_COLUMNS}
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
                    "FEV1": 2.0,
                    "FEFMax": 100.0,
                },
            ),
            build_visit_row(
                1,
                2,
                {
                    "FEV1": 1.0,
                    "FEFMax": 50.0,
                },
            ),
            build_visit_row(
                1,
                5,
                {
                    "FEFMax": 10.0,
                },
            ),
            build_visit_row(
                1,
                9,
                {
                    "FEV1": 0.25,
                    "FEFMax": 0.0,
                },
            ),
            build_visit_row(
                1,
                10,
                {
                    "FEV1": 1.0,
                    "FEFMax": 0.0,
                },
            ),
        ]
    )


def test_fvl_percent_predicted_and_zscore_lms() -> None:
    """Verifica porcentaje predicho y z-score LMS."""

    analytical_dataframe = transform_fvl(build_transform_input())

    assert len(analytical_dataframe) == 1
    assert analytical_dataframe.loc[0, "fev1_percent_predicted_pre"] == 50.0
    assert analytical_dataframe.loc[0, "fev1_zscore_pre"] == -2.0


def test_fvl_fallback_sd_for_fefmax_zscore() -> None:
    """Verifica el fallback por SD para FEFMax."""

    analytical_dataframe = transform_fvl(build_transform_input())

    assert analytical_dataframe.loc[0, "fefmax_percent_predicted_pre"] == 50.0
    assert analytical_dataframe.loc[0, "fefmax_zscore_pre"] == -5.0
