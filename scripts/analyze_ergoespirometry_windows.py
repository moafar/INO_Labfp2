# scripts/analyze_ergoespirometry_windows.py
"""Evalúa correspondencias entre señales GX y resúmenes de Patient Query."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.validate_ergoespirometry import (
    DEFAULT_REFERENCE_PATH,
    load_reference,
    normalize_datetime,
    normalize_patient_id,
)
from src.extract.ergoespirometry import extract_ergoespirometry
from src.transform.ergoespirometry import (
    ErgoespirometryDecodeError,
    decode_manual_data,
    decode_raw_data,
    manual_data_to_dataframe,
    raw_data_to_dataframe,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "ergoespirometry_window_scores.csv"
)

WINDOW_SECONDS = [10, 20, 30, 45, 60, 90, 120]
WINDOW_POSITIONS = ("pre", "centered", "post")
EVALUATION_MODULUS = 5
AMBIENT_FIO2_FRACTION = 0.2093
AMBIENT_FICO2_FRACTION = 0.0004
MIN_PLAUSIBLE_MANUAL_HEART_RATE_BPM = 20.0
MAX_PLAUSIBLE_MANUAL_HEART_RATE_BPM = 300.0

MOMENT_CONFIG = {
    "rest": {
        "label": "GX Rest",
        "time_column": "StartExerciseTime",
        "pq_time_column": "GX Rest Time (min)",
    },
    "at": {
        "label": "GX AT",
        "time_column": "ATElapsedTime",
        "pq_time_column": "GX AT Time (min)",
    },
    "vo2_max": {
        "label": "GX VO2 Max",
        "time_column": "VO2MaxElapsedTime",
        "pq_time_column": "GX VO2 Max Time (min)",
    },
}

TARGET_SUFFIXES = {
    "vo2": "VO2 (mL/min)",
    "vco2": "VCO2 (mL/min)",
    "rq": "RQ",
    "heart_rate": "HR (BPM)",
    "work": "Work (Watts)",
    "tidal_volume": "Vt BTPS (L)",
    "ventilation": "VE BTPS (L/min)",
    "respiratory_rate": "RR (br/min)",
    "ve_vo2": "VE/VO2",
    "ve_vco2": "VE/VCO2",
    "vo2_hr": "VO2/HR (mL/beat)",
    "petco2": "PETCO2 (mmHg)",
    "peto2": "PETO2 (mmHg)",
}

PRIORITY_RAW_CANDIDATES = {
    "respiratory_rate": {"rr_from_breath_duration"},
    "tidal_volume": {"vt_atps_from_channel_12_l"},
    "ventilation": {"ve_atps_from_vt_ttot_l_min"},
    "work": {"work_watts"},
    "vo2": {
        "vo2_haldane_derived_mixed_atps_ml_min",
        "vo2_haldane_ambient_derived_mixed_atps_ml_min",
        "vo2_simple_derived_mixed_atps_ml_min",
    },
    "vco2": {
        "vco2_haldane_derived_mixed_atps_ml_min",
        "vco2_haldane_ambient_derived_mixed_atps_ml_min",
        "vco2_simple_derived_mixed_atps_ml_min",
    },
    "rq": {"rer_haldane_derived_mixed"},
    "ve_vo2": {"ve_vo2_haldane_derived_mixed"},
    "ve_vco2": {"ve_vco2_haldane_derived_mixed"},
    "heart_rate": {"manual_heart_rate_bpm"},
}

SIGNAL_RELATIONSHIPS = {
    "inspiratory_time_vs_breath_duration": (
        "inspiratory_time_s",
        "breath_duration_s",
    ),
    "gross_expired_o2_volume_vs_tidal_volume": (
        "gross_expired_o2_volume_ml_per_breath",
        "tidal_volume_atps_ml",
    ),
    "gross_expired_co2_volume_vs_tidal_volume": (
        "gross_expired_co2_volume_ml_per_breath",
        "tidal_volume_atps_ml",
    ),
}

RAW_EXCLUDED_COLUMNS = {
    "observation_index",
    "elapsed_time_s",
}


def prepare_sql_extract(
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Extrae las pruebas GX y conserva sus binarios."""

    dataframe = extract_ergoespirometry(
        start_date=start_date,
        end_date=end_date,
    ).copy()

    dataframe["match_patient_id"] = normalize_patient_id(
        dataframe["PatientIDNum"]
    )
    dataframe["match_visit_datetime"] = normalize_datetime(
        dataframe["VisitDateTime"]
    )

    duplicate_mask = dataframe.duplicated(
        subset=[
            "match_patient_id",
            "match_visit_datetime",
        ],
        keep=False,
    )

    if duplicate_mask.any():
        raise ValueError(
            "La extracción contiene claves de emparejamiento ambiguas: "
            f"{int(duplicate_mask.sum())} filas afectadas."
        )

    return dataframe


def build_matched_tests(
    reference: pd.DataFrame,
    sql_extract: pd.DataFrame,
) -> pd.DataFrame:
    """Empareja las pruebas y conserva solo binarios disponibles."""

    matched = reference.merge(
        sql_extract,
        on=[
            "match_patient_id",
            "match_visit_datetime",
        ],
        how="inner",
        suffixes=("_patient_query", "_sql"),
        validate="one_to_one",
    )

    return matched[
        matched["GXTestRawData"].notna()
    ].copy()


def get_target_time(
    record: pd.Series,
    moment: str,
) -> float | None:
    """Obtiene el segundo objetivo para un momento de resumen."""

    config = MOMENT_CONFIG[moment]
    raw_value = record.get(config["time_column"])

    if pd.isna(raw_value):
        return None
    value = float(raw_value)
    if not np.isfinite(value) or value <= 0:
        return None
    return value


def get_patient_query_time(
    record: pd.Series,
    moment: str,
) -> float | None:
    """Obtiene el tiempo publicado, redondeado por Patient Query a minutos."""

    raw_value = record.get(MOMENT_CONFIG[moment]["pq_time_column"])
    if pd.isna(raw_value):
        return None
    return float(raw_value) * 60.0


def build_target_values(
    record: pd.Series,
    moment: str,
) -> dict[str, float]:
    """Extrae los resultados publicados por Patient Query."""

    prefix = MOMENT_CONFIG[moment]["label"]
    targets: dict[str, float] = {}

    for target_name, suffix in TARGET_SUFFIXES.items():
        column_name = f"{prefix} {suffix}"
        value = record.get(column_name)

        targets[target_name] = (
            float(value)
            if pd.notna(value)
            else np.nan
        )

    return targets


def calculate_haldane_series(
    expired_ventilation_l_min: pd.Series,
    fio2_fraction: pd.Series,
    feo2_fraction: pd.Series,
    fico2_fraction: pd.Series,
    feco2_fraction: pd.Series,
) -> tuple[pd.Series, pd.Series]:
    """Vectoriza Haldane sin atribuir identidad definitiva a los canales GX."""

    inspired_inert_fraction = 1.0 - fio2_fraction - fico2_fraction
    expired_inert_fraction = 1.0 - feo2_fraction - feco2_fraction
    fractions = pd.concat(
        [
            fio2_fraction,
            feo2_fraction,
            fico2_fraction,
            feco2_fraction,
        ],
        axis="columns",
    )
    valid = (
        expired_ventilation_l_min.gt(0)
        & fractions.ge(0).all(axis="columns")
        & fractions.lt(1).all(axis="columns")
        & inspired_inert_fraction.gt(0)
        & expired_inert_fraction.gt(0)
    )
    inspired_ventilation_l_min = (
        expired_ventilation_l_min
        * expired_inert_fraction
        / inspired_inert_fraction
    ).where(valid)
    vo2_ml_min = (
        inspired_ventilation_l_min * fio2_fraction
        - expired_ventilation_l_min * feo2_fraction
    ) * 1000.0
    vco2_ml_min = (
        expired_ventilation_l_min * feco2_fraction
        - inspired_ventilation_l_min * fico2_fraction
    ) * 1000.0
    return vo2_ml_min.where(vo2_ml_min.ge(0)), vco2_ml_min.where(
        vco2_ml_min.ge(0)
    )


def add_derived_raw_series(
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Añade candidatos calculables desde las señales originales."""

    result = signals.copy()

    ventilatory_columns = {
        "breath_duration_s",
        "tidal_volume_atps_ml",
    }

    if not ventilatory_columns.issubset(result.columns):
        return result

    duration = pd.to_numeric(
        result["breath_duration_s"],
        errors="coerce",
    )

    tidal_volume_atps_ml = pd.to_numeric(
        result["tidal_volume_atps_ml"],
        errors="coerce",
    )

    valid_duration = duration.gt(0)

    result["rr_from_breath_duration"] = np.where(
        valid_duration,
        60.0 / duration,
        np.nan,
    )

    valid_tidal_volume = tidal_volume_atps_ml.gt(0)
    result["vt_atps_from_channel_12_l"] = (
        tidal_volume_atps_ml / 1000.0
    ).where(valid_tidal_volume)

    result["ve_atps_from_vt_ttot_l_min"] = np.where(
        valid_duration & valid_tidal_volume,
        (
            tidal_volume_atps_ml
            * 60.0
            / duration
            / 1000.0
        ),
        np.nan,
    )

    gas_columns = {
        "fio2_fraction",
        "fico2_fraction",
        "gross_expired_o2_volume_ml_per_breath",
        "gross_expired_co2_volume_ml_per_breath",
    }

    if not gas_columns.issubset(result.columns):
        return result

    fio2 = pd.to_numeric(
        result["fio2_fraction"],
        errors="coerce",
    )
    gross_expired_o2_ml = pd.to_numeric(
        result["gross_expired_o2_volume_ml_per_breath"],
        errors="coerce",
    )
    fico2 = pd.to_numeric(
        result["fico2_fraction"],
        errors="coerce",
    )
    gross_expired_co2_ml = pd.to_numeric(
        result["gross_expired_co2_volume_ml_per_breath"],
        errors="coerce",
    )
    ve_atps = pd.to_numeric(
        result["ve_atps_from_vt_ttot_l_min"],
        errors="coerce",
    )

    feo2_mixed = (
        gross_expired_o2_ml / tidal_volume_atps_ml
    ).where(valid_tidal_volume)
    feco2_mixed = (
        gross_expired_co2_ml / tidal_volume_atps_ml
    ).where(valid_tidal_volume)
    result["feo2_mixed_fraction_from_expired_volumes"] = feo2_mixed
    result["feco2_mixed_fraction_from_expired_volumes"] = feco2_mixed

    vo2_haldane, vco2_haldane = calculate_haldane_series(
        expired_ventilation_l_min=ve_atps,
        fio2_fraction=fio2,
        feo2_fraction=feo2_mixed,
        fico2_fraction=fico2,
        feco2_fraction=feco2_mixed,
    )
    result["vo2_haldane_derived_mixed_atps_ml_min"] = vo2_haldane
    result["vco2_haldane_derived_mixed_atps_ml_min"] = vco2_haldane

    ambient_fio2 = pd.Series(
        AMBIENT_FIO2_FRACTION,
        index=result.index,
    )
    ambient_fico2 = pd.Series(
        AMBIENT_FICO2_FRACTION,
        index=result.index,
    )
    vo2_ambient, vco2_ambient = calculate_haldane_series(
        expired_ventilation_l_min=ve_atps,
        fio2_fraction=ambient_fio2,
        feo2_fraction=feo2_mixed,
        fico2_fraction=ambient_fico2,
        feco2_fraction=feco2_mixed,
    )
    result["vo2_haldane_ambient_derived_mixed_atps_ml_min"] = vo2_ambient
    result["vco2_haldane_ambient_derived_mixed_atps_ml_min"] = vco2_ambient

    result["vo2_simple_derived_mixed_atps_ml_min"] = (
        ve_atps * (fio2 - feo2_mixed) * 1000.0
    ).where(ve_atps.gt(0))
    result["vco2_simple_derived_mixed_atps_ml_min"] = (
        ve_atps * (feco2_mixed - fico2) * 1000.0
    ).where(ve_atps.gt(0))

    result["rer_haldane_derived_mixed"] = (
        vco2_haldane / vo2_haldane
    ).where(vo2_haldane.gt(0))
    result["ve_vo2_haldane_derived_mixed"] = (
        ve_atps * 1000.0 / vo2_haldane
    ).where(vo2_haldane.gt(0))
    result["ve_vco2_haldane_derived_mixed"] = (
        ve_atps * 1000.0 / vco2_haldane
    ).where(vco2_haldane.gt(0))

    return result


def summarize_at_time(
    signals: pd.DataFrame,
    target_time: float,
) -> list[dict[str, object]]:
    """Calcula muestra cercana y ventanas pre, centradas y posteriores."""

    elapsed = pd.to_numeric(
        signals["elapsed_time_s"],
        errors="coerce",
    )

    valid_time = elapsed.notna()

    if not valid_time.any():
        return []

    nearest_index = (
        elapsed.loc[valid_time] - target_time
    ).abs().idxmin()

    raw_columns = [
        column
        for column in signals.columns
        if column not in RAW_EXCLUDED_COLUMNS
    ]

    summaries: list[dict[str, object]] = []

    for raw_metric in raw_columns:
        series = pd.to_numeric(
            signals[raw_metric],
            errors="coerce",
        )

        nearest_value = series.loc[nearest_index]

        summaries.append(
            {
                "raw_metric": raw_metric,
                "window_seconds": 0,
                "window_position": "nearest",
                "statistic": "nearest",
                "raw_value": nearest_value,
                "observations": 1,
                "mean_time_offset_s": (
                    elapsed.loc[nearest_index] - target_time
                ),
            }
        )

        for window_seconds in WINDOW_SECONDS:
            bounds = {
                "pre": (
                    target_time - window_seconds,
                    target_time,
                ),
                "centered": (
                    target_time - window_seconds / 2.0,
                    target_time + window_seconds / 2.0,
                ),
                "post": (
                    target_time,
                    target_time + window_seconds,
                ),
            }

            for window_position in WINDOW_POSITIONS:
                lower_bound, upper_bound = bounds[window_position]
                window_mask = elapsed.ge(lower_bound) & elapsed.le(
                    upper_bound
                )
                window = series.loc[window_mask].dropna()

                if window.empty:
                    continue

                for statistic in ("mean", "median"):
                    summary_value = getattr(window, statistic)()
                    summaries.append(
                        {
                            "raw_metric": raw_metric,
                            "window_seconds": window_seconds,
                            "window_position": window_position,
                            "statistic": statistic,
                            "raw_value": summary_value,
                            "observations": len(window),
                            "mean_time_offset_s": (
                                elapsed.loc[window.index].mean()
                                - target_time
                            ),
                        }
                    )

    return summaries


def build_feature_table(
    matched: pd.DataFrame,
) -> pd.DataFrame:
    """Decodifica cada prueba y construye candidatos de resumen."""

    rows: list[dict[str, object]] = []
    decode_errors: list[tuple[int, str]] = []

    for position, (_, record) in enumerate(
        matched.iterrows(),
        start=1,
    ):
        gx_test_id = int(record["GXTestID"])

        try:
            signals = raw_data_to_dataframe(
                decode_raw_data(record["GXTestRawData"])
            )
        except ErgoespirometryDecodeError as error:
            decode_errors.append(
                (gx_test_id, str(error))
            )
            continue

        signals = add_derived_raw_series(signals)
        manual_signals = pd.DataFrame()
        manual_blob = record.get("ManuallyEnteredData")
        test_start_time = record.get("GXTestStartTime")
        if pd.notna(manual_blob) and pd.notna(test_start_time):
            try:
                manual_data = manual_data_to_dataframe(
                    decode_manual_data(manual_blob)
                )
                heart_rate = manual_data[
                    manual_data["measurement_name"].eq("heart_rate")
                ].copy()
                if not heart_rate.empty:
                    plausible = heart_rate["value"].between(
                        MIN_PLAUSIBLE_MANUAL_HEART_RATE_BPM,
                        MAX_PLAUSIBLE_MANUAL_HEART_RATE_BPM,
                    )
                    heart_rate = heart_rate.loc[plausible].copy()
                    heart_rate["elapsed_time_s"] = (
                        pd.to_datetime(heart_rate["timestamp"])
                        - pd.Timestamp(test_start_time)
                    ).dt.total_seconds()
                    manual_signals = heart_rate[
                        ["elapsed_time_s", "value"]
                    ].rename(columns={"value": "manual_heart_rate_bpm"})
            except ErgoespirometryDecodeError as error:
                decode_errors.append((gx_test_id, str(error)))

        for moment in MOMENT_CONFIG:
            target_time = get_target_time(
                record=record,
                moment=moment,
            )
            patient_query_time = get_patient_query_time(
                record=record,
                moment=moment,
            )

            if target_time is None:
                continue

            target_values = build_target_values(
                record=record,
                moment=moment,
            )

            summaries = summarize_at_time(
                signals=signals,
                target_time=target_time,
            )
            if not manual_signals.empty:
                summaries.extend(
                    summarize_at_time(
                        signals=manual_signals,
                        target_time=target_time,
                    )
                )

            for summary in summaries:
                row = {
                    "gx_test_id": gx_test_id,
                    "pat_visit_id": int(record["PatVisitID"]),
                    "moment": moment,
                    "target_time_s": target_time,
                    "pq_target_time_s": patient_query_time,
                    "pq_time_minus_marker_s": (
                        patient_query_time - target_time
                        if patient_query_time is not None
                        else np.nan
                    ),
                    "evaluation_set": (
                        gx_test_id % EVALUATION_MODULUS == 0
                    ),
                    **summary,
                }

                for target_name, target_value in (
                    target_values.items()
                ):
                    row[f"pq_{target_name}"] = target_value

                rows.append(row)

        if position % 50 == 0 or position == len(matched):
            print(
                f"Pruebas decodificadas: "
                f"{position:,}/{len(matched):,}"
            )

    if decode_errors:
        print("\nErrores de decodificación:")
        for gx_test_id, message in decode_errors:
            print(f"- GXTestID {gx_test_id}: {message}")

    return pd.DataFrame(rows)


def calculate_scores(
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Evalúa candidatos sin ajuste solo en la partición independiente."""

    score_rows: list[dict[str, object]] = []

    group_columns = [
        "moment",
        "raw_metric",
        "window_seconds",
        "window_position",
        "statistic",
    ]

    for group_key, group in features.groupby(
        group_columns,
        dropna=False,
        sort=False,
    ):
        (
            moment,
            raw_metric,
            window_seconds,
            window_position,
            statistic,
        ) = group_key

        raw_values = pd.to_numeric(
            group["raw_value"],
            errors="coerce",
        )

        for target_name in TARGET_SUFFIXES:
            target_column = f"pq_{target_name}"

            target_values = pd.to_numeric(
                group[target_column],
                errors="coerce",
            )

            valid = (
                raw_values.notna()
                & target_values.notna()
                & np.isfinite(raw_values)
                & np.isfinite(target_values)
            )
            evaluation_mask = group["evaluation_set"].fillna(False).astype(
                bool
            )
            test_valid = valid & evaluation_mask
            train_valid = valid & ~evaluation_mask
            test_size = int(test_valid.sum())

            if test_size < 10:
                continue

            predicted = raw_values.loc[test_valid].astype("float64")
            observed = target_values.loc[test_valid].astype("float64")
            train_predicted = raw_values.loc[train_valid].astype("float64")
            train_observed = target_values.loc[train_valid].astype("float64")

            if (
                predicted.nunique(dropna=True) < 2
                or observed.nunique(dropna=True) < 2
            ):
                pearson = np.nan
                spearman = np.nan
            else:
                pearson = predicted.corr(
                    observed,
                    method="pearson",
                )

                spearman = predicted.rank(
                    method="average",
                ).corr(
                    observed.rank(method="average"),
                    method="pearson",
                )

            residual = predicted - observed
            absolute_error = residual.abs()
            nonzero_target = observed.abs().gt(1e-12)

            if nonzero_target.any():
                median_absolute_percentage_error = (
                    (
                        absolute_error.loc[nonzero_target]
                        / observed.loc[nonzero_target].abs()
                    )
                    .median()
                    * 100.0
                )
            else:
                median_absolute_percentage_error = np.nan

            total_sum = ((observed - observed.mean()) ** 2).sum()
            r2 = (
                1.0 - ((observed - predicted) ** 2).sum() / total_sum
                if total_sum > 0
                else np.nan
            )
            residual_quantiles = residual.quantile(
                [0.05, 0.25, 0.5, 0.75, 0.95]
            )
            train_residual = train_predicted - train_observed
            train_total_sum = (
                (train_observed - train_observed.mean()) ** 2
            ).sum()
            train_nonzero = train_observed.abs().gt(1e-12)
            train_pearson = (
                train_predicted.corr(train_observed)
                if train_predicted.nunique() >= 2
                and train_observed.nunique() >= 2
                else np.nan
            )

            score_rows.append(
                {
                    "moment": moment,
                    "target_metric": target_name,
                    "raw_metric": raw_metric,
                    "window_seconds": window_seconds,
                    "window_position": window_position,
                    "statistic": statistic,
                    "split_rule": "gx_test_id_mod_5_eq_0",
                    "train_size": int(train_valid.sum()),
                    "test_size": test_size,
                    "train_pearson": train_pearson,
                    "train_r2": (
                        1.0
                        - ((train_observed - train_predicted) ** 2).sum()
                        / train_total_sum
                        if train_total_sum > 0
                        else np.nan
                    ),
                    "train_mean_absolute_error": train_residual.abs().mean(),
                    "train_median_absolute_percentage_error": (
                        (
                            train_residual.loc[train_nonzero].abs()
                            / train_observed.loc[train_nonzero].abs()
                        ).median()
                        * 100.0
                        if train_nonzero.any()
                        else np.nan
                    ),
                    "train_bias": train_residual.mean(),
                    "test_pearson": pearson,
                    "abs_pearson": (
                        abs(pearson)
                        if pd.notna(pearson)
                        else np.nan
                    ),
                    "test_spearman": spearman,
                    "test_r2": r2,
                    "test_mean_absolute_error": (
                        absolute_error.mean()
                    ),
                    "test_median_absolute_percentage_error": (
                        median_absolute_percentage_error
                    ),
                    "test_bias": residual.mean(),
                    "test_residual_std": residual.std(ddof=1),
                    "test_residual_p05": residual_quantiles.loc[0.05],
                    "test_residual_p25": residual_quantiles.loc[0.25],
                    "test_residual_median": residual_quantiles.loc[0.5],
                    "test_residual_p75": residual_quantiles.loc[0.75],
                    "test_residual_p95": residual_quantiles.loc[0.95],
                }
            )

    return pd.DataFrame(score_rows)


def calculate_signal_relationship_scores(
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Evalúa relaciones algebraicas de canales desconocidos fuera de muestra."""

    index_columns = [
        "gx_test_id",
        "moment",
        "window_seconds",
        "window_position",
        "statistic",
        "evaluation_set",
    ]
    metrics = {
        metric
        for relationship in SIGNAL_RELATIONSHIPS.values()
        for metric in relationship
    }
    wide = (
        features.loc[features["raw_metric"].isin(metrics)]
        .pivot(index=index_columns, columns="raw_metric", values="raw_value")
        .reset_index()
    )
    rows: list[dict[str, object]] = []
    config_columns = [
        "moment",
        "window_seconds",
        "window_position",
        "statistic",
    ]

    for config, group in wide.groupby(config_columns, sort=False):
        moment, window_seconds, window_position, statistic = config
        evaluation_mask = group["evaluation_set"].astype(bool)

        for relationship_name, (observed_metric, predictor_metric) in (
            SIGNAL_RELATIONSHIPS.items()
        ):
            observed = pd.to_numeric(group[observed_metric], errors="coerce")
            predictor = pd.to_numeric(group[predictor_metric], errors="coerce")
            valid = (
                observed.notna()
                & predictor.notna()
                & np.isfinite(observed)
                & np.isfinite(predictor)
                & predictor.abs().gt(1e-12)
            )
            train = valid & ~evaluation_mask
            test = valid & evaluation_mask
            if int(train.sum()) < 50 or int(test.sum()) < 20:
                continue

            x_train = predictor.loc[train].astype("float64")
            y_train = observed.loc[train].astype("float64")
            denominator = float((x_train**2).sum())
            if denominator <= 1e-12:
                continue
            coefficient = float((x_train * y_train).sum() / denominator)

            x_test = predictor.loc[test].astype("float64")
            y_test = observed.loc[test].astype("float64")
            predicted = coefficient * x_test
            residual = predicted - y_test
            absolute_error = residual.abs()
            ratios = y_test / x_test
            total_sum = ((y_test - y_test.mean()) ** 2).sum()
            r2 = (
                1.0 - ((y_test - predicted) ** 2).sum() / total_sum
                if total_sum > 0
                else np.nan
            )

            rows.append(
                {
                    "relationship": relationship_name,
                    "observed_metric": observed_metric,
                    "predictor_metric": predictor_metric,
                    "moment": moment,
                    "window_seconds": window_seconds,
                    "window_position": window_position,
                    "statistic": statistic,
                    "train_size": int(train.sum()),
                    "test_size": int(test.sum()),
                    "proportional_coefficient": coefficient,
                    "test_pearson": x_test.corr(y_test),
                    "test_r2": r2,
                    "test_mean_absolute_error": absolute_error.mean(),
                    "test_median_absolute_percentage_error": (
                        (absolute_error / y_test.abs()).median() * 100.0
                    ),
                    "test_bias": residual.mean(),
                    "test_ratio_p10": ratios.quantile(0.10),
                    "test_ratio_median": ratios.median(),
                    "test_ratio_p90": ratios.quantile(0.90),
                }
            )

    return pd.DataFrame(rows)


def print_best_candidates(
    scores: pd.DataFrame,
) -> None:
    """Muestra la mejor regla temporal por fórmula prioritaria sin ajuste."""

    for moment in MOMENT_CONFIG:
        print(f"\n=== {moment.upper()} ===")

        for target_metric, raw_metrics in PRIORITY_RAW_CANDIDATES.items():
            candidates = (
                scores[
                    scores["moment"].eq(moment)
                    & scores["target_metric"].eq(
                        target_metric
                    )
                    & scores["raw_metric"].isin(raw_metrics)
                ]
                .sort_values(
                    by=[
                        "train_median_absolute_percentage_error",
                        "train_r2",
                    ],
                    ascending=[True, False],
                )
                .head(1)
            )

            print(f"\nPatient Query: {target_metric}")

            if candidates.empty:
                print("Sin candidatos.")
                continue

            print(
                candidates[
                    [
                        "raw_metric",
                        "window_seconds",
                        "window_position",
                        "statistic",
                        "test_size",
                        "test_pearson",
                        "test_r2",
                        "test_mean_absolute_error",
                        "test_median_absolute_percentage_error",
                        "test_bias",
                    ]
                ].to_string(
                    index=False,
                    float_format=lambda value: f"{value:.3f}",
                )
            )


def parse_arguments() -> argparse.Namespace:
    """Lee la ventana y las rutas del análisis."""

    parser = argparse.ArgumentParser(
        description=(
            "Analiza ventanas y correspondencias "
            "de las señales GX."
        )
    )

    parser.add_argument(
        "--reference-path",
        type=Path,
        default=DEFAULT_REFERENCE_PATH,
    )

    parser.add_argument(
        "--start-date",
        default="2026-01-07",
    )

    parser.add_argument(
        "--end-date",
        default="2026-07-02",
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta el análisis completo."""

    arguments = parse_arguments()

    reference = load_reference(
        reference_path=arguments.reference_path,
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )

    sql_extract = prepare_sql_extract(
        start_date=arguments.start_date,
        end_date=arguments.end_date,
    )

    matched = build_matched_tests(
        reference=reference,
        sql_extract=sql_extract,
    )

    print(f"Referencias incluidas: {len(reference):,}")
    print(f"Pruebas emparejadas con binario: {len(matched):,}")

    features = build_feature_table(matched)
    arguments.output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    features_path = arguments.output_path.with_name(
        "ergoespirometry_window_features.parquet"
    )

    features.to_parquet(
        features_path,
        index=False,
    )

    print(
        "Características detalladas guardadas en: "
        f"{features_path}"
    )

    scores = calculate_scores(features)
    scores.to_csv(
        arguments.output_path,
        index=False,
        encoding="utf-8",
    )

    signal_scores = calculate_signal_relationship_scores(features)
    signal_scores_path = arguments.output_path.with_name(
        "ergoespirometry_signal_relationship_scores.csv"
    )
    signal_scores.to_csv(
        signal_scores_path,
        index=False,
        encoding="utf-8",
    )

    print_best_candidates(scores)

    print(
        "\nResultados completos guardados en: "
        f"{arguments.output_path}"
    )
    print(f"Relaciones entre señales guardadas en: {signal_scores_path}")


if __name__ == "__main__":
    main()
