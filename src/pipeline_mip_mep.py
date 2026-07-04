# src/pipeline_mip_mep.py
"""Ejecuta la extracción y transformación de MIP/MEP."""

import argparse
from pathlib import Path

from src.extract.mip_mep import extract_mip_mep
from src.load.parquet import save_parquet
from src.transform.mip_mep import transform_mip_mep


# Define la carpeta local de salida temporal.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed"


def run_pipeline(
    start_date: str,
    end_date: str,
) -> Path:
    """Extrae, transforma y guarda localmente la tabla analítica."""

    print(
        "Iniciando pipeline de MIP/MEP: "
        f"{start_date} a {end_date}"
    )

    # Extrae las filas originales desde SQL Server.
    raw_dataframe = extract_mip_mep(
        start_date=start_date,
        end_date=end_date,
    )

    print(f"Filas extraídas: {len(raw_dataframe):,}")

    # Construye una única fila analítica por visita.
    analytical_dataframe = transform_mip_mep(raw_dataframe)

    print(
        "Visitas transformadas: "
        f"{len(analytical_dataframe):,}"
    )

    output_file = (
        OUTPUT_DIR
        / f"mip_mep_analytics_{start_date}_{end_date}.parquet"
    )

    save_parquet(
        dataframe=analytical_dataframe,
        output_file=output_file,
    )

    print(f"Archivo generado: {output_file}")

    return output_file


def parse_arguments() -> argparse.Namespace:
    """Lee las fechas proporcionadas desde la terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Extrae y transforma resultados de MIP/MEP."
        )
    )

    parser.add_argument(
        "--start-date",
        required=True,
        help="Fecha inicial inclusiva en formato YYYY-MM-DD.",
    )

    parser.add_argument(
        "--end-date",
        required=True,
        help="Fecha final exclusiva en formato YYYY-MM-DD.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta el pipeline con los argumentos recibidos."""

    arguments = parse_arguments()

    run_pipeline(
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )


if __name__ == "__main__":
    main()
