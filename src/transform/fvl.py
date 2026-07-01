# src/transform/fvl.py
"""Transforma la extracción FVL en una tabla analítica por visita."""

from collections.abc import Iterable

import numpy as np
import pandas as pd

from src.config.fvl import (
    FVL_NUMERIC_COLUMNS,
    FVL_SQL_COLUMNS,
)


# Parámetros funcionales que se transformarán a formato ancho.
FVL_PARAMETERS = list(FVL_NUMERIC_COLUMNS)

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

    # Solo se calculan resultados con insumos válidos y positivos.
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

    # Para L distinto de cero se aplica la fórmula general LMS.
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

    # Para L igual a cero se utiliza el límite logarítmico.
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


def build_fvl_measurements(raw_dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convierte los componentes FVL a formato ancho por visita."""

    measurement_columns = [
        "PatVisitID",
        "EffortTypeID",
        *FVL_PARAMETERS,
    ]

    measurements = raw_dataframe[measurement_columns].copy()

    # Conserva únicamente filas con significado analítico conocido.
    measurements = measurements[
        measurements["EffortTypeID"].isin(
            EFFORT_TYPE_COMPONENTS
        )
    ].copy()

    # Sustituye el código técnico por el componente analítico.
    measurements["component"] = measurements[
        "EffortTypeID"
    ].map(EFFORT_TYPE_COMPONENTS)

    # Verifica que cada visita tenga como máximo una fila por componente.
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
            "Existen varias filas para la misma visita y componente FVL:\n"
            + duplicate_rows.head(20).to_string(index=False)
        )

    # Lleva los parámetros a formato largo.
    long_dataframe = measurements.melt(
        id_vars=["PatVisitID", "component"],
        value_vars=FVL_PARAMETERS,
        var_name="parameter",
        value_name="value",
    )

    # Construye una columna por parámetro y componente.
    wide_dataframe = long_dataframe.pivot(
        index="PatVisitID",
        columns=["parameter", "component"],
        values="value",
    )

    # Convierte el índice multinivel en nombres compatibles con BigQuery.
    wide_dataframe.columns = [
        f"{parameter.lower()}_{component}"
        for parameter, component in wide_dataframe.columns
    ]

    return wide_dataframe.reset_index()


def add_derived_metrics(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Añade porcentajes predichos y z-scores pre y post."""

    transformed = dataframe.copy()
    derived_columns: dict[str, pd.Series] = {}

    for parameter in FVL_PARAMETERS:
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

            required_lms_columns = {
                predicted_column,
                cv_column,
                skewness_column,
            }

            if not required_lms_columns.issubset(
                transformed.columns
            ):
                continue

            derived_columns[
                f"{prefix}_zscore_{moment}"
            ] = calculate_lms_zscore(
                observed=observed,
                predicted=transformed[predicted_column],
                coefficient_variation=transformed[cv_column],
                skewness=transformed[skewness_column],
            )

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


def transform_fvl(
    raw_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Construye la tabla analítica final de espirometrías."""

    required_columns = [
        *VISIT_COLUMNS,
        "EffortTypeID",
        *FVL_PARAMETERS,
    ]

    validate_columns(
        dataframe=raw_dataframe,
        required_columns=required_columns,
    )

    visit_dataframe = build_visit_dimension(raw_dataframe)
    measurement_dataframe = build_fvl_measurements(
        raw_dataframe
    )

    # Une los datos descriptivos con las mediciones de la visita.
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

    # Ordena cronológicamente la salida para facilitar su revisión.
    analytical_dataframe = analytical_dataframe.sort_values(
        by=["visit_datetime", "pat_visit_id"],
        kind="stable",
    ).reset_index(drop=True)

    return analytical_dataframe