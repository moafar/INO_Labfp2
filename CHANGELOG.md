# Changelog

## [Unreleased]

### Added

- Pipelines funcionales para FVL, DLCO, Pleth, MIP/MEP y Methacholine.
- Entry points para DLCO y Pleth.
- Orquestador general `src.run_all_pipelines`.
- Índice analítico de visitas y pruebas.
- Separación de tests unitarios e integración SQL Server.

### Changed

- Los tests con SQL Server quedaron aislados en `tests/integration/`.
- La suite por defecto evita tocar SQL Server sin `--run-sqlserver`.

### Fixed

- Fallback por SD para z-scores en DLCO, FVL y Pleth.
- Ajuste de `dlva_zscore_pre` validado contra Breeze.

### Validation

- Validación ad-hoc contra informes Breeze para DLCO y Pleth.
- FVL, DLCO y Pleth quedaron comparados contra informes reales de muestra.

### Pending

- Validación clínica de MIP/MEP.
- Validación clínica de Methacholine.
- Consolidación posterior de nuevas métricas de cobertura si aparecen más estudios.
