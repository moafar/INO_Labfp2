# src/extract/ergoespirometry.py
"""Extrae pruebas de ergoespirometría desde SQL Server Breeze."""

from pathlib import Path

import pandas as pd

from src.sqlserver import get_sqlserver_connection


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_FILE = PROJECT_ROOT / "sql" / "extract_ergoespirometry.sql"


def load_sql_query() -> str:
    """Lee la consulta versionada de ergoespirometría."""

    return SQL_FILE.read_text(encoding="utf-8")


def extract_ergoespirometry(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae una fila por GXTest dentro de una ventana de visitas."""

    with get_sqlserver_connection() as connection:
        return pd.read_sql_query(
            sql=load_sql_query(),
            con=connection,
            params=[start_date, end_date],
        )
