# labfp2

ETL en Python para Breeze/SQL Server en laboratorio de función pulmonar.

El proyecto extrae datos clínicos desde SQL Server, transforma cada estudio a una tabla analítica por visita, guarda salidas reproducibles en Parquet y permite cargar esas salidas en PostgreSQL `staging`.

## Arquitectura

Flujo general:

1. `src/extract/` lee SQL Server Breeze.
2. `src/transform/` consolida y calcula métricas derivadas.
3. `src/load/parquet.py` escribe Parquet analíticos.
4. `src/run_all_pipelines.py` orquesta todos los estudios.
5. `src/pipeline_visit_index.py` construye el índice analítico de visitas.
6. `src/load/postgres.py` carga Parquet en PostgreSQL `staging`.
7. `src/pipeline_load_staging.py` ejecuta cargas Parquet → PostgreSQL `staging`.

La capa Parquet se mantiene como punto físico reproducible entre extracción y persistencia. PostgreSQL `staging` no reemplaza los Parquet; los consume.

## Estructura

- `src/` código fuente.
- `src/extract/` extracción SQL Server.
- `src/transform/` transformaciones analíticas.
- `src/load/parquet.py` salida a Parquet.
- `src/load/postgres.py` carga de Parquet a PostgreSQL `staging`.
- `src/config/` catálogos validados de columnas.
- `src/pipeline_*.py` entrypoints por componente.
- `src/run_all_pipelines.py` orquestador general.
- `src/pipeline_visit_index.py` índice de visitas.
- `src/pipeline_load_staging.py` carga PostgreSQL `staging`.
- `sql/postgres/` DDL versionado para auditoría y staging.
- `tests/unit/` tests unitarios.
- `tests/integration/` tests con SQL Server.
- `docs/` documentación y validaciones.

## Pipelines

- FVL: `src.pipeline_fvl`
- DLCO: `src.pipeline_dlco`
- Pleth: `src.pipeline_pleth`
- MIP/MEP: `src.pipeline_mip_mep`
- Methacholine: `src.pipeline_methacholine`
- Ergoespirometría: extracción y decodificador binario documentados; pipeline
  analítico pendiente de definir tras validar los alias provisionales
- Visit index: `src.pipeline_visit_index`
- Orquestador: `src.run_all_pipelines`
- Carga PostgreSQL staging: `src.pipeline_load_staging`

## Variables de entorno

El proyecto usa `.env` local. No debe versionarse.

Variables SQL Server:

```text
SQLSERVER_HOST
SQLSERVER_PORT
SQLSERVER_DATABASE
SQLSERVER_USER
SQLSERVER_PASSWORD
SQLSERVER_DRIVER
```

Variables PostgreSQL:

```text
POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DATABASE
POSTGRES_USER
POSTGRES_PASSWORD
```

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

Carga de una ventana ya generada en Parquet hacia PostgreSQL `staging`:

```bash
python -m src.pipeline_load_staging \
  --start-date 2026-07-08 \
  --end-date 2026-07-09 \
  --component all
```

Carga de un solo componente:

```bash
python -m src.pipeline_load_staging \
  --start-date 2026-07-08 \
  --end-date 2026-07-09 \
  --component visit_index
```

## PostgreSQL staging

La fase actual llega solamente hasta la capa `staging`.

Tablas iniciales:

```text
staging.visit_index
staging.fvl_analytics
staging.dlco_analytics
staging.pleth_analytics
staging.mip_mep_analytics
staging.methacholine_analytics
audit.load_control
```

La carga a `staging`:

- parte siempre de Parquet;
- agrega `load_id`, `loaded_at`, ventana de extracción, ruta de archivo y hash;
- registra cada carga en `audit.load_control`;
- bloquea recargas accidentales del mismo archivo sobre la misma tabla;
- agrega dinámicamente columnas faltantes de los Parquet;
- protege duplicados por `load_id + pat_visit_id`.

La capa `core` no forma parte de esta fase.

## Tests

- Unitarios: `pytest tests/unit -q`
- Suite por defecto: `pytest -q`
- Integración SQL Server: `pytest tests/integration --run-sqlserver -q`
- Compilación Python: `python -m compileall src`

## Datos sensibles

- No versionar PDFs clínicos.
- No versionar Parquet clínicos.
- No versionar CSV de validación con identificadores.
- No versionar `.env`.
- Mantener `data/validation/` fuera de Git.

## Estado actual

- FVL, DLCO y Pleth están validados contra informes Breeze.
- MIP/MEP y Methacholine siguen pendientes de validación clínica.
- Ergoespirometría tiene documentada la estructura binaria versión 10 y un
  decodificador validado; los nombres fisiológicos salvo el tiempo siguen
  marcados como provisionales.
- Los tests unitarios corren por defecto y la integración SQL Server requiere `--run-sqlserver`.
- El índice de visitas consolida la cobertura de pruebas por `pat_visit_id`.
- PostgreSQL `staging` está implementado para cargar Parquet analíticos con auditoría.

## Pendientes

- Validar MIP/MEP con informes clínicos.
- Validar Methacholine con informes clínicos.
- Mantener la separación entre unitarios e integración SQL Server.
- Ejecutar migración histórica por ventanas hacia PostgreSQL `staging`.
- Diseñar la capa `core` en una fase posterior.
