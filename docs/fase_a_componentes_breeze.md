# Fase A - Componentes Breeze

## Objetivo

Cerrar la Fase A para las pruebas funcionales respiratorias disponibles en Breeze antes de diseñar incrementalidad, BigQuery y carga.

Fase A significa que cada componente debe tener:

1. Tablas y campos SQL Server identificados.
2. Query de extracción creada.
3. Regla funcional de prueba realizada validada.
4. Transformación analítica creada.
5. Resultado representativo validado.
6. Comparación con Patient Query.
7. Esquema analítico documentado.
8. Pruebas automatizadas creadas.

## Componentes de la guía clínica

| Prueba clínica | Componente técnico | Tabla principal | Indicador principal | Estado |
|---|---|---|---|---|
| Espirometría pre y post broncodilatador | FVL | `FVLData` | `PatVisit.FVLTest` | Cerrado hasta pruebas automatizadas |
| Volúmenes pulmonares pre y post broncodilatador | Pleth | `PlethData` | `PatVisit.PlethTest` | Fuente y regla identificadas |
| Resistencias en la vía aérea pre y post broncodilatador | Pleth / RAW | `PlethData` | `PatVisit.PlethTest` | Fuente y regla identificadas |
| Capacidad de difusión con monóxido de carbono | DLCO | `DLCOData` | `PatVisit.DLCOTest`, no suficiente como regla | Fuente y regla identificada |
| Medición de fuerza inspiratoria y espiratoria máxima | MIP/MEP | `MipData` | `PatVisit.MipMepTest`, no suficiente como regla | Fuente y regla identificada |
| Test de broncoprovocación con metacolina | Challenge / ExFVL | No confirmado | No confirmado | Sin registros compatibles encontrados |

## Reglas funcionales provisionales

### FVL / Espirometría

    pv.FVLTest = 1
    AND EXISTS (
        SELECT 1
        FROM dbo.FVLData AS fvl_effort
        WHERE fvl_effort.PatVisitID = pv.PatVisitID
          AND fvl_effort.EffortTypeID = 0
    )

En la extracción productiva se usa un `INNER JOIN` contra visitas FVL con maniobras para evitar un `EXISTS` correlacionado.

    INNER JOIN (
        SELECT DISTINCT PatVisitID
        FROM dbo.FVLData
        WHERE EffortTypeID = 0
    ) AS visitas_con_maniobras
        ON visitas_con_maniobras.PatVisitID = pv.PatVisitID

### Pleth / Volúmenes pulmonares y resistencias

    pv.PlethTest = 1
    AND EXISTS (
        SELECT 1
        FROM dbo.PlethData AS pl_effort
        WHERE pl_effort.PatVisitID = pv.PatVisitID
          AND pl_effort.EffortTypeID = 0
    )

`PlethData` contiene simultáneamente variables de volúmenes pulmonares y resistencias. La tabla tiene indicadores de selección separados para TGV/volúmenes y RAW/resistencias, por lo que no debe asumirse que una única fila seleccionada representa todos los resultados.

### DLCO / Difusión de monóxido de carbono

    EXISTS (
        SELECT 1
        FROM dbo.DLCOData AS dl_effort
        WHERE dl_effort.PatVisitID = pv.PatVisitID
          AND dl_effort.EffortTypeID = 0
    )

`PatVisit.DLCOTest` no debe ser obligatorio como regla funcional porque se encontraron visitas con `DLCOTest = 0` y maniobras reales, y visitas con `DLCOTest = 1` pero solo filas estructurales.

### MIP/MEP / Fuerza inspiratoria y espiratoria máxima

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

La existencia de maniobras no basta para MIP/MEP. La regla exige resultado representativo válido en Pre/Baseline.

### Metacolina / Broncoprovocación

No se encontraron registros compatibles con broncoprovocación con metacolina en la réplica local revisada.

Los registros observados en `GXTest` y `ExFVLData` corresponden a pruebas de ejercicio con protocolo de bicicleta o rampa, no a metacolina. Por tanto, no se construirá extractor definitivo de metacolina hasta disponer de datos reales o de un Patient Query compatible.

## Decisión de diseño provisional

La Fase A continuará por componente técnico, no directamente por nombre clínico de la guía.

Orden de trabajo:

1. DLCO.
2. Pleth.
3. MIP/MEP.
4. Metacolina solo como documentación de ausencia de datos compatibles.

`PlethData` se tratará como un componente técnico único de pletismografía. Más adelante se decidirá si BigQuery publica una tabla combinada o vistas separadas para volúmenes pulmonares y resistencias.

## Estado operativo

FVL queda como patrón de referencia para los demás componentes:

- extracción desde SQL Server;
- transformación a una fila analítica por visita;
- uso directo de filas Pre/Baseline y Post;
- no reconstrucción de resultados mediante máximos de maniobras;
- comparación contra Patient Query;
- documentación del esquema analítico;
- pruebas automatizadas.

El siguiente componente a construir es DLCO.
