#!usr/bin/python3
from datareader import fetch_data, make_parquet
from typedefs import Limit
from pathlib import Path
from collections import defaultdict
import pandas as pd
import os
from names import get_output_name 
from massive import RESTClient 
from dataclasses import asdict
from massive.rest.futures import FuturesAgg
from numpy.typing import ArrayLike
import numpy as np
from typing import Any
from collections.abc import Generator, Sequence
from atript_secrets import (
                     get_massive_api_key,
                     get_account_id,
                     get_bucket_name,
                     get_access_key_id,
                     get_secret_access_key,
                     get_s3_api_key,
                     get_claude_key
                     )

# VWAP, RSI, EMA, ATR, bollinger Bands (20, 2\sigma), MACD

KEYS: dict[str,str | None] = {
        "R2_ACCOUNT_ID" : get_account_id(),
        "R2_BUCKET" : get_bucket_name(),
        "ENDPOINT_URL" : get_s3_api_key(),
        "AWS_ACCESS_KEY" : get_access_key_id(),
        "AWS_SECRET_ACCESS_KEY" : get_secret_access_key(),
        "MASSIVE_API" : get_massive_api_key(),
        "CLAUDE_KEY":  get_claude_key()
}

TICKERS: list[str] = ["MESU6"]
MASSIVE_CLIENT = RESTClient(KEYS["MASSIVE_API"]);

def preprocess(data: dict[str, Generator[FuturesAgg]]) -> pd.DataFrame:
    flat_data: list[dict] = [e.__dict__ for ticker in data for e in data[ticker]]
    d = {
            key: [d[key] for d in flat_data] 
            for key in flat_data[0].keys()
    }
    df = pd.DataFrame(d).sort_values(by='window_start')

    df['returns'] = get_returns(df['close'])
    df['rsi'] = rsi(df['close'], 14)

    df = df.drop(['settlement_price', 'session_end_date', 'open', 'high', 'low','close'], axis=1)
    return df


'''
Computes the returns for a sequence of candlestick closes.

@param close An array of closing values for candlesticks.

@Note Returns are the relative change in closing value between observation k and k + 1.
'''
def get_returns(close: pd.Series) -> pd.Series:
    return pd.Series(np.diff(close) / close[:-1]).shift(1)

'''
Computes relative strength index for an array of price history.

@param prices An array of price history.
@param n The number of candlesticks to use in the computations.
'''
def rsi(prices: pd.Series, n: int) -> np.ndarray:
    ret: np.ndarray = np.full(len(prices), np.nan)
    diff: np.ndarray = np.diff(prices)

    for i in range(n, len(prices)):
        window: np.ndarray = diff[i - n:i]

        avg_gain: float = sum(window[window > 0]) / n
        avg_loss: float = -sum(window[window < 0]) / n 

        if avg_loss == 0 and avg_gain == 0:
            rsi = 50.0
        elif avg_loss == 0:
            rsi = 100.0
        else:
            rs: float = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        ret[i] = rsi
    return ret

def bollinger_bands():
    ...

def msi():
    ...
def vwap():
    ...

def main() -> None: 

    if not Path("data").exists():
        os.mkdir("data")

    pq: pd.DataFrame | None = None

    # Retrieve stored data.
    if (Path("Data/data.parquet").exists()):
        pq = pd.read_parquet("data/data.parquet")

    massive_parameters = {
            "limit": Limit(100), 
            "sort": "window_start.asc", 
            "resolution": "15min",
    }

    next_window_start: int | None = pq['window_start'].iloc[-1] + 1 if pq is not None else None
    if (next_window_start): 
        massive_parameters["window_start"] = next_window_start

    # Fetch new data.
    data: dict[str , Generator[FuturesAgg]] = fetch_data(MASSIVE_CLIENT, TICKERS, massive_parameters)

    df: pd.DataFrame = preprocess(data)
    print(df.head(20))

    # print(dir(next(data["MESU6"])))
    # print(list((next(data["MESU6"])).__dict__.keys()))


    # print(list(data["MESU6"])[:5])
    # make_csv(datak)

    # with open(file, 'rb') as f:
    #     file_upload = client.beta.files.upload(
    #             file=(Path(file).name, f, "application/json")
    #     )

if __name__ == '__main__':
    main()
