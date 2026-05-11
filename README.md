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

## Run locally

```bash
# Linux: install Python dev headers (required for C++ engine)
sudo apt-get install python3-dev

# Build C++ engine, create venv, install dependencies
bash build.sh

source venv/bin/activate
streamlit run frontend/app.py
```

Opens at `http://localhost:8501`.

> Without the C++ engine the app falls back to the pure-Python implementation automatically.

## Project structure

```
option-pricer/
├── cpp/
│   ├── pricer.cpp       # Binomial tree + Heston MC in C++
│   ├── pricer.hpp
│   └── bindings.cpp     # pybind11 bindings
├── frontend/app.py      # Streamlit app (self-contained, used in production)
├── api/main.py          # FastAPI backend (local development only)
├── build.sh             # Builds C++ extension into build/
├── CMakeLists.txt
└── requirements.txt
```

The Streamlit app embeds all pricing logic directly — no external API needed for cloud deployment. The C++ engine is loaded at runtime if available; otherwise the app uses the pure-Python fallback.

## Stack

- [Streamlit](https://streamlit.io/) — UI
- [Plotly](https://plotly.com/) — charts
- [NumPy](https://numpy.org/) — Monte Carlo paths (Python fallback)
- [pybind11](https://pybind11.readthedocs.io/) — C++ bindings (local only)
- Python `math` — analytical pricing (no Fortran compiler required on Streamlit Cloud)
