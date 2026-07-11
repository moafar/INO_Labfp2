# src/query_fvl_results.py
"""Consulta y presenta los resultados analíticos de una espirometría."""

import argparse
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd
from sqlalchemy import text

from src.postgres import get_postgres_engine


RESULTS = [
    ("FVC (L)", "fvc"),
    ("FEV1 (L)", "fev1"),
    ("FEV1/FVC (%)", "fev1fvc"),
    ("FEF 25% (L/s)", "fef25"),
    ("FEF 75% (L/s)", "fef75"),
    ("FEF 25-75% (L/s)", "fef2575"),
    ("FEF Max (L/s)", "fefmax"),
    ("PEF (L/min)", "pef"),
    ("FEV6 (L)", "fev6"),
    ("FEV6/FVC (%)", "fev6fvc"),
    ("FIVC (L)", "fivc"),
    ("Back Extrap Vol (L)", "volextrap"),
    ("Expiratory Time (s)", "exptime"),
]


def parse_date(value: str) -> date:
    """Valida una fecha recibida en formato ISO YYYY-MM-DD."""

    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "La fecha debe tener el formato YYYY-MM-DD."
        ) from error


def to_decimal(value: Any) -> Decimal | None:
    """Convierte un valor de staging a Decimal cuando es numérico."""

    if value is None:
        return None

    text_value = str(value).strip()

    if not text_value or text_value.lower() in {"nan", "none", "<na>"}:
        return None

    try:
        return Decimal(text_value)
    except InvalidOperation:
        return None


def format_number(value: Any, decimals: int = 2) -> str:
    """Devuelve un número formateado o una cadena vacía."""

    number = to_decimal(value)

    if number is None:
        return ""

    return f"{number:.{decimals}f}"


def calculate_change(pre_value: Any, post_value: Any) -> str:
    """Calcula el cambio porcentual entre los resultados pre y post."""

    pre = to_decimal(pre_value)
    post = to_decimal(post_value)

    if pre is None or post is None or pre == 0:
        return ""

    change = ((post - pre) / pre) * Decimal("100")

    return f"{change:.1f}"


def get_latest_result(
    identification: str,
    visit_date: date,
) -> dict[str, Any] | None:
    """Obtiene la carga más reciente para un paciente y una fecha."""

    query = text(
        """
        SELECT *
        FROM staging.fvl_analytics
        WHERE patient_id_num = :identification
          AND visit_datetime::date = :visit_date
        ORDER BY loaded_at DESC
        LIMIT 1
        """
    )

    engine = get_postgres_engine()

    with engine.connect() as connection:
        row = connection.execute(
            query,
            {
                "identification": identification,
                "visit_date": visit_date,
            },
        ).mappings().first()

    if row is None:
        return None

    return dict(row)


def build_results_table(result: dict[str, Any]) -> pd.DataFrame:
    """Construye una tabla legible con los resultados clínicos."""

    rows: list[dict[str, str]] = []

    for label, prefix in RESULTS:
        pre = result.get(f"{prefix}_pre")
        post = result.get(f"{prefix}_post")

        rows.append(
            {
                "Resultado": label,
                "Pre": format_number(pre),
                "Predicho": format_number(
                    result.get(f"{prefix}_predicted")
                ),
                "%Pred pre": format_number(
                    result.get(f"{prefix}_percent_predicted_pre")
                ),
                "Post": format_number(post),
                "%Pred post": format_number(
                    result.get(f"{prefix}_percent_predicted_post")
                ),
                "%Cambio": calculate_change(pre, post),
                "Z pre": format_number(
                    result.get(f"{prefix}_zscore_pre")
                ),
                "Z post": format_number(
                    result.get(f"{prefix}_zscore_post")
                ),
            }
        )

    rows.append(
        {
            "Resultado": "TestGrade (ATS)",
            "Pre": str(result.get("testgradeats_pre") or ""),
            "Predicho": "",
            "%Pred pre": "",
            "Post": str(result.get("testgradeats_post") or ""),
            "%Pred post": "",
            "%Cambio": "",
            "Z pre": "",
            "Z post": "",
        }
    )

    return pd.DataFrame(rows)


def parse_arguments() -> argparse.Namespace:
    """Lee los parámetros de línea de comandos."""

    parser = argparse.ArgumentParser(
        description=(
            "Consulta una espirometría en PostgreSQL por identificación "
            "del paciente y fecha de visita."
        )
    )

    parser.add_argument(
        "--identification",
        required=True,
        help="Identificación del paciente.",
    )

    parser.add_argument(
        "--date",
        required=True,
        type=parse_date,
        help="Fecha de la prueba en formato YYYY-MM-DD.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la consulta y muestra los resultados."""

    arguments = parse_arguments()

    result = get_latest_result(
        identification=arguments.identification.strip(),
        visit_date=arguments.date,
    )

    if result is None:
        print(
            "No se encontró una espirometría para "
            f"{arguments.identification} el {arguments.date}."
        )
        return

    print()
    print(f"Identificación: {result.get('patient_id_num', '')}")
    print(f"Fecha: {result.get('visit_datetime', '')}")
    print(f"PatVisitID: {result.get('pat_visit_id', '')}")
    print()

    table = build_results_table(result)

    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
