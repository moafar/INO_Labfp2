# tests/test_transform_fvl.py
"""Pruebas automatizadas de extracción y transformación FVL."""

import pandas as pd

from src.extract.fvl import extract_fvl
from src.transform.fvl import transform_fvl


START_DATE = "2025-05-14"
END_DATE = "2025-05-15"


def _build_sample() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye la muestra validada de SQL Server y su analítico."""

    raw_dataframe = extract_fvl(
        start_date=START_DATE,
        end_date=END_DATE,
    )

    analytical_dataframe = transform_fvl(raw_dataframe)

    return raw_dataframe, analytical_dataframe


def test_transform_creates_expected_shape() -> None:
    """Comprueba dimensiones esperadas en la muestra validada."""

    raw_dataframe, analytical_dataframe = _build_sample()

    assert len(raw_dataframe) == 557
    assert len(analytical_dataframe) == 31
    assert len(analytical_dataframe.columns) == 623


def test_transform_has_one_row_per_visit() -> None:
    """Comprueba que la granularidad sea una fila por visita."""

    _, analytical_dataframe = _build_sample()

    assert analytical_dataframe["pat_visit_id"].is_unique
    assert analytical_dataframe["pat_visit_guid"].is_unique


def test_transform_required_columns_exist() -> None:
    """Comprueba presencia de columnas clínicas principales."""

    _, analytical_dataframe = _build_sample()

    required_columns = {
        "patient_guid",
        "patient_id_num",
        "pat_visit_id",
        "pat_visit_guid",
        "visit_datetime",
        "fvc_pre",
        "fev1_pre",
        "fev1fvc_pre",
        "fvc_post",
        "fev1_post",
        "fev1fvc_post",
        "fvc_predicted",
        "fev1_predicted",
        "fev1fvc_predicted",
        "fvc_sd",
        "fev1_sd",
        "fev1fvc_sd",
        "fvc_percent_predicted_pre",
        "fev1_percent_predicted_pre",
        "fvc_zscore_pre",
        "fev1_zscore_pre",
    }

    missing_columns = required_columns - set(analytical_dataframe.columns)

    assert not missing_columns


def test_transform_numeric_columns_are_numeric() -> None:
    """Comprueba que las columnas analíticas numéricas no queden como object."""

    _, analytical_dataframe = _build_sample()

    categorical_columns = {
        "testgradeats_predicted",
        "testgradeats_sd",
        "testgradeats_cv",
        "testgradeats_skewness",
        "testgradeats_pre",
        "testgradeats_post",
        "testgradenlhep_predicted",
        "testgradenlhep_sd",
        "testgradenlhep_cv",
        "testgradenlhep_skewness",
        "testgradenlhep_pre",
        "testgradenlhep_post",
    }

    numeric_suffixes = (
        "_predicted",
        "_sd",
        "_cv",
        "_skewness",
        "_pre",
        "_post",
    )

    suspect_columns = [
        column
        for column in analytical_dataframe.columns
        if column.endswith(numeric_suffixes)
        and column not in categorical_columns
        and analytical_dataframe[column].dtype == "object"
    ]

    assert not suspect_columns


def test_percent_predicted_formula_for_fvc_pre() -> None:
    """Comprueba el cálculo de porcentaje del predicho para FVC pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["fvc_predicted"].notna()
        & (analytical_dataframe["fvc_predicted"] != 0)
        & analytical_dataframe["fvc_pre"].notna()
    ].copy()

    expected = (
        valid_rows["fvc_pre"]
        / valid_rows["fvc_predicted"]
        * 100
    )

    difference = (
        valid_rows["fvc_percent_predicted_pre"]
        - expected
    ).abs()

    assert difference.max() < 0.000001


def test_zscore_formula_for_fvc_pre() -> None:
    """Comprueba el cálculo de z-score LMS para FVC pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["fvc_pre"].notna()
        & analytical_dataframe["fvc_predicted"].notna()
        & analytical_dataframe["fvc_cv"].notna()
        & analytical_dataframe["fvc_skewness"].notna()
        & (analytical_dataframe["fvc_pre"] > 0)
        & (analytical_dataframe["fvc_predicted"] > 0)
        & (analytical_dataframe["fvc_cv"] != 0)
        & (analytical_dataframe["fvc_skewness"] != 0)
    ].copy()

    expected = (
        (
            (
                valid_rows["fvc_pre"]
                / valid_rows["fvc_predicted"]
            )
            ** valid_rows["fvc_skewness"]
            - 1
        )
        / (
            valid_rows["fvc_skewness"]
            * valid_rows["fvc_cv"]
        )
    )

    difference = (
        valid_rows["fvc_zscore_pre"]
        - expected
    ).abs()

    assert difference.max() < 0.000001


def test_extractor_returns_only_visits_with_efforts() -> None:
    """Comprueba que toda visita extraída tenga al menos una maniobra."""

    raw_dataframe, analytical_dataframe = _build_sample()

    effort_counts = (
        raw_dataframe.loc[
            raw_dataframe["EffortTypeID"] == 0,
            "PatVisitID",
        ]
        .value_counts()
    )

    missing_efforts = [
        pat_visit_id
        for pat_visit_id in analytical_dataframe["pat_visit_id"]
        if pat_visit_id not in effort_counts.index
    ]

    assert not missing_efforts


def test_zscore_uses_sd_formula_when_lms_is_not_available() -> None:
    """Comprueba fallback por SD cuando LMS no produce z-score."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["fefmax_pre"].notna()
        & analytical_dataframe["fefmax_predicted"].notna()
        & analytical_dataframe["fefmax_sd"].notna()
        & analytical_dataframe["fefmax_sd"].gt(0)
        & analytical_dataframe["fefmax_cv"].fillna(0).eq(0)
        & analytical_dataframe["fefmax_skewness"].fillna(0).eq(0)
    ].copy()

    expected = (
        valid_rows["fefmax_pre"]
        - valid_rows["fefmax_predicted"]
    ) / valid_rows["fefmax_sd"]

    pd.testing.assert_series_equal(
        valid_rows["fefmax_zscore_pre"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )
