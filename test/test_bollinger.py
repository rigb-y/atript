import numpy as np
import pandas as pd

from datetime import datetime
from futures_pipeline.preprocessing  import percent_b
from futures_pipeline.datareader import load_latest_day, load_prior_data
from futures_pipeline.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

ticker = "MESU6"
data_path = PROCESSED_DATA_DIR/ticker
print(data_path)
# df = load_prior_data(data_path, "MESU6", "2026-08-27", "2026-08-28")
df = load_prior_data(data_path, "MESU6", "2026-09-01", "2026-09-01")
if (df is None):
    exit()

print(min(df['real_timestamp']))
print(max(df['real_timestamp']))

print(df.iloc[91])

# Starts at 4pm CT and ends the following day at 5pm CT

# print(df[df['real_timestamp'] == datetime.fromisoformat("2026-08-27T23:45:00Z")])
# print(df[df['real_timestamp'] == datetime.fromisoformat("2026-08-28T00:00:00Z")])

# print(df.head(30))


# prices: pd.Series = df['close']
# pct_b = percent_b(prices)
# print(pct_b)
