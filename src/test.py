import pandas as pd
from massive import RESTClient
from atript_secrets import get_massive_api_key
from collections import defaultdict

# df = pd.read_parquet('data/MESU6/MESU6-2026-08-20.parquet')
# print(df)

client = RESTClient(api_key=get_massive_api_key())

agg = client.list_futures_aggregates("MESN5", resolution="15min", window_start_gte="2025-07-19", window_start_lte="2025-07-21")

d = defaultdict(list)
for i in agg:
    for k,v in i.__dict__.items():
        d[k].append(v)
df = pd.DataFrame(d)

print(df)


