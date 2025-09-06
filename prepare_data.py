
import os, pandas as pd
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
CLEAN_DIR = os.path.join(BASE_DIR, "data", "clean")
TICKERS = ["TSLA","AAPL","MSFT","NVDA","AMZN"]
BENCHMARK = "SP500"
def load_single_csv(path, name):
    import pandas as pd
    import os, re

    df = pd.read_csv(path)

    # Normalise column names (strip spaces/case)
    cols = {c.lower().strip(): c for c in df.columns}

    # Try common close-price names across sources
    # Yahoo: "Adj Close" or "Close"
    # Nasdaq: "Close/Last"
    # Investing.com: sometimes "Price"
    close_candidates = [
        cols.get("adj close"),
        cols.get("close"),
        cols.get("close/last"),
        cols.get("price"),
        cols.get("last"),
    ]
    close_col = next((c for c in close_candidates if c in df.columns), None)
    if close_col is None:
        raise ValueError(
            f"Couldn't find a close price column in {os.path.basename(path)}. "
            f"Expected one of: 'Adj Close', 'Close', 'Close/Last', 'Price', 'Last'. "
            f"Found: {list(df.columns)}"
        )

    # Find date column (Nasdaq uses "Date", sometimes lower/other cases)
    date_col = cols.get("date")
    if date_col is None:
        raise ValueError(f"No 'Date' column found in {os.path.basename(path)}. Columns: {list(df.columns)}")

    # Keep only Date + Close
    df = df[[date_col, close_col]].copy()
    df.columns = ["Date", "Close"]

    # Clean values like "$232.33" or "2,345.10"
    if df["Close"].dtype == object:
        df["Close"] = (
            df["Close"]
            .astype(str)
            .str.replace(r"[\$,]", "", regex=True)  # remove $ and commas
            .str.strip()
        )

    # Convert types
    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date

    # Drop rows we couldn't parse
    df = df.dropna(subset=["Date", "Close"]).copy()

    # Add ticker
    df["Ticker"] = name
    return df

def main():
    frames=[]
    for t in TICKERS+[BENCHMARK]:
        p=os.path.join(RAW_DIR,f"{t}.csv")
        if not os.path.exists(p): raise FileNotFoundError(p)
        frames.append(load_single_csv(p,t))
    long_df = pd.concat(frames, ignore_index=True).sort_values(["Date","Ticker"])
    os.makedirs(CLEAN_DIR, exist_ok=True)
    long_df.to_csv(os.path.join(CLEAN_DIR,"prices_long.csv"),index=False)
    wide = long_df.pivot(index="Date", columns="Ticker", values="Close").reset_index()
    wide.to_csv(os.path.join(CLEAN_DIR,"portfolio_prices.csv"), index=False)
    print("Saved clean data.")
if __name__=="__main__": main()
