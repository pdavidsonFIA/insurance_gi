"""
Functions to project renewals of contracts based on most recent inception date
Can be daily or monthly accuracy

# Sample products: coverage_period, lapse_rate, loss_ratio, comm_ratio, gwp, contracts
products = [[1, 0.1, 0.7, 0.2, 10, 10],
            [3, 0.1, 1.2, 0.2, 10, 10],
            [12, 0.1, 0.7, 0.4, 10, 10],
            [36, 0.1, 0.7, 0.2, 10, 10]]

# Monthly
import pandas as pd
ref_date = pd.Period('2022-01')
projection_horizon = 84

# Daily
from datetime import date
ref_date = date(2022,1,2)
ref_date = pd.to_datetime(ref_date)

df = pd.DataFrame([[ref_date, *prod] for prod in products], columns=[ 'gwp_from', 'coverage_period', 'lapse_rate', 'loss_ratio', 'comm_ratio', 'gwp', 'contracts'])

import insurance_gi as gi
df = gi.renewals(df, projection_horizon)
df = gi.lapses(df)
df = gi.financials(df)


"""
import pandas as pd
import numpy as np


def add_number_of_renewals(df: pd.DataFrame, projection_horizon: int) -> pd.DataFrame:
    """
    How many times does the contract renew within the projection horizon.
    coverage_period is defined in months
    This function adds a renewal index as well as months offset since initial data
    - m_offset is used to build future coverage periods
    - ren_idx drives the application of lapse rates
    """
    # df['m_offset'] = df.coverage_period.apply(lambda x: list(range(0, projection_horizon * 12, x)))
    df['m_offset'] = df.coverage_period.apply(
        lambda x: list([(i, x * i) for i in range(0, int(projection_horizon / x))]))
    df = df.explode('m_offset')
    df[['ren_idx', 'm_offset']] = pd.DataFrame(df.m_offset.to_list(), index=df.index)
    return df


def add_future_coverage_periods(df):
    """ Accepts dates or monthly periods """
    if df.gwp_from.dtype == 'datetime64[ns]':
        # Start of period incremented by months -> daily accuracy:
        for m_offset in set(df['m_offset'].unique()):
            df.loc[df['m_offset'] == m_offset, 'gwp_from'] += pd.DateOffset(months=m_offset)
        # End period = start period + coverage period
        df['gwp_until'] = df['gwp_from']
        for interval in set(df['coverage_period'].unique()):
            df.loc[df['coverage_period'] == interval, 'gwp_until'] += pd.DateOffset(months=interval)

    elif df.gwp_from.dtype == 'period[M]':
        # Simpler logic for monthly periods -> no daily accuracy just complete months
        for m_offset in set(df['m_offset'].unique()):
            df.loc[df['m_offset'] == m_offset, 'gwp_from'] += m_offset
        df['gwp_until'] = df['gwp_from']
        for interval in set(df['coverage_period'].unique()):
            df.loc[df['coverage_period'] == interval, 'gwp_until'] += interval

    return df


def adjust_gwp_from_monthends(df):
    # Group the gwp according to reporting month
    df['gwp_ismonthend'] = df['gwp_from'].dt.is_month_end
    # Need to be careful with pandas offsets as if it is already a monthend, will move to next month
    df.loc[~df.gwp_ismonthend, 'gwp_from'] += pd.offsets.MonthEnd(0)
    df.drop(columns=['gwp_ismonthend'], inplace=True)
    return df


def premium_dates_to_period(df):
    # Fixing dates to use monthly periods:
    cols = ['gwp_from', 'acc_month']
    for col in cols:
        if col in df.columns:
            # df[col] = pd.to_datetime(df[col])
            df[col] = df[col].dt.to_period('M')
    return df



def generate_earnings_pattern(df):
    """
    This function builds an accident month series with balance of remaining earnings at end of acc month
    """
    if df.gwp_from.dtype == 'datetime64[ns]':
        # df = adjust_gwp_from_monthends(df)
        # df = premium_dates_to_period(df)
        # 1 down to zero, linearly across coverage period, resampled at month ends
        df['earnings_bop'] = - 1.
        df['earnings_eop'] = 0.

        # This creates an index for the 1st of each month following the gwp date, needed for correct interpolation
        # Want the 1st of the month of every month after gwp date until the upr has completely run off:
        df['upr_idx_bom'] = df.apply(
            lambda x: pd.date_range(x.gwp_from, x.gwp_until + pd.DateOffset(months=1), freq='MS', inclusive='right'),
            axis=1)
        # This creates an eom index consistent with rep date - i.e. end of the last day of the month is equivalent to start of the 1st day of the next month:
        df['upr_idx_eom'] = df.apply(
            lambda x: pd.date_range(x.gwp_from,
                                    x.gwp_until + pd.DateOffset(months=1), freq='M', inclusive='left'), axis=1)

        # This is a heavy step.
        # The month-start index is joined to the gwp from and until dates
        # The UPR is interpolated along the index from the initial value (gwp) to zero
        # The index is reset and samples the month end figures only, and drops the start and end
        df['upr_s'] = df.apply(
            lambda x:
            pd.Series([x.earnings_bop, x.earnings_eop], index=[x.gwp_from, x.gwp_until])
                .reindex(np.unique([x.gwp_from, x.gwp_until] + x.upr_idx_bom.tolist()))
                .interpolate('index')
                .reindex(x.upr_idx_bom).to_list(),
            axis=1)
        df['earning_series'] = df.upr_s.apply(lambda x: list(range(len(x))))
        df['upr_x'] = df.apply(lambda x: list(zip(x.earning_series, x.upr_idx_eom, x.upr_s)), axis=1)
        df = df.drop(columns=['gwp_until', 'earnings_bop', 'earnings_eop', 'upr_idx_bom', 'upr_idx_eom', 'upr_s', 'earning_series'])

        # df.index.name = 'temp_idx'
        df = df.explode('upr_x')
        df[['earning_period', 'acc_month', 'earnings_remaining']] = pd.DataFrame(df.upr_x.to_list(), index=df.index)
        df = df.drop(columns=['upr_x'])
        df['earnings_current'] = df.groupby(by=df.index)['earnings_remaining'].transform(
            lambda x: x.diff())
        df.earnings_current = df.earnings_current.fillna(df.earnings_remaining)

        # df['upr_x'] = df.apply(lambda x: list(zip(x.upr_idx_eom, x.upr_s)), axis=1)
        # df = df.drop(columns=['gwp_until', 'earnings_bop', 'earnings_eop', 'upr_idx_bom', 'upr_idx_eom', 'upr_s'])
        #
        # # df.index.name = 'temp_idx'
        # df = df.explode('upr_x')
        # df[['acc_month', 'earnings_remaining']] = pd.DataFrame(df.upr_x.to_list(), index=df.index)
        # df = df.drop(columns=['upr_x'])
        # df['earnings_current'] = df.groupby(by=df.index)['earnings_remaining'].transform(
        #     lambda x: x.diff())
        # df.earnings_current = df.earnings_current.fillna(df.earnings_remaining)


    elif df.gwp_from.dtype == 'period[M]':
        # 1/earning_pattern. Requires earning pattern to be added in prior step.
        # Build acc months series. f generates the earnings pattern for a given number of months
        # E.g. f(1), f(12)
        # f = lambda x: list([(i, 1 - (i+1)/x) for i in range(0, x)])
        g = lambda x, y: 1 / y - 1 if x == 0 else 1 / y
        h = lambda x: x == 0
        f = lambda x: list([(i, 1 - (i + 1) / x, g(i, x), h(i)) for i in range(0, x)])
        df['temp_series'] = df.coverage_period.apply(f)
        df = df.explode('temp_series')
        # df[['acc_months', 'earnings_remaining']] = pd.DataFrame(df.acc_months.to_list(), index=df.index)
        df[['earning_period', 'earnings_remaining', 'earnings_current', 'initial_recognition']] = pd.DataFrame(df.temp_series.to_list(), index=df.index)
        df['acc_month'] = df.gwp_from
        for mth in set(df['earning_period'].unique()):
            df.loc[df.earning_period == mth, 'acc_month'] += mth

        df = df.drop(columns=['temp_series', 'coverage_period'])
    return df


def renewals(df: pd.DataFrame, projection_horizon: int) -> pd.DataFrame:
    """

    :param df: columns: gwp_from - day or monthly period, coverage_period -> number of months
    :param proj_horizon: -> Number of periods into future to project
    :return:
    """
    df = add_number_of_renewals(df, projection_horizon)
    df = add_future_coverage_periods(df)
    df = generate_earnings_pattern(df)
    return df

