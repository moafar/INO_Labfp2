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
| 11 | 1000 | `breath_duration_s` | Validado |
| 10 | 1000 | `channel_10` | Desconocido |
| 12 | 1000 | `tidal_volume_atps_ml` | Validado |
| 18 | 1000 | `channel_18` | Desconocido |
| 20 | 10000 | `fio2_fraction` | Provisional |
| 19 | 10000 | `feo2_fraction` | Provisional |
| 15 | 1000 | `channel_15` | Desconocido |
| 17 | 10000 | `fico2_fraction` | Provisional |
| 16 | 10000 | `feco2_fraction` | Provisional |

### Validación contra Patient Query

La exportación `GX INO Resultados2.xls` contenía 465 ergoespirometrías
completas. La réplica `MGCDBase_DEV` cubría el periodo hasta el 1 de julio de
2026 y permitió emparejar exactamente 428 pruebas por documento y fecha-hora.
Una de ellas, `GXTestID 3712`, no tenía `GXTestRawData`; por tanto, la
validación de señales utilizó 427 pruebas decodificables.

La partición es determinista: los `GXTestID` divisibles por cinco forman las 85
pruebas de evaluación y las 342 restantes se usan para seleccionar fórmula,
posición, ventana, estadístico y calibración. Una regla debe cubrir al menos el
80 % de la cobertura máxima para no favorecer submuestras pequeñas. La tabla
informa la calibración proporcional ajustada solo en entrenamiento; `MdAPE` es
el error porcentual absoluto mediano en evaluación.

| Variable | Momento | Regla temporal | R² | MAE | MdAPE |
|---|---|---|---:|---:|---:|
| RR (br/min) | Rest | media, 30 s previos | 0,794 | 1,60 | 5,05 % |
| RR (br/min) | AT | media, 10 s previos | 0,955 | 1,22 | 3,16 % |
| RR (br/min) | VO₂ Max | mediana, 10 s previos | 0,958 | 1,20 | 2,16 % |
| Vt BTPS (L) | Rest | media, 45 s previos | 0,851 | 0,053 | 6,17 % |
| Vt BTPS (L) | AT | mediana, 30 s centrados | 0,956 | 0,064 | 4,65 % |
| Vt BTPS (L) | VO₂ Max | media, 10 s previos | 0,984 | 0,048 | 2,31 % |
| VE BTPS (L/min) | Rest | media, 30 s previos | 0,726 | 0,90 | 4,16 % |
| VE BTPS (L/min) | AT | media, 10 s previos | 0,970 | 1,10 | 2,44 % |
| VE BTPS (L/min) | VO₂ Max | media, 10 s previos | 0,989 | 1,43 | 1,93 % |

Las fórmulas implementadas antes de cualquier corrección empírica son:

```text
RR (br/min) = 60 / breath_duration_s
Vt_ATPS (L) = tidal_volume_atps_ml / 1000
VE_ATPS (L/min) = Vt_ATPS * RR
```

RR queda derivada mediante una identidad dimensional validada. El volumen del
canal 12 y VE calculada son candidatos ATPS; Patient Query publica BTPS. Los
factores proporcionales permanecen cerca de uno, pero siguen siendo
calibraciones y no correcciones ambientales confirmadas.

### VO₂, VCO₂ y variables derivadas

Se evaluó Haldane con fracciones inspiradas medidas y con una alternativa de
aire ambiente, además de la diferencia simple de fracciones:

```text
FIN2 = 1 - FIO2 - FICO2
FEN2 = 1 - FEO2 - FECO2
VI = VE * FEN2 / FIN2
VO2 = (VI * FIO2 - VE * FEO2) * 1000
VCO2 = (VE * FECO2 - VI * FICO2) * 1000
```

Los signos y unidades son coherentes, pero la salida sin calibrar sobrestima
Patient Query. El factor proporcional de VO₂ cambia aproximadamente de 0,51
en Rest a 0,56 en AT y 0,57 en VO₂ Max; no es una corrección única estable.
Por ello no se ha incorporado una reconstrucción productiva silenciosa.

| Variable | Momento | R² evaluación | MAE (mL/min) | MdAPE |
|---|---|---:|---:|---:|
| VO₂ calibrado | Rest | 0,632 | 35,7 | 9,28 % |
| VO₂ calibrado | AT | 0,964 | 58,4 | 5,88 % |
| VO₂ calibrado | VO₂ Max | 0,968 | 80,7 | 5,50 % |
| VCO₂ calibrado | Rest | 0,663 | 30,4 | 8,78 % |
| VCO₂ calibrado | AT | 0,951 | 55,2 | 4,80 % |
| VCO₂ calibrado | VO₂ Max | 0,984 | 63,1 | 2,94 % |

Los ajustes afines mejoran algunos resultados, pero introducen interceptos de
decenas de mL/min sin explicación física; se conservan como análisis y no como
fórmula confirmada.

La estratificación independiente por cuartiles confirma que el error no es
homogéneo. El MdAPE de VO₂ varía entre 7,47-11,01 % en Rest, 2,44-8,73 % en AT
y 4,74-6,50 % en VO₂ Max; para VCO₂ los intervalos son 8,19-11,39 %,
4,52-6,52 % y 1,90-4,29 %. RR, Vt y VE son más estables, aunque Rest conserva
menor R². El CSV de estabilidad y el parquet de residuos permiten revisar cada
cuartil y los cuantiles p05-p95 sin volver a ajustar los modelos.

`RQ/RER = VCO2 / VO2` es más estable porque cancela parte del factor común. La
calibración proporcional logra R² de 0,813, 0,868 y 0,889 y MdAPE de 2,04 %,
1,95 % y 2,18 % en Rest, AT y VO₂ Max. `VE/VO2`, `VE/VCO2` y `VO2/HR` publicados
son sus cocientes algebraicos redondeados. Su reconstrucción desde Breeze
hereda la incertidumbre de VO₂/VCO₂; las funciones productivas solo implementan
los cocientes con unidades y denominadores seguros.

### Semántica temporal

Patient Query redondea `GX * Time (min)` a minutos. Frente a los marcadores SQL,
AT y VO₂ Max cubren aproximadamente -30 a +30 segundos. En Rest, el instante
exacto es `StartExerciseTime`; usar el minuto exportado como segundo objetivo
explicaba gran parte del peor resultado previo.

No aparece una ventana universal. VO₂ Max favorece los 10 segundos previos;
Rest necesita 20-45 segundos previos; AT combina 10 segundos previos para
RR/VE con 30 segundos centrados para Vt. Las ventanas posteriores no explican
de forma estable los tres momentos.

### Canales sin identidad confirmada

- El canal 10 mantiene una relación moderada con la duración respiratoria, pero
  el cociente cambia entre Rest y ejercicio; sigue desconocido.
- El canal 18 se aproxima a `Vt * FEO2`: en evaluación obtiene R² entre 0,991 y
  0,996, pero el factor varía entre 1,06 y 1,10. No se valida su identidad.
- El antiguo alias `ventilation_l_min` del canal 15 queda rechazado. Frente a VE
  derivada obtiene R² entre -0,108 y 0,442 y MdAPE de 20-35 %. En cambio se
  asocia con `Vt * FECO2` (R² 0,966-0,991), también con factor dependiente de la
  fase. Se renombra de forma conservadora a `channel_15` y queda desconocido.
- Los canales 16, 17, 19 y 20 mantienen identidades de fracciones gaseosas
  provisionales. Plausibilidad y correlación no bastan para validarlos.

### Clasificación actual

- Exacto: estructura binaria, escalado `raw/scale`, eje temporal y marcadores.
- Derivado y validado: RR; conversiones de unidades y cocientes algebraicos.
- Derivado con condición no confirmada: Vt ATPS y VE ATPS.
- Calibrado: Vt/VE BTPS y los candidatos de VO₂/VCO₂ de las tablas.
- No reproducible de forma general: VO₂/VCO₂ exactos, trabajo y HR de Rest/AT
  cuando no existe una medición manual próxima.
- Reproducible en VO₂ Max: HR manual más cercana, con R² 0,993, MAE 0,2 bpm y
  MdAPE 0 % en las 85 pruebas de evaluación.

El código conserva siempre `channel_id`, escala, descriptor y valores enteros
originales. Así, un alias provisional puede corregirse sin perder trazabilidad.

## ManuallyEnteredData

La estructura se consumió exactamente en los binarios de las 427 pruebas de
validación:

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
El código 3068 aparece al menos una vez en cada prueba emparejada. La medición
más cercana reproduce VO₂ Max casi exactamente. Para AT solo hay una medición
en los 30 segundos previos en una minoría de pruebas, y Rest contiene eventos
alejados; por ello no se extrapola una regla exacta a esos momentos.

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
  Expone `respiratory_rate_br_min`, `tidal_volume_atps_l` y
  `minute_ventilation_atps_l_min` con condiciones y unidades explícitas.
- `tests/unit/test_transform_ergoespirometry.py`: cubre longitud, escalas,
  tabla longitudinal, fechas OLE, fórmulas, unidades, valores no físicos y
  códigos desconocidos.
- `scripts/analyze_ergoespirometry_windows.py`: genera características para
  muestra cercana y ventanas pre, centradas y post, además de métricas directas
  y relaciones entre señales.
- `scripts/analyze_ergoespirometry_calibration.py`: ajusta modelos
  proporcionales y afines en entrenamiento, evalúa aparte y guarda residuos y
  estabilidad por cuartiles de magnitud.

Comandos reproducibles:

```bash
python -m scripts.validate_ergoespirometry
python -m scripts.analyze_ergoespirometry_windows
python -m scripts.analyze_ergoespirometry_calibration
pytest tests/unit/test_transform_ergoespirometry.py -q
pytest tests/unit/test_analyze_ergoespirometry.py -q
pytest -q
```

Los artefactos detallados se escriben en `data/validation/` y permanecen fuera
de Git: características, métricas directas, relaciones entre señales,
calibraciones, mejores candidatos, residuos de evaluación y estabilidad por
magnitud.

Los archivos clínicos usados para la validación no se versionan.
