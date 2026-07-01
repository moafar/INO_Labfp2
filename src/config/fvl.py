# src/config/fvl.py
"""Centraliza la configuración validada de variables FVL."""

from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FVL_MAPPING_PATH = (
    PROJECT_ROOT
    / "data"
    / "catalogs"
    / "fvl_mapping_candidates.csv"
)

EXPECTED_FVL_VARIABLES = 61


def load_fvl_mapping() -> pd.DataFrame:
    """Carga y valida la correspondencia funcional de FVLData."""

    if not FVL_MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"No existe el catálogo FVL: {FVL_MAPPING_PATH}"
        )

    mapping = pd.read_csv(
        FVL_MAPPING_PATH,
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
            "Faltan columnas en el catálogo FVL: "
            + ", ".join(sorted(missing_columns))
        )

    if len(mapping) != EXPECTED_FVL_VARIABLES:
        raise ValueError(
            f"El catálogo contiene {len(mapping)} variables FVL; "
            f"se esperaban {EXPECTED_FVL_VARIABLES}."
        )

    if mapping["campo_sql_candidato"].isna().any():
        raise ValueError(
            "Existen variables FVL sin campo SQL candidato."
        )

    if mapping["campo_sql_candidato"].duplicated().any():
        raise ValueError(
            "Existen campos SQL FVL duplicados."
        )

    validated = (
        mapping["validado"]
        .str.strip()
        .str.lower()
        .eq("true")
    )

    if not validated.all():
        raise ValueError(
            "Existen correspondencias FVL pendientes de validación."
        )

    return mapping


FVL_MAPPING = load_fvl_mapping()

FVL_SQL_COLUMNS = tuple(
    FVL_MAPPING["campo_sql_candidato"].tolist()
)

FVL_FUNCTIONAL_TO_SQL = dict(
    zip(
        FVL_MAPPING["variable_funcional"],
        FVL_MAPPING["campo_sql_candidato"],
        strict=True,
    )
)
