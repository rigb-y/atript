import pandas as pd  # requires: pip install 'pandas[pyarrow]'
from pathlib import Path
from chronos import Chronos2Pipeline
from .config import PROCESSED_DATA_DIR
from .typedefs import EvaluationResult
from futures_pipeline.datareader import load_prior_data
from pathlib import Path
import numpy as np


def run_model(
    ticker,
    target,
    pred_length,
    hf_token=None,
    model_dir=None,
    store_weights: bool = False,
    eval: bool=False
) -> None:
    pipeline = load_chronos(model_dir, store_weights=store_weights, hf_token=hf_token)

    quantiles = [0.1, 0.5, 0.9]

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

    if eval:
        initial_train_size = int(context_df.shape[0] * .80)
        e = walk_forward_evaluate(pipeline, context_df, pred_length, pred_length,initial_train_size, target, quantiles)
        eval_results: EvaluationResult = evaluate(pred_df, eval_df, target, quantiles)

        print(f"MAE: {eval_results.mae:.8f}")
        print(f"Baseline MAE: {eval_results.baseline_mae:.8f}")
        print(f"MAE Skill: {eval_results.mae_skill:.2%}")
        print(f"RMSE: {eval_results.rmse:.8f}")
        print(f"Directional accuracy: {eval_results.directional_accuracy:.8f}")


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
    for end in range(initial_train_size, context_df.shape[0], step):
        pred_df = predict_chronos(pipeline, context_df[: end], horizon, target, quantiles)
        eval_df = context_df[['ticker','model_timestamp', target]].iloc[end: end + horizon]
        results.append(pred_df.merge(
                eval_df,
                on=['ticker','model_timestamp'],
                how="inner",
                validate="one_to_one"
        ))

    return pd.concat(results, ignore_index=True)

def evaluate(
    pred_df: pd.DataFrame, eval_df: pd.DataFrame, target: str, quantiles: list[float]
) -> EvaluationResult:

    evaluation = pred_df.merge(
        eval_df[["ticker", "model_timestamp", target]],
        on=["ticker", "model_timestamp"],
        how="inner",
        validate="one_to_one",
    )

    actual = evaluation[target]
    predicted = evaluation["predictions"]
    error = actual - predicted

    mae: float = error.abs().mean()
    rmse: float = error.pow(2).mean() ** 0.5

    # TODO: hardcoded to target = returns.
    directional_accuracy = (np.sign(predicted) == np.sign(actual)).mean()

    # Predicting every future return is zero as a baseline for mae.
    baseline_mae = actual.abs().mean()

    # Measures how much the model improves upon the baseline.

    mae_skill = 1 - mae / baseline_mae

    return EvaluationResult(
        pred_df, eval_df, mae, baseline_mae, mae_skill, rmse, directional_accuracy, {}
    )

    # TODO: Write loss function
    for quantile in quantiles:
        loss = pinball_loss(evaluation[quantile], evaluation[target], quantile)
        print(loss)
