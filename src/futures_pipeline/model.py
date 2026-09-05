import pandas as pd  # requires: pip install 'pandas[pyarrow]'
from pathlib import Path
from chronos import Chronos2Pipeline
from .config import PROCESSED_DATA_DIR
from .typedefs import EvaluationResult
from futures_pipeline.datareader import load_prior_data
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def run_model(
    ticker,
    target,
    pred_length,
    quantiles,
    prediction_interval,
    hf_token=None,
    model_dir=None,
    store_weights: bool = False,
    eval: bool=False
) -> None:
    pipeline = load_chronos(model_dir, store_weights=store_weights, hf_token=hf_token)

    # Load historical target values and past values of covariates
    data: pd.DataFrame | None = load_prior_data(PROCESSED_DATA_DIR / ticker, ticker)

    if data is None:
        raise RuntimeError("No data.")

    covariates: list = ["volume", "rsi", "VWAP", "wma", "sma", "percent_b", "ema"]

    context_df = (
        data[["model_timestamp", "ticker", target, *covariates]]
        .sort_values("model_timestamp")
        .reset_index(drop=True)
    )

    # TODO: group mae, directional accuracy, pinball loss, and interval coverage by horizon.


    if eval:
        initial_train_size = int(context_df.shape[0] * .80)
        e = walk_forward_evaluate(pipeline, context_df, pred_length, pred_length,initial_train_size, target, quantiles)
        eval_results: EvaluationResult = evaluate(e, context_df.iloc[:initial_train_size][target], target, quantiles, prediction_interval)

        print(f"=== POINT FORECAST METRICS ===")
        print(f"MAE: {eval_results.mae:.8f}")
        print(f"Baseline MAE: {eval_results.baseline_mae:.8f}")
        print(f"MAE Skill: {eval_results.mae_skill:.2%}")
        print(f"RMSE: {eval_results.rmse:.8f}")
        print(f"Directional accuracy: {eval_results.directional_accuracy:.8f}\n")

        loss_skill = {
                q: 1 - eval_results.loss[q] / eval_results.baseline_loss[q]
                if eval_results.baseline_loss[q] != 0 else np.nan
                for q in quantiles
        }

        print(f"=== QUANTILE LOSS ===")
        for t in zip(
            eval_results.loss.items(),
            eval_results.baseline_loss.items(),
            loss_skill.items(),
        ):
            (quantile, avg_loss), (_, baseline_loss), (_, loss_skill) = t
            print(f"avg loss for {quantile:.2%}th quantile: {avg_loss:.10f}")
            print(f"avg baseline loss for {quantile:.2%}th quantile: {baseline_loss:.10f}")
            print(f"loss skill for {quantile:.2%}th quantile: {loss_skill:.2%}\n")

        print(f" === Quantile Calibration === ")
        for q, v in eval_results.quantile_calibration.items():
            print(f"q={q}: {v}")

        print(f" \n=== Calibration Error === ")
        for q, v in eval_results.calibration_error.items():
            print(f"q={q}: {v}")

        print(f"\n=== PREDICTION INTERVAL ===")
        print(f"Mean PI coverage: {eval_results.pi_coverage:.2%}")
        print(f"Nominal coverage: {eval_results.nominal_coverage:.2%}")
        print(f"Mean PI width: {eval_results.mean_interval_width:.8f}")

    else:
        pred_df = predict_chronos(pipeline, context_df, pred_length, target, quantiles)

        ts_context = context_df.set_index('model_timestamp')[target].tail(256)
        ts_pred = pred_df.set_index("model_timestamp")

        ts_context.plot(label="historical data", figsize=(12,3))
        ts_pred['predictions'].plot(label="forecast")

        plt.fill_between(
                ts_pred.index,
                ts_pred["0.1"],
                ts_pred["0.9"],
                alpha=0.7,
                label="prediction interval"
        )
        plt.legend()
        plt.show()


def predict_chronos(
    pipeline,
    context_df,
    pred_length: int,
    target: str,
    quantiles,
) -> pd.DataFrame:

    # Generate predictions with covariates
    pred_df = pipeline.predict_df(
        context_df,
        prediction_length=pred_length,  # Number of steps to forecast
        quantile_levels=quantiles,  # Quantile for probabilistic forecast
        id_column="ticker",  # Column identifying different time series
        timestamp_column="model_timestamp",  # Column with datetime information
        target=target,  # Column(s) with time series values to predict
    )
    return pred_df


def load_chronos(model_dir: Path | None = None, store_weights=False, hf_token=None):
    pipeline: Chronos2Pipeline | None = None

    if model_dir is not None and model_dir.exists():
        try:
            pipeline = Chronos2Pipeline.from_pretrained(
                model_dir, device_map="cuda", local_files_only=True
            )
        except (OSError, ValueError) as e:
            print(f"Error occured while loading chronos-2 from {model_dir}: {str(e)}")

    if pipeline is None:
        pipeline = Chronos2Pipeline.from_pretrained(
            "amazon/chronos-2", device_map="cuda", token=hf_token
        )

    if store_weights:
        assert model_dir is not None, "model_dir is required when store_weights=True"
        pipeline.save_pretrained(model_dir)

    return pipeline

"""
pinball loss function.
"""
def pinball_loss(y_true, y_pred, quantile):
    return np.where(
        y_true >= y_pred,
        quantile * (y_true - y_pred),
        (quantile - 1) * (y_true - y_pred),
    )

def walk_forward_evaluate(pipeline, context_df, step, horizon, initial_train_size, target, quantiles):
    results: list[pd.DataFrame] = []
    last = context_df.shape[0] - horizon
    for window_len in range(initial_train_size, last + 1, step):
        pred_df = predict_chronos(pipeline, context_df[: window_len], horizon, target, quantiles)
        eval_df = context_df[['ticker','model_timestamp', target]].iloc[window_len: window_len + horizon]
        results.append(pred_df.merge(
                eval_df,
                on=['ticker','model_timestamp'],
                how="inner",
                validate="one_to_one"
        ))

    return pd.concat(results, ignore_index=True)

def evaluate(
        eval: pd.DataFrame, hold_out_set: pd.Series, target: str, quantiles: list[float], prediction_interval: tuple[float, float]
) -> EvaluationResult:

    actual = eval[target]
    predicted = eval["predictions"]
    error = actual - predicted

    mae: float = error.abs().mean()
    rmse: float = error.pow(2).mean() ** 0.5

    # TODO: hardcoded to target = returns.
    directional_accuracy = (np.sign(predicted) == np.sign(actual)).mean()

    # Predicting every future return is zero as a baseline for mae.
    baseline_mae = actual.abs().mean()

    # Measures how much the model improves upon the baseline.

    mae_skill = 1 - mae / baseline_mae

    df = eval.set_index("model_timestamp")

    loss: dict[float, float] = {}
    for quantile in quantiles:
        loss[quantile] = pinball_loss(eval[target], eval[str(quantile)], quantile).mean()

    baseline_loss: dict[float, float] = {}

    # Baseline for quantiles.
    for q in quantiles:
        # Use a zero-return baseline for median.
        if q == 0.5:
            baseline_value = 0
        # Use a q-quantile computed from history.
        else:
            baseline_value = hold_out_set.quantile(q)

        baseline_loss[q] = pinball_loss(actual, np.full(len(actual), baseline_value), q).mean()

    lower_bound, upper_bound = prediction_interval
    pi_coverage: float = ((eval[str(lower_bound)] <= eval[target]) & (eval[target] <= eval[str(upper_bound)])).mean()
    nominal_coverage = upper_bound - lower_bound
    mean_interval_width = (eval[str(upper_bound)] - eval[str(lower_bound)]).mean()

    # Ratio of the amount of actual values below its prediction.
    quantile_calibration: dict[float, float] = {
            q: (actual <= eval[str(q)]).mean()
            for q in quantiles
    }
    calibration_error: dict[float, float] = {
            q: quantile_calibration[q] - q
            for q in quantiles
    }


    return EvaluationResult (
        df['predictions'], 
        df['returns'], 
        mae, 
        baseline_mae, 
        mae_skill, 
        rmse, 
        directional_accuracy, 
        loss, 
        baseline_loss,
        pi_coverage,
        nominal_coverage,
        mean_interval_width,
        quantile_calibration,
        calibration_error,
    )
