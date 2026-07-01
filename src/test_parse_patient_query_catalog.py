# src/test_parse_patient_query_catalog.py
"""Pruebas del parser del catálogo funcional de Patient Query."""

from pathlib import Path

from parse_patient_query_catalog import (
    parse_catalog,
    validate_catalog,
)

import pandas as pd

CATALOG_PATH = Path("catalogo_completo_campos.txt")


def test_catalog_structure() -> None:
    """Comprueba conteos, conjuntos, índices y claves del catálogo."""

    dataframe, declared_counts = parse_catalog(CATALOG_PATH)

    validate_catalog(dataframe, declared_counts)

    assert dataframe["conjunto"].nunique() == 28
    assert len(dataframe) == 8309
    assert dataframe["clave_catalogo"].is_unique


def test_table_and_unit_extraction() -> None:
    """Comprueba la separación de nombres, unidades y tablas físicas."""

    dataframe, _ = parse_catalog(CATALOG_PATH)

    row = dataframe.loc[
        dataframe["clave_catalogo"] == "PF Pre::90"
    ].iloc[0]

    assert row["variable_original"] == "FEV1 (L) [FVLData]"
    assert row["variable"] == "FEV1"
    assert row["unidad"] == "L"
    assert row["tabla_origen"] == "FVLData"
    assert row["familia_clinica"] == "espirometria"


def test_functional_qualifiers_are_preserved() -> None:
    """Comprueba que calificadores funcionales no se traten como unidades."""

    dataframe, _ = parse_catalog(CATALOG_PATH)

    ats_row = dataframe.loc[
        dataframe["clave_catalogo"] == "PF Pre::288"
    ].iloc[0]

    assert ats_row["variable"] == "TestGrade(ATS)"
    assert pd.isna(ats_row["unidad"])

    calc_row = dataframe.loc[
        dataframe["clave_catalogo"] == "PF Pre::58"
    ].iloc[0]

    assert calc_row["variable"] == "f/Vt (calc)"
    assert pd.isna(calc_row["unidad"])
