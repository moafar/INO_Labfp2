# src/transform/visit_index.py
"""Construye un índice de visitas desde Parquets analíticos."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

import pandas as pd


SOURCE_ORDER = (
    ("fvl", "has_fvl"),
    ("dlco", "has_dlco"),
    ("pleth", "has_pleth"),
    ("mip_mep", "has_mip_mep"),
    ("methacholine", "has_methacholine"),
)

VISIT_COLUMNS = [
    "patient_guid",
    "patient_id_num",
    "patient_last_name",
    "patient_first_name",
    "pat_visit_id",
    "pat_visit_guid",
    "visit_datetime",
]


def _is_missing(value: object) -> bool:
    """Comprueba si un valor está vacío."""

    return pd.isna(value)


def _load_source_frame(path: Path, flag_column: str) -> pd.DataFrame:
    """Carga solo las columnas necesarias de un Parquet analítico."""

    dataframe = pd.read_parquet(path, columns=VISIT_COLUMNS)
    dataframe = dataframe.drop_duplicates(subset=["pat_visit_id"], keep="first")
    dataframe = dataframe.copy()
    dataframe[flag_column] = True
    return dataframe


def build_visit_index(paths: Mapping[str, Path]) -> pd.DataFrame:
    """Consolida las visitas presentes en los Parquets funcionales."""

    records: dict[object, dict[str, object]] = {}

    for source_name, flag_column in SOURCE_ORDER:
        source_path = paths[source_name]
        source_frame = _load_source_frame(source_path, flag_column)

        for row in source_frame.to_dict(orient="records"):
            pat_visit_id = row["pat_visit_id"]
            record = records.setdefault(
                pat_visit_id,
                {"pat_visit_id": pat_visit_id},
            )

            for column in VISIT_COLUMNS:
                value = row.get(column)
                if _is_missing(value):
                    continue

                if column not in record or _is_missing(record[column]):
                    record[column] = value

            record[flag_column] = True

    output_columns = [
        "patient_guid",
        "patient_id_num",
        "patient_last_name",
        "patient_first_name",
        "pat_visit_id",
        "pat_visit_guid",
        "visit_datetime",
        "has_fvl",
        "has_dlco",
        "has_pleth",
        "has_mip_mep",
        "has_methacholine",
        "test_count",
    ]

    if not records:
        return pd.DataFrame(columns=output_columns)

    visit_index = pd.DataFrame(records.values())

    for _, flag_column in SOURCE_ORDER:
        if flag_column not in visit_index.columns:
            visit_index[flag_column] = False

    visit_index[[
        "has_fvl",
        "has_dlco",
        "has_pleth",
        "has_mip_mep",
        "has_methacholine",
    ]] = visit_index[[
        "has_fvl",
        "has_dlco",
        "has_pleth",
        "has_mip_mep",
        "has_methacholine",
    ]].fillna(False).astype(bool)

    visit_index["test_count"] = (
        visit_index[
            [
                "has_fvl",
                "has_dlco",
                "has_pleth",
                "has_mip_mep",
                "has_methacholine",
            ]
        ]
        .sum(axis=1)
        .astype("int64")
    )

    visit_index["_visit_datetime_sort"] = pd.to_datetime(
        visit_index["visit_datetime"],
        errors="coerce",
    )

    visit_index = visit_index.sort_values(
        by=["_visit_datetime_sort", "pat_visit_id"],
        kind="stable",
    ).drop(columns=["_visit_datetime_sort"])

    return visit_index[output_columns].reset_index(drop=True)
