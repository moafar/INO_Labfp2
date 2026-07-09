# src/load/postgres.py
"""Carga archivos Parquet en tablas staging de PostgreSQL."""

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from src.postgres import get_postgres_engine


OPERATIONAL_COLUMNS = {
    "load_id",
    "loaded_at",
    "source_start_date",
    "source_end_date",
    "source_file",
    "source_file_hash",
    "pat_visit_id",
    "visit_datetime",
    "has_fvl",
    "has_dlco",
    "has_pleth",
    "has_mip_mep",
    "has_methacholine",
    "test_count",
}


def quote_identifier(identifier: str) -> str:
    """Escapa un identificador SQL de PostgreSQL."""

    return '"' + identifier.replace('"', '""') + '"'


def calculate_file_hash(file_path: Path) -> str:
    """Calcula el hash SHA-256 de un archivo."""

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha256.update(chunk)

    return sha256.hexdigest()


def get_existing_columns(
    target_schema: str,
    target_table: str,
) -> set[str]:
    """Obtiene las columnas existentes de una tabla PostgreSQL."""

    engine = get_postgres_engine()

    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = :target_schema
                  AND table_name = :target_table
                """
            ),
            {
                "target_schema": target_schema,
                "target_table": target_table,
            },
        ).scalars().all()

    return set(rows)


def infer_staging_column_type(column: str) -> str:
    """Define el tipo PostgreSQL para columnas agregadas dinámicamente."""

    if column == "pat_visit_id":
        return "bigint"

    if column == "visit_datetime":
        return "timestamp without time zone"

    if column in {
        "has_fvl",
        "has_dlco",
        "has_pleth",
        "has_mip_mep",
        "has_methacholine",
    }:
        return "boolean"

    if column == "test_count":
        return "bigint"

    return "text"


def ensure_staging_columns(
    dataframe: pd.DataFrame,
    target_schema: str,
    target_table: str,
) -> None:
    """Agrega a la tabla staging las columnas faltantes del DataFrame."""

    existing_columns = get_existing_columns(
        target_schema=target_schema,
        target_table=target_table,
    )

    missing_columns = [
        column
        for column in dataframe.columns
        if column not in existing_columns
    ]

    if not missing_columns:
        return

    engine = get_postgres_engine()

    with engine.begin() as connection:
        for column in missing_columns:
            column_type = infer_staging_column_type(column)
            sql = (
                f"ALTER TABLE {quote_identifier(target_schema)}."
                f"{quote_identifier(target_table)} "
                f"ADD COLUMN {quote_identifier(column)} {column_type}"
            )
            connection.execute(text(sql))


def prepare_staging_dataframe(
    dataframe: pd.DataFrame,
    load_id: str,
    loaded_at: datetime,
    source_start_date: str,
    source_end_date: str,
    source_file: str,
    source_file_hash: str,
) -> pd.DataFrame:
    """Agrega metadatos y normaliza columnas no operativas a texto."""

    staged_dataframe = dataframe.copy()

    staged_dataframe.insert(0, "source_file_hash", source_file_hash)
    staged_dataframe.insert(0, "source_file", source_file)
    staged_dataframe.insert(0, "source_end_date", source_end_date)
    staged_dataframe.insert(0, "source_start_date", source_start_date)
    staged_dataframe.insert(0, "loaded_at", loaded_at)
    staged_dataframe.insert(0, "load_id", load_id)

    for column in staged_dataframe.columns:
        if column not in OPERATIONAL_COLUMNS:
            staged_dataframe[column] = staged_dataframe[column].astype("string")

    return staged_dataframe


def register_load_start(
    load_id: str,
    pipeline_name: str,
    target_schema: str,
    target_table: str,
    source_file: str,
    source_file_hash: str,
    source_start_date: str,
    source_end_date: str,
    rows_read: int,
) -> None:
    """Registra el inicio de una carga en audit.load_control."""

    engine = get_postgres_engine()

    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    INSERT INTO audit.load_control (
                        load_id,
                        pipeline_name,
                        target_schema,
                        target_table,
                        source_system,
                        source_start_date,
                        source_end_date,
                        source_file,
                        source_file_hash,
                        rows_read,
                        rows_loaded,
                        status
                    )
                    VALUES (
                        :load_id,
                        :pipeline_name,
                        :target_schema,
                        :target_table,
                        'Breeze',
                        :source_start_date,
                        :source_end_date,
                        :source_file,
                        :source_file_hash,
                        :rows_read,
                        0,
                        'running'
                    )
                    """
                ),
                {
                    "load_id": load_id,
                    "pipeline_name": pipeline_name,
                    "target_schema": target_schema,
                    "target_table": target_table,
                    "source_start_date": source_start_date,
                    "source_end_date": source_end_date,
                    "source_file": source_file,
                    "source_file_hash": source_file_hash,
                    "rows_read": rows_read,
                },
            )
    except IntegrityError as error:
        raise RuntimeError(
            "Carga bloqueada: este archivo ya fue cargado previamente "
            f"en {target_schema}.{target_table}. "
            "No se insertaron filas nuevas en staging."
        ) from error


def register_load_success(load_id: str, rows_loaded: int) -> None:
    """Marca una carga como exitosa."""

    engine = get_postgres_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE audit.load_control
                SET
                    rows_loaded = :rows_loaded,
                    finished_at = now(),
                    status = 'success'
                WHERE load_id = :load_id
                """
            ),
            {
                "load_id": load_id,
                "rows_loaded": rows_loaded,
            },
        )


def register_load_error(load_id: str, error_message: str) -> None:
    """Marca una carga como fallida."""

    engine = get_postgres_engine()

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                UPDATE audit.load_control
                SET
                    finished_at = now(),
                    status = 'failed',
                    error_message = :error_message
                WHERE load_id = :load_id
                """
            ),
            {
                "load_id": load_id,
                "error_message": error_message,
            },
        )


def load_parquet_to_staging(
    parquet_file: Path,
    pipeline_name: str,
    target_table: str,
    source_start_date: str,
    source_end_date: str,
    target_schema: str = "staging",
) -> str:
    """Carga un archivo Parquet en una tabla staging y registra auditoría."""

    file_path = parquet_file.resolve()
    load_id = str(uuid.uuid4())
    loaded_at = datetime.now(UTC)
    file_hash = calculate_file_hash(file_path)

    dataframe = pd.read_parquet(file_path)
    rows_read = len(dataframe)

    register_load_start(
        load_id=load_id,
        pipeline_name=pipeline_name,
        target_schema=target_schema,
        target_table=target_table,
        source_file=str(file_path),
        source_file_hash=file_hash,
        source_start_date=source_start_date,
        source_end_date=source_end_date,
        rows_read=rows_read,
    )

    try:
        staged_dataframe = prepare_staging_dataframe(
            dataframe=dataframe,
            load_id=load_id,
            loaded_at=loaded_at,
            source_start_date=source_start_date,
            source_end_date=source_end_date,
            source_file=str(file_path),
            source_file_hash=file_hash,
        )

        ensure_staging_columns(
            dataframe=staged_dataframe,
            target_schema=target_schema,
            target_table=target_table,
        )

        engine = get_postgres_engine()

        with engine.begin() as connection:
            staged_dataframe.to_sql(
                name=target_table,
                con=connection,
                schema=target_schema,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )

        register_load_success(
            load_id=load_id,
            rows_loaded=rows_read,
        )

    except Exception as error:
        register_load_error(
            load_id=load_id,
            error_message=str(error),
        )
        raise

    return load_id
