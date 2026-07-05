# tests/unit/test_transform_dlco.py
"""Pruebas sintéticas de DLCO."""

from __future__ import annotations

import pandas as pd

from src.config.dlco import DLCO_SQL_COLUMNS
from src.transform.dlco import transform_dlco


def build_visit_row(
    pat_visit_id: int,
    effort_type_id: int,
    updates: dict[str, object],
) -> dict[str, object]:
    """Construye una fila mínima de DLCO."""

    row: dict[str, object] = {column: pd.NA for column in DLCO_SQL_COLUMNS}
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
                    "DLCOunc": 2.0,
                    "DLVA": 5.0,
                },
            ),
            build_visit_row(
                1,
                2,
                {
                    "DLCOunc": 1.0,
                    "DLVA": 2.0,
                },
            ),
            build_visit_row(
                1,
                5,
                {
                    "DLVA": 1.0,
                },
            ),
            build_visit_row(
                1,
                9,
                {
                    "DLCOunc": 0.2,
                    "DLVA": 0.0,
                },
            ),
            build_visit_row(
                1,
                10,
                {
                    "DLCOunc": 1.0,
                    "DLVA": 0.0,
                },
            ),
        ]
    )


def test_dlco_percent_predicted_and_zscore_lms() -> None:
    """Verifica porcentaje predicho y z-score LMS."""

    analytical_dataframe = transform_dlco(build_transform_input())

    assert len(analytical_dataframe) == 1
    assert analytical_dataframe.loc[0, "dlcounc_percent_predicted_pre"] == 50.0
    assert analytical_dataframe.loc[0, "dlcounc_zscore_pre"] == -2.5


def test_dlco_fallback_sd_for_dlva_zscore() -> None:
    """Verifica el fallback por SD para DL/VA."""

    analytical_dataframe = transform_dlco(build_transform_input())

    assert analytical_dataframe.loc[0, "dlva_percent_predicted_pre"] == 40.0
    assert analytical_dataframe.loc[0, "dlva_zscore_pre"] == -3.0
