# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement

# --- Do not remove these libs ---
import numpy as np  # noqa
import pandas as pd  # noqa
import math
from pandas import DataFrame

from freqtrade.strategy.interface import IStrategy
from finta import TA
from freqtrade.utils.indicators import ccistc, t3cci
from freqtrade.utils.hyperopt_helpers import convert_buy_params, convert_sell_params

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

buy_params = {
    'cci-above-trigger-value': -176,
    'cci-below-trigger-value': -176,
    'cci-enabled': False,
    'cci-value': -154,
    'stc-above-trigger-value': 18,
    'stc-below-trigger-value': 11,
    'stc-enabled': True,
    'stc-value': 16,
    't3cci-above-trigger-value': -135,
    't3cci-below-trigger-value': -101,
    't3cci-enabled': False,
    't3cci-value': -112,
    'trigger': 'cci-below'
}

# Sell hyperspace params:
sell_params = {
    'sell-cci-above-trigger-value': 318,
    'sell-cci-below-trigger-value': 106,
    'sell-cci-enabled': False,
    'sell-cci-value': 303,
    'sell-stc-above-trigger-value': 76,
    'sell-stc-below-trigger-value': 82,
    'sell-stc-enabled': True,
    'sell-stc-value': 84,
    'sell-t3cci-above-trigger-value': 38,
    'sell-t3cci-below-trigger-value': 178,
    'sell-t3cci-enabled': False,
    'sell-t3cci-value': 169,
    'sell-trigger': 'sell-t3cci-below'
}

# Stoploss:
stoploss = -0.02953

class ScalpStrategy(IStrategy):
    """
    This is a strategy template to get you started.
    More information in https://github.com/freqtrade/freqtrade/blob/develop/docs/bot-optimization.md

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the prototype for the methods: minimal_roi, stoploss, populate_indicators, populate_buy_trend,
    populate_sell_trend, hyperopt_space, buy_strategy_generator
    """
    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 2

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    # minimal_roi = {
    #     "60": 0.01,
    #     "30": 0.01,
    #     "0": 0.01
    # }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = stoploss

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = '15m'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = False

    # These values can be overridden in the "ask_strategy" section in the config.
    use_sell_signal = True
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 14

    # Optional order type mapping.
    order_types = {
        'buy': 'market',
        'sell': 'market',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force.
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }

    plot_config = {
        # Main plot indicators (Moving averages, ...)
        'main_plot': {
            'sma_short': { 'color': 'blue'},
            'sma_long': {'color': 'pink'},
        },
        'subplots': {
            # Subplots - each dict defines one additional plot
            'rsi': {
                'rsi': { 'color': 'blue' }
            },
            'cci': {
                'cci': { 'color': 'pink' }
            }
        }
    }
    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # Momentum Indicators
        # ------------------------------------

        dataframe['stc'] = ccistc(dataframe, 10)
        dataframe['t3cci'] = t3cci(dataframe)
        dataframe['cci'] = ta.CCI(dataframe)
        # dataframe['stc'] = TA.STC(dataframe)
        # dataframe['sma_short'] = ta.SMA(dataframe, timeperiod=100)
        # dataframe['sma_long'] = ta.SMA(dataframe, timeperiod=300)
        # dataframe['rsi'] = ta.RSI(dataframe, timeperiod=500)

        # Retrieve best bid and best ask from the orderbook
        # ------------------------------------
        """
        # first check if dataprovider is available
        if self.dp:
            if self.dp.runmode in ('live', 'dry_run'):
                ob = self.dp.orderbook(metadata['pair'], 1)
                dataframe['best_bid'] = ob['bids'][0][0]
                dataframe['best_ask'] = ob['asks'][0][0]
        """

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            convert_buy_params(buy_params, dataframe),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            convert_sell_params(sell_params, dataframe),
            'sell'] = 1
        return dataframe
