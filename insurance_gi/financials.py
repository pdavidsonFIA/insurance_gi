"""
This module considers basic financial components:
- gwp & upr
- commission & dac
- initial loss recognition:
  - dac write-down
  - urr
"""

import pandas as pd


def financials(df: pd.DataFrame) -> pd.DataFrame:
    """
    Requires loss ratio and commission ratio
    :param df:
    :return:
    """
    # Build premium earnings -> UPR is negative as it's a liability
    df['upr'] = - df.gwp * df.earnings_remaining
    df['d_upr'] = df.gwp * df.earnings_current

    # Add commission / expenses
    df['comm'] = - df.gwp * df.comm_ratio

    # Only recognise gwp at start of coverage period
    df.loc[df.earning_period != 0, ['gwp', 'comm']] = 0.

    df['gep'] = df.gwp + df.d_upr

    # Contract exposure
    df['exposure'] = df.earnings_current
    df.loc[df.earning_period == 0, 'exposure'] += 1.
    df.exposure *= df.contracts

    # Apply loss ratio to earnings for ultimate loss
    df['ult'] = df.loss_ratio * df.gep

    # Add loss recognition / urr for loss rations > 100%
    df['urr_ratio'] = df.loss_ratio.apply(lambda x: max(0., x - 1.))
    df['urr'] = df.upr * df.urr_ratio
    df['d_urr'] = df.d_upr * df.urr_ratio

    # Add loss recognition: limit dac for combined ratio > 100%
    dac_limit = lambda x: min(x.comm_ratio, max(1. - x.loss_ratio, 0.))
    df['dac_limit_ratio'] = df.apply(dac_limit, axis=1)

    # DAC is an asset (normally) so reverse sign of UPR
    df['dac'] = - df.upr * df.dac_limit_ratio
    df['d_dac'] = - df.d_upr * df.dac_limit_ratio


    df = df.drop(columns=['dac_limit_ratio', 'urr_ratio', 'loss_ratio', 'comm_ratio', 'earning_period'])

    return df
