# labfp2

ETL en Python para Breeze/SQL Server en laboratorio de función pulmonar. Extrae datos clínicos desde SQL Server, transforma cada estudio a una tabla analítica por visita y guarda salidas en Parquet.

## Arquitectura

Flujo general:
1. `src/extract/` lee SQL Server.
2. `src/transform/` consolida y calcula métricas derivadas.
3. `src/load/parquet.py` escribe Parquet.
4. `src/run_all_pipelines.py` orquesta todos los estudios.
5. `src/pipeline_visit_index.py` construye el índice analítico de visitas.

## Estructura

- `src/` código fuente
- `src/extract/` extracción SQL Server
- `src/transform/` transformaciones analíticas
- `src/load/` salida a Parquet
- `src/config/` catálogos validados de columnas
- `src/pipeline_*.py` entrypoints por componente
- `src/run_all_pipelines.py` orquestador general
- `src/pipeline_visit_index.py` índice de visitas
- `tests/unit/` tests unitarios
- `tests/integration/` tests con SQL Server
- `docs/` documentación y validaciones

## Pipelines

- FVL: `src.pipeline_fvl`
- DLCO: `src.pipeline_dlco`
- Pleth: `src.pipeline_pleth`
- MIP/MEP: `src.pipeline_mip_mep`
- Methacholine: `src.pipeline_methacholine`
- Visit index: `src.pipeline_visit_index`
- Orquestador: `src.run_all_pipelines`

## Ejemplos

Pipeline individual:

```bash
python -m src.pipeline_fvl --start-date 2026-06-10 --end-date 2026-06-14
```

Orquestador:

```bash
python -m src.run_all_pipelines --start-date 2026-06-10 --end-date 2026-06-14
```

Visit index:

```bash
python -m src.pipeline_visit_index \
  --fvl-path data/processed/fvl_analytics_2026-06-10_2026-06-14.parquet \
  --dlco-path data/processed/dlco_analytics_2026-06-10_2026-06-14.parquet \
  --pleth-path data/processed/pleth_analytics_2026-06-10_2026-06-14.parquet \
  --mip-mep-path data/processed/mip_mep_analytics_2026-06-10_2026-06-14.parquet \
  --methacholine-path data/processed/methacholine_analytics_2026-06-10_2026-06-14.parquet \
  --output-path data/processed/visit_index_2026-06-10_2026-06-14.parquet
```

## Tests

- Unitarios: `pytest tests/unit -q`
- Suite por defecto: `pytest -q`
- Integración SQL Server: `pytest tests/integration --run-sqlserver -q`

## Datos sensibles

- No versionar PDFs clínicos.
- No versionar Parquet clínicos.
- No versionar CSV de validación con identificadores.
- Mantener `data/validation/` fuera de Git.

## Estado actual

- FVL, DLCO y Pleth están validados contra informes Breeze.
- MIP/MEP y Methacholine siguen pendientes de validación clínica.
- Los tests unitarios corren por defecto y la integración SQL Server requiere `--run-sqlserver`.
- El índice de visitas consolida la cobertura de pruebas por `pat_visit_id`.

## Pendientes

- Validar MIP/MEP con informes clínicos.
- Validar Methacholine con informes clínicos.
- Mantener la separación entre unitarios e integración SQL Server.
