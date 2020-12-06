from datetime import datetime
from math import exp

from pandas import DataFrame

from freqtrade.optimize.hyperopt import IHyperOptLoss


# Define some constants:

# set TARGET_TRADES to suit your number concurrent trades so its realistic
# to the number of days
TARGET_TRADES = 500
# This is assumed to be expected avg profit * expected trade count.
# For example, for 0.35% avg per trade (or 0.0035 as ratio) and 1100 trades,
# self.expected_max_profit = 3.85
# Check that the reported Σ% values do not exceed this!
# Note, this is ratio. 3.85 stated above means 385Σ%.
EXPECTED_MAX_PROFIT = 3.0

# max average trade duration in minutes
# if eval ends with higher value, we consider it a failed eval
MAX_ACCEPTED_TRADE_DURATION = 800


class ScalpHyperOptLoss(IHyperOptLoss):
    """
    Defines the default loss function for hyperopt
    This is intended to give you some inspiration for your own loss function.

    The Function needs to return a number (float) - which becomes smaller for better backtest
    results.
    """

    @staticmethod
    def hyperopt_loss_function(results: DataFrame, trade_count: int,
                               min_date: datetime, max_date: datetime,
                               *args, **kwargs) -> float:
        """
        Objective function, returns smaller number for better results
        """
        total_profit = results.profit_percent.sum()
        average_profit_pct = results.profit_percent.mean()
        average_profit_abs = results.profit_abs.mean()
        trade_duration = results.trade_duration.mean()
        winning_trade_count = results[results.profit_abs > 0].count()['profit_abs']
        losing_trade_count = results[results.profit_abs <= 0].count()['profit_abs']
        win_trade_profit = results[results.profit_abs > 0].profit_percent.sum()

        # trade_loss = 1 - 0.25 * exp(-(trade_count - TARGET_TRADES) ** 2 / 10 ** 5.8)
        # profit_loss = max(0, 1 - total_profit / EXPECTED_MAX_PROFIT)
        # duration_loss = 0.4 * min(trade_duration / MAX_ACCEPTED_TRADE_DURATION, 1)
        if (trade_duration < MAX_ACCEPTED_TRADE_DURATION):
            duration_loss = 0
        else:
            duration_loss = 1000

        if (trade_count > TARGET_TRADES):
            trade_loss = 0
        else:
            trade_loss = 1000

        result = losing_trade_count * 3 - winning_trade_count - (win_trade_profit * 100) + trade_loss + duration_loss
        return result
