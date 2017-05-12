import numpy as np
import pandas as pd

import scipy.stats as ss
import statsmodels.tsa.stattools as sts
import statsmodels.tools.tools as stt

# import statsmodels.stats.diagnostic as ssd


# maxzero = lambda x: np.maximum(x, 0)
# vmax = np.vectorize(np.maximum)

# default no. of trading days in a year, 255.
trading_days = 255


def returns_gmean(returns):
    '''
    Calculates geometric average returns from a given returns series.
    '''
    if isinstance(returns, pd.DataFrame) or isinstance(returns, pd.Series):
        returns = returns.fillna(0)
    else:
        returns = np.nan_to_num(returns)
    return ss.gmean(1 + returns, axis=0) - 1


def log_returns(prices, n=1):
    return np.log(prices / prices.shift(n)).fillna(0)


def pct_to_log_return(pct_returns):
    if isinstance(pct_returns, pd.DataFrame) or \
            isinstance(pct_returns, pd.Series):
        return np.log(1 + pct_returns.fillna(0))
    else:
        return np.log(1 + np.nan_to_num(pct_returns))


def log_to_pct_return(log_returns):
    return np.exp(log_returns) - 1


def validate_mean_method(method):
    if method not in {'gmean', 'simple'}:
        raise AssertionError('mean_method can only be {"gmean", "simple"}')


def validate_return_type(return_type):
    if return_type not in {'pct', 'log'}:
        raise AssertionError('mean_method can only be {"pct", "log"}')


def maxzero(x):
    return np.maximum(x, 0)


def LPM(returns, target_rtn, moment):
    if isinstance(returns, pd.DataFrame) or isinstance(returns, pd.Series):
        adj_returns = (target_rtn - returns).apply(maxzero)
        return np.power(adj_returns, moment).mean()
    else:
        adj_returns = np.ndarray.clip(target_rtn - returns, min=0)
        # only averaging over non nan values
        # return np.nansum(np.power(adj_returns, moment)) / \
        #     np.count_nonzero(~np.isnan(adj_returns))
        return np.nanmean(np.power(adj_returns, moment), axis=0)


def kappa(returns, target_rtn, moment, return_type='log'):
    '''
    Geometric mean should be used when returns are percentage returns.
    Arithmetic mean should be used when returns are log returns.
    '''
    validate_return_type(return_type)

    if return_type == 'pct':
        # mean = returns_gmean(returns)
        excess = pct_to_log_return(returns - target_rtn)
    else:
        excess = returns - target_rtn

    if isinstance(excess, pd.DataFrame) or isinstance(excess, pd.Series):
        mean = excess.mean()
    else:
        mean = np.nanmean(excess)

    kappa = mean / np.power(LPM(returns, target_rtn, moment=moment),
                            1.0 / moment)
    return kappa


def kappa3(returns, target_rtn=0, return_type='log'):
    '''
    Kappa 3
    '''
    return kappa(returns, target_rtn=target_rtn, moment=3,
                 return_type=return_type)


def omega(returns, target_rtn=0, return_type='log'):
    '''
    Omega Ratio
    '''
    return 1 + kappa(returns,
                     target_rtn=target_rtn,
                     moment=1,
                     return_type=return_type)


def omega_empirical(returns, target_rtn=0, return_type='log',
                    plot=False, steps=1000):
    '''
    Omega Ratio based on empirical distribution.
    '''
    validate_return_type(return_type)

    if return_type == 'pct':
        returns = pct_to_log_return(returns)

    # TODO
    ecdf = stt.ECDF(returns)

    # Generate computation space
    x = np.linspace(start=returns.min(), stop=returns.max(), num=steps)
    y = ecdf(x)

    norm_cdf = ss.norm.cdf(x,
                           loc=returns.mean(),
                           scale=returns.std(ddof=1))

    # Plot empirical distribution CDF versus Normal CDF with same mean and
    # stdev
    if plot:
        fig, ax = plt.subplots()
        fig.set_size_inches((12, 6))
        ax.plot(x, y, c='r', ls='--', lw=1.5, alpha=.8, label='ECDF')
        ax.plot(x, norm_cdf,
                alpha=.3, ls='-', c='b', lw=5,
                label='Normal CDF')
        ax.legend(loc='best')
        plt.show(fig)
        plt.close(fig)

        # TODO calculate omega ratio


def sortino(returns, target_rtn=0, factor=1, return_type='log'):
    '''
    Sortino I.I.D ratio caluclated using Lower Partial Moment.
    Result should be the same as `sortino_iid`.
    '''
    validate_return_type(return_type)

    if return_type == 'pct':
        returns = pct_to_log_return(returns)

    if isinstance(returns, pd.DataFrame) or isinstance(returns, pd.Series):
        return (returns.mean() - target_rtn) / \
               np.sqrt(LPM(returns, target_rtn, 2)) * factor
    else:
        return np.nanmean(returns - target_rtn) / \
               np.sqrt(LPM(returns, target_rtn, 2)) * factor
        # else:
        #     mean = returns_gmean(returns)
        #     return (mean - target_rtn) / \
        #         np.sqrt(LPM(returns, target_rtn, 2)) * factor


def sortino_iid(df, bench=0, factor=1, return_type='log'):
    validate_return_type(return_type)

    if isinstance(df, np.ndarray):
        df = pd.DataFrame(df)

    if return_type == 'pct':
        excess = pct_to_log_return(df - bench)
        # excess = returns_gmean(df) - bench
    else:
        excess = df - bench

    neg_rtns = excess.where(cond=lambda x: x < 0)
    neg_rtns.fillna(0, inplace=True)
    semi_std = np.sqrt(neg_rtns.pow(2).mean())

    # print(excess, semi_std, np.std(neg_rtns, ddof=0))

    return factor * excess.mean() / semi_std


# def rolling_lpm(returns, target_rtn, moment, window):
#     adj_returns = returns - target_rtn
#     adj_returns[adj_returns > 0] = 0
#     return pd.rolling_mean(adj_returns**moment,
#                            window=window, min_periods=window)


# def rolling_sortino(returns, window, target_rtn=0):
#     '''
#     This is ~150x faster than using rolling_ratio which uses rolling_apply
#     '''
#     num = pd.rolling_mean(returns, window=window,
#                           min_periods=window) - target_rtn
#     denom = np.sqrt(rolling_lpm(returns, target_rtn,
#                                 moment=2, window=window))
#     return num / denom


# def sharpe(returns, bench_rtn=0):
#     excess = returns - bench_rtn
#     if isinstance(excess, pd.DataFrame) or isinstance(excess, pd.Series):
#         return excess.mean() / excess.std(ddof=1)
#     else:
#         return np.nanmean(excess) / np.nanstd(excess, ddof=1)


def sharpe_iid(df, bench=0, factor=1, return_type='log'):
    validate_return_type(return_type)

    excess = df - bench
    if return_type == 'pct':
        excess = pct_to_log_return(excess)

    if isinstance(df, pd.DataFrame) or isinstance(df, pd.Series):
        # return factor * excess.mean() / excess.std(ddof=1)
        # if return_type == 'pct':
        #     excess_mean = returns_gmean(excess)
        # else:
        excess_mean = excess.mean()
        return factor * excess_mean / excess.std(ddof=1)
    else:
        # numpy way
        # if return_type == 'pct':
        #     excess_mean = returns_gmean(excess)
        # else:
        excess_mean = np.nanmean(excess, axis=0)
        return factor * excess_mean / np.nanstd(excess, axis=0, ddof=1)


def sharpe_iid_rolling(df, window, bench=0, factor=1, return_type='log'):
    '''
    Rolling sharpe ratio, unadjusted by time aggregation.
    '''
    validate_return_type(return_type)

    if return_type == 'pct':
        excess = pct_to_log_return(df - bench)
    else:
        excess = df - bench

    roll = excess.rolling(window=window)
    # return factor * (roll.mean() - bench) / roll.std(ddof=1)
    return factor * roll.mean() / roll.std(ddof=1)


def sharpe_iid_adjusted(df, bench=0, factor=1, return_type='log'):
    '''
    Adjusted Sharpe Ratio, acount for skew and kurtosis in return series.

    Pezier and White (2006) adjusted sharpe ratio.

    https://www.google.co.uk/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwi42ZKgg_TOAhVFbhQKHSXPDY0QFggcMAA&url=http%3A%2F%2Fwww.icmacentre.ac.uk%2Fpdf%2Fdiscussion%2FDP2006-10.pdf&usg=AFQjCNF9axYf4Gbz4TVdJUdM8o2M2rz-jg&sig2=pXHZ7M-n-PtNd2d29xhRBw

    Parameters:
        df : returns dataframe. Default should be log returns
        bench : benchmark return
        factor : time aggregation factor, default 1, i.e. not adjusted.
        return_type : {'log', 'pct'}, return series type, log or arithmetic
            percentages.
    '''
    sr = sharpe_iid(df, bench=bench, factor=1, return_type=return_type)

    if isinstance(df, pd.DataFrame) or isinstance(df, pd.Series):
        skew = df.skew()
        excess_kurt = df.kurtosis()
    else:
        skew = ss.skew(df, bias=False, nan_policy='omit')
        excess_kurt = ss.kurtosis(df, bias=False, fisher=True,
                                  nan_policy='omit')
    return adjusted_sharpe(sr, skew, excess_kurt) * factor


def adjusted_sharpe(sr, skew, excess_kurtosis):
    '''
    Adjusted Sharpe Ratio, acount for skew and kurtosis in return series.

    Pezier and White (2006) adjusted sharpe ratio.

    https://www.google.co.uk/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwi42ZKgg_TOAhVFbhQKHSXPDY0QFggcMAA&url=http%3A%2F%2Fwww.icmacentre.ac.uk%2Fpdf%2Fdiscussion%2FDP2006-10.pdf&usg=AFQjCNF9axYf4Gbz4TVdJUdM8o2M2rz-jg&sig2=pXHZ7M-n-PtNd2d29xhRBw

    Parameters:
        sr : sharpe ratio
        skew : return series skew
        excess_kurtosis : return series excess kurtosis
    '''
    # return sr * (1 + (skew / 6.0) * sr + (kurtosis - 3) / 24.0 * sr**2)
    return sr * (1 + (skew / 6.0) * sr + excess_kurtosis / 24.0 * sr ** 2)


def sharpe_non_iid(df, bench=0, q=trading_days, p_critical=.05,
                   return_type='log'):
    '''
    Return Sharpe Ratio adjusted for auto-correlation, iff Ljung-Box test
    indicates that the return series exhibits auto-correlation. Based on
    Andrew Lo (2002).

    Parameters:
        df : return series
        bench : risk free rate, default 0
        q : time aggregation frequency, e.g. 12 for monthly to annual.
            Default 255.
        p_critical : critical p-value to reject Ljung-Box Null, default 0.05.
        return_type : {'log', 'pct'}, return series type, log or arithmetic
            percentages.
    '''
    if type(q) is not np.int64 or type(q) is not np.int32:
        q = np.round(q, 0).astype(np.int64)

    sr = sharpe_iid(df, bench=bench, factor=1, return_type=return_type)

    if not isinstance(df, pd.DataFrame):
        adj_factor, pval = sharpe_autocorr_factor(df, q=q)
        if pval < p_critical:
            # reject Ljung-Box Null, there is serial correlation
            return sr * adj_factor
        else:
            return sr * np.sqrt(q)
    else:
        tests = [sharpe_autocorr_factor(df[col].dropna().values, q=q)
                 for col in df.columns]
        factors = [adj_factor if pval < p_critical else np.sqrt(q)
                   for adj_factor, pval in tests]
        res = pd.Series(factors, index=df.columns)

        return res.multiply(sr)


def sharpe_autocorr_factor(returns, q):
    '''
    Auto-correlation correction for Sharpe ratio time aggregation based on
    Andrew Lo's 2002 paper.

    Link:
    https://www.google.co.uk/url?sa=t&rct=j&q=&esrc=s&source=web&cd=1&cad=rja&uact=8&ved=0ahUKEwj5wf2OjO_OAhWDNxQKHT0wB3EQFggeMAA&url=http%3A%2F%2Fedge-fund.com%2FLo02.pdf&usg=AFQjCNHbSz0LDZxFXm6pmBQukCfAYd0K7w&sig2=zQgZAN22RQcQatyP68VKmQ

    Parameters:
        returns : return sereis
        q : time aggregation factor, e.g. 12 for monthly to annual,
        255 for daily to annual

    Returns:
        factor : time aggregation factor
        p-value : p-value for Ljung-Box serial correation test.
    '''
    # Ljung-Box Null: data is independent, i.e. no auto-correlation.
    # smaller p-value would reject the Null, i.e. there is auto-correlation
    acf, _, pval = sts.acf(returns, unbiased=False, nlags=q, qstat=True)
    term = [(q - (k + 1)) * acf[k + 1] for k in range(q - 2)]
    factor = q / np.sqrt(q + 2 * np.sum(term))

    return factor, pval[-2]


def annualized_pct_return(total_return, days, ann_factor=365.):
    '''
    Parameters:
        total_return: total pct equity curve, e.g. if return is +50%, then this
            should be 1.5 (e.g. 1. + .5)
        days : number of days in period.
        ann_factor : number of days in a year
    Returns:
        Annualized percentage return.
    '''
    years = days / ann_factor
    ann = np.power(total_return, 1 / years) - 1
    return ann


def annualized_log_return(total_return, days, ann_factor=365.):
    '''
    Parameters:
        total_return: total log return, e.g. if return is +50%, then this
            should be 0.5, e.g. not 1.5.
        days : number of days in period.
        ann_factor : number of days in a year
    Returns:
        Annualized percentage return.
    '''

    years = days / ann_factor
    ann = total_return / years
    return ann


if __name__ == 'main':
    pass
