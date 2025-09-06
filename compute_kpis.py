import os
import numpy as np
import pandas as pd

# ---- Paths (no "..") ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
WEIGHTS_PATH = os.path.join(BASE_DIR, "data", "weights.csv")

ROLLING_WINDOW = 30  # trading days window (~1.5 months)

def max_drawdown(cum_curve: pd.Series) -> pd.Series:
    """Compute drawdown series from a cumulative return curve that starts ~1.0."""
    running_peak = cum_curve.cummax()
    return (cum_curve - running_peak) / running_peak

def main():
    prices = pd.read_csv(os.path.join(CLEAN_DIR, "portfolio_prices.csv"), parse_dates=["Date"])
    weights = pd.read_csv(WEIGHTS_PATH)

    # Map weights to tickers present
    weights_map = dict(zip(weights["ticker"], weights["weight"]))

    # Identify tickers (exclude Date and benchmark column)
    cols = [c for c in prices.columns if c != "Date"]
    benchmark_col = "SP500"
    if benchmark_col not in cols:
        raise ValueError(f"Benchmark column '{benchmark_col}' not found in portfolio_prices.csv. Found: {cols}")
    tickers = [c for c in cols if c != benchmark_col]

    # Daily returns per asset (including benchmark)
    asset_returns = prices.copy()
    for t in tickers + [benchmark_col]:
        asset_returns[t] = prices[t].pct_change()
    asset_returns.to_csv(os.path.join(CLEAN_DIR, "asset_returns.csv"), index=False)

    # Portfolio daily return using weights (auto-normalise in case they don't sum to 1)
    present_weights = np.array([weights_map[t] for t in tickers])
    present_weights = present_weights / present_weights.sum()
    port_ret = (asset_returns[tickers] * present_weights).sum(axis=1)

    df_port = pd.DataFrame({
        "Date": prices["Date"],
        "portfolio_return": port_ret
    }).dropna()  # first row will be NaN due to pct_change

    # Cumulative return curve starting at 1.0
    df_port["portfolio_cum"] = (1 + df_port["portfolio_return"]).cumprod()

    # Rolling volatility (annualised)
    df_port["portfolio_vol_30d"] = (
        df_port["portfolio_return"].rolling(ROLLING_WINDOW).std() * np.sqrt(252)
    )

    # Max drawdown from the cumulative curve
    df_port["portfolio_drawdown"] = max_drawdown(df_port["portfolio_cum"])

    # Benchmark KPIs
    df_bench = pd.DataFrame({
        "Date": prices["Date"],
        "benchmark_return": asset_returns[benchmark_col]
    }).dropna()
    df_bench["benchmark_cum"] = (1 + df_bench["benchmark_return"]).cumprod()
    df_bench["benchmark_vol_30d"] = (
        df_bench["benchmark_return"].rolling(ROLLING_WINDOW).std() * np.sqrt(252)
    )
    df_bench["benchmark_drawdown"] = max_drawdown(df_bench["benchmark_cum"])

    # Save outputs
    df_port.to_csv(os.path.join(CLEAN_DIR, "portfolio_timeseries.csv"), index=False)
    df_bench.to_csv(os.path.join(CLEAN_DIR, "benchmark_timeseries.csv"), index=False)

    print("Saved KPIs to:")
    print(" - data/clean/asset_returns.csv")
    print(" - data/clean/portfolio_timeseries.csv")
    print(" - data/clean/benchmark_timeseries.csv")

if __name__ == "__main__":
    main()
