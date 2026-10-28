import os
import pandas as pd
import yfinance as yf
from datetime import datetime

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "monthly_oil_rand.csv")
DEFAULT_BASELINE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "monthly_oil_rand_baseline.csv")
BENCHMARK_CUTOFF = "2026-09-01"


def load_monthly_data(
    filepath: str = None,
    cutoff_date: str = BENCHMARK_CUTOFF,
    compute_zar: bool = True
) -> pd.DataFrame:
    """
    Load monthly oil and rand price data.
    
    Parameters
    ----------
    filepath : str, optional
        Path to the CSV file. Defaults to data/monthly_oil_rand.csv or baseline fallback.
    cutoff_date : str, optional
        Last complete month to include (e.g. '2026-09-01'). If None, returns all rows.
    compute_zar : bool, default True
        Whether to calculate and attach 'oil_zar' (oil_usd * usd_zar).
        
    Returns
    -------
    pd.DataFrame
        Cleaned monthly dataframe with DatetimeIndex.
    """
    if filepath is None:
        if os.path.exists(DEFAULT_DATA_PATH):
            filepath = DEFAULT_DATA_PATH
        elif os.path.exists(DEFAULT_BASELINE_PATH):
            filepath = DEFAULT_BASELINE_PATH
        else:
            raise FileNotFoundError(f"Neither {DEFAULT_DATA_PATH} nor fallback baseline exists.")

    df = pd.read_csv(filepath, index_col=0, parse_dates=True)
    df.index.name = "Date"

    # Filter to cutoff if requested
    if cutoff_date is not None:
        df = df.loc[:cutoff_date].copy()
    else:
        df = df.copy()

    # Derived oil price in ZAR terms
    if compute_zar and "oil_zar" not in df.columns:
        df["oil_zar"] = df["oil_usd"] * df["usd_zar"]

    return df


def fetch_live_data(start_date: str = "2016-01-01", save_to: str = None) -> pd.DataFrame:
    """
    Download daily Brent crude ('BZ=F') and USD/ZAR ('ZAR=X') prices from Yahoo Finance,
    clean missing days with forward-fill, and aggregate to monthly averages.
    
    Parameters
    ----------
    start_date : str
        Start date in 'YYYY-MM-DD' format.
    save_to : str, optional
        If specified, persists the result to this CSV file path.
        
    Returns
    -------
    pd.DataFrame
        Monthly averaged dataframe.
    """
    data = yf.download(["BZ=F", "ZAR=X"], start=start_date, progress=False)
    if "Close" in data:
        close = data["Close"].copy()
    else:
        close = data.copy()

    close = close.rename(columns={"BZ=F": "oil_usd", "ZAR=X": "usd_zar"})

    # Forward fill holiday / market closure gaps, then drop initial unseeded days
    close = close.ffill().dropna()

    # Monthly average by month-start
    monthly = close.resample("MS").mean()
    monthly.index.name = "Date"

    if save_to:
        os.makedirs(os.path.dirname(os.path.abspath(save_to)), exist_ok=True)
        monthly.to_csv(save_to)

    return monthly
