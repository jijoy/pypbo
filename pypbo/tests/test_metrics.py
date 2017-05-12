import pytest
import numpy as np
import pandas as pd

import pypbo as pbo
import pypbo.perf as perf


# TODO test scripts


def test_log_returns():
    '''
    Test log return logic. Asserts that cumulative value is the same as
    generated data.
    '''
    # generate data
    np.random.seed(7)
    tests = pd.Series([1 + np.random.rand() for _ in range(100)])
    log_rtns = perf.log_returns(tests)

    reconstruct = tests.head(1).values * np.exp(log_rtns.cumsum())

    assert(np.allclose(tests, reconstruct))


def test_pct_to_log_return():
    np.random.seed(7)
    tests = pd.Series([1 + np.random.rand() for _ in range(100)])

    pct_rtns = tests.pct_change().fillna(0)
    log_rtns = perf.pct_to_log_return(pct_rtns)

    recon1 = (1 + pct_rtns).cumprod()
    recon2 = np.exp(log_rtns.cumsum())

    assert(np.allclose(recon1, recon2))


def test_sharpe_iid():
    data = np.array([0.259,
                     .198,
                     .364,
                     -.081,
                     .057,
                     .055,
                     .188,
                     .317,
                     .24,
                     .184,
                     -.01,
                     .526])

    # numpy array
    sharpe = perf.sharpe_iid(data, bench=.05, factor=1, return_type='log')

    assert(np.isclose(sharpe, .834364))

    sharpe = perf.sharpe_iid(data, bench=.05, factor=1, return_type='pct')

    assert(np.isclose(sharpe, 0.8189144744629443))

    # turn data to pandas.Series
    data = pd.Series(data)

    sharpe = perf.sharpe_iid(data, bench=.05, factor=1, return_type='log')

    assert(np.isclose(sharpe, .834364))

    sharpe = perf.sharpe_iid(data, bench=.05, factor=1, return_type='pct')

    assert(np.isclose(sharpe, 0.8189144744629443))


def test_sortino_iid():
    '''
    Test both `sortino_iid` and `sortino`.
    '''
    data = np.array([.17,
                     .15,
                     .23,
                     -.05,
                     .12,
                     .09,
                     .13,
                     -.04])

    ratio = perf.sortino_iid(data, bench=0, factor=1, return_type='log')
    print(ratio)
    assert(np.isclose(ratio, 4.417261))

    ratio = perf.sortino(data, target_rtn=0, factor=1, return_type='log')
    assert(np.isclose(ratio, 4.417261))

    data = pd.DataFrame(data)
    ratio = perf.sortino_iid(data, bench=0, factor=1, return_type='log')
    print(ratio)
    assert(np.isclose(ratio, 4.417261))

    ratio = perf.sortino(data, target_rtn=0, factor=1, return_type='log')
    assert(np.isclose(ratio, 4.417261))


def test_omega():
    '''
    Based on numerical example found here:

    http://investexcel.net/calculate-the-omega-ratio-with-excel/

    '''
    data = np.array([.0089,
                     .0012,
                     -.002,
                     .01,
                     -.0002,
                     .02,
                     .03,
                     .01,
                     -.003,
                     .01,
                     .0102,
                     -.01])
    mar = .01

    omega = perf.omega(data, target_rtn=mar, return_type='log')

    assert(np.isclose(omega, .463901689))

    # DataFrame version.
    df = pd.DataFrame(data)

    omega = perf.omega(df, target_rtn=mar, return_type='log')

    assert(np.isclose(omega, .463901689))


def test_annualized_log_return():
    log_rtn = 0.51470826725926955
    test_val = perf.annualized_log_return(log_rtn, days=827, ann_factor=365.)
    assert(np.isclose(test_val, 0.22716870320390978))

def test_annualized_pct_return():
    tr = 1.673150317863489
    test_val = perf.annualized_pct_return(tr, days=827, ann_factor=365.)
    assert(np.isclose(test_val, 0.25504157961707952))

