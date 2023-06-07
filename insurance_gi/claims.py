"""
This
- adds payment patterns and
- runs off ultimate loss to cash
- Allows for build & release of IBNR & case reserves

import pandas as pd
paid = [.9**(9-x) for x in range(10)] # cumulative
inc = [paid[0]+ (1-paid[0])/6 * x for x in range(6)] + (len(paid) - 6) * [1.] # linear over 6 months
pattern = [(index, p, i) for index, (p, i) in enumerate(zip(paid, inc))]

cum_to_inc = lambda patt: [patt[0]] + [j-i for i, j in zip(patt[:-1], patt[1:])] # incremental
paid = list(enumerate(cum_to_inc(paid)))
inc =  list(enumerate(cum_to_inc(inc)))
pattern = [(index, p, i) for index, (p, i) in enumerate(zip(cum_to_inc(paid), cum_to_inc(inc)))]

ref_date = pd.Period('2022-01')
df = pd.DataFrame([[ref_date + i, -1, pattern] for i in range(5)], columns=['acc_month', 'ult', 'pattern'])

"""
import pandas as pd
import numpy as np


def claims_runoff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Payment patterns and ultimates
    payment patterns should be (period, paid, incurred) -> cumulative
    :param df:
    :return:
    """
    original_columns = df.columns
    claims_runoff_columms = {'claims', 'resv', 'd_claims', 'd_resv', 'ult', 'ibnr', 'd_ibnr', 'incurred'}
    date_columns = {'rep_date', 'acc_month'}
    # Don't want to duplicate GWP across every runoff period of the claims
    columns_to_null_after_explode = list(set(original_columns).difference(claims_runoff_columms.union(date_columns)))

    if 'acc_month' in df.index.names:
        df = df.reset_index('acc_month')
        acc_month_in_index = True
    else:
        acc_month_in_index = False

    if 'claims' not in df.columns:
        # If no initial claims set then set to 0
        df['claims'] = 0.
    if 'resv' not in df.columns:
        df['resv'] = 0.
    df['remaining_to_be_paid'] = df.ult - df.claims
    df['incurred'] = df.claims + df.resv
    df['remaining_to_be_reported'] = df.ult - df.incurred

    df = df.explode('pattern')
    df[['rep_date_idx', 'claim_s', 'incurred_s']] = pd.DataFrame(df.pattern.to_list(), index=df.index)
    if 'rep_date' in df.columns:
        # If running off incurred then acc_month might be in the past, only want to increment from current rep date
        df['rep_date'] += df.rep_date_idx
    else:
        # Future accident months
        df['rep_date'] = df.acc_month + df.rep_date_idx

    # Cumulative claims paid & reported
    df['claims'] += df.claim_s * df.remaining_to_be_paid
    df['incurred'] += df.incurred_s * df.remaining_to_be_reported
    df['resv'] = df.incurred - df.claims
    df['ibnr'] = df.ult - df.incurred

    # Rename blanks in the index
    df.index.names = [f"idx{i}" if v is None else v for i, v in enumerate(df.index.names)]
    grping_idx = df.index.names + ['acc_month']

    df = df.reset_index().set_index(grping_idx).sort_index()
    # Deltas for claims & reserve positions
    df['d_claims'] = df.groupby(by=grping_idx)['claims'].diff().fillna(df.claims)
    df['d_ibnr'] = df.groupby(by=grping_idx)['ibnr'].diff().fillna(df.ibnr)
    df['d_resv'] = df.groupby(by=grping_idx)['resv'].diff().fillna(df.resv)

    # Cleanup
    df.loc[df.rep_date_idx != 0, columns_to_null_after_explode] = np.nan  # maybe 0. is better
    df = df.drop(columns=['pattern', 'rep_date_idx', 'claim_s', 'incurred_s', 'remaining_to_be_paid', 'remaining_to_be_reported'])
    if ~acc_month_in_index:
        df = df.reset_index('acc_month')

    return df
