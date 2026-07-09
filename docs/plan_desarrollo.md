# Plan de desarrollo

## Objetivo general

Construir un flujo reproducible para extraer pruebas funcionales respiratorias desde Breeze/SQL Server, transformarlas en salidas analíticas por visita, persistirlas en PostgreSQL y preparar salidas posteriores para análisis y publicación.

## Fase A - Componentes Breeze

Estado: implementada para los componentes principales, con validaciones clínicas pendientes en algunos casos.

Objetivo:

```text
SQL Server Breeze
    → extracción por componente
    → transformación analítica
    → Parquet por componente
```

Componentes:

```text
FVL
DLCO
Pleth
MIP/MEP
Methacholine
Visit index
```

Criterios de cierre:

```text
- extractor SQL Server
- transformación analítica
- Parquet reproducible
- prueba automatizada
- documentación de esquema
- validación contra informe clínico cuando aplique
```

Estado:

```text
FVL            implementado y validado parcialmente
DLCO           implementado y validado parcialmente
Pleth          implementado y validado parcialmente
MIP/MEP        implementado, pendiente de validación clínica
Methacholine   implementado, pendiente de validación clínica
Visit index    implementado
```

## Fase B - PostgreSQL staging

Estado: en desarrollo funcional.

Objetivo:

```text
Parquet analítico
    → auditoría de carga
    → PostgreSQL staging
```

Alcance:

```text
- conexión PostgreSQL
- DDL audit
- DDL staging inicial
- loader Parquet → staging
- carga por componente
- carga de todos los componentes de una ventana
- bloqueo de recarga duplicada
- columnas dinámicas
- validaciones básicas de conteo y duplicados
```

Fuera de alcance:

```text
- core
- deid
- BigQuery
- reglas finales de publicación
```

Criterios de cierre:

```text
- audit.load_control creado
- staging.* creado
- carga de los 6 componentes validada
- recarga duplicada bloqueada
- validaciones SQL documentadas
- documentación actualizada
- tests existentes pasando
```

## Fase C - Migración histórica a staging

Estado: pendiente.

Objetivo:

```text
Ejecutar cargas históricas por ventanas desde Parquet hacia PostgreSQL staging.
```

Estrategia propuesta:

```text
1. Definir rango histórico.
2. Definir tamaño de ventana.
3. Ejecutar pipelines por ventana.
4. Generar Parquet.
5. Cargar staging.
6. Validar auditoría y conteos.
7. Registrar incidencias.
```

Criterios de cierre:

```text
- todas las ventanas esperadas registradas en audit.load_control
- cargas exitosas documentadas
- fallos documentados
- conteos por componente revisados
- sin duplicados por load_id + pat_visit_id
```

## Fase D - PostgreSQL core

Estado: pendiente.

Objetivo:

```text
staging
    → modelo core identificado
```

La capa `core` debe ser el modelo persistente analítico estable. No debe ser una copia de Breeze ni una copia textual de `staging`.

Definiciones pendientes:

```text
- tablas core
- llaves primarias
- llaves foráneas
- tipos clínicos definitivos
- reglas de upsert
- reglas de consolidación por pat_visit_id
- manejo de recargas
- índices de consulta
```

## Fase E - Desidentificación y salida BigQuery

Estado: pendiente.

Objetivo:

```text
core
    → deid
    → BigQuery
```

Definiciones pendientes:

```text
- campos excluidos
- identificador seudonimizado estable
- salt controlado
- política de fechas
- documentación de datos sensibles
- esquema BigQuery
```

## Principios de trabajo

```text
- No consultar Breeze innecesariamente si ya existe Parquet reproducible.
- No eliminar Parquet como capa intermedia.
- No mezclar staging con core.
- No publicar datos identificados fuera de PostgreSQL controlado.
- No versionar datos clínicos ni archivos con identificadores.
- Mantener pruebas unitarias separadas de integración SQL Server.
```

## Validaciones mínimas por fase

### Fase B / staging

```text
- conteo Parquet = rows_read
- rows_read = rows_loaded
- rows_loaded = conteo en tabla staging
- status = success
- duplicados por load_id + pat_visit_id = 0
- registros clínicos presentes en visit_index
- recarga duplicada bloqueada
```

### Fase C / migración histórica

```text
- ventanas esperadas vs ventanas cargadas
- conteos por mes y componente
- identificación de ventanas vacías
- identificación de fallos
- trazabilidad completa en audit.load_control
```

### Fase D / core

```text
- unicidad por pat_visit_id y componente
- tipos clínicos válidos
- consistencia entre visit y resultados
- recargas idempotentes
- trazabilidad hacia staging
```
