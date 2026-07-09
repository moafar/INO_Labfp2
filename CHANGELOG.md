# Changelog

## [Unreleased]

### Added

- Pipelines funcionales para FVL, DLCO, Pleth, MIP/MEP y Methacholine.
- Entry points para DLCO y Pleth.
- Orquestador general `src.run_all_pipelines`.
- Índice analítico de visitas y pruebas.
- Separación de tests unitarios e integración SQL Server.
- Conexión PostgreSQL encapsulada en `src.postgres`.
- DDL PostgreSQL versionado en `sql/postgres/`.
- Tabla de auditoría `audit.load_control`.
- Tablas iniciales de PostgreSQL `staging` para:
  - `visit_index`
  - `fvl_analytics`
  - `dlco_analytics`
  - `pleth_analytics`
  - `mip_mep_analytics`
  - `methacholine_analytics`
- Loader Parquet → PostgreSQL `staging` en `src.load.postgres`.
- Entry point `src.pipeline_load_staging`.
- Bloqueo de recarga accidental por `target_schema`, `target_table` y `source_file_hash`.
- Agregado dinámico de columnas faltantes en tablas `staging`.
- Restricciones únicas por `load_id + pat_visit_id` en tablas staging.
- Documentación específica de PostgreSQL staging.
- Plan de desarrollo por fases.

### Changed

- Los tests con SQL Server quedaron aislados en `tests/integration/`.
- La suite por defecto evita tocar SQL Server sin `--run-sqlserver`.
- La arquitectura documentada incorpora PostgreSQL `staging` sin eliminar la capa Parquet.
- La Fase A queda documentada como fase de cierre de componentes analíticos, anterior a la persistencia PostgreSQL.
- `requirements.txt` incorpora dependencias para PostgreSQL:
  - `SQLAlchemy`
  - `psycopg2-binary`

### Fixed

- Fallback por SD para z-scores en DLCO, FVL y Pleth.
- Ajuste de `dlva_zscore_pre` validado contra Breeze.
- Mensaje limpio para recargas duplicadas hacia PostgreSQL staging.

### Validation

- Validación ad-hoc contra informes Breeze para DLCO y Pleth.
- FVL, DLCO y Pleth quedaron comparados contra informes reales de muestra.
- Carga PostgreSQL staging validada con ventana `2026-07-08` a `2026-07-09`.
- Conteos validados entre Parquet, `audit.load_control` y tablas `staging`.
- Validación sin duplicados por `load_id + pat_visit_id`.
- Validación de correspondencia entre tablas clínicas y `staging.visit_index`.
- Bloqueo de recarga duplicada validado.
- Suite local validada con `python -m compileall src` y `pytest`.

### Pending

- Validación clínica de MIP/MEP.
- Validación clínica de Methacholine.
- Consolidación posterior de nuevas métricas de cobertura si aparecen más estudios.
- Migración histórica por ventanas hacia PostgreSQL `staging`.
- Diseño de capa `core` en PostgreSQL en una fase posterior.
- Diseño de capa desidentificada y salida BigQuery en una fase posterior.
