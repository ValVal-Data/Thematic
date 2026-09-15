import pandas as pan
import numpy as np

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