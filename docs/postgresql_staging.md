# PostgreSQL staging

## Objetivo

Documentar la fase de persistencia PostgreSQL `staging` del proyecto `labfp2`.

Esta fase llega solamente hasta cargar en PostgreSQL las salidas Parquet generadas por los pipelines actuales. No incluye diseño de capa `core`, desidentificación ni BigQuery.

## Principio de arquitectura

El Parquet se mantiene como capa física reproducible.

```text
SQL Server Breeze
    → extracción
    → transformación
    → Parquet analítico
    → PostgreSQL staging
```

La carga a PostgreSQL no consulta directamente SQL Server. Siempre parte de los Parquet ya generados.

## Esquemas involucrados

```text
audit
staging
```

La base PostgreSQL puede tener otros esquemas, como `core` o `deid`, pero no forman parte de esta fase.

## Tablas de auditoría

### audit.load_control

Registra cada intento de carga Parquet → PostgreSQL staging.

Campos principales:

```text
load_id
pipeline_name
target_schema
target_table
source_system
source_start_date
source_end_date
source_file
source_file_hash
rows_read
rows_loaded
started_at
finished_at
status
error_message
```

Restricciones principales:

```text
PRIMARY KEY (load_id)
UNIQUE (target_schema, target_table, source_file_hash)
```

La restricción única bloquea recargas accidentales del mismo archivo sobre la misma tabla.

## Tablas staging iniciales

```text
staging.visit_index
staging.fvl_analytics
staging.dlco_analytics
staging.pleth_analytics
staging.mip_mep_analytics
staging.methacholine_analytics
```

Todas las tablas tienen metadatos de carga:

```text
load_id
loaded_at
source_start_date
source_end_date
source_file
source_file_hash
```

Todas las tablas clínicas tienen `pat_visit_id`.

Cada tabla tiene protección contra duplicados por:

```text
load_id + pat_visit_id
```

## Tipado

La capa `staging` prioriza preservación y tolerancia a cambios de estructura.

Criterio general:

```text
metadatos operativos tipados
identificador de visita tipado
columnas clínicas mayoritariamente text
```

Tipos operativos:

```text
load_id              text
loaded_at            timestamptz
source_start_date    date
source_end_date      date
source_file          text
source_file_hash     text
pat_visit_id         bigint
visit_datetime       timestamp without time zone
flags de cobertura   boolean
test_count           bigint
```

El resto de columnas agregadas dinámicamente se crean como `text`.

## Carga

Entry point:

```bash
python -m src.pipeline_load_staging \
  --start-date 2026-07-08 \
  --end-date 2026-07-09 \
  --component all
```

Componentes permitidos:

```text
visit_index
fvl
dlco
pleth
mip_mep
methacholine
all
```

La carga espera encontrar los Parquet en `data/processed/`.

Ejemplo para un solo componente:

```bash
python -m src.pipeline_load_staging \
  --start-date 2026-07-08 \
  --end-date 2026-07-09 \
  --component fvl
```

## DDL

Archivos versionados:

```text
sql/postgres/001_create_audit_tables.sql
sql/postgres/002_create_staging_tables.sql
```

Aplicación manual:

```bash
psql -h 127.0.0.1 -U rom -d obsino -f sql/postgres/001_create_audit_tables.sql
psql -h 127.0.0.1 -U rom -d obsino -f sql/postgres/002_create_staging_tables.sql
```

## Validaciones ejecutadas

Ventana validada:

```text
2026-07-08 <= VisitDateTime < 2026-07-09
```

Resultados de carga:

```text
visit_index     42 filas
fvl             27 filas
dlco            16 filas
pleth           14 filas
mip_mep          3 filas
methacholine     2 filas
```

Validaciones realizadas:

```text
- rows_read = rows_loaded en audit.load_control
- conteos staging = conteos audit
- columnas dinámicas creadas correctamente
- duplicados por load_id + pat_visit_id = 0
- todas las filas clínicas tienen correspondencia en staging.visit_index
- recarga duplicada bloqueada por source_file_hash
- intento fallido no inserta filas adicionales en staging
```

Validaciones de código:

```bash
python -m compileall src
pytest
```

Resultado observado:

```text
12 passed, 31 skipped
```

## Alcance excluido

No pertenece a esta fase:

```text
core.visit
core.*_result
deid
BigQuery
reglas finales de publicación analítica
desidentificación
```

## Siguiente fase

La siguiente fase debe diseñar `core` a partir de `staging`.

Esa fase deberá definir:

```text
- modelo relacional/analítico estable
- llaves finales
- upsert por pat_visit_id
- tipos clínicos definitivos
- reglas de consolidación
- índices de consulta
- relación con capa desidentificada
```
