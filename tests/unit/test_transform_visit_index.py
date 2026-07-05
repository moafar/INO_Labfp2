# tests/unit/test_transform_visit_index.py
"""Pruebas sintéticas del índice de visitas."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.transform.visit_index import build_visit_index


def write_parquet(path: Path, rows: list[dict[str, object]]) -> Path:
    """Escribe un Parquet mínimo para pruebas."""

    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def test_build_visit_index_consolidates_and_flags(tmp_path: Path) -> None:
    """Verifica consolidación, flags y conteo."""

    paths = {
        "fvl": write_parquet(
            tmp_path / "fvl.parquet",
            [
                {
                    "patient_guid": "guid-1",
                    "patient_id_num": "id-1",
                    "patient_last_name": "FVL",
                    "patient_first_name": "Ana",
                    "pat_visit_id": 2,
                    "pat_visit_guid": "visit-2-fvl",
                    "visit_datetime": "2024-01-01 09:00:00",
                },
                {
                    "patient_guid": "guid-1",
                    "patient_id_num": "id-1",
                    "patient_last_name": "FVL",
                    "patient_first_name": "Ana",
                    "pat_visit_id": 1,
                    "pat_visit_guid": "visit-1-fvl",
                    "visit_datetime": "2024-01-02 10:00:00",
                },
            ],
        ),
        "dlco": write_parquet(
            tmp_path / "dlco.parquet",
            [
                {
                    "patient_guid": "guid-1-dlco",
                    "patient_id_num": "id-1-dlco",
                    "patient_last_name": "DLCO",
                    "patient_first_name": "Bea",
                    "pat_visit_id": 1,
                    "pat_visit_guid": "visit-1-dlco",
                    "visit_datetime": "2024-01-02 10:00:00",
                },
                {
                    "patient_guid": "guid-2",
                    "patient_id_num": "id-2",
                    "patient_last_name": "DLCO",
                    "patient_first_name": "Beto",
                    "pat_visit_id": 3,
                    "pat_visit_guid": "visit-3-dlco",
                    "visit_datetime": "2024-01-03 11:00:00",
                },
            ],
        ),
        "pleth": write_parquet(
            tmp_path / "pleth.parquet",
            [
                {
                    "patient_guid": "guid-2",
                    "patient_id_num": "id-2",
                    "patient_last_name": "Pleth",
                    "patient_first_name": "Cia",
                    "pat_visit_id": 3,
                    "pat_visit_guid": "visit-3-pleth",
                    "visit_datetime": "2024-01-03 11:00:00",
                },
            ],
        ),
        "mip_mep": write_parquet(
            tmp_path / "mip_mep.parquet",
            [
                {
                    "patient_guid": "guid-4",
                    "patient_id_num": "id-4",
                    "patient_last_name": "MIP",
                    "patient_first_name": "Dio",
                    "pat_visit_id": 4,
                    "pat_visit_guid": "visit-4-mip",
                    "visit_datetime": "2024-01-04 12:00:00",
                },
            ],
        ),
        "methacholine": write_parquet(
            tmp_path / "methacholine.parquet",
            [
                {
                    "patient_guid": "guid-1",
                    "patient_id_num": "id-1",
                    "patient_last_name": "Meth",
                    "patient_first_name": "Ana",
                    "pat_visit_id": 1,
                    "pat_visit_guid": "visit-1-meth",
                    "visit_datetime": "2024-01-02 10:00:00",
                },
            ],
        ),
    }

    visit_index = build_visit_index(paths)

    assert len(visit_index) == 4
    assert list(visit_index["pat_visit_id"]) == [2, 1, 3, 4]
    assert visit_index.loc[visit_index["pat_visit_id"] == 1, "patient_last_name"].item() == "FVL"
    assert visit_index.loc[visit_index["pat_visit_id"] == 1, "has_fvl"].item() == True
    assert visit_index.loc[visit_index["pat_visit_id"] == 1, "has_dlco"].item() == True
    assert visit_index.loc[visit_index["pat_visit_id"] == 1, "has_methacholine"].item() == True
    assert visit_index.loc[visit_index["pat_visit_id"] == 1, "test_count"].item() == 3
    assert visit_index.loc[visit_index["pat_visit_id"] == 3, "test_count"].item() == 2
    assert visit_index.loc[visit_index["pat_visit_id"] == 4, "test_count"].item() == 1
