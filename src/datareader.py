from massive.rest.futures import FuturesAgg
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

@api-param limit A limit on the amount of candlesticks to fetch.
@api-param window_start The start time of the candlesticks. A Unix timestamp or YYYY-MM-DD value.
@api-param resolution The size of each aggregate candle, specified as a number followed 
                  by a unit: sec, min, hour, week, month, quarter, year.
@api-param sort Sort results by field and direction using dotted notation e.g. ticker.asc, name.desc

@return  OHLC data for each provided ticker.
'''
def fetch_data(client, tickers: list[str], **api_parameters) -> dict[str, Generator[FuturesAgg | bytes]]:
    data: dict[str, Generator[FuturesAgg]] = dict()

    if ((window_start := api_parameters.get('window_start')) and isinstance(window_start, str)):
        time = [int(t) for t in window_start.strip().split('-')]
        dt: datetime = datetime(*time)
        api_parameters['window_start'] = int(dt.timestamp())

    for ticker in tickers:
        aggregates: list[FuturesAgg] = client.list_futures_aggregates(ticker=ticker, **api_parameters)
        data[ticker] = aggregates
    return data

def make_parquet(data: dict[str,Generator[FuturesAgg]]) -> None:

    d = defaultdict(lambda: [])

    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)
    df = pd.DataFrame(d)
    df.to_parquet("data.csv", index=False)

