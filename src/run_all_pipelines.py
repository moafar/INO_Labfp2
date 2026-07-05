# src/run_all_pipelines.py
"""Ejecuta todos los pipelines funcionales."""

import argparse
from pathlib import Path
from types import ModuleType
from src import pipeline_dlco
from src import pipeline_fvl
from src import pipeline_methacholine
from src import pipeline_mip_mep
from src import pipeline_pleth


PIPELINES: tuple[tuple[str, str, ModuleType], ...] = (
    ("fvl", "FVL", pipeline_fvl),
    ("dlco", "DLCO", pipeline_dlco),
    ("pleth", "Pleth", pipeline_pleth),
    ("mip_mep", "MIP/MEP", pipeline_mip_mep),
    ("methacholine", "Metacolina", pipeline_methacholine),
)


def run_all_pipelines(start_date: str, end_date: str) -> dict[str, Path]:
    """Ejecuta todos los pipelines en serie."""

    print(
        "Iniciando ejecución de todos los pipelines: "
        f"{start_date} a {end_date}"
    )

    outputs: dict[str, Path] = {}

    for key, label, module in PIPELINES:
        print(f"Iniciando {label}...")

        try:
            output_file = module.run_pipeline(
                start_date=start_date,
                end_date=end_date,
            )
        except Exception:
            print(f"Falló el pipeline {label}.")
            raise

        outputs[key] = output_file
        print(f"{label} generado: {output_file}")

    print("Resumen final:")
    for key, output_file in outputs.items():
        print(f"- {key}: {output_file}")

    return outputs


def parse_arguments() -> argparse.Namespace:
    """Lee las fechas de ejecución."""

    parser = argparse.ArgumentParser(
        description="Ejecuta todos los pipelines funcionales.",
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
    """Ejecuta el orquestador desde terminal."""

    arguments = parse_arguments()
    run_all_pipelines(
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )


if __name__ == "__main__":
    main()
