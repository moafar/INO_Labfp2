# src/config/pleth.py
"""Centraliza la configuración validada de variables Pleth."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PLETH_MAPPING_PATH = (
    PROJECT_ROOT
    / "data"
    / "catalogs"
    / "pleth_mapping_candidates.csv"
)

EXPECTED_PLETH_VARIABLES = 17


def load_pleth_mapping() -> pd.DataFrame:
    """Carga y valida la correspondencia funcional de PlethData."""

    if not PLETH_MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"No existe el catálogo Pleth: {PLETH_MAPPING_PATH}"
        )

    mapping = pd.read_csv(
        PLETH_MAPPING_PATH,
        dtype="string",
    )

    required_columns = {
        "variable_funcional",
        "campo_sql_candidato",
        "tipo_sql",
        "validado",
    }

    missing_columns = required_columns - set(mapping.columns)

    if missing_columns:
        raise ValueError(
            "Faltan columnas en el catálogo Pleth: "
            + ", ".join(sorted(missing_columns))
        )

    if len(mapping) != EXPECTED_PLETH_VARIABLES:
        raise ValueError(
            f"El catálogo contiene {len(mapping)} variables Pleth; "
            f"se esperaban {EXPECTED_PLETH_VARIABLES}."
        )

    if mapping["campo_sql_candidato"].isna().any():
        raise ValueError(
            "Existen variables Pleth sin campo SQL candidato."
        )

    if mapping["campo_sql_candidato"].duplicated().any():
        raise ValueError(
            "Existen campos SQL Pleth duplicados."
        )

    validated = (
        mapping["validado"]
        .str.strip()
        .str.lower()
        .eq("true")
    )

    if not validated.all():
        raise ValueError(
            "Existen correspondencias Pleth pendientes de validación."
        )

    return mapping


PLETH_MAPPING = load_pleth_mapping()

PLETH_SQL_COLUMNS = tuple(
    PLETH_MAPPING["campo_sql_candidato"].tolist()
)

PLETH_CATEGORICAL_COLUMNS = (
    "PlethATSCodes",
)

PLETH_NUMERIC_COLUMNS = tuple(
    column
    for column in PLETH_SQL_COLUMNS
    if column not in PLETH_CATEGORICAL_COLUMNS
)

PLETH_FUNCTIONAL_TO_SQL = dict(
    zip(
        PLETH_MAPPING["variable_funcional"],
        PLETH_MAPPING["campo_sql_candidato"],
        strict=True,
    )
)
