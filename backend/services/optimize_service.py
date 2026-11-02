import logging as lg
import sqlite3 as sq
import uuid as uu
from concurrent.futures import Future
from contextlib import closing
from typing import Any, cast

import fastapi as fa
import numpy as np
import pandas as pan
import scipy.interpolate as inp
import scipy.optimize as op

import config.config as cn

log = lg.getLogger(__name__)

jobs: dict[Any, Any] = {}
fut: dict[Any, Any] = {}
res: dict[Any, Any] = {}


def get_progress(job_id: str) -> dict:
    """Get progress for a certain job id"""
    global jobs, fut
    job = jobs.get(job_id)
    if job is None:
        raise fa.HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    else:
        if cast(Future, fut[job_id].cancelled()):
            jobs[job_id] = "cancelled"
        elif cast(Future, fut[job_id].running()):
            jobs[job_id]["status"] = "running"
        elif cast(Future, fut[job_id].done()):
            try:
                res[job_id] = fut[job_id].result()
                print(res[job_id])
                jobs[job_id]["status"] = "completed"
            except Exception as e:
                jobs[job_id]["status"] = "failed"
                msg = f"{type(e).__name__}: {e} - {e.__cause__}"
                lg.error(msg)
                jobs[job_id]["message"] = msg
    return job


def new_job(cons: dict) -> str:
    global jobs
    job_id = str(uu.uuid4())
    jobs[job_id] = {"progress": 0.0, "status": "created", "constraints": cons}
    lg.info(f"Job '{job_id}' created")
    return job_id


def def_constraints(ret: np.ndarray, lim: dict) -> list:
    """
    Function to define constraint based on data

    Parameters:
        ret (np.ndarray): DataFrame with returns per equity
        lim (dict): Dictionnary with limit rules

    Returns:
        result (list)
    """
    cons = [{"type": "eq", "fun": lambda w: np.sum(w) - 1}]
    for elem in lim:
        cons.append(
            {
                "type": "ineq",
                "fun": lambda w, elem=elem: lim[elem]["fun"](w, ret, lim[elem]["lim"]),
            }
        )
    return cons


def set_future(future: Future, job_id: str) -> None:
    global fut
    fut[job_id] = future


def post_optimize(cons: dict, job_id: str) -> None:
    global jobs
    # Data for optimization
    w0 = np.array(cons["w0"])
    ind = cons["indus"]
    nb = cons["nb"]
    name = cons["ticker"]
    with closing(sq.connect("database/database.db")) as conn:
        query = f"SELECT * FROM thematic_score WHERE Ticker IN ({','.join('?' * nb)})"
        data = pan.read_sql(query, conn, params=name)
        cursor = conn.execute("PRAGMA table_info(returns)").fetchall()
        nt = [row[1] for row in cursor]
        ro = np.array([na in nt for na in name])
        if ro.all():
            query = f"SELECT {','.join(name)} FROM returns"
            retEq = pan.read_sql(query, conn)
        else:
            tmp = np.array(name)
            tmp = (tmp[~ro]).tolist()
            raise ValueError(f"Column {', '.join(tmp)} not in returns")
    sc = data["Score"].to_list()

    # Contraints
    indus = matrix_correspondance(retEq, data, "Industry")
    lim = {
        "Industry": {"fun": industry_constraint, "lim": (w0 @ indus) * ind},
        "VaR": {"fun": var_constraint, "lim": cons["var"] / 100},
        "Volatility": {"fun": vol_constraint, "lim": 0.2},
    }
    bounds = [cons["bounds"] for _ in range(nb)]

    # Boundaries for each position
    maxsc = maxScore(sc, bounds[0])  # Maximum Thematic score
    var = calc_error(retEq, data)  # Calculate errors
    param = np.arange(cons["ramp"][0], cons["ramp"][1], cons["ramp"][2])  # Temperature ramp

    # Initialize data
    retEq_np = np.array(retEq)
    it = int(np.floor(len(retEq) / 4 - 1))
    w = np.zeros(len(cons["w0"]))
    wd = np.zeros((it, 4, len(cons["w0"])))
    stat = np.zeros((it, 4))
    msg = np.full((it, 3), "", dtype=str)
    idx = np.zeros((it + 1, len(cons["w0"])))
    ww0 = drift_weight(retEq_np[0:4], cons["w0"])

    # Initial optimization
    lg.info(f"Job '{job_id}' running")
    w, stat[0], msg[0], idx[0] = optimize_portfolio_Bayes(
        param.tolist(),
        sc,
        retEq_np[0:8],
        maxsc,
        bounds,
        def_constraints(retEq_np[0:8], lim),
        ww0[0],
        var,
    )
    progress = (len(retEq) - 12) // 4
    # Optimization
    for index, i in enumerate(range(12, len(retEq), 4)):
        cons["progress"] = index / progress * 100
        wd[index] = drift_weight(retEq_np[i - 4 : i], w)  # Drift previous weights
        w, stat[index + 1], msg[index + 1], idx[index + 1] = optimize_portfolio_Bayes(
            param.tolist(),
            sc,
            retEq_np[i - 8 : i],
            maxsc,
            bounds,
            def_constraints(retEq_np[i - 8 : i], lim),
            wd[index, -1],
            var,
        )
    cons["progress"] = 100.0
    np.savez(
        f"results/{job_id}.npz",
        w=wd,
        stat=stat,
        msg=msg,
        idx=idx,
        name=name,
        w0=w0,
        maxsc=maxsc,
    )


def matrix_correspondance(retEq: pan.DataFrame, data: pan.DataFrame, name: str) -> np.ndarray:
    """
    Make a binary matrix to indicate to which industry/Country/... the asset is part of.

    Parameters:
        retEq (pan.DataFrame): DataFrame with return of each asset per column
        data (pan.DataFrame): DataFrame with scoring information
        name (str): Column to take

    Returns:
        indus (np.ndarray)
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


def maxScore(sc: list, bounds: tuple) -> float:
    """
    Calculate max score based on boundary limit for weights

    Parameters:
        sc (list): Scores
        bounds (tuple): (lower range, upper range)

    Returns:
        value (float)
    """
    sc2 = sorted(sc, reverse=True)
    remaining = 1 - len(sc) * bounds[0]
    w = [bounds[0]] * len(sc)
    dw = bounds[1] - bounds[0]
    for i in range(len(sc)):
        if dw < remaining:
            w[i] += dw
            remaining -= dw
        else:
            w[i] += remaining
            break
    return np.dot(w, sc2)


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
        retEq (np.ndarray): DataFrame with returns per equity
        w0 (np.ndarray): Initial weights

    Returns:
        result (np.ndarray)
    """
    new_w = drift_weight(retEq, w0)
    return (retEq * new_w).sum(axis=1)


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
        w (np.ndarray): Weights
        ret (np.ndarray): Close value data frame with each equity as column
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


def es_constraint(w: np.ndarray, ret: np.ndarray, lim: float) -> float:
    """
    Function for constraint of portfolio optimization on ES

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for ES

    Returns:
        score (float)
    """
    es = calc_ES(w, ret)
    return abs(lim - es)


def var_constraint(w: np.ndarray, ret: np.ndarray, lim: float) -> float:
    """
    Function for constraint of portfolio optimization on VaR

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for VaE

    Returns:
        score (float)
    """
    es = calc_VaR(w, ret)
    return abs(lim - es)


def industry_constraint(w: np.ndarray, ret: np.ndarray, ind: np.ndarray, limInd: list) -> float:
    """
    Function for constraint of portfolio optimization on industry allocation

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        ind (np.array): Matrix of industry allocation per position
        lim (list): limit for each industry allocation

    Returns:
        score (float)
    """
    wd = drift_weight(ret, w)
    dist = ((wd @ ind).sum(axis=0)) / len(ret)
    return np.sum(abs(limInd - dist))


def vol_constraint(w: np.ndarray, ret: np.ndarray, lim: float) -> float:
    """
    Function for constraint of portfolio optimization on annualized Volatility

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for annualized Volatility

    Returns:
        score (float)
    """
    histvar = drift_return(ret, w)
    vol = np.std(histvar) * np.sqrt(52)
    return abs(lim - vol)


def calc_error(
    retEq: pan.DataFrame, data: pan.DataFrame, n: int = 1000, alpha: float = 0.975
) -> list:
    """
    Calculate error (Variance) on annualized return, volatility, industry distribution,
    VaR and thematic score.

    Parameters:
        retEq (pan.DataFrame): DataFrame with return of each asset per column
        data (pan.DataFrame): DataFrame with scoring information
        n=1000 (int): Number of bootstrap
        alpha=0.975 (float): Confidence level

    Returns:
        Var (list): Annualized return, Annualized volatility, industry distribution,
        VaR and thematic score

    Notes:
        - Return the variance as this is used for Bayesian function
        - Volatility and Return use a 52 week rolling window
        - Bootstrap on score (with perturbation) for thematic score
    """
    # Volatility error
    vol_err = []
    for asset in retEq.columns:
        roll_vol = retEq[asset].rolling(window=52).std() * np.sqrt(52)
        vol_err.append(roll_vol.var())

    # Error on annualized returns = sd(1-year rolling window annualized returns)
    ret_err = []
    for asset in retEq.columns:
        roll_ret = (
            (1 + retEq[asset])
            .rolling(window=52)
            .apply(lambda x: np.prod(x) ** (52 / len(x)) - 1, raw=False)
        )
        ret_err.append(roll_ret.var())

    # Error on Thematic ratio by bootstrapping on scoring function
    them_err = []
    val = data.iloc[:, 4:14].copy()
    col_to_clip = [
        "Revenue",
        "Thematic",
        "Pipeline Maturity",
        "Pipeline Breadth",
        "Pipeline Differentiation",
        "Novelty of the technology",
        "Validation",
        "Number of active partnerships",
        "Ecosystem component",
    ]
    for _ in range(n):
        # Add pertubation
        pertubed = val + np.random.randn(
            *val.shape,
        )
        # Clip
        pertubed[col_to_clip] = pertubed[col_to_clip].clip(0, 1)
        # Calc score
        scb = pertubed.apply(lambda x: cn.scoreData(x, "config/weight.json"), axis=1)
        them_err.append(scb)
    them_err2 = np.array(them_err)
    them_err2 = them_err2.var(axis=0)
    # Mean of each asset error
    var = [np.mean(ret_err), np.mean(vol_err), np.mean(them_err2)]
    return var


def entropy_Shannon(w: np.ndarray, w0: np.ndarray) -> float:
    """
    Shanon relative entropy

    Parameters:
        w (np.array): Weights
        w0 (np.array): Initial weights

    Returns:
        Entropy (float)
    """
    return sum((w * np.log(w / w0)).sum(axis=1))


def chi2(
    w: np.ndarray, score: list, ret: np.ndarray, maxsc: float, var: list, w0: np.ndarray
) -> float:
    """
    Chi2 function for the Bayesian optimization. Take into account thematic score,
    return and volatility.

    Parameters:
        w (np.array): Weights
        score (list): Thematic score
        ret (np.array): Close value data frame with each equity as column
        maxsc (float): Maximum thematic score given equity
        t (float): Temperature
        var (list): Variance for each component of the Chi2 function
        w0 (list): Initial weights

    Returns:
        Chi2 (float)
    """
    histvar = drift_return(ret, w)
    ret_2month = (1 + histvar).prod() - 1
    ratio = np.dot(w, score) / maxsc
    ratio = np.mean(ratio)
    return -((ratio) ** 2 / var[0] + (ret_2month) ** 2 / var[1]) / 2


def objective_Bayes(
    w: np.ndarray,
    score: list,
    ret: np.ndarray,
    maxsc: float,
    t: float,
    var: list,
    w0: np.ndarray,
) -> float:
    """
    Objective function for the Bayesian optimization. Take into account thematic score,
    return and volatility.

    Parameters:
        w (list): Weights
        score (list): Thematic score
        ret (np.array): Close value data frame with each equity as column
        maxsc (float): Maximum thematic score given equity
        t (float): Temperature
        var (list): Variance for each component of the Chi2 function
        w0 (list): Initial weights

    Returns:
        score (float): Score to minimize
    """
    ww = drift_weight(ret, w)
    return chi2(ww, score, ret, maxsc, var, w0) + t * entropy_Shannon(ww, w0)


def optimize_portfolio_Bayes(
    t: list,
    sc: list,
    retEq: np.ndarray,
    maxsc: float,
    bounds: list,
    cons: list,
    w0: np.ndarray,
    var: list,
    round: float = 0.005,
) -> tuple:
    """
    Optimize portfolio using bayesian maximum entropy

    Parameters:
        t (list): Temperature for maximum entropy
        sc (list): Thematic score
        retEq (np.array): Close value data frame with each equity as column
        maxsc (float): Maximum thematic score given equity
        bounds (list): List of maximum allocation for each position as tuple
        cons (list): Constraints as dictionary form as required by SciPy
        w0 (np.array): Initial weights
        var (list): Variance for each component of the Chi2 function
        round=0.005 (float): Discretization of weight to reduce turnover
    Returns:
        w (list): Weights, metrics, opti messages, rebalanced list
    """
    stat = np.zeros((len(t), 4))
    wr = np.zeros(len(w0))
    for i, p in enumerate(t):
        res = op.minimize(
            objective_Bayes,
            w0,
            args=(sc, retEq, maxsc, p, var, w0),
            method="slsqp",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 1000, "ftol": 1e-4},
        )
        # Discretization of weight
        wreal = discretize(res.x, round)
        w = drift_weight(retEq, wreal)
        # Calculation of energy
        s = entropy_Shannon(w, w0)
        c = chi2(w, sc, retEq, maxsc, var, w0)
        stat[i] = [p, p * s - c, c, s]

    # Look for optimal temperature
    spline = inp.CubicSpline(stat[:, 0], stat[:, 2])
    f1 = spline.derivative(1)
    f2 = spline.derivative(2)
    grid = np.linspace(stat[:, 0].min(), stat[:, 0].max(), 2000)
    kappa = np.abs(f2(grid)) / (1 + f1(grid) ** 2) ** 1.5
    ideal = grid[np.argmax(kappa)]

    # Optimize according to optimal temperature
    res = op.minimize(
        objective_Bayes,
        w0,
        args=(sc, retEq, maxsc, ideal, var, w0),
        method="slsqp",
        bounds=bounds,
        constraints=cons,
        options={"maxiter": 1000, "ftol": 1e-4},
    )
    wreal = discretize(res.x, round)
    w = drift_weight(retEq, res.x)
    s = entropy_Shannon(w, w0)
    c = chi2(w, sc, retEq, maxsc, var, w0)

    # Rebalancing
    diff = abs(wreal - w0)
    idx = diff > round
    wr[idx] = discretize(wreal)[idx]
    wr[~idx] = wreal[~idx]
    wr /= wr.sum()

    return (
        wr,
        [ideal, ideal * s - c, c, s],
        np.array([str(res.nit), str(res.message), str(res.success)]),
        (res.x - w0) * idx.astype(int),
    )


def optimize_portfolio(
    param: list,
    sc: list,
    retEq: pan.DataFrame,
    maxsc: float,
    bounds: list,
    cons: list,
    w0: list,
) -> list:
    """
    Optimize portfolio

    Parameters:
        param (list): Hyperparameter value
        sc (list): Thematic score
        retEq (pan.DataFrame): Close value data frame with each equity as column
        maxsc (float): Maximum thematic score given equity
        bounds (list): List of maximum allocation for each position as tuple
        cons (list): Constraints as dictionary form as required by SciPy
        w0 (list): Initial weights

    Returns:
        w (list): Optimal weights
    """
    w = []
    for p in param:
        res = op.minimize(
            objective,
            w0,
            args=(sc, retEq, p[0], p[1], p[2], maxsc),
            method="slsqp",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 1000, "ftol": 1e-9},
        )
        w.append(res.x)
    return w


def objective(
    w: list, score: list, ret: np.ndarray, m: float, cp: float, k: float, maxsc: float
) -> float:
    """
    Objective function for the optimization. Take into account thematic score,
    return and volatility.

    Parameters:
        w (list): Weights
        score (list): Thematic score
        ret (pan.DataFrame): Close value data frame with each equity as column
        m (float): Weight of the thematic score
        cp (float): Weight of the annualized return
        k (float): Weight of the annualized volatility
        maxsc (float): Maximum thematic score given equity

    Returns:
        score (float): Score to minimize
    """
    histvar = ret @ w
    ret_annual = pow(1 + histvar.mean(), 52) - 1
    vol = np.std(histvar) * np.sqrt(52)
    return -m * np.dot(w, score) / maxsc - cp * ret_annual / 0.20 + k * vol / 0.2
