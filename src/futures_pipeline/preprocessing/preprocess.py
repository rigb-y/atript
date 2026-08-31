import pandas as pd
from ..datareader import load_prior_data
from pathlib import Path
from ..config import PROCESSED_DATA_DIR, RAW_DATA_DIR, load_settings, Settings
from .indicators import smoothed_rsi, percent_b, get_returns, sma, ema, msi, vwap, wma, vwap


def preprocess(ticker: str) -> None:
    processed_path: Path = Path(PROCESSED_DATA_DIR) / ticker
    raw_path: Path = Path(RAW_DATA_DIR) / ticker
    settings: Settings = load_settings()

    processed_path.mkdir(exist_ok=True, parents=True)

    data: pd.DataFrame | None = load_prior_data(raw_path, ticker)

    if data is None:
        print(f"No data available for {ticker}.")
        return

    print(f"Processing {data.shape[0]} records for {ticker}.")

    # prior_n: pd.DataFrame | None = load_last_n(
    #     raw_path, ticker, settings.indicator_lookback
    # )

    # Concatenate new data with the prior n observations needed to calculate indicators.
    # if prior_n is not None:
    #     data = pd.concat([data, prior_n], ignore_index=True)

    data = (
        data.drop_duplicates(subset=["window_start"])
        .sort_values("window_start", ascending=False, kind="stable")
        .dropna()
        .reset_index(drop=True)
    )

    data["returns"] = get_returns(data["close"])

    data["rsi"] = smoothed_rsi(data["close"])
    data["percent_b"] = percent_b(data["close"])
    data["sma"] = sma(data["close"])
    data["wma"] = wma(data["close"])
    data["VWAP"]= vwap(data)
    print(data)

    # data = data.drop(["open", "high", "low", "close"], axis=1)
    # print(data)

    # Write data to parquete files.
    dates = pd.Series(data["session_end_date"], dtype="datetime64[ns]")
    for day, rows in data.groupby(dates.dt.date):
        path: str = f"{PROCESSED_DATA_DIR}/{ticker}/{ticker}-{day}.parquet"
        prior: pd.DataFrame | None = load_prior_data(processed_path, ticker, day, day)
        if prior is not None:
            rows = pd.concat([rows, prior], ignore_index=True).drop_duplicates(
                subset="window_start"
            )
        rows = rows.sort_values(
            "window_start", ascending=False, kind="stable"
        ).reset_index(drop=True)
        rows.to_parquet(path, index=False)
        print(f"Wrote {path} ({rows.shape[0]:,} rows)")
