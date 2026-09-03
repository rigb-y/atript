import pandas as pd  # requires: pip install 'pandas[pyarrow]'
from pathlib import Path
from chronos import Chronos2Pipeline
from futures_pipeline.config import PROCESSED_DATA_DIR
from futures_pipeline.datareader import load_prior_data
from pathlib import Path


def chronos(model_dir: str | Path, ticker: str, target: str = 'close', hf_token: str | None = None) -> pd.DataFrame:
    if not isinstance(model_dir, Path):
        model_dir = Path(model_dir)

    pipeline = load_chronos(model_dir, local_weights=True, hf_token=hf_token)

    data_path = f"{PROCESSED_DATA_DIR}/{ticker}"

    # Load historical target values and past values of covariates
    data: pd.DataFrame | None = load_prior_data(Path(data_path), ticker)

    if data is None:
        raise RuntimeError("No data.")

    covariates: list = ["volume", "rsi", "VWAP", "wma", "sma", "percent_b", "ema"]

    context_df = (
        data[["model_timestamp", "ticker", target, *covariates]]
        .sort_values("model_timestamp")
        .reset_index(drop=True)
    )

    # Generate predictions with covariates
    pred_df = pipeline.predict_df(
        context_df,
        prediction_length=10,  # Number of steps to forecast
        quantile_levels=[0.1, 0.5, 0.9],  # Quantile for probabilistic forecast
        id_column="ticker",  # Column identifying different time series
        timestamp_column="model_timestamp",  # Column with datetime information
        target=target,  # Column(s) with time series values to predict
    )
    return pred_df


def load_chronos(model_dir: Path, local_weights: bool = False, hf_token=None):
    pipeline: Chronos2Pipeline | None = None
    if local_weights:
        try:
            pipeline = Chronos2Pipeline.from_pretrained(
                model_dir, device_map="cuda", local_files_only=True
            )
        except Exception as e:
            print(f"Error occured loading model from disk: {str(e)}")

    if pipeline is None:
        pipeline = Chronos2Pipeline.from_pretrained(
            "amazon/chronos-2", device_map="cuda", token=hf_token
        )
        pipeline.save_pretrained(model_dir)

    return pipeline
