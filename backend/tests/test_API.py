import unittest as ut
import sqlite3 as sq
from contextlib import closing
import services.score_service as sc

class Test_service_score(ut.TestCase):
    def test_read_thematic_score(self):
        with closing(sq.connect("tests/fixtures/test.db")) as conn:
            res=sc.read_thematic_score(conn)
        self.assertEqual(res.shape,(3,15))

    def test_get_score(self):
        res=sc.get_score("tests/fixtures/test.db")
        self.assertEqual(list(res.values()),[3,2,1])

    def test_get_universe(self):
        res=sc.get_score("tests/fixtures/test.db")
        self.assertEqual(list(res.keys()),["C","B","A"])
    
    def test_get_weight(self):
        res=sc.get_weight("tests/fixtures/test_weight.json")
        self.assertEqual(res,{"Test":1})
    

class Test_service_optimize(ut.TestCase):
    def test_get_score(self):
        return 0

class Test_service_stress(ut.TestCase):
    def test_get_score(self):
        return 0

if __name__ == "__main__":
    ut.main()