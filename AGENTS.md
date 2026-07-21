# AGENTS.md

## Proyecto

Este repositorio implementa la extracción, transformación, validación y carga de pruebas de función pulmonar desde la base Breeze/MGCDBase hacia PostgreSQL.

El objetivo de ergoespirometría es reproducir de forma auditable los resultados exportados por Patient Query, usando como referencia el archivo:

`GX INO Resultados2(1).xls`

La prioridad actual son los resultados GX de:

- reposo (`GX Rest`);
- umbral anaeróbico (`GX AT`);
- consumo máximo (`GX VO2 Max`).

## Forma de trabajo

- Trabajar de manera autónoma hasta alcanzar una conclusión verificable.
- No detenerse después de presentar un plan: inspeccionar, ejecutar, analizar, implementar y probar.
- Agrupar inspecciones y comandos de solo lectura cuando sea eficiente.
- Evitar solicitar confirmación para acciones locales, reversibles y dentro del alcance.
- Pedir intervención únicamente ante una decisión clínica, una ambigüedad que cambie materialmente el resultado, falta de credenciales o una acción irreversible.
- Mantener actualizaciones breves y centradas en hallazgos, decisiones y bloqueos.
- Responder y documentar en español.
- Mantener identificadores de código en inglés.
- Usar exclusivamente comandos Linux/WSL.
- Ejecutar los scripts del directorio `scripts` como módulos:

```bash
python -m scripts.nombre_del_modulo
```

## Economía de contexto y prompts

- Leer este archivo antes de trabajar y no pedir nuevamente información que ya contiene.
- Inspeccionar primero el código, las pruebas, la documentación y los resultados existentes.
- Reutilizar scripts y artefactos de validación en lugar de repetir análisis manuales.
- No volcar archivos completos en la conversación salvo que sea imprescindible.
- Informar resultados agregados y ejemplos anonimizados.
- Registrar en la documentación los hallazgos que deban persistir entre sesiones.
- No repetir explicaciones ya asentadas en el repositorio.
- Preferir una ejecución amplia y bien instrumentada sobre múltiples iteraciones pequeñas sin evidencia nueva.

## Privacidad

- Los datos proceden de pruebas clínicas.
- No mostrar ni registrar nombres, documentos de identidad, fechas de nacimiento u otros identificadores personales.
- Usar `GXTestID` y `PatVisitID` únicamente cuando sean necesarios para trazabilidad técnica.
- No incorporar datos clínicos identificables al repositorio.
- Mantener fuera de Git los archivos de referencia y resultados intermedios que contengan datos de pacientes.

## Estado confirmado de GXTestRawData

Estructura binaria confirmada:

- versión: `10`;
- canales declarados: `12`;
- señales con descriptor: `10`;
- tamaño: `326 + 44 × N`;
- cada descriptor conserva el identificador, la escala y los bytes originales;
- cada valor decodificado se obtiene como `raw_value / scale`.

Catálogo actual:

| ID | Alias | Confianza |
|---:|---|---|
| 1 | `elapsed_time_s` | confirmed |
| 11 | `breath_duration_s` | validated |
| 10 | `channel_10` | unknown |
| 12 | `tidal_volume_atps_ml` | validated |
| 18 | `channel_18` | unknown |
| 20 | `fio2_fraction` | provisional |
| 19 | `feo2_fraction` | provisional |
| 15 | `ventilation_l_min` | provisional |
| 17 | `fico2_fraction` | provisional |
| 16 | `feco2_fraction` | provisional |

No renombrar los canales 10 o 18 ni elevar un canal provisional a validado basándose únicamente en correlación.

## Datos de referencia

Estado conocido de la validación:

- 428 pruebas emparejadas entre SQL Server y Patient Query;
- 427 pruebas con `GXTestRawData`;
- `GXTestID 3712` no tiene binario;
- la comparación debe usar exactamente el mismo intervalo temporal en ambas fuentes;
- la clave de emparejamiento normalizada es paciente más fecha y hora de visita;
- deben detectarse y rechazarse claves ambiguas.

El archivo Patient Query contiene 210 columnas y resultados de:

- `GX Rest`;
- `GX AT`;
- `GX VO2 Max`;
- `GX Predicted`;
- función pulmonar asociada.

El alcance actual se limita a ergoespirometría. No desarrollar ahora la reconstrucción de las columnas de función pulmonar `PF`.

## Criterio científico

Distinguir siempre entre:

1. estructura binaria confirmada;
2. identidad de señal validada;
3. hipótesis fisiológica;
4. asociación estadística;
5. calibración empírica;
6. reproducción del resultado Patient Query.

Una correlación alta no demuestra identidad. Puede reflejar que dos variables aumentan simultáneamente durante el ejercicio.

Para validar una fórmula o señal:

- justificar su coherencia fisiológica y dimensional;
- comprobar unidades y factores de escala;
- evaluarla en una muestra independiente;
- informar tamaño muestral;
- informar Pearson, R², MAE y error porcentual absoluto mediano;
- analizar por separado Rest, AT y VO2 Max;
- comprobar estabilidad entre pruebas y fases;
- revisar valores atípicos;
- comparar contra alternativas más simples;
- evitar calibraciones con interceptos grandes sin explicación física.

La partición actual es determinista:

```python
test_mask = gx_test_ids.mod(5).eq(0)
```

No evaluar como validación fuera de muestra los mismos datos usados para ajustar parámetros.

## Hipótesis ventilatorias en evaluación

La relación fisiológica básica que debe contrastarse es:

```text
RR = 60 / breath_duration_s

VE_ATPS (L/min) =
    tidal_volume_atps_ml
    × 60
    / breath_duration_s
    / 1000
```

La transformación de Haldane que debe evaluarse, sin asumirla confirmada, es:

```text
FIN2 = 1 - FIO2 - FICO2
FEN2 = 1 - FEO2 - FECO2

VI = VE × FEN2 / FIN2

VO2 = (VI × FIO2 - VE × FEO2) × 1000
VCO2 = (VE × FECO2 - VI × FICO2) × 1000
```

No buscar ni incorporar por ahora temperatura, humedad o presión barométrica. Si su ausencia impide una reproducción exacta, cuantificar la diferencia y dejarla documentada como limitación.

## Estrategia de reproducción

El objetivo inmediato es reproducir, con la mayor precisión justificable:

- `Vt BTPS`;
- `RR`;
- `VE BTPS`;
- `VO2`;
- `VCO2`;

para:

- `GX Rest`;
- `GX AT`;
- `GX VO2 Max`.

Si esos resultados quedan suficientemente explicados, avanzar sin esperar una nueva instrucción hacia variables derivables:

- `RQ` o `RER`;
- `VO2/HR`, si HR queda identificada;
- `VE/VO2`;
- `VE/VCO2`;
- tiempos de cada marcador;
- trabajo en vatios, si existe una fuente verificable;
- otras variables GX reproducibles sin recurrir a condiciones ambientales omitidas.

No implementar una aproximación silenciosa. Toda salida debe indicar si es:

- exacta;
- derivada mediante fórmula confirmada;
- calibrada;
- provisional;
- no reproducible con los datos disponibles.

## Ventanas temporales

Patient Query publica resúmenes, no necesariamente la observación más cercana al marcador.

Evaluar de manera sistemática:

- observación más cercana;
- media;
- mediana;
- ventanas anteriores de 10, 20, 30, 45, 60, 90 y 120 segundos.

No elegir una ventana únicamente porque maximiza una métrica global. Comprobar que sea estable y coherente con la definición del resumen.

Investigar especialmente por qué Rest puede comportarse de manera diferente a AT y VO2 Max.

## Código y pruebas

Antes de modificar:

```bash
git status -sb
git diff
```

Preservar todos los cambios existentes del usuario.

No eliminar archivos desconocidos sin inspeccionarlos.

Después de modificar:

```bash
python -m py_compile scripts/analyze_ergoespirometry_windows.py
python -m scripts.analyze_ergoespirometry_windows
python -m scripts.analyze_ergoespirometry_calibration
pytest tests/unit/test_transform_ergoespirometry.py -q
```

Ejecutar también la suite completa si el cambio afecta código compartido:

```bash
pytest -q
```

Requisitos:

- mantener funciones pequeñas y auditables;
- evitar números mágicos;
- nombrar unidades en columnas y variables;
- mantener separados análisis exploratorio y transformación productiva;
- añadir pruebas para toda fórmula incorporada a `src/transform`;
- conservar compatibilidad con los binarios ya validados;
- no añadir dependencias salvo necesidad demostrable;
- documentar comandos reproducibles.

## Git

- No hacer commit, push, merge ni abrir pull request salvo petición explícita.
- No descartar cambios existentes.
- No usar comandos destructivos.
- Al terminar, mostrar:
  - archivos modificados;
  - pruebas ejecutadas;
  - resultados cuantitativos;
  - hipótesis confirmadas, rechazadas y pendientes;
  - `git status -sb`.

## Condición de finalización

No considerar terminada una sesión solo porque un script se ejecuta.

Debe entregarse:

1. análisis reproducible;
2. resultados cuantificados fuera de muestra;
3. fórmulas y unidades explícitas;
4. código actualizado cuando la evidencia lo justifique;
5. pruebas automatizadas;
6. documentación técnica;
7. listado claro de limitaciones y próximos problemas investigables.