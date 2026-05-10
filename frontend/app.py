import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from math import exp, log, sqrt, erf, pi

# Pricing functions
def norm_pdf(x: float) -> float:
    return (1.0 / sqrt(2.0 * pi)) * exp(-0.5 * x * x)

def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + erf(x / sqrt(2.0)))

def black_scholes_price(spot: float, strike: float, rate: float, vol: float, 
                       maturity: float, is_call: bool) -> float:
    d1 = (log(spot / strike) + (rate + 0.5 * vol ** 2) * maturity) / (vol * sqrt(maturity))
    d2 = d1 - vol * sqrt(maturity)
    
    if is_call:
        price = spot * norm_cdf(d1) - strike * exp(-rate * maturity) * norm_cdf(d2)
    else:
        price = strike * exp(-rate * maturity) * norm_cdf(-d2) - spot * norm_cdf(-d1)
    
    return price

def black_scholes_greeks(spot: float, strike: float, rate: float, vol: float,
                        maturity: float, is_call: bool) -> dict:
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
    
    vega = spot * norm_pdf(d1) * sqrt(maturity) / 100
    
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
    price_vol_down = binomial_price(spot, strike, rate, vol - h_vol, maturity, is_call, is_american, steps)
    vega = (price_vol_up - price_vol_down) / (2 * h_vol) / 100
    
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
    price_vol_down = heston_price(spot, strike, rate, vol - h_vol, maturity, is_call, num_sims, kappa, sigma, rho)
    vega = (price_vol_up - price_vol_down) / (2 * h_vol) / 100
    
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

def calculate_price_and_greeks(spot, strike, rate, vol, maturity, option_type, model, is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations):
    is_call = option_type == "call"
    
    if model == "black-scholes":
        if is_american:
            raise ValueError("Black-Scholes only supports European options. Use Binomial for American.")
        
        greeks = black_scholes_greeks(spot, strike, rate, vol, maturity, is_call)
        greeks["model"] = "Black-Scholes"
        
    elif model == "binomial":
        greeks = binomial_greeks(spot, strike, rate, vol, maturity, is_call, is_american, steps)
        option_style = "American" if is_american else "European"
        greeks["model"] = f"Binomial ({option_style}, {steps} steps)"
        
    elif model == "heston":
        if is_american:
            raise ValueError("Heston model only supports European options. Use Binomial for American.")
        
        greeks = heston_greeks(spot, strike, rate, vol, maturity, is_call, num_simulations, mean_reversion, vol_of_vol, correlation)
        greeks["model"] = f"Heston ({num_simulations} simulations)"
        
    else:
        raise ValueError(f"Unknown model: {model}")
    
    return greeks

def get_payoff_diagram(spot, strike, rate, vol, maturity, option_type, model, is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations):
    is_call = option_type == "call"
    spot_range = np.linspace(spot * 0.5, spot * 1.5, 100)
    
    prices = []
    payoffs = []
    
    for S in spot_range:
        if model == "black-scholes":
            price = black_scholes_price(S, strike, rate, vol, maturity, is_call)
        elif model == "binomial":
            price = binomial_price(S, strike, rate, vol, maturity, is_call, is_american, steps)
        else:
            price = heston_price(S, strike, rate, vol, maturity, is_call, num_simulations, mean_reversion, vol_of_vol, correlation)
        
        prices.append(float(price))
        
        if is_call:
            payoff = max(S - strike, 0)
        else:
            payoff = max(strike - S, 0)
        payoffs.append(float(payoff))
    
    return {
        "spot_range": spot_range.tolist(),
        "option_prices": prices,
        "payoffs": payoffs,
        "strike": strike
    }

st.set_page_config(
    page_title="Option Pricing Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    .stApp {
        background: #0e1117;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #f9fafb;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 14px;
        font-weight: 500;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #374151;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1f2937 0%, #111827 100%);
    }
    h1 {
        font-weight: 800;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5em;
        margin-bottom: 0;
    }
    h2 {
        color: #e5e7eb;
        font-weight: 600;
        margin-top: 2rem;
    }
    h3 {
        color: #d1d5db;
        font-weight: 600;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        font-size: 18px;
        padding: 0.75rem 1.5rem;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    div[data-baseweb="select"] {
        background-color: #1f2937;
    }
    .stNumberInput>div>div>input {
        background-color: #1f2937;
        color: #e5e7eb;
        border: 1px solid #374151;
        border-radius: 8px;
    }
    .stSelectbox>div>div {
        background-color: #1f2937;
        color: #e5e7eb;
        border-radius: 8px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border: 1px solid #374151;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

col1, col2 = st.columns([6, 1])
with col1:
    st.title("Option Pricing Platform")
with col2:
    st.markdown("### <span style='color: #10b981;'>●</span> Live", unsafe_allow_html=True)

st.markdown("---")

with st.sidebar:
    st.markdown("## Configuration")
    st.markdown("### Market Data")
    
    spot = st.number_input("Spot Price", value=100.0, min_value=0.01, step=1.0)
    strike = st.number_input("Strike Price", value=100.0, min_value=0.01, step=1.0)
    maturity = st.number_input("Time to Maturity (years)", value=1.0, min_value=0.01, max_value=10.0, step=0.1)
    rate = st.number_input("Risk-Free Rate (%)", value=5.0, min_value=-10.0, max_value=50.0, step=0.5) / 100
    vol = st.number_input("Volatility (%)", value=20.0, min_value=0.1, max_value=200.0, step=1.0) / 100
    
    option_type = st.selectbox("Option Type", ["call", "put"])
    
    st.markdown("---")
    st.markdown("### Pricing Model")
    
    model = st.selectbox("Model", ["black-scholes", "binomial", "heston"], 
                         format_func=lambda x: {"black-scholes": "Black-Scholes", 
                                               "binomial": "Binomial Tree", 
                                               "heston": "Heston Model"}[x])
    
    is_american = False
    steps = 100
    mean_reversion = 2.0
    vol_of_vol = 0.5
    correlation = -0.5
    num_simulations = 10000
    
    if model == "binomial":
        st.markdown("### Tree Parameters")
        is_american = st.checkbox("American Option")
        steps = st.slider("Number of Steps", 10, 500, 100, 10)
        
    elif model == "heston":
        st.markdown("### Heston Parameters")
        mean_reversion = st.number_input("Mean Reversion (κ)", value=2.0, min_value=0.1, max_value=10.0, step=0.1)
        vol_of_vol = st.number_input("Vol of Vol (σ)", value=0.5, min_value=0.1, max_value=2.0, step=0.1)
        correlation = st.slider("Correlation (ρ)", -1.0, 1.0, -0.5, 0.1)
        num_simulations = st.slider("Simulations", 1000, 50000, 10000, 1000)
    
    st.markdown("---")
    calculate_btn = st.button("Calculate Price", type="primary")

if calculate_btn:
    try:
        with st.spinner("Computing..."):
            result = calculate_price_and_greeks(
                spot, strike, rate, vol, maturity, option_type, model,
                is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations
            )
            st.session_state["result"] = result
            
            payoff = get_payoff_diagram(
                spot, strike, rate, vol, maturity, option_type, model,
                is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations
            )
            st.session_state["payoff"] = payoff
    except Exception as e:
        st.error(f"Error: {str(e)}")

if "result" in st.session_state:
    result = st.session_state["result"]
    
    st.markdown("## Pricing Results")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Option Price", f"${result['price']:.4f}")
    
    with col2:
        moneyness = (spot - strike) / strike * 100
        st.metric("Moneyness", f"{moneyness:+.2f}%")
    
    with col3:
        intrinsic = max((spot - strike) if option_type == "call" else (strike - spot), 0)
        st.metric("Intrinsic Value", f"${intrinsic:.4f}")
    
    with col4:
        time_value = result['price'] - intrinsic
        st.metric("Time Value", f"${time_value:.4f}")
    
    st.markdown("## The Greeks")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    greeks_data = [
        ("Delta (Δ)", result['delta'], col1),
        ("Gamma (Γ)", result['gamma'], col2),
        ("Theta (Θ)", result['theta'], col3),
        ("Vega (ν)", result['vega'], col4),
        ("Rho (ρ)", result['rho'], col5)
    ]
    
    for name, value, col in greeks_data:
        with col:
            st.metric(name, f"{value:.4f}")
    
    if "payoff" in st.session_state:
        payoff_data = st.session_state["payoff"]
        
        st.markdown("## Price Analysis")
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=("Option Value vs Underlying Price", "Value Decomposition"),
            vertical_spacing=0.18,
            row_heights=[0.58, 0.42]
        )
        
        fig.add_trace(
            go.Scatter(
                x=payoff_data["spot_range"],
                y=payoff_data["option_prices"],
                name="Option Price",
                line=dict(color="#667eea", width=3),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.1)'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=payoff_data["spot_range"],
                y=payoff_data["payoffs"],
                name="Payoff at Expiry",
                line=dict(color="#f59e0b", width=2, dash="dash")
            ),
            row=1, col=1
        )
        
        fig.add_vline(
            x=payoff_data["strike"],
            line_dash="dot",
            line_color="#6b7280",
            row=1, col=1
        )
        
        fig.add_vline(
            x=spot,
            line_dash="dot",
            line_color="#10b981",
            row=1, col=1
        )
        
        intrinsic_values = []
        time_values = []
        for i, S in enumerate(payoff_data["spot_range"]):
            if option_type == "call":
                intrinsic = max(S - strike, 0)
            else:
                intrinsic = max(strike - S, 0)
            intrinsic_values.append(intrinsic)
            time_values.append(payoff_data["option_prices"][i] - intrinsic)
        
        fig.add_trace(
            go.Scatter(
                x=payoff_data["spot_range"],
                y=intrinsic_values,
                name="Intrinsic Value",
                fill='tozeroy',
                line=dict(color="#10b981", width=2),
                fillcolor='rgba(16, 185, 129, 0.3)'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=payoff_data["spot_range"],
                y=time_values,
                name="Time Value",
                fill='tozeroy',
                line=dict(color="#8b5cf6", width=2),
                fillcolor='rgba(139, 92, 246, 0.3)'
            ),
            row=2, col=1
        )
        
        fig.update_xaxes(title_text="Underlying Price ($)", row=1, col=1, gridcolor='#374151')
        fig.update_xaxes(title_text="Underlying Price ($)", row=2, col=1, gridcolor='#374151')
        fig.update_yaxes(title_text="Option Value ($)", row=1, col=1, gridcolor='#374151')
        fig.update_yaxes(title_text="Value ($)", row=2, col=1, gridcolor='#374151')
        
        fig.update_layout(
            height=980,
            showlegend=True,
            hovermode="x unified",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(31, 41, 55, 0.5)',
            font=dict(family="Inter, sans-serif", size=12, color="#e5e7eb"),
            margin=dict(t=110, b=50, l=40, r=40),
            legend=dict(
                bgcolor="rgba(31, 41, 55, 0.8)",
                bordercolor="#374151",
                borderwidth=1
            )
        )

        fig.update_annotations(yshift=24, yanchor="bottom", font=dict(size=13, color="#e5e7eb"))
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("## Greeks Sensitivity")
        
        tab1, tab2, tab3 = st.tabs(["Delta Profile", "Gamma Profile", "Time Value vs Maturity"])
        
        with tab1:
            spot_range_greek = np.linspace(spot * 0.7, spot * 1.3, 50)
            delta_values = []
            
            for S in spot_range_greek:
                try:
                    temp_result = calculate_price_and_greeks(
                        S, strike, rate, vol, maturity, option_type, model,
                        is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations
                    )
                    delta_values.append(temp_result["delta"])
                except:
                    delta_values.append(None)
            
            fig_delta = go.Figure()
            fig_delta.add_trace(go.Scatter(
                x=spot_range_greek,
                y=delta_values,
                line=dict(color="#667eea", width=3),
                fill='tozeroy',
                fillcolor='rgba(102, 126, 234, 0.2)'
            ))
            
            fig_delta.add_vline(x=spot, line_dash="dash", line_color="#10b981", 
                               annotation_text="Current Spot")
            fig_delta.add_vline(x=strike, line_dash="dot", line_color="#6b7280", 
                               annotation_text="Strike")
            
            fig_delta.update_layout(
                title="Delta vs Underlying Price",
                xaxis_title="Spot Price ($)",
                yaxis_title="Delta",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(31, 41, 55, 0.5)',
                height=500
            )
            
            st.plotly_chart(fig_delta, use_container_width=True)
        
        with tab2:
            gamma_values = []
            
            for S in spot_range_greek:
                try:
                    temp_result = calculate_price_and_greeks(
                        S, strike, rate, vol, maturity, option_type, model,
                        is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations
                    )
                    gamma_values.append(temp_result["gamma"])
                except:
                    gamma_values.append(None)
            
            fig_gamma = go.Figure()
            fig_gamma.add_trace(go.Scatter(
                x=spot_range_greek,
                y=gamma_values,
                line=dict(color="#f59e0b", width=3),
                fill='tozeroy',
                fillcolor='rgba(245, 158, 11, 0.2)'
            ))
            
            fig_gamma.add_vline(x=spot, line_dash="dash", line_color="#10b981", 
                               annotation_text="Current Spot")
            fig_gamma.add_vline(x=strike, line_dash="dot", line_color="#6b7280", 
                               annotation_text="Strike")
            
            fig_gamma.update_layout(
                title="Gamma vs Underlying Price",
                xaxis_title="Spot Price ($)",
                yaxis_title="Gamma",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(31, 41, 55, 0.5)',
                height=500
            )
            
            st.plotly_chart(fig_gamma, use_container_width=True)
        
        with tab3:
            time_range = np.linspace(0.01, maturity, 20)
            theta_prices = []
            
            for t in time_range:
                try:
                    temp_result = calculate_price_and_greeks(
                        spot, strike, rate, vol, t, option_type, model,
                        is_american, steps, mean_reversion, vol_of_vol, correlation, num_simulations
                    )
                    theta_prices.append(temp_result["price"])
                except:
                    theta_prices.append(None)
                
            fig_theta = go.Figure()
            fig_theta.add_trace(go.Scatter(
                x=time_range,
                y=theta_prices,
                line=dict(color="#ef4444", width=3),
                fill='tozeroy',
                fillcolor='rgba(239, 68, 68, 0.2)'
            ))
            
            fig_theta.add_vline(x=maturity, line_dash="dash", line_color="#10b981", 
                               annotation_text="Current Maturity")
            
            fig_theta.update_layout(
                title="Option Price vs Time to Maturity",
                xaxis_title="Time to Maturity (years)",
                yaxis_title="Option Price ($)",
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(31, 41, 55, 0.5)',
                height=500
            )
            
            st.plotly_chart(fig_theta, use_container_width=True)

else:
    st.markdown("""
    <div style='text-align: center; padding: 4rem 2rem;'>
        <h2 style='color: #9ca3af; font-weight: 400;'>Configure parameters and calculate to see results</h2>
        <p style='color: #6b7280; font-size: 1.1rem; margin-top: 1rem;'>
            Supports Black-Scholes, Binomial Tree, and Heston stochastic volatility models
        </p>
    </div>
    """, unsafe_allow_html=True)

