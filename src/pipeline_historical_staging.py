# src/pipeline_historical_staging.py
"""Orquesta la migración histórica de Breeze hacia PostgreSQL staging."""

import argparse
from datetime import date, datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

from src.pipeline_load_staging import STAGING_LOADS, load_component
from src.postgres import get_postgres_engine
from src.run_all_pipelines import run_all_pipelines


def parse_date(value: str) -> date:
    """Convierte una fecha YYYY-MM-DD a date."""

    return datetime.strptime(value, "%Y-%m-%d").date()


def add_month(value: date) -> date:
    """Devuelve el primer día del mes siguiente."""

    if value.month == 12:
        return date(value.year + 1, 1, 1)

    return date(value.year, value.month + 1, 1)


def build_monthly_windows(start_date: date, end_date: date) -> list[tuple[date, date]]:
    """Construye ventanas mensuales cerradas-abiertas."""

    if start_date >= end_date:
        raise ValueError("start_date debe ser menor que end_date.")

    windows: list[tuple[date, date]] = []
    current = start_date

    while current < end_date:
        next_date = min(add_month(current), end_date)
        windows.append((current, next_date))
        current = next_date

    return windows


def assert_window_not_loaded(
    component: str,
    start_date: str,
    end_date: str,
) -> None:
    """Bloquea una carga si la tabla y ventana ya fueron cargadas con éxito."""

    config = STAGING_LOADS[component]
    engine = get_postgres_engine()

    query = text(
        """
        SELECT COUNT(*) AS successful_loads
        FROM audit.load_control
        WHERE target_schema = 'staging'
          AND target_table = :target_table
          AND source_start_date = :source_start_date
          AND source_end_date = :source_end_date
          AND status = 'success'
        """
    )

    with engine.connect() as connection:
        successful_loads = connection.execute(
            query,
            {
                "target_table": config["target_table"],
                "source_start_date": start_date,
                "source_end_date": end_date,
            },
        ).scalar_one()

    if successful_loads:
        raise RuntimeError(
            "Carga bloqueada: ya existe una carga exitosa para "
            f"{config['target_table']} entre {start_date} y {end_date}."
        )


def build_parquet_path(
    component: str,
    start_date: str,
    end_date: str,
) -> Path:
    """Construye la ruta local esperada para un Parquet."""

    config = STAGING_LOADS[component]
    filename = config["filename_template"].format(
        start_date=start_date,
        end_date=end_date,
    )

    return Path("data") / "processed" / filename


def assert_parquet_outputs_exist(
    start_date: str,
    end_date: str,
    components: list[str],
) -> None:
    """Verifica que existan los Parquet esperados para una ventana."""

    missing_files: list[Path] = []

    for component in components:
        path = build_parquet_path(
            component=component,
            start_date=start_date,
            end_date=end_date,
        )

        if not path.exists():
            missing_files.append(path)

    if missing_files:
        missing = "\n".join(str(path) for path in missing_files)
        raise FileNotFoundError(
            "Faltan Parquet esperados para la carga:\n" + missing
        )


def parquet_has_rows(
    component: str,
    start_date: str,
    end_date: str,
) -> bool:
    """Indica si el Parquet de un componente tiene filas."""

    path = build_parquet_path(
        component=component,
        start_date=start_date,
        end_date=end_date,
    )

    dataframe = pd.read_parquet(path, columns=None)

    return len(dataframe) > 0


def run_historical_staging(
    start_date: str,
    end_date: str,
    component: str,
    dry_run: bool,
) -> None:
    """Ejecuta la migración histórica por ventanas mensuales."""

    start = parse_date(start_date)
    end = parse_date(end_date)
    windows = build_monthly_windows(start, end)

    if component == "all":
        components = list(STAGING_LOADS.keys())
    else:
        components = [component]

    print("Ventanas históricas a procesar:")
    for window_start, window_end in windows:
        print(f"- {window_start} a {window_end}")

    if dry_run:
        print("Dry-run activo. No se ejecutó extracción ni carga.")
        return

    for window_start, window_end in windows:
        window_start_text = window_start.isoformat()
        window_end_text = window_end.isoformat()

        print(
            "Iniciando ventana histórica: "
            f"{window_start_text} a {window_end_text}"
        )

        for current_component in components:
            assert_window_not_loaded(
                component=current_component,
                start_date=window_start_text,
                end_date=window_end_text,
            )

        run_all_pipelines(
            start_date=window_start_text,
            end_date=window_end_text,
        )

        assert_parquet_outputs_exist(
            start_date=window_start_text,
            end_date=window_end_text,
            components=components,
        )

        for current_component in components:
            if not parquet_has_rows(
                component=current_component,
                start_date=window_start_text,
                end_date=window_end_text,
            ):
                print(
                    "Carga omitida por Parquet vacío: "
                    f"{current_component} | "
                    f"{window_start_text} a {window_end_text}"
                )
                continue

            load_component(
                component=current_component,
                start_date=window_start_text,
                end_date=window_end_text,
            )

        print(
            "Ventana histórica completada: "
            f"{window_start_text} a {window_end_text}"
        )


def parse_arguments() -> argparse.Namespace:
    """Lee argumentos de ejecución."""

    parser = argparse.ArgumentParser(
        description="Migra históricamente Parquet analíticos a staging."
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
        help="Componente a migrar. Por defecto carga todos.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra las ventanas sin ejecutar extracción ni carga.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la migración histórica desde terminal."""

    arguments = parse_arguments()

    run_historical_staging(
        start_date=arguments.start_date,
        end_date=arguments.end_date,
        component=arguments.component,
        dry_run=arguments.dry_run,
    )


if __name__ == "__main__":
    main()
