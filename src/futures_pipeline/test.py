import pandas as pd
from massive import RESTClient
from atript_secrets import get_massive_api_key
from collections import defaultdict

# df = pd.read_parquet('data/MESU6/MESU6-2026-08-20.parquet')
# print(df)

client = RESTClient(api_key=get_massive_api_key())

data = client.list_futures_aggregates(ticker="MESU6", resolution="15min", limit=100)
print(type(data))
print(next(data))

# df = pd.read_parquet("data/MESU6/MESU6-2026-08-15.parquet")



