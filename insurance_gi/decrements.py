"""
This module just applies lapse/cancellations to future business
"""

import pandas as pd


def lapses(df: pd.DataFrame) -> pd.DataFrame:
    """
    df requires lapse rate and renewal index
    :param df:
    :return:
    """
    df['remaining_bop'] = (1 - df.lapse_rate) ** df.ren_idx

    columns_to_decrement = ['gwp', 'contracts', 'tariffs']
    columns_to_decrement = list(set(columns_to_decrement).intersection(df.columns))
    for col in columns_to_decrement:
        df[col] *= df.remaining_bop
    # Could also drop lapse_rate and ren_idx
    df = df.drop(columns=['remaining_bop', 'lapse_rate'])
    return df
