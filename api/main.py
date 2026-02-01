from math import exp, log, sqrt, erf, pi
from typing import Literal
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Option Pricing API",
    version="1.0.0",
    description="Pure Python option pricing with Black-Scholes, Binomial, and Heston models"
)


class OptionRequest(BaseModel):
    spot: float = Field(..., gt=0)
    strike: float = Field(..., gt=0)
    maturity_years: float = Field(..., gt=0)
    rate: float
    vol: float = Field(..., gt=0)
    option_type: Literal["call", "put"]
    model: Literal["black-scholes", "binomial", "heston"] = Field("black-scholes")
    is_american: bool = False
    steps: int = Field(100, ge=10, le=500)
    mean_reversion: float = 2.0
    vol_of_vol: float = 0.5
    correlation: float = Field(-0.5, ge=-1, le=1)
    num_simulations: int = Field(10000, ge=1000, le=50000)


class OptionResponse(BaseModel):
    price: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float
    model: str


def black_scholes_price(spot: float, strike: float, rate: float, vol: float, 
                       maturity: float, is_call: bool) -> float:
    def norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + erf(x / sqrt(2.0)))

    d1 = (log(spot / strike) + (rate + 0.5 * vol ** 2) * maturity) / (vol * sqrt(maturity))
    d2 = d1 - vol * sqrt(maturity)
    
    if is_call:
        price = spot * norm_cdf(d1) - strike * exp(-rate * maturity) * norm_cdf(d2)
    else:
        price = strike * exp(-rate * maturity) * norm_cdf(-d2) - spot * norm_cdf(-d1)
    
    return price


def black_scholes_greeks(spot: float, strike: float, rate: float, vol: float,
                        maturity: float, is_call: bool) -> dict:
    def norm_pdf(x: float) -> float:
        return (1.0 / sqrt(2.0 * pi)) * exp(-0.5 * x * x)

    def norm_cdf(x: float) -> float:
        return 0.5 * (1.0 + erf(x / sqrt(2.0)))

    d1 = (log(spot / strike) + (rate + 0.5 * vol ** 2) * maturity) / (vol * sqrt(maturity))
    d2 = d1 - vol * sqrt(maturity)
    
    price = black_scholes_price(spot, strike, rate, vol, maturity, is_call)
    
    if is_call:
        delta = norm_cdf(d1)
    else:
        delta = norm_cdf(d1) - 1
    
    gamma = norm_pdf(d1) / (spot * vol * sqrt(maturity))
    
    theta_common = -(spot * norm_pdf(d1) * vol) / (2 * sqrt(maturity))
    if is_call:
        theta = theta_common - rate * strike * exp(-rate * maturity) * norm_cdf(d2)
    else:
        theta = theta_common + rate * strike * exp(-rate * maturity) * norm_cdf(-d2)
    theta = theta / 365
    
    vega = spot * norm_pdf(d1) * sqrt(maturity)
    
    if is_call:
        rho = strike * maturity * exp(-rate * maturity) * norm_cdf(d2)
    else:
        rho = -strike * maturity * exp(-rate * maturity) * norm_cdf(-d2)
    
    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }


def binomial_price(spot: float, strike: float, rate: float, vol: float,
                  maturity: float, is_call: bool, is_american: bool, steps: int) -> float:
    dt = maturity / steps
    u = exp(vol * sqrt(dt))
    d = 1 / u
    p = (exp(rate * dt) - d) / (u - d)
    discount = exp(-rate * dt)
    
    prices = np.zeros(steps + 1)
    for i in range(steps + 1):
        prices[i] = spot * (u ** (steps - i)) * (d ** i)
    
    if is_call:
        values = np.maximum(prices - strike, 0)
    else:
        values = np.maximum(strike - prices, 0)
    
    for step in range(steps - 1, -1, -1):
        for i in range(step + 1):
            values[i] = discount * (p * values[i] + (1 - p) * values[i + 1])
            
            if is_american:
                current_price = spot * (u ** (step - i)) * (d ** i)
                if is_call:
                    intrinsic = max(current_price - strike, 0)
                else:
                    intrinsic = max(strike - current_price, 0)
                values[i] = max(values[i], intrinsic)
    
    return values[0]


def binomial_greeks(spot: float, strike: float, rate: float, vol: float,
                   maturity: float, is_call: bool, is_american: bool, steps: int) -> dict:
    price = binomial_price(spot, strike, rate, vol, maturity, is_call, is_american, steps)
    
    h = spot * 0.01
    price_up = binomial_price(spot + h, strike, rate, vol, maturity, is_call, is_american, steps)
    price_down = binomial_price(spot - h, strike, rate, vol, maturity, is_call, is_american, steps)
    delta = (price_up - price_down) / (2 * h)
    
    gamma = (price_up - 2 * price + price_down) / (h ** 2)
    
    h_vol = 0.01
    price_vol_up = binomial_price(spot, strike, rate, vol + h_vol, maturity, is_call, is_american, steps)
    vega = (price_vol_up - price) / h_vol
    
    h_time = 1 / 365
    if maturity > h_time:
        price_time = binomial_price(spot, strike, rate, vol, maturity - h_time, is_call, is_american, steps)
        theta = (price_time - price) / h_time
    else:
        theta = 0
    
    h_rate = 0.01
    price_rate_up = binomial_price(spot, strike, rate + h_rate, vol, maturity, is_call, is_american, steps)
    rho = (price_rate_up - price) / h_rate
    
    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho
    }


def heston_price(spot: float, strike: float, rate: float, vol: float, maturity: float,
                is_call: bool, num_sims: int, kappa: float, sigma: float, rho: float) -> float:
    np.random.seed(42)
    dt = maturity / 100
    num_steps = 100
    
    S = np.full(num_sims, spot)
    V = np.full(num_sims, vol ** 2)
    
    for _ in range(num_steps):
        Z1 = np.random.standard_normal(num_sims)
        Z2 = np.random.standard_normal(num_sims)
        W1 = Z1
        W2 = rho * Z1 + sqrt(1 - rho ** 2) * Z2
        
        V_new = V + kappa * (vol ** 2 - V) * dt + sigma * np.sqrt(np.maximum(V, 0)) * sqrt(dt) * W2
        V = np.maximum(V_new, 0)
        
        S = S * np.exp((rate - 0.5 * V) * dt + np.sqrt(V) * sqrt(dt) * W1)
    
    if is_call:
        payoff = np.maximum(S - strike, 0)
    else:
        payoff = np.maximum(strike - S, 0)
    
    price = exp(-rate * maturity) * np.mean(payoff)
    return price


def heston_greeks(spot: float, strike: float, rate: float, vol: float, maturity: float,
                 is_call: bool, num_sims: int, kappa: float, sigma: float, rho: float) -> dict:
    price = heston_price(spot, strike, rate, vol, maturity, is_call, num_sims, kappa, sigma, rho)
    
    h = spot * 0.01
    price_up = heston_price(spot + h, strike, rate, vol, maturity, is_call, num_sims, kappa, sigma, rho)
    price_down = heston_price(spot - h, strike, rate, vol, maturity, is_call, num_sims, kappa, sigma, rho)
    delta = (price_up - price_down) / (2 * h)
    
    gamma = (price_up - 2 * price + price_down) / (h ** 2)
    
    h_vol = 0.01
    price_vol_up = heston_price(spot, strike, rate, vol + h_vol, maturity, is_call, num_sims, kappa, sigma, rho)
    vega = (price_vol_up - price) / h_vol
    
    h_time = 1 / 365
    if maturity > h_time:
        price_time = heston_price(spot, strike, rate, vol, maturity - h_time, is_call, num_sims, kappa, sigma, rho)
        theta = (price_time - price) / h_time
    else:
        theta = 0
    
    h_rate = 0.01
    price_rate_up = heston_price(spot, strike, rate + h_rate, vol, maturity, is_call, num_sims, kappa, sigma, rho)
    rho_greek = (price_rate_up - price) / h_rate
    
    return {
        "price": price,
        "delta": delta,
        "gamma": gamma,
        "theta": theta,
        "vega": vega,
        "rho": rho_greek
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/price", response_model=OptionResponse)
async def price_option(req: OptionRequest):
    try:
        is_call = req.option_type == "call"
        
        if req.model == "black-scholes":
            if req.is_american:
                raise HTTPException(400, "Black-Scholes only supports European options. Use Binomial for American.")
            
            greeks = black_scholes_greeks(
                req.spot, req.strike, req.rate, req.vol, req.maturity_years, is_call
            )
            greeks["model"] = "Black-Scholes"
            
        elif req.model == "binomial":
            greeks = binomial_greeks(
                req.spot, req.strike, req.rate, req.vol, req.maturity_years,
                is_call, req.is_american, req.steps
            )
            option_style = "American" if req.is_american else "European"
            greeks["model"] = f"Binomial ({option_style}, {req.steps} steps)"
            
        elif req.model == "heston":
            if req.is_american:
                raise HTTPException(400, "Heston model only supports European options. Use Binomial for American.")
            
            greeks = heston_greeks(
                req.spot, req.strike, req.rate, req.vol, req.maturity_years,
                is_call, req.num_simulations, req.mean_reversion, req.vol_of_vol, req.correlation
            )
            greeks["model"] = f"Heston ({req.num_simulations} simulations)"
            
        else:
            raise HTTPException(400, f"Unknown model: {req.model}")
        
        return OptionResponse(**greeks)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Pricing failed: {str(e)}")


@app.post("/payoff")
async def get_payoff_diagram(req: OptionRequest):
    try:
        is_call = req.option_type == "call"
        spot_range = np.linspace(req.spot * 0.5, req.spot * 1.5, 100)
        
        prices = []
        payoffs = []
        
        for S in spot_range:
            if req.model == "black-scholes":
                price = black_scholes_price(S, req.strike, req.rate, req.vol, req.maturity_years, is_call)
            elif req.model == "binomial":
                price = binomial_price(S, req.strike, req.rate, req.vol, req.maturity_years,
                                      is_call, req.is_american, req.steps)
            else:
                price = heston_price(S, req.strike, req.rate, req.vol, req.maturity_years,
                                    is_call, req.num_simulations, req.mean_reversion,
                                    req.vol_of_vol, req.correlation)
            
            prices.append(float(price))
            
            if is_call:
                payoff = max(S - req.strike, 0)
            else:
                payoff = max(req.strike - S, 0)
            payoffs.append(float(payoff))
        
        return {
            "spot_range": spot_range.tolist(),
            "option_prices": prices,
            "payoffs": payoffs,
            "strike": req.strike
        }
        
    except Exception as e:
        raise HTTPException(500, f"Payoff calculation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
