import json as js
import logging as lg
import sqlite3 as sq
from typing import Any

import pandas as pan

import database.database as db

log = lg.getLogger(__name__)


def loadScore(f: str) -> dict:
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
    score: dict[Any, Any] = {}
    with open(f) as file:
        sc = js.load(file)
        # Modify range rule
        for rule in sc:
            if sc[rule]["Type"] == "Range":
                score[rule] = {}
                tmp = {}
                for ke in sc[rule]["Rule"]:
                    cp = ke.split("-")
                    ne = (float(cp[0]), float(cp[1]))
                    tmp[ne] = sc[rule]["Rule"][ke]
                score[rule]["Type"] = "Range"
                score[rule]["Rule"] = tmp
            else:
                score[rule] = sc[rule]
    return score


def scoreData(entry: pan.DataFrame, pth: str) -> pan.Series:
    """
    Scoring function

    Parameters:
        entry (pan.DataFrame): Row of a DataFrame
        pth (str): Path to weight

    Returns:
        score (float)

    Notes:
        - See README for the definition
    """
    with open(pth) as file:
        w = js.load(file)
    ps = (
        w["Pipeline"]["Pipeline Maturity"] * entry["Pipeline Maturity"]
        + w["Pipeline"]["Pipeline Breadth"] ** entry["Pipeline Breadth"]
        + w["Pipeline"]["Pipeline Differentiation"] * entry["Pipeline Differentiation"]
    )
    bp = (
        w["Breakthrough"]["Novelty of the technology"] * entry["Novelty of the technology"]
        + w["Breakthrough"]["Validation"] * entry["Validation"]
    )
    inno = (
        w["Innovation"]["Pipeline Strength"] * ps
        + w["Innovation"]["Breakthrough potential"] * bp
        + w["Innovation"]["Number of active partnerships"]
        * entry["Number of active partnerships"]
    )
    ts = (
        w["Score"]["Thematic"] * entry["Thematic"]
        + w["Score"]["Innovation"] * inno
        + w["Score"]["Revenue"] * entry["Revenue"]
        + w["Score"]["CAGR"] * entry["CAGR"]
    ) * (1 + w["Score"]["Ecosystem component"] * entry["Ecosystem component"])
    log.info("thematic score calculated")
    return ts


def convertForRanking(data: pan.DataFrame, score: dict) -> pan.DataFrame:
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
        if score[key]["Type"] == "Range":
            data[key] = data[key].map(lambda x, key=key: searchRange(x, score[key]["Rule"]))
        elif score[key]["Type"] == "Category":
            data[key] = data[key].map(score[key]["Rule"])
        else:
            print("Error: Rule type not recognized")
            exit()
    return data


def searchRange(value: str, ran: dict) -> float:
    """
    For rule when rule are based on a range

    Parameters:
        value (str): Value of the cell
        ran (dict): Dictionary with range (as tuple) for key and corresponding value

    Returns:
        value (float)
    """
    if value == "NA":
        return 0
    v = float(value)
    for (start, end), label in ran.items():
        if start <= v < end:
            return label
    return 0


def make_scoring() -> None:
    # Scoring
    score = loadScore("config/scoring.json")
    convert = db.load_convert("config/convert.json")
    with sq.connect("database/database.db") as conn:
        data = pan.read_sql("SELECT * FROM thematic", conn)
    conn.close()
    data = convertForRanking(data, score)
    data["Cap"] = data["Revenue"].map(convert["ca"])
    data["Score"] = scoreData(data, "config/weight.json")
    with sq.connect("database/database.db") as conn:
        data.to_sql("thematic_score", conn, if_exists="replace", index=False)
    conn.close()
    log.info("thematic database updated")


if __name__ == "__main__":
    log.error("config.py should not be run as main")
