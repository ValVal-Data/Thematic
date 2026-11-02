import logging as lg
import sqlite3 as sq
from contextlib import closing
from typing import cast

import numpy as np
import pandas as pan
import scipy.stats as scp

import common.utils as ut
import database.database as db

log = lg.getLogger(__name__)


def get_perf(job_id) -> dict:
    res = {}
    # Reload optimization
    re = np.load(f"results/{job_id}.npz")
    nb = len(re["name"])
    res["name"] = re["name"]
    with closing(sq.connect("database/database.db")) as conn:
        query = f"SELECT * FROM thematic_score WHERE Ticker IN ({','.join('?' * nb)})"
        dataf = pan.read_sql(query, conn, params=re["name"])
        cursor = conn.execute("PRAGMA table_info(returns)").fetchall()
        nt = [row[1] for row in cursor]
        ro = np.array([na in nt for na in re["name"]])
        if ro.all():
            query = f"SELECT {','.join(re['name'])} FROM returns"
            retEq = pan.read_sql(query, conn)
            query = f"SELECT {','.join(re['name'])} FROM price"
            dataPos = pan.read_sql(query, conn)
            query = f'SELECT {",".join(re["name"])},"SP500","MSCI-World","MSCI-ACWI" FROM price'
            dataClose = pan.read_sql(query, conn)
        else:
            tmp = np.array(re["name"])
            tmp = (tmp[~ro]).tolist()
            raise ValueError(f"Column {', '.join(tmp)} not in returns")
        sc = dataf["Score"].to_list()

    cost = re["idx"][1:-1]

    conv = db.load_convert("config/convert.json")

    # Make continuous weight table
    ww = np.zeros((len(re["w0"]), 252))
    for i in range(len(re["w0"])):
        ww[i] = re["w"][:-1, :, i].flatten()
    ww = ww.transpose()

    # Add info about companies from the Universe
    da = pan.DataFrame(ww.mean(axis=0), columns=["w0"], index=retEq.columns)
    da["Industry"] = da.index.map(lambda x: dataf[dataf["NameC"] == x].iloc[0].loc["Industry"])
    da["Location"] = da.index.map(lambda x: dataf[dataf["NameC"] == x].iloc[0].loc["Location"])
    da["Cap"] = da.index.map(lambda x: dataf[dataf["NameC"] == x].iloc[0].loc["Cap"])
    da["Cost"] = da["Cap"].map(conv["cost_cat"]) / 10000

    # Calculate performances
    turn, co = calc_turnover(cost, da)
    performance = pan.DataFrame(turn, columns=["Turnover"])
    res["turnover"] = turn
    performance["Cost"] = co  # Calculate rebalancing cost
    return_month = ut.returns(dataPos[0::4])[1:-1]
    performance["Return"] = np.array((return_month * ww[0::4]).sum(axis=1))
    performance["Return net"] = performance["Return"] - performance["Cost"]
    performance["Cum Return"] = (1 + performance["Return"]).cumprod()
    performance["Cum Return net"] = (1 + performance["Return net"]).cumprod()
    n_months = len(performance)
    n_year = n_months / 12
    res["date_month"] = return_month.index.to_list()
    res["Return"] = performance["Return"]
    res["Return net"] = performance["Return net"]
    res["Cum Return net"] = performance["Cum Return net"]
    res["Cum Return"] = performance["Cum Return"]
    res["cagr_gross"] = (performance["Cum Return"].iloc[-1]) ** (1 / n_year) - 1
    res["cagr_net"] = (performance["Cum Return net"].iloc[-1]) ** (1 / n_year) - 1
    res["cost_annual"] = res["cagr_gross"] - res["cagr_net"]

    # Calculate exposure
    indus = matrix_correspondance(
        retEq, dataf, "Industry"
    )  # Correspondance matrix for industry
    loca = matrix_correspondance(retEq, dataf, "Location")  # Correspondance matrix for location
    capi = matrix_correspondance(retEq, dataf, "Cap")  # Correspondance
    res["exp_ind"] = pan.DataFrame(ww @ indus, columns=np.unique(dataf["Industry"]))
    res["exp_loca"] = pan.DataFrame(ww @ loca, columns=np.unique(dataf["Location"]))
    res["exp_cap"] = pan.DataFrame(ww @ capi, columns=np.unique(dataf["Cap"]))
    res["exp_w"] = pan.DataFrame(ww).rolling(24).mean().dropna()
    res["exp_w"] = res["exp_w"][res["exp_w"].median().sort_values(ascending=False).index]
    res["exp_theme"] = pan.Series(np.dot(ww, sc) / re["maxsc"])

    # Concentration metrics
    wr = pan.DataFrame(ww)
    wr = np.array(wr.rolling(24).mean().dropna())
    res["hhi"] = calc_HHI(wr)
    res["cr5"] = calc_CR(wr, 5)
    res["cr8"] = calc_CR(wr, 8)
    res["cr3"] = calc_CR(wr, 3)

    # Risk metrics
    b1 = dataClose[["SP500", "MSCI-World", "MSCI-ACWI"]]
    b1 = ut.returns(b1[0::4])[1:-1]
    fund_met = calc_metrics_roll(performance["Return net"], 4)
    world_met = calc_metrics_roll(b1["MSCI-World"], 4)
    sp500_met = calc_metrics_roll(b1["SP500"], 4)
    res["met"] = {
        "Fund": fund_met.tolist(),
        "MSCI-World": world_met.tolist(),
        "sp500": sp500_met.tolist(),
    }
    b1_cum = (1 + b1).cumprod()
    b1_cum["Fund"] = res["Cum Return net"].to_list()
    res["bench"] = b1_cum.to_dict()

    # PCA factor regression
    mat = np.array(
        [performance["Return net"], b1["MSCI-World"], b1["MSCI-ACWI"], b1["SP500"]]
    ).transpose()
    pc = pca(mat)
    res["pca"] = [x.tolist() for x in pc]
    be = pca_factor(mat, 2)
    be = np.round(be, 1)
    res["pca_mat"] = mat
    res["pca_factor"] = be
    res["bench_name"] = ["Thematic", "MSCI-World", "MSCI-ACWI", "SP500"]

    # Change type to send it
    for key, value in res.items():
        if isinstance(value, np.ndarray):
            res[key] = res[key].tolist()
        if isinstance(value, np.float64):
            res[key] = float(res[key])
        elif isinstance(value, pan.DataFrame):
            res[key] = res[key].to_dict()
        elif isinstance(value, pan.Series):
            res[key] = res[key].to_list()

    return res


def matrix_correspondance(retEq: pan.DataFrame, data: pan.DataFrame, name: str) -> np.ndarray:
    """
    Make a binary matrix to indicate to which industry/Country/... the asset is part of.

    Parameters:
        retEq (pan.DataFrame): DataFrame with return of each asset per column
        data (pan.DataFrame): DataFrame with scoring information
        name (str): Column to take

    Returns:
        indus (np.array)
    """
    ind = []
    for eq in retEq.columns:
        ind.append(data[data["NameC"] == eq].iloc[0][name])
    ind = pan.DataFrame(ind, columns=[name])
    indus = []
    for eq in np.unique(ind[name]):
        temp = ind[name] == eq
        indus.append(np.array(temp.astype(float)))
    return np.array(indus).transpose()


def pca(a: np.ndarray) -> tuple:
    """
    Calculate Principal component analysis

    Parameters:
        a (np.array): Matrix of returns.

    Returns:
        Result (tuple): Eigenvalues, Eigenvectors, Varianced per component
    """
    cov = np.cov(a, rowvar=False)
    val, vect = np.linalg.eigh(cov)
    return val[::-1], vect[:, ::-1], val[::-1] / val[::-1].sum()


def pca_factor(mat: np.ndarray, cp: int = 2) -> np.ndarray:
    """
    Calculate Principal component analysis

    Parameters:
        mat (np.array): Matrix of returns.
        cp (int): Number of component to take

    Returns:
        pan.DataFrame: Eigenvalues, Eigenvectors, Varianced per component

    Notes:
        - The function also plot the variance explained per components and
            the heatmap of the pca
    """
    pc = pca(mat)
    fact_ret = mat @ pc[1]
    # Fit
    f = fact_ret[:, :cp]
    xreg = np.column_stack([np.ones(len(f)), f])
    beta, resid, ran, s = np.linalg.lstsq(xreg, mat[:, 0], rcond=None)
    # Error
    y_pred = xreg @ beta
    s_res = np.sum((mat[:, 0] - y_pred) ** 2)
    s_tot = np.sum((mat[:, 0] - mat[:, 0].mean()) ** 2)
    r2 = 1 - s_res / s_tot
    tracking_err = np.std(mat[:, 0] - xreg @ beta) * 100
    # Table and plot
    be = pan.DataFrame([beta * 100], columns=["Alpha", "Beta,Market", "Beta,Theme"])
    be["Track"] = tracking_err * 100
    be["r2"] = r2
    be = abs(np.round(be.transpose(), 1))
    return be


def calc_turnover(cost: np.ndarray, da: pan.DataFrame) -> tuple:
    """
    Calculate turnover

    Parameters:
        cost (np.array): Matrix of returns.
        dda (pan.DataFrame): DataFrame with position informations

    Returns:
        result (tuple): turnover, cost
    """
    turnover = np.zeros(int(252 / 4))
    co = np.zeros(int(252 / 4))
    for i in range(len(cost)):
        current = cost[i]
        sell = -current[current < 0]
        buy = current[current > 0]
        if sell.sum() < buy.sum():
            best = sell
            mask = current < 0
        else:
            best = buy
            mask = current > 0
        turnover[i] = best.sum()
        if mask.sum() <= 0:
            co[i] = 0
        else:
            co[i] = sum(best * da["Cost"].loc[mask])
    return turnover, co


def calc_metrics_roll(
    ret: pan.Series, roll: int, alpha: float = 0.975, rf: float = 0.0
) -> np.ndarray:
    """
    Calculate metrics on a rolling windows

    Parameters:
        ret (pan.Series): Series with returns per equity
        roll (int): Size of the rolling window
        alpha=0.975 (float): Confidence level
        rf=0.0 (float): Reference rate

    Returns:
        result (np.array)
    """
    score = np.zeros((len(ret) - roll, 6))
    for ide, i in enumerate(range(roll, len(ret), 1)):
        score[ide] = calc_metrics(ret.iloc[i - roll : i], alpha=alpha, rf=rf, freq=12 // roll)
    return score


def calc_HHI(w: np.ndarray) -> np.ndarray:
    """
    Calculate Herfindahl-Hirschmann index

    Parameters:
        w (np.array): Weights

    Returns:
        result (np.array)
    """
    w2 = w**2
    return w2.sum(axis=1)


def calc_CR(w: np.ndarray, x: int) -> np.ndarray:
    """
    Calculate concentration ratio

    Parameters:
        w (np.array): Weights
        x (int): Number of value to take

    Returns:
        result (np.array)
    """
    w2 = [sorted(y, reverse=True) for y in w]
    return np.array([sum(y[:x]) for y in w2])


def discretize(val: np.ndarray, round: float = 0.005) -> np.ndarray:
    """
    Discretize weights

    Parameters:
        val (np.array): Returns
        round=0.005 (float): Value to round the weights to

    Returns:
        result (np.array)
    """
    wreal = np.round(val / round) * round
    wreal = np.maximum(wreal, 0)
    wreal /= wreal.sum()
    return wreal


def calc_ES(w: np.ndarray, ret: np.ndarray, alpha: float = 0.975) -> float:
    """
    Calculate Expected Shortfall (ES) using historical data

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level

    Returns:
        ES (float)
    """
    histvar = drift_return(ret, w)
    var_95 = np.quantile(histvar, 1 - alpha)
    es = -histvar[histvar < var_95].mean()
    return es


def calc_VaR(w: np.ndarray, ret: np.ndarray, alpha: float = 0.975) -> float:
    """
    Calculate Value at Risk (VaR) using historical data

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level

    Returns:
        VaR (float)
    """
    histvar = drift_return(ret, w)
    var_95 = np.quantile(histvar, 1 - alpha)
    return var_95


def drift_weight(retEq: np.ndarray, w0: np.ndarray) -> np.ndarray:
    """
    Drift weight based on returns

    Parameters:
        retEq (pan.DataFrame): DataFrame with returns per equity
        w0 (np.array): Initial weights

    Returns:
        result (np.array)
    """
    growth = (1 + retEq) * w0
    total = growth.sum(axis=1)
    new_w = growth / total.reshape(-1, 1)
    return new_w


def drift_return(retEq: np.ndarray, w0: np.ndarray) -> np.ndarray:
    """
    Drift returns

    Parameters:
        retEq (pan.DataFrame): DataFrame with returns per equity
        w0 (np.array): Initial weights

    Returns:
        result (np.array)
    """
    new_w = drift_weight(retEq, w0)
    return (retEq * new_w).sum(axis=1)


def calc_metrics(
    ret: pan.Series, alpha: float = 0.975, rf: float = 0.0, freq: int = 12
) -> tuple:
    """
    Calculate metrics

    Parameters:
        ret (pan.Series): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level
        rf=0.02 (float): Risk free reference rate

    Returns:
        metrics (tuple): Returns, Volatility, MDD, Sharpe ratio, VaR, ES
    """
    # Annualized return
    ret_annual = pow(1 + ret.mean(), freq) - 1
    # Volatility
    vol = np.std(ret) * np.sqrt(freq)
    # Max drawdown
    cm_index = (1 + ret).cumprod()
    r_max = cm_index.cummax()
    draw = cm_index / r_max - 1
    mdd = draw.min()
    # Sharpe ratio
    sharpe = (ret_annual - rf) / vol
    # Risk
    var_95 = ret.quantile(1 - alpha)
    es = -ret[ret < var_95].mean()
    return 100 * ret_annual, 100 * vol, 100 * mdd, sharpe, -100 * var_95, 100 * es


def calc_bench(ret: pan.DataFrame, bench: pan.DataFrame) -> tuple:
    """
    Calculate greeks (Alpha, Beta, Tracking error) of the portfolio against a benchmark

    Parameters:
        ret (pan.DataFrame): Close value data frame with each equity as column
        bench (pan.DataFrame): Close value data frame with benchmark as column

    Returns:
        metrics (tuple): Alpha, t-stat alpha, Beta, t-stat beta, tracking error
    """
    # Beta and alpha
    beta, alpha, r_val, p_val, std_er = scp.linregress(bench, ret)
    alpha_annual = pow(1 + cast(float, alpha), 52) - 1
    b_t_stat = cast(float, beta) / cast(float, std_er)
    # t-stat for alpha
    residual = ret - (alpha + beta * bench)
    n = len(ret)
    x_mean = np.mean(bench)
    sxx = np.sum((bench - x_mean) ** 2)
    sigma2 = np.sum(residual**2) / (n - 2)
    se_alpha = np.sqrt(sigma2 * (1 / n + x_mean**2 / sxx))
    t_alpha = alpha / se_alpha
    # Tracking error
    active_r = ret - bench
    tracking_err_week = np.std(active_r, ddof=1)
    tracking_err_annual = tracking_err_week * np.sqrt(52)
    return 100 * alpha_annual, t_alpha, beta, b_t_stat, 100 * tracking_err_annual
