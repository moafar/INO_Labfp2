# src/extract/pleth.py
"""Extrae datos de Pleth desde SQL Server."""

from pathlib import Path

import pandas as pd

from src.config.pleth import PLETH_SQL_COLUMNS
from src.sqlserver import get_sqlserver_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = PROJECT_ROOT / "sql" / "extract_pleth.sql"


def load_sql_query() -> str:
    """Lee la consulta SQL e incorpora las columnas Pleth configuradas."""

    query = SQL_FILE.read_text(encoding="utf-8")

    column_lines = []

    for index, column in enumerate(PLETH_SQL_COLUMNS):
        suffix = "," if index < len(PLETH_SQL_COLUMNS) - 1 else ""
        column_lines.append(f"    pl.{column}{suffix}")

    pleth_columns_sql = "\n".join(column_lines)

    marker = "    -- PLETH_COLUMNS"

    if marker not in query:
        raise ValueError(
            "La consulta SQL no contiene el marcador -- PLETH_COLUMNS."
        )

    return query.replace(
        marker,
        pleth_columns_sql,
    )


def extract_pleth(
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

    dataframe = extract_pleth(
        start_date="2025-05-14",
        end_date="2025-05-15",
    )

    print(f"Filas extraídas: {len(dataframe):,}")
    print(f"Columnas extraídas: {len(dataframe.columns):,}")
    print(dataframe.head())


if __name__ == "__main__":
    main()
