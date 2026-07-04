# src/transform/pleth.py
"""Transforma la extracción PLETH en una tabla analítica por visita."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from src.config.pleth import (
    PLETH_CATEGORICAL_COLUMNS,
    PLETH_FUNCTIONAL_TO_SQL,
    PLETH_NUMERIC_COLUMNS,
    PLETH_SQL_COLUMNS,
)


# Parámetros funcionales que se transformarán a formato ancho.
PLETH_SQL_TO_FUNCTIONAL = {
    sql_column: functional_column
    for functional_column, sql_column in PLETH_FUNCTIONAL_TO_SQL.items()
}

PLETH_PARAMETERS = list(PLETH_NUMERIC_COLUMNS)
PLETH_NUMERIC_FUNCTIONAL_COLUMNS = [
    PLETH_SQL_TO_FUNCTIONAL[column]
    for column in PLETH_NUMERIC_COLUMNS
]
PLETH_CATEGORICAL_FUNCTIONAL_COLUMNS = [
    PLETH_SQL_TO_FUNCTIONAL[column]
    for column in PLETH_CATEGORICAL_COLUMNS
]

# Correspondencia entre tipos de fila y componentes analíticos.
EFFORT_TYPE_COMPONENTS = {
    1: "predicted",
    2: "pre",
    3: "post",
    5: "sd",
    6: "lln",
    7: "uln",
    9: "cv",
    10: "skewness",
}


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


def calculate_lms_zscore(
    observed: pd.Series,
    predicted: pd.Series,
    coefficient_variation: pd.Series,
    skewness: pd.Series,
) -> pd.Series:
    """Calcula z-scores mediante el método LMS."""

    observed = pd.to_numeric(observed, errors="coerce")
    predicted = pd.to_numeric(predicted, errors="coerce")
    coefficient_variation = pd.to_numeric(
        coefficient_variation,
        errors="coerce",
    )
    skewness = pd.to_numeric(skewness, errors="coerce")

    valid = (
        observed.notna()
        & predicted.notna()
        & coefficient_variation.notna()
        & skewness.notna()
        & observed.gt(0)
        & predicted.gt(0)
        & coefficient_variation.ne(0)
    )

    result = pd.Series(
        np.nan,
        index=observed.index,
        dtype="float64",
    )

    nonzero_l = valid & skewness.ne(0)

    result.loc[nonzero_l] = (
        (
            observed.loc[nonzero_l]
            / predicted.loc[nonzero_l]
        )
        ** skewness.loc[nonzero_l]
        - 1.0
    ) / (
        skewness.loc[nonzero_l]
        * coefficient_variation.loc[nonzero_l]
    )

    zero_l = valid & skewness.eq(0)

    result.loc[zero_l] = np.log(
        observed.loc[zero_l]
        / predicted.loc[zero_l]
    ) / coefficient_variation.loc[zero_l]

    return result


def build_visit_dimension(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Obtiene una única fila descriptiva por visita."""

    visit_dataframe = (
        raw_dataframe[VISIT_COLUMNS]
        .drop_duplicates(subset=["PatVisitID"])
        .copy()
    )

    return visit_dataframe


def build_pleth_measurements(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convierte los componentes PLETH a formato ancho por visita."""

    measurement_columns = [
        "PatVisitID",
        "EffortTypeID",
        *PLETH_SQL_COLUMNS,
    ]

    measurements = raw_dataframe[measurement_columns].copy()

    measurements = measurements[
        measurements["EffortTypeID"].isin(
            EFFORT_TYPE_COMPONENTS
        )
    ].copy()

    measurements["component"] = measurements[
        "EffortTypeID"
    ].map(EFFORT_TYPE_COMPONENTS)

    duplicate_mask = measurements.duplicated(
        subset=["PatVisitID", "component"],
        keep=False,
    )

    if duplicate_mask.any():
        duplicate_rows = (
            measurements.loc[
                duplicate_mask,
                ["PatVisitID", "EffortTypeID", "component"],
            ]
            .sort_values(
                by=["PatVisitID", "EffortTypeID"],
                kind="stable",
            )
        )

        raise ValueError(
            "Existen varias filas para la misma visita y componente PLETH:\n"
            + duplicate_rows.head(20).to_string(index=False)
        )

    long_dataframe = measurements.melt(
        id_vars=["PatVisitID", "component"],
        value_vars=PLETH_SQL_COLUMNS,
        var_name="parameter",
        value_name="value",
    )

    wide_dataframe = long_dataframe.pivot(
        index="PatVisitID",
        columns=["parameter", "component"],
        values="value",
    )

    wide_dataframe.columns = [
        f"{PLETH_SQL_TO_FUNCTIONAL[parameter]}_{component}"
        for parameter, component in wide_dataframe.columns
    ]

    numeric_columns = [
        f"{parameter}_{component}"
        for parameter in PLETH_NUMERIC_FUNCTIONAL_COLUMNS
        for component in EFFORT_TYPE_COMPONENTS.values()
        if f"{parameter}_{component}" in wide_dataframe.columns
    ]

    wide_dataframe[numeric_columns] = wide_dataframe[
        numeric_columns
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    wide_dataframe = wide_dataframe.copy()

    return wide_dataframe.reset_index()


def add_derived_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Añade porcentajes predichos y z-scores pre y post."""

    transformed = dataframe.copy()
    derived_columns: dict[str, pd.Series] = {}

    for parameter in PLETH_NUMERIC_FUNCTIONAL_COLUMNS:
        prefix = parameter.lower()

        predicted_column = f"{prefix}_predicted"
        cv_column = f"{prefix}_cv"
        skewness_column = f"{prefix}_skewness"

        for moment in ["pre", "post"]:
            observed_column = f"{prefix}_{moment}"

            if observed_column not in transformed.columns:
                continue

            observed = pd.to_numeric(
                transformed[observed_column],
                errors="coerce",
            )

            if predicted_column in transformed.columns:
                predicted = pd.to_numeric(
                    transformed[predicted_column],
                    errors="coerce",
                )

                derived_columns[
                    f"{prefix}_percent_predicted_{moment}"
                ] = pd.Series(
                    np.where(
                        predicted.gt(0),
                        (observed / predicted) * 100.0,
                        np.nan,
                    ),
                    index=transformed.index,
                    dtype="float64",
                )

            zscore = pd.Series(
                np.nan,
                index=transformed.index,
                dtype="float64",
            )

            required_lms_columns = {
                predicted_column,
                cv_column,
                skewness_column,
            }

            if required_lms_columns.issubset(transformed.columns):
                zscore = calculate_lms_zscore(
                    observed=observed,
                    predicted=transformed[predicted_column],
                    coefficient_variation=transformed[cv_column],
                    skewness=transformed[skewness_column],
                )

            sd_column = f"{prefix}_sd"
            required_sd_columns = {
                predicted_column,
                sd_column,
            }

            if required_sd_columns.issubset(transformed.columns):
                predicted = pd.to_numeric(
                    transformed[predicted_column],
                    errors="coerce",
                )
                sd = pd.to_numeric(
                    transformed[sd_column],
                    errors="coerce",
                )

                sd_valid = (
                    zscore.isna()
                    & observed.notna()
                    & predicted.notna()
                    & sd.notna()
                    & sd.gt(0)
                )

                zscore.loc[sd_valid] = (
                    observed.loc[sd_valid]
                    - predicted.loc[sd_valid]
                ) / sd.loc[sd_valid]

            derived_columns[f"{prefix}_zscore_{moment}"] = zscore

    if derived_columns:
        derived_dataframe = pd.DataFrame(
            derived_columns,
            index=transformed.index,
        )

        transformed = pd.concat(
            [transformed, derived_dataframe],
            axis=1,
        )

    return transformed


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
    }

    return dataframe.rename(columns=rename_map)


def transform_pleth(
    raw_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla analítica final de PLETH."""

    required_columns = [
        *VISIT_COLUMNS,
        "EffortTypeID",
        *PLETH_SQL_COLUMNS,
    ]

    validate_columns(
        dataframe=raw_dataframe,
        required_columns=required_columns,
    )

    visit_dataframe = build_visit_dimension(raw_dataframe)
    measurement_dataframe = build_pleth_measurements(
        raw_dataframe
    )

    analytical_dataframe = visit_dataframe.merge(
        measurement_dataframe,
        on="PatVisitID",
        how="left",
        validate="one_to_one",
    )

    analytical_dataframe = add_derived_metrics(
        analytical_dataframe
    )

    analytical_dataframe = normalize_column_names(
        analytical_dataframe
    )

    analytical_dataframe = analytical_dataframe.sort_values(
        by=["visit_datetime", "pat_visit_id"],
        kind="stable",
    ).reset_index(drop=True)

    return analytical_dataframe
