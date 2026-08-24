from massive.rest.futures import FuturesAgg
from copy import copy
from typedefs import Limit, MassiveParameters
from collections import defaultdict
import pandas as pd
from pprint import pprint
from collections.abc import Generator
from datetime import datetime, timezone
from pathlib import Path
from datetime import date
from dateutil.relativedelta import relativedelta

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



"""
Fetches OHLC data from massive.com for a specified lookback period.

@param period Lookback unit accepted by datettime's relativedelta such as 'days', 'weeks', 'months', 'years'.
@param depth The number of lookback units to fetch.
@param massive_parameters parameters to use in the call to the massive api.
@param client An instance of a massive Restclient.

@return A generator yielding OHLC data.
"""
def fetch_lookback(period: str, depth: int, massive_parameters: MassiveParameters, massive_client) -> Generator[FuturesAgg | bytes]:
    params = copy(massive_parameters)
    current_date = date.today()

    past_date = current_date - relativedelta(**{period: depth}) # type: ignore

    params['window_start_gte'] = past_date.isoformat()
    params['window_start_lte'] = current_date.isoformat()
    print(f"Fetching the last {depth} {period} of history for {massive_parameters['ticker']}.")
    return fetch_data(massive_client, params)

"""
Fetches OHLC from massive.com between a specifed date range.

@param
"""
def fetch_range(begin: str, end: str, massive_parameters: MassiveParameters, massive_client) -> Generator[FuturesAgg | bytes]:
    params: MassiveParameters = copy(massive_parameters)
    params['window_start_gte'] = begin
    params['window_start_lte'] = end
    print(f"Fetching data for {massive_parameters['ticker']} between {begin} and {end}")
    return fetch_data(massive_client, params)

"""

"""
def fetch_latest(massive_parameters: MassiveParameters, massive_client) -> Generator[FuturesAgg | bytes] | None:
    params = copy(massive_parameters)
    # Load the latest observations from disk. 
    last_observation: pd.DataFrame | None = load_last_n(massive_parameters["ticker"], 1)
    if (last_observation is None):
        print("No history for this ticker. Use --lookback or --range instead")
        return None

    # Get the observations next starting window from the most recent observation.
    next_window_start: int = last_observation['window_start'].iloc[0] + 1 
    params["window_start_gte"] = next_window_start

    dt = datetime.fromtimestamp(
        next_window_start / 1_000_000_000,
        tz=timezone.utc,
    )
    print(f"Fetching the latest data for {massive_parameters['ticker']} beginning at {dt}")

    return fetch_data(massive_client,params)


