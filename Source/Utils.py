#Tool functions

import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as scp
import pandas as pan
import glob as gb
import scipy.optimize as op

def write_table_md(f:str,d:pan.DataFrame)->None:
    """
    Save table to HTML

    Parameters:
        f (str): Path to the file.
        d (pan.DataFrame): file to save

    Returns:
        None, save the file
    """
    with open(f,"w") as file:
        file.write(d.to_html(index=True))

def exRate(fRate:str)->dict:
    """
    File loading of currency exchange rate data

    Parameters:
        frate (str): Path to the file.

    Returns:
        ex (dictionary)
    
    Notes:
        - Data should be in tabular format with "," as separation
        - The format is: From,To,Exchange rate
    """
    ex={}
    with open(fRate,"r") as file:
            for line in file:
                  l=line.split(",")
                  ex[l[0]+"/"+l[1]]=float(l[2])
    return ex

def load(pth:str)->pan.DataFrame:
    """
    File loading of temporal asset data

    Parameters:
        pth (str): Path to the file.

    Returns:
        data (pan.DataFrame)
    
    Notes:
        - Data should be in tabular format with "  " as separation
    """
    data=pan.read_csv(pth,sep=" ",engine="python")
    data["Date"]=pan.to_datetime(data["Date"],dayfirst=True)
    data=data.set_index("Date")
    data=data.sort_index(ascending=True)
    return(data)
    
#Load all files in Data
def loadAll()->list:
    """
    Load multiple files contain in set files

    Parameters:
        None

    Returns:
        dataClose (pan.DataFrame): Contain closing data with each asset as a column
        dataDiv (pan.DataFrame): Contain dividend data with each asset as a column
        dataCur (pan.DataFrame): Contain currency exchange data with each asset as a column
        info (dic): Dictionnary that contain information from file, such as currency and capitalization
    
    Notes:
        - Data should be in the folder Data
        - They are separated between closing value, currency exchange rate and dividends
        - This separation is specified by a code before the extension separated by '_'
    """
    #Find all files in Data
    filesDiv=gb.glob("Data/*Div.dat")
    filesClose=gb.glob("Data/*Close.dat")
    filesCur=gb.glob("Data/*Cur.dat")

    #Extract info from name
    name=[f.split('_')[0].split('\\')[1] for f in filesClose]
    currency=[f.split('_')[-3] for f in filesClose]
    distrib=[f.split('_')[-2] for f in filesClose]
    info={na: {"Currency":cu,"Type":ty} for na, cu, ty in zip(name,currency,distrib)}
    nameC=[f.split('-')[0].split('\\')[1] for f in filesCur]
    nameDiv=[f.split('_')[0].split('\\')[1] for f in filesDiv]

    #Load data
    dataClose=[load(f) for f in filesClose]
    dataDiv=[load(f) for f in filesDiv]
    dataCur=[load(f) for f in filesCur]

    #Merge into a single table
    dataClose=pan.concat(dataClose,axis=1)
    dataClose.columns=name
    dataDiv=pan.concat(dataDiv,axis=1,sort=True)
    dataDiv.columns=nameDiv
    dataCur=pan.concat(dataCur,axis=1)
    dataCur.columns=nameC

    #Adjust for dividends
    for fund in nameDiv:
        dataClose[fund+"_div"]=dataDiv[fund]
        dataClose[fund+"_div"]=dataClose[fund+"_div"].fillna(0)
        dataClose[fund]+=dataClose[fund+"_div"]
        dataClose.drop(columns=[fund+"_div"],inplace=True)
        
    #Convert everything to CHF
    for fund in name:
        if info[fund]["Currency"]!="CHF":
            dataClose[fund]*=dataCur[info[fund]["Currency"]]

    #Load portfolio and adjust values
    """
    dataClose/=list(dataClose.iloc[0])
    port=pan.read_csv("Portfolio.txt",sep="\t",engine="python")
    dataClose/=list(dataClose.iloc[0])
    with open("Portfolio.txt","r") as f:
        for line in f:
            l=line.split("\t")
            if l[0] in ["CHF","USD","EUR"]:
                dataClose[l[0]]=int(l[1])*dataCur[l[0]]/float(dataCur[l[0]].iloc[0])
            else:
                dataClose[l[0]]*=int(l[1])
    dataClose["Total"]=dataClose.sum(axis=1)
    """

    return((dataClose,dataDiv, dataCur,info))

def returnsP(data:pan.DataFrame)->pan.DataFrame:
    """
    Calculate returns in percentage r=(p1-p0)/p0*100

    Parameters:
        data (pan.DataFrame): Data to convert

    Returns:
        histVar (pan.DataFrame)

    """
    histVar=data.copy(deep=True)
    for fund in data.columns:
        histVar[fund]=(-data[fund]+data[fund].shift(1))/data[fund].shift(1)*100
    histVar=histVar.dropna()
    return(histVar)

def returns(data:pan.DataFrame)->pan.DataFrame:
    """
    Calculate returns in percentage r=(p1-p0)/p0

    Parameters:
        data (pan.DataFrame): Data to convert

    Returns:
        histVar (pan.DataFrame)

    """
    histVar=data.copy(deep=True)
    for fund in data.columns:
        histVar[fund]=(data[fund]-data[fund].shift(1))/data[fund].shift(1)
    histVar=histVar.dropna()
    return(histVar)

def returnsL(data:pan.DataFrame)->pan.DataFrame:
    """
    Calculate returns log returns lr=log(p1/p0)

    Parameters:
        data (pan.DataFrame): Data to convert

    Returns:
        histVar (pan.DataFrame)

    """
    histVar=data.copy(deep=True)
    for fund in data.columns:
        histVar[fund]=np.log(data[fund]/data[fund].shift(1))
    histVar=histVar.dropna()
    return(histVar)