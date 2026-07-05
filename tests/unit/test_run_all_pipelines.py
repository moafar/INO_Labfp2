# tests/unit/test_run_all_pipelines.py
"""Pruebas sintéticas del orquestador de pipelines."""

from __future__ import annotations

from pathlib import Path
from collections.abc import Callable

import pytest
import pandas as pd

import src.pipeline_dlco as pipeline_dlco
import src.pipeline_fvl as pipeline_fvl
import src.pipeline_methacholine as pipeline_methacholine
import src.pipeline_mip_mep as pipeline_mip_mep
import src.pipeline_pleth as pipeline_pleth
import src.run_all_pipelines as run_all_pipelines_module


def test_run_all_pipelines_executes_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verifica orden y resultado agregado."""

    calls: list[str] = []

    def make_runner(name: str) -> Callable[[str, str], Path]:
        def runner(start_date: str, end_date: str) -> Path:
            calls.append(name)
            return Path(f"/tmp/{name}.parquet")

        return runner

    monkeypatch.setattr(pipeline_fvl, "run_pipeline", make_runner("fvl"))
    monkeypatch.setattr(pipeline_dlco, "run_pipeline", make_runner("dlco"))
    monkeypatch.setattr(pipeline_pleth, "run_pipeline", make_runner("pleth"))
    monkeypatch.setattr(pipeline_mip_mep, "run_pipeline", make_runner("mip_mep"))
    monkeypatch.setattr(
        pipeline_methacholine,
        "run_pipeline",
        make_runner("methacholine"),
    )

    monkeypatch.setattr(
        run_all_pipelines_module,
        "build_visit_index",
        lambda paths: pd.DataFrame(
            [
                {
                    "patient_guid": "guid-1",
                    "patient_id_num": "id-1",
                    "patient_last_name": "Test",
                    "patient_first_name": "Ana",
                    "pat_visit_id": 1,
                    "pat_visit_guid": "visit-1",
                    "visit_datetime": "2024-01-01 10:00:00",
                    "has_fvl": True,
                    "has_dlco": True,
                    "has_pleth": False,
                    "has_mip_mep": False,
                    "has_methacholine": False,
                    "test_count": 2,
                }
            ]
        ),
    )
    monkeypatch.setattr(
        run_all_pipelines_module,
        "save_parquet",
        lambda dataframe, output_file: output_file,
    )

    outputs = run_all_pipelines_module.run_all_pipelines(
        "2024-01-01",
        "2024-01-02",
    )

    expected_visit_index = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "processed"
        / "visit_index_2024-01-01_2024-01-02.parquet"
    )

    assert calls == ["fvl", "dlco", "pleth", "mip_mep", "methacholine"]
    assert outputs == {
        "fvl": Path("/tmp/fvl.parquet"),
        "dlco": Path("/tmp/dlco.parquet"),
        "pleth": Path("/tmp/pleth.parquet"),
        "mip_mep": Path("/tmp/mip_mep.parquet"),
        "methacholine": Path("/tmp/methacholine.parquet"),
        "visit_index": expected_visit_index,
    }


def test_run_all_pipelines_stops_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verifica que un fallo corta la secuencia."""

    calls: list[str] = []

    def fvl_runner(start_date: str, end_date: str) -> Path:
        calls.append("fvl")
        return Path("/tmp/fvl.parquet")

    def dlco_runner(start_date: str, end_date: str) -> Path:
        calls.append("dlco")
        raise RuntimeError("boom")

    def pleth_runner(start_date: str, end_date: str) -> Path:
        calls.append("pleth")
        return Path("/tmp/pleth.parquet")

    monkeypatch.setattr(pipeline_fvl, "run_pipeline", fvl_runner)
    monkeypatch.setattr(pipeline_dlco, "run_pipeline", dlco_runner)
    monkeypatch.setattr(pipeline_pleth, "run_pipeline", pleth_runner)
    monkeypatch.setattr(
        pipeline_mip_mep,
        "run_pipeline",
        lambda start_date, end_date: Path("/tmp/mip_mep.parquet"),
    )
    monkeypatch.setattr(
        pipeline_methacholine,
        "run_pipeline",
        lambda start_date, end_date: Path("/tmp/methacholine.parquet"),
    )
    monkeypatch.setattr(
        run_all_pipelines_module,
        "build_visit_index",
        lambda paths: pd.DataFrame(),
    )
    monkeypatch.setattr(
        run_all_pipelines_module,
        "save_parquet",
        lambda dataframe, output_file: output_file,
    )

    with pytest.raises(RuntimeError):
        run_all_pipelines_module.run_all_pipelines(
            "2024-01-01",
            "2024-01-02",
        )

    assert calls == ["fvl", "dlco"]
