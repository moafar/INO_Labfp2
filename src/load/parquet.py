# src/load/parquet.py
"""Guarda DataFrames procesados en archivos Parquet."""

from pathlib import Path

import pandas as pd


def save_parquet(
    dataframe: pd.DataFrame,
    output_file: Path,
) -> Path:
    """Guarda un DataFrame en Parquet y devuelve la ruta generada."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe.to_parquet(
        output_file,
        index=False,
    )

    return output_file
