#!usr/bin/python3
from .datareader import (
    load_prior_data,
    fetch_latest,
    fetch_lookback,
    fetch_range,
)
from typedefs import MassiveParameters
from pathlib import Path
from collections import defaultdict
import pandas as pd
from itertools import chain
from massive_client import create_massive_client
from .config import load_settings, Settings, RAW_DATA_DIR
from .cli import create_parser
from .validate import validate_data

# VWAP, RSI, EMA, ATR, bollinger Bands (20, 2\sigma), MACD

def main() -> None:

    settings: Settings = load_settings()
    massive_client = create_massive_client(settings.massive_api_key)

    parser = create_parser()
    args = parser.parse_args()

    Path(f"{RAW_DATA_DIR}/{args.ticker}").mkdir(parents=True, exist_ok=True)

    massive_parameters: MassiveParameters = {
        # "limit": 100,
        "sort": "window_start.desc",
        "resolution": (
            args.resolution
            if getattr(args, "resolution")
            else settings.default_resolution
        ),
        "ticker": args.ticker,
    }

    match args.command:
        case "latest":
            data = fetch_latest(massive_parameters, massive_client)
        case "lookback":
            data = fetch_lookback(
                args.period, args.depth, massive_parameters, massive_client
            )
        case "range":
            data = fetch_range(args.begin, args.end, massive_parameters, massive_client)
        case _:
            return

    # Check if data is empty.
    try:
        first = next(iter(data))
    except StopIteration:
        return

    data = chain((first,), data)
    data = validate_data(data)

    # Convert data into DataFrame
    d: defaultdict[str, list] = defaultdict(lambda: [])
    for futuresagg in data:
        for k, v in (vars(futuresagg)).items():
            d[k].append(v)
    df: pd.DataFrame = pd.DataFrame(d)

    print(f"Fetched {df.shape[0]:,} observations for {args.ticker}")
    print(df.head())

    # prior_n = load_last_n(args.ticker, settings.indicator_lookback)

    # Concatenate new data with the prior n observations needed to calculate indicators.
    # if (prior_n is not None):
    #     df = pd.concat([df, prior_n], ignore_index=True)

    # df = preprocess(df)

    # Write data to parquete files.
    dates = pd.Series(df["session_end_date"], dtype="datetime64[ns]")
    for day, rows in df.groupby(dates.dt.date):
        prior: pd.DataFrame | None = load_prior_data(args.ticker, day, day)

        if prior is not None:
            rows = pd.concat([rows, prior], ignore_index=True).drop_duplicates(
                subset="window_start"
            )

        path: str = f"{RAW_DATA_DIR}/{args.ticker}/{args.ticker}-{day}.parquet"
        rows.to_parquet(path, index=False)
        print(f"Wrote {path} ({rows.shape[0]:,} rows)")


if __name__ == "__main__":
    main()
