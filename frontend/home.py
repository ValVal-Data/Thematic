import streamlit as st

from theme.plotly_theme import register_plotly_theme

register_plotly_theme()


st.title("Thematic Portfolio Optimizer")

st.markdown("""
## Disclaimer

This application is provided for educational and illustrative purposes only. It does not constitute investment advice, financial research, or a recommendation to buy, sell, or hold any financial instrument. Any references to companies, sectors, technologies, or investment themes are included solely to demonstrate a structured investment research and portfolio-construction process.


## Overview

This platform supports the construction and evaluation of a cardiometabolic thematic equity strategy. It combines scientific analysis, financial assessment, and quantitative portfolio optimisation within a transparent and reproducible research workflow.

The investment universe spans pharmaceuticals, biotechnology, medical devices, life-science tools, and manufacturing enablers. Companies are evaluated using a proprietary thematic framework that incorporates factors such as theme exposure, pipeline maturity, differentiation, innovation, validation, partnerships, and commercial traction.

Portfolio allocations are generated using a constrained maximum-entropy optimisation framework designed to balance expected return, thematic conviction, diversification, and turnover control.


## Navigation

Use the navigation menu on the left to access the different stages of the investment process:

### Score
Generate thematic scores for the investment universe.

- Assess cardiometabolic exposure and strategic relevance
- Review company-level scoring components
- Adjust factor weights and inclusion thresholds
- Analyse score distributions and rankings

### Optimize
Construct and analyse portfolio allocations.

- Select eligible securities
- Configure portfolio constraints
- Optimise weights using the maximum-entropy framework

### Analyze
Assess portfolio performance and risk.

- Evalutate performance and drivers
- Measure portfolio sensitivity and exposure shifts
- Evaluate concentration and risk impacts


## Key Features

- Proprietary cardiometabolic thematic scoring methodology
- Bayesian maximum-entropy portfolio optimisation
- Portfolio performance and risk analysis
- Factor and PCA-based risk decomposition
- SQL-backed research database
- REST API integration
- Interactive analytics dashboards
- Reproducible and containerised deployment
""")
