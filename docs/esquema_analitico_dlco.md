# Esquema analítico DLCO

## Definición general

La tabla analítica DLCO contiene una fila por visita clínica con prueba funcional DLCO realizada.

La clave funcional de la tabla es `pat_visit_id`.

La regla funcional de inclusión es:

```sql
EXISTS (
    SELECT 1
    FROM dbo.DLCOData AS dl_effort
    WHERE dl_effort.PatVisitID = pv.PatVisitID
      AND dl_effort.EffortTypeID = 0
)
```

No se exige `pv.DLCOTest = 1` porque la validación de la base local mostró visitas con maniobras reales en `dbo.DLCOData` aun cuando el indicador de visita no es suficiente como criterio funcional.

Los resultados clínicos representativos se toman directamente de las filas generadas por Breeze:

- `EffortTypeID = 2`: resultado basal o `Pre/Baseline`.

Las maniobras individuales (`EffortTypeID = 0`) se usan para definir inclusión funcional de la visita, pero no para reconstruir el resultado representativo.

No se documentan columnas post para DLCO en esta fase. En la ventana anual validada `2025-01-01` a `2026-01-01` no se observaron registros `EffortTypeID = 3` en la extracción funcional DLCO.

## Resumen de columnas

- Total de columnas: 248
- Identificación de paciente: 8
- Visita: 13
- Referencias predicted/sd/cv/skewness: 132
- Observadas pre/baseline: 33
- Derivadas percent predicted / zscore: 62
- Variables DLCO configuradas: 33
- Variables numéricas con derivadas: 31
- Variables categóricas sin derivadas: 2

## Bloque de identificación de paciente

- `patient_guid`
- `patient_id_num`
- `patient_last_name`
- `patient_first_name`
- `patient_middle_name`
- `birthday`
- `sex_list_id`
- `race_list_id`

## Bloque de visita

- `pat_visit_id`
- `pat_visit_guid`
- `visit_datetime`
- `age`
- `weight`
- `height`
- `bmi`
- `pred_set_name`
- `diagnosis`
- `comments`
- `post_comment`
- `signed`
- `signed_datetime`

## Bloque de referencia

Cada variable base tiene columnas con sufijos:

- `_predicted`
- `_sd`
- `_cv`
- `_skewness`

Columnas:

- `dlcounc_predicted`
- `dlcounc_sd`
- `dlcounc_cv`
- `dlcounc_skewness`
- `dlcocor_predicted`
- `dlcocor_sd`
- `dlcocor_cv`
- `dlcocor_skewness`
- `dm_predicted`
- `dm_sd`
- `dm_cv`
- `dm_skewness`
- `kco_predicted`
- `kco_sd`
- `kco_cv`
- `kco_skewness`
- `va_predicted`
- `va_sd`
- `va_cv`
- `va_skewness`
- `dlva_predicted`
- `dlva_sd`
- `dlva_cv`
- `dlva_skewness`
- `svcsb_predicted`
- `svcsb_sd`
- `svcsb_cv`
- `svcsb_skewness`
- `frcsb_predicted`
- `frcsb_sd`
- `frcsb_cv`
- `frcsb_skewness`
- `rvsb_predicted`
- `rvsb_sd`
- `rvsb_cv`
- `rvsb_skewness`
- `ervsb_predicted`
- `ervsb_sd`
- `ervsb_cv`
- `ervsb_skewness`
- `tlcsb_predicted`
- `tlcsb_sd`
- `tlcsb_cv`
- `tlcsb_skewness`
- `rvtlcsb_predicted`
- `rvtlcsb_sd`
- `rvtlcsb_cv`
- `rvtlcsb_skewness`
- `tau_predicted`
- `tau_sd`
- `tau_cv`
- `tau_skewness`
- `fine_predicted`
- `fine_sd`
- `fine_cv`
- `fine_skewness`
- `fene_predicted`
- `fene_sd`
- `fene_cv`
- `fene_skewness`
- `fico_predicted`
- `fico_sd`
- `fico_cv`
- `fico_skewness`
- `feco_predicted`
- `feco_sd`
- `feco_cv`
- `feco_skewness`
- `bht_predicted`
- `bht_sd`
- `bht_cv`
- `bht_skewness`
- `ivc_predicted`
- `ivc_sd`
- `ivc_cv`
- `ivc_skewness`
- `dlcoatscodes_predicted`
- `dlcoatscodes_sd`
- `dlcoatscodes_cv`
- `dlcoatscodes_skewness`
- `startcollectvol_predicted`
- `startcollectvol_sd`
- `startcollectvol_cv`
- `startcollectvol_skewness`
- `stopcollectvol_predicted`
- `stopcollectvol_sd`
- `stopcollectvol_cv`
- `stopcollectvol_skewness`
- `ictlcsb_predicted`
- `ictlcsb_sd`
- `ictlcsb_cv`
- `ictlcsb_skewness`
- `fich4_predicted`
- `fich4_sd`
- `fich4_cv`
- `fich4_skewness`
- `fech4_predicted`
- `fech4_sd`
- `fech4_cv`
- `fech4_skewness`
- `fic2h2_predicted`
- `fic2h2_sd`
- `fic2h2_cv`
- `fic2h2_skewness`
- `fec2h2_predicted`
- `fec2h2_sd`
- `fec2h2_cv`
- `fec2h2_skewness`
- `ch4slope_predicted`
- `ch4slope_sd`
- `ch4slope_cv`
- `ch4slope_skewness`
- `anatomicdeadspace_predicted`
- `anatomicdeadspace_sd`
- `anatomicdeadspace_cv`
- `anatomicdeadspace_skewness`
- `valvedeadspace_predicted`
- `valvedeadspace_sd`
- `valvedeadspace_cv`
- `valvedeadspace_skewness`
- `vatlcpl_predicted`
- `vatlcpl_sd`
- `vatlcpl_cv`
- `vatlcpl_skewness`
- `vatlcn2_predicted`
- `vatlcn2_sd`
- `vatlcn2_cv`
- `vatlcn2_skewness`
- `dlcoatsgrades_predicted`
- `dlcoatsgrades_sd`
- `dlcoatsgrades_cv`
- `dlcoatsgrades_skewness`

## Bloque de resultados observados pre/baseline

Cada variable base observada validada aparece con sufijo `_pre`.

Columnas:

- `dlcounc_pre`
- `dlcocor_pre`
- `dm_pre`
- `kco_pre`
- `va_pre`
- `dlva_pre`
- `svcsb_pre`
- `frcsb_pre`
- `rvsb_pre`
- `ervsb_pre`
- `tlcsb_pre`
- `rvtlcsb_pre`
- `tau_pre`
- `fine_pre`
- `fene_pre`
- `fico_pre`
- `feco_pre`
- `bht_pre`
- `ivc_pre`
- `dlcoatscodes_pre`
- `startcollectvol_pre`
- `stopcollectvol_pre`
- `ictlcsb_pre`
- `fich4_pre`
- `fech4_pre`
- `fic2h2_pre`
- `fec2h2_pre`
- `ch4slope_pre`
- `anatomicdeadspace_pre`
- `valvedeadspace_pre`
- `vatlcpl_pre`
- `vatlcn2_pre`
- `dlcoatsgrades_pre`

## Bloque de variables derivadas

Para las variables numéricas se calculan:

- `_percent_predicted_pre`
- `_zscore_pre`

Columnas:

- `dlcounc_percent_predicted_pre`
- `dlcounc_zscore_pre`
- `dlcocor_percent_predicted_pre`
- `dlcocor_zscore_pre`
- `dm_percent_predicted_pre`
- `dm_zscore_pre`
- `kco_percent_predicted_pre`
- `kco_zscore_pre`
- `va_percent_predicted_pre`
- `va_zscore_pre`
- `dlva_percent_predicted_pre`
- `dlva_zscore_pre`
- `svcsb_percent_predicted_pre`
- `svcsb_zscore_pre`
- `frcsb_percent_predicted_pre`
- `frcsb_zscore_pre`
- `rvsb_percent_predicted_pre`
- `rvsb_zscore_pre`
- `ervsb_percent_predicted_pre`
- `ervsb_zscore_pre`
- `tlcsb_percent_predicted_pre`
- `tlcsb_zscore_pre`
- `rvtlcsb_percent_predicted_pre`
- `rvtlcsb_zscore_pre`
- `tau_percent_predicted_pre`
- `tau_zscore_pre`
- `fine_percent_predicted_pre`
- `fine_zscore_pre`
- `fene_percent_predicted_pre`
- `fene_zscore_pre`
- `fico_percent_predicted_pre`
- `fico_zscore_pre`
- `feco_percent_predicted_pre`
- `feco_zscore_pre`
- `bht_percent_predicted_pre`
- `bht_zscore_pre`
- `ivc_percent_predicted_pre`
- `ivc_zscore_pre`
- `startcollectvol_percent_predicted_pre`
- `startcollectvol_zscore_pre`
- `stopcollectvol_percent_predicted_pre`
- `stopcollectvol_zscore_pre`
- `ictlcsb_percent_predicted_pre`
- `ictlcsb_zscore_pre`
- `fich4_percent_predicted_pre`
- `fich4_zscore_pre`
- `fech4_percent_predicted_pre`
- `fech4_zscore_pre`
- `fic2h2_percent_predicted_pre`
- `fic2h2_zscore_pre`
- `fec2h2_percent_predicted_pre`
- `fec2h2_zscore_pre`
- `ch4slope_percent_predicted_pre`
- `ch4slope_zscore_pre`
- `anatomicdeadspace_percent_predicted_pre`
- `anatomicdeadspace_zscore_pre`
- `valvedeadspace_percent_predicted_pre`
- `valvedeadspace_zscore_pre`
- `vatlcpl_percent_predicted_pre`
- `vatlcpl_zscore_pre`
- `vatlcn2_percent_predicted_pre`
- `vatlcn2_zscore_pre`

## Variables categóricas

Las variables categóricas se conservan en los bloques de referencia y observación, pero no tienen columnas derivadas de porcentaje del predicho ni z-score.

- `dlcoatscodes`
- `dlcoatsgrades`

## Criterios de exclusión

No se incluyen en el esquema analítico inicial:

- claves internas de fila como `DLCODataID`;
- campos binarios `varbinary`;
- campos de control técnico de maniobra;
- columnas post no observadas en la validación anual;
- reconstrucciones manuales a partir de curvas o fuentes binarias.

## Fórmulas derivadas

Para cada variable numérica con valor observado basal y valor predicho:

```text
percent_predicted_pre = pre / predicted * 100
```

Para cada variable numérica con valor observado basal, valor predicho, coeficiente de variación y skewness:

```text
zscore_pre = (((pre / predicted) ** skewness) - 1) / (skewness * cv)
```

Estas fórmulas se aplican solo cuando los insumos son válidos y no nulos.
