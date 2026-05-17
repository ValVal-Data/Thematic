#Contain all function needed to plot

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pat
import scipy.stats as scp
import pandas as pan
from Source.Utils import *
from Source.PortfolioOptimization import *
from matplotlib.lines import Line2D

def perf_plot(performance:pan.DataFrame,b1:pan.DataFrame,name:list,met2:np.array,da:pan.DataFrame)->None:
    """
    Plot Cumulative return with Benchmarks, Return vs risk and top-5 positions

    Parameters:
        performance (pan.DataFrame): Performance dataframe
        b1 (pan.DataFrame): DataFrame with benchmark informations
        name (list): list with the name of the fund and benchmarks
        met2 (np.array): Metrics for the fund and benchmarks
        da (pan.DataFrame): DataFrame with position informations
        
    Returns:
        None, plot the figure directly
    """
    b1_cum=(1+b1).cumprod()
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]
    fig,ax=plt.subplots(1,3,figsize=(10,3))
    ax[0].plot(performance["Cum Return net"]*100)
    ax[0].plot(np.array(b1_cum["MSCI-World"]*100))
    ax[0].plot(np.array(b1_cum["MSCI-ACWI"]*100))
    ax[0].plot(np.array(b1_cum["SP500"]*100))
    ax[0].axhline(y=100,color='black',linestyle="-")
    ax[0].legend(name)
    ax[0].set_xlabel("Time (Month)")
    ax[0].set_title("Performance over time")
    ax[0].set_ylabel("Cumulative Return (%)")
    ax[0].set_xticks([])

    ax[1].set_xlabel("Month")
    ax[1].set_ylabel("Performance (%)")
    ax[1].set_title("Performance over time")

    for ide, elem in enumerate(met2):   
        ax[1].scatter(elem[1],elem[0],s=10)
        if name[ide]=="Thematic fund":
            ax[1].text(elem[1]-0.1,elem[0]+0.4,name[ide],va="top",ha="right",color=colors[ide],size=8)
        else:
            ax[1].text(elem[1]+0.1,elem[0]+0.4,name[ide],va="top",ha="left",color=colors[ide],size=8)

    ax[1].set_xlabel("Risk (Annualized Volatility (%))")
    ax[1].set_ylabel("Annualized Return (%)")
    ax[1].set_title("Risk vs Return")

    da2=da.copy(deep=True)
    da2.sort_values(by="w0",ascending=False,inplace=True)
    da2=da2["w0"]
    other=da2.iloc[5:].sum()
    da2=da2.head(5)
    da2.loc["Other"]=other
    wedges,texts,autotexts=ax[2].pie(da2*100,labels=da2.index,autopct='%d%%')
    for t in autotexts:
        t.set_color("white")
    ax[2].set_title("Top 5-positions")

    plt.subplots_adjust(wspace=0.4)
    plt.savefig("Figures/perf.png",dpi=300,bbox_inches="tight")
    plt.show()

def risk_plot(met:list)->None:
    """
    Plot Annualized volatility, Maximum drawdown, Sharpe ratio, VaR and ES 97.5%

    Parameters:
        met (list): Annualized volatility, Maximum drawdown, Sharpe ratio, VaR and ES
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,5,figsize=(16,6))

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]

    for ide,fi in enumerate(met):
        ax[0].plot(fi[:,1])
        ax[0].axhline(y=fi[:,1].mean(),linestyle="--",color=colors[ide])
    ax[0].set_xlabel("Time (6 months rolling windows)")
    ax[0].set_xticks([])
    ax[0].set_ylabel("Annualized Volatility (%)")
    ax[0].set_title("Volatility over time")

    for ide,fi in enumerate(met):
        ax[1].plot(fi[:,2])
        ax[1].axhline(y=fi[:,2].mean(),linestyle="--",color=colors[ide])
    ax[1].set_xlabel("Time (6 months rolling windows)")
    ax[1].set_xticks([])
    ax[1].set_ylabel("6-months Maximum Drawdown (%)")
    ax[1].set_title("Maximum Drawdown over time")

    for ide,fi in enumerate(met):
        ax[2].plot(fi[:,3])
    ax[2].set_xlabel("Time (6 months rolling windows)")
    ax[2].set_xticks([])
    ax[2].set_ylabel("Sharpe ratio")
    ax[2].set_title("Sharpe ratio over time")
    ax[2].legend(["Thematic fund","MSCI-World","S&P500"],loc='upper center',bbox_to_anchor=(0.5,-0.1),ncol=1)
    for ide,fi in enumerate(met):
        ax[2].axhline(y=fi[:,3].mean(),linestyle="--",color=colors[ide])

    for ide,fi in enumerate(met):
        ax[3].plot(fi[:,4])
        ax[3].axhline(y=fi[:,4].mean(),linestyle="--",color=colors[ide])
    ax[3].set_xlabel("Time (6 months rolling windows)")
    ax[3].set_xticks([])
    ax[3].set_ylabel("6-Month 97.5% VaR (%)")
    ax[3].set_title("VaR over time")

    for ide,fi in enumerate(met):
        ax[4].plot(fi[:,5])
        ax[4].axhline(y=fi[:,5].mean(),linestyle="--",color=colors[ide])
    ax[4].set_xlabel("Time (6 months rolling windows)")
    ax[4].set_xticks([])
    ax[4].set_ylabel("6-Month 97.5% ES (%)")
    ax[4].set_title("ES over time")

    plt.tight_layout()
    plt.savefig("Figures/risk.png",dpi=300,bbox_inches="tight")
    plt.show()

def concentration_plot(hhi:np.array,cr3:np.array,cr5:np.array,cr8:np.array,da:pan.DataFrame)->None:
    """
    Plot Herfindahl-Hirschmann index, concentration index and top 5 positions

    Parameters:
        hhi (np.array): hhi as function of time
        cr3 (np.array): Concentration index 3 as function of time
        cr5 (np.array): Concentration index 5 as function of time
        cr8 (np.array): Concentration index 8 as function of time
        da (pan.DataFrame): DataFrame with position informations
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,3,figsize=(16,4))

    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]

    ax[0].plot(hhi)
    ax[0].set_title("Herfindahl-Hirschmann index")
    ax[0].set_xlabel("Time (6 months rolling windows)")
    ax[0].set_xticks([])
    ax[0].set_ylabel("H")
    ax[0].axhline(y=hhi.mean(),linestyle="--",color="black")
    plt.text(0.6,0.05,"$|N_{eff}|$ = "+str(np.round(1/hhi.mean(),1)),transform=ax[0].transAxes,fontsize=14)

    ax[1].plot(cr3)
    ax[1].plot(cr5)
    ax[1].plot(cr8)
    ax[1].set_title("Concentration ratio")
    ax[1].set_xlabel("Time (6 months rolling windows)")
    ax[1].set_xticks([])
    ax[1].set_ylabel("$CR_{x}$")
    ax[1].axhline(y=cr3.mean(),linestyle="--",color=colors[0])
    ax[1].axhline(y=cr5.mean(),linestyle="--",color=colors[1])
    ax[1].axhline(y=cr8.mean(),linestyle="--",color=colors[2])
    ax[1].legend(["$CR_{3}$","$CR_{5}$","$CR_{8}$"],loc='upper right')
    da2=da.copy(deep=True)
    da2.sort_values(by="w0",ascending=False,inplace=True)
    da2=da2["w0"]
    other=da2.iloc[5:].sum()
    da2=da2.head(5)
    da2.loc["Other"]=other
    wedges,texts,autotexts=ax[2].pie(da2*100,labels=da2.index,autopct='%d%%')
    for t in autotexts:
        t.set_color("white")
    ax[2].set_title("Top 5-positions")
    plt.subplots_adjust(wspace=0.2)
    plt.savefig("Figures/conc.png",dpi=300,bbox_inches="tight")
    plt.show()

def exposure_plot(exp_ind:pan.DataFrame,exp_loca:pan.DataFrame,exp_cap:pan.DataFrame,exp_w:pan.DataFrame,exp_theme:pan.DataFrame)->None:
    """
    Plot exposure plot over time (6-months rolling windows) for industry, location, capitalization, weight and theme score

    Parameters:
        exp_ind (pan.DataFrame): DataFrame with the data
        exp_loca (pan.DataFrame): DataFrame with the data
        exp_cap (pan.DataFrame): DataFrame with the data
        exp_w (pan.DataFrame): DataFrame with the data
        exp_theme (pan.DataFrame): DataFrame with the data
        
    Returns:
        None, plot the figure directly
    """
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:12]
    fig,ax=plt.subplots(1,5,figsize=(16,5))

    ax[0].plot(exp_ind.rolling(24).mean()*100)
    for i in range(len(exp_ind.columns)):
        ax[0].axhline(y=exp_ind.iloc[:,i].rolling(24).mean().mean()*100,color=colors[i],linestyle="--")
    ax[0].set_xlabel("Time (6 months rolling windows)")
    ax[0].set_xticks([])
    ax[0].set_ylabel("Industry composition (%)")
    box=ax[0].get_position()
    ax[0].set_position([box.x0,box.y0+box.height*0.05,box.width,box.height*0.95])
    ax[0].set_title("Industry exposure over time")
    ax[0].legend(exp_ind.columns,loc='upper center',bbox_to_anchor=(0.5,-0.1),ncol=1)

    ax[1].plot(exp_loca.rolling(24).mean()*100)
    for i in range(len(exp_loca.columns)):
        ax[1].axhline(y=exp_loca.iloc[:,i].rolling(24).mean().mean()*100,color=colors[i],linestyle="--")
    ax[1].set_xlabel("Time (6 months rolling windows)")
    ax[1].set_xticks([])
    ax[1].set_ylabel("Location (%)")
    ax[1].set_title("Geography exposure over time")
    ax[1].legend(exp_loca.columns,loc='upper center',bbox_to_anchor=(0.5,-0.1),ncol=1)

    ax[3].boxplot(exp_w*100,showfliers=False)
    ax[3].set_xlabel("Position")
    ax[3].set_xticks([])
    ax[3].set_ylabel("Weight (%)")
    ax[3].set_title("Weight distributions")

    ax[2].plot(exp_cap.rolling(24).mean()*100)
    for i in range(len(exp_cap.columns)):
        ax[2].axhline(y=exp_cap.iloc[:,i].rolling(24).mean().mean()*100,color=colors[i],linestyle="--")
    ax[2].set_xlabel("Time (6 months rolling windows)")
    ax[2].set_xticks([])
    ax[2].set_ylabel("Company sizes (%)")
    ax[2].set_title("Size exposure over time")
    ax[2].legend(exp_cap.columns,loc='upper center',bbox_to_anchor=(0.5,-0.1),ncol=1)

    ax[4].plot(exp_theme.rolling(24).mean()*100)
    ax[4].set_xticks([])
    ax[4].set_xlabel("Time (6 months rolling windows)")
    ax[4].set_ylabel("Theme score (%)")
    ax[4].set_title("Theme exposure over time")
    ax[4].axhline(y=exp_theme.rolling(24).mean().mean()*100,color="Black",linestyle="--")

    plt.tight_layout()
    plt.savefig("Figures/exp.png",dpi=300,bbox_inches="tight")
    plt.show()

def turnover_plot(performance:pan.DataFrame)->None:
    """
    Plot Turnover, cumulative return and net return over time and return vs net return

    Parameters:
        performance (pan.DataFrame): DataFrame with the data
        
    Returns:
        None, plot the figure directly
    """
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]
    fig,ax=plt.subplots(1,2,figsize=(7,3))
    ax[0].plot(performance["Turnover"]*100)
    ax[0].axhline(y=performance["Turnover"].mean()*100,color=colors[1],linestyle="--")
    ax[0].axhline(y=np.median(performance["Turnover"])*100,color=colors[2],linestyle="--")
    ax[0].axhline(y=np.mean(np.quantile(performance["Turnover"],0.9))*100,color=colors[3],linestyle="--")
    ax[0].set_xlabel("Month")
    ax[0].set_xticks([])
    ax[0].set_ylabel("Turnover (%)")
    ax[0].set_title("Turnover over time")
    legend_elmt=[
        Line2D([0],[0],color=colors[1],linestyle="--",label="Mean"),
        Line2D([0],[0],color=colors[2],linestyle="--",label="Median"),
        Line2D([0],[0],color=colors[3],linestyle="--",label="Q 90%")
    ]
    ax[0].legend(handles=legend_elmt)
    ax[1].plot(performance["Cum Return"]*100)
    ax[1].plot(performance["Cum Return net"]*100)
    ax[1].set_xlabel("Month")
    ax[1].set_xticks([])
    ax[1].set_ylabel("Performance (%)")
    ax[1].set_title("Performance over time")
    ax[1].legend(["Gross","Net"])
    plt.tight_layout()
    plt.savefig("Figures/turnover.png",dpi=300,bbox_inches="tight")
    plt.show()

def evidence_plot(stat:np.array,optiT:float)->None:
    """
    Plot the different component of the energy function and the optimal temperature

    Parameters:
        stat (np.array): Matrix with temperature, chi2, s
        optiT (float): Optimal temperature
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,3,figsize=(10,3))

    ax[0].scatter(stat[:,0],stat[:,2]*stat[:,0])
    ax[0].axvline(x=optiT,color="black",linestyle="--")
    ax[0].set_xlabel("Temperature (K)")
    ax[0].set_ylabel("Entropy * T")
    ax[1].scatter(stat[:,0],stat[:,1])
    ax[1].axvline(x=optiT,color="black",linestyle="--")
    ax[1].set_xlabel("Temperature (K)")
    ax[1].set_ylabel("Chi2")
    sca3=ax[2].scatter(stat[:,0],-stat[:,1]+stat[:,2]*stat[:,0])
    ax[2].axvline(x=optiT,color="black",linestyle="--")
    ax[2].set_xlabel("Temperature (K)")
    ax[2].set_ylabel("Evidence score")
    plt.tight_layout()
    plt.show()

def universe_w_plot(data:pan.DataFrame,lab:str)->None:
    """
    Plot pie chart with info about location, size and industry distribution using weight

    Parameters:
        data (pan.DataFrame): Data to plot
        lab (str): Title of the figure
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,3,figsize=(9,3))

    ax[2].pie(data.groupby("Location")["w"].sum(),labels=list(data.groupby("Location")["w"].sum().index))
    ax[2].set_title("Geographic distribution")
    ax[1].pie(data.groupby("Cap")["w"].sum(),labels=list(data.groupby("Cap")["w"].sum().index))
    ax[1].set_title("Size distribution")
    temp=data.groupby("Industry")["w"].sum().sort_values(ascending=False)
    ax[0].barh(list(temp.index),temp*100)
    ax[0].set_title("Industry distribution")
    ax[0].set_xlabel("Fraction (%)")
    plt.subplots_adjust(wspace=0,left=0,right=1.05)
    plt.tight_layout()
    plt.show()

def metric_exploration_plot(se:pan.DataFrame,id:list,lab:list)->None:
    """
    Plot 3 scatter plots with always the same 2D-dimensions and color for multiple other dimensions

    Parameters:
        se (pan.DataFrame): Data to plot
        id (list): id of the column to plot. First two are in x and y.
        lab (list): Title of the axis. First two are in x and y.
    Returns:
        None, plot the figure directly
    """
    #Look at result
    fig,ax=plt.subplots(1,3,figsize=(15,4))
    fig.suptitle("Exploration of the portfolio metrics")
    sca=ax[0].scatter(se[:,id[0]],se[:,id[1]],c=se[:,id[2]],cmap="viridis")
    ax[0].set_xlabel(lab[0])
    ax[0].set_ylabel(lab[1])
    fig.colorbar(sca,label=lab[2])
    sca2=ax[1].scatter(se[:,id[0]],se[:,id[1]],c=se[:,id[3]],cmap="plasma")
    ax[1].set_xlabel(lab[0])
    ax[1].set_ylabel(lab[1])
    fig.colorbar(sca2,label=lab[3])
    sca3=ax[2].scatter(se[:,id[0]],se[:,id[1]],c=se[:,id[4]],cmap="cividis")
    ax[2].set_xlabel(lab[0])
    ax[2].set_ylabel(lab[1])
    fig.colorbar(sca3,label=lab[4])
    plt.tight_layout()
    plt.show()

def universe_plot(data:pan.DataFrame,lab:str)->None:
    """
    Plot pie chart with info about location, size and industry distribution

    Parameters:
        data (pan.DataFrame): Data to plot
        lab (str): Title of the figure
        
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,3,figsize=(9,3))

    ax[2].pie(data["Location"].value_counts(),labels=list(data["Location"].value_counts().index))
    ax[2].set_title("Geographic distribution")
    ax[1].pie(data["Cap"].value_counts(),labels=list(data["Cap"].value_counts().index))
    ax[1].set_title("Size distribution")
    ax[0].barh(list(data["Industry"].value_counts().index),data["Industry"].value_counts()/len(data)*100)
    ax[0].set_title("Industry distribution")
    ax[0].set_xlabel("Fraction (%)")
    plt.subplots_adjust(wspace=0,left=0,right=1.05)
    plt.tight_layout()
    plt.savefig("Figures/"+lab+".png",dpi=300)
    plt.show()

def key_plot(met:list,da:pan.DataFrame,ret:pan.DataFrame,lim:tuple)->None:
    """
    Plot Risk vs Return in a scatter plot and top 5 consituents of the portfolio in a pie chart

    Parameters:
        met (list): Metrics for the theme
        da (pan.DataFrame): Data frame containing information about geography, size and industry
        ret (pan.DataFrame): Data frame with returns for the benchmarks
        lim (tuple): list of limit for x and y acis
        
    Returns:
        None, plot the figure directly
    """
    metric=pan.DataFrame(met,columns=["Theme"],index=["Annualized Return (%)","Annualized Volatility (%)","Max drawdown (%)","Sharpe Ratio","1-week VaR 97.5% (%)","1-week ES 97.5% (%)"])
    metric["MSCI-World"]=calc_metrics(ret["MSCI-World"])
    metric["MSCI-ACWI"]=calc_metrics(ret["MSCI-ACWI"])
    metric["S&P500"]=calc_metrics(ret["SP500"])
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]
    fig,ax=plt.subplots(1,2,figsize=(7,4))

    for i in range(len(metric.columns)):
        fund=metric.columns[i]
        ax[0].scatter(metric.iloc[1][fund],metric.iloc[0][fund],s=7)
        if fund=="MSCI-ACWI":
            ax[0].text(metric.iloc[1][fund],metric.iloc[0][fund],fund,va="top",ha="left",color=colors[i])
        else:
            ax[0].text(metric.iloc[1][fund],metric.iloc[0][fund],fund,va="bottom",ha="left",color=colors[i])
    ax[0].set_xlabel("Risk (Volatility (%))")
    ax[0].set_ylabel("Return (%)")
    ax[0].set_title("Risk vs Return")
    ax[0].set_xlim(lim[0])
    ax[0].set_ylim(lim[1])
    da2=da.copy(deep=True)
    da2=da2["w"]
    other=da2.iloc[5:].sum()
    da2=da2.head(5)
    da2.loc["Other"]=other
    wedges,texts,autotexts=ax[1].pie(da2*100,labels=da2.index,autopct='%d%%')
    for t in autotexts:
        t.set_color("white")
    ax[1].set_title("Portfolio composition")
    fig.text(0.5,0.01,"Higher return with moderately higher volatility compared to the benchmark.",ha="center",fontsize=11)
    plt.tight_layout(rect=[0,0.05,1,1])
    plt.show()

def fund_stat_plot(da:pan.DataFrame,price:pan.DataFrame,bench:list,lab:list)->None:
    """
    Plot 3 pie charts with geographic, size and industry distribution as well as portfolio performance compared to benchmarks

    Parameters:
        da (pan.DataFrame): Data frame containing information about geography, size and industry
        price (pan.DataFrame): Price for portfolio
        bench (list): Price for benchmarks
        lab (list): List of string for legend of price evolution 
    
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(2,2,figsize=(9,9))

    ax[0,0].pie(da.groupby("Location")["w"].sum(),labels=list(da.groupby("Location")["w"].sum().index))
    ax[0,0].set_title("Geographic distribution")
    ax[0,1].pie(da.groupby("Cap")["w"].sum(),labels=list(da.groupby("Cap")["w"].sum().index))
    ax[0,1].set_title("Size distribution")
    ax[1,0].set_title("Industry distribution")
    ax[1,0].pie(da.groupby("Industry")["w"].sum(),labels=list(da.groupby("Industry")["w"].sum().index))
    ax[1,1].set_title("Comparison with benchmarks")
    for i in range(len(bench)):
        ax[1,1].plot(bench[i])
    ax[1,1].plot(price)
    ax[1,1].legend(lab)
    ax[1,1].set_xlabel("Date (year)")
    ax[1,1].set_ylabel("Return (%)")
    plt.show()

def equityPlot(dataf:pan.DataFrame)->None:
    """
    Bar plot to show equity with their score and coloring according to their capitalization

    Parameters:
        dataf (pan.DataFrame): Data frame to plot
    
    Returns:
        None, plot the figure directly
    """
    colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:3]
    colmap={0.0:colors[0],0.5:colors[1],1.0:colors[2]}
    legend=[pat.Patch(color=colors[0],label="Small-cap"),pat.Patch(color=colors[1],label="Medium-cap"),pat.Patch(color=colors[2],label="Large-cap")]
    col=list(dataf["Revenue"].map(colmap))
    fig,ax=plt.subplots(1,1,figsize=(5,5))
    ax.barh(dataf["Name"],dataf["Score"],color=col)
    ax.invert_yaxis()
    ax.set_xlabel("Score")
    ax.set_title("Selected equities")
    ax.legend(handles=legend,loc="lower right")
    plt.show()

def makeScoringPlot(data:pan.DataFrame,cdf:list,point:tuple,mi:float)->None:
    """
    Plot the distribution of the score and the cumulative contribution

    Parameters:
        data (pan.DataFrame): Data frame witch each column being an asset over time
        cdf (list): Cumulative contribution
        point(tuple): (Threshold,y-value), where y-value is from the interpolation of the cdf function
        mi(float): Minimal score of the selection
    Returns:
        None, plot the figure directly
    """
    fig,ax=plt.subplots(1,2,figsize=(7,3))
    ax[0].hist(data["Score"],bins=8)
    ax[0].axvline(x=mi,color="black",linestyle="--")
    ax[0].set_xlabel("Score")
    ax[0].set_ylabel("Count")
    ax[0].set_title("Score distribution")
    ax[0].set_ylim(0,15)
    ax[0].set_xlim(0,1)
    ax[1].set_xlabel("Number of element taken")
    ax[1].set_ylabel("Contribution")
    ax[1].set_title("Cumulative contribution")
    ax[1].plot([0,point[1]],[point[0],point[0]],color="black",linestyle="--")
    ax[1].plot([point[1],point[1]],[0,point[0]],color="black",linestyle="--")
    ax[1].set_xlim(1,len(data))
    ax[1].set_ylim(0,1)
    ax[1].plot(cdf)
    plt.tight_layout()
    plt.show()

def plotPriceEvolution(data:pan.DataFrame,title:str)->None:
    """
    Plot price evolution in % change (starting at 0)

    Parameters:
        data (pan.DataFrame): Data frame witch each column being an asset over time
        title (str): Title of the plot

    Returns:
        None, plot the figure directly
    """
    plt.plot(data/list(data.iloc[0])*100-100)#Normalize so they all start at 0
    plt.xlabel("Date")
    plt.ylabel("Evolution (+%)")
    plt.legend(data.columns)
    plt.title(title)
    plt.show()
