from massive.rest.futures import FuturesAgg
import json
from typedefs import Limit

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

    to_json: dict[str, list[dict[str, str]]] = {}
    for ticker in tickers:
        to_json[ticker] = []

    for agg in mesu6_aggs:
        to_json[agg.ticker].append(agg.__dict__) 

    with open(out_file, "w") as file:
        json.dump(to_json, file)
