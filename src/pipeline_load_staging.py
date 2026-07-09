# src/pipeline_load_staging.py
"""Carga los Parquet analíticos existentes en PostgreSQL staging."""

import argparse
from pathlib import Path

from src.load.postgres import load_parquet_to_staging


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


STAGING_LOADS = {
    "visit_index": {
        "pipeline_name": "visit_index",
        "target_table": "visit_index",
        "filename_template": "visit_index_{start_date}_{end_date}.parquet",
    },
    "fvl": {
        "pipeline_name": "fvl",
        "target_table": "fvl_analytics",
        "filename_template": "fvl_analytics_{start_date}_{end_date}.parquet",
    },
    "dlco": {
        "pipeline_name": "dlco",
        "target_table": "dlco_analytics",
        "filename_template": "dlco_analytics_{start_date}_{end_date}.parquet",
    },
    "pleth": {
        "pipeline_name": "pleth",
        "target_table": "pleth_analytics",
        "filename_template": "pleth_analytics_{start_date}_{end_date}.parquet",
    },
    "mip_mep": {
        "pipeline_name": "mip_mep",
        "target_table": "mip_mep_analytics",
        "filename_template": "mip_mep_analytics_{start_date}_{end_date}.parquet",
    },
    "methacholine": {
        "pipeline_name": "methacholine",
        "target_table": "methacholine_analytics",
        "filename_template": "methacholine_analytics_{start_date}_{end_date}.parquet",
    },
}


def build_parquet_path(component: str, start_date: str, end_date: str) -> Path:
    """Construye la ruta esperada del Parquet de un componente."""

    config = STAGING_LOADS[component]
    filename = config["filename_template"].format(
        start_date=start_date,
        end_date=end_date,
    )

    return PROCESSED_DIR / filename


def load_component(
    component: str,
    start_date: str,
    end_date: str,
) -> str:
    """Carga un componente en staging."""

    config = STAGING_LOADS[component]
    parquet_file = build_parquet_path(
        component=component,
        start_date=start_date,
        end_date=end_date,
    )

    if not parquet_file.exists():
        raise FileNotFoundError(
            f"No existe el Parquet esperado: {parquet_file}"
        )

    print(f"Cargando {component}: {parquet_file}")

    load_id = load_parquet_to_staging(
        parquet_file=parquet_file,
        pipeline_name=config["pipeline_name"],
        target_table=config["target_table"],
        source_start_date=start_date,
        source_end_date=end_date,
    )

    print(f"Componente cargado: {component} | load_id={load_id}")

    return load_id


def parse_arguments() -> argparse.Namespace:
    """Lee argumentos de ejecución."""

    parser = argparse.ArgumentParser(
        description="Carga Parquet analíticos en PostgreSQL staging."
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

    parser.add_argument(
        "--component",
        choices=[*STAGING_LOADS.keys(), "all"],
        default="all",
        help="Componente a cargar. Por defecto carga todos.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la carga a staging."""

    arguments = parse_arguments()

    if arguments.component == "all":
        components = list(STAGING_LOADS.keys())
    else:
        components = [arguments.component]

    for component in components:
        try:
            load_component(
                component=component,
                start_date=arguments.start_date,
                end_date=arguments.end_date,
            )
        except RuntimeError as error:
            print(f"ERROR: {error}")
            raise SystemExit(1) from error


if __name__ == "__main__":
    main()
