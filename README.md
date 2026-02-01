# Option Pricing Platform

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

### Install Dependencies

First, create and activate a virtual environment (recommended):

```bash
# Create virtual environment
python3 -m venv option-pricer-venv

# Activate it (Linux/Mac)
source option-pricer-venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start the API

```bash
# Make sure virtual environment is activated
source option-pricer-venv/bin/activate
python api/main.py
```

The API will run on http://0.0.0.0:8000

### Start the Dashboard

Open a new terminal and activate the virtual environment:

```bash
source option-pricer-venv/bin/activate
streamlit run frontend/app.py
```

The dashboard will open at http://localhost:8501

## Usage

1. Configure option parameters in the sidebar
2. Select pricing model
3. Click Calculate Price
4. View results and interactive charts

## API Endpoints

### POST /price

Price an option and calculate Greeks.

Request:
```json
{
  "spot": 100,
  "strike": 100,
  "maturity_years": 1.0,
  "rate": 0.05,
  "vol": 0.2,
  "option_type": "call",
  "model": "black-scholes",
  "is_american": false,
  "steps": 100,
  "mean_reversion": 2.0,
  "vol_of_vol": 0.5,
  "correlation": -0.5,
  "num_simulations": 10000
}
```

Response:
```json
{
  "price": 10.4506,
  "delta": 0.6368,
  "gamma": 0.0188,
  "theta": -0.0176,
  "vega": 0.3752,
  "rho": 0.5323,
  "model": "Black-Scholes"
}
```

**Parameters:**
- `spot`: Current price of underlying asset (required, > 0)
- `strike`: Strike price (required, > 0)
- `maturity_years`: Time to expiration in years (required, > 0)
- `rate`: Risk-free interest rate (required)
- `vol`: Volatility (required, > 0)
- `option_type`: "call" or "put" (required)
- `model`: "black-scholes", "binomial", or "heston" (default: "black-scholes")
- `is_american`: Enable early exercise for Binomial model (default: false)
- `steps`: Number of steps for Binomial tree (10-500, default: 100)
- `mean_reversion`: Mean reversion speed for Heston (default: 2.0)
- `vol_of_vol`: Volatility of volatility for Heston (default: 0.5)
- `correlation`: Correlation between price and volatility for Heston (-1 to 1, default: -0.5)
- `num_simulations`: Number of Monte Carlo simulations for Heston (1000-50000, default: 10000)

### POST /payoff

Generate payoff diagram data for visualization.

**Parameters:** Same as `/price` endpoint

**Response:**
```json
{
  "spot_range": [50, 51, ..., 150],
  "option_prices": [50.0, 49.5, ..., 0.1],
  "payoffs": [0, 0, ..., 50],
  "strike": 100
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok"
}
```

## Project Structure

```
option-pricer/
├── api/
│   └── main.py           # FastAPI backend
├── frontend/
│   └── app.py            # Streamlit dashboard
├── requirements.txt      # Dependencies
└── README.md
```

## Models

**Black-Scholes**
- Analytical solution for European options
- Fast and precise
- Constant volatility assumption

**Binomial Tree**
- Discrete-time model
- Supports early exercise (American options)
- Configurable steps

**Heston Model**
- Stochastic volatility
- Monte Carlo simulation
- Captures volatility smile

## Requirements

- Python 3.8+
- FastAPI 0.115.0
- Uvicorn 0.32.0
- Streamlit 1.39.0
- NumPy 1.26.4
- SciPy 1.13.1
- Plotly 5.24.1
- Requests 2.32.3
- Pydantic 2.9.0

## Notes

- **Virtual Environment**: It's highly recommended to use a virtual environment to avoid dependency conflicts
- **Linux/Mac vs Windows**: The virtual environment activation command differs:
  - Linux/Mac: `source option-pricer-venv/bin/activate`
  - Windows: `option-pricer-venv\Scripts\activate`
- **API Server**: Runs on http://0.0.0.0:8000 (accessible from network) 
- **Dashboard**: Runs on http://localhost:8501 (local only)
- **Model Selection**: Black-Scholes and Heston only support European options; use Binomial for American options

