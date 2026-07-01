# src/query_fvl_test.py
"""Consulta una prueba específica y genera un informe HTML."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from extract_fvl import extract_fvl
from transform_fvl import transform_fvl


# Define la carpeta donde se guardarán los informes.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "reports"


def query_test(
    patient_id: str,
    test_date: str,
) -> pd.DataFrame:
    """Consulta una prueba por identificación y fecha."""

    # Construye un intervalo de un día.
    start_datetime = datetime.strptime(
        test_date,
        "%Y-%m-%d",
    )
    end_datetime = start_datetime + timedelta(days=1)

    # Extrae las pruebas realizadas durante la fecha indicada.
    raw_dataframe = extract_fvl(
        start_date=start_datetime.strftime("%Y-%m-%d"),
        end_date=end_datetime.strftime("%Y-%m-%d"),
    )

    # Construye una fila analítica por visita.
    analytical_dataframe = transform_fvl(raw_dataframe)

    # Filtra el paciente solicitado.
    result = analytical_dataframe[
        analytical_dataframe["patient_id_num"]
        .astype(str)
        .str.strip()
        == str(patient_id).strip()
    ].copy()

    return result


def build_report_table(result: pd.DataFrame) -> pd.DataFrame:
    """Organiza los parámetros principales en formato clínico."""

    row = result.iloc[0]

    parameters = [
        ("FVC (L)", "fvc"),
        ("FEV1 (L)", "fev1"),
        ("FEV1/FVC (%)", "fev1fvc"),
        ("FEF 25-75% (L/s)", "fef2575"),
        ("PEF (L/min)", "pef"),
    ]

    report_rows = []

    for label, prefix in parameters:
        report_rows.append(
            {
                "Parámetro": label,
                "Pre": row.get(f"{prefix}_pre"),
                "Predicho": row.get(f"{prefix}_predicted"),
                "% predicho pre": row.get(
                    f"{prefix}_percent_predicted_pre"
                ),
                "Post": row.get(f"{prefix}_post"),
                "% predicho post": row.get(
                    f"{prefix}_percent_predicted_post"
                ),
                "LLN": row.get(f"{prefix}_lln"),
                "ULN": row.get(f"{prefix}_uln"),
                "Z-score pre": row.get(
                    f"{prefix}_zscore_pre"
                ),
                "Z-score post": row.get(
                    f"{prefix}_zscore_post"
                ),
            }
        )

    return pd.DataFrame(report_rows)


def format_value(value: object) -> str:
    """Formatea valores numéricos para su presentación."""

    if pd.isna(value):
        return ""

    if isinstance(value, (int, float)):
        return f"{value:.2f}"

    return str(value)


def save_html_report(
    result: pd.DataFrame,
    patient_id: str,
    test_date: str,
) -> Path:
    """Genera un informe HTML visual de la prueba."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    row = result.iloc[0]
    report_table = build_report_table(result)

    # Aplica formato de presentación a la tabla.
    formatted_table = report_table.map(format_value)

    html_table = formatted_table.to_html(
        index=False,
        border=0,
        classes="results-table",
    )

    patient_name = " ".join(
        value
        for value in [
            str(row.get("patient_first_name", "")).strip(),
            str(row.get("patient_middle_name", "")).strip(),
            str(row.get("patient_last_name", "")).strip(),
        ]
        if value and value != "nan"
    )

    html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Espirometría {patient_id}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 32px;
            color: #222;
        }}

        h1 {{
            margin-bottom: 8px;
        }}

        .metadata {{
            display: grid;
            grid-template-columns: repeat(3, minmax(180px, 1fr));
            gap: 10px 24px;
            margin-bottom: 28px;
            padding: 16px;
            background: #f4f6f8;
            border-radius: 8px;
        }}

        .metadata div {{
            line-height: 1.4;
        }}

        .results-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 16px;
        }}

        .results-table th,
        .results-table td {{
            border: 1px solid #d5d9dd;
            padding: 9px 10px;
            text-align: right;
        }}

        .results-table th {{
            background: #eef1f4;
            font-weight: bold;
        }}

        .results-table th:first-child,
        .results-table td:first-child {{
            text-align: left;
        }}

        .footer {{
            margin-top: 24px;
            font-size: 12px;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>Resultado de espirometría</h1>

    <div class="metadata">
        <div><strong>Paciente:</strong> {patient_name}</div>
        <div><strong>Identificación:</strong> {patient_id}</div>
        <div><strong>Fecha:</strong> {test_date}</div>
        <div><strong>Visita:</strong> {row.get("pat_visit_id", "")}</div>
        <div><strong>Edad:</strong> {format_value(row.get("age"))}</div>
        <div><strong>Sexo:</strong> {row.get("sex_list_id", "")}</div>
        <div><strong>Talla:</strong> {format_value(row.get("height"))} cm</div>
        <div><strong>Peso:</strong> {format_value(row.get("weight"))} kg</div>
        <div><strong>Predicción:</strong> {row.get("pred_set_name", "")}</div>
    </div>

    {html_table}

    <div class="footer">
        Informe generado desde SQL Server mediante el pipeline Python.
    </div>
</body>
</html>
"""

    output_file = (
        OUTPUT_DIR
        / f"fvl_{patient_id}_{test_date}.html"
    )

    output_file.write_text(
        html_content,
        encoding="utf-8",
    )

    return output_file


def parse_arguments() -> argparse.Namespace:
    """Lee la identificación y la fecha desde la terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Consulta una espirometría y genera un informe HTML."
        )
    )

    parser.add_argument(
        "--patient-id",
        required=True,
        help="Identificación del paciente.",
    )

    parser.add_argument(
        "--test-date",
        required=True,
        help="Fecha de la prueba en formato YYYY-MM-DD.",
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la consulta y guarda el informe visual."""

    arguments = parse_arguments()

    result = query_test(
        patient_id=arguments.patient_id,
        test_date=arguments.test_date,
    )

    if result.empty:
        print(
            "No se encontraron pruebas para la identificación "
            f"{arguments.patient_id} en la fecha "
            f"{arguments.test_date}."
        )
        return

    output_file = save_html_report(
        result=result,
        patient_id=arguments.patient_id,
        test_date=arguments.test_date,
    )

    print(f"Informe generado: {output_file}")


if __name__ == "__main__":
    main()