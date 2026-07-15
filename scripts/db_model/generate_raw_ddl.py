# scripts/db_model/generate_raw_ddl.py
"""Genera DDL PostgreSQL raw desde inventarios SQL Server."""

from pathlib import Path
import re

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
COLUMNS_PATH = (
    PROJECT_ROOT
    / "docs"
    / "db_model"
    / "raw_inventory"
    / "breeze_raw_columns_inventory.tsv"
)
CONSTRAINTS_PATH = (
    PROJECT_ROOT
    / "docs"
    / "db_model"
    / "raw_inventory"
    / "breeze_raw_constraints_inventory.tsv"
)
OUTPUT_PATH = PROJECT_ROOT / "sql" / "raw" / "001_create_raw_tables.sql"


def to_snake_case(name: str) -> str:
    """Convierte nombres Breeze/PascalCase a snake_case estable."""
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    name = name.replace("/", "_")
    name = name.replace("%", "percent")
    name = re.sub(r"[^a-zA-Z0-9]+", "_", name)
    name = re.sub(r"_+", "_", name)
    return name.strip("_").lower()


def map_sqlserver_type(row: pd.Series) -> str:
    """Mapea tipos SQL Server a tipos PostgreSQL para capa raw."""
    sql_type = str(row["sqlserver_type"]).lower()
    max_length = int(row["max_length"])
    precision = int(row["precision"])
    scale = int(row["scale"])

    if sql_type in {"int"}:
        return "integer"
    if sql_type in {"bigint"}:
        return "bigint"
    if sql_type in {"smallint"}:
        return "smallint"
    if sql_type in {"tinyint"}:
        return "smallint"
    if sql_type in {"bit"}:
        return "boolean"
    if sql_type in {"float"}:
        return "double precision"
    if sql_type in {"real"}:
        return "real"
    if sql_type in {"datetime", "smalldatetime", "datetime2"}:
        return "timestamp without time zone"
    if sql_type in {"date"}:
        return "date"
    if sql_type in {"uniqueidentifier"}:
        return "uuid"
    if sql_type in {"varbinary", "binary", "image"}:
        return "bytea"
    if sql_type in {"nvarchar", "varchar", "nchar", "char", "ntext", "text"}:
        if max_length == -1:
            return "text"

        # nvarchar/nchar max_length viene en bytes; en SQL Server usa 2 bytes por carácter.
        if sql_type.startswith("n"):
            char_length = max_length // 2
        else:
            char_length = max_length

        if char_length <= 0:
            return "text"

        return f"varchar({char_length})"

    if sql_type in {"decimal", "numeric", "money", "smallmoney"}:
        if precision > 0:
            return f"numeric({precision}, {scale})"
        return "numeric"

    return "text"


def nullable_sql(row: pd.Series) -> str:
    """Devuelve cláusula NULL/NOT NULL."""
    return "" if int(row["is_nullable"]) == 1 else " NOT NULL"


def build_create_table(table_name: str, table_columns: pd.DataFrame, pk_columns: list[str]) -> str:
    """Construye CREATE TABLE para una tabla raw."""
    target_table = to_snake_case(table_name)

    lines = [f"CREATE TABLE IF NOT EXISTS raw.{target_table} ("]

    column_lines = []
    for _, row in table_columns.sort_values("column_id").iterrows():
        target_column = to_snake_case(str(row["source_column"]))
        pg_type = map_sqlserver_type(row)
        column_lines.append(f"    {target_column} {pg_type}{nullable_sql(row)}")

    column_lines.extend(
        [
            "    _snapshot_id bigint",
            "    _load_id bigint",
            "    _loaded_at timestamp without time zone NOT NULL DEFAULT now()",
            "    _source_row_hash text",
        ]
    )

    if pk_columns:
        pk_target_columns = ", ".join(to_snake_case(col) for col in pk_columns)
        column_lines.append(f"    PRIMARY KEY ({pk_target_columns})")

    lines.append(",\n".join(column_lines))
    lines.append(");")

    return "\n".join(lines)


def build_index(table_name: str, source_column: str) -> str:
    """Construye índice para columna relacional raw."""
    target_table = to_snake_case(table_name)
    target_column = to_snake_case(source_column)
    index_name = f"idx_raw_{target_table}_{target_column}"
    return (
        f"CREATE INDEX IF NOT EXISTS {index_name}\n"
        f"    ON raw.{target_table} ({target_column});"
    )


def main() -> None:
    """Genera archivo SQL raw."""
    columns = pd.read_csv(COLUMNS_PATH, sep="\t", dtype=str).fillna("")
    constraints = pd.read_csv(CONSTRAINTS_PATH, sep="\t", dtype=str).fillna("")

    numeric_columns = [
        "column_id",
        "max_length",
        "precision",
        "scale",
        "is_nullable",
        "is_identity",
    ]
    for column in numeric_columns:
        columns[column] = columns[column].astype(int)

    constraints["key_ordinal"] = constraints["key_ordinal"].astype(int)

    statements = [
        "-- sql/raw/001_create_raw_tables.sql",
        "-- Generado automáticamente desde docs/db_model/raw_inventory/*.tsv.",
        "-- No editar manualmente salvo que se regenere desde los inventarios.",
        "",
        "CREATE SCHEMA IF NOT EXISTS raw;",
        "",
    ]

    for table_name in sorted(columns["source_table"].unique()):
        table_columns = columns[columns["source_table"] == table_name]

        pk_rows = constraints[
            (constraints["source_table"] == table_name)
            & (constraints["constraint_type"] == "PK")
        ].sort_values("key_ordinal")
        pk_columns = pk_rows["source_column"].tolist()

        statements.append(build_create_table(table_name, table_columns, pk_columns))
        statements.append("")

    fk_rows = constraints[constraints["constraint_type"] == "FK"]
    index_pairs = (
        fk_rows[["source_table", "source_column"]]
        .drop_duplicates()
        .sort_values(["source_table", "source_column"])
    )

    statements.append("-- Índices sobre columnas relacionales detectadas como FK en SQL Server.")
    for _, row in index_pairs.iterrows():
        statements.append(build_index(row["source_table"], row["source_column"]))
        statements.append("")

    OUTPUT_PATH.write_text("\n".join(statements), encoding="utf-8")
    print(f"DDL generado: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()