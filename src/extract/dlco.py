# src/extract/dlco.py
"""Extrae datos de DLCO desde SQL Server."""

from pathlib import Path

import pandas as pd

from src.sqlserver import get_sqlserver_connection
from src.config.dlco import DLCO_SQL_COLUMNS


# Define las rutas relativas del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = PROJECT_ROOT / "sql" / "extract_dlco.sql"


def load_sql_query() -> str:
    """Lee la consulta SQL e incorpora las columnas DLCO configuradas."""

    query = SQL_FILE.read_text(encoding="utf-8")

    column_lines = []

    for index, column in enumerate(DLCO_SQL_COLUMNS):
        suffix = "," if index < len(DLCO_SQL_COLUMNS) - 1 else ""
        column_lines.append(f"    dl.{column}{suffix}")

    dlco_columns_sql = "\n".join(column_lines)

    marker = "    -- DLCO_COLUMNS"

    if marker not in query:
        raise ValueError(
            "La consulta SQL no contiene el marcador -- DLCO_COLUMNS."
        )

    return query.replace(
        marker,
        dlco_columns_sql,
    )


def extract_dlco(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae resultados entre dos fechas."""

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

    dataframe = extract_dlco(
        start_date="2025-05-14",
        end_date="2025-05-15",
    )

    print(f"Filas extraídas: {len(dataframe):,}")
    print(f"Columnas extraídas: {len(dataframe.columns):,}")
    print(dataframe.head())


if __name__ == "__main__":
    main()
