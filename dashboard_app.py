import os
import pandas as pd
import plotly.express as px
import streamlit as st

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN = os.path.join(BASE_DIR, "data", "clean")
WEIGHTS_PATH = os.path.join(BASE_DIR, "data", "weights.csv")

# -------------------------
# Streamlit Config
# -------------------------
st.set_page_config(page_title="Financial Dashboard", layout="wide")
st.title("Financial Data Analytics Dashboard")

# -------------------------
# Load Data
# -------------------------
port_path = os.path.join(CLEAN, "portfolio_timeseries.csv")
bench_path = os.path.join(CLEAN, "benchmark_timeseries.csv")

if not (os.path.exists(port_path) and os.path.exists(bench_path)):
    st.error("Missing data files. Run `prepare_data.py` and `compute_kpis.py` first.")
    st.stop()

df_port = pd.read_csv(port_path, parse_dates=["Date"])
df_bench = pd.read_csv(bench_path, parse_dates=["Date"])

# -------------------------
# Date Range Filter
# -------------------------
min_date = max(df_port["Date"].min(), df_bench["Date"].min())
max_date = min(df_port["Date"].max(), df_bench["Date"].max())
date_range = st.slider(
    "Select Date Range",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime())
)

mask_port = (df_port["Date"] >= date_range[0]) & (df_port["Date"] <= date_range[1])
mask_bench = (df_bench["Date"] >= date_range[0]) & (df_bench["Date"] <= date_range[1])

# -------------------------
# KPI Cards
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Cumulative Return",
              f"{(df_port.loc[mask_port, 'portfolio_cum'].iloc[-1]-1)*100:.2f}%")

with col2:
    st.metric("Volatility (30d, Annualised)",
              f"{df_port.loc[mask_port, 'portfolio_vol_30d'].iloc[-1]*100:.2f}%")

with col3:
    st.metric("Max Drawdown",
              f"{df_port.loc[mask_port, 'portfolio_drawdown'].min()*100:.2f}%")

# -------------------------
# Charts
# -------------------------
# Performance vs Benchmark
perf = pd.DataFrame({
    "Date": df_port.loc[mask_port, "Date"],
    "Portfolio": df_port.loc[mask_port, "portfolio_cum"],
}).merge(pd.DataFrame({"Date": df_bench.loc[mask_bench, "Date"],"Benchmark": df_bench.loc[mask_bench, "benchmark_cum"]}),on="Date",how="inner")

st.subheader("Cumulative Performance")
fig_perf = px.line(perf, x="Date", y=["Portfolio", "Benchmark"], labels={"value": "Cumulative Return"})
st.plotly_chart(fig_perf, use_container_width=True)

# Drawdown
st.subheader("Portfolio Drawdown")
fig_dd = px.area(df_port.loc[mask_port], x="Date", y="portfolio_drawdown",
                 labels={"portfolio_drawdown": "Drawdown"})
st.plotly_chart(fig_dd, use_container_width=True)

# Rolling Volatility
st.subheader("Portfolio Rolling Volatility (30d, Annualised)")
fig_vol = px.line(df_port.loc[mask_port], x="Date", y="portfolio_vol_30d",
                  labels={"portfolio_vol_30d": "Volatility"})
st.plotly_chart(fig_vol, use_container_width=True)


if os.path.exists(WEIGHTS_PATH):
    st.subheader("Portfolio Weights")
    weights_df = pd.read_csv(WEIGHTS_PATH)
    st.table(weights_df)

