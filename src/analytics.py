import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, Any, Tuple, Optional


def compute_monthly_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate month-over-month percentage changes.
    
    Parameters
    ----------
    df : pd.DataFrame
        Monthly price dataframe containing oil_usd and usd_zar.
        
    Returns
    -------
    pd.DataFrame
        Dataframe of percentage changes (oil_change_pct, rand_change_pct, oil_zar_change_pct).
    """
    cols_to_change = ["oil_usd", "usd_zar"]
    if "oil_zar" in df.columns:
        cols_to_change.append("oil_zar")

    changes = df[cols_to_change].pct_change().dropna() * 100
    rename_dict = {
        "oil_usd": "oil_change_pct",
        "usd_zar": "rand_change_pct",
        "oil_zar": "oil_zar_change_pct"
    }
    return changes.rename(columns=rename_dict)


def compute_correlation_stats(series_x: pd.Series, series_y: pd.Series) -> Dict[str, Any]:
    """
    Compute Pearson and Spearman correlation statistics including p-values.
    
    Parameters
    ----------
    series_x : pd.Series
    series_y : pd.Series
    
    Returns
    -------
    dict
        Dictionary with pearson_r, pearson_p, spearman_rho, spearman_p, and n_obs.
    """
    valid = pd.concat([series_x, series_y], axis=1).dropna()
    x = valid.iloc[:, 0]
    y = valid.iloc[:, 1]
    n = len(valid)

    if n < 3:
        return {
            "pearson_r": np.nan,
            "pearson_p": np.nan,
            "spearman_rho": np.nan,
            "spearman_p": np.nan,
            "n_obs": n
        }

    p_r, p_val = stats.pearsonr(x, y)
    s_rho, s_val = stats.spearmanr(x, y)

    return {
        "pearson_r": float(p_r),
        "pearson_p": float(p_val),
        "spearman_rho": float(s_rho),
        "spearman_p": float(s_val),
        "n_obs": int(n)
    }


def compute_rolling_correlation(
    series_x: pd.Series,
    series_y: pd.Series,
    window: int = 24
) -> pd.Series:
    """
    Compute rolling Pearson correlation between two series.
    """
    return series_x.rolling(window=window).corr(series_y)


def filter_changes_dynamically(
    changes_df: pd.DataFrame,
    exclude_all_2020: bool = False,
    exclude_covid_crash_months: bool = False,
    exclude_march_2026: bool = False,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Filter monthly percentage changes dataframe based on user criteria.
    """
    filtered = changes_df.copy()

    if start_date:
        filtered = filtered[filtered.index >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered.index <= pd.to_datetime(end_date)]

    if exclude_all_2020:
        filtered = filtered[filtered.index.year != 2020]
    elif exclude_covid_crash_months:
        crash_dates = [pd.to_datetime("2020-03-01"), pd.to_datetime("2020-04-01")]
        filtered = filtered.drop([d for d in crash_dates if d in filtered.index], errors="ignore")

    if exclude_march_2026:
        m26 = pd.to_datetime("2026-03-01")
        if m26 in filtered.index:
            filtered = filtered.drop(m26, errors="ignore")

    return filtered


def run_sensitivity_scenarios(changes_df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the standardized sensitivity scenarios documented in the analysis.
    
    Returns
    -------
    pd.DataFrame
        Scenario comparison table.
    """
    scenarios = {
        "1. Full Period (All Months)": changes_df,
        "2. Exclude Full Year 2020": changes_df[changes_df.index.year != 2020],
        "3. Exclude March & April 2020": changes_df.drop(
            [d for d in [pd.to_datetime("2020-03-01"), pd.to_datetime("2020-04-01")] if d in changes_df.index],
            errors="ignore"
        ),
        "4. Post-COVID Era Only (2021+)": changes_df[changes_df.index >= "2021-01-01"],
        "5. Pre-COVID Era (2016-2019)": changes_df[changes_df.index < "2020-01-01"],
    }

    m26 = pd.to_datetime("2026-03-01")
    if m26 in changes_df.index:
        scenarios["6. Exclude March 2026 Shock"] = changes_df.drop(m26, errors="ignore")

    rows = []
    for name, subset in scenarios.items():
        st = compute_correlation_stats(subset["oil_change_pct"], subset["rand_change_pct"])
        rows.append({
            "Scenario": name,
            "Months (N)": st["n_obs"],
            "Pearson r": round(st["pearson_r"], 4),
            "p-value": f"{st['pearson_p']:.4f}" if st['pearson_p'] >= 0.0001 else "<0.0001",
            "Statistically Significant (p<0.05)": "Yes" if st["pearson_p"] < 0.05 else "No",
            "Spearman rho": round(st["spearman_rho"], 4),
        })

    return pd.DataFrame(rows)


def compute_summary_metrics(monthly_df: pd.DataFrame, changes_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute key historical extremes, volatility metrics, and baseline statistics.
    """
    metrics = {
        # Levels
        "highest_oil_usd": (monthly_df["oil_usd"].max(), monthly_df["oil_usd"].idxmax()),
        "lowest_oil_usd": (monthly_df["oil_usd"].min(), monthly_df["oil_usd"].idxmin()),
        "weakest_rand": (monthly_df["usd_zar"].max(), monthly_df["usd_zar"].idxmax()),
        "strongest_rand": (monthly_df["usd_zar"].min(), monthly_df["usd_zar"].idxmin()),
        "highest_oil_zar": (monthly_df["oil_zar"].max(), monthly_df["oil_zar"].idxmax()),
        "lowest_oil_zar": (monthly_df["oil_zar"].min(), monthly_df["oil_zar"].idxmin()),
        # Changes
        "oil_volatility_std": changes_df["oil_change_pct"].std(),
        "rand_volatility_std": changes_df["rand_change_pct"].std(),
        "oil_zar_volatility_std": changes_df["oil_zar_change_pct"].std() if "oil_zar_change_pct" in changes_df else np.nan,
        "biggest_oil_fall": (changes_df["oil_change_pct"].min(), changes_df["oil_change_pct"].idxmin()),
        "biggest_oil_rise": (changes_df["oil_change_pct"].max(), changes_df["oil_change_pct"].idxmax()),
        "biggest_rand_depreciation": (changes_df["rand_change_pct"].max(), changes_df["rand_change_pct"].idxmax()),
        "biggest_rand_appreciation": (changes_df["rand_change_pct"].min(), changes_df["rand_change_pct"].idxmin()),
        # Correlation
        "level_correlation": monthly_df[["oil_usd", "usd_zar"]].corr().iloc[0, 1],
        "changes_correlation": changes_df[["oil_change_pct", "rand_change_pct"]].corr().iloc[0, 1]
    }
    return metrics


def simulate_fuel_cost(
    base_oil_usd: float,
    base_usd_zar: float,
    sim_oil_usd: float,
    sim_usd_zar: float,
    litres_per_barrel: float = 158.987
) -> Dict[str, float]:
    """
    Simulate the combined oil price in Rand and estimated crude cost per litre.
    
    Parameters
    ----------
    base_oil_usd : float
        Benchmark Brent price ($/bbl).
    base_usd_zar : float
        Benchmark USD/ZAR rate.
    sim_oil_usd : float
        Simulated Brent price ($/bbl).
    sim_usd_zar : float
        Simulated USD/ZAR rate.
    litres_per_barrel : float, default 158.987
        Standard conversion factor (1 barrel of crude oil ≈ 159 litres).
        
    Returns
    -------
    dict
        Simulated metrics and deltas.
    """
    base_zar_bbl = base_oil_usd * base_usd_zar
    sim_zar_bbl = sim_oil_usd * sim_usd_zar
    diff_zar_bbl = sim_zar_bbl - base_zar_bbl
    pct_change = (diff_zar_bbl / base_zar_bbl) * 100

    base_cpl = base_zar_bbl / litres_per_barrel
    sim_cpl = sim_zar_bbl / litres_per_barrel
    diff_cpl = sim_cpl - base_cpl

    return {
        "base_zar_bbl": base_zar_bbl,
        "sim_zar_bbl": sim_zar_bbl,
        "diff_zar_bbl": diff_zar_bbl,
        "pct_change": pct_change,
        "base_cpl": base_cpl,
        "sim_cpl": sim_cpl,
        "diff_cpl": diff_cpl
    }
