#Portfolio optimization functions

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as scp
import scipy.optimize as op
import scipy.interpolate as inp
import pandas as pan
import glob as gb
from Source.Score import *

def pca(a:np.array)->np.array:
    """
    Calculate Principal component analysis

    Parameters:
        a (np.array): Matrix of returns.

    Returns:
        Result (list): Eigenvalues, Eigenvectors, Varianced per component
    """
    cov=np.cov(a,rowvar=False)
    val,vect=np.linalg.eigh(cov)
    return val[::-1],vect[:,::-1],val[::-1]/val[::-1].sum()

def pca_factor(mat:np.array,l:int)->pan.DataFrame:
    """
    Calculate Principal component analysis

    Parameters:
        mat (np.array): Matrix of returns.
        l (int): Number of component to take

    Returns:
        pan.DataFrame: Eigenvalues, Eigenvectors, Varianced per component

    Notes:
        - The function also plot the variance explained per components and the heatmap of the pca
    """
    pc=pca(mat)
    fact_ret=mat@pc[1]
    #Fit
    l=2
    f=fact_ret[:,:l]
    xreg=np.column_stack([np.ones(len(f)),f])
    beta,resid,ran,s=np.linalg.lstsq(xreg,mat[:,0],rcond=None)
    #Error
    y_pred=xreg@beta
    s_res=np.sum((mat[:,0]-y_pred)**2)
    s_tot=np.sum((mat[:,0]-mat[:,0].mean())**2)
    r2=1-s_res/s_tot
    tracking_err=np.std(mat[:,0]-xreg@beta)*100
    #Table and plot
    be=pan.DataFrame([beta*100],columns=["Alpha","Beta,Market","Beta,Theme"])
    be["Track"]=tracking_err*100
    be["r2"]=r2
    be=abs(np.round(be.transpose(),1))
    be.columns=["Fund"]
    pca_plot(pc,mat,l)
    return be

def pca_plot(pc:list,mat:np.array,l:int)->None:
    """
    Plot variance explained by PC and PC weight heatmap

    Parameters:
        pc (list): PCA result from pca function
        mat (np.array): Return list of the different assay
        l (int): Number of componenet taken
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,2,figsize=(7,3.5))

    ax[0].scatter(range(1,len(pc[2])+1),pc[2]*100)
    ax[0].set_ylabel("Variance explained (%)")
    ax[0].set_xlabel("Number of components")
    ax[0].set_title("Variance vs nb of components")
    ax[0].set_ylim((0,100))

    im=ax[1].imshow((-pc[1][:,0:2]).transpose(),cmap='coolwarm',aspect='auto',vmin=-1,vmax=1)
    ax[1].set_yticks(range(l),[f"PC{i+1}" for i in range(l)])
    ax[1].set_xticks(range(mat.shape[1]),["Thematic fund","MSCI-World","MSCI-ACWI","SP500"],rotation=45)
    ax[1].set_title("PCA Loadings Heatmaps")
    fig.colorbar(im,ax=ax[1],label="Loading weight")
    plt.tight_layout()
    plt.savefig("Figures/pca.png",dpi=300)
    plt.show()

def calc_turnover(cost:np.array,da:pan.DataFrame)->list:
    """
    Calculate turnover

    Parameters:
        cost (np.array): Matrix of returns.
        dda (pan.DataFrame): DataFrame with position informations

    Returns:
        result (list): turnover, cost
    """
    turnover=np.zeros(int(252/4))
    co=np.zeros(int(252/4))
    for i in range(len(cost)):
        current=cost[i]
        sell=-current[current<0]
        buy=current[current>0]
        if sell.sum()<buy.sum():
            best=sell
            mask=current<0
        else:
            best=buy
            mask=current>0
        turnover[i]=best.sum()
        if mask.sum()<=0:
            co[i]=0
        else:
            co[i]=sum(best*da["Cost"].loc[mask])
    return turnover,co

def def_constraints(ret:pan.DataFrame,lim:dict)->list:
    """
    Function to define constraint based on data

    Parameters:
        ret (pan.DataFrame): DataFrame with returns per equity
        lim (dict): Dictionnary with limit rules

    Returns:
        result (list)
    """
    cons=[{'type':'eq','fun':lambda w: np.sum(w)-1}]
    for elem in lim.keys():
      cons.append({'type':'ineq','fun':lambda w: lim[elem]["fun"](w,ret,lim[elem]["lim"])})
    return cons

def calc_metrics_roll(ret:pan.DataFrame,roll:int,alpha:float=0.975,rf:float=0.0)->np.array:
    """
    Calculate metrics on a rolling windows

    Parameters:
        ret (pan.DataFrame): DataFrame with returns per equity
        roll (int): Size of the rolling window
        alpha=0.975 (float): Confidence level
        rf=0.0 (float): Reference rate

    Returns:
        result (np.array)
    """
    score=np.zeros((len(ret)-roll,6))
    for ide,i in enumerate(range(roll,len(ret),1)):
        score[ide]=calc_metrics(ret.iloc[i-roll:i],alpha=alpha,rf=rf,freq=12/roll)
    return score

def calc_HHI(w:np.array)->np.array:
    """
    Calculate Herfindahl-Hirschmann index

    Parameters:
        w (np.array): Weights

    Returns:
        result (np.array)
    """
    w2=w**2
    return w2.sum(axis=1)

def calc_CR(w:np.array,x:int)->np.array:
    """
    Calculate concentration ratio

    Parameters:
        w (np.array): Weights
        x (int): Number of value to take

    Returns:
        result (np.array)
    """
    w2=[sorted(y,reverse=True) for y in w]
    return np.array([sum(y[:x]) for y in w2])

def drift_weight(retEq:np.array,w0:np.array)->np.array:
    """
    Drift weight based on returns

    Parameters:
        retEq (pan.DataFrame): DataFrame with returns per equity
        w0 (np.array): Initial weights

    Returns:
        result (np.array)
    """
    growth=(1+retEq)*w0
    total=growth.sum(axis=1)
    new_w=growth/total.reshape(-1,1)
    return new_w

def drift_return(retEq:np.array,w0:np.array)->np.array:
    """
    Drift returns

    Parameters:
        retEq (pan.DataFrame): DataFrame with returns per equity
        w0 (np.array): Initial weights

    Returns:
        result (np.array)
    """
    new_w=drift_weight(retEq,w0)
    return (retEq*new_w).sum(axis=1)

def discretize(val:np.array,round:float=0.005)->np.array:
    """
    Discretize weights

    Parameters:
        val (np.array): Returns
        round=0.005 (float): Value to round the weights to

    Returns:
        result (np.array)
    """
    wreal=np.round(val/round)*round
    wreal=np.maximum(wreal,0)
    wreal/=wreal.sum()
    return wreal

def calc_ES(w:np.array,ret:np.array,alpha:float=0.975)->float:
    """
    Calculate Expected Shortfall (ES) using historical data

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level

    Returns:
        ES (float)
    """
    histvar=drift_return(ret,w)
    var_95=np.quantile(histvar,1-alpha)
    es=-histvar[histvar<var_95].mean()
    return es

def calc_VaR(w:np.array,ret:np.array,alpha:float=0.975)->float:
    """
    Calculate Value at Risk (VaR) using historical data

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level

    Returns:
        VaR (float)
    """
    histvar=drift_return(ret,w)
    var_95=np.quantile(histvar,1-alpha)
    return var_95

def es_constraint(w:np.array,ret:np.array,lim:float)->float:
    """
    Function for constraint of portfolio optimization on ES

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for ES

    Returns:
        score (float)
    """
    es=calc_ES(w,ret)
    return abs(lim-es)

def var_constraint(w:np.array,ret:np.array,lim:float)->float:
    """
    Function for constraint of portfolio optimization on VaR

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for VaE

    Returns:
        score (float)
    """
    es=calc_VaR(w,ret)
    return abs(lim-es)

def industry_constraint(w:np.array,ret:np.array,ind:np.array,limInd:list)->float:
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
    wd=drift_weight(ret,w)
    dist=((wd@ind).sum(axis=0))/len(ret)
    return np.sum(abs(limInd-dist))

def vol_constraint(w:np.array,ret:np.array,lim:float)->float:
    """
    Function for constraint of portfolio optimization on annualized Volatility

    Parameters:
        w (np.array): Weights
        ret (np.array): Close value data frame with each equity as column
        lim (float): limit for annualized Volatility

    Returns:
        score (float)
    """
    histvar=drift_return(ret,w)
    vol=np.std(histvar)*np.sqrt(52)
    return abs(lim-vol)


def matrix_correspondance(retEq:pan.DataFrame,data:pan.DataFrame,name:str)->np.array:
    """
    Make a binary matrix to indicate to which industry/Country/... the asset is part of.

    Parameters:
        retEq (pan.DataFrame): DataFrame with return of each asset per column
        data (pan.DataFrame): DataFrame with scoring information
        name (str): Column to take

    Returns:
        indus (np.array)
    """
    ind=[]
    for eq in retEq.columns:
        ind.append(data[data["NameC"]==eq].iloc[0][name])
    ind=pan.DataFrame(ind,columns=[name])
    indus=[]
    for eq in np.unique(ind[name]):
        temp=ind[name]==eq
        indus.append(np.array(temp.astype(float)))
    return np.array(indus).transpose()


def calc_error(retEq:pan.DataFrame,data:pan.DataFrame,n:int=1000,alpha:float=0.975)->list:
    """
    Calculate error (Variance) on annualized return, volatility, industry distribution, VaR and thematic score. 

    Parameters:
        retEq (pan.DataFrame): DataFrame with return of each asset per column
        data (pan.DataFrame): DataFrame with scoring information
        n=1000 (int): Number of bootstrap
        alpha=0.975 (float): Confidence level

    Returns:
        Var (list): Annualized return, Annualized volatility, industry distribution, VaR and thematic score

    Notes:
        - Return the variance as this is used for Bayesian function
        - Volatility and Return use a 52 week rolling window
        - Bootstrap on score (with perturbation) for thematic score
    """
    #Volatility error
    vol_err=[]
    for asset in retEq.columns:
        roll_vol=retEq[asset].rolling(window=52).std()*np.sqrt(52)
        vol_err.append(roll_vol.var())

    #Error on annualized returns = sd(1-year rolling window annualized returns)
    ret_err=[]
    for asset in retEq.columns:
        roll_ret=((1+retEq[asset]).rolling(window=52).apply(lambda x: np.prod(x)**(52/len(x))-1,raw=False))
        ret_err.append(roll_ret.var())

    #Error on Thematic ratio by bootstrapping on scoring function
    them_err=[]
    val=data.iloc[:,3:13].copy()
    col_to_clip=['Revenue', 'Thematic', 'Pipeline Maturity', 'Pipeline Breadth',
        'Pipeline Differentiation', 'Novelty of the technology', 'Validation',
        'Number of active partnerships', 'Ecosystem component']
    for i in range(n):
        #Add pertubation
        pertubed=val+np.random.randn(*val.shape,)
        #Clip
        pertubed[col_to_clip]=pertubed[col_to_clip].clip(0,1)
        #Calc score
        scb=pertubed.apply(scoreData,axis=1)
        them_err.append(scb)
    them_err=np.array(them_err)
    them_err=them_err.var(axis=0)
    #Mean of each asset error
    var=[np.mean(ret_err),np.mean(vol_err),np.mean(them_err)]
    return var

def entropy_Shannon(w:np.array,w0:np.array)->float:
    """
    Shanon relative entropy

    Parameters:
        w (np.array): Weights
        w0 (np.array): Initial weights

    Returns:
        Entropy (float)
    """
    return sum((w*np.log(w/w0)).sum(axis=1))

def chi2(w:np.array,score:list,ret:np.array,maxsc:float,var:list,w0:list)->float:
    """
    Chi2 function for the Bayesian optimization. Take into account thematic score, return and volatility.

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
    histvar=drift_return(ret,w)
    ret_2month=(1+histvar).prod()-1
    ratio=np.dot(w,score)/maxsc
    ratio=np.mean(ratio)
    return -((ratio)**2/var[0]+(ret_2month)**2/var[1])/2

def objective_Bayes(w:list,score:list,ret:np.array,maxsc:float,t:float,var:list,w0:list)->float:
    """
    Objective function for the Bayesian optimization. Take into account thematic score, return and volatility.

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
    ww=drift_weight(ret,w)
    return chi2(ww,score,ret,maxsc,var,w0)+t*entropy_Shannon(ww,w0)

def optimize_portfolio_Bayes(t:list,sc:list,retEq:np.array,maxsc:float,bounds:list,cons:list,w0:np.array,var:list,round:float=0.005)->list:
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
    stat=np.zeros((len(t),4))
    wr=np.zeros(len(w0))
    for i,p in enumerate(t):
        res=op.minimize(
            objective_Bayes,
            w0,
            args=(sc,retEq,maxsc,p,var,w0),
            method='slsqp',
            bounds=bounds,
            constraints=cons,
            options={'maxiter':1000,'ftol':1e-4}
            )
        #Discretization of weight
        wreal=discretize(res.x,round)
        w=drift_weight(retEq,wreal)
        #Calculation of energy
        s=entropy_Shannon(w,w0)
        c=chi2(w,sc,retEq,maxsc,var,w0)
        stat[i]=[p,p*s-c,c,s]

    #Look for optimal temperature
    spline=inp.CubicSpline(stat[:,0],stat[:,2])
    f1=spline.derivative(1)
    f2=spline.derivative(2)
    grid=np.linspace(stat[:,0].min(),stat[:,0].max(),2000)
    kappa=np.abs(f2(grid))/(1+f1(grid)**2)**1.5
    ideal=grid[np.argmax(kappa)]

    #Optimize according to optimal temperature
    res=op.minimize(
        objective_Bayes,
        w0,
        args=(sc,retEq,maxsc,ideal,var,w0),
        method='slsqp',
        bounds=bounds,
        constraints=cons,
        options={'maxiter':1000,'ftol':1e-4}
        )
    wreal=discretize(res.x,round)
    w=drift_weight(retEq,res.x)
    s=entropy_Shannon(w,w0)
    c=chi2(w,sc,retEq,maxsc,var,w0)

    #Rebalancing
    diff=abs(wreal-w0)
    idx=diff>round
    wr[idx]=discretize(wreal)[idx]
    wr[~idx]=wreal[~idx]
    wr/=wr.sum()

    return wr,[ideal,ideal*s-c,c,s],np.array([str(res.nit),str(res.message),str(res.success)]),(res.x-w0)*idx.astype(int)

def recalc_portfolio(w:list,sc:list,retEq:pan.DataFrame,maxsc:float,ret:pan.DataFrame)->list:
    """
    Calculate metrics for portfolio given weight

    Parameters:
        w (list): Weight of each asset
        sc (list): Thematic score
        retEq (pan.DataFrame): Close value data frame with each equity as column
        maxsc (float): Maximum thematic score given equity
        retEq (pan.DataFrame): Close value data frame with each equity as column with benchmarks

    Returns:
        value (list): Return, Close, Theme ratio, Metrics, Benchmarks
    """
    histvar=[]
    price=[]
    theme_ratio=[]
    metrics=[]
    benches=[]
    for weight in w:
        histvar.append(retEq @ weight)
        price.append(100*((1+histvar[-1]).cumprod()-1))
        theme_ratio.append(round(np.dot(sc,weight)/maxsc*100,1))
        metrics.append(calc_metrics(histvar[-1]))
        benches.append(calc_bench(histvar[-1],ret["MSCI-World"]))
    return histvar,price,theme_ratio,metrics,benches

def optimize_portfolio(param:list,sc:list,retEq:pan.DataFrame,maxsc:float,bounds:list,cons:list,w0:list)->list:
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
    w=[]
    for p in param:
        res=op.minimize(
            objective,
            w0,
            args=(sc,retEq,p[0],p[1],p[2],maxsc),
            method='slsqp',
            bounds=bounds,
            constraints=cons,
            options={'maxiter':1000,'ftol':1e-9}
            )
        w.append(res.x)
    return w

def objective(w:list,score:list,ret:pan.DataFrame,m:float,l:float,k:float,maxsc:float)->float:
    """
    Objective function for the optimization. Take into account thematic score, return and volatility.

    Parameters:
        w (list): Weights
        score (list): Thematic score
        ret (pan.DataFrame): Close value data frame with each equity as column
        m (float): Weight of the thematic score
        l (float): Weight of the annualized return
        k (float): Weight of the annualized volatility
        maxsc (float): Maximum thematic score given equity

    Returns:
        score (float): Score to minimize
    """
    histvar=ret @ w
    ret_annual=pow(1+histvar.mean(),52)-1
    vol=np.std(histvar)*np.sqrt(52)
    return -m*np.dot(w,score)/maxsc-l*ret_annual/0.20+k*vol/0.2

def makeTable(met:list,ben:list,his:pan.DataFrame,ret:pan.DataFrame)->list:
    """
    Calculate and print metrics table

    Parameters:
        met (list): Portfolio metrics
        ben (list): Benchmark metrics
        his (pan.DataFrame): Historical returns
        ret (pan.DataFrame): Close value data frame with each equity as column

    Returns:
        Metrics: Metric, Benchmarks
    """
    metric=pan.DataFrame(met,columns=["Theme"],index=["Annualized Return (%)","Annualized Volatility (%)","Max drawdown (%)","Sharpe Ratio","1-week VaR 97.5% (%)","1-week ES 97.5% (%)"])
    metric["MSCI-World"]=calc_metrics(ret["MSCI-World"])
    metric["MSCI-ACWI"]=calc_metrics(ret["MSCI-ACWI"])
    metric["S&P500"]=calc_metrics(ret["SP500"])
    print("Metrics")
    print(metric.round(1))
    bench=pan.DataFrame(ben,columns=["MSCI-World"],index=["Alpha (%)","Alpha t-stat","Beta","Beta t-stat","Annualized tracking error (%)"])
    bench["MSCI-ACWI"]=calc_bench(his,ret["MSCI-ACWI"])
    print()
    print("Greeks against different benchmarks")
    print(bench.round(1))
    return metric.round(1),bench.round(1)

def calc_metrics(ret:pan.DataFrame,alpha:float=0.975,rf:float=0.0,freq:int=12)->list:
    """
    Calculate metrics

    Parameters:
        ret (pan.DataFrame): Close value data frame with each equity as column
        alpha=0.975 (float): Confidence level
        rf=0.02 (float): Risk free reference rate

    Returns:
        metrics (list): Returns, Volatility, MDD, Sharpe ratio, VaR, ES
    """
    #Annualized return
    ret_annual=pow(1+ret.mean(),freq)-1
    #Volatility
    vol=np.std(ret)*np.sqrt(freq)
    #Max drawdown
    cm_index=(1+ret).cumprod()
    r_max=cm_index.cummax()
    draw=cm_index/r_max-1
    mdd=draw.min()
    #Sharpe ratio
    sharpe=(ret_annual-rf)/vol
    #Risk
    var_95=ret.quantile(1-alpha)
    es=-ret[ret<var_95].mean()
    return 100*ret_annual,100*vol,100*mdd,sharpe,-100*var_95,100*es

def calc_bench(ret:pan.DataFrame,bench:pan.DataFrame)->list:
    """
    Calculate greeks (Alpha, Beta, Tracking error) of the portfolio against a benchmark

    Parameters:
        ret (pan.DataFrame): Close value data frame with each equity as column
        bench (pan.DataFrame): Close value data frame with benchmark as column

    Returns:
        metrics (list): Alpha, t-stat alpha, Beta, t-stat beta, tracking error
    """
    #Beta and alpha
    beta,alpha,r_val,p_val,std_er=scp.linregress(bench,ret)
    alpha_annual=pow(1+alpha,52)-1
    b_t_stat=beta/std_er
    #t-stat for alpha
    residual=ret-(alpha+beta*bench)
    n=len(ret)
    x_mean=np.mean(bench)
    sxx=np.sum((bench-x_mean)**2)
    sigma2=np.sum(residual**2)/(n-2)
    se_alpha=np.sqrt(sigma2*(1/n+x_mean**2 / sxx))
    t_alpha=alpha/se_alpha
    #Tracking error
    active_r=ret-bench
    tracking_err_week=np.std(active_r,ddof=1)
    tracking_err_annual=tracking_err_week*np.sqrt(52)
    return 100*alpha_annual,t_alpha,beta,b_t_stat,100*tracking_err_annual