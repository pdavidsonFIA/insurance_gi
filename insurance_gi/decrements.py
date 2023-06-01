"""
This module just applies lapse/cancellations to future business
import pandas as pd
ref_date = pd.Period('2022-01')
coverage_periods = [1,3,12,36]
projection_horizon = 84
df = pd.DataFrame([[ref_date, 10,10, coverage_period, 0.1] for coverage_period in coverage_periods], columns=['gwp_from', 'gwp', 'contracts','coverage_period', 'lapse_rate'])
from insurance_gi.renewals import renewals
df = renewals(df, projection_horizon)


"""



def add_lapse_prob(df):
    """
    Adds % remaining ad beginning of renewal period, and % lapses expected in that period
    :param df:
    :return:
    """
    # Renewal probability for cumulative tariffs
    df['renewal_prob'] = df.renewal_rate ** df.ren_idx
    df['remaining_bop'] = df.renewal_rate ** df.ren_idx

    # Lapse rate -> expected cancellations of contracts before the end of the coverage period
    df['lapse_prob'] = df.renewal_prob * (1 - df.renewal_rate)

    df = df.drop(columns=['renewal_rate', 'renewal_prob', 'renewal_type'])

    return df


def lapses(df):
    """
    df requires lapse rate and renewal index
    :param df:
    :return:
    """
    df['remaining_bop'] = (1 - df.lapse_rate) ** df.ren_idx
