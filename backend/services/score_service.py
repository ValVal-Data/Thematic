import json as js
import config.config as cn
import sqlite3 as sq
import pandas as pan
import logging as lg
from contextlib import closing

log=lg.getLogger(__name__)

def read_thematic_score(conn:sq.Connection)->pan.DataFrame:
    """
    Return whole thematic score table
    
    Parameters:
        conn (sq.Connection): Connection to database.
    
    Returns:
        table (pan.Dataframe):
    """
    return pan.read_sql("SELECT * FROM thematic_score",conn)

def get_score(pth:str)->dict:
    """
    Return thematic score
    
    Parameters:
        pth (str): Path to database.
    
    Returns:
        score (dict):
    """
    with closing(sq.connect(pth)) as conn:
        data=read_thematic_score(conn)
    d=data.sort_values("Score",ascending=False)
    d.index=d["Ticker"]
    return d["Score"].to_dict()

def get_universe(pth:str)->dict:
    """
    Return universe
    
    Parameters:
        pth (str): Path to database.
    
    Returns:
        universe (dict):
    """
    with closing(sq.connect(pth)) as conn:
        data=read_thematic_score(conn)
    conn.close()
    return data.to_dict()

def get_weight(pth)->dict:
    """
    Return scoring weight
    
    Parameters:
        pth (str): Path to database.
    
    Returns:
        weight (dict):
    """
    with open(pth,"r") as file:
        w=js.load(file)
    return w

def calc_score()->None:
    """
    Recalculate thematic score
    
    Parameters:
        None
    
    Returns:
        None
    """
    cn.make_scoring()

def update_weight(pth:str,data:dict)->None:
    """
    Update scoring weight
    
    Parameters:
        pth (str): Path to database.
        data (dict): New weight.
    
    Returns:
        None
    """
    with open(pth,"w") as file:
        js.dump(data,file)
    log.info("score weight updated")

def update_universe(pth:str,data:dict)->None:
    """
    Update universe and recalculate thematic score
    
    Parameters:
        pth (str): Path to database.
        data (dict): New weight.
    
    Returns:
        None
    """
    d=pan.DataFrame(data)
    with closing(sq.connect(pth)) as conn:
        d.to_sql(
            "thematic",
            conn,
            if_exists="replace",
            index=False
        )
    log.info("universe updated")
    cn.make_scoring()
