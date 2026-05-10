# Option Pricing Platform

**Live app**: [option-pricing-simulator.streamlit.app](https://option-pricing-simulator.streamlit.app/)

Interactive dashboard for pricing options and computing Greeks with three models.

## Models

| Model | Style | Method | Notes |
|---|---|---|---|
| Black-Scholes | European only | Analytical | Exact Greeks, instant |
| Binomial Tree | American & European | Discrete tree | Configurable steps (10–500) |
| Heston | European only | Monte Carlo | Stochastic vol, captures smile |

## Greeks

Delta, Gamma, Theta (per day), Vega (per 1% vol move), Rho — computed analytically for Black-Scholes and via central finite differences for Binomial/Heston.


## Project structure

```
option-pricer/
├── frontend/app.py      # Streamlit app (self-contained, used in production)
├── api/main.py          # FastAPI backend (local development only)
└── requirements.txt
```

The Streamlit app embeds all pricing logic directly — no external API call needed for cloud deployment.

## Stack

- [Streamlit](https://streamlit.io/) — UI
- [Plotly](https://plotly.com/) — charts
- [NumPy](https://numpy.org/) — Monte Carlo paths
- Python `math` — analytical pricing (no Fortran compiler required on Streamlit Cloud)
