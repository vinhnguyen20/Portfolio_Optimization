"""
Fetch historical price data from Binance public API and generate
dataset files compatible with the portfolio optimization project.

No API key required - uses public endpoints only.

Output format (same as assets1.txt, assets2.txt, ...):
    N
    ExpReturn1 StDev1
    ExpReturn2 StDev2
    ...
    1 2 Correlation(1,2)
    1 3 Correlation(1,3)
    ...

Usage:
    python fetch_binance_data.py
    python fetch_binance_data.py --symbols BTC ETH BNB SOL --interval 1d --lookback 365
"""

import requests
import numpy as np
import pandas as pd
import argparse
import time
import os
from itertools import combinations


BINANCE_API = "https://api.binance.com/api/v3/klines"

# Default: top 20 crypto pairs against USDT
DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT", "LINKUSDT",
    "LTCUSDT", "UNIUSDT", "ATOMUSDT", "ETCUSDT", "XLMUSDT",
    "ALGOUSDT", "VETUSDT", "FILUSDT", "AAVEUSDT", "NEARUSDT",
]


def fetch_klines(symbol: str, interval: str = "1d", limit: int = 365) -> pd.Series | None:
    """Fetch closing prices for a symbol from Binance."""
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    try:
        resp = requests.get(BINANCE_API, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            print(f"  [WARN] No data for {symbol}")
            return None
        # Column 4 is close price
        closes = pd.Series(
            [float(row[4]) for row in data],
            name=symbol
        )
        return closes
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {symbol}: {e}")
        return None


def compute_stats(prices_df: pd.DataFrame):
    """
    Compute daily log returns, then:
      - expected return  = mean of daily returns  (annualized x 252)
      - std dev          = std  of daily returns  (annualized x sqrt(252))
      - correlation matrix between all assets
    """
    returns = np.log(prices_df / prices_df.shift(1)).dropna()

    # Annualize
    mu = returns.mean() * 252
    sigma = returns.std() * np.sqrt(252)
    corr = returns.corr()

    return mu, sigma, corr


def write_dataset(symbols: list[str], mu: pd.Series, sigma: pd.Series,
                  corr: pd.DataFrame, output_path: str):
    """Write dataset in the format expected by portfolio_opt.py."""
    N = len(symbols)
    lines = []

    # Line 1: number of assets
    lines.append(f" {N}")

    # Lines 2..N+1: ExpReturn StDev
    for sym in symbols:
        exp_ret = mu[sym]
        std_dev = sigma[sym]
        lines.append(f" {exp_ret:.6f} {std_dev:.6f}")

    # Diagonal (correlation of each asset with itself = 1.0)
    for i in range(N):
        lines.append(f" {i+1} {i+1} 1.000000")

    # Correlation pairs (upper triangle, 1-indexed)
    for i, j in combinations(range(N), 2):
        corr_val = corr.loc[symbols[i], symbols[j]]
        lines.append(f" {i+1} {j+1} {corr_val:.6f}")

    with open(output_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"  Saved -> {output_path}  ({N} assets)")


def main():
    parser = argparse.ArgumentParser(description="Fetch Binance data for portfolio optimization")
    parser.add_argument("--symbols", nargs="+", default=None,
                        help="List of Binance symbols e.g. BTCUSDT ETHUSDT (default: top 20)")
    parser.add_argument("--interval", default="1d",
                        choices=["1d", "1w", "4h", "1h"],
                        help="Kline interval (default: 1d)")
    parser.add_argument("--lookback", type=int, default=365,
                        help="Number of candles to fetch (default: 365 for daily = 1 year)")
    parser.add_argument("--output", default="datasets/binance_assets.txt",
                        help="Output file path (default: datasets/binance_assets.txt)")
    parser.add_argument("--min-history", type=float, default=0.9,
                        help="Min fraction of candles required to keep a symbol (default: 0.9)")
    args = parser.parse_args()

    symbols = args.symbols if args.symbols else DEFAULT_SYMBOLS

    print(f"Fetching {args.interval} data for {len(symbols)} symbols "
          f"(lookback={args.lookback} candles)...\n")

    # Fetch price series for all symbols
    price_series = {}
    for sym in symbols:
        print(f"  Fetching {sym}...")
        s = fetch_klines(sym, args.interval, args.lookback)
        if s is not None:
            price_series[sym] = s
        time.sleep(0.15)  # be polite to the API

    if not price_series:
        print("No data fetched. Exiting.")
        return

    # Align on common index and drop symbols with too many missing values
    prices_df = pd.DataFrame(price_series)
    min_rows = int(args.lookback * args.min_history)
    valid_cols = prices_df.columns[prices_df.count() >= min_rows].tolist()

    if len(valid_cols) < 2:
        print(f"Not enough valid symbols (need >= 2, got {len(valid_cols)}). Exiting.")
        return

    dropped = set(price_series.keys()) - set(valid_cols)
    if dropped:
        print(f"\n  Dropped (insufficient history): {', '.join(dropped)}")

    prices_df = prices_df[valid_cols].dropna()
    symbols_final = valid_cols

    print(f"\nComputing stats for {len(symbols_final)} symbols "
          f"over {len(prices_df)} candles...")

    mu, sigma, corr = compute_stats(prices_df)

    # Print summary
    print("\n--- Asset Summary ---")
    summary = pd.DataFrame({"Symbol": symbols_final,
                             "AnnReturn": mu[symbols_final].values,
                             "AnnStdDev": sigma[symbols_final].values})
    print(summary.to_string(index=False))

    # Write output
    os.makedirs(os.path.dirname(args.output) if os.path.dirname(args.output) else ".", exist_ok=True)
    write_dataset(symbols_final, mu, sigma, corr, args.output)

    print("\nDone! You can now use this dataset in portfolio_opt.py:")
    print(f"  ls_files = ['{args.output}']")


if __name__ == "__main__":
    main()
