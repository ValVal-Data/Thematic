import glob as gb
import json as js
import logging as lg
import sqlite3 as sq
from contextlib import closing
from pathlib import Path
from typing import Any, cast

import pandas as pan

import common.utils as ut

log = lg.getLogger(__name__)


def load(pth: str) -> pan.DataFrame:
    """
    File loading of temporal asset data

    Parameters:
        pth (str): Path to the file.

    Returns:
        data (pan.DataFrame)

    Notes:
        - Data should be in tabular format with "  " as separation
    """
    data = pan.read_csv(pth, sep=" ", engine="python")
    data["Date"] = pan.to_datetime(data["Date"], dayfirst=True)
    data = data.set_index("Date")
    data = data.sort_index(ascending=True)
    return data


# Load all files in Data
def loadAll(pth: str, ext: str) -> tuple:
    """
    Load multiple files contain in set files

    Parameters:
        pth (str): Path to file folder
        ext (str): File extension name

    Returns:
        dataClose (pan.DataFrame): Contain closing data with each asset as a column
        dataDiv (pan.DataFrame): Contain dividend data with each asset as a column
        dataCur (pan.DataFrame): Contain currency exchange data with each asset as a column
        info (dic): Dictionnary that contain information from file,
            such as currency and capitalization

    Notes:
        - Data should be in the folder Data
        - They are separated between closing value, currency exchange rate and dividends
        - This separation is specified by a code before the extension separated by '_'
    """
    # Find all files in Data
    filesDiv = gb.glob(pth + "*Div." + ext)
    filesClose = gb.glob(pth + "*Close." + ext)
    filesCur = gb.glob(pth + "*Cur." + ext)

    # Extract info from name
    name = [Path(f).stem.split("_")[0] for f in filesClose]
    currency = [f.split("_")[-3] for f in filesClose]
    distrib = [f.split("_")[-2] for f in filesClose]
    info = {
        na: {"Currency": cu, "Type": ty}
        for na, cu, ty in zip(name, currency, distrib, strict=False)
    }
    nameC = [Path(f).stem.split("-")[0] for f in filesCur]
    nameDiv = [Path(f).stem.split("_")[0] for f in filesDiv]

    # Load data
    dataClose = [load(f) for f in filesClose]
    dataDiv = [load(f) for f in filesDiv]
    dataCur = [load(f) for f in filesCur]

    # Merge into a single table
    dataClose = pan.concat(dataClose, axis=1, sort=True)
    dataClose.columns = name
    dataDiv = pan.concat(dataDiv, axis=1, sort=True)
    dataDiv.columns = nameDiv
    dataCur = pan.concat(dataCur, axis=1)
    dataCur.columns = nameC

    # Adjust for dividends
    for fund in nameDiv:
        dataClose[fund + "_div"] = dataDiv[fund]
        dataClose[fund + "_div"] = dataClose[fund + "_div"].fillna(0)
        dataClose[fund] += dataClose[fund + "_div"]
        dataClose.drop(columns=[fund + "_div"], inplace=True)

    # Convert everything to CHF
    for fund in name:
        if info[fund]["Currency"] != "CHF":
            dataClose[fund] *= dataCur[info[fund]["Currency"]]
    return dataClose, dataDiv, dataCur, info


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


def load_convert(pth: str) -> dict:
    dico = {}
    with open(pth) as f:
        convert = js.load(f)
        dico["rule"] = convert["Currency"]
        dico["geography"] = convert["Market"]
        dico["cost_cat"] = convert["Cost"]
        dico["ca"] = {float(x): y for x, y in convert["Capital"].items()}
    return dico


def make_thematic() -> None:
    data = pan.read_csv("data/Universe.txt", sep=",", engine="python").fillna("NA")  # Load data
    with open("config/exrate.json") as f:  # Convert all revenue to CHF
        rate = js.load(f)
    convert = load_convert("config/convert.json")

    # Convert Universe data
    data["Location"] = data["Market"].map(convert["geography"])
    data["Revenue"] *= data["Market"].map(convert["rule"]).map(rate)
    data["CAGR"] = data["CAGR"] / 100
    data["NameC"] = data["Ticker"].map(lambda x: cast(str, x).split(".")[0])
    data = data.reset_index()

    # Add to database
    with closing(sq.connect("database/database.db")) as conn:
        data.to_sql("thematic", conn, if_exists="replace", index=False)
    log.info("thematic table of database.db updated")


def make_price() -> None:
    # Load data
    (dataClose, _, _, _) = loadAll("data/", "dat")
    dataClose = dataClose.iloc[:-2]
    ret = ut.returns(dataClose)
    # Update database
    with closing(sq.connect("database/database.db")) as conn:
        dataClose.to_sql("price", conn, if_exists="replace", index=False)
        log.info("price table of database.db updated")
        ret.to_sql("returns", conn, if_exists="replace", index=False)
        log.info("returns table of database.db updated")


def make_database() -> None:
    make_thematic()
    make_price()


if __name__ == "__main__":
    log.error("database.py should not be run as main")
