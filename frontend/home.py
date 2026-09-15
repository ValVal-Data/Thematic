import streamlit as st

st.title("Thematic Portfolio Optimizer")

st.markdown("""
## Disclamer
This app is provided for educational and illustrative purposes only. It does not constitute investment advice, financial research, or a recommendation to buy or sell any financial instrument. Any references to companies, sectors or themes are used solely to demonstrate a structured investment process.

## Getting started
This software help create a cardiometabolic investment strategy. It allows for equities scoring as well as constraint selection on the portfolio and stress testing of the strategy.

Use the navigation on the left:
- Score
    - Thematic scoring of the universe
    - Modify scoring weight and score threshold
- Optimize
    - Optimize selected equities using maximum entropy
    - Modify constraints
    - See performance
- Stress
    - Generate stress scenario
- Report
    - Produce summary of the portfolio performance
""")