import sqlite3 as sq
import unittest as ut
from contextlib import closing

import pandas as pan

import config.config as cn
import database.database as db


class Test_config(ut.TestCase):
    def test_loadScore(self):
        res = cn.loadScore("tests/fixtures/test_score.json")
        self.assertEqual(res["Revenue"]["Rule"][(0.0, 0.5)], 0)
        self.assertEqual(res["Thematic"]["Rule"]["N"], 0)

    def test_scoreData(self):
        with closing(sq.connect("tests/fixtures/test.db")) as conn:
            univ = pan.read_sql("SELECT * FROM thematic_score", conn)
        res = cn.scoreData(univ, "tests/fixtures/test_weight_full.json")
        self.assertEqual(res.iloc[0], 0.9271000000000001)

    def test_convertForRanking(self):
        univ = pan.DataFrame([[0.2, "N"], [10, "H"]], columns=["Revenue", "Thematic"])
        conv = cn.loadScore("tests/fixtures/test_score.json")
        res = cn.convertForRanking(univ, conv)
        self.assertEqual(res.iloc[0, 0], 0)
        self.assertEqual(res.iloc[0, 1], 0)

    def test_searchRange(self):
        ran = {(0, 1): 0, (1, 2): 1, (2, 3): 2}
        self.assertEqual(cn.searchRange("0.5", ran), 0)
        self.assertEqual(cn.searchRange("1.5", ran), 1)
        self.assertEqual(cn.searchRange("2.5", ran), 2)


class Test_database(ut.TestCase):
    def test_load(self):
        res = db.load("tests/fixtures/test_stock_Close.txt")
        self.assertEqual(len(res), 5)

    def test_loadScore(self):
        res = db.loadScore("tests/fixtures/test_score.json")
        self.assertEqual(res["Revenue"]["Type"], "Range")
        self.assertEqual(res["Thematic"]["Type"], "Category")

    def test_load_convert(self):
        conv = cn.loadScore("tests/fixtures/test_score.json")
        self.assertEqual(conv["Revenue"]["Rule"][(0.0, 0.5)], 0.0)


if __name__ == "__main__":
    ut.main()
