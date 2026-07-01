# src/parse_patient_query_catalog.py
"""Convierte el catálogo textual de Patient Query en un catálogo estructurado."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


EXPECTED_SET_COUNT = 28
EXPECTED_VARIABLE_COUNT = 8309


SET_METADATA: dict[str, tuple[str | None, str]] = {
    "Demographic": (None, "dato_demografico"),
    "GX AT": ("at", "observado"),
    "GX Max Value": (None, "maximum"),
    "GX Max Value Exercise": ("exercise", "maximum"),
    "GX Mean": (None, "mean"),
    "GX Other": (None, "other"),
    "GX Predicted": (None, "predicted"),
    "GX RC": ("rc", "observado"),
    "GX Rest": ("rest", "observado"),
    "GX SD": (None, "sd"),
    "GX VO2 Max": ("vo2_max", "observado"),
    "GX Work Max": ("work_max", "observado"),
    "PF %Change Chlg": ("challenge", "percent_change"),
    "PF %Change Post": ("post", "percent_change"),
    "PF %Pred Pre": ("pre", "percent_predicted"),
    "PF %Var Post": ("post", "percent_variation"),
    "PF %Var Pre": ("pre", "percent_variation"),
    "PF Challenge": ("challenge", "observado"),
    "PF Coefficient Of Variation": (None, "coefficient_of_variation"),
    "PF LLN": (None, "lln"),
    "PF Post": ("post", "observado"),
    "PF Pre": ("pre", "observado"),
    "PF Predicted": (None, "predicted"),
    "PF SD": (None, "sd"),
    "PF Skewness": (None, "skewness"),
    "PF ULN": (None, "uln"),
    "PF Volume Change Chlg": ("challenge", "absolute_change"),
    "PF Volume Change Post": ("post", "absolute_change"),
}


TABLE_FAMILY: dict[str, str] = {
    "FVLData": "espirometria",
    "DLCOData": "dlco",
    "PlethData": "pletismografia",
    "SVCData": "svc",
    "MVVData": "mvv",
    "MIPData": "mip_mep",
    "FOTData": "fot",
}


# Solo estos contenidos entre paréntesis se interpretan como unidades.
# Etiquetas como ATS, DLCO, NLHEP, calc o non-prot permanecen en el nombre.
KNOWN_UNITS = {
    "%",
    "%CO2",
    "1/cmH2O*s",
    "BPM",
    "F",
    "Fraction",
    "KCal/br",
    "KCal/min",
    "Kcal/day",
    "Kcal/dy/m^2",
    "Kcal/hour",
    "Kcal/hr",
    "Kcal/kg",
    "Kcal/m^2/hr",
    "Kcal/min",
    "L",
    "L/Min",
    "L/Min/Watt",
    "L/breath",
    "L/cmH2O",
    "L/day",
    "L/m^2",
    "L/min",
    "L/min/m^2",
    "L/s/cmH2O",
    "L/sec",
    "L^2/sec",
    "MPH",
    "Min/L",
    "RPM",
    "Sec",
    "TLC/sec",
    "V5",
    "V5 uV",
    "Watts",
    "bpm",
    "br/min",
    "cmH20",
    "cmH2O",
    "cmH2O*s",
    "cmH2O*s/L",
    "cmH2O/L/s",
    "cmH2O/lps",
    "ft",
    "g/day",
    "gm/L",
    "gm/dL",
    "mEq/L",
    "mL",
    "mL/beat",
    "mL/br",
    "mL/kg/min",
    "mL/kgIBW/min",
    "mL/kgLBM/min",
    "mL/m^2",
    "mL/min",
    "mL/min/watt",
    "mL/sec",
    "min",
    "ml/min/mmHg",
    "ml/min/mmHg/L",
    "mmHg",
    "sec",
    "vols%",
}


SET_PATTERN = re.compile(r"^CONJUNTO:\s*(.+?)\s*$")
COUNT_PATTERN = re.compile(r"^Cantidad de variables:\s*(\d+)\s*$")
VARIABLE_PATTERN = re.compile(r"^\[(\d+)\]\s+(.+?)\s*$")
TABLE_PATTERN = re.compile(r"\s+\[([A-Za-z][A-Za-z0-9_]*)\]\s*$")
PARENTHESIS_PATTERN = re.compile(r"\s*\(([^()]*)\)\s*$")


def extract_table(variable_original: str) -> tuple[str, str | None]:
    """Separa la tabla física indicada al final entre corchetes."""

    match = TABLE_PATTERN.search(variable_original)

    if match is None:
        return variable_original.strip(), None

    variable_text = variable_original[: match.start()].strip()
    return variable_text, match.group(1)


def extract_unit(variable_text: str) -> tuple[str, str | None]:
    """Separa una unidad final únicamente cuando pertenece al catálogo conocido."""

    match = PARENTHESIS_PATTERN.search(variable_text)

    if match is None:
        return variable_text.strip(), None

    candidate = match.group(1).strip()

    if candidate not in KNOWN_UNITS:
        return variable_text.strip(), None

    variable = variable_text[: match.start()].strip()
    return variable, candidate


def classify_family(conjunto: str, tabla_origen: str | None) -> str:
    """Asigna la familia clínica sin inferir relaciones no demostradas."""

    if conjunto == "Demographic":
        return "demografia"

    if conjunto.startswith("GX "):
        return "ergoespirometria"

    if tabla_origen in TABLE_FAMILY:
        return TABLE_FAMILY[tabla_origen]

    return "otros"


def parse_catalog(source_path: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    """Lee el TXT y devuelve sus variables estructuradas y conteos declarados."""

    rows: list[dict[str, object]] = []
    declared_counts: dict[str, int] = {}

    current_set: str | None = None

    with source_path.open("r", encoding="utf-8-sig") as source:
        for line_number, raw_line in enumerate(source, start=1):
            line = raw_line.rstrip("\r\n")

            set_match = SET_PATTERN.match(line)
            if set_match:
                current_set = set_match.group(1).strip()

                if current_set in declared_counts:
                    raise ValueError(
                        f"Conjunto repetido en la línea {line_number}: {current_set}"
                    )

                continue

            count_match = COUNT_PATTERN.match(line)
            if count_match:
                if current_set is None:
                    raise ValueError(
                        f"Conteo sin conjunto en la línea {line_number}."
                    )

                declared_counts[current_set] = int(count_match.group(1))
                continue

            variable_match = VARIABLE_PATTERN.match(line)
            if variable_match is None:
                continue

            if current_set is None:
                raise ValueError(
                    f"Variable sin conjunto en la línea {line_number}: {line}"
                )

            if current_set not in SET_METADATA:
                raise ValueError(
                    f"No existe metadato para el conjunto: {current_set}"
                )

            index = int(variable_match.group(1))
            variable_original = variable_match.group(2).strip()

            variable_text, source_table = extract_table(variable_original)
            variable, unit = extract_unit(variable_text)
            phase, result_type = SET_METADATA[current_set]

            rows.append(
                {
                    "clave_catalogo": f"{current_set}::{index}",
                    "conjunto": current_set,
                    "indice": index,
                    "variable_original": variable_original,
                    "variable": variable,
                    "unidad": unit,
                    "tabla_origen": source_table,
                    "fase": phase,
                    "tipo_resultado": result_type,
                    "familia_clinica": classify_family(
                        current_set,
                        source_table,
                    ),
                }
            )

    dataframe = pd.DataFrame(rows)
    return dataframe, declared_counts


def validate_catalog(
    dataframe: pd.DataFrame,
    declared_counts: dict[str, int],
) -> None:
    """Comprueba integridad estructural y consistencia con el TXT."""

    errors: list[str] = []

    found_sets = set(dataframe["conjunto"].unique())
    expected_sets = set(SET_METADATA)

    if len(found_sets) != EXPECTED_SET_COUNT:
        errors.append(
            f"Se encontraron {len(found_sets)} conjuntos; "
            f"se esperaban {EXPECTED_SET_COUNT}."
        )

    if found_sets != expected_sets:
        missing = sorted(expected_sets - found_sets)
        unexpected = sorted(found_sets - expected_sets)

        if missing:
            errors.append(f"Conjuntos ausentes: {missing}")

        if unexpected:
            errors.append(f"Conjuntos inesperados: {unexpected}")

    if len(dataframe) != EXPECTED_VARIABLE_COUNT:
        errors.append(
            f"Se encontraron {len(dataframe)} variables; "
            f"se esperaban {EXPECTED_VARIABLE_COUNT}."
        )

    if dataframe["clave_catalogo"].duplicated().any():
        duplicates = dataframe.loc[
            dataframe["clave_catalogo"].duplicated(keep=False),
            "clave_catalogo",
        ].tolist()
        errors.append(f"Claves duplicadas: {duplicates[:10]}")

    if dataframe["variable"].isna().any() or dataframe["variable"].eq("").any():
        errors.append("Existen variables vacías.")

    if dataframe["familia_clinica"].isna().any():
        errors.append("Existen filas sin familia clínica.")

    for set_name, group in dataframe.groupby("conjunto", sort=False):
        actual_count = len(group)
        declared_count = declared_counts.get(set_name)

        if declared_count is None:
            errors.append(f"{set_name}: no tiene conteo declarado.")
        elif actual_count != declared_count:
            errors.append(
                f"{set_name}: declaró {declared_count} variables "
                f"pero se leyeron {actual_count}."
            )

        indexes = sorted(group["indice"].tolist())
        expected_indexes = list(range(actual_count))

        if indexes != expected_indexes:
            errors.append(
                f"{set_name}: los índices no son consecutivos desde cero."
            )

    if errors:
        formatted_errors = "\n- ".join(errors)
        raise ValueError(f"Catálogo inválido:\n- {formatted_errors}")


def save_catalog(
    dataframe: pd.DataFrame,
    csv_path: Path,
    parquet_path: Path,
) -> None:
    """Guarda el catálogo validado en CSV y Parquet."""

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    dataframe.to_csv(csv_path, index=False, encoding="utf-8")
    dataframe.to_parquet(parquet_path, index=False)


def print_summary(dataframe: pd.DataFrame) -> None:
    """Presenta un resumen verificable del resultado."""

    with_table = int(dataframe["tabla_origen"].notna().sum())
    without_table = int(dataframe["tabla_origen"].isna().sum())

    print(f"Conjuntos leídos: {dataframe['conjunto'].nunique()}")
    print(f"Variables leídas: {len(dataframe)}")
    print(f"Variables con tabla física: {with_table}")
    print(f"Variables sin tabla física: {without_table}")
    print("Errores de conteo: 0")
    print("Índices no consecutivos: 0")


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos."""

    parser = argparse.ArgumentParser(
        description="Estructura el catálogo de Patient Query."
    )
    parser.add_argument(
        "--source",
        type=Path,
        required=True,
        help="Ruta del archivo catalogo_completo_campos.txt.",
    )
    parser.add_argument(
        "--csv-output",
        type=Path,
        default=Path("data/catalogs/patient_query_catalog.csv"),
    )
    parser.add_argument(
        "--parquet-output",
        type=Path,
        default=Path("data/catalogs/patient_query_catalog.parquet"),
    )
    return parser.parse_args()


def main() -> None:
    """Ejecuta lectura, validación y escritura del catálogo."""

    arguments = parse_arguments()

    dataframe, declared_counts = parse_catalog(arguments.source)
    validate_catalog(dataframe, declared_counts)
    save_catalog(
        dataframe,
        arguments.csv_output,
        arguments.parquet_output,
    )
    print_summary(dataframe)


if __name__ == "__main__":
    main()
