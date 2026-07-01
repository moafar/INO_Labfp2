# src/build_patient_query_mapping.py
"""Genera la matriz base de correspondencia entre Patient Query y SQL Server."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SOURCE_PATH = Path("data/catalogs/patient_query_catalog.parquet")
OUTPUT_PATH = Path("data/catalogs/patient_query_mapping.csv")


def build_mapping(catalog: pd.DataFrame) -> pd.DataFrame:
    """Añade las columnas necesarias para documentar la correspondencia física."""

    mapping = catalog.copy()

    mapping["clasificacion_correspondencia"] = pd.NA
    mapping["tabla_sql"] = mapping["tabla_origen"]
    mapping["campo_sql"] = pd.NA
    mapping["formula"] = pd.NA
    mapping["unidad_sql"] = pd.NA
    mapping["observaciones"] = pd.NA
    mapping["estado_validacion"] = "pendiente"

    columns = [
        "clave_catalogo",
        "conjunto",
        "indice",
        "variable_original",
        "variable",
        "unidad",
        "tabla_origen",
        "fase",
        "tipo_resultado",
        "familia_clinica",
        "clasificacion_correspondencia",
        "tabla_sql",
        "campo_sql",
        "formula",
        "unidad_sql",
        "observaciones",
        "estado_validacion",
    ]

    return mapping[columns]


def validate_mapping(mapping: pd.DataFrame, catalog: pd.DataFrame) -> None:
    """Comprueba que la matriz conserve íntegramente el catálogo maestro."""

    if len(mapping) != len(catalog):
        raise ValueError(
            f"La matriz tiene {len(mapping)} filas y el catálogo {len(catalog)}."
        )

    if not mapping["clave_catalogo"].is_unique:
        raise ValueError("La matriz contiene claves de catálogo duplicadas.")

    if set(mapping["clave_catalogo"]) != set(catalog["clave_catalogo"]):
        raise ValueError("La matriz no conserva todas las claves del catálogo.")


def main() -> None:
    """Construye y guarda la matriz inicial."""

    catalog = pd.read_parquet(SOURCE_PATH)
    mapping = build_mapping(catalog)

    validate_mapping(mapping, catalog)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    mapping.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    print(f"Filas generadas: {len(mapping)}")
    print(f"Claves únicas: {mapping['clave_catalogo'].nunique()}")
    print(
        "Filas con tabla de origen indicada: "
        f"{mapping['tabla_sql'].notna().sum()}"
    )
    print(f"Salida: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
