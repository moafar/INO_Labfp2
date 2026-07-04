# Validación contra informes Breeze

## Objetivo

Contrastar los valores producidos por el pipeline Breeze/SQL Server contra informes clínicos exportados desde Breeze, considerados gold standard del proceso.

## Informes utilizados

Se usaron 7 informes de muestra:

- CAPACIDAD DE DIFUSION 1.pdf
- CAPACIDAD DE DIFUSION 2.pdf
- CAPACIDAD DE DIFUSION 3.pdf
- VOLUMENES 1.pdf
- VOLUMENES 2.pdf
- VOLUMENES 3.pdf
- CAPACIDAD DE DIFUSION + VOLUMENES.pdf

## Ventana de extracción

```text
2026-06-10 <= VisitDateTime < 2026-06-14
```

## Pipelines validados

```bash
python -m src.pipeline_dlco \
  --start-date 2026-06-10 \
  --end-date 2026-06-14

python -m src.pipeline_pleth \
  --start-date 2026-06-10 \
  --end-date 2026-06-14
```

## Variables validadas

### DLCO

- DLCOcor
- DLCOunc
- DL/VA
- VA
- IVC
- BHT
- TestGrade
- % predicho cuando aparece en el informe
- z-score cuando aparece en el informe

### Volúmenes pulmonares / Pleth

- FRC Pleth / TGV
- TLC
- RV
- RV/TLC
- Valores pre y post
- % predicho cuando aparece en el informe
- z-score cuando aparece en el informe

## Conversión de unidades DLCO

Los valores DLCO del pipeline están en unidades internas compatibles con mmol/min/kPa, mientras que los informes Breeze muestran DLCO en ml/min/mmHg.

Para comparar contra el informe se aplicó:

```text
valor_informe ≈ valor_pipeline × 2.986
```

Esta conversión fue necesaria para:

- DLCOcor
- DLCOunc
- DL/VA observado

## Criterios de comparación

```text
Valores observados:
- Volúmenes y DLCO: tolerancia absoluta 0.05
- Porcentajes: tolerancia absoluta 1 punto porcentual
- z-scores: tolerancia absoluta 0.05
- TestGrade: coincidencia exacta
```

Los campos sin valor transcrito en el informe se clasificaron como `not_applicable` y no penalizaron la validación.

## Resultado final

```text
overall_match_status:
60 match

value_match_status:
60 match

percent_match_status:
48 match
12 not_applicable

zscore_match_status:
40 match
20 not_applicable
```

## Hallazgo sobre DL/VA

La fila DL/VA del informe Breeze corresponde a:

```text
valor observado: kco_pre convertido a ml/min/mmHg/L
% predicho: dlva_percent_predicted_pre
z-score: dlva_zscore_pre
```

Para `dlva_zscore_pre`, el cálculo validado contra los informes fue:

```text
dlva_zscore = (dlva_pre - dlva_predicted) / dlva_sd
```

Este ajuste quedó incorporado en `src/transform/dlco.py`.

## Archivos locales de apoyo

Durante la validación se usaron archivos locales en `data/validation/`, entre ellos:

```text
data/validation/breeze_report_gold_standard.csv
data/validation/compare_breeze_reports.py
data/validation/breeze_reports_comparison.csv
```

Estos archivos no fueron versionados porque `data/validation/` está ignorado por Git. El resultado documentado aquí resume la validación sin incorporar datos clínicos ni informes PDF al repositorio.

## Limitaciones

Esta validación cubre DLCO y volúmenes pulmonares/Pleth para 7 informes de muestra.

No valida todavía:

- Espirometría FVL
- MIP/MEP
- Broncoprovocación con metacolina