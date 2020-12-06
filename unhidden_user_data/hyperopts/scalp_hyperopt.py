# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# isort: skip_file
# --- Do not remove these libs ---
from functools import reduce
from typing import Any, Callable, Dict, List

import numpy as np  # noqa
import pandas as pd  # noqa
from pandas import DataFrame
from skopt.space import Categorical, Dimension, Integer, Real  # noqa

from freqtrade.optimize.hyperopt_interface import IHyperOpt
from finta import TA

# --------------------------------
# Add your lib to import here
import talib.abstract as ta  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib


class ScalpHyperOpt(IHyperOpt):
    """
    This is a sample hyperopt to inspire you.
    Feel free to customize it.

    More information in the documentation: https://www.freqtrade.io/en/latest/hyperopt/

    You should:
    - Rename the class name to some unique name.
    - Add any methods you want to build your hyperopt.
    - Add any lib you need to build your hyperopt.

    You must keep:
    - The prototypes for the methods: populate_indicators, indicator_space, buy_strategy_generator.

    The methods roi_space, generate_roi_table and stoploss_space are not required
    and are provided by default.
    However, you may override them if you need the
    'roi' and the 'stoploss' spaces that differ from the defaults offered by Freqtrade.

    This sample illustrates how to override these methods.
    """
    @staticmethod
    def populate_indicators(dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        This method can also be loaded from the strategy, if it doesn't exist in the hyperopt class.
        """
        dataframe['cci'] = ta.CCI(dataframe)
        dataframe['stc'] = TA.STC(dataframe)

        return dataframe

    @staticmethod
    def buy_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the buy strategy parameters to be used by hyperopt
        """
        def populate_buy_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Buy strategy Hyperopt will build and use
            """
            conditions = []
            if 'cci-enabled' in params and params['cci-enabled']:
                conditions.append(dataframe['cci'] < params['cci-value'])
            if 'stc-enabled' in params and params['stc-enabled']:
                conditions.append(dataframe['stc'] < params['stc-value'])

            if 'trigger' in params:
                if params['trigger'] == 'cci-above':
                    conditions.append(
                        qtpylib.crossed_above(
                            dataframe['cci'], params['cci-above-trigger-value']
                        )
                    )
                if params['trigger'] == 'stc-above':
                    conditions.append(
                        qtpylib.crossed_above(
                            dataframe['stc'], params['stc-above-trigger-value']
                        )
                    )
                if params['trigger'] == 'cci-below':
                    conditions.append(
                        qtpylib.crossed_below(
                            dataframe['cci'], params['cci-below-trigger-value']
                        )
                    )
                if params['trigger'] == 'stc-below':
                    conditions.append(
                        qtpylib.crossed_below(
                            dataframe['stc'], params['stc-below-trigger-value']
                        )
                    )

            # Check that volume is not 0
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'buy'] = 1

            return dataframe

        return populate_buy_trend

    @staticmethod
    def indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching strategy parameters
        """
        return [
            Integer(-400, -100, name='cci-value'),
            Integer(5, 25, name='stc-value'),
            Integer(-400, -100, name='cci-above-trigger-value'),
            Integer(5, 25, name='stc-above-trigger-value'),
            Integer(-400, -100, name='cci-below-trigger-value'),
            Integer(5, 25, name='stc-below-trigger-value'),
            Categorical([True, False], name='cci-enabled'),
            Categorical([True, False], name='stc-enabled'),
            Categorical(['cci-above', 'stc-above', 'cci-below', 'stc-below'], name='trigger')
        ]

    @staticmethod
    def sell_strategy_generator(params: Dict[str, Any]) -> Callable:
        """
        Define the sell strategy parameters to be used by hyperopt
        """
        def populate_sell_trend(dataframe: DataFrame, metadata: dict) -> DataFrame:
            """
            Sell strategy Hyperopt will build and use
            """
            # print(params)
            conditions = []
            if 'sell-cci-enabled' in params and params['sell-cci-enabled']:
                conditions.append(dataframe['cci'] > params['sell-cci-value'])
            if 'sell-stc-enabled' in params and params['sell-stc-enabled']:
                conditions.append(dataframe['stc'] > params['sell-stc-value'])

            if 'sell-trigger' in params:
                if params['sell-trigger'] == 'sell-cci-above':
                    conditions.append(
                        qtpylib.crossed_above(
                            dataframe['cci'], params['sell-cci-above-trigger-value']
                        )
                    )
                if params['sell-trigger'] == 'sell-stc-above':
                    conditions.append(
                        qtpylib.crossed_above(
                            dataframe['stc'], params['sell-stc-above-trigger-value']
                        )
                    )
                if params['sell-trigger'] == 'sell-cci-below':
                    conditions.append(
                        qtpylib.crossed_below(
                            dataframe['cci'], params['sell-cci-below-trigger-value']
                        )
                    )
                if params['sell-trigger'] == 'sell-stc-below':
                    conditions.append(
                        qtpylib.crossed_below(
                            dataframe['stc'], params['sell-stc-below-trigger-value']
                        )
                    )

            # Check that volume is not 0
            conditions.append(dataframe['volume'] > 0)

            if conditions:
                dataframe.loc[
                    reduce(lambda x, y: x & y, conditions),
                    'sell'] = 1

            return dataframe

        return populate_sell_trend

    @staticmethod
    def sell_indicator_space() -> List[Dimension]:
        """
        Define your Hyperopt space for searching sell strategy parameters
        """
        return [
            Integer(100, 400, name='sell-cci-value'),
            Integer(75, 100, name='sell-stc-value'),
            Integer(100, 400, name='sell-cci-above-trigger-value'),
            Integer(75, 100, name='sell-stc-above-trigger-value'),
            Integer(100, 400, name='sell-cci-below-trigger-value'),
            Integer(75, 100, name='sell-stc-below-trigger-value'),
            Categorical([True, False], name='sell-cci-enabled'),
            Categorical([True, False], name='sell-stc-enabled'),
            Categorical(['sell-cci-above', 'sell-stc-above', 'sell-cci-below', 'sell-stc-below'], name='sell-trigger')
        ]

    @staticmethod
    def generate_roi_table(params: Dict) -> Dict[int, float]:
        """
        Generate the ROI table that will be used by Hyperopt

        This implementation generates the default legacy Freqtrade ROI tables.

        Change it if you need different number of steps in the generated
        ROI tables or other structure of the ROI tables.

        Please keep it aligned with parameters in the 'roi' optimization
        hyperspace defined by the roi_space method.
        """
        roi_table = {}
        roi_table[0] = params['roi_p1'] + params['roi_p2'] + params['roi_p3']
        roi_table[params['roi_t3']] = params['roi_p1'] + params['roi_p2']
        roi_table[params['roi_t3'] + params['roi_t2']] = params['roi_p1']
        roi_table[params['roi_t3'] + params['roi_t2'] + params['roi_t1']] = 0

        return roi_table

    @staticmethod
    def roi_space() -> List[Dimension]:
        """
        Values to search for each ROI steps

        Override it if you need some different ranges for the parameters in the
        'roi' optimization hyperspace.

        Please keep it aligned with the implementation of the
        generate_roi_table method.
        """
        return [
            Integer(10, 120, name='roi_t1'),
            Integer(10, 60, name='roi_t2'),
            Integer(10, 40, name='roi_t3'),
            Real(0.01, 0.04, name='roi_p1'),
            Real(0.01, 0.07, name='roi_p2'),
            Real(0.01, 0.20, name='roi_p3'),
        ]

    @staticmethod
    def stoploss_space() -> List[Dimension]:
        """
        Stoploss Value to search

        Override it if you need some different range for the parameter in the
        'stoploss' optimization hyperspace.
        """
        return [
            Real(-1, -0.02, name='stoploss'),
        ]

    @staticmethod
    def trailing_space() -> List[Dimension]:
        """
        Create a trailing stoploss space.

        You may override it in your custom Hyperopt class.
        """
        return [
            # It was decided to always set trailing_stop is to True if the 'trailing' hyperspace
            # is used. Otherwise hyperopt will vary other parameters that won't have effect if
            # trailing_stop is set False.
            # This parameter is included into the hyperspace dimensions rather than assigning
            # it explicitly in the code in order to have it printed in the results along with
            # other 'trailing' hyperspace parameters.
            Categorical([True], name='trailing_stop'),

            Real(0.01, 0.35, name='trailing_stop_positive'),

            # 'trailing_stop_positive_offset' should be greater than 'trailing_stop_positive',
            # so this intermediate parameter is used as the value of the difference between
            # them. The value of the 'trailing_stop_positive_offset' is constructed in the
            # generate_trailing_params() method.
            # This is similar to the hyperspace dimensions used for constructing the ROI tables.
            Real(0.001, 0.1, name='trailing_stop_positive_offset_p1'),

            Categorical([True, False], name='trailing_only_offset_is_reached'),
        ]

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators.
        Can be a copy of the corresponding method from the strategy,
        or will be loaded from the strategy.
        Must align to populate_indicators used (either from this File, or from the strategy)
        Only used when --spaces does not include buy
        """
        dataframe.loc[
            (
                (dataframe['cci'] < -100) &
                (dataframe['stc'] < 25)
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators.
        Can be a copy of the corresponding method from the strategy,
        or will be loaded from the strategy.
        Must align to populate_indicators used (either from this File, or from the strategy)
        Only used when --spaces does not include sell
        """
        dataframe.loc[
            (
                (dataframe['cci'] > 100) &
                (dataframe['stc'] > 75)
            ),
            'sell'] = 1
        return dataframe
