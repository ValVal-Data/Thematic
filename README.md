# GLP-1 Thematic Investment portfolio
## 1 Overview


## 1.i Table of content
1. Overview
    1. Table of content
2. Key features
3. Data sources
    1. Company data
    2. Patent data
    3. Tickers
        1. ETFs
        2. Currency Rates
4. Methodology
    1. Investment universe
    2. Thematic scoring
    3. Portfolio optimization
5. How to run the project
6. Results
7. Limitations
8. Background and motivation
9. Project structure
10. Future improvements

# 2. Key features
# 3. Data sources
## 3.i Company data
## 3.ii Patent data
## 3.iii Tickers
# 4. Methodology
## 4.i Investment universe
Company list was aggregated from the following sources:
| Provider | Fund Name | ISIN | Date |
|----------|-----------|------|------|
| BFG | BGF World Healthscience Fund | LU0331289677 | 27.04.26 |
| Ishare | Nasdaq US Biotechnology UCITS ETF | IE00BYXG2H39 | 27.04.26 |
| Pictet | Biotech | LU0843168732 | 27.04.26 |
| Pictet | Longevity | LU3099149455 | 27.04.26 |
| UBS | Sustainable Health Transformation Equity Fund USD P-acc | LU0085953304 | 27.04.26 |
| UBS | Biotech Equity Fund USD P-acc | LU0069152568 | 27.04.26 |
| MSCI | ACWI IMI SDG 3 Good Health and Well-being Select | Index | 27.04.26 |
| MSCI | ACWI IMI Digital Health | Index | 27.04.26 |

Each time, the 10 first position were taken. I added also companies that were not in these index/fund based on research of the sector. In total, 49 companies composed the universe.

## 4.ii Thematic scoring
The following component were used with each factor being from 0 to 100%
- TP: Thematic purity
    - Categories:
        - N: Effectively 0% metabolic revenue: 0%
        - L: Some exposure (products, pipeline, or tools): 10%
        - M: Important but not dominant, or mixed portfolio: 30%
        - H: Cardiometabolic/metabolic is a core revenue driver: 60%
- Innovation score
    - Components:
        - PS: Pipeline Strength
            - Pipeline Maturity (Highest):
                - PreClinical: 10%
                - Phase 1: 30%
                - Phase 2: 60%
                - Phase 3: 85%
                - Approved: 100%
            - Pipeline Breadth
                - 0-1: 10%
                - 2-3: 30%
                - 4-6: 60%
                - 7-10 80%
                - More than 10: 100% 
                - From 'https://clinicaltrials.gov/' Taking: Active, not recruiting
            - Pipeline Differentiation
                - N: Crowded space: 20%
                - L: Incremental improvement: 40%
                - M: Novel mechanism: 60%
                - H: First-in-class: 80%
                - VH: First-in-disease: 100%
            - 'Pipeline Strength = 50% Maturity + 35% Breadth + 15% Differentiation'
        - BP: Breakthrough Potential
            - Novelty of the technology
                - NA: No metabolic/cardiometabolic drugs: 0%
                - N: New formulation: 20%
                - L: Incremental improvement: 40%
                - M: Novel mechanism: 60%
                - H: First-in-class: 80%
                - VH: First-in-disease: 100% 
            - Validation
                - N: None: 0%
                - L: Preclinical: 20%
                - M: Peer-reviewed publications: 60%
                - H: Strategic partnerships: 80%
                - VH: Multiple high-quality validation: 100% 
            - 'Breakthrough Potential = 70% Novelty + 30% Validation'
        - NP: Number of active partnerships
            - N: No visible partnering activity in metabolic/cardiometabolic: 0% 
            - L: A few deals, mostly small or historic: 30% 
            - M: Regular partnering, visible in recent years: 60% 
            - H: Partnering is a core part of the business model : 90%  
    - '**Innovation score** = 40% PS + 40% BP + 20% NP'
- Revenue
    - To capture risk & investability
    - Categories:
        - Small cap < $500M: 0%
        - Medium cap < $5B: 50%
        - Large cap > $5B: 100%
- Growth metrics
    - Revenue CAGR (3 years)
- Ecosystem component
    - To capture the full ecosystem
    - Categories:
        - C: Core Innovator: 5% 
        - E: Enabler: 3%
        - A: Adopter: 0%
- '**Thematic score** = (50% Thematic purity + 30% Innovation score)(1+Ecosystem component)'
    - Not to overweight innovation

## 4.iii Portfolio optimization

# 5. How to run the project
# 6. Results
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>Theme</th>
      <th>MSCI-World</th>
      <th>MSCI-ACWI</th>
      <th>S&amp;P500</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>Annualized Return (%)</th>
      <td>18.9</td>
      <td>7.5</td>
      <td>6.7</td>
      <td>9.5</td>
    </tr>
    <tr>
      <th>Annualized Volatility (%)</th>
      <td>18.3</td>
      <td>14.9</td>
      <td>14.4</td>
      <td>16.3</td>
    </tr>
    <tr>
      <th>Max drawdown (%)</th>
      <td>-18.9</td>
      <td>-21.3</td>
      <td>-21.9</td>
      <td>-22.2</td>
    </tr>
    <tr>
      <th>Sharpe Ratio</th>
      <td>0.9</td>
      <td>0.4</td>
      <td>0.3</td>
      <td>0.5</td>
    </tr>
    <tr>
      <th>1-week VaR 97.5% (%)</th>
      <td>4.5</td>
      <td>4.5</td>
      <td>4.2</td>
      <td>5.0</td>
    </tr>
    <tr>
      <th>1-week ES 97.5% (%)</th>
      <td>5.7</td>
      <td>6.1</td>
      <td>5.9</td>
      <td>6.7</td>
    </tr>
  </tbody>
</table>
# 7. Limitations
# 8. Background and motivation
# 9. Project structure
# 10. Future improvements