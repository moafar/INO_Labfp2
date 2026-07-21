# scripts/analyze_ergoespirometry_calibration.py
"""Evalúa transformaciones lineales entre señales GX y Patient Query."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.analyze_ergoespirometry_windows import PRIORITY_RAW_CANDIDATES


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_FEATURES_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "ergoespirometry_window_features.parquet"
)

DEFAULT_OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "validation"
    / "ergoespirometry_calibration_scores.csv"
)

TARGET_METRICS = [
    "vo2",
    "vco2",
    "tidal_volume",
    "ventilation",
    "respiratory_rate",
    "heart_rate",
    "work",
    "rq",
    "ve_vo2",
    "ve_vco2",
    "vo2_hr",
]

CALIBRATION_MODELS = ("proportional", "affine")


def calculate_r2(
    observed: pd.Series,
    predicted: pd.Series,
) -> float:
    """Calcula R² sobre la muestra de evaluación."""

    residual_sum = (
        (observed - predicted) ** 2
    ).sum()

    total_sum = (
        (observed - observed.mean()) ** 2
    ).sum()

    if total_sum <= 0:
        return np.nan

    return 1.0 - (residual_sum / total_sum)


def calculate_median_ape(
    observed: pd.Series,
    predicted: pd.Series,
) -> float:
    """Calcula el error porcentual absoluto mediano."""

    nonzero = observed.abs().gt(1e-12)

    if not nonzero.any():
        return np.nan

    return float(
        (
            (
                observed.loc[nonzero]
                - predicted.loc[nonzero]
            ).abs()
            / observed.loc[nonzero].abs()
        ).median()
        * 100.0
    )


def calculate_scores(
    features: pd.DataFrame,
) -> pd.DataFrame:
    """Ajusta calibraciones explícitas en entrenamiento y evalúa aparte."""

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
        moment, raw_metric, window_seconds, window_position, statistic = (
            group_key
        )
        raw_values = pd.to_numeric(group["raw_value"], errors="coerce")
        gx_test_ids = pd.to_numeric(group["gx_test_id"], errors="coerce")

        for target_metric in TARGET_METRICS:
            target_values = pd.to_numeric(
                group[f"pq_{target_metric}"], errors="coerce"
            )
            valid = (
                raw_values.notna()
                & target_values.notna()
                & gx_test_ids.notna()
                & np.isfinite(raw_values)
                & np.isfinite(target_values)
            )
            if int(valid.sum()) < 100:
                continue

            x = raw_values.loc[valid].astype("float64")
            y = target_values.loc[valid].astype("float64")
            ids = gx_test_ids.loc[valid].astype("int64")
            if x.nunique(dropna=True) < 2 or y.nunique(dropna=True) < 2:
                continue

            test_mask = ids.mod(5).eq(0)
            train_mask = ~test_mask
            if int(train_mask.sum()) < 50 or int(test_mask.sum()) < 20:
                continue

            x_train = x.loc[train_mask]
            y_train = y.loc[train_mask]
            x_test = x.loc[test_mask]
            y_test = y.loc[test_mask]
            if x_train.std() <= 1e-12:
                continue

            for model_type in CALIBRATION_MODELS:
                if model_type == "affine":
                    slope, intercept = np.polyfit(x_train, y_train, 1)
                else:
                    denominator = float((x_train**2).sum())
                    if denominator <= 1e-12:
                        continue
                    slope = float((x_train * y_train).sum() / denominator)
                    intercept = 0.0

                predicted = slope * x_test + intercept
                residual = predicted - y_test
                train_predicted = slope * x_train + intercept
                train_residual = train_predicted - y_train
                residual_quantiles = residual.quantile(
                    [0.05, 0.25, 0.5, 0.75, 0.95]
                )
                test_pearson = (
                    x_test.corr(y_test)
                    if x_test.nunique() >= 2 and y_test.nunique() >= 2
                    else np.nan
                )
                score_rows.append(
                    {
                        "moment": moment,
                        "target_metric": target_metric,
                        "raw_metric": raw_metric,
                        "window_seconds": window_seconds,
                        "window_position": window_position,
                        "statistic": statistic,
                        "model_type": model_type,
                        "split_rule": "gx_test_id_mod_5_eq_0",
                        "train_size": int(train_mask.sum()),
                        "test_size": int(test_mask.sum()),
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "train_pearson": float(x_train.corr(y_train)),
                        "train_r2": float(
                            calculate_r2(y_train, train_predicted)
                        ),
                        "train_mean_absolute_error": float(
                            train_residual.abs().mean()
                        ),
                        "train_median_absolute_percentage_error": (
                            calculate_median_ape(y_train, train_predicted)
                        ),
                        "train_bias": float(train_residual.mean()),
                        "test_pearson": float(test_pearson),
                        "test_r2": float(calculate_r2(y_test, predicted)),
                        "test_mean_absolute_error": float(
                            residual.abs().mean()
                        ),
                        "test_median_absolute_percentage_error": (
                            calculate_median_ape(y_test, predicted)
                        ),
                        "test_bias": float(residual.mean()),
                        "test_residual_std": float(residual.std(ddof=1)),
                        "test_residual_p05": residual_quantiles.loc[0.05],
                        "test_residual_p25": residual_quantiles.loc[0.25],
                        "test_residual_median": residual_quantiles.loc[0.5],
                        "test_residual_p75": residual_quantiles.loc[0.75],
                        "test_residual_p95": residual_quantiles.loc[0.95],
                    }
                )

    return pd.DataFrame(score_rows)


def select_best_candidates(
    scores: pd.DataFrame,
) -> pd.DataFrame:
    """Selecciona un candidato por momento, variable y tipo de calibración."""

    selected: list[pd.DataFrame] = []
    for moment in ("rest", "at", "vo2_max"):
        for target_metric, raw_metrics in PRIORITY_RAW_CANDIDATES.items():
            for model_type in CALIBRATION_MODELS:
                candidates = scores[
                    scores["moment"].eq(moment)
                    & scores["target_metric"].eq(target_metric)
                    & scores["raw_metric"].isin(raw_metrics)
                    & scores["model_type"].eq(model_type)
                ].copy()
                if candidates.empty:
                    continue

                # Evita recomendar una ventana perfecta pero disponible solo
                # en una minoría de pruebas (especialmente para HR manual).
                candidates = candidates[
                    candidates["train_size"].ge(
                        0.8 * candidates["train_size"].max()
                    )
                    & candidates["test_size"].ge(
                        0.8 * candidates["test_size"].max()
                    )
                ].sort_values(
                    by=[
                        "train_r2",
                        "train_median_absolute_percentage_error",
                    ],
                    ascending=[False, True],
                )
                if not candidates.empty:
                    selected.append(candidates.head(1))

    if not selected:
        return pd.DataFrame(columns=scores.columns)
    return pd.concat(selected, ignore_index=True)


def print_best_candidates(
    best_candidates: pd.DataFrame,
) -> None:
    """Muestra un informe compacto de candidatos calibrados."""

    columns = [
        "moment",
        "target_metric",
        "raw_metric",
        "window_seconds",
        "window_position",
        "statistic",
        "model_type",
        "test_size",
        "slope",
        "intercept",
        "test_pearson",
        "test_r2",
        "test_mean_absolute_error",
        "test_median_absolute_percentage_error",
        "test_bias",
    ]
    if best_candidates.empty:
        print("Sin candidatos calibrables.")
        return
    print(
        best_candidates[columns].to_string(
            index=False,
            float_format=lambda value: f"{value:.4f}",
        )
    )


def build_evaluation_residuals(
    features: pd.DataFrame,
    best_candidates: pd.DataFrame,
) -> pd.DataFrame:
    """Materializa predicciones evaluadas para auditar residuos y magnitud."""

    rows: list[pd.DataFrame] = []
    for _, candidate in best_candidates.iterrows():
        selected = features[
            features["moment"].eq(candidate["moment"])
            & features["raw_metric"].eq(candidate["raw_metric"])
            & features["window_seconds"].eq(candidate["window_seconds"])
            & features["window_position"].eq(candidate["window_position"])
            & features["statistic"].eq(candidate["statistic"])
            & features["evaluation_set"].astype(bool)
        ].copy()
        target_column = f"pq_{candidate['target_metric']}"
        selected["raw_value"] = pd.to_numeric(
            selected["raw_value"], errors="coerce"
        )
        selected["observed"] = pd.to_numeric(
            selected[target_column], errors="coerce"
        )
        selected = selected[
            selected["raw_value"].notna()
            & selected["observed"].notna()
            & np.isfinite(selected["raw_value"])
            & np.isfinite(selected["observed"])
        ].copy()
        selected["predicted"] = (
            float(candidate["slope"]) * selected["raw_value"]
            + float(candidate["intercept"])
        )
        selected["residual"] = selected["predicted"] - selected["observed"]
        selected["absolute_percentage_error"] = (
            selected["residual"].abs()
            / selected["observed"].abs().where(
                selected["observed"].abs().gt(1e-12)
            )
            * 100.0
        )
        selected["target_metric"] = candidate["target_metric"]
        selected["model_type"] = candidate["model_type"]
        rows.append(
            selected[
                [
                    "gx_test_id",
                    "moment",
                    "target_metric",
                    "raw_metric",
                    "window_seconds",
                    "window_position",
                    "statistic",
                    "model_type",
                    "raw_value",
                    "observed",
                    "predicted",
                    "residual",
                    "absolute_percentage_error",
                ]
            ]
        )

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def calculate_magnitude_stability(
    residuals: pd.DataFrame,
) -> pd.DataFrame:
    """Resume sesgo y error por cuartil de magnitud observada."""

    if residuals.empty:
        return pd.DataFrame()

    group_columns = [
        "moment",
        "target_metric",
        "raw_metric",
        "window_seconds",
        "window_position",
        "statistic",
        "model_type",
    ]
    rows: list[dict[str, object]] = []
    for key, group in residuals.groupby(group_columns, sort=False):
        group = group.copy()
        group["magnitude_quartile"] = pd.qcut(
            group["observed"],
            q=4,
            labels=False,
            duplicates="drop",
        )
        for quartile, subset in group.groupby("magnitude_quartile"):
            rows.append(
                {
                    **dict(zip(group_columns, key)),
                    "magnitude_quartile": int(quartile) + 1,
                    "sample_size": len(subset),
                    "observed_min": subset["observed"].min(),
                    "observed_max": subset["observed"].max(),
                    "mean_absolute_error": subset["residual"].abs().mean(),
                    "median_absolute_percentage_error": subset[
                        "absolute_percentage_error"
                    ].median(),
                    "bias": subset["residual"].mean(),
                    "residual_std": subset["residual"].std(ddof=1),
                }
            )
    return pd.DataFrame(rows)


def parse_arguments() -> argparse.Namespace:
    """Lee las rutas del análisis."""

    parser = argparse.ArgumentParser(
        description=(
            "Evalúa calibraciones lineales entre "
            "señales GX y Patient Query."
        )
    )

    parser.add_argument(
        "--features-path",
        type=Path,
        default=DEFAULT_FEATURES_PATH,
    )

    parser.add_argument(
        "--output-path",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
    )

    return parser.parse_args()


def main() -> None:
    """Ejecuta la evaluación de calibraciones."""

    arguments = parse_arguments()

    features = pd.read_parquet(
        arguments.features_path,
    )

    print(f"Filas de características: {len(features):,}")
    print(
        "Pruebas diferentes: "
        f"{features['gx_test_id'].nunique():,}"
    )

    scores = calculate_scores(features)

    arguments.output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scores.to_csv(
        arguments.output_path,
        index=False,
        encoding="utf-8",
    )

    best_candidates = select_best_candidates(scores)
    best_candidates_path = arguments.output_path.with_name(
        "ergoespirometry_best_candidates.csv"
    )
    best_candidates.to_csv(
        best_candidates_path,
        index=False,
        encoding="utf-8",
    )
    residuals = build_evaluation_residuals(features, best_candidates)
    residuals_path = arguments.output_path.with_name(
        "ergoespirometry_evaluation_residuals.parquet"
    )
    residuals.to_parquet(residuals_path, index=False)
    magnitude_stability = calculate_magnitude_stability(residuals)
    magnitude_stability_path = arguments.output_path.with_name(
        "ergoespirometry_magnitude_stability.csv"
    )
    magnitude_stability.to_csv(
        magnitude_stability_path,
        index=False,
        encoding="utf-8",
    )
    print_best_candidates(best_candidates)

    print(
        "\nResultados guardados en: "
        f"{arguments.output_path}"
    )
    print(f"Resumen de candidatos guardado en: {best_candidates_path}")
    print(f"Residuos de evaluación guardados en: {residuals_path}")
    print(f"Estabilidad por magnitud guardada en: {magnitude_stability_path}")


if __name__ == "__main__":
    main()
