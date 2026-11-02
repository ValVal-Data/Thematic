import copy as cp
import logging as lg
from itertools import chain

import numpy as np
import pandas as pan
import plotly.express as px
import requests as rq
import streamlit as st

from theme.plotly_theme import register_plotly_theme

register_plotly_theme()

log = lg.getLogger(__name__)

if "df" not in st.session_state:
    response = rq.get("http://backend:8000/score/universe", timeout=10).json()
    st.session_state.df = pan.DataFrame(cp.deepcopy(response), index=response["index"])
if "weight" not in st.session_state:
    response = rq.get("http://backend:8000/score/weight", timeout=10).json()
    st.session_state.weight = cp.deepcopy(response)
if "threshold" not in st.session_state:
    st.session_state.threshold = 0.25
if "df_selected" not in st.session_state:
    mask = st.session_state.df["Score"] >= st.session_state.threshold
    st.session_state.df_selected = st.session_state.df[mask]
if "sc" not in st.session_state:
    st.session_state.sc = False

if "weight_value" not in st.session_state:
    st.session_state.weight_value = [
        [False for _ in inner] for inner in st.session_state.weight.values()
    ]


def update(key_widget) -> None:
    key1, key2 = key_widget.split("_")
    st.session_state.weight[key1][key2] = st.session_state[key_widget]


st.title("Thematic score")
hist_score = px.histogram(st.session_state.df, x="Score", nbins=30, title="Score distribution")
hist_score_country = px.histogram(
    st.session_state.df,
    x="Score",
    color="Location",
    nbins=10,
    title="Location",
    histnorm="probability",
    barmode="overlay",
)
hist_score_country.update_layout(
    legend=dict(
        x=0.98, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(0,0,0,0)", borderwidth=0
    )
)
hist_score_country.update_xaxes(range=[0, 1])
hist_score_industry = px.histogram(
    st.session_state.df,
    x="Score",
    color="Industry",
    nbins=10,
    title="Industry",
    histnorm="probability",
    barmode="overlay",
)
hist_score_industry.update_yaxes(range=[0, 2.5])
hist_score_industry.update_xaxes(range=[0, 1])
hist_score_industry.update_layout(
    legend=dict(
        x=0.98, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(0,0,0,0)", borderwidth=0
    )
)
hist_score_size = px.histogram(
    st.session_state.df,
    x="Score",
    color="Cap",
    nbins=10,
    title="Size",
    histnorm="probability",
    barmode="overlay",
)
hist_score_size.update_layout(
    legend=dict(
        x=0.98, y=0.98, xanchor="right", yanchor="top", bgcolor="rgba(0,0,0,0)", borderwidth=0
    )
)
hist_score_size.update_xaxes(range=[0, 1])

bins = np.linspace(0, 1, 20)
binsx = [(a + b) / 2 for a, b in zip(bins[:-1], bins[1:], strict=False)]
counts, _ = np.histogram(st.session_state.df["Score"], bins=bins)
cum_counts = np.cumsum(counts)
cum_counts = cum_counts[-1] - cum_counts
line_cumsum = px.line(x=binsx, y=cum_counts, title="Cumulative count")
line_cumsum.update_xaxes(title="Score threshold")
line_cumsum.update_yaxes(title="Count")
line_cumsum.update_traces(fill="tozeroy")
line_cumsum.add_vline(x=st.session_state.threshold, line_color="#0B2239", line_dash="dash")
line_cumsum.update_layout(height=350)


pie_industry = px.pie(st.session_state.df, names="Industry", title="Universe")
pie_industry.update_traces(textposition="inside", textinfo="percent+label")
pie_industry.update_layout(showlegend=False, height=350)
pie_location = px.pie(st.session_state.df, names="Location", title="Universe")
pie_location.update_traces(textposition="inside", textinfo="percent+label")
pie_location.update_layout(showlegend=False, height=350)

pie_cap = px.pie(st.session_state.df, names="Cap", title="Universe")
pie_cap.update_traces(textposition="inside", textinfo="percent+label")
pie_cap.update_layout(showlegend=False, height=350)

pie_industry_sel = px.pie(st.session_state.df_selected, names="Industry", title="Selection")
pie_industry_sel.update_traces(textposition="inside", textinfo="percent+label")
pie_industry_sel.update_layout(showlegend=False, height=350)

pie_location_sel = px.pie(st.session_state.df_selected, names="Location", title="Selection")
pie_location_sel.update_traces(textposition="inside", textinfo="percent+label")
pie_location_sel.update_layout(showlegend=False, height=350)

pie_cap_sel = px.pie(st.session_state.df_selected, names="Cap", title="Selection")
pie_cap_sel.update_traces(textposition="inside", textinfo="percent+label")
pie_cap_sel.update_layout(showlegend=False, height=350)
tabPie, tabHist, tabTable = st.tabs(["Universe vs Selection", "Score Distributions", "Table"])
with tabPie:
    g = st.columns(3)
    with g[0]:
        st.write("**Industry**")
    with g[1]:
        st.write("**Location**")
    with g[2]:
        st.write("**Company size**")

    c = st.columns(6)
    with c[0]:
        st.plotly_chart(pie_industry)
    with c[1]:
        st.plotly_chart(pie_industry_sel)
    with c[2]:
        st.plotly_chart(pie_location)
    with c[3]:
        st.plotly_chart(pie_location_sel)
    with c[4]:
        st.plotly_chart(pie_cap)
    with c[5]:
        st.plotly_chart(pie_cap_sel)

with tabHist:
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.plotly_chart(hist_score)
    with e2:
        st.plotly_chart(hist_score_industry)
    with e3:
        st.plotly_chart(hist_score_country)
    with e4:
        st.plotly_chart(hist_score_size)

with tabTable:
    st.dataframe(
        st.session_state.df[
            ["Name", "Ticker", "Location", "Industry", "Cap", "Revenue", "CAGR", "Score"]
        ],
        hide_index=True,
    )

st.subheader("Weights")
st.latex(
    "Thematic Score = (Thematic + (Pipeline + Breakthrough + Innovation) + \
        Revenue + CAGR)*(1 + Ecosystem \\; component)"
)
d1, d2 = st.columns([3, 1])
with d1:
    co = d1.columns(len(st.session_state.weight.keys()))
    for x, group in enumerate(st.session_state.weight):
        co[x].subheader(group)
        for y, value in enumerate(st.session_state.weight[group]):
            widget_key = "_".join([group, value])
            if widget_key not in st.session_state:
                st.session_state[widget_key] = st.session_state.weight[group][value]
            if y >= len(st.session_state.weight[group].keys()) - 1:
                su = sum(list(st.session_state.weight[group].values())[:-1])
                st.session_state[widget_key] = 1 - su
                co[x].slider(
                    label=f"{value}",
                    min_value=min([0.0, 1 - su]),
                    max_value=max([1.0, 1 - su]),
                    key=widget_key,
                    disabled=True,
                )
                if su > 1.0:
                    st.session_state.weight_value[x][y] = True
                    co[x].write("Sum of weight > 1.0")
                else:
                    st.session_state.weight_value[x][y] = False
            else:
                co[x].slider(label=f"{value}", min_value=0.0, max_value=1.0, key=widget_key)
            update(widget_key)

over = any(chain.from_iterable(st.session_state.weight_value))
with d2:
    st.plotly_chart(line_cumsum)
    if st.button("Recalculate score", disabled=over):
        lg.info("Recalculating score")
        rq.put("http://backend:8000/score/weight", timeout=10, json=st.session_state.weight)
        rq.post("http://backend:8000/score/score")
        response = rq.get("http://backend:8000/score/universe", timeout=10).json()
        st.session_state.df = pan.DataFrame(cp.deepcopy(response), index=response["index"])
        st.rerun()
    st.slider(
        label="Threshold",
        min_value=0.0,
        max_value=1.0,
        key="threshold",
    )
    if st.button("Recalculate composition"):
        lg.info("Recalculating composition")
        mask = st.session_state.df["Score"] >= st.session_state.threshold
        st.session_state.df_selected = st.session_state.df[mask]
        st.session_state.sc = True
        st.rerun()
