# src/query_fvl_test.py
"""Consulta y transforma una prueba específica de espirometría."""

import argparse
from datetime import datetime, timedelta

from extract.fvl import extract_fvl
from transform.fvl import transform_fvl


def query_test(
    patient_id: str,
    test_date: str,
):
    """Consulta una prueba por identificación y fecha."""

    # Convierte la fecha recibida y construye el intervalo de un día.
    start_datetime = datetime.strptime(
        test_date,
        "%Y-%m-%d",
    )

    end_datetime = start_datetime + timedelta(days=1)

    # Extrae todas las pruebas realizadas durante el día indicado.
    raw_dataframe = extract_fvl(
        start_date=start_datetime.strftime("%Y-%m-%d"),
        end_date=end_datetime.strftime("%Y-%m-%d"),
    )

    # Construye una fila analítica por visita.
    analytical_dataframe = transform_fvl(raw_dataframe)

    # Filtra únicamente el paciente solicitado.
    result = analytical_dataframe[
        analytical_dataframe["patient_id_num"].astype(str).str.strip()
        == str(patient_id).strip()
    ].copy()

    return result


def parse_arguments() -> argparse.Namespace:
    """Lee la identificación y la fecha desde la terminal."""

    parser = argparse.ArgumentParser(
        description=(
            "Consulta una prueba de espirometría "
            "por identificación y fecha."
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
    """Ejecuta la consulta y muestra los resultados principales."""

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

    columns_to_show = [
        "patient_id_num",
        "patient_last_name",
        "patient_first_name",
        "pat_visit_id",
        "visit_datetime",
        "age",
        "weight",
        "height",
        "pred_set_name",
        "fvc_pre",
        "fvc_predicted",
        "fvc_percent_predicted_pre",
        "fvc_post",
        "fvc_percent_predicted_post",
        "fvc_zscore_pre",
        "fev1_pre",
        "fev1_predicted",
        "fev1_percent_predicted_pre",
        "fev1_post",
        "fev1_percent_predicted_post",
        "fev1_zscore_pre",
        "fev1fvc_pre",
        "fev1fvc_predicted",
        "fev1fvc_percent_predicted_pre",
        "fev1fvc_post",
        "fev1fvc_percent_predicted_post",
        "fev1fvc_zscore_pre",
        "fef2575_pre",
        "fef2575_predicted",
        "fef2575_percent_predicted_pre",
        "fef2575_post",
        "fef2575_percent_predicted_post",
        "fef2575_zscore_pre",
        "pef_pre",
        "pef_post",
    ]

    # Conserva solo las columnas disponibles en el resultado.
    available_columns = [
        column
        for column in columns_to_show
        if column in result.columns
    ]

    print(
        result[available_columns].to_string(
            index=False,
        )
    )


if __name__ == "__main__":
    main()

# python src/query_fvl_test.py \
#  --patient-id 1098724357 \
#  --test-date 2025-05-14