#!usr/bin/python3
from secrets import get_massive_api_key
from datareader import read_data
import types

def main(*args, **kwargs) -> None: 
    massive_api: str = secrets.get_massive_api_key()
    tickers: list[str] = ["MESU6"]
    read_data(massive_api, tickers, Limit(100), "dumps/dump.json")

if __name__ == '__main__':
    main()
