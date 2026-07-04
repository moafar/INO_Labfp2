# src/transform/mip_mep.py
"""Transforma la extracción MIP/MEP en una tabla analítica por visita."""

from collections.abc import Iterable

import pandas as pd


# Campos que describen al paciente y la visita.
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
    "MipMepTest",
]

MEASUREMENT_COLUMNS = [
    "MipDataID",
    "EffortTypeID",
    "EffortTypeDesc",
    "EffortTime",
    "EffortArtificial",
    "EffortManual",
    "EffortSelected",
    "PFProtocolStageIndex",
    "MIP",
    "MEP",
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


def validate_one_row_per_visit(dataframe: pd.DataFrame) -> None:
    """Comprueba que la extracción conserve una fila por visita."""

    duplicate_mask = dataframe.duplicated(
        subset=["PatVisitID"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicate_rows = (
            dataframe.loc[
                duplicate_mask,
                ["PatVisitID", "MipDataID", "EffortTypeID"],
            ]
            .sort_values(
                by=["PatVisitID", "MipDataID"],
                kind="stable",
            )
        )

        raise ValueError(
            "Existen varias filas MIP/MEP para la misma visita:\n"
            + duplicate_rows.head(20).to_string(index=False)
        )


def validate_valid_measurements(dataframe: pd.DataFrame) -> None:
    """Comprueba que toda fila tenga al menos MIP o MEP válido."""

    mip = pd.to_numeric(dataframe["MIP"], errors="coerce")
    mep = pd.to_numeric(dataframe["MEP"], errors="coerce")

    invalid_mask = mip.fillna(0).eq(0) & mep.fillna(0).eq(0)

    if invalid_mask.any():
        invalid_rows = dataframe.loc[
            invalid_mask,
            ["PatVisitID", "MipDataID", "MIP", "MEP"],
        ]

        raise ValueError(
            "Existen filas MIP/MEP sin valores clínicos válidos:\n"
            + invalid_rows.head(20).to_string(index=False)
        )


def normalize_column_names(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
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
        "MipMepTest": "mip_mep_test",
        "MipDataID": "mip_data_id",
        "EffortTypeID": "effort_type_id",
        "EffortTypeDesc": "effort_type_desc",
        "EffortTime": "effort_time",
        "EffortArtificial": "effort_artificial",
        "EffortManual": "effort_manual",
        "EffortSelected": "effort_selected",
        "PFProtocolStageIndex": "pf_protocol_stage_index",
        "MIP": "mip",
        "MEP": "mep",
    }

    return dataframe.rename(columns=rename_map)


def transform_mip_mep(
    raw_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla analítica final de MIP/MEP."""

    required_columns = [
        *VISIT_COLUMNS,
        *MEASUREMENT_COLUMNS,
    ]

    validate_columns(
        dataframe=raw_dataframe,
        required_columns=required_columns,
    )

    analytical_dataframe = raw_dataframe[
        required_columns
    ].copy()

    validate_one_row_per_visit(analytical_dataframe)
    validate_valid_measurements(analytical_dataframe)

    analytical_dataframe["MIP"] = pd.to_numeric(
        analytical_dataframe["MIP"],
        errors="coerce",
    )
    analytical_dataframe["MEP"] = pd.to_numeric(
        analytical_dataframe["MEP"],
        errors="coerce",
    )

    analytical_dataframe = normalize_column_names(
        analytical_dataframe
    )

    # Ordena cronológicamente la salida para facilitar su revisión.
    analytical_dataframe = analytical_dataframe.sort_values(
        by=["visit_datetime", "pat_visit_id"],
        kind="stable",
    ).reset_index(drop=True)

    return analytical_dataframe
