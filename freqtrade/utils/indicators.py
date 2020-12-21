import numpy as np  # noqa
import pandas as pd  # noqa
import math
from pandas import DataFrame
from finta import TA
import talib.abstract as ta


def ccistc(ohlc: DataFrame, k_period: int = 10, period_fast: int = 23,
      period_slow: int = 50,
      column: str = "close",
      adjust: bool = True
  ):
    # CCI = TA.CCI(ohlc, k_period)

    EMA_fast = pd.Series(
        ohlc[column].ewm(ignore_na=False, span=period_fast, adjust=adjust).mean(),
        name="EMA_fast",
    )

    EMA_slow = pd.Series(
        ohlc[column].ewm(ignore_na=False, span=period_slow, adjust=adjust).mean(),
        name="EMA_slow",
    )

    CCI = pd.Series((EMA_fast - EMA_slow), name="MACD")

    STOK_min = CCI.rolling(window=k_period).min()
    STOK_max = CCI.rolling(window=k_period).max()

    STOK = pd.Series(
        ((CCI - STOK_min) / (STOK_max - STOK_min)) * 100
    )

    STOD = smooth(STOK)
    STOD_min = STOD.rolling(window=k_period).min()
    STOD_max = STOD.rolling(window=k_period).max()
    STOKD = pd.Series(
        ((STOD - STOD_min) / (STOD_max - STOD_min)) * 100
    )
    STODKD = smooth(STOKD)
    return pd.Series(STODKD, name="{0} period CCISTC".format(k_period))


def smooth(sto):
    smoothed_array = []
    for idx, value in sto.items():
        if idx == 0 or math.isnan(smoothed_array[idx - 1]):
            smoothed_array.append(value)
        else:
            smoothed_array.append(smoothed_array[idx - 1] + 0.5 * (value - smoothed_array[idx - 1]))
    return pd.Series(smoothed_array)

def t3cci(dataframe: DataFrame, cci_period: int = 14, t3_period: int = 5):
    t3cci = []
    cci = ta.CCI(dataframe, cci_period)
    b = 0.618
    b2 = b * b
    b3 = b2 * b
    c1 = -b3
    c2 = (3 * (b2 + b3))
    c3 = -3 * (2 * b2 + b + b3)
    c4 = (1 + 3 * b + b3 + 3 * b2)
    nr = 1 + 0.5 * (t3_period - 1)
    w1 = 2 / (nr + 1)
    w2 = 1 - w1
    le1 = 0
    le2 = 0
    le3 = 0
    le4 = 0
    le5 = 0
    le6 = 0
    for idx, value in cci.items():
        if np.isnan(value):
            t3cci.append(value)
            continue

        e1 = w1 * value + w2 * le1
        e2 = w1 * e1 + w2 * le2
        e3 = w1 * e2 + w2 * le3
        e4 = w1 * e3 + w2 * le4
        e5 = w1 * e4 + w2 * le5
        e6 = w1 * e5 + w2 * le6
        t3cci.append(c1*e6 + c2*e5 + c3*e4 + c4*e3)

        le1 = e1
        le2 = e2
        le3 = e3
        le4 = e4
        le5 = e5
        le6 = e6

    return pd.Series(t3cci)
