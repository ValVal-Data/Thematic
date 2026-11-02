import sqlite3 as sq
import unittest as ut
from contextlib import closing

import numpy as np
import pandas as pan

import services.optimize_service as os
import services.performance_service as ps
import services.score_service as sc


class Test_service_score(ut.TestCase):
    def test_read_thematic_score(self):
        with closing(sq.connect("tests/fixtures/test.db")) as conn:
            res = sc.read_thematic_score(conn)
        self.assertEqual(res.shape, (3, 15))

    def test_get_score(self):
        res = sc.get_score("tests/fixtures/test.db")
        self.assertEqual(list(res.values()), [3, 2, 1])

    def test_get_universe(self):
        res = sc.get_score("tests/fixtures/test.db")
        self.assertEqual(list(res.keys()), ["C", "B", "A"])

    def test_get_weight(self):
        res = sc.get_weight("tests/fixtures/test_weight.json")
        self.assertEqual(res, {"Test": 1})


class Test_service_optimize(ut.TestCase):
    def test_matrix_correspondance(self):
        retEq = pan.DataFrame([[0, 0, 0], [0, 0, 0]], columns=["test1", "test2", "test3"])
        data = pan.DataFrame(
            [
                ["test1", "test2", "test3"],
                ["test2", "test1", "test1"],
                ["test3", "test1", "test1"],
            ],
            columns=["NameC", "test2", "test3"],
        )
        test = os.matrix_correspondance(retEq, data, "test3")
        self.assertEqual(test[0, -1], 1)

    def test_maxScore(self):
        sc = [1, 0]
        bounds = (0, 1)
        test = os.maxScore(sc, bounds)
        self.assertEqual(test, 1)

    def test_drift_weight(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.array([[1, 1]])
        test = os.drift_weight(retEq, w0)
        self.assertEqual(test[0, 0], test[0, 1])

    def test_drift_return(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.array([[1, 1], [1, 1]])
        test = os.drift_return(retEq, w0)
        self.assertEqual(test[0], test[1])

    def test_discretize(self):
        val = np.array([0.003, 0.006])
        test = os.discretize(val)
        self.assertEqual(test[0], test[1])

    def test_calc_ES(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.random.normal(size=(1000, 2))
        test = os.calc_ES(retEq, w0)
        self.assertEqual(np.round(test, 1), -0.5)

    def test_calc_VaR(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.random.normal(size=(1000, 2))
        test = os.calc_VaR(retEq, w0)
        self.assertEqual(np.round(test, 1), 0.5)


class Test_service_performance(ut.TestCase):
    def test_matrix_correspondance(self):
        retEq = pan.DataFrame([[0, 0, 0], [0, 0, 0]], columns=["test1", "test2", "test3"])
        data = pan.DataFrame(
            [
                ["test1", "test2", "test3"],
                ["test2", "test1", "test1"],
                ["test3", "test1", "test1"],
            ],
            columns=["NameC", "test2", "test3"],
        )
        test = ps.matrix_correspondance(retEq, data, "test3")
        self.assertEqual(test[0, -1], 1)

    def test_drift_weight(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.array([[1, 1]])
        test = ps.drift_weight(retEq, w0)
        self.assertEqual(test[0, 0], test[0, 1])

    def test_drift_return(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.array([[1, 1], [1, 1]])
        test = ps.drift_return(retEq, w0)
        self.assertEqual(test[0], test[1])

    def test_discretize(self):
        val = np.array([0.003, 0.006])
        test = ps.discretize(val)
        self.assertEqual(test[0], test[1])

    def test_calc_ES(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.random.normal(size=(1000, 2))
        test = ps.calc_ES(retEq, w0)
        self.assertEqual(np.round(test, 1), -0.5)

    def test_calc_VaR(self):
        w0 = np.array([0.5, 0.5])
        retEq = np.random.normal(size=(1000, 2))
        test = ps.calc_VaR(retEq, w0)
        self.assertEqual(np.round(test, 1), 0.5)

    def test_pca(self):
        a = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        test = ps.pca(a)
        self.assertEqual(np.round(test[0].sum(), 0), 27)
        self.assertEqual(np.round(test[1].sum(), 1), -1.7)

    def test_calc_HHI(self):
        w = np.ones((10, 2)) / 2
        test = ps.calc_HHI(w)
        self.assertEqual(int(test.sum()), 5)

    def test_calc_CR(self):
        w = np.ones((10, 2)) / 2
        test = ps.calc_CR(w, 2)
        self.assertEqual(int(test.sum()), 10)


if __name__ == "__main__":
    ut.main()
