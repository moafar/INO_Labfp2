# src/test_transform_fvl.py
"""Prueba la extracción y transformación analítica de espirometrías."""

from extract_fvl import extract_fvl
from transform_fvl import transform_fvl


def main() -> None:
    """Ejecuta una prueba controlada sobre un día de datos."""

    # Extrae un intervalo corto para validar el flujo completo.
    raw_dataframe = extract_fvl(
        start_date="2025-05-14",
        end_date="2025-05-15",
    )

    # Construye una fila analítica por visita.
    analytical_dataframe = transform_fvl(raw_dataframe)

    print(f"Filas crudas: {len(raw_dataframe):,}")
    print(f"Visitas analíticas: {len(analytical_dataframe):,}")
    print(f"Columnas analíticas: {len(analytical_dataframe.columns):,}")

    # Valida el paciente utilizado como caso de referencia.
    patient_result = analytical_dataframe[
        analytical_dataframe["patient_id_num"] == "1098724357"
    ]

    columns_to_show = [
        "patient_id_num",
        "pat_visit_id",
        "visit_datetime",
        "fvc_pre",
        "fvc_predicted",
        "fvc_zscore_pre",
        "fev1_pre",
        "fev1_predicted",
        "fev1_zscore_pre",
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in patient_result.columns
    ]

    print(patient_result[available_columns].to_string(index=False))


if __name__ == "__main__":
    main()