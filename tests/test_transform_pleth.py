# tests/test_transform_pleth.py
"""Pruebas automatizadas de extracción y transformación Pleth."""

import pandas as pd

from src.extract.pleth import extract_pleth
from src.transform.pleth import transform_pleth


START_DATE = "2025-05-14"
END_DATE = "2025-05-15"


def _build_sample() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye la muestra validada de SQL Server y su analítico."""

    raw_dataframe = extract_pleth(
        start_date=START_DATE,
        end_date=END_DATE,
    )

    analytical_dataframe = transform_pleth(raw_dataframe)

    return raw_dataframe, analytical_dataframe


def test_transform_creates_expected_shape() -> None:
    """Comprueba dimensiones esperadas en la muestra validada."""

    raw_dataframe, analytical_dataframe = _build_sample()

    assert len(raw_dataframe) == 220
    assert raw_dataframe["PatVisitID"].nunique() == 18
    assert len(analytical_dataframe) == 18
    assert len(analytical_dataframe.columns) == 187


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
        "tgv_pleth_pre",
        "tgv_pleth_post",
        "rv_pleth_pre",
        "rv_pleth_post",
        "tlc_pleth_pre",
        "tlc_pleth_post",
        "rv_tlc_pleth_pre",
        "rv_tlc_pleth_post",
        "raw_pre",
        "raw_post",
        "s_gaw_pre",
        "s_gaw_post",
        "tgv_pleth_predicted",
        "tgv_pleth_sd",
        "tgv_pleth_cv",
        "tgv_pleth_skewness",
        "tgv_pleth_percent_predicted_pre",
        "tgv_pleth_percent_predicted_post",
        "tgv_pleth_zscore_pre",
        "tgv_pleth_zscore_post",
        "pleth_ats_codes_pre",
        "pleth_ats_codes_post",
    }

    missing_columns = required_columns - set(analytical_dataframe.columns)

    assert not missing_columns


def test_transform_numeric_columns_are_numeric() -> None:
    """Comprueba que las columnas analíticas numéricas no queden como object."""

    _, analytical_dataframe = _build_sample()

    categorical_columns = {
        "pleth_ats_codes_predicted",
        "pleth_ats_codes_sd",
        "pleth_ats_codes_cv",
        "pleth_ats_codes_skewness",
        "pleth_ats_codes_pre",
        "pleth_ats_codes_post",
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


def test_percent_predicted_formula_for_tgv_pleth_pre() -> None:
    """Comprueba el porcentaje del predicho para TGVPleth pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["tgv_pleth_predicted"].notna()
        & (analytical_dataframe["tgv_pleth_predicted"] != 0)
        & analytical_dataframe["tgv_pleth_pre"].notna()
    ].copy()

    expected = (
        valid_rows["tgv_pleth_pre"]
        / valid_rows["tgv_pleth_predicted"]
        * 100
    )

    difference = (
        valid_rows["tgv_pleth_percent_predicted_pre"]
        - expected
    ).abs()

    assert difference.max() < 0.000001


def test_percent_predicted_formula_for_tgv_pleth_post() -> None:
    """Comprueba el porcentaje del predicho para TGVPleth post."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["tgv_pleth_predicted"].notna()
        & (analytical_dataframe["tgv_pleth_predicted"] != 0)
        & analytical_dataframe["tgv_pleth_post"].notna()
    ].copy()

    expected = (
        valid_rows["tgv_pleth_post"]
        / valid_rows["tgv_pleth_predicted"]
        * 100
    )

    difference = (
        valid_rows["tgv_pleth_percent_predicted_post"]
        - expected
    ).abs()

    assert difference.max() < 0.000001


def test_zscore_formula_for_tgv_pleth_pre() -> None:
    """Comprueba el cálculo de z-score LMS para TGVPleth pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["tgv_pleth_pre"].notna()
        & analytical_dataframe["tgv_pleth_predicted"].notna()
        & analytical_dataframe["tgv_pleth_cv"].notna()
        & analytical_dataframe["tgv_pleth_skewness"].notna()
        & (analytical_dataframe["tgv_pleth_pre"] > 0)
        & (analytical_dataframe["tgv_pleth_predicted"] > 0)
        & (analytical_dataframe["tgv_pleth_cv"] != 0)
        & (analytical_dataframe["tgv_pleth_skewness"] != 0)
    ].copy()

    expected = (
        (
            (
                valid_rows["tgv_pleth_pre"]
                / valid_rows["tgv_pleth_predicted"]
            )
            ** valid_rows["tgv_pleth_skewness"]
            - 1
        )
        / (
            valid_rows["tgv_pleth_skewness"]
            * valid_rows["tgv_pleth_cv"]
        )
    )

    difference = (
        valid_rows["tgv_pleth_zscore_pre"]
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
