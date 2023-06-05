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


def claims_runoff(df: pd.DataFrame) -> pd.DataFrame:
    """
    Payment patterns and ultimates
    payment patterns should be (period, paid, incurred) -> cumulative
    :param df:
    :return:
    """
    df = df.explode('pattern')
    df[['rep_date_idx', 'claim_s', 'incurred_s']] = pd.DataFrame(df.pattern.to_list(), index=df.index)
    df['rep_date'] = df.acc_month + df.rep_date_idx

    # Cumulative claims paid & reported
    df['claims'] = df.ult * df.claim_s
    df['incurred'] = df.ult * df.incurred_s
    df['resv'] = df.incurred - df.claims
    df['ibnr'] = df.ult - df.incurred

    # Rename blanks in the index
    df.index.names = [f"idx{i}" if v is None else v for i, v in enumerate(df.index.names)]
    grping_idx = df.index.names + ['acc_month']

    # Deltas for claims & reserve positions
    df['d_claims'] = df.groupby(by=grping_idx)['claims'].diff().fillna(df.claims)
    df['d_ibnr'] = df.groupby(by=grping_idx)['ibnr'].diff().fillna(df.ibnr)
    df['d_resv'] = df.groupby(by=grping_idx)['resv'].diff().fillna(df.resv)

    return df
