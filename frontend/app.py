import streamlit as st
import logging as lg

lg.basicConfig(
    level=lg.DEBUG,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
log=lg.getLogger(__name__)

st.set_page_config(
    page_title="Portfolio Dashboard",
    layout="wide"
)

home=st.Page("home.py",title="Home")
score=st.Page("pages/score.py",title="Thematic Scoring")
optimize=st.Page("pages/optimize.py",title="Portfolio Optimization")
stress=st.Page("pages/stress.py",title="Portfolio Stress")
report=st.Page("pages/report.py",title="Report")
pg=st.navigation([home,score,optimize,stress,report])
pg.run()

