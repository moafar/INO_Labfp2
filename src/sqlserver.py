# src/sqlserver.py
"""Gestiona conexiones robustas y reutilizables con SQL Server."""

import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pyodbc
from dotenv import load_dotenv


# Localiza la raíz del proyecto y carga explícitamente su archivo .env.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


def build_connection_string() -> str:
    """Construye la cadena de conexión a SQL Server."""

    required_variables = [
        "SQLSERVER_HOST",
        "SQLSERVER_PORT",
        "SQLSERVER_DATABASE",
        "SQLSERVER_USER",
        "SQLSERVER_PASSWORD",
        "SQLSERVER_DRIVER",
    ]

    # Comprueba que todas las variables obligatorias estén configuradas.
    missing = [
        variable
        for variable in required_variables
        if not os.getenv(variable)
    ]

    if missing:
        raise ValueError(
            "Faltan variables de entorno: "
            + ", ".join(missing)
        )

    # Se confía en el certificado del servidor interno.
    return (
        f"DRIVER={{{os.environ['SQLSERVER_DRIVER']}}};"
        f"SERVER={os.environ['SQLSERVER_HOST']},"
        f"{os.environ['SQLSERVER_PORT']};"
        f"DATABASE={os.environ['SQLSERVER_DATABASE']};"
        f"UID={os.environ['SQLSERVER_USER']};"
        f"PWD={os.environ['SQLSERVER_PASSWORD']};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
        "Connection Timeout=30;"
    )


def open_sqlserver_connection(
    max_attempts: int = 3,
    retry_delay_seconds: int = 5,
) -> pyodbc.Connection:
    """Abre una conexión aplicando reintentos ante fallos transitorios."""

    connection_string = build_connection_string()
    last_error: pyodbc.Error | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            print(
                f"Conectando con SQL Server "
                f"(intento {attempt}/{max_attempts})..."
            )

            return pyodbc.connect(connection_string)

        except pyodbc.Error as error:
            last_error = error

            if attempt < max_attempts:
                print(
                    "La conexión falló. "
                    f"Nuevo intento en {retry_delay_seconds} segundos."
                )
                time.sleep(retry_delay_seconds)

    raise ConnectionError(
        f"No fue posible conectar con SQL Server "
        f"después de {max_attempts} intentos."
    ) from last_error


@contextmanager
def get_sqlserver_connection() -> Iterator[pyodbc.Connection]:
    """Abre y cierra de forma segura una conexión con SQL Server."""

    connection = open_sqlserver_connection()

    try:
        yield connection
    finally:
        connection.close()