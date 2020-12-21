from skopt.space import Categorical, Dimension, Integer, Real  # noqa
import freqtrade.vendor.qtpylib.indicators as qtpylib
import re
from functools import reduce

    # buy_params = {
    #     'cci-above-trigger-value': -222,
    #     'cci-below-trigger-value': -170,
    #     'cci-enabled': False,
    #     'cci-value': -301,
    #     'stc-above-trigger-value': 19,
    #     'stc-below-trigger-value': 10,
    #     'stc-enabled': True,
    #     'stc-value': 18,
    #     't3cci-above-trigger-value': -42,
    #     't3cci-below-trigger-value': -196,
    #     't3cci-enabled': False,
    #     't3cci-value': -125,
    #     'trigger': 'cci-below'
    # }
def convert_buy_params(buy_params, dataframe):
    conditions = []
    for param, value in buy_params.items():
        indicator_reg = re.search('(.*)-enabled', param)
        if not indicator_reg:
            continue
        indicator = indicator_reg.group(1)
        if value == True:
            conditions.append(dataframe[indicator] < buy_params[f'{indicator}-value'])

    trigger_param = f"{buy_params['trigger']}-trigger-value"
    trigger_indicator = buy_params['trigger'].split('-')[0]
    trigger_direction = buy_params['trigger'].split('-')[1]
    if trigger_direction == 'above':
        conditions.append(
            qtpylib.crossed_above(
                dataframe[f'{trigger_indicator}'], buy_params[f'{trigger_indicator}-above-trigger-value']
            )
        )

    if trigger_direction == 'below':
        conditions.append(
            qtpylib.crossed_below(
                dataframe[f'{trigger_indicator}'], buy_params[f'{trigger_indicator}-below-trigger-value']
            )
        )

    return reduce(lambda x, y: x & y, conditions)

def convert_sell_params(sell_params, dataframe):
    conditions = []
    for param, value in sell_params.items():
        indicator_reg = re.search('sell-(.*)-enabled', param)
        if not indicator_reg:
            continue
        indicator = indicator_reg.group(1)
        if value == True:
            conditions.append(dataframe[indicator] > sell_params[f'sell-{indicator}-value'])

    trigger_param = f"{sell_params['sell-trigger']}-trigger-value"
    trigger_indicator = sell_params['sell-trigger'].split('-')[1]
    trigger_direction = sell_params['sell-trigger'].split('-')[2]
    if trigger_direction == 'above':
        conditions.append(
            qtpylib.crossed_above(
                dataframe[f'{trigger_indicator}'], sell_params[f'sell-{trigger_indicator}-above-trigger-value']
            )
        )

    if trigger_direction == 'below':
        conditions.append(
            qtpylib.crossed_below(
                dataframe[f'{trigger_indicator}'], sell_params[f'sell-{trigger_indicator}-below-trigger-value']
            )
        )

    return reduce(lambda x, y: x & y, conditions)



def indicator_space_generator(indicator_dict, sell=False):
    statements = []
    sell_string = 'sell-' if sell else ''

    for indicator, range in indicator_dict.items():
        statements.append(Integer(range[0], range[1], name=f'{sell_string}{indicator}-value'))
        statements.append(Integer(range[0], range[1], name=f'{sell_string}{indicator}-above-trigger-value'))
        statements.append(Integer(range[0], range[1], name=f'{sell_string}{indicator}-below-trigger-value'))
        statements.append(Categorical([True, False], name=f'{sell_string}{indicator}-enabled'))

    trigger_list = []
    for indicator in indicator_dict:
        trigger_list.append(f'{sell_string}{indicator}-above')
        trigger_list.append(f'{sell_string}{indicator}-below')
    statements.append(Categorical(trigger_list, name=f'{sell_string}trigger'))

    return statements

def trend_conditions_generator(indicators, dataframe, params, sell=False):
    conditions = []
    sell_string = 'sell-' if sell else ''

    for indicator in indicators:
        if f'{sell_string}{indicator}-enabled' in params and params[f'{sell_string}{indicator}-enabled']:
            if sell:
                conditions.append(dataframe[f'{indicator}'] > params[f'{sell_string}{indicator}-value'])
            else:
                conditions.append(dataframe[f'{indicator}'] < params[f'{sell_string}{indicator}-value'])
        if f'{sell_string}trigger' in params:
            if params[f'{sell_string}trigger'] == f'{sell_string}{indicator}-above':
                conditions.append(
                    qtpylib.crossed_above(
                        dataframe[f'{indicator}'], params[f'{sell_string}{indicator}-above-trigger-value']
                    )
                )
            if params[f'{sell_string}trigger'] == f'{sell_string}{indicator}-below':
                conditions.append(
                    qtpylib.crossed_below(
                        dataframe[f'{indicator}'], params[f'{sell_string}{indicator}-below-trigger-value']
                    )
                )

    return conditions
