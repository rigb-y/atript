from massive.rest.futures import FuturesAgg
import json
from typedefs import Limit
from collections import defaultdict
import pandas as pd
from pprint import pprint
from collections.abc import Generator
from datetime import datetime

'''
Fetches OHLC data from Massive.com.

@param client A massive Restclient instance.
@param tickers A list of futures tickers.
@param limit A limit on the amount of.
@param window_start The start time of the candlesticks. A Unix timestamp or YYYY-MM-DD value
@return A list of 
'''
def fetch_data(client, tickers: list[str], limit: Limit, window_start: int | str) -> dict[list[FuturesAgg | bytes]]:
    data: dict[str, Generator[FuturesAgg]] = dict()

    if (isinstance(window_start, str)):
        time: list[str] = window_start.strip().split('-')
        time = datetime(*time)

    for ticker in tickers:
        aggregates: list[FuturesAgg] = client.list_futures_aggregates(
                ticker=ticker,
                resolution="15min",
                window_start_gte=window_start,
                sort="window_start.desc",
                limit=limit.limit,
                )
        data[ticker] = aggregates
    return data


def make_parquet(data: dict[str,Generator[FuturesAgg]]) -> None:

    d = defaultdict(lambda: [])

    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)
    df = pd.DataFrame(d)
    df.to_parquet("data.csv", index=False)

