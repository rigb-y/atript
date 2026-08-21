from massive.rest.futures import FuturesAgg
from typedefs import Limit
from collections import defaultdict
import pandas as pd
from pprint import pprint
from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from datetime import date

'''
Fetches OHLC data from Massive.com.

@param client A massive Restclient instance.
@param tickers A list of futures tickers.

@api-param limit The number of results to return per page.
@api-param window_start The start time of the candlesticks. A Unix timestamp or YYYY-MM-DD value.
@api-param resolution The size of each aggregate candle, specified as a number followed 
                  by a unit: sec, min, hour, week, month, quarter, year.
@api-param sort Sort results by field and direction using dotted notation e.g. ticker.asc, name.desc

@return  OHLC data for each provided ticker.
'''
def fetch_data(client,  fetch_parameters) -> Generator[FuturesAgg | bytes]:
    if ((window_start := fetch_parameters.get('window_start')) and isinstance(window_start, str)):
        time: list[int] = [int(t) for t in window_start.strip().split('-')]
        dt: datetime = datetime(time[0], time[1], time[2])
        fetch_parameters['window_start'] = int(dt.timestamp())

    return client.list_futures_aggregates(**fetch_parameters)

"""
Loads stored data from disk from a range of dates

@param ticker The ticker to retreive.
@param begin The first trading day  to retrieve.
@param end The last trading day  to retrieve.

@note If end is omited, the function will return all data 
      from the start date through the most recent stored trading day.
      If begin is omited, the function will return all data from 
      the least recent trading day to specified end date.
"""
def load_prior_data(ticker: str, begin: str | date = "", end: str | date = "") -> pd.DataFrame | None:
    data_dir = Path(f"data/{ticker}")
    if (not data_dir.is_dir()):
        print(f"No data for {ticker}.")
        return None

    if (not begin):
        start_date = min(
                date.fromisoformat(file.stem.removeprefix(f"{ticker}-"))
                for file in data_dir.iterdir()
                if (file.is_file())
        )
    else:
        start_date = date.fromisoformat(begin) if isinstance(begin, str) else begin
    if (not end):
        end_date = max(
                date.fromisoformat(file.stem.removeprefix(f"{ticker}-"))
                for file in data_dir.iterdir()
                if (file.is_file())
        )
    else:
        end_date = date.fromisoformat(end) if isinstance(end, str) else end

    files: list[Path] = [
            f for f in data_dir.iterdir() 
            if start_date <= date.fromisoformat(f.stem.removeprefix(f"{ticker}-")) <= end_date
    ]
    if (not files):
        print(f"No data for {ticker}.")
        return None

    return pd.concat([pd.read_parquet(file) for file in files], ignore_index=True)


"""
Loads a tickers most recent trading day from disk.

@param ticker The ticker to use.
"""
def load_latest_day(ticker) -> pd.DataFrame | None:
    data_dir = Path(f"data/{ticker}")
    if (not data_dir.is_dir()):
        return None


    target_file: Path | None = max(
            (file for file in data_dir.iterdir() if file.is_file()), 
            key=lambda file: date.fromisoformat(file.stem.removeprefix(f"{ticker}-")),
            default=None
    )
    if target_file is None:
        return None

    return pd.read_parquet(target_file)


"""
Loads a tickers most recent n observations from disk.

@param ticker The ticker to use.
@param n The number of observations to load from disk.
"""
def load_last_n(ticker: str, n: int) -> pd.DataFrame | None:
    data_dir = Path(f"data/{ticker}")
    if (not data_dir.is_dir()):
        return None

    files: list[Path] = [file for file in data_dir.iterdir() if file.is_file()]

    if (not files):
        return None

    files.sort(key = lambda file: date.fromisoformat(file.stem.removeprefix(f"{ticker}-")), reverse=True)

    dfs: list[pd.DataFrame] = []
    it = iter(files)
    while (n > 0):
        next_file = next(it, None)
        if (not next_file):
            break

        next_df: pd.DataFrame = pd.read_parquet(next_file).iloc[:n]
        n -= next_df.shape[0]
        dfs.append(next_df)
    
    return pd.concat(dfs, ignore_index=True)


def make_parquet(data: dict[str,Generator[FuturesAgg]]) -> None:

    d = defaultdict(lambda: [])

    for futuresagg in data:
        for k,v in (futuresagg.__dict__).items():
            d[k].append(v)
    df = pd.DataFrame(d)

    df.to_parquet("data.csv", index=False)

