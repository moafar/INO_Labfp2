# Esquema analítico de ergoespirometría

## Conclusión

La ergoespirometría conserva la relación general de Breeze:

```text
Patient -> PatVisit -> GXTest
                    -> GXPredicted
```

La diferencia respecto a FVL, DLCO o pletismografía es física, no relacional.
`GXTest` contiene la cabecera de la prueba y guarda las series fisiológicas en
`GXTestRawData` (`varbinary(max)`). Las mediciones introducidas durante la
prueba se guardan en `ManuallyEnteredData` (`varbinary(max)`). `GXPredicted`
aporta una única fila de valores predichos por `PatVisitID` en los datos
revisados.

Por tanto, `GXTest` basta para localizar y reconstruir la señal registrada,
pero no basta por sí sola para una tabla analítica completa: se debe conservar
la visita para enlazar paciente, fecha y valores predichos.

## Unidad de extracción

La consulta debe comenzar en `GXTest`, no en `GXPredicted`:

- `GXTest`: 1821 pruebas y 1820 visitas en la revisión.
- `GXPredicted`: 10781 visitas, de las cuales 8961 no tenían `GXTest`.
- una visita tenía dos pruebas GX que compartían su fila predicha.

La clave de la prueba es `GXTestID`; `PatVisitID` es la clave de enlace con la
visita y los predichos. Una prueba es decodificable cuando
`GXTestRawData IS NOT NULL`. Se observaron 1816 binarios decodificables y cinco
registros sin serie.

## GXTestRawData versión 10

Los 1816 binarios examinados declararon versión 10, doce canales y cumplieron
exactamente:

```text
longitud = 326 + 44 * N
```

`N` es el número de observaciones, almacenado como `uint16` little-endian en el
offset 10 (bytes 11-12 en SQL Server). Su rango observado fue 10-815.

| Segmento | Longitud | Interpretación |
|---|---:|---|
| Cabecera | 36 bytes | Versión, longitud, 12 canales, N y campos aún no descritos |
| Canales auxiliares | 4 × N | Dos `uint16` por observación; significado pendiente |
| Diez bloques | 10 × (6 + 4 × N) | Descriptor de 6 bytes y N valores `int32` |
| Cola | 230 bytes | Estructura aún no descrita; se conserva intacta |

En cada descriptor se han confirmado el identificador en el primer byte y la
escala `uint16` little-endian en los bytes 3-4. Los demás bytes se conservan
sin interpretación.

| ID | Escala | Alias actual | Confianza |
|---:|---:|---|---|
| 1 | 1000 | `elapsed_time_s` | Confirmado |
| 11 | 1000 | `breath_duration_s` | Provisional |
| 10 | 1000 | `tidal_volume_l` | Provisional |
| 12 | 1000 | `vo2_ml_min` | Provisional |
| 18 | 1000 | `heart_rate_bpm` | Provisional |
| 20 | 10000 | `fio2_fraction` | Provisional |
| 19 | 10000 | `feo2_fraction` | Provisional |
| 15 | 1000 | `ventilation_l_min` | Provisional |
| 17 | 10000 | `fico2_fraction` | Provisional |
| 16 | 10000 | `feco2_fraction` | Provisional |

El código conserva siempre `channel_id`, escala, descriptor y valores enteros
originales. Así, un alias provisional puede corregirse sin perder trazabilidad.

## ManuallyEnteredData

La estructura se consumió exactamente en las dos muestras disponibles:

```text
uint16 reservado
uint32 cantidad de eventos
repetir por evento:
    double fecha OLE Automation
    uint16 cantidad de mediciones
    repetir por medición:
        uint16 código
        double valor
```

La fecha usa el origen `1899-12-30`. Los códigos confirmados son:

| Código | Medición | Conversión |
|---:|---|---|
| 3037 | Presión sistólica | kPa × 7.50062 = mmHg |
| 3038 | Presión diastólica | kPa × 7.50062 = mmHg |
| 3068 | Frecuencia cardiaca | Sin conversión, bpm |
| 3180 | SpO2 | Sin conversión, % |

Los códigos desconocidos no se descartan: salen con código y valor originales.

## Marcadores y predichos

`StartExerciseTime`, `StartRecoveryTime`, `ATElapsedTime`, `RCElapsedTime` y
`VO2MaxElapsedTime` están expresados en segundos sobre el mismo eje temporal de
`elapsed_time_s`. Para reproducir los minutos relativos al comienzo del
ejercicio:

```text
(marcador - StartExerciseTime) / 60
```

`GXPredicted` se enlaza por `PatVisitID`. Sus valores no son nuevas pruebas y
no deben usarse para decidir la existencia de una ergoespirometría.

## Implementación

- `sql/extract_ergoespirometry.sql`: parte de `GXTest`, enlaza visita, paciente
  y predichos, y conserva ambos binarios.
- `src/extract/ergoespirometry.py`: ejecuta la extracción por ventana.
- `src/transform/ergoespirometry.py`: valida y decodifica ambos formatos.
- `tests/unit/test_transform_ergoespirometry.py`: cubre longitud, escalas,
  tabla longitudinal, fechas OLE, conversiones y códigos desconocidos.

Los archivos clínicos usados para la validación no se versionan.
