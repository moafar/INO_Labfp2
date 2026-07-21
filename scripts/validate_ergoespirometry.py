# scripts/validate_ergoespirometry.py
"""Empareja la exportación de Patient Query con las pruebas GX de SQL Server."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.extract.ergoespirometry import extract_ergoespirometry


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_REFERENCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "GX INO Resultados2.xls"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "ergoespirometry_reference_matches.csv"
)

REFERENCE_REQUIRED_COLUMNS = [
    "Visit Date",
    "ID",
    "GX Rest VO2 (mL/min)",
    "GX AT VO2 (mL/min)",
    "GX VO2 Max VO2 (mL/min)",
    "GX Predicted VO2 (mL/min)",
]

SQL_REQUIRED_COLUMNS = [
    "GXTestID",
    "PatVisitID",
    "PatientIDNum",
    "VisitDateTime",
    "GXTestRawData",
]


def validate_columns(
    dataframe: pd.DataFrame,
    required_columns: list[str],
    source_name: str,
) -> None:
    """Comprueba que una fuente contenga las columnas obligatorias."""

    missing_columns = [
        column
        for column in required_columns
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Faltan columnas en {source_name}: "
            + ", ".join(missing_columns)
        )


def normalize_patient_id(series: pd.Series) -> pd.Series:
    """Normaliza documentos leídos como texto, entero o decimal."""

    return (
        series.astype("string")
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)
    )


def normalize_datetime(series: pd.Series) -> pd.Series:
    """Convierte fechas a precisión de segundos para el emparejamiento."""

    return pd.to_datetime(
        series,
        errors="coerce",
    ).dt.floor("s")


def load_reference(
    reference_path: Path,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Lee y depura las ergoespirometrías completas de Patient Query."""

    dataframe = pd.read_excel(
        reference_path,
        engine="openpyxl",
    )

    validate_columns(
        dataframe=dataframe,
        required_columns=REFERENCE_REQUIRED_COLUMNS,
        source_name=str(reference_path),
    )

    # Una fila se considera GX completa cuando contiene los cuatro
    # resultados principales empleados para la validación.
    complete_mask = dataframe[
        REFERENCE_REQUIRED_COLUMNS[2:]
    ].notna().all(axis=1)

    reference = dataframe.loc[complete_mask].copy()

    reference["match_patient_id"] = normalize_patient_id(
        reference["ID"]
    )
    reference["match_visit_datetime"] = normalize_datetime(
        reference["Visit Date"]
    )

    start_timestamp = pd.Timestamp(start_date)
    end_timestamp = pd.Timestamp(end_date)

    reference = reference[
        reference["match_visit_datetime"].ge(start_timestamp)
        & reference["match_visit_datetime"].lt(end_timestamp)
    ].copy()

    invalid_key_mask = (
        reference["match_patient_id"].isna()
        | reference["match_visit_datetime"].isna()
    )

    if invalid_key_mask.any():
        raise ValueError(
            "La referencia contiene filas GX sin documento o fecha válida."
        )

    duplicate_mask = reference.duplicated(
        subset=[
            "match_patient_id",
            "match_visit_datetime",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        raise ValueError(
            "La referencia contiene claves de emparejamiento ambiguas: "
            f"{int(duplicate_mask.sum())} filas afectadas."
        )

    return reference


def prepare_sql_extract(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae y normaliza las claves GX procedentes de SQL Server."""

    dataframe = extract_ergoespirometry(
        start_date=start_date,
        end_date=end_date,
    )

    validate_columns(
        dataframe=dataframe,
        required_columns=SQL_REQUIRED_COLUMNS,
        source_name="extracción SQL Server",
    )

    dataframe = dataframe.copy()

    dataframe["match_patient_id"] = normalize_patient_id(
        dataframe["PatientIDNum"]
    )
    dataframe["match_visit_datetime"] = normalize_datetime(
        dataframe["VisitDateTime"]
    )

    dataframe["raw_data_available"] = dataframe[
        "GXTestRawData"
    ].notna()

    # Los binarios no se escriben en el CSV de emparejamiento.
    return dataframe.drop(
        columns=[
            "GXTestRawData",
            "ManuallyEnteredData",
        ],
        errors="ignore",
    )


def build_matches(
    reference: pd.DataFrame,
    sql_extract: pd.DataFrame,
) -> pd.DataFrame:
    """Empareja Patient Query y SQL Server por documento y fecha."""

    matched = reference.merge(
        sql_extract,
        on=[
            "match_patient_id",
            "match_visit_datetime",
        ],
        how="left",
        suffixes=("_patient_query", "_sql"),
        indicator=True,
        validate="one_to_many",
    )

    matched["match_status"] = matched["_merge"].map(
        {
            "both": "matched",
            "left_only": "not_found_in_sql",
            "right_only": "not_in_reference",
        }
    )

    return matched.drop(columns="_merge")


def print_summary(
    reference: pd.DataFrame,
    sql_extract: pd.DataFrame,
    matched: pd.DataFrame,
) -> None:
    """Muestra controles básicos del emparejamiento."""

    matched_count = int(
        matched["match_status"].eq("matched").sum()
    )
    unmatched_count = int(
        matched["match_status"].eq("not_found_in_sql").sum()
    )

    duplicate_sql_keys = int(
        sql_extract.duplicated(
            subset=[
                "match_patient_id",
                "match_visit_datetime",
            ],
            keep=False,
        ).sum()
    )

    decodable_count = int(
        matched.loc[
            matched["match_status"].eq("matched"),
            "raw_data_available",
        ].fillna(False).sum()
    )

    print(f"Ergoespirometrías en Patient Query: {len(reference):,}")
    print(f"Pruebas GX extraídas de SQL Server: {len(sql_extract):,}")
    print(f"Emparejamientos encontrados: {matched_count:,}")
    print(f"Referencias sin coincidencia: {unmatched_count:,}")
    print(f"Filas SQL con clave duplicada: {duplicate_sql_keys:,}")
    print(f"Coincidencias con binario disponible: {decodable_count:,}")

    if unmatched_count:
        print(
            "Las referencias sin coincidencia no se muestran para evitar "
            "exponer identificadores personales."
        )


def parse_arguments() -> argparse.Namespace:
    """Lee las rutas y la ventana de validación."""

    parser = argparse.ArgumentParser(
        description=(
            "Empareja resultados GX de Patient Query "
            "con pruebas extraídas de SQL Server."
        )
    )

    parser.add_argument(
        "--reference-path",
        type=Path,
        default=DEFAULT_REFERENCE_PATH,
        help="Archivo Excel exportado desde Patient Query.",
    )

    parser.add_argument(
        "--start-date",
        default="2026-01-07",
        help="Fecha inicial inclusiva en formato YYYY-MM-DD.",
    )

    parser.add_argument(
        "--end-date",
        default="2026-07-16",
        help="Fecha final exclusiva en formato YYYY-MM-DD.",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="CSV local con el resultado del emparejamiento.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la validación de correspondencia."""

    arguments = parse_arguments()

    reference = load_reference(
        reference_path=arguments.reference_path,
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )

    sql_extract = prepare_sql_extract(
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )

    matched = build_matches(
        reference=reference,
        sql_extract=sql_extract,
    )

    arguments.output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_output_columns = [
        column
        for column in (
            "GXTestID",
            "PatVisitID",
            "raw_data_available",
            "match_status",
        )
        if column in matched.columns
    ]
    matched[safe_output_columns].to_csv(
        arguments.output_path,
        index=False,
        encoding="utf-8",
    )

    print_summary(
        reference=reference,
        sql_extract=sql_extract,
        matched=matched,
    )

    print(f"Resultado guardado en: {arguments.output_path}")


if __name__ == "__main__":
    main()
