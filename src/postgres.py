# src/postgres.py
"""Gestiona la conexión a PostgreSQL."""

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


REQUIRED_ENV_VARS = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DATABASE",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
]


def validate_environment() -> None:
    """Comprueba que existan las variables de entorno requeridas."""

    missing_vars = [
        variable
        for variable in REQUIRED_ENV_VARS
        if not os.getenv(variable)
    ]

    if missing_vars:
        raise RuntimeError(
            "Faltan variables de entorno PostgreSQL: "
            + ", ".join(missing_vars)
        )


def get_postgres_engine() -> Engine:
    """Crea un engine SQLAlchemy para PostgreSQL."""

    load_dotenv()
    validate_environment()

    user = os.environ["POSTGRES_USER"]
    password = quote_plus(os.environ["POSTGRES_PASSWORD"])
    host = os.environ["POSTGRES_HOST"]
    port = os.environ["POSTGRES_PORT"]
    database = os.environ["POSTGRES_DATABASE"]

    url = (
        f"postgresql+psycopg2://{user}:{password}"
        f"@{host}:{port}/{database}"
    )

    return create_engine(url)


def check_postgres_connection() -> dict[str, object]:
    """Valida la conexión y devuelve datos básicos de la sesión."""

    engine = get_postgres_engine()

    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT
                    current_database() AS database_name,
                    current_user AS user_name,
                    inet_server_addr() AS server_addr,
                    inet_server_port() AS server_port
                """
            )
        ).mappings().one()

    return dict(row)
