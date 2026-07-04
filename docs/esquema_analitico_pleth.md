# Esquema analítico Pleth

## Definición general

La tabla analítica Pleth contiene una fila por visita clínica con pletismografía realizada.

La clave funcional de la tabla es `pat_visit_id`.

La regla funcional de inclusión es:

```sql
pv.PlethTest = 1
AND EXISTS (
    SELECT 1
    FROM dbo.PlethData AS pl_effort
    WHERE pl_effort.PatVisitID = pv.PatVisitID
      AND pl_effort.EffortTypeID = 0
)
```

La validación anual mostró que las visitas con `PlethTest = 1` coinciden con las visitas que tienen maniobras reales `EffortTypeID = 0` en `dbo.PlethData`.

Los resultados clínicos representativos se toman directamente de las filas generadas por Breeze:

- `EffortTypeID = 2`: resultado basal o `Pre/Baseline`.
- `EffortTypeID = 3`: resultado post.

Las maniobras individuales (`EffortTypeID = 0`) se usan para definir inclusión funcional de la visita, pero no para reconstruir el resultado representativo.

## Resumen de columnas

- Total de columnas: 187
- Identificación de paciente: 8
- Visita: 13
- Referencias predicted/sd/cv/skewness: 68
- Observadas pre/post: 34
- Derivadas percent predicted / zscore: 64
- Variables Pleth configuradas: 17
- Variables numéricas con derivadas: 16
- Variables categóricas sin derivadas: 1

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

- `tgv_pleth_predicted`
- `tgv_pleth_sd`
- `tgv_pleth_cv`
- `tgv_pleth_skewness`
- `rv_pleth_predicted`
- `rv_pleth_sd`
- `rv_pleth_cv`
- `rv_pleth_skewness`
- `tlc_pleth_predicted`
- `tlc_pleth_sd`
- `tlc_pleth_cv`
- `tlc_pleth_skewness`
- `rv_tlc_pleth_predicted`
- `rv_tlc_pleth_sd`
- `rv_tlc_pleth_cv`
- `rv_tlc_pleth_skewness`
- `trapped_gas_predicted`
- `trapped_gas_sd`
- `trapped_gas_cv`
- `trapped_gas_skewness`
- `v_pant_predicted`
- `v_pant_sd`
- `v_pant_cv`
- `v_pant_skewness`
- `raw_predicted`
- `raw_sd`
- `raw_cv`
- `raw_skewness`
- `gaw_predicted`
- `gaw_sd`
- `gaw_cv`
- `gaw_skewness`
- `s_gaw_predicted`
- `s_gaw_sd`
- `s_gaw_cv`
- `s_gaw_skewness`
- `s_raw_predicted`
- `s_raw_sd`
- `s_raw_cv`
- `s_raw_skewness`
- `raw_inspiratory_predicted`
- `raw_inspiratory_sd`
- `raw_inspiratory_cv`
- `raw_inspiratory_skewness`
- `raw_expiratory_predicted`
- `raw_expiratory_sd`
- `raw_expiratory_cv`
- `raw_expiratory_skewness`
- `v_pant_freq_predicted`
- `v_pant_freq_sd`
- `v_pant_freq_cv`
- `v_pant_freq_skewness`
- `pleth_ats_codes_predicted`
- `pleth_ats_codes_sd`
- `pleth_ats_codes_cv`
- `pleth_ats_codes_skewness`
- `external_resistance_predicted`
- `external_resistance_sd`
- `external_resistance_cv`
- `external_resistance_skewness`
- `box_volume_predicted`
- `box_volume_sd`
- `box_volume_cv`
- `box_volume_skewness`
- `ic_tlc_pleth_predicted`
- `ic_tlc_pleth_sd`
- `ic_tlc_pleth_cv`
- `ic_tlc_pleth_skewness`

## Bloque de resultados observados pre/post

Cada variable base observada validada puede aparecer con sufijos:

- `_pre`
- `_post`

Columnas:

- `tgv_pleth_pre`
- `tgv_pleth_post`
- `rv_pleth_pre`
- `rv_pleth_post`
- `tlc_pleth_pre`
- `tlc_pleth_post`
- `rv_tlc_pleth_pre`
- `rv_tlc_pleth_post`
- `trapped_gas_pre`
- `trapped_gas_post`
- `v_pant_pre`
- `v_pant_post`
- `raw_pre`
- `raw_post`
- `gaw_pre`
- `gaw_post`
- `s_gaw_pre`
- `s_gaw_post`
- `s_raw_pre`
- `s_raw_post`
- `raw_inspiratory_pre`
- `raw_inspiratory_post`
- `raw_expiratory_pre`
- `raw_expiratory_post`
- `v_pant_freq_pre`
- `v_pant_freq_post`
- `pleth_ats_codes_pre`
- `pleth_ats_codes_post`
- `external_resistance_pre`
- `external_resistance_post`
- `box_volume_pre`
- `box_volume_post`
- `ic_tlc_pleth_pre`
- `ic_tlc_pleth_post`

## Bloque de variables derivadas

Para las variables numéricas se calculan:

- `_percent_predicted_pre`
- `_zscore_pre`
- `_percent_predicted_post`
- `_zscore_post`

Columnas:

- `tgv_pleth_percent_predicted_pre`
- `tgv_pleth_zscore_pre`
- `tgv_pleth_percent_predicted_post`
- `tgv_pleth_zscore_post`
- `rv_pleth_percent_predicted_pre`
- `rv_pleth_zscore_pre`
- `rv_pleth_percent_predicted_post`
- `rv_pleth_zscore_post`
- `tlc_pleth_percent_predicted_pre`
- `tlc_pleth_zscore_pre`
- `tlc_pleth_percent_predicted_post`
- `tlc_pleth_zscore_post`
- `rv_tlc_pleth_percent_predicted_pre`
- `rv_tlc_pleth_zscore_pre`
- `rv_tlc_pleth_percent_predicted_post`
- `rv_tlc_pleth_zscore_post`
- `trapped_gas_percent_predicted_pre`
- `trapped_gas_zscore_pre`
- `trapped_gas_percent_predicted_post`
- `trapped_gas_zscore_post`
- `v_pant_percent_predicted_pre`
- `v_pant_zscore_pre`
- `v_pant_percent_predicted_post`
- `v_pant_zscore_post`
- `raw_percent_predicted_pre`
- `raw_zscore_pre`
- `raw_percent_predicted_post`
- `raw_zscore_post`
- `gaw_percent_predicted_pre`
- `gaw_zscore_pre`
- `gaw_percent_predicted_post`
- `gaw_zscore_post`
- `s_gaw_percent_predicted_pre`
- `s_gaw_zscore_pre`
- `s_gaw_percent_predicted_post`
- `s_gaw_zscore_post`
- `s_raw_percent_predicted_pre`
- `s_raw_zscore_pre`
- `s_raw_percent_predicted_post`
- `s_raw_zscore_post`
- `raw_inspiratory_percent_predicted_pre`
- `raw_inspiratory_zscore_pre`
- `raw_inspiratory_percent_predicted_post`
- `raw_inspiratory_zscore_post`
- `raw_expiratory_percent_predicted_pre`
- `raw_expiratory_zscore_pre`
- `raw_expiratory_percent_predicted_post`
- `raw_expiratory_zscore_post`
- `v_pant_freq_percent_predicted_pre`
- `v_pant_freq_zscore_pre`
- `v_pant_freq_percent_predicted_post`
- `v_pant_freq_zscore_post`
- `external_resistance_percent_predicted_pre`
- `external_resistance_zscore_pre`
- `external_resistance_percent_predicted_post`
- `external_resistance_zscore_post`
- `box_volume_percent_predicted_pre`
- `box_volume_zscore_pre`
- `box_volume_percent_predicted_post`
- `box_volume_zscore_post`
- `ic_tlc_pleth_percent_predicted_pre`
- `ic_tlc_pleth_zscore_pre`
- `ic_tlc_pleth_percent_predicted_post`
- `ic_tlc_pleth_zscore_post`

## Variables categóricas

Las variables categóricas se conservan en los bloques de referencia y observación, pero no tienen columnas derivadas de porcentaje del predicho ni z-score.

- `pleth_ats_codes`

## Criterios de exclusión

No se incluyen en el esquema analítico inicial:

- claves internas de fila como `PlethDataID`;
- campos binarios `varbinary`;
- campos de control técnico de maniobra;
- pendientes, offsets y parámetros técnicos de calibración de las curvas;
- reconstrucciones manuales a partir de curvas o fuentes binarias.

## Fórmulas derivadas

Para cada variable numérica con valor observado y valor predicho:

```text
percent_predicted = observed / predicted * 100
```

Para cada variable numérica con valor observado, valor predicho, coeficiente de variación y skewness:

```text
zscore = (((observed / predicted) ** skewness) - 1) / (skewness * cv)
```

Estas fórmulas se aplican para `pre` y `post` solo cuando los insumos son válidos y no nulos.
