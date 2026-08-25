#!usr/bin/python3
from datareader import fetch_data, load_last_n, load_prior_data, fetch_latest, fetch_lookback, fetch_range
from typedefs import MassiveParameters
from pathlib import Path
from collections import defaultdict
import pandas as pd
import os
from massive import RESTClient 
from collections import defaultdict
from itertools import chain
from argparse import ArgumentParser
from atript_secrets import (
                     get_massive_api_key,
                     get_account_id,
                     get_bucket_name,
                     get_access_key_id,
                     get_secret_access_key, get_s3_api_key,
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
        "CLAUDE_KEY":  get_claude_key() }

MASSIVE_CLIENT = RESTClient(KEYS["MASSIVE_API"]);

# The number of prior observations needed to compute the indicators for new data.
INDICATOR_LOOKBACK = 14


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

    if not (Path("data") / args.ticker).exists():
        os.mkdir(f"data/{args.ticker}")

    massive_parameters: MassiveParameters = {
        # "limit": 100,
        "sort": "window_start.desc", 
        "resolution": args.resolution,
        "ticker": args.ticker
    }

    match args.command:
        case "latest":
            data = fetch_latest(massive_parameters, MASSIVE_CLIENT)
        case "lookback":
            data = fetch_lookback(args.period, args.depth, massive_parameters, MASSIVE_CLIENT)
        case "range":
            data = fetch_range(args.begin, args.end, massive_parameters, MASSIVE_CLIENT)
        case _:
            return

    
    # Check if data is empty.
    try:
        first = next(iter(data)) 
    except StopIteration:
        print("No history for this ticker. Use --lookback or --range instead" if args.latest else "No data Returned.")
        return

    data = chain((first,), iter(data))

    # Convert data into DataFrame
    d: defaultdict[str, list] = defaultdict(lambda: [])
    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)
    df: pd.DataFrame = pd.DataFrame(d)

    print(f"Fetched {df.shape[0]:,} observations for {args.ticker}")

    prior_n = load_last_n(args.ticker, INDICATOR_LOOKBACK)

    # Concatenate new data with the prior n observations needed to calculate indicators.
    if (prior_n is not None):
        df = pd.concat([df, prior_n], ignore_index=True)

   # df = preprocess(df)

   # Write data to parquete files.
    dates = pd.Series(df['session_end_date'], dtype="datetime64[ns]")
    for day, rows in df.groupby(dates.dt.date):
        prior: pd.DataFrame | None = load_prior_data(args.ticker, day, day)

        if (prior is not None):
            rows = pd.concat([rows, prior], ignore_index=True).drop_duplicates(subset="window_start")
        path = f"data/{args.ticker}/{args.ticker}-{day}.parquet"
        rows.to_parquet(path, index=False)
        print(f"Wrote {path} ({rows.shape[0]:,} rows)")


if __name__ == '__main__':
    main()
