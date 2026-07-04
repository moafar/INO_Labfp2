# tests/test_transform_methacholine.py
"""Prueba la transformación analítica de metacolina."""

import pandas as pd

from src.transform.methacholine import transform_methacholine


def build_row(
    pat_visit_id: int,
    stage_index: int,
    fev1: float | None,
    concentration: float | None,
    delivered_dose: float | None,
    effort_type_id: int,
) -> dict:
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
        "VisitDateTime": "2023-08-29 10:23:47",
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
        "LastPFProtocolStageIndex": 7,
        "TestingStage": None,
        "PFProtocolName": "TEST DE METACOLINA",
        "ChallengeAgentID": 3,
        "ChallengeAgentName": "Methacholine",
        "ChallengeAgentType": 1,
        "PFProtocolStageIndex": stage_index,
        "PFProtocolStageLabel": f"stage {stage_index}",
        "PFProtocolStageConcentration": concentration,
        "PFProtocolStageDeliveredDose": delivered_dose,
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
    """Clasifica como positivo si FEV1 cae al menos 20% desde basal."""

    raw_dataframe = pd.DataFrame(
        [
            build_row(1, 1, 3.0, None, None, 2),
            build_row(1, 2, 2.8, 0.063, 0.315, 8),
            build_row(1, 3, 2.3, 0.25, 1.25, 8),
            build_row(1, 7, 2.9, None, None, 3),
        ]
    )

    transformed = transform_methacholine(raw_dataframe)

    assert len(transformed) == 1
    assert transformed.loc[0, "baseline_fev1"] == 3.0
    assert transformed.loc[0, "max_fev1_drop_stage"] == 3
    assert transformed.loc[0, "max_fev1_drop_concentration"] == 0.25
    assert round(transformed.loc[0, "max_fev1_drop_percent"], 2) == -23.33
    assert transformed.loc[0, "methacholine_positive"] == True


def test_transform_methacholine_unclassifiable_visit() -> None:
    """Deja sin clasificación visitas sin etapas válidas de metacolina."""

    raw_dataframe = pd.DataFrame(
        [
            build_row(2, 1, 2.0, None, None, 2),
            build_row(2, 2, None, 0.063, 0.315, 8),
            build_row(2, 7, 2.1, None, None, 3),
        ]
    )

    transformed = transform_methacholine(raw_dataframe)

    assert len(transformed) == 1
    assert pd.isna(transformed.loc[0, "max_fev1_drop_percent"])
    assert pd.isna(transformed.loc[0, "max_fev1_drop_stage"])
    assert pd.isna(transformed.loc[0, "methacholine_positive"])
