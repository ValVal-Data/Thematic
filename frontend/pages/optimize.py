import logging as lg

import numpy as np
import requests as rq
import streamlit as st

from theme.plotly_theme import register_plotly_theme

register_plotly_theme()

log = lg.getLogger(__name__)

if "running" not in st.session_state:
    st.session_state.running = False

if "sc" not in st.session_state:
    st.session_state.sc = False
if "var" not in st.session_state:
    st.session_state.var = 100
    st.session_state.es = 100
    st.session_state.ub = 100
    st.session_state.lb = 1
    st.session_state.indus = 1.0
    st.session_state.ramp_l = 1.0
    st.session_state.ramp_u = 100
    st.session_state.ramp_s = 1.0
    st.session_state.job_id = ""
    st.session_state.prog_opti = 0
    st.session_state.nb = len(st.session_state.df_selected)
    st.session_state.stat = ""
    st.session_state.job_id_t = st.session_state.job_id


@st.fragment(run_every="30s" if st.session_state.running else None)
def progress_update():
    if st.session_state.job_id != "":
        st.session_state.job_id_t = st.session_state.job_id
        prog = rq.get(
            "http://backend:8000/optimize/progress",
            timeout=10,
            params={"job_id": st.session_state.job_id},
        )
        if prog.status_code == 404:
            lg.error(f"job '{st.session_state.job_id}' not found")
        elif prog.status_code == 500:
            lg.error("Connection error when updating optimize")
        else:
            pro = prog.json()
            st.session_state.stat = pro["status"]
            if pro["status"] == "completed":
                st.session_state.running = False
                st.rerun()
            elif pro["status"] == "failed":
                st.session_state.running = False
                lg.error(pro["message"])
                st.rerun()


if st.session_state.running:
    progress_update()

if not st.session_state.sc:
    st.title("Optimization requires scoring first")
    st.write("Run first scoring to be able to do optimization")
else:
    st.title("Portfolio optimization")

    e1, e2 = st.columns(2)
    with e1:
        st.subheader("Constraints")
        st.session_state.var = st.slider(
            label="Value At Risk (%)",
            min_value=0,
            max_value=100,
            value=100,
            disabled=st.session_state.running,
        )
        st.session_state.es = st.slider(
            label="Expected Shortfall (%)",
            min_value=0,
            max_value=100,
            value=100,
            disabled=st.session_state.running,
        )
        st.session_state.indus = st.slider(
            label="Maximal Industry Allocation Change (%)",
            min_value=0,
            max_value=500,
            value=100,
            disabled=st.session_state.running,
        )
        st.session_state.lb, st.session_state.ub = st.slider(
            label="Weights Boundaries (%)",
            min_value=1,
            max_value=100,
            value=(1, 100),
            disabled=st.session_state.running,
        )
    with e2:
        st.subheader("Optimization parameters")
        f1, f2 = st.columns(2)
        st.session_state.ramp_l, st.session_state.ramp_u = f1.slider(
            label="Temperature range",
            min_value=0,
            max_value=500,
            value=(0, 500),
            disabled=st.session_state.running,
        )
        st.session_state.ramp_s = f2.slider(
            label="Temperature step",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            disabled=st.session_state.running,
        )
        st.subheader("Information")
        i1, i2 = st.columns([3, 1])
        bar = i1.text_area("Job_id:", key="job_id_t", height=2)
        i2.write(st.session_state.stat)
        if st.button("Optimize", disabled=st.session_state.running):
            st.session_state.nb = 4
            cons = {
                "var": st.session_state.var / 100,
                "es": st.session_state.es / 100,
                "bounds": (st.session_state.lb / 100, st.session_state.ub / 100),
                "indus": st.session_state.indus / 100,
                "ramp": [
                    st.session_state.ramp_l,
                    st.session_state.ramp_u,
                    st.session_state.ramp_s,
                ],
                "w0": list(np.ones(st.session_state.nb) / st.session_state.nb),
                "nb": st.session_state.nb,
                "ticker": st.session_state.df_selected["Ticker"].to_list(),
            }
            """cons={
                "var":st.session_state.var/100,
                "es":st.session_state.es/100,
                "bounds":(st.session_state.lb/100,st.session_state.ub/100),
                "indus":st.session_state.indus/100,
                "ramp":[st.session_state.ramp_l,
                    st.session_state.ramp_u,
                        st.session_state.ramp_s],
                "w0":list(
                    np.ones(14)/14),
                "nb":14,
                "ticker":["LLY","AZN","NVO","NOVN","INSM","AMGN","ISRG","JNJ","MDGL","LONN","BBIO","MDT","ROIV","UTHR"]
                        }"""
            tmp = rq.post(
                "http://backend:8000/optimize/optimize", timeout=10, json={"cons": cons}
            ).json()
            st.session_state.job_id = tmp["job_id"]
            st.session_state.running = True
            lg.info("Started optimization")
            st.rerun()
