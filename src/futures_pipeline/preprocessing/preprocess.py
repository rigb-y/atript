import pandas as pd
import numpy as np
from  import create_preprocess_parser

def handle_missing(data: pd.DataFrame) -> pd.DataFrame:
    print(data.isna().any())
    ...
def handle_duplicates(data: pd.DataFrame) -> pd.DataFrame:
    ...

def preprocess(data: pd.DataFrame) -> pd.DataFrame:

    data['returns'] = get_returns(data['close'])
    data['rsi'] = rsi(data['close'], 14)

    data = data.drop(['settlement_price', 'open', 'high', 'low','close'], axis=1)
    return data

'''
Computes the returns for a sequence of candlestick closes.
@param close An array of closing values for candlesticks.

@Note Returns are the relative change in closing value between observation k and k + 1.
@Note Assumes close is ordered by most recent observation to least recent observation.
'''
def get_returns(close: pd.Series) -> pd.Series:
    return pd.Series(-np.diff(close) / close[1:]).shift(1)

'''
Computes relative strength index for an array of price history.

@param prices An array of price history.
@param n The number of candlesticks to use in the computations.
'''
def rsi(prices: pd.Series, n: int) -> np.ndarray:
    ret: np.ndarray = np.full(len(prices), np.nan)
    diff: np.ndarray = -np.diff(prices)

    for i in range(len(prices) - n):
        window: np.ndarray = diff[i:i + n]

        avg_gain: float = sum(window[window > 0]) / n
        avg_loss: float = -sum(window[window < 0]) / n 

        if avg_loss == 0 and avg_gain == 0:
            rsi = 50.0
        elif avg_loss == 0:
            rsi = 100.0
        else:
            rs: float = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        ret[i] = rsi
    return ret

'''
Computes the p period simple moving average

@param prices An array of price history.
@param p Period length

@note 
    SMA_M: M \\to M-p+1 = 1/p \\sum_{i=m-p+1}^M x_i
    SMA_{M+1}: M+1 \\to m-p+2 = SMA_{M} + 1/p(x_{M+1} - x_{M-p+1})
'''
def sma(prices: pd.Series, p: int):
    if (p <= 0 or p > len(prices)): return

    n: int = len(prices) - 1
    ret: np.ndarray = np.full(n+1, np.nan)

    k: int = 0
    price_sum: np.float64 = np.float64()
    initial: np.float64 = np.float64()
    
    for i in range(n, n-p, -1):
        price_sum += prices.iloc[i]

    initial = price_sum / p
    ret[k] = initial
    tail: int = n

    k+=1
    for i in range(n-p+1, 0, -1):
        ret[k] = ret[k-1] + 1/p * (prices.iloc[i] - prices.iloc[tail])
        tail-=1 
        k+=1

    return ret

def wma():
    ...

def ema(prices: pd.Series): 
    ...

def bollinger_bands():
    ...

def msi():
    ...
def vwap():
    ...

def main():
    parser = create_preprocess_parser()

    args = parser.parser_args()

if __name__ == "__main__":
    main()

