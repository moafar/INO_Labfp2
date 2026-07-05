# tests/unit/test_transform_methacholine.py
"""Pruebas sintéticas de metacolina."""

from __future__ import annotations

import pandas as pd

from src.transform.methacholine import transform_methacholine


def build_row(
    pat_visit_id: int,
    stage_index: int,
    fev1: float | None,
) -> dict[str, object]:
    """Construye una fila mínima compatible con el transformador."""

    return {
        "PatientGUID": "patient-guid-1",
        "PatientIDNum": "DOC001",
        "PatientLastName": "Test",
        "PatientFirstName": "Patient",
        "PatientMidName": None,
        "Birthday": "1980-01-01",
        "SexListID": 1,
        "RaceListID": None,
        "PatVisitID": pat_visit_id,
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
        "PFProtocolGUID": "protocol-guid-1",
        "LastPFProtocolStageIndex": 2,
        "TestingStage": None,
        "PFProtocolName": "TEST DE METACOLINA",
        "ChallengeAgentID": 3,
        "ChallengeAgentName": "Methacholine",
        "ChallengeAgentType": 1,
        "PFProtocolStageIndex": stage_index,
        "PFProtocolStageLabel": f"stage {stage_index}",
        "PFProtocolStageConcentration": 0.063 if stage_index == 2 else None,
        "PFProtocolStageDeliveredDose": 0.315 if stage_index == 2 else None,
        "PFProtocolStageComment": None,
        "FVLDataID": pat_visit_id * 100 + stage_index,
        "EffortTime": None,
        "EffortArtificial": 0,
        "EffortManual": 0,
        "EffortSelected": 0,
        "FVC": None,
        "FEV1": fev1,
        "FEV1FVC": None,
        "FEF2575": None,
        "PEF": None,
        "FVLATSCodes": None,
        "TestGradeATS": "EE",
        "TestGradeNLHEP": None,
    }


def test_transform_methacholine_positive_visit() -> None:
    """Clasifica como positiva una caída de FEV1 mayor o igual al 20%."""

    raw_dataframe = pd.DataFrame(
        [
            build_row(1, 1, 3.0),
            build_row(1, 2, 2.3),
        ]
    )

    transformed = transform_methacholine(raw_dataframe)

    assert len(transformed) == 1
    assert transformed.loc[0, "baseline_fev1"] == 3.0
    assert round(transformed.loc[0, "max_fev1_drop_percent"], 2) == -23.33
    assert transformed.loc[0, "methacholine_positive"] == True


def test_transform_methacholine_negative_visit() -> None:
    """Clasifica como negativa una caída de FEV1 menor al 20%."""

    raw_dataframe = pd.DataFrame(
        [
            build_row(2, 1, 3.0),
            build_row(2, 2, 2.8),
        ]
    )

    transformed = transform_methacholine(raw_dataframe)

    assert len(transformed) == 1
    assert round(transformed.loc[0, "max_fev1_drop_percent"], 2) == -6.67
    assert transformed.loc[0, "methacholine_positive"] == False
