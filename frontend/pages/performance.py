import copy as cp
import logging as lg

import numpy as np
import pandas as pan
import plotly.express as px
import requests as rq
import streamlit as st

from theme.plotly_theme import register_plotly_theme

register_plotly_theme()

log = lg.getLogger(__name__)


def plot_line(data, x, y, title, xlab, ylab, leg):
    if x != "":
        line = px.line(data, y=y, x=x, title=title)
    else:
        line = px.line(data, y=y, title=title)
    line.update_xaxes(title=xlab)
    line.update_yaxes(title=ylab)
    line.update_layout(
        legend=dict(
            x=0.01,
            y=0.99,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(255,255,255,0.0)",
            borderwidth=0,
        ),
        legend_title_text=leg,
    )
    return line


def plot_line_wmean(data, x, y, title, xlab, ylab, leg):
    if x != "":
        li = px.line(data, y=y, x=x, title=title)
    else:
        li = px.line(data, y=y, title=title)
    li.update_xaxes(title=xlab)
    li.update_yaxes(title=ylab)
    if len(y) > 1:
        li.update_layout(
            legend=dict(
                x=0.01,
                y=0.99,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.0)",
                borderwidth=0,
            ),
            legend_title_text=leg,
        )
    else:
        li.update_layout(showlegend=False)

    for trace in li.data:
        color = trace.line.color

        li.add_hline(y=trace.y.mean(), line_color=color, line_dash="dash")
    return li


def make_data_table(data, id):
    tmp = pan.DataFrame([[row[id] for row in x] for _, x in data.items()]).transpose()
    tmp.columns = list(data.keys())
    return tmp


if "job_id" not in st.session_state:
    st.session_state.job_id = False
    st.session_state.response = {}
    st.session_state.performance = pan.DataFrame({})
    st.session_state.bench = pan.DataFrame({})
    st.session_state.tab = pan.DataFrame({})
    st.session_state.pca_tab = pan.DataFrame({})
    st.session_state.pca_heat = pan.DataFrame({})
    st.session_state.var = []
st.title("Portfolio Analytics")
tabLoad, tabDist, tabIndicator, tabPerf, tabRisk = st.tabs(
    ["Load", "Distribution", "Indicators", "Performance", "Risk"]
)

with tabLoad:
    bar = st.text_area("Job id:", key="job_id_t", height=1)

    if st.button("Load"):
        st.session_state.response = rq.get(
            "http://backend:8000/performance/perf", timeout=10, params={"job_id": bar}
        ).json()
        st.session_state.name = st.session_state.response["name"]
        st.session_state.performance = pan.DataFrame(
            {
                x: st.session_state.response[x]
                for x in [
                    "date_month",
                    "Cum Return net",
                    "Cum Return",
                    "turnover",
                    "Return",
                    "Return net",
                ]
            }
        )
        st.session_state.performance *= 100
        st.session_state.performance["date_month"] = st.session_state.response["date_month"]
        st.session_state.performance["Mean turnover"] = [
            np.mean(st.session_state.performance["turnover"])
            for x in st.session_state.performance["turnover"]
        ]
        st.session_state.performance["Median turnover"] = [
            np.median(st.session_state.performance["turnover"])
            for x in st.session_state.performance["turnover"]
        ]
        st.session_state.performance["Q90% turnover"] = [
            np.quantile(st.session_state.performance["turnover"], 0.9)
            for x in st.session_state.performance["turnover"]
        ]

        st.session_state.bench = pan.DataFrame(st.session_state.response["bench"]) * 100

        st.session_state.tab = pan.DataFrame(
            [
                {
                    x: st.session_state.response[x]
                    for x in ["cagr_gross", "cagr_net", "cost_annual"]
                }
            ]
        )
        st.session_state.tab *= 100
        st.session_state.tab = st.session_state.tab.round(1)
        st.session_state.tab.index = ["Value (%)"]

        st.session_state.pca_tab = pan.DataFrame([st.session_state.response["pca_factor"]["0"]])
        # st.session_state.pca_tab*=100
        st.session_state.pca_tab = st.session_state.pca_tab.round(1)
        st.session_state.pca_tab.index = ["Value (%)"]

        st.session_state.pca_heat = pan.DataFrame(st.session_state.response["pca"][1])
        st.session_state.pca_heat.index = st.session_state.response["bench_name"]
        st.session_state.pca_heat.columns = [
            f"PC{x + 1}" for x, _ in enumerate(st.session_state.response["bench_name"])
        ]

        st.session_state.var = [x * 100 for x in st.session_state.response["pca"][2]]

        response = rq.get("http://backend:8000/score/universe", timeout=10).json()
        st.session_state.df2 = pan.DataFrame(cp.deepcopy(response), index=response["index"])

        st.session_state.df2 = st.session_state.df2[
            st.session_state.df2["Ticker"].isin(st.session_state.name)
        ]

        st.session_state.job_id = True

if st.session_state.job_id:
    with tabDist:
        pie_industry = px.pie(st.session_state.df2, names="Industry", title="Industry")
        pie_industry.update_traces(textposition="inside", textinfo="percent+label")
        pie_industry.update_layout(showlegend=False)
        pie_location = px.pie(st.session_state.df2, names="Location", title="Location")
        pie_location.update_traces(textposition="inside", textinfo="percent+label")
        pie_location.update_layout(showlegend=False)

        pie_cap = px.pie(st.session_state.df2, names="Cap", title="Size")
        pie_cap.update_traces(textposition="inside", textinfo="percent+label")
        pie_cap.update_layout(showlegend=False)

        g = st.columns(3)
        with g[0]:
            st.plotly_chart(pie_industry)
        with g[1]:
            st.plotly_chart(pie_location)
        with g[2]:
            st.plotly_chart(pie_cap)
        st.dataframe(
            st.session_state.df2[
                ["Name", "Ticker", "Location", "Industry", "Cap", "Revenue", "CAGR", "Score"]
            ],
            hide_index=True,
        )
    with tabIndicator:
        ti1, ti2, ti3 = st.columns(3)
        with ti1:
            st.subheader("Performance")
            st.dataframe(st.session_state.tab[["cagr_gross", "cagr_net"]].transpose())
        with ti2:
            st.subheader("Risk")
            st.dataframe(st.session_state.tab[["cost_annual"]].transpose())
        with ti3:
            st.subheader("Factor")
            st.dataframe(st.session_state.pca_tab.transpose())

    with tabPerf:
        c1, c2, c3 = st.columns(3)
        with c1:
            line_ret = plot_line(
                st.session_state.performance,
                "date_month",
                ["Cum Return", "Cum Return net"],
                "Returns",
                "Week",
                "Cumulative Return (%)",
                "",
            )
            st.plotly_chart(line_ret)
        with c2:
            line_turn = plot_line(
                st.session_state.performance,
                "date_month",
                ["turnover", "Mean turnover", "Median turnover", "Q90% turnover"],
                "Turnover",
                "Week",
                "Turnover (%)",
                "",
            )
            st.plotly_chart(line_turn)
        with c3:
            line_bench = plot_line(
                st.session_state.bench,
                "",
                ["Fund", "MSCI-World", "SP500"],
                "Benchmark",
                "Week",
                "Cumulative Return (%)",
                "",
            )
            st.plotly_chart(line_bench)

        d1, d2 = st.columns(2)
        with d1:
            line_pca = px.scatter(
                y=st.session_state.var, x=range(1, len(st.session_state.var) + 1), title="PCA"
            )
            line_pca.update_xaxes(title="Component")
            line_pca.update_yaxes(title="Variance explained (%)")
            st.plotly_chart(line_pca)
        with d2:
            heat_pca = px.imshow(
                st.session_state.pca_heat.transpose() * 100,
                title="PCA Loading Heatmap",
                color_continuous_scale="RdBu_r",
                zmin=-100,
                zmax=100,
            )
            heat_pca.update_coloraxes(colorbar_title="Correlation (%)")
            st.plotly_chart(heat_pca)
    with tabRisk:
        (
            tabExposure,
            tabConcentration,
            tabRisk2,
        ) = st.tabs(["Exposure", "Concentration", "Indicators"])
        with tabExposure:
            tr1 = st.columns(2)
            with tr1[0]:
                tmp = pan.DataFrame(st.session_state.response["exp_ind"])
                tmp *= 100
                lw_exp_ind = plot_line_wmean(
                    tmp, "", tmp.columns, "Industry exposure", "Week", "Exposure (%)", ""
                )
                st.plotly_chart(lw_exp_ind)
            with tr1[1]:
                tmp = pan.DataFrame(st.session_state.response["exp_loca"])
                tmp *= 100
                lw_exp_loc = plot_line_wmean(
                    tmp, "", tmp.columns, "Geographic exposure", "Week", "Exposure (%)", ""
                )
                st.plotly_chart(lw_exp_loc)
            tr2 = st.columns(2)
            with tr2[0]:
                tmp = pan.DataFrame(st.session_state.response["exp_cap"])
                tmp *= 100
                lw_exp_cap = plot_line_wmean(
                    tmp, "", tmp.columns, "Cap exposure", "Week", "Exposure (%)", ""
                )
                st.plotly_chart(lw_exp_cap)
            with tr2[1]:
                tmp = pan.DataFrame(st.session_state.response["exp_theme"])
                lw_exp_theme = plot_line_wmean(
                    tmp, "", tmp.columns, "Theme exposure", "Week", "Exposure (%)", ""
                )
                st.plotly_chart(lw_exp_theme)

        with tabConcentration:
            ca = st.columns(3)
            with ca[0]:
                line_hhi = px.line(
                    st.session_state.response["hhi"], title="Herfindahl-Hirschmann index"
                )
                line_hhi.update_layout(showlegend=False)
                line_hhi.add_hline(
                    y=np.mean(st.session_state.response["hhi"]),
                    line_dash="dash",
                    line_color="#0B2239",
                )
                line_hhi.update_xaxes(title="6 month rolling windows", showticklabels=False)
                line_hhi.update_yaxes(title="H")
                st.plotly_chart(line_hhi)

            with ca[1]:
                tmp = pan.DataFrame(
                    [
                        st.session_state.response["cr5"],
                        st.session_state.response["cr8"],
                        st.session_state.response["cr3"],
                    ]
                ).transpose()
                tmp.columns = ["CR3", "CR5", "CR8"]
                lw_conc = plot_line_wmean(
                    tmp, "", tmp.columns, "Concentration", "6 month rolling windows", "CRx", ""
                )
                lw_conc.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_conc)

            with ca[2]:
                tmp = pan.DataFrame(st.session_state.response["exp_w"])
                tmp *= 100
                box_w = px.box(tmp, title="Weight distribution")
                box_w.update_xaxes(showticklabels=False)
                box_w.update_xaxes(title="Position")
                box_w.update_yaxes(title="Weight (%)")
                st.plotly_chart(box_w)
        with tabRisk2:
            ra1 = st.columns(3)
            with ra1[0]:
                tmp = make_data_table(st.session_state.response["met"], 1)
                lw_vol = plot_line_wmean(
                    tmp,
                    "",
                    tmp.columns,
                    "Volatility",
                    "6 month rolling windows",
                    "Annualized volatility (%)",
                    "",
                )
                lw_vol.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_vol)
            with ra1[1]:
                tmp = make_data_table(st.session_state.response["met"], 2)
                lw_vol = plot_line_wmean(
                    tmp,
                    "",
                    tmp.columns,
                    "Maximum Drawdown",
                    "6 month rolling windows",
                    "Maximum Drawdown (%)",
                    "",
                )
                lw_vol.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_vol)
            with ra1[2]:
                tmp = make_data_table(st.session_state.response["met"], 3)
                lw_vol = plot_line_wmean(
                    tmp,
                    "",
                    tmp.columns,
                    "Sharpe ratio",
                    "6 month rolling windows",
                    "Sharpe ratio",
                    "",
                )
                lw_vol.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_vol)
            ra2 = st.columns(2)
            with ra2[0]:
                tmp = make_data_table(st.session_state.response["met"], 4)
                lw_vol = plot_line_wmean(
                    tmp,
                    "",
                    tmp.columns,
                    "Value at Risk",
                    "6 month rolling windows",
                    "6-months 97.5& VaR (%)",
                    "",
                )
                lw_vol.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_vol)
            with ra2[1]:
                tmp = make_data_table(st.session_state.response["met"], 5)
                lw_vol = plot_line_wmean(
                    tmp,
                    "",
                    tmp.columns,
                    "Expected Shortfall",
                    "6 month rolling windows",
                    "6-months 97.5& ES (%)",
                    "",
                )
                lw_vol.update_xaxes(showticklabels=False)
                st.plotly_chart(lw_vol)
