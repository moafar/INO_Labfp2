# tests/test_transform_dlco.py
"""Pruebas automatizadas de extracción y transformación DLCO."""

import pandas as pd

from src.extract.dlco import extract_dlco
from src.transform.dlco import transform_dlco


START_DATE = "2025-05-14"
END_DATE = "2025-05-15"


def _build_sample() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye la muestra validada de SQL Server y su analítico."""

    raw_dataframe = extract_dlco(
        start_date=START_DATE,
        end_date=END_DATE,
    )

    analytical_dataframe = transform_dlco(raw_dataframe)

    return raw_dataframe, analytical_dataframe


def test_transform_creates_expected_shape() -> None:
    """Comprueba dimensiones esperadas en la muestra validada."""

    raw_dataframe, analytical_dataframe = _build_sample()

    assert len(raw_dataframe) == 111
    assert raw_dataframe["PatVisitID"].nunique() == 17
    assert len(analytical_dataframe) == 17
    assert len(analytical_dataframe.columns) == 248


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
        "dlcounc_pre",
        "dlcocor_pre",
        "va_pre",
        "kco_pre",
        "bht_pre",
        "ivc_pre",
        "dlcounc_predicted",
        "dlcocor_predicted",
        "va_predicted",
        "kco_predicted",
        "dlcounc_sd",
        "dlcocor_sd",
        "va_sd",
        "kco_sd",
        "dlcounc_percent_predicted_pre",
        "dlcocor_percent_predicted_pre",
        "va_percent_predicted_pre",
        "kco_percent_predicted_pre",
        "dlcounc_zscore_pre",
        "dlcocor_zscore_pre",
    }

    missing_columns = required_columns - set(analytical_dataframe.columns)

    assert not missing_columns


def test_transform_numeric_columns_are_numeric() -> None:
    """Comprueba que las columnas analíticas numéricas no queden como object."""

    _, analytical_dataframe = _build_sample()

    categorical_columns = {
        "dlcoatscodes_predicted",
        "dlcoatscodes_sd",
        "dlcoatscodes_cv",
        "dlcoatscodes_skewness",
        "dlcoatscodes_pre",
        "dlcoatscodes_post",
        "dlcoatsgrades_predicted",
        "dlcoatsgrades_sd",
        "dlcoatsgrades_cv",
        "dlcoatsgrades_skewness",
        "dlcoatsgrades_pre",
        "dlcoatsgrades_post",
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


def test_percent_predicted_formula_for_dlcounc_pre() -> None:
    """Comprueba el cálculo de porcentaje del predicho para DLCOunc pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["dlcounc_predicted"].notna()
        & (analytical_dataframe["dlcounc_predicted"] != 0)
        & analytical_dataframe["dlcounc_pre"].notna()
    ].copy()

    expected = (
        valid_rows["dlcounc_pre"]
        / valid_rows["dlcounc_predicted"]
        * 100
    )

    difference = (
        valid_rows["dlcounc_percent_predicted_pre"]
        - expected
    ).abs()

    assert difference.max() < 0.000001


def test_zscore_formula_for_dlcounc_pre() -> None:
    """Comprueba el cálculo de z-score LMS para DLCOunc pre."""

    _, analytical_dataframe = _build_sample()

    valid_rows = analytical_dataframe[
        analytical_dataframe["dlcounc_pre"].notna()
        & analytical_dataframe["dlcounc_predicted"].notna()
        & analytical_dataframe["dlcounc_cv"].notna()
        & analytical_dataframe["dlcounc_skewness"].notna()
        & (analytical_dataframe["dlcounc_pre"] > 0)
        & (analytical_dataframe["dlcounc_predicted"] > 0)
        & (analytical_dataframe["dlcounc_cv"] != 0)
        & (analytical_dataframe["dlcounc_skewness"] != 0)
    ].copy()

    expected = (
        (
            (
                valid_rows["dlcounc_pre"]
                / valid_rows["dlcounc_predicted"]
            )
            ** valid_rows["dlcounc_skewness"]
            - 1
        )
        / (
            valid_rows["dlcounc_skewness"]
            * valid_rows["dlcounc_cv"]
        )
    )

    difference = (
        valid_rows["dlcounc_zscore_pre"]
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


def test_dlva_zscore_uses_sd_formula_when_lms_is_not_available() -> None:
    """Calcula z-score DL/VA con fórmula por SD si no hay LMS."""

    raw_dataframe, _ = _build_sample()
    analytical_dataframe = transform_dlco(raw_dataframe)

    assert "dlva_zscore_pre" in analytical_dataframe.columns

    valid_rows = analytical_dataframe[
        analytical_dataframe["dlva_pre"].notna()
        & analytical_dataframe["dlva_predicted"].notna()
        & analytical_dataframe["dlva_sd"].notna()
        & analytical_dataframe["dlva_sd"].gt(0)
    ]

    assert not valid_rows.empty

    expected = (
        valid_rows["dlva_pre"]
        - valid_rows["dlva_predicted"]
    ) / valid_rows["dlva_sd"]

    pd.testing.assert_series_equal(
        valid_rows["dlva_zscore_pre"].reset_index(drop=True),
        expected.reset_index(drop=True),
        check_names=False,
    )
