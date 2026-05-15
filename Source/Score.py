#Tool functions

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as scp
import pandas as pan
import glob as gb
import scipy.optimize as op
import json

def loadScore(f:str)->dict:
    """
    File loading of scoring data

    Parameters:
        pth (str): Path to the file.

    Returns:
        score (dictionary)
    
    Notes:
        - Two types of scoring can be provided
            - Range with: lim1-lim2=val
            - Categorical with: symbol=val
    """
    score={}
    with open(f,"r") as file:
        sc=json.load(file)
        #Modify range rule
        for rule in sc.keys():
            if sc[rule]["Type"]=="Range":
                score[rule]={}
                tmp={}
                for ke in sc[rule]["Rule"]:
                    l=ke.split("-")
                    ne=(float(l[0]),float(l[1]))
                    tmp[ne]=sc[rule]["Rule"][ke]
                score[rule]["Type"]="Range"
                score[rule]["Rule"]=tmp
            else:
                score[rule]=sc[rule] 
    return score

def scoreData(entry:pan.DataFrame)->float:
    """
    Scoring function

    Parameters:
        entry (pan.DataFrame): Row of a DataFrame

    Returns:
        score (float)

    Notes:
        - See README for the definition
    """
    ps=0.5*entry["Pipeline Maturity"]+0.35*entry["Pipeline Breadth"]+0.15*entry["Pipeline Differentiation"]
    bp=0.7*entry["Novelty of the technology"]+0.3*entry["Validation"]
    inno=0.40*ps+0.4*bp+0.2*entry["Number of active partnerships"]
    ts=(0.55*entry["Thematic"]+0.325*inno+0.05*entry["Revenue"]+ 0.075*entry["CAGR"])*(1+entry["Ecosystem component"])
    return ts

def convertForRanking(data:pan.DataFrame,score:dict)->pan.DataFrame:
    """
    For rule when rule are based on a range

    Parameters:
        data (pan.DataFrame): Data to convert
        score (dict): Dictionary with rule for value

    Returns:
        data (pan.DataFrame)

    Notes:
        - Only column defined in score will be modified
    """
    for key in list(score.keys()):
        if score[key]["Type"]=="Range":
            data[key]=data[key].map(lambda x: searchRange(x,score[key]["Rule"]))
        elif score[key]["Type"]=="Category":
            data[key]=data[key].map(score[key]["Rule"])
        else:
            print("Error: Rule type not recognized")
            exit()
    return data

def searchRange(value:str,ran:dict)->float:
    """
    For rule when rule are based on a range

    Parameters:
        value (str): Value of the cell
        ran (dict): Dictionary with range (as tuple) for key and corresponding value

    Returns:
        value (float)
    """
    if value=="NA":
        return 0
    v=float(value)
    for (start,end),label in ran.items():
        if start <= v < end:
            return label
    return 0

def maxScore(sc:list,bounds:tuple)->float:
    """
    Calculate max score based on boundary limit for weights

    Parameters:
        sc (list): Scores
        bounds (tuple): (lower range, upper range)

    Returns:
        value (float)
    """
    sc2=sorted(sc,reverse=True)
    remaining=1-len(sc)*bounds[0]
    w=[bounds[0]]*len(sc)
    dw=bounds[1]-bounds[0]
    for i in range(len(sc)):
        if dw<remaining:
            w[i]+=dw
            remaining-=dw
        else:
            w[i]+=remaining
            break
    return np.dot(w,sc2)

