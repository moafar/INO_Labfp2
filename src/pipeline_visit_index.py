# src/pipeline_visit_index.py
"""Genera el índice analítico de visitas."""

import argparse
from pathlib import Path

from src.load.parquet import save_parquet
from src.transform.visit_index import build_visit_index


def run_pipeline(
    fvl_path: Path,
    dlco_path: Path,
    pleth_path: Path,
    mip_mep_path: Path,
    methacholine_path: Path,
    output_path: Path,
) -> Path:
    """Construye y guarda el índice de visitas."""

    paths = {
        "fvl": fvl_path,
        "dlco": dlco_path,
        "pleth": pleth_path,
        "mip_mep": mip_mep_path,
        "methacholine": methacholine_path,
    }

    dataframe = build_visit_index(paths)
    save_parquet(dataframe=dataframe, output_file=output_path)

    print(f"Filas generadas: {len(dataframe):,}")
    print(f"Archivo generado: {output_path}")

    return output_path


def parse_arguments() -> argparse.Namespace:
    """Lee los argumentos de línea de comandos."""

    parser = argparse.ArgumentParser(
        description="Genera el índice analítico de visitas.",
    )

    parser.add_argument("--fvl-path", required=True, type=Path)
    parser.add_argument("--dlco-path", required=True, type=Path)
    parser.add_argument("--pleth-path", required=True, type=Path)
    parser.add_argument("--mip-mep-path", required=True, type=Path)
    parser.add_argument("--methacholine-path", required=True, type=Path)
    parser.add_argument("--output-path", required=True, type=Path)

    return parser.parse_args()


def main() -> None:
    """Ejecuta el pipeline desde terminal."""

    arguments = parse_arguments()
    run_pipeline(
        fvl_path=arguments.fvl_path,
        dlco_path=arguments.dlco_path,
        pleth_path=arguments.pleth_path,
        mip_mep_path=arguments.mip_mep_path,
        methacholine_path=arguments.methacholine_path,
        output_path=arguments.output_path,
    )


if __name__ == "__main__":
    main()
