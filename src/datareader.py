from massive.rest.futures import FuturesAgg
import json
from typedefs import Limit
from pprint import pprint
from collections import defaultdict
import pandas as pd

'''
 TODO: 
     (1) Command Line arg for tickers to include. --tickers=[...]
     (2) Fix file naming data/{ticker}.csv
     (3) add a claude skills.md file
        skill = client.beta.skills.create(
                files=[b"Example data"],
        )
'''

def read_data(client, massive_api: str, tickers: list[str], limit: Limit, out_file: str) -> None:
    # TODO: Use all tickers in tickers
    mesu6_aggs: list[FuturesAgg | bytes] = []

    for a in client.list_futures_aggregates(
        ticker="MESU6",
        resolution="15min",
        window_start_gte="2026-07-06",
        sort="window_start.desc",
        limit=limit.limit,
    ):
        mesu6_aggs.append(a)

    return mesu6_aggs

def make_csv(data: list[FuturesAgg | bytes]) -> None:
    d = defaultdict(lambda: [])

    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)

    df = pd.DataFrame(d)
    print(df.head(10))
    df.to_csv("data.csv", index=False)


