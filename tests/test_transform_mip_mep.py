# tests/test_transform_mip_mep.py
"""Pruebas automatizadas de extracción y transformación MIP/MEP."""

import pandas as pd

from src.extract.mip_mep import extract_mip_mep
from src.transform.mip_mep import transform_mip_mep


START_DATE = "2023-03-01"
END_DATE = "2023-04-01"


def _build_sample() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Construye la muestra validada de SQL Server y su analítico."""

    raw_dataframe = extract_mip_mep(
        start_date=START_DATE,
        end_date=END_DATE,
    )

    analytical_dataframe = transform_mip_mep(raw_dataframe)

    return raw_dataframe, analytical_dataframe


def test_transform_creates_expected_shape() -> None:
    """Comprueba dimensiones esperadas en la muestra validada."""

    raw_dataframe, analytical_dataframe = _build_sample()

    assert len(raw_dataframe) == 6
    assert raw_dataframe["PatVisitID"].nunique() == 6
    assert len(analytical_dataframe) == 6
    assert len(analytical_dataframe.columns) == 32


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
        "mip_data_id",
        "effort_type_id",
        "effort_type_desc",
        "effort_time",
        "mip",
        "mep",
        "mip_mep_test",
    }

    missing_columns = required_columns - set(analytical_dataframe.columns)

    assert not missing_columns


def test_transform_numeric_columns_are_numeric() -> None:
    """Comprueba que MIP y MEP sean columnas numéricas."""

    _, analytical_dataframe = _build_sample()

    assert pd.api.types.is_numeric_dtype(analytical_dataframe["mip"])
    assert pd.api.types.is_numeric_dtype(analytical_dataframe["mep"])


def test_extractor_returns_only_valid_baseline_rows() -> None:
    """Comprueba que la extracción solo incluya resultados basales válidos."""

    raw_dataframe, _ = _build_sample()

    assert set(raw_dataframe["EffortTypeID"]) == {2}

    invalid_rows = raw_dataframe[
        (raw_dataframe["MIP"].fillna(0) == 0)
        & (raw_dataframe["MEP"].fillna(0) == 0)
    ]

    assert invalid_rows.empty


def test_extractor_does_not_require_patvisit_indicator() -> None:
    """Comprueba que MipMepTest sea auxiliar y no criterio estructural."""

    raw_dataframe, analytical_dataframe = _build_sample()

    assert "MipMepTest" in raw_dataframe.columns
    assert "mip_mep_test" in analytical_dataframe.columns
