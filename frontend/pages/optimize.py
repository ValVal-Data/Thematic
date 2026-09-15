import streamlit as st
import requests as rq
import logging as lg
import numpy as np

log=lg.getLogger(__name__)

if "sc" not in st.session_state:
    st.session_state.sc=False
if "var" not in st.session_state:
    st.session_state.var=100
    st.session_state.es=100
    st.session_state.ub=100
    st.session_state.lb=0
    st.session_state.indus=1.0
    st.session_state.ramp_l=1.0
    st.session_state.ramp_u=100
    st.session_state.ramp_s=1.0
    st.session_state.job_id = ""
    st.session_state.prog_opti = 0
    st.session_state.running = False
    st.session_state.nb=len(st.session_state.df_selected)
    st.session_state.stat=""


@st.fragment(run_every="30s" if st.session_state.running else None)
def progress_update():
    if st.session_state.job_id!="":
        prog=rq.get("http://127.0.0.1:8000/optimize/progress",timeout=10,params={"job_id":st.session_state.job_id})
        if prog.status_code==404:
            lg.error(f"job '{st.session_state.job_id}' not found")
        elif prog.status_code==500:
            lg.error(f"Connection error when updating optimize")
        else:
            pro=prog.json()
            st.session_state.stat=pro["status"]
            if pro["status"] =="completed":
                st.session_state.running = False
                st.rerun()
            elif pro["status"] =="failed":
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

    e1,e2 = st.columns(2)
    with e1:
        st.session_state.var=st.slider(
            label="Var",
            min_value=0,
            max_value=100,
            disabled=st.session_state.running
        )
        st.session_state.es=st.slider(
            label="ES",
            min_value=0,
            max_value=100,
            disabled=st.session_state.running
        )
        st.session_state.indus=st.slider(
            label="Industry",
            min_value=0,
            max_value=500,
            value=100,
            disabled=st.session_state.running
        )
    with e2:
        st.session_state.lb,st.session_state.ub=st.slider(
            label="Bounds",
            min_value=0,
            max_value=100,
            value=(0,100),
            disabled=st.session_state.running
        )
        f1,f2 = st.columns(2)
        st.session_state.ramp_l,st.session_state.ramp_u=f1.slider(
            label="Temperature range",
            min_value=0,
            max_value=500,
            value=(0,500),
            disabled=st.session_state.running
        )
        st.session_state.ramp_s=f2.slider(
            label="Temperature step",
            min_value=0.0,
            max_value=5.0,
            value=0.5,
            disabled=st.session_state.running
        )
        i1,i2 = st.columns([3,1])
        bar = i1.progress(st.session_state.prog_opti)
        i2.write(st.session_state.stat)
        g1,g2 = st.columns(2)
        if g1.button("Optimize",disabled=st.session_state.running):
            """cons={
                "var":st.session_state.var,
                "es":st.session_state.es,
                "bounds":(st.session_state.lb,st.session_state.ub),
                "indus":st.session_state.indus,
                "ramp":[st.session_state.ramp_l,
                    st.session_state.ramp_u,
                        st.session_state.ramp_s],
                "w0":list(
                    np.ones(st.session_state.nb)/st.session_state.nb),
                "nb":st.session_state.nb,
                "ticker":st.session_state.df_selected["Ticker"].to_list()
            }"""
            cons={
                "var":st.session_state.var,
                "es":st.session_state.es,
                "bounds":(st.session_state.lb,st.session_state.ub),
                "indus":st.session_state.indus,
                "ramp":[st.session_state.ramp_l,
                    st.session_state.ramp_u,
                        st.session_state.ramp_s],
                "w0":list(
                    np.ones(st.session_state.nb)/st.session_state.nb),
                "nb":st.session_state.nb,
                "ticker":["LLY","AZN","NVO","NOVN"]
                        }
            tmp=rq.post("http://127.0.0.1:8000/optimize/optimize",timeout=10,json={"cons":cons}).json()
            st.session_state.job_id= tmp["job_id"]
            st.session_state.running = True
            lg.info("Started optimization")
            st.rerun()
        if g2.button("Calculate performance"):
            progress_update()