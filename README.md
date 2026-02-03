# Option Pricing Platform

**Live App**: [https://option-pricing-simulator.streamlit.app/](https://option-pricing-simulator.streamlit.app/)

Option pricing with Black-Scholes, Binomial, and Heston models.

## Features

**Three Pricing Models**
- Black-Scholes (analytical)
- Binomial Tree (American & European)
- Heston (stochastic volatility with Monte Carlo)

**Full Greeks Calculation**
- Delta, Gamma, Theta, Vega, Rho

**Interactive Dashboard**
- Real-time pricing
- Payoff diagrams
- Value decomposition charts
- Greeks sensitivity analysis

## Quick Start

### Option 1: Run Locally

```bash
# Create virtual environment
python3 -m venv option-pricer-venv

# Activate it (Linux/Mac)
source option-pricer-venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run frontend/app.py
```

The dashboard will open at http://localhost:8501

### Option 2: Run on Streamlit Cloud

Visit: [Option Pricing Platform](https://option-pricing-simulator.streamlit.app/)

No installation needed—runs directly in your browser!

## Usage

1. **Configure Parameters**: Use the sidebar to set:
   - Spot & Strike prices
   - Time to maturity
   - Risk-free rate & Volatility
   - Option type (call/put)
   
2. **Select Pricing Model**:
   - **Black-Scholes**: Fast analytical solution for European options
   - **Binomial Tree**: Discrete-time model supporting American options
   - **Heston**: Stochastic volatility with Monte Carlo simulation
   
3. **Click Calculate Price** to compute option value and Greeks

4. **View Results**:
   - Price, Greeks, intrinsic/time value decomposition
   - Payoff diagram vs underlying price
   - Greeks sensitivity across spot, gamma, and time

## Architecture

**Standalone Streamlit App**: All pricing functions are integrated directly into the frontend for cloud deployment without external API dependencies.

**Pricing Functions**:
- Pure Python implementations using `math` module (erf, sqrt, log, exp)
- No external scientific libraries needed for cloud deployment
- Efficient NumPy array operations for vectorized calculations

## Project Structure

```
option-pricer/
├── frontend/
│   └── app.py            # Streamlit dashboard with integrated pricing
├── api/
│   └── main.py           # FastAPI backend (optional for local development)
├── requirements.txt      # Dependencies
├── runtime.txt           # Python version for Streamlit Cloud
└── README.md
```

## Pricing Models

**Black-Scholes**
- Analytical solution for European options
- O(1) computation
- Constant volatility assumption
- Fastest pricing method

**Binomial Tree**
- Discrete-time recombining tree
- Supports American options with early exercise
- Configurable steps (10-500)
- More accurate near expiration

**Heston Model**
- Stochastic volatility using CIR process
- Monte Carlo simulation (1000-50000 paths)
- Captures volatility smile effects
- Most flexible but slowest

## Tech Stack

- **Frontend**: Streamlit 1.39.0
- **Visualizations**: Plotly 5.24.1
- **Numerical Computing**: NumPy 1.26.4
- **Math Functions**: Python `math` module (erf, sqrt, log, exp)
- **Deployment**: Streamlit Cloud

## Requirements

- Python 3.8+
- Streamlit 1.39.0
- NumPy 1.26.4
- Plotly 5.24.1

See [requirements.txt](requirements.txt) for full list.

## Notes

- **Virtual Environment**: Recommended to avoid dependency conflicts
  - Create: `python3 -m venv option-pricer-venv`
  - Activate (Linux/Mac): `source option-pricer-venv/bin/activate`
  - Activate (Windows): `option-pricer-venv\Scripts\activate`

- **Model Limitations**:
  - Black-Scholes: European options only
  - Heston: European options only
  - Binomial: Supports both American & European options

- **Cloud Deployment**: Optimized for Streamlit Cloud with pure-Python numerical methods (no Fortran compiler needed)

