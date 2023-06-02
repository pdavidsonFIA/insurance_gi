"""
This
- adds payment patterns and
- runs off ultimate loss to cash
- Allows for build & release of IBNR & case reserves

import pandas as pd
pattern = [.9**(9-x) for x in range(10)] # cumulative
pattern = [pattern[0]] + [j-i for i, j in zip(pattern[:-1], pattern[1:])] # incremental
pattern = list(enumerate(pattern))
ref_date = pd.Period('2022-01')
df = pd.DataFrame([[ref_date + i, -1, pattern] for i in range(5)], columns=['acc_month', 'ult', 'payment_pattern'])

"""
import pandas as pd
import numpy as np


def claims_runoff(df: pd.DataFrame) -> pd.DataFrame:
    df = df.explode('payment_pattern')
    df[['rep_date_idx', 'claims_s']] = pd.DataFrame(df.payment_pattern.to_list(), index=df.index)
    df['rep_date'] = df.acc_month + df.rep_date_idx

    df['d_claims'] = df.ult * df.claims_s

    # Rename blanks in the index
    df.index.names = [f"idx{i}" if v is None else v for i, v in enumerate(df.index.names)]
    grping_idx = df.index.names + ['acc_month']

    # Arbitrary, zero initial reserves at end of first month
    df['resv'] = 0.
    # Cumulative totals calculate for ibnr & case:
    df['claims'] = df.groupby(by=grping_idx)['d_claims'].cumsum()
    df['incurred'] = df.resv + df.claims


    df.loc[df.rep_date_idx > 0, 'incurred'] = np.nan
    df.loc[df.rep_date_idx >= 6, 'incurred'] = df.loc[df.rep_date_idx >= 6, 'ult']
    df.incurred = df.incurred.interpolate()

    # IBNR should run to zero after 6 months. incurred and ibnr both negative, but ult a positive
    df['ibnr'] = df.ult - df.incurred
    df['d_ibnr'] = df.groupby(by=grping_idx)['ibnr'].diff().fillna(df.ibnr)

    # Recalculating case reserves:
    df['resv'] = df['incurred'] - df['claims']
    df['d_resv'] = df.groupby(by=grping_idx)['resv'].diff().fillna(df.resv)


    return df
