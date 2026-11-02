import logging as lg

import streamlit as st

lg.basicConfig(
    level=lg.DEBUG,
    format="%(asctime)s - [%(name)s] - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
log = lg.getLogger(__name__)

st.set_page_config(page_title="Portfolio Dashboard", layout="wide")

home = st.Page("home.py", title="Home")
score = st.Page("pages/score.py", title="Thematic Scoring")
optimize = st.Page("pages/optimize.py", title="Optimization")
perf = st.Page("pages/performance.py", title="Analytics")
pg = st.navigation([home, score, optimize, perf])
pg.run()
