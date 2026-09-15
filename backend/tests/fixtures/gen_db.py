import sqlite3 as sq
from contextlib import closing

"""Execute to create the test database test.db"""

with closing(sq.connect("tests/fixtures/test.db")) as conn:
    conn.execute("""
        CREATE TABLE thematic_score (
            id INTEGER PRIMARY KEY,
            Ticker TEXT,
            Score INTEGER,
            "Pipeline Maturity" INTEGER,
            "Pipeline Breadth" INTEGER,
            "Pipeline Differentiation" INTEGER,
            "Novelty of the technology" INTEGER,
            Validation INTEGER,
            "Pipeline Strength" INTEGER,
            "Breakthrough potential" INTEGER,
            "Number of active partnerships" INTEGER,
            Thematic INTEGER,
            Revenue INTEGER,
            CAGR INTEGER,
            "Ecosystem component" INTEGER,
            Currency TEXT,
            Market TEXT,
            Capital REAL
        )
    """)
    conn.executemany('INSERT INTO thematic_score (Ticker,Score,"Pipeline Maturity","Pipeline Breadth","Pipeline Differentiation","Novelty of the technology",Validation,"Pipeline Strength","Breakthrough potential","Number of active partnerships",Thematic,Revenue,CAGR,"Ecosystem component") VALUES (?,?,1,1,1,1,1,1,1,1,1,1,1,1,"LON",)',(("A",1),("B",2),("C",3)))
    conn.commit()