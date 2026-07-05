# tests/unit/test_transform_mip_mep.py
"""Pruebas sintéticas de MIP/MEP."""

from __future__ import annotations

import pandas as pd

from src.transform.mip_mep import transform_mip_mep


def build_transform_input() -> pd.DataFrame:
    """Construye una fila mínima válida de MIP/MEP."""

    return pd.DataFrame(
        [
            {
                "PatientGUID": "patient-guid-1",
                "PatientIDNum": "DOC001",
                "PatientLastName": "Test",
                "PatientFirstName": "Patient",
                "PatientMidName": None,
                "Birthday": "1980-01-01",
                "SexListID": 1,
                "RaceListID": None,
                "PatVisitID": 1,
                "PatVisitGUID": "visit-guid-1",
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
                "MipMepTest": 1,
                "MipDataID": 1001,
                "EffortTypeID": 2,
                "EffortTypeDesc": "Baseline",
                "EffortTime": 12,
                "EffortArtificial": 0,
                "EffortManual": 0,
                "EffortSelected": 1,
                "PFProtocolStageIndex": 1,
                "MIP": 10.0,
                "MEP": 20.0,
            }
        ]
    )


def test_transform_mip_mep_basic_shape() -> None:
    """Verifica la transformación básica y las columnas principales."""

    analytical_dataframe = transform_mip_mep(build_transform_input())

    assert len(analytical_dataframe) == 1
    assert analytical_dataframe.loc[0, "mip_mep_test"] == 1
    assert analytical_dataframe.loc[0, "mip"] == 10.0
    assert analytical_dataframe.loc[0, "mep"] == 20.0
    assert "pat_visit_id" in analytical_dataframe.columns
    assert "mip_data_id" in analytical_dataframe.columns
