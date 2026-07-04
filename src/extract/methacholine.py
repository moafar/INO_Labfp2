# src/extract/methacholine.py
"""Extrae datos de broncoprovocación con metacolina desde SQL Server."""

from pathlib import Path

import pandas as pd

from src.sqlserver import get_sqlserver_connection


# Define las rutas relativas del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = PROJECT_ROOT / "sql" / "extract_methacholine.sql"


def load_sql_query() -> str:
    """Lee la consulta SQL de metacolina."""

    return SQL_FILE.read_text(encoding="utf-8")


def extract_methacholine(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae etapas de metacolina entre dos fechas."""

    query = load_sql_query()

    params = [
        start_date,
        end_date,
    ]

    with get_sqlserver_connection() as connection:
        dataframe = pd.read_sql_query(
            sql=query,
            con=connection,
            params=params,
        )

    return dataframe


def main() -> None:
    """Ejecuta una extracción pequeña de prueba."""

    dataframe = extract_methacholine(
        start_date="2023-08-01",
        end_date="2023-09-01",
    )

    print(f"Filas extraídas: {len(dataframe):,}")
    print(f"Columnas extraídas: {len(dataframe.columns):,}")
    print(dataframe.head())


if __name__ == "__main__":
    main()
