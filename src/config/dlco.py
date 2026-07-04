# src/config/dlco.py
"""Centraliza la configuración validada de variables DLCO."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DLCO_MAPPING_PATH = (
    PROJECT_ROOT
    / "data"
    / "catalogs"
    / "dlco_mapping_candidates.csv"
)

EXPECTED_DLCO_VARIABLES = 33


def load_dlco_mapping() -> pd.DataFrame:
    """Carga y valida la correspondencia funcional de DLCOData."""

    if not DLCO_MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"No existe el catálogo DLCO: {DLCO_MAPPING_PATH}"
        )

    mapping = pd.read_csv(
        DLCO_MAPPING_PATH,
        dtype="string",
    )

    required_columns = {
        "variable_funcional",
        "campo_sql_candidato",
        "validado",
    }

    missing_columns = required_columns - set(mapping.columns)

    if missing_columns:
        raise ValueError(
            "Faltan columnas en el catálogo DLCO: "
            + ", ".join(sorted(missing_columns))
        )

    if len(mapping) != EXPECTED_DLCO_VARIABLES:
        raise ValueError(
            f"El catálogo contiene {len(mapping)} variables DLCO; "
            f"se esperaban {EXPECTED_DLCO_VARIABLES}."
        )

    if mapping["campo_sql_candidato"].isna().any():
        raise ValueError(
            "Existen variables DLCO sin campo SQL candidato."
        )

    if mapping["campo_sql_candidato"].duplicated().any():
        raise ValueError(
            "Existen campos SQL DLCO duplicados."
        )

    validated = (
        mapping["validado"]
        .str.strip()
        .str.lower()
        .eq("true")
    )

    if not validated.all():
        raise ValueError(
            "Existen correspondencias DLCO pendientes de validación."
        )

    return mapping


DLCO_MAPPING = load_dlco_mapping()

DLCO_SQL_COLUMNS = tuple(
    DLCO_MAPPING["campo_sql_candidato"].tolist()
)

DLCO_CATEGORICAL_COLUMNS = (
    "DLCOATSCodes",
    "DLCOATSGrades",
)

DLCO_NUMERIC_COLUMNS = tuple(
    column
    for column in DLCO_SQL_COLUMNS
    if column not in DLCO_CATEGORICAL_COLUMNS
)

DLCO_FUNCTIONAL_TO_SQL = dict(
    zip(
        DLCO_MAPPING["variable_funcional"],
        DLCO_MAPPING["campo_sql_candidato"],
        strict=True,
    )
)
