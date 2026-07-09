# Fase A - Componentes Breeze

## Objetivo

Cerrar la Fase A para las pruebas funcionales respiratorias disponibles en Breeze antes de avanzar a persistencia PostgreSQL, migración histórica, capa `core`, desidentificación y BigQuery.

Fase A significa que cada componente debe tener:

1. Tablas y campos SQL Server identificados.
2. Query de extracción creada.
3. Regla funcional de prueba realizada validada.
4. Transformación analítica creada.
5. Resultado representativo validado.
6. Comparación con Patient Query cuando exista correspondencia.
7. Esquema analítico documentado.
8. Pruebas automatizadas creadas.
9. Salida Parquet reproducible.

## Componentes de la guía clínica

| Prueba clínica | Componente técnico | Tabla principal | Indicador principal | Estado |
|---|---|---|---|---|
| Espirometría pre y post broncodilatador | FVL | `FVLData` | `PatVisit.FVLTest` | Implementado y validado parcialmente |
| Volúmenes pulmonares pre y post broncodilatador | Pleth | `PlethData` | `PatVisit.PlethTest` | Implementado y validado parcialmente |
| Resistencias en la vía aérea pre y post broncodilatador | Pleth / RAW | `PlethData` | `PatVisit.PlethTest` | Integrado en componente técnico Pleth |
| Capacidad de difusión con monóxido de carbono | DLCO | `DLCOData` | `PatVisit.DLCOTest`, no suficiente como regla | Implementado y validado parcialmente |
| Medición de fuerza inspiratoria y espiratoria máxima | MIP/MEP | `MipData` | `PatVisit.MipMepTest`, no suficiente como regla | Implementado, pendiente de validación clínica |
| Test de broncoprovocación con metacolina | Methacholine / Challenge | Extractor específico del proyecto | Regla funcional documentada en pipeline | Implementado, pendiente de validación clínica |

## Reglas funcionales

### FVL / Espirometría

```sql
pv.FVLTest = 1
AND EXISTS (
    SELECT 1
    FROM dbo.FVLData AS fvl_effort
    WHERE fvl_effort.PatVisitID = pv.PatVisitID
      AND fvl_effort.EffortTypeID = 0
)
```

En la extracción productiva se usa un `INNER JOIN` contra visitas FVL con maniobras para evitar un `EXISTS` correlacionado.

```sql
INNER JOIN (
    SELECT DISTINCT PatVisitID
    FROM dbo.FVLData
    WHERE EffortTypeID = 0
) AS visitas_con_maniobras
    ON visitas_con_maniobras.PatVisitID = pv.PatVisitID
```

### Pleth / Volúmenes pulmonares y resistencias

```sql
pv.PlethTest = 1
AND EXISTS (
    SELECT 1
    FROM dbo.PlethData AS pl_effort
    WHERE pl_effort.PatVisitID = pv.PatVisitID
      AND pl_effort.EffortTypeID = 0
)
```

`PlethData` contiene simultáneamente variables de volúmenes pulmonares y resistencias. La tabla tiene indicadores de selección separados para TGV/volúmenes y RAW/resistencias, por lo que no debe asumirse que una única fila seleccionada representa todos los resultados.

### DLCO / Difusión de monóxido de carbono

```sql
EXISTS (
    SELECT 1
    FROM dbo.DLCOData AS dl_effort
    WHERE dl_effort.PatVisitID = pv.PatVisitID
      AND dl_effort.EffortTypeID = 0
)
```

`PatVisit.DLCOTest` no debe ser obligatorio como regla funcional porque se encontraron visitas con `DLCOTest = 0` y maniobras reales, y visitas con `DLCOTest = 1` pero solo filas estructurales.

### MIP/MEP / Fuerza inspiratoria y espiratoria máxima

```sql
EXISTS (
    SELECT 1
    FROM dbo.MipData AS md_pre
    WHERE md_pre.PatVisitID = pv.PatVisitID
      AND md_pre.EffortTypeID = 2
      AND (
          md_pre.MIP <> 0
          OR md_pre.MEP <> 0
      )
)
```

La existencia de maniobras no basta para MIP/MEP. La regla exige resultado representativo válido en Pre/Baseline.

### Metacolina / Broncoprovocación

El componente Methacholine queda incorporado al conjunto de pipelines analíticos del proyecto y genera salida Parquet con granularidad por visita.

La validación clínica contra informes o fuente externa compatible sigue pendiente.

## Decisión de diseño

La Fase A se organiza por componente técnico, no directamente por nombre clínico de la guía.

Componentes técnicos implementados:

1. FVL.
2. DLCO.
3. Pleth.
4. MIP/MEP.
5. Methacholine.
6. Visit index.

`PlethData` se trata como un componente técnico único de pletismografía. Más adelante se decidirá si la capa `core` publica una tabla combinada o estructuras separadas para volúmenes pulmonares y resistencias.

## Relación con PostgreSQL staging

La Fase A produce salidas Parquet analíticas por componente.

La fase PostgreSQL staging parte de esas salidas Parquet y no modifica las reglas clínicas ni la transformación analítica de Fase A.

Flujo entre fases:

```text
Fase A:
SQL Server Breeze
    → extracción
    → transformación analítica
    → Parquet por componente

Fase PostgreSQL staging:
Parquet por componente
    → auditoría de carga
    → tablas staging
```

La capa `core` no pertenece a Fase A ni a la fase actual de staging. Se diseñará posteriormente, usando como insumo las tablas `staging` ya cargadas y auditadas.

## Estado operativo

FVL queda como patrón de referencia para los demás componentes:

- extracción desde SQL Server;
- transformación a una fila analítica por visita;
- uso directo de filas Pre/Baseline y Post;
- no reconstrucción de resultados mediante máximos de maniobras;
- comparación contra Patient Query;
- documentación del esquema analítico;
- pruebas automatizadas;
- salida Parquet reproducible.

Estado actual:

- FVL, DLCO y Pleth están implementados y validados contra muestras de informes Breeze.
- MIP/MEP está implementado y pendiente de validación clínica.
- Methacholine está implementado y pendiente de validación clínica.
- Visit index consolida cobertura de pruebas por `pat_visit_id`.
- PostgreSQL staging ya puede cargar los Parquet analíticos sin alterar Fase A.
