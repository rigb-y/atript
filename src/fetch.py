#!usr/bin/python3
from datetime import date, datetime, timezone
from dateutil.relativedelta import relativedelta
from datareader import fetch_data, load_last_n, load_prior_data, fetch_latest, fetch_lookback, fetch_range
from typedefs import Limit, MassiveParameters
from copy import copy
from pathlib import Path
from collections import defaultdict
import pandas as pd
import os
from massive import RESTClient 
from collections import defaultdict
from massive.rest.futures import FuturesAgg
import numpy as np
from collections.abc import Generator
from argparse import ArgumentParser
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
        "AWS_ACCESS_KEY" : get_access_key_id(), "AWS_SECRET_ACCESS_KEY" : get_secret_access_key(), "MASSIVE_API" : get_massive_api_key(), "CLAUDE_KEY":  get_claude_key()
}

TICKERS: list[str] = ["MESU6"]
MASSIVE_CLIENT = RESTClient(KEYS["MASSIVE_API"]);



# The number of prior observations needed to compute the indicators for new data.
INDICATOR_LOOKBACK = 14

def preprocess(data: pd.DataFrame) -> pd.DataFrame:

    data['returns'] = get_returns(data['close'])
    data['rsi'] = rsi(data['close'], 14)

    data = data.drop(['settlement_price', 'open', 'high', 'low','close'], axis=1)
    return data


'''
Computes the returns for a sequence of candlestick closes.

@param close An array of closing values for candlesticks.

@Note Returns are the relative change in closing value between observation k and k + 1.
@Note Assumes close is ordered by most recent observation to least recent observation.
'''
def get_returns(close: pd.Series) -> pd.Series:
    return pd.Series(-np.diff(close) / close[1:]).shift(1)

'''
Computes relative strength index for an array of price history.

@param prices An array of price history.
@param n The number of candlesticks to use in the computations.
'''
def rsi(prices: pd.Series, n: int) -> np.ndarray:
    ret: np.ndarray = np.full(len(prices), np.nan)
    diff: np.ndarray = -np.diff(prices)

    for i in range(len(prices) - n):
        window: np.ndarray = diff[i:i + n]

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

    parser = ArgumentParser()
    parser.add_argument("-t", "--ticker", type=str, required=True)
    parser.add_argument("-r", "--resolution", type=str, required=True)

    subparsers = parser.add_subparsers(dest="command", required=True)

    latest_parser = subparsers.add_parser("latest")
    
    lookback_parser = subparsers.add_parser("lookback")
    lookback_parser.add_argument("--period", choices=["days","weeks","months","years"], required=True)
    lookback_parser.add_argument("--depth", required=True, type=int)

    range_parser = subparsers.add_parser("range")
    range_parser.add_argument("--begin", required=True)
    range_parser.add_argument("--end", required=True)

    args = parser.parse_args()

    ticker = args.ticker
    if not (Path("data") / ticker).exists():
        os.mkdir(f"data/{ticker}")

    massive_parameters: MassiveParameters = {
        # "limit": 100,
        "sort": "window_start.desc", 
        "resolution": args.resolution,
        "ticker": ticker
    }

    data: Generator[FuturesAgg | bytes] | None = None
    match args.command:
        case "latest":
            data = fetch_latest(massive_parameters, MASSIVE_CLIENT)
        case "lookback":
            data = fetch_lookback(args.period, args.depth, massive_parameters, MASSIVE_CLIENT)
        case "range":
            data = fetch_range(args.begin, args.end, massive_parameters, MASSIVE_CLIENT)

    if (data is None):
        return


    # Convert data into DataFrame
    d: defaultdict[str, list] = defaultdict(lambda: [])
    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)
    df: pd.DataFrame = pd.DataFrame(d)

    print(f"Data fetch was successful. Got {df.shape[0]} observations")

    prior_n = load_last_n(ticker, INDICATOR_LOOKBACK)

    # Concatenate new data with the prior n observations needed to calculate indicators.
    if (prior_n is not None):
        df = pd.concat([df, prior_n], ignore_index=True)

    df = preprocess(df)

   # Write data to parquete files.
    dates = pd.Series(df['session_end_date'], dtype="datetime64[ns]")
    for day, rows in df.groupby(dates.dt.date):
        prior: pd.DataFrame | None = load_prior_data(ticker, day, day)

        if (prior is not None):
            rows = pd.concat([rows, prior], ignore_index=True).drop_duplicates(subset="window_start")
        rows.to_parquet(f"data/{ticker}/{ticker}-{day}.parquet", index=False)


if __name__ == '__main__':
    main()
