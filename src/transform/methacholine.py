# src/transform/methacholine.py
"""Transforma etapas de metacolina en una tabla analítica por visita."""

from collections.abc import Iterable

import numpy as np
import pandas as pd


VISIT_COLUMNS = [
    "PatientGUID",
    "PatientIDNum",
    "PatientLastName",
    "PatientFirstName",
    "PatientMidName",
    "Birthday",
    "SexListID",
    "RaceListID",
    "PatVisitID",
    "PatVisitGUID",
    "VisitDateTime",
    "Age",
    "Weight",
    "Height",
    "BMI",
    "PredSetName",
    "Diagnosis",
    "Comments",
    "PostComm",
    "Signed",
    "SignedDateTime",
    "PFProtocolGUID",
    "LastPFProtocolStageIndex",
    "TestingStage",
    "PFProtocolName",
    "ChallengeAgentID",
    "ChallengeAgentName",
    "ChallengeAgentType",
]

STAGE_COLUMNS = [
    "PFProtocolStageLabel",
    "PFProtocolStageConcentration",
    "PFProtocolStageDeliveredDose",
    "PFProtocolStageComment",
    "FVLDataID",
    "EffortTime",
    "EffortArtificial",
    "EffortManual",
    "EffortSelected",
    "FVC",
    "FEV1",
    "FEV1FVC",
    "FEF2575",
    "PEF",
    "FVLATSCodes",
    "TestGradeATS",
    "TestGradeNLHEP",
]


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: Iterable[str],
) -> None:
    """Comprueba que el DataFrame contenga las columnas obligatorias."""

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Faltan columnas obligatorias: "
            + ", ".join(missing_columns)
        )


def build_visit_dimension(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Obtiene una única fila descriptiva por visita."""

    return (
        raw_dataframe[VISIT_COLUMNS]
        .drop_duplicates(subset=["PatVisitID"])
        .copy()
    )


def build_stage_measurements(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convierte las etapas de metacolina a formato ancho por visita."""

    measurements = raw_dataframe[
        [
            "PatVisitID",
            "PFProtocolStageIndex",
            *STAGE_COLUMNS,
        ]
    ].copy()

    measurements["stage"] = (
        pd.to_numeric(
            measurements["PFProtocolStageIndex"],
            errors="coerce",
        )
        .astype("Int64")
        .astype("string")
    )

    duplicate_mask = measurements.duplicated(
        subset=["PatVisitID", "stage"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicate_rows = (
            measurements.loc[
                duplicate_mask,
                ["PatVisitID", "stage", "FVLDataID"],
            ]
            .sort_values(
                by=["PatVisitID", "stage", "FVLDataID"],
                kind="stable",
            )
        )

        raise ValueError(
            "Existen varias filas para la misma visita y etapa de metacolina:\n"
            + duplicate_rows.head(20).to_string(index=False)
        )

    long_dataframe = measurements.melt(
        id_vars=["PatVisitID", "stage"],
        value_vars=STAGE_COLUMNS,
        var_name="parameter",
        value_name="value",
    )

    wide_dataframe = long_dataframe.pivot(
        index="PatVisitID",
        columns=["stage", "parameter"],
        values="value",
    )

    wide_dataframe.columns = [
        f"stage_{stage}_{parameter.lower()}"
        for stage, parameter in wide_dataframe.columns
    ]

    numeric_fragments = (
        "concentration",
        "delivereddose",
        "fvldataid",
        "fvc",
        "fev1",
        "fev1fvc",
        "fef2575",
        "pef",
    )

    numeric_columns = [
        column
        for column in wide_dataframe.columns
        if column.endswith(numeric_fragments)
    ]

    wide_dataframe[numeric_columns] = wide_dataframe[
        numeric_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    return wide_dataframe.reset_index()


def add_derived_metrics(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Añade cambios de FEV1 respecto al basal."""

    transformed = dataframe.copy()

    fev1_stage_columns = sorted(
        [
            column
            for column in transformed.columns
            if column.startswith("stage_")
            and column.endswith("_fev1")
        ],
        key=lambda column: int(column.split("_")[1]),
    )

    if not fev1_stage_columns:
        return transformed

    baseline_column = fev1_stage_columns[0]
    baseline = pd.to_numeric(
        transformed[baseline_column],
        errors="coerce",
    )

    derived_columns = {}

    for column in fev1_stage_columns:
        stage = column.split("_")[1]
        current = pd.to_numeric(
            transformed[column],
            errors="coerce",
        )

        derived_columns[f"stage_{stage}_fev1_change_from_baseline"] = (
            current - baseline
        )

        derived_columns[f"stage_{stage}_fev1_percent_change_from_baseline"] = (
            np.where(
                baseline.gt(0),
                ((current - baseline) / baseline) * 100.0,
                np.nan,
            )
        )

    derived_dataframe = pd.DataFrame(
        derived_columns,
        index=transformed.index,
    )

    transformed = pd.concat(
        [transformed, derived_dataframe],
        axis=1,
    )

    # Resume la respuesta bronquial durante las etapas de metacolina.
    challenge_percent_columns = [
        column
        for column in transformed.columns
        if column.startswith("stage_")
        and column.endswith("_fev1_percent_change_from_baseline")
        and column.split("_")[1] not in {"1", "7"}
    ]

    if challenge_percent_columns:
        challenge_stages = [
            column.split("_")[1]
            for column in challenge_percent_columns
        ]

        transformed["baseline_fev1"] = baseline
        transformed["max_fev1_drop_percent"] = transformed[
            challenge_percent_columns
        ].min(axis=1, skipna=True)

        has_challenge_values = transformed[
            challenge_percent_columns
        ].notna().any(axis=1)

        transformed["max_fev1_drop_stage"] = pd.Series(
            pd.NA,
            index=transformed.index,
            dtype="Int64",
        )

        stage_labels = transformed.loc[
            has_challenge_values,
            challenge_percent_columns,
        ].idxmin(axis=1, skipna=True)

        transformed.loc[
            has_challenge_values,
            "max_fev1_drop_stage",
        ] = pd.to_numeric(
            stage_labels.str.extract(r"stage_(\d+)_")[0],
            errors="coerce",
        ).astype("Int64")

        concentration_lookup = {}

        for stage in challenge_stages:
            concentration_column = (
                f"stage_{stage}_pfprotocolstageconcentration"
            )
            if concentration_column in transformed.columns:
                concentration_lookup[int(stage)] = concentration_column

        transformed["max_fev1_drop_concentration"] = np.nan

        for stage, concentration_column in concentration_lookup.items():
            mask = transformed["max_fev1_drop_stage"].eq(stage)
            transformed.loc[
                mask,
                "max_fev1_drop_concentration",
            ] = transformed.loc[
                mask,
                concentration_column,
            ]

        transformed["methacholine_positive"] = pd.Series(
            pd.NA,
            index=transformed.index,
            dtype="boolean",
        )

        transformed.loc[
            transformed["max_fev1_drop_percent"].notna(),
            "methacholine_positive",
        ] = transformed.loc[
            transformed["max_fev1_drop_percent"].notna(),
            "max_fev1_drop_percent",
        ] <= -20.0

    return transformed


def normalize_column_names(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convierte los nombres descriptivos a snake_case."""

    rename_map = {
        "PatientGUID": "patient_guid",
        "PatientIDNum": "patient_id_num",
        "PatientLastName": "patient_last_name",
        "PatientFirstName": "patient_first_name",
        "PatientMidName": "patient_middle_name",
        "Birthday": "birthday",
        "SexListID": "sex_list_id",
        "RaceListID": "race_list_id",
        "PatVisitID": "pat_visit_id",
        "PatVisitGUID": "pat_visit_guid",
        "VisitDateTime": "visit_datetime",
        "Age": "age",
        "Weight": "weight",
        "Height": "height",
        "BMI": "bmi",
        "PredSetName": "pred_set_name",
        "Diagnosis": "diagnosis",
        "Comments": "comments",
        "PostComm": "post_comment",
        "Signed": "signed",
        "SignedDateTime": "signed_datetime",
        "PFProtocolGUID": "pf_protocol_guid",
        "LastPFProtocolStageIndex": "last_pf_protocol_stage_index",
        "TestingStage": "testing_stage",
        "PFProtocolName": "pf_protocol_name",
        "ChallengeAgentID": "challenge_agent_id",
        "ChallengeAgentName": "challenge_agent_name",
        "ChallengeAgentType": "challenge_agent_type",
    }

    return dataframe.rename(columns=rename_map)


def transform_methacholine(
    raw_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla analítica final de metacolina."""

    required_columns = [
        *VISIT_COLUMNS,
        "PFProtocolStageIndex",
        *STAGE_COLUMNS,
    ]

    validate_columns(
        dataframe=raw_dataframe,
        required_columns=required_columns,
    )

    visit_dataframe = build_visit_dimension(raw_dataframe)
    measurement_dataframe = build_stage_measurements(raw_dataframe)

    analytical_dataframe = visit_dataframe.merge(
        measurement_dataframe,
        on="PatVisitID",
        how="left",
        validate="one_to_one",
    )

    analytical_dataframe = add_derived_metrics(analytical_dataframe)
    analytical_dataframe = normalize_column_names(analytical_dataframe)

    analytical_dataframe = analytical_dataframe.sort_values(
        by=["visit_datetime", "pat_visit_id"],
        kind="stable",
    ).reset_index(drop=True)

    return analytical_dataframe
