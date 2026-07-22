# Variables requeridas para ergoespirometría

## Alcance y criterio

Este inventario define los insumos y resultados que deben estar localizados
antes de ampliar la extracción GX. No propone cambios de SQL ni convierte una
coincidencia nominal o estadística en una correspondencia demostrada.

La prioridad inmediata sigue siendo reproducir los resúmenes de `GX Rest`,
`GX AT` y `GX VO2 Max`. Los nombres de Patient Query se escriben como aparecen
en el catálogo o en la exportación de referencia. La notación
`GX {Rest|AT|VO2 Max}` significa que existe una columna homóloga para cada uno
de esos tres momentos.

### Nivel de necesidad

| Código | Significado |
|---|---|
| **I** | Indispensable para calcular uno de los resultados prioritarios o situarlo en su instante correcto. |
| **N** | Necesaria para interpretar clínicamente el resultado o normalizarlo. |
| **Q** | Útil para control de calidad, auditoría o trazabilidad. |
| **O** | Opcional para el alcance inmediato; amplía la interpretación o permite índices secundarios. |

### Tratamiento operativo

| Tratamiento | Uso operativo |
|---|---|
| `extraer` | Leer un campo físico escalar o conservar un binario sin interpretarlo. |
| `decodificar` | Interpretar una estructura o señal contenida en un binario ya extraído. |
| `derivar` | Calcular una variable a partir de insumos extraídos o decodificados. |
| `enlazar` | Resolver una relación entre tablas, configuraciones o componentes analíticos. |
| `investigar` | Localizar o demostrar origen, semántica, unidad o fórmula antes de incorporarla. |
| `no incorporar por ahora` | Mantener documentada la variable fuera de la siguiente ampliación. |

### Fase operativa

| Fase | Alcance |
|---|---|
| `núcleo inicial` | Señales, marcadores, insumos y trazabilidad necesarios para los resultados GX prioritarios. |
| `ampliación clínica` | Variables interpretativas que no bloquean la reproducción inicial. |
| `investigación` | Identidades, fórmulas, condiciones o fuentes todavía no demostradas. |

### Estado de la correspondencia

| Estado | Uso en este documento |
|---|---|
| `confirmado` | Estructura, campo físico o marcador demostrado directamente. No implica por sí solo reproducción de Patient Query. |
| `validado` | Identidad de señal o fórmula contrastada además contra datos de referencia. |
| `provisional` | Candidato fisiológica o nominalmente plausible pendiente de validación independiente o de condición/unidad. |
| `desconocido` | El dato físico existe, pero su identidad analítica no está establecida. |
| `no localizado` | No se ha encontrado un origen físico para la variable en las fuentes revisadas. |

Un campo puede estar físicamente confirmado y conservar estado `provisional`
si su correspondencia con la columna de Patient Query, su unidad o su regla de
selección no están validadas.

### Evidencias revisadas

| Código | Evidencia |
|---|---|
| E1 | Inventario validado `docs/db_model/raw_inventory/breeze_raw_columns_inventory.tsv`. No contiene las tablas `GXTest` ni `GXPredicted`. |
| E2 | Catálogo de 8.309 variables `data/catalogs/patient_query_catalog.csv` y mapeo `patient_query_mapping.csv`. El mapeo GX permanece pendiente. |
| E3 | Cabecera de 210 columnas de `GX INO Resultados2.xls` y reglas de emparejamiento de `scripts/validate_ergoespirometry.py`. |
| E4 | `docs/esquema_analitico_ergoespirometria.md`: estructura GX, conteos, marcadores, señales y evaluación independiente. |
| E5 | Decodificador, fórmulas y pruebas sintéticas de `src/transform/ergoespirometry.py` y `tests/unit/test_transform_ergoespirometry.py`. |
| E6 | Análisis de ventanas y calibración de `scripts/analyze_ergoespirometry_windows.py` y `scripts/analyze_ergoespirometry_calibration.py`. |
| E7 | Campos realmente consultados por `sql/extract_ergoespirometry.sql`; la consulta fue la fuente de las validaciones GX documentadas. |
| E8 | Esquema FVL, inventario físico y mapeo nominal de Patient Query para la función pulmonar previa. |
| E9 | Enlaces GX de configuración y hardware confirmados para esta especificación operativa. Su contenido funcional sigue sin documentar. |

La exportación de 210 columnas confirma que Patient Query publica los nombres
indicados, pero no demuestra su procedencia física ni la fórmula interna.

## Matriz de variables

### Demográficas y antropométricas

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | extraer | núcleo inicial | Edad en la visita | Interpretación clínica y valores predichos | años | `Age` | `dbo.PatVisit.Age` | almacenada | Directa en la visita; no recalcular desde fecha de nacimiento salvo control | provisional | E1, E2, E3, E7 | Validar igualdad y tratamiento de decimales contra Patient Query. |
| N | extraer | núcleo inicial | Sexo | Interpretación y ecuaciones de referencia | categoría codificada | `Sex` | `dbo.Patient.SexListID` | almacenada | Resolver el catálogo del código sin inferirlo por frecuencia | provisional | E1, E2, E3, E7 | Localizar y validar la tabla de códigos usada por Patient Query. |
| N | extraer | núcleo inicial | Raza/grupo de referencia | Interpretación de predichos heredados | categoría codificada | `Race` | `dbo.Patient.RaceListID` | almacenada | Resolver el catálogo y registrar si la ecuación aplica corrección | provisional | E1, E2, E3, E7 | Validar catálogo y uso efectivo en el conjunto GX predicho. |
| I | extraer | núcleo inicial | Peso | VO2 relativo, METS y normalización | kg esperado; unidad SQL no documentada | `Weight` | `dbo.PatVisit.Weight` | almacenada | `VO2_rel = VO2_mL_min / weight_kg` | provisional | E1, E2, E3, E7 | Confirmar unidad y correspondencia; rechazar peso nulo o no físico. |
| N | extraer | núcleo inicial | Talla | Predichos, BSA e interpretación | cm esperado; unidad SQL no documentada | `Height` | `dbo.PatVisit.Height` | almacenada | Directa; la fórmula de BSA no debe asumirse | provisional | E1, E2, E3, E7 | Confirmar unidad y correspondencia. |
| N | extraer | ampliación clínica | IMC | Interpretación antropométrica | kg/m² | `BMI` | `dbo.PatVisit.BMI` | almacenada | Control posible: `weight_kg / height_m²` | provisional | E1, E2, E3, E7 | Comparar valor almacenado con el publicado y con el recálculo. |
| N | extraer | núcleo inicial | Superficie corporal (BSA) | Índices por m² y predichos | m² | `BSA` | `dbo.PatVisit.BSA` | almacenada | Directa; fórmula interna no confirmada | provisional | E1, E2, E3 | Incorporar el campo al futuro extractor y validar contra Patient Query. |
| O | no incorporar por ahora | ampliación clínica | Envergadura | Alternativa antropométrica a talla | cm esperado | `ArmSpan` | `dbo.PatVisit.ArmSpan` | almacenada | Directa | provisional | E1, E2, E3 | Confirmar unidad y uso en predichos GX. |
| O | no incorporar por ahora | ampliación clínica | Peso corporal ideal | VO2 por peso ideal | kg esperado | `Ideal Body Weight`; no está en las 210 columnas seleccionadas | `dbo.PatVisit.IdealBodyWeight`; también `dbo.GXPredicted.IdealBodyWeight` en E7 | almacenada | No asumir equivalencia entre ambas fuentes | provisional | E1, E2, E7 | Determinar cuál usa Patient Query y validar su unidad. |
| O | no incorporar por ahora | ampliación clínica | Masa magra | VO2 por masa magra | kg esperado | `Lean Body Mass`; no está en las 210 columnas seleccionadas | `dbo.PatVisit.LeanBodyMass` | almacenada | Directa | provisional | E1, E2 | Confirmar unidad y si interviene en algún predicho GX. |

### Ambientales

Estos datos son indispensables para demostrar una conversión exacta entre
ATPS, BTPS y STPD, pero el alcance actual no autoriza incorporarlos todavía a
una fórmula productiva. El inventario físico no documenta sus unidades y la
exportación de 210 columnas no los incluye.

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I | no incorporar por ahora | investigación | Temperatura ambiente | Corrección ATPS↔BTPS/STPD | °C requerido; unidad almacenada desconocida | `Temp`; fuera de la exportación de 210 columnas | `dbo.PatVisit.Temperature` | almacenada | Entraría en el factor de corrección, todavía no definido | provisional | E1, E2 | Verificar unidad, validez temporal y si los ceros son ausencia. |
| I | no incorporar por ahora | investigación | Presión barométrica | Corrección ATPS↔BTPS/STPD y presiones parciales | unidad requerida por fórmula; unidad almacenada desconocida | `BarPress`; fuera de la exportación de 210 columnas | `dbo.PatVisit.BarPress` | almacenada | Entraría en las correcciones y en `PETO2`/`PETCO2`; fórmula pendiente | provisional | E1, E2 | Verificar unidad, rango y uso real de Breeze. |
| I | no incorporar por ahora | investigación | Humedad relativa / presión de vapor | Corrección de gas húmedo/seco | % HR o presión de vapor; semántica por confirmar | `Humidity`; fuera de la exportación de 210 columnas | `dbo.PatVisit.Humidity` | almacenada | Conversión a presión de vapor no definida | provisional | E1, E2 | Confirmar unidad y si GX usa humedad medida o saturación asumida. |
| Q | no incorporar por ahora | investigación | Estado de cartucho seco GX | Calidad y condición húmeda/seca | booleano | No localizado en Patient Query | `dbo.Workstation.GXDryCartridge` | almacenada | No aplica | provisional | E1 | Confirmar el enlace de la estación usada en la prueba y su efecto. |

### Protocolo y carga

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | extraer | núcleo inicial | Modalidad bicicleta/cinta | Interpretación y selección del predicho | categoría | No hay columna directa en las 210 seleccionadas | `dbo.PatVisit.BikeTest`, `dbo.PatVisit.TreadmillTest` | almacenada | Validar exclusividad y coherencia con protocolo | confirmado | E1, E7 | Incorporar ambos indicadores y contrastarlos con el nombre de protocolo. |
| N | extraer | núcleo inicial | Nombre del protocolo de ejercicio | Interpretación de etapas y carga | texto | `PFProtocol` es demográfico en el catálogo, pero no demuestra equivalencia GX | `dbo.GXTest.GXTestExProtocolName` | almacenada | Directa | confirmado | E4, E7 | Catalogar valores observados sin datos personales y comparar con modalidad. |
| Q | extraer | núcleo inicial | Nombre y tipo de script GX | Reproducibilidad técnica | texto / código | No localizado | `dbo.GXTest.GXTestScriptName`, `GXTestScriptType` | almacenada | Directa | confirmado | E7 | Documentar catálogo de tipos y versiones de script. |
| N | decodificar | núcleo inicial | Trabajo observado en AT, VO2 Max y Rest | Interpretación de la respuesta a la carga | W | `GX {Rest\|AT\|VO2 Max} Work (Watts)` | `dbo.GXTest.GXTestRawData`, canal 24 | señal binaria | `raw_value / 10` | validado | E2, E3, E4, E5, E6 | Conservar la regla temporal por fase separada del decodificador. No usar `GXPredicted.BikeWatts` como observado. |
| N | enlazar | ampliación clínica | Trabajo predicho | Comparación con carga alcanzada | W | `GX Predicted Work (Watts)` | Candidatos `dbo.GXPredicted.BikeWatts`, `TreadmillWatts` | almacenada | Selección condicionada por modalidad, aún no validada | provisional | E3, E7 | Validar selección bicicleta/cinta contra Patient Query. |
| O | no incorporar por ahora | investigación | Velocidad de cinta | Interpretación de protocolo | km/h o mph, por confirmar | `Speed (MPH)` en el catálogo; no en las 210 columnas | — | señal binaria por localizar | Conversión de unidad si procede | no localizado | E2 | Localizar serie o eventos de equipo. |
| O | no incorporar por ahora | investigación | Pendiente de cinta | Interpretación y cálculo de trabajo | % | `Grade (%)` en el catálogo; no en las 210 columnas | — | señal binaria por localizar | No definida | no localizado | E2 | Localizar serie o eventos de equipo. |
| N | decodificar | núcleo inicial | Cadencia de bicicleta | Calidad de carga | rpm | `GX {Rest\|AT\|VO2 Max} Speed (RPM)` | `dbo.GXTest.GXTestRawData`, canal 25 | señal binaria | `raw_value / 10` | validado | E2, E4, E5, E6 | Mantener cero real como cero. La selección de Rest sigue sin una regla temporal definitiva. |
| Q | extraer | núcleo inicial | Inicio y fin absolutos de la prueba | Duración y alineación de eventos manuales | fecha-hora | No localizado como resultado PQ | `dbo.GXTest.GXTestStartTime`, `GXTestEndTime` | marcador | `duration_s = end - start` | confirmado | E4, E7 | Verificar zona/precisión y controlar fin anterior a inicio. |

### Ventilatorias

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I | decodificar | núcleo inicial | Duración respiratoria total (`Ttot`) | Calcular RR y VE | s | `Ttot (sec)` en catálogo; no en las 210 seleccionadas | `dbo.GXTest.GXTestRawData`, canal 11 | señal binaria | `raw_value / 1000` | validado | E4, E5, E6 | Mantener controles `Ttot > 0` y estabilidad por fase. |
| I | derivar | núcleo inicial | Frecuencia respiratoria (RR) | Resultado prioritario | respiraciones/min | `GX {Rest\|AT\|VO2 Max} RR (br/min)` | Derivada del canal 11 | derivada | `RR = 60 / breath_duration_s` | validado | E3, E4, E5, E6 | Conservar reglas temporales específicas por fase; no imponer ventana universal. |
| I | decodificar | núcleo inicial | Volumen corriente ATPS | Base para Vt y VE | mL o L, ATPS | `Vt ATPS` en catálogo; no en las 210 seleccionadas | `dbo.GXTest.GXTestRawData`, canal 12 | señal binaria | `raw_value / 1000` produce mL; `L = mL / 1000` | validado | E4, E5, E6 | Mantener explícita la condición ATPS. |
| I | derivar | núcleo inicial | Volumen corriente BTPS | Resultado prioritario | L, BTPS | `GX {Rest\|AT\|VO2 Max} Vt BTPS (L)` | —; candidato derivado del canal 12 | derivada | `Vt_BTPS = Vt_ATPS × factor_ATPS_BTPS`, factor no confirmado | provisional | E3, E4, E6 | Demostrar el factor físico; la calibración proporcional no equivale a corrección ambiental. |
| I | derivar | núcleo inicial | Ventilación minuto ATPS | Base para intercambio gaseoso | L/min, ATPS | `VE ATPS (L/min)` en catálogo; no en las 210 seleccionadas | Derivada de canales 11 y 12 | derivada | `VE_ATPS = tidal_volume_atps_ml × 60 / Ttot_s / 1000` | validado | E4, E5, E6 | Mantener validación dimensional y denominadores positivos. |
| I | derivar | núcleo inicial | Ventilación minuto BTPS | Resultado prioritario e interpretación | L/min, BTPS | `GX {Rest\|AT\|VO2 Max} VE BTPS (L/min)` | —; candidata derivada de canales 11 y 12 | derivada | `VE_BTPS = VE_ATPS × factor_ATPS_BTPS`, factor no confirmado | provisional | E3, E4, E6 | Demostrar corrección física y reglas temporales por fase. |
| N | investigar | investigación | Reserva ventilatoria | Limitación ventilatoria | L/min y % | `BR (L/Min)`, `BR (%)`; no están en las 210 seleccionadas | — | derivada | Fórmula exacta de Patient Query no confirmada; depende de MVV y VE | no localizado | E2 | Determinar si usa `MVV - VE`, predicho alternativo u otra definición. |
| N | derivar | ampliación clínica | VE/MVV | Limitación ventilatoria | % | `GX AT VE/MVV (%)`, `GX VO2 Max VE/MVV (%)` | Derivable cuando MVV quede seleccionada | derivada | `100 × VE_BTPS / MVV` como hipótesis | provisional | E3, E4 | Confirmar condición de VE, selección de MVV y redondeo. |
| O | no incorporar por ahora | ampliación clínica | Vt/IC | Hiperinsuflación dinámica / patrón ventilatorio | % | `GX AT Vt/IC (%)`, `GX VO2 Max Vt/IC (%)` | Derivable cuando IC quede seleccionada | derivada | `100 × Vt_BTPS / IC` | provisional | E3, E4 | Confirmar momento y fuente de IC. |
| I | decodificar | núcleo inicial | Tiempo inspiratorio (`Ti`) | Patrón ventilatorio | s | `GX {Rest\|AT\|VO2 Max} Ti (sec)` | `dbo.GXTest.GXTestRawData`, canal 10 | señal binaria | `raw_value / 1000` | validado | E2, E4, E5, E6 | `Te` y `Ti/Ttot` pueden derivarse, pero requieren validación independiente de la regla de resumen. |
| I | decodificar | núcleo inicial | Volumen bruto espirado de O2 por respiración | Derivar fracción mezclada e intercambio gaseoso | mL O2/resp | No equivale a `VO2 (mL/br)` | `dbo.GXTest.GXTestRawData`, canal 18 | señal binaria | `raw_value / 1000` | validado | E4, E5, E6 | No denominar consumo o captación neta de O2. La condición volumétrica exacta sigue abierta. |
| I | decodificar | núcleo inicial | Volumen bruto espirado de CO2 por respiración | Derivar fracción mezclada e intercambio gaseoso | mL CO2/resp | No equivale a `VCO2 (mL/br)` | `dbo.GXTest.GXTestRawData`, canal 15 | señal binaria | `raw_value / 1000` | validado | E4, E5, E6 | No denominar producción neta de CO2. La condición volumétrica exacta sigue abierta. |
| Q | decodificar | núcleo inicial | Doce descriptores físicos | Trazabilidad de orden, tipo y escala | bytes | No publicado | `dbo.GXTest.GXTestRawData`, doce bloques columnares | señal binaria | Dos bloques de 16 bits y diez `int32`; `value = raw_value / scale` | confirmado | E4, E5 | Conservar completos los seis bytes de cada descriptor. |

### Intercambio gaseoso

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I | decodificar | núcleo inicial | FIO2 | Entrada de Haldane | fracción; seco/húmedo no confirmado | `FIO2` y `FIO2 (dry)` | `dbo.GXTest.GXTestRawData`, canal 20 | señal binaria | `raw_value / 10000` | validado | E2, E4, E5, E6 | Mantener abierta únicamente la condición seco/húmedo. |
| I | decodificar | núcleo inicial | FETO2 end-tidal | Patrón del gas al final de la espiración | fracción | `FETO2 (%)` | `dbo.GXTest.GXTestRawData`, canal 19 | señal binaria | `raw_value / 10000` | validado | E2, E4, E5, E6 | No usar como `FEO2-Mix` en Haldane. |
| I | decodificar | núcleo inicial | FICO2 | Entrada de Haldane | fracción; seco/húmedo no confirmado | `FICO2` y `FICO2 (dry)` | `dbo.GXTest.GXTestRawData`, canal 17 | señal binaria | `raw_value / 10000` | validado | E2, E4, E5, E6 | Mantener controles de valores instrumentales anómalos. |
| I | decodificar | núcleo inicial | FETCO2 end-tidal | Patrón del gas al final de la espiración | fracción | `FETCO2 (%)` | `dbo.GXTest.GXTestRawData`, canal 16 | señal binaria | `raw_value / 10000` | validado | E2, E4, E5, E6 | No usar como `FECO2-Mix` en Haldane. |
| I | derivar | núcleo inicial | FEO2-Mix y FECO2-Mix | Balance de Haldane | fracción | `FEO2-Mix`, `FECO2-Mix` | Derivadas de canales 18/15 y canal 12 | derivada | `FEO2_mix = gross_O2 / Vt`; `FECO2_mix = gross_CO2 / Vt` | validado dimensionalmente | E4, E5, E6 | La regla temporal de Patient Query y la condición volumétrica continúan abiertas. |
| I | derivar | núcleo inicial | Fracciones inertes inspirada y espirada | Balance de Haldane | fracción | No publicadas | Derivadas de fracciones inspiradas y mezcladas | derivada | `FIN2 = 1 - FIO2 - FICO2`; `FEN2 = 1 - FEO2_mix - FECO2_mix` | provisional | E4, E5, E6 | Exigir fracciones físicas y confirmar que el gas inerte puede tratarse así. |
| I | derivar | núcleo inicial | Ventilación inspirada (`VI`) | Balance de Haldane | L/min; condición heredada de VE | No publicada | Derivada | derivada | `VI = VE × FEN2 / FIN2` | provisional | E4, E5, E6 | Confirmar condición de VE y fracciones antes de uso productivo. |
| I | derivar | núcleo inicial | Consumo de oxígeno (`VO2`) | Resultado prioritario | mL/min; condición PQ no declarada, STPD por confirmar | `GX {Rest\|AT\|VO2 Max} VO2 (mL/min)` | Candidato desde canales 11, 12, 18, 20, 15 y 17 | derivada | `(VI × FIO2 - VE × FEO2_mix) × 1000` | provisional | E3, E4, E5, E6 | Resolver condición del gas y factor dependiente de fase; no incorporar una aproximación silenciosa. |
| N | derivar | ampliación clínica | VO2 relativo | Interpretación de capacidad aeróbica | mL/kg/min; condición heredada de VO2 | `GX {Rest\|AT\|VO2 Max} VO2 (mL/kg/min)` | Derivable con `PatVisit.Weight` | derivada | `VO2_mL_min / weight_kg` | provisional | E1, E3, E4 | Validar peso, redondeo y tratamiento de valores ausentes. |
| I | derivar | núcleo inicial | Producción de CO2 (`VCO2`) | Resultado prioritario | mL/min; condición PQ no declarada, STPD por confirmar | `GX {Rest\|AT\|VO2 Max} VCO2 (mL/min)` | Candidato desde canales 11, 12, 18, 20, 15 y 17 | derivada | `(VE × FECO2_mix - VI × FICO2) × 1000` | provisional | E3, E4, E5, E6 | Resolver condición del gas y calibración dependiente de fase. |
| N | derivar | núcleo inicial | RER / RQ | Intensidad y calidad del esfuerzo | razón adimensional | `GX {Rest\|AT\|VO2 Max} RQ`; también `GX AT RER` y `GX VO2 Max RER` | Derivable de VO2 y VCO2 | derivada | `VCO2 / VO2` | provisional | E3, E4, E5, E6 | Determinar si `RQ` y `RER` son equivalentes en Patient Query y validar sin depender de una calibración común. |
| N | derivar | ampliación clínica | Equivalente ventilatorio de O2 | Eficiencia ventilatoria | razón adimensional | `GX {Rest\|AT\|VO2 Max} VE/VO2` | Derivable de VE y VO2 | derivada | `VE_L_min × 1000 / VO2_mL_min` | provisional | E3, E4, E5 | Hereda la incertidumbre de VE/VO2; confirmar condiciones y ventana. |
| N | derivar | ampliación clínica | Equivalente ventilatorio de CO2 | Eficiencia ventilatoria | razón adimensional | `GX {Rest\|AT\|VO2 Max} VE/VCO2` | Derivable de VE y VCO2 | derivada | `VE_L_min × 1000 / VCO2_mL_min` | provisional | E3, E4, E5 | Hereda la incertidumbre de VE/VCO2; confirmar condiciones y ventana. |
| N | investigar | investigación | PETCO2 y PETO2 | Interpretación ventilatoria | mmHg | `GX {Rest\|AT\|VO2 Max} PETCO2 (mmHg)`, `PETO2 (mmHg)` | — | señal binaria o derivada por localizar | Requiere fracción end-tidal y presión efectiva; no usar fracción mezclada sin prueba | no localizado | E2, E3, E4 | Localizar señales end-tidal y fórmula de presión parcial. |
| O | no incorporar por ahora | investigación | Espacio muerto `Vd/Vt` estimado y medido | Ineficiencia ventilatoria | razón | `GX {Rest\|AT\|VO2 Max} Vd/Vt - est`, `Vd/Vt - meas` | — | derivada por localizar | Bohr/Enghoff u otra variante no confirmada | no localizado | E3 | Identificar PaCO2/PECO2 y la fórmula exacta de Patient Query. |
| O | no incorporar por ahora | investigación | Pendiente VO2/trabajo | Respuesta metabólica a carga | mL/min/W | `GX {Rest\|AT\|VO2 Max} VO2WorkSlope (mL/min/watt)`; `VO2/Work Slope` en GX Other | — | derivada | Regresión/intervalo no confirmado | no localizado | E2, E3 | Requiere primero trabajo observado y definición de la ventana de ajuste. |
| N | enlazar | núcleo inicial | VO2 predicho | Porcentaje alcanzado e interpretación | mL/min y mL/kg/min | `GX Predicted VO2 (mL/min)`, `GX Predicted VO2 (mL/kg/min)` | Candidatos `dbo.GXPredicted.VO2Bike_mLmin`, `VO2Treadmill_mLmin`, `VO2Bike_kg`, `VO2Treadmill_kg` | almacenada | Selección por modalidad, no validada | provisional | E3, E4, E7 | Validar selección y correspondencia antes de calcular `% predicho`. |
| O | no incorporar por ahora | ampliación clínica | VCO2 y VE predichos | Comparación con respuesta esperada | mL/min o L/min; condición por confirmar | `GX Predicted VCO2 (mL/min)`, `GX Predicted VE BTPS (L/min)` | Candidatos `dbo.GXPredicted.VCO2Bike`, `VCO2Treadmill`, `VE_BTPS` | almacenada | Selección por modalidad cuando aplique | provisional | E3, E7 | Validar unidades y correspondencia con Patient Query. |
| O | no incorporar por ahora | ampliación clínica | Gasometría asociada | Interpretación avanzada | pH, mmHg, mEq/L, % | `pH`, `PaCO2_man`, `HCO3`, `PaO2_man`, `SaO2`, `P(A-a)O2`, `PECO2` por momento | Candidatos `dbo.BloodData.pH`, `PaCO2`, `HCO3`, `PaO2`, `SaO2`, `PAaO2`; no hay campo `PECO2` nominal | almacenada | Selección temporal/por `EffortTypeID` no establecida | provisional | E1, E2, E3 | Validar enlace temporal y equivalencias; localizar PECO2. |

### Cardiovasculares

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | decodificar | núcleo inicial | Frecuencia cardiaca observada | Intensidad, respuesta cronotrópica y pulso de O2 | bpm | `GX {Rest\|AT\|VO2 Max} HR (BPM)` | `dbo.GXTest.ManuallyEnteredData`, código 3068 | señal binaria | Valor directo; tiempo OLE alineado con `GXTestStartTime` | validado | E3, E4, E5, E6 | La reproducción es casi exacta en VO2 Max; definir cobertura/regla distinta para Rest y AT. |
| N | enlazar | ampliación clínica | Frecuencia cardiaca predicha | Interpretación cronotrópica | bpm | `GX Predicted HR (BPM)` | `dbo.GXPredicted.HR` | almacenada | Directa como candidata | provisional | E3, E7 | Validar contra Patient Query y documentar ecuación/autor. |
| N | investigar | investigación | Porcentaje de FC predicha y reserva | Respuesta cronotrópica | % y bpm | `HR/Pred`, `HRR`; no están en las 210 seleccionadas | Derivable si FC predicha y FC de reposo quedan validadas | derivada | Fórmula exacta de Patient Query no confirmada | no localizado | E2 | Determinar definiciones de HRR y FC basal usada. |
| N | derivar | ampliación clínica | Pulso de oxígeno | Respuesta cardiovascular indirecta | mL/latido; condición heredada de VO2 | `GX {Rest\|AT\|VO2 Max} VO2/HR (mL/beat)` | Derivable de VO2 y FC | derivada | `VO2_mL_min / HR_bpm` | provisional | E3, E4, E5 | Hereda incertidumbre de VO2 y cobertura temporal de FC. |
| O | no incorporar por ahora | ampliación clínica | Producto frecuencia-presión | Demanda miocárdica | `SBP × bpm / 100` | `RatePrsPd SBP*HR/100` en catálogo | Derivable de SBP y FC | derivada | `SBP_mmHg × HR_bpm / 100` | provisional | E2, E5 | Confirmar momento, factor de escala y tratamiento de medidas alejadas. |
| O | no incorporar por ahora | investigación | Índice cronotrópico | Respuesta cardiovascular avanzada | razón | `Chronotropic Index` en `GX Other` | — | derivada por localizar | Definición no confirmada | no localizado | E2 | Definir FC de reserva, edad y carga usadas por Patient Query. |
| O | no incorporar por ahora | investigación | Cambios ST/ECG | Seguridad e interpretación | µV / pendiente | `ST elev`, `ST slope` en catálogo; no en las 210 seleccionadas | — | señal binaria por localizar | No definida | no localizado | E2 | Localizar fuente ECG solo si se amplía el alcance clínico. |

### Oximetría y presión arterial

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | decodificar | ampliación clínica | SpO2 | Seguridad e interpretación del esfuerzo | % | `GX {Rest\|AT\|VO2 Max} SpO2 (%)` | `dbo.GXTest.ManuallyEnteredData`, código 3180 | señal binaria | Valor directo en el evento | confirmado | E3, E4, E5 | Validar la regla temporal y cobertura por fase contra Patient Query. |
| N | decodificar | ampliación clínica | Presión sistólica | Seguridad y respuesta hemodinámica | mmHg | `GX {Rest\|AT\|VO2 Max} sysBP (mmHg)` | `dbo.GXTest.ManuallyEnteredData`, código 3037 | señal binaria | `raw_kPa × 7.50062` | confirmado | E3, E4, E5 | Validar proximidad temporal, redondeo y cobertura por fase. |
| N | decodificar | ampliación clínica | Presión diastólica | Seguridad y respuesta hemodinámica | mmHg | `GX {Rest\|AT\|VO2 Max} diaBP (mmHg)` | `dbo.GXTest.ManuallyEnteredData`, código 3038 | señal binaria | `raw_kPa × 7.50062` | confirmado | E3, E4, E5 | Validar proximidad temporal, redondeo y cobertura por fase. |
| O | no incorporar por ahora | ampliación clínica | Presión de pulso | Interpretación hemodinámica | mmHg | `PulsePres (mmHg)` en catálogo; no en las 210 seleccionadas | Derivable de las dos presiones | derivada | `SBP - DBP` | confirmado | E2, E5 | Aplicar solo a medidas del mismo evento. |

### Síntomas

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | extraer | ampliación clínica | Disnea basal | Contexto clínico | categoría codificada | `Dyspnea` | `dbo.PatVisit.DyspneaID` | almacenada | Resolver catálogo de código | provisional | E1, E2, E3 | Validar catálogo y correspondencia de la visita. |
| O | no incorporar por ahora | ampliación clínica | Tos y sibilancias | Contexto clínico | categorías codificadas | `Cough`, `Wheez` | `dbo.PatVisit.CoughID`, `WheezeID` | almacenada | Resolver catálogos | provisional | E1, E2, E3 | Validar catálogos de códigos. |
| O | no incorporar por ahora | ampliación clínica | Exposición tabáquica | Contexto clínico | producto, años, paquetes/día, paquetes-año | `Tbco Prod`, `Yrs Smk`, `Pks/Day`, `Yrs Quit`, `Pk Yrs` | `dbo.PatVisit.TobaccoID`, `YearsSmoke`, `PackaDay`, `QuitYears`, `PackYears` | almacenada | Directa salvo categoría de producto | provisional | E1, E2, E3 | Confirmar unidades y catálogo de `TobaccoID`. |
| N | investigar | investigación | Borg de disnea durante ejercicio | Síntoma limitante | escala Borg configurada | `Borg Dyspnea` en catálogo; no en las 210 seleccionadas | Solo se confirma `dbo.GXTest.GXTestBorgScale` como configuración, no la lectura | señal binaria por localizar | No definida | no localizado | E2, E7 | Identificar códigos de `ManuallyEnteredData` o fuente específica; no confundir escala con valor. |
| N | investigar | investigación | Borg de fatiga de piernas / esfuerzo percibido | Síntoma limitante | escala Borg configurada | `Borg Leg Fatigue`, `Borg PE` en catálogo; no en las 210 seleccionadas | — | señal binaria por localizar | No definida | no localizado | E2 | Identificar códigos/eventos y su alineación temporal. |
| Q | no incorporar por ahora | ampliación clínica | Diagnóstico y comentarios previos | Contexto y auditoría clínica | texto | `Diagnosis`, `Pre Test Comments` | `dbo.PatVisit.Diagnosis`, `Comments` | almacenada | Directa | provisional | E1, E2, E3, E7 | Definir tratamiento de texto y privacidad antes de persistirlo. |

### Función pulmonar previa

Estas variables se inventarían para interpretar la ergoespirometría, no para
reconstruir ahora todo el bloque `PF`. La exportación incluye resultados
observados, predichos, porcentaje del predicho, LLN, ULN y SD.

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N | enlazar | ampliación clínica | FVC pre y predicha | Contexto ventilatorio | L, BTPS esperado | `PF Pre FVC (L)`, `PF Predicted FVC (L)` | `dbo.FVLData.FVC`, filas por `EffortTypeID` | almacenada | Selección representativa de Breeze; no máximo de maniobras | provisional | E1, E3, E8 | Validar específicamente las columnas del export GX; no duplicar la reconstrucción PF. |
| N | enlazar | ampliación clínica | FEV1 pre y predicho | Obstrucción y relaciones Vt/FEV1 | L, BTPS esperado | `PF Pre FEV1 (L)`, `PF Predicted FEV1 (L)` | `dbo.FVLData.FEV1`, filas por `EffortTypeID` | almacenada | Selección representativa de Breeze | provisional | E1, E3, E8 | Validar correspondencia en el mismo intervalo GX. |
| N | enlazar | ampliación clínica | FEV1/FVC pre y predicho | Patrón obstructivo | % | `PF Pre FEV1/FVC (%)`, `PF Predicted FEV1/FVC (%)` | `dbo.FVLData.FEV1FVC` | almacenada | Directa | provisional | E1, E3, E8 | Validar escala porcentaje frente a fracción. |
| O | no incorporar por ahora | ampliación clínica | PEF pre | Calidad/contexto espirométrico | L/min | `PF Pre PEF (L/min)` | `dbo.FVLData.PEF` | almacenada | Directa | provisional | E1, E3, E8 | Validar selección de fila representativa. |
| N | enlazar | ampliación clínica | MVV pre y predicha | Reserva ventilatoria y VE/MVV | L/min, BTPS esperado | `PF Pre MVV (L/min)`, `PF Predicted MVV (L/min)` | `dbo.MVVData.MVV` | almacenada | Selección por `EffortTypeID`/`EffortSelected` aún no validada para GX | provisional | E1, E3, E8 | Establecer selección y si Patient Query usa MVV medida o estimada. |
| N | enlazar | ampliación clínica | IC pre y predicha | Vt/IC e hiperinsuflación | L, BTPS esperado | `PF Pre IC (L)`, `PF Predicted IC (L)` | Candidatos `dbo.SVCData.ICSVC`, `AutoICSVC` | almacenada | Selección y candidato exacto no confirmados | provisional | E1, E3, E8 | Validar columna y fila contra Patient Query. |
| O | no incorporar por ahora | ampliación clínica | SVC pre y predicha | Contexto de volumen pulmonar | L, BTPS esperado | `PF Pre SVC (L)`, `PF Predicted SVC (L)` | Candidato `dbo.SVCData.VCSVC` | almacenada | Selección no confirmada | provisional | E1, E3, E8 | Validar columna y fila contra Patient Query. |
| Q | no incorporar por ahora | ampliación clínica | Calidad FVL | Calidad de función pulmonar previa | grado ATS | `PF Pre TestGrade(ATS)` | `dbo.FVLData.TestGradeATS` | almacenada | Directa en fila representativa | provisional | E1, E3, E8 | Validar selección y catálogo de grados. |
| Q | no incorporar por ahora | ampliación clínica | Retroextrapolación y tiempo espiratorio | Calidad FVL | L y s | `PF Pre Back Extrap Vol (L)`, `PF Pre Expiratory Time (sec)` | `dbo.FVLData.VolExtrap`, `ExpTime` | almacenada | Directa en fila representativa | provisional | E1, E3, E8 | Validar selección; son control de calidad, no insumos del cálculo GX prioritario. |

### Marcadores temporales

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| I | decodificar | núcleo inicial | Eje temporal respiración a respiración | Alinear señales y ventanas | s desde inicio de prueba | No publicado por observación | `dbo.GXTest.GXTestRawData`, canal 1 | señal binaria | `raw_value / 1000` | confirmado | E4, E5 | Mantener monotonicidad y cobertura de marcadores como controles. |
| I | extraer | núcleo inicial | Marcador de reposo | Resumen Rest | s desde inicio de prueba | `GX Rest Time (min)` | `dbo.GXTest.StartExerciseTime` | marcador | El marcador exacto es `StartExerciseTime`; PQ redondea a minutos | confirmado | E3, E4, E6, E7 | No usar el minuto PQ como instante exacto; conservar diferencia de redondeo. |
| I | extraer | núcleo inicial | Marcador de umbral anaeróbico | Resumen AT | s desde inicio de prueba | `GX AT Time (min)` | `dbo.GXTest.ATElapsedTime` | marcador | Tiempo relativo a ejercicio: `(AT - StartExerciseTime) / 60` | confirmado | E3, E4, E6, E7 | Validar presencia/rango y conservar la ventana específica de cada variable. |
| I | extraer | núcleo inicial | Marcador de VO2 máximo | Resumen VO2 Max | s desde inicio de prueba | `GX VO2 Max Time (min)` | `dbo.GXTest.VO2MaxElapsedTime` | marcador | Tiempo relativo: `(VO2Max - StartExerciseTime) / 60` | confirmado | E3, E4, E6, E7 | Validar presencia/rango y que esté dentro de la serie. |
| N | extraer | núcleo inicial | Inicio de recuperación | Delimitar ejercicio y recuperación | s desde inicio de prueba | No hay columna directa en las 210 seleccionadas | `dbo.GXTest.StartRecoveryTime` | marcador | Directa | confirmado | E4, E7 | Comprobar orden respecto de inicio de ejercicio y fin de prueba. |
| O | no incorporar por ahora | ampliación clínica | Marcador de compensación respiratoria | Interpretación avanzada | s desde inicio de prueba | `GX RC Time` sería posible por catálogo, pero no está en las 210 seleccionadas | `dbo.GXTest.RCElapsedTime` | marcador | Tiempo relativo: `(RC - StartExerciseTime) / 60` | confirmado | E2, E4, E7 | Validar significado clínico y cobertura antes de publicar. |
| N | investigar | investigación | Tiempo de ejercicio publicado | Interpretación de duración por momento | min | `GX {Rest\|AT\|VO2 Max} Ex Time (min)` | — | derivada por localizar | Relación con inicio de ejercicio no demostrada | no localizado | E3 | Comparar candidatos basados en marcadores sin asumir equivalencia. |
| Q | derivar | investigación | Regla de resumen temporal | Reproducción auditable | ventana s, posición, estadístico | Implícita; Patient Query solo publica el resumen | Metadato analítico, no campo SQL | derivada | Cercana, media o mediana; ventanas pre/centradas/post de 10–120 s | provisional | E4, E6 | Mantener reglas por variable y fase, seleccionadas solo en entrenamiento. |

### Calibración y trazabilidad

| Nivel | Tratamiento | Fase | Variable analítica requerida | Finalidad | Unidad / condición | Nombre en Patient Query | Tabla y columna física confirmada | Origen | Regla de cálculo | Estado | Evidencia disponible | Acción pendiente |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Q | extraer | núcleo inicial | Identificador de prueba GX | Trazabilidad técnica y partición | entero | No se exporta en las 210 columnas | `dbo.GXTest.GXTestID` | almacenada | Clave de prueba; evaluación si `GXTestID mod 5 = 0` | confirmado | E3, E4, E6, E7 | No exponer fuera del uso técnico necesario. |
| Q | enlazar | núcleo inicial | Identificador y fecha de visita | Enlace y emparejamiento | entero / fecha-hora | `Visit Date`; el identificador interno no se publica | `dbo.PatVisit.PatVisitID`, `VisitDateTime`, `PatVisitGUID` | almacenada | Emparejamiento validado: paciente normalizado + fecha-hora; rechazar ambigüedad | validado | E1, E3, E4, E7 | Mantener rechazo de claves duplicadas y separación de identificadores personales. |
| Q | extraer | núcleo inicial | Binario GX original | Auditoría y reprocesado | bytes | No publicado | `dbo.GXTest.GXTestRawData` | señal binaria | Preservar sin alteración | confirmado | E4, E5, E7 | Registrar disponibilidad y error estructural sin volcar datos clínicos. |
| Q | decodificar | núcleo inicial | Versión, longitud y número de observaciones | Integridad binaria | versión 10; bytes; N | No publicado | Cabecera de `GXTestRawData` | señal binaria | Cabecera de 24 bytes; `length = 326 + 44 × N`; 12 canales y 12 descriptores | confirmado | E4, E5 | Mantener validación estricta antes de decodificar. |
| Q | decodificar | núcleo inicial | Descriptor, ID, escala y entero original por señal | Auditabilidad de identidades | bytes / entero | No publicado | Descriptores y bloques de `GXTestRawData` | señal binaria | `value = raw_value / scale` | confirmado | E4, E5 | Conservar incluso cuando cambie un alias provisional. |
| Q | decodificar | núcleo inicial | Eventos manuales originales | Auditoría de FC, SpO2 y PA | fecha OLE, código, valor | No publicado | `dbo.GXTest.ManuallyEnteredData` | señal binaria | Estructura de eventos consumida exactamente; conservar códigos desconocidos | confirmado | E4, E5 | Inventariar códigos adicionales sin inferir significado por frecuencia. |
| Q | derivar | núcleo inicial | Disponibilidad/completitud de señal | Calidad | booleanos y conteos | No publicado | Derivada de ambos binarios y sus cabeceras | derivada | `GXTestRawData IS NOT NULL`, decodificación válida, cobertura temporal | confirmado | E4, E5 | Mantener indicadores por prueba y por marcador. |
| Q | enlazar | núcleo inicial | Fecha, estación, configuraciones y hardware GX | Calidad instrumental y trazabilidad de la configuración | fecha-hora / GUID / ID | `Calibration Date/Time` en catálogo; los enlaces GX no se publican | `dbo.PatVisit.CalibrationDateTime`, `CalibrationWorkstationGUID`; `GXTest.GXTestBxBConfigGUID → Config.ConfigGUID`; `GXTest.GXTestSummaryConfigGUID → Config.ConfigGUID`; `GXTest.HardwareID → Hardware.HardwareID` | almacenada | Extraer las claves y resolver los tres enlaces confirmados; no derivar parámetros de calibración | confirmado | E1, E2, E9 | Documentar el contenido y significado de `Config` y `Hardware` antes de interpretar sus campos. Confirmar aparte el destino de `CalibrationWorkstationGUID`. |
| Q | no incorporar por ahora | investigación | Espacio muerto externo | Corrección instrumental y calidad | volumen; unidad desconocida | No localizado | `dbo.GXTest.GXTestExternalDeadspace`; también configuración `dbo.Workstation.WorkstationExternalDeadSpace` | almacenada | Uso en fórmulas no confirmado | provisional | E1, E7 | Confirmar unidad, precedencia y corrección aplicada por Breeze. |
| Q | extraer | núcleo inicial | Frecuencia configurada de presión arterial | Calidad de muestreo | intervalo; unidad desconocida | No localizado | `dbo.GXTest.GXTestBPFreq` | almacenada | Directa como configuración | confirmado | E7 | Documentar unidad y contrastar con eventos observados. |
| N | extraer | núcleo inicial | Conjunto de predicción GX | Reproducibilidad de predichos | texto | `GX Predicted Set Name` | `dbo.PatVisit.GXPredSetName` | almacenada | Directa | provisional | E1, E2 | El extractor actual selecciona `PredSetName`; validar y usar el campo GX específico en un cambio posterior. |
| Q | enlazar | núcleo inicial | Identificador de fila predicha | Trazabilidad del enlace | entero | No publicado | `dbo.GXPredicted.GXPredictedID`, enlazado por `PatVisitID` | almacenada | Una fila predicha no prueba existencia de GX | confirmado | E4, E7 | Controlar la visita con dos pruebas que comparte predichos. |
| Q | derivar | investigación | Metadatos de calibración empírica | Auditoría de resultados aproximados | ventana, estadístico, pendiente, intercepto, muestra | No publicado | Artefactos analíticos fuera de SQL Server | derivada | Ajustar solo en entrenamiento; evaluar en `GXTestID mod 5 = 0` | confirmado | E4, E6 | Toda salida calibrada debe etiquetarse y conservar métricas por fase. |
| Q | no incorporar por ahora | ampliación clínica | Firma de la visita | Estado de revisión clínica | booleano / fecha-hora | `Signed`, `Signed Date` en catálogo; no en las 210 seleccionadas | `dbo.PatVisit.Signed`, `SignedDateTime` | almacenada | Directa | confirmado | E1, E2, E7 | Decidir si será criterio de calidad, nunca de existencia de GX sin validación. |

## Orígenes físicos confirmados

Ya existe un origen físico demostrado para los siguientes grupos:

- visita y antropometría: edad, peso, talla, BSA, IMC, envergadura, masa
  magra, peso ideal, fecha y claves de visita; sexo y raza están almacenados
  como códigos en `Patient`;
- ambiente de visita: temperatura, presión barométrica y humedad, aunque sus
  unidades y uso GX siguen pendientes;
- cabecera GX: inicio/fin, protocolo, script, configuración Borg/PA, espacio
  muerto y los cinco marcadores temporales revisados;
- `GXTestRawData`: doce canales validados: trabajo, RPM, eje temporal, Ttot,
  Ti, volumen corriente, volúmenes brutos espirados de O2/CO2, FIO2, FICO2 y
  las concentraciones end-tidal FETO2/FETCO2;
- `ManuallyEnteredData`: presión sistólica, presión diastólica, frecuencia
  cardiaca y SpO2 con código y conversión conocidos;
- `GXPredicted`: filas y candidatos físicos de VE, FC, VO2, VCO2 y trabajo
  predichos; falta validar la selección por modalidad y la correspondencia con
  cada columna publicada;
- función pulmonar: FVC, FEV1, FEV1/FVC, PEF, MVV y candidatos de IC/SVC, más
  campos de calidad FVL;
- gasometría: candidatos físicos para pH, PaO2, PaCO2, HCO3, SaO2 y gradiente
  alveolo-arterial;
- calibración y auditoría: fecha/estación de calibración, firma, binarios,
  descriptores, escalas y claves técnicas.

## Variables aún sin localizar

No se ha demostrado un origen físico para:

- las series de velocidad y pendiente de cinta; trabajo en vatios y cadencia
  de bicicleta sí están localizados en ID24 e ID25;
- el factor físico exacto ATPS→BTPS y las conversiones necesarias para obtener
  VO2/VCO2 en la condición usada por Patient Query;
- PETCO2, PETO2, PECO2 y `Vd/Vt` estimado o medido;
- Te, reserva ventilatoria y la definición exacta de HRR; Ti está localizado
  en ID10;
- valores Borg de disnea, fatiga de piernas o esfuerzo percibido; el campo
  `GXTestBorgScale` solo confirma la escala configurada;
- cambios ECG/ST, índice cronotrópico y pendiente VO2/trabajo;
- la regla física de `GX * Ex Time (min)` y la semántica diferencial de `RQ`
  frente a `RER`;
- una fuente continua de FC, SpO2 o presión arterial: solo están confirmados
  eventos manuales discretos.

Los doce canales de `GXTestRawData` tienen identidad validada y conservan su
descriptor, tipo, escala y entero original. Las cuestiones abiertas de este
apartado se refieren a derivaciones o reglas temporales, no al mapeo físico.

## Campos físicos para la próxima ampliación del extractor

La próxima ampliación queda limitada a campos almacenados, binarios ya
conocidos y claves de enlace. No presupone el contenido funcional de las
tablas enlazadas.

### Añadir

- `PatVisit.BSA`.
- `PatVisit.BikeTest` y `PatVisit.TreadmillTest`.
- `PatVisit.GXPredSetName`.
- `PatVisit.CalibrationDateTime` y
  `PatVisit.CalibrationWorkstationGUID`.
- `GXTest.GXTestBxBConfigGUID` y la clave destino `Config.ConfigGUID`.
- `GXTest.GXTestSummaryConfigGUID` y la clave destino
  `Config.ConfigGUID`.
- `GXTest.HardwareID` y la clave destino `Hardware.HardwareID`.

### Conservar en la extracción

- claves técnicas: `GXTest.GXTestID`, `GXTest.PatVisitID` y
  `PatVisit.PatVisitID`;
- binarios: `GXTest.GXTestRawData` y `GXTest.ManuallyEnteredData`;
- tiempos y marcadores: `GXTestStartTime`, `GXTestEndTime`,
  `StartExerciseTime`, `StartRecoveryTime`, `ATElapsedTime`,
  y `VO2MaxElapsedTime`;
- protocolo y control: `GXTestExProtocolName`, `GXTestScriptName`,
  `GXTestScriptType` y `GXTestBPFreq`;
- campos demográficos ya extraídos que alimentan el núcleo: `Age`, `Weight`,
  `Height`, `BMI`, `SexListID` y `RaceListID`;
- predichos necesarios para el núcleo: `GXPredicted.GXPredictedID`,
  `GXPredicted.VO2Bike_mLmin`, `GXPredicted.VO2Treadmill_mLmin`,
  `GXPredicted.VO2Bike_kg` y `GXPredicted.VO2Treadmill_kg`, conservando el
  enlace por `GXPredicted.PatVisitID`.

### Fuera de esta lista

- **Derivadas:** RR, Vt/VE convertidos, VO2, VCO2, RER/RQ, VO2 relativo,
  equivalentes ventilatorios, pulso de oxígeno, reserva ventilatoria,
  cocientes y pendientes. Se calculan después de extraer o decodificar sus
  insumos; nunca se solicitan como columnas físicas.
- **Opcionales:** envergadura, peso ideal, masa magra, velocidad, pendiente,
  cadencia, Vt/IC, Vd/Vt, gasometría, índices cardiovasculares secundarios,
  función pulmonar opcional, RC y firma. Permanecen fuera de la próxima
  ampliación.
- **No localizadas:** trabajo observado, Ti/Te, PETCO2/PETO2/PECO2, Borg,
  ECG/ST, tiempo de ejercicio publicado y demás variables sin origen físico
  demostrado. Continúan en investigación.
- **Ambientales y configuración no interpretada:** temperatura, presión,
  humedad, cartucho seco, espacio muerto externo y contenido de `Config` o
  `Hardware`. No se incorporan por ahora ni se convierten en parámetros de
  calibración.
