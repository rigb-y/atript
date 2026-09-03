import numpy as np
import pandas as pd

from futures_pipeline.preprocessing  import percent_b
from futures_pipeline.datareader import load_latest_day
from futures_pipeline.config import PROCESSED_DATA_DIR

ticker = "MESU6"
data_path = f"{PROCESSED_DATA_DIR}/{ticker}"
print(data_path)
df = load_latest_day(data_path, "MESU6")
if (df is None):
    exit()

print(df.groupby("ticker").cumcount())

# prices: pd.Series = df['close']
# pct_b = percent_b(prices)
# print(pct_b)

