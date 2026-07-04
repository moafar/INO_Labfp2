# src/extract/mip_mep.py
"""Extrae datos de MIP/MEP desde SQL Server."""

from pathlib import Path

import pandas as pd

from src.sqlserver import get_sqlserver_connection


# Define las rutas relativas del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = PROJECT_ROOT / "sql" / "extract_mip_mep.sql"


def load_sql_query() -> str:
    """Lee la consulta SQL de extracción MIP/MEP."""

    return SQL_FILE.read_text(encoding="utf-8")


def extract_mip_mep(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae resultados MIP/MEP entre dos fechas."""

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

    dataframe = extract_mip_mep(
        start_date="2023-03-01",
        end_date="2023-04-01",
    )

    print(f"Filas extraídas: {len(dataframe):,}")
    print(f"Columnas extraídas: {len(dataframe.columns):,}")
    print(dataframe.head())


if __name__ == "__main__":
    main()
