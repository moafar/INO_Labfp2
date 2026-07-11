# Migración histórica a PostgreSQL staging

## Alcance

Migración histórica de datos analíticos derivados de Breeze / SQL Server hacia PostgreSQL staging.

Periodo cubierto:

- Fecha inicial: 2023-02-01
- Fecha final exclusiva: 2026-07-01
- Equivalencia funcional: visitas con fecha <= 2026-06-30

## Estado de auditoría

Todas las cargas registradas finalizaron correctamente.

| Estado | Registros |
|---|---:|
| success | 235 |

No quedaron cargas en estado `running` ni `failed`.

## Resumen por tabla

| Tabla | Cargas | Filas cargadas | Desde | Hasta |
|---|---:|---:|---|---|
| staging.visit_index | 41 | 43.900 | 2023-02-01 | 2026-07-01 |
| staging.fvl_analytics | 41 | 32.991 | 2023-02-01 | 2026-07-01 |
| staging.dlco_analytics | 41 | 15.443 | 2023-02-01 | 2026-07-01 |
| staging.pleth_analytics | 41 | 12.884 | 2023-02-01 | 2026-07-01 |
| staging.mip_mep_analytics | 41 | 827 | 2023-02-01 | 2026-07-01 |
| staging.methacholine_analytics | 30 | 946 | 2023-02-01 | 2026-07-01 |

## Validaciones realizadas

1. Los conteos físicos de las tablas coinciden con `audit.load_control`.
2. No se identificaron duplicados internos por `pat_visit_id`.
3. Todas las visitas presentes en tablas analíticas existen en `staging.visit_index`.
4. Las ventanas no registradas corresponden a Parquet vacíos.
5. La carga histórica fue ejecutada por ventanas mensuales cerradas-abiertas.

## Observación sobre metacolina

`staging.methacholine_analytics` tiene menos cargas registradas porque los meses sin filas fueron omitidos por el orquestador histórico. Esta decisión evita registrar repetidamente Parquet vacíos con el mismo hash.

## Código utilizado

```bash
python -m src.pipeline_historical_staging \
  --start-date 2023-04-01 \
  --end-date 2026-07-01 \
  --component all
```

El orquestador está versionado en GitHub, rama `main`.
