from massive.rest.futures import FuturesAgg
import json
from typedefs import Limit
from pprint import pprint
from collections import defaultdict
import pandas as pd
from names import get_output_name

'''
 TODO: 
     (3) add a claude skills.md file
        skill = client.beta.skills.create(
                files=[b"Example data"],
        )
'''

def read_data(client, tickers: list[str], limit: Limit) -> dict[str, list[FuturesAgg | bytes]]:
    ticker_data: dict[str, list[FuturesAgg | bytes]] = defaultdict(lambda: [])
    for ticker in tickers:
        for a in client.list_futures_aggregates(
                ticker=ticker,
                resolution="15min",
                window_start_gte="2026-07-06",
                sort="window_start.asc",
                limit=limit.limit,
                ):
            ticker_data[ticker].append(a)

    return ticker_data

def make_csv(ticker: str, data: list[FuturesAgg | bytes]) -> None:
    d = defaultdict(lambda: [])
    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)

    df = pd.DataFrame(d)
    df = df.drop(labels=["settlement_price"], axis=1)
    f_name: str = get_output_name(ticker)
    df.to_csv(f"{f_name}.csv", index=False)

