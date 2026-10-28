import os
import streamlit as st
import pandas as pd
import numpy as np

from src.data_loader import load_monthly_data, fetch_live_data, BENCHMARK_CUTOFF
from src.analytics import (
    compute_monthly_changes,
    compute_correlation_stats,
    compute_rolling_correlation,
    filter_changes_dynamically,
    run_sensitivity_scenarios,
    compute_summary_metrics,
    simulate_fuel_cost
)
from src.visualisations import (
    create_dual_axis_chart,
    create_oil_zar_chart,
    create_changes_scatter_chart,
    create_rolling_corr_chart,
    create_volatility_comparison_chart
)

# -----------------------------------------------------------------------------
# Streamlit Page Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Fuel Drivers Analysis | South Africa",
    page_icon="⛽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for crisp, executive dashboard presentation
st.markdown("""
<style>
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-delta {
        font-size: 0.85rem;
        font-weight: 500;
    }
    .delta-pos { color: #dc2626; }  /* For fuel costs, price increases are red */
    .delta-neg { color: #16a34a; }  /* Price decreases are green */
    .delta-neutral { color: #475569; }
    .badge-alert {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #fee2e2;
        color: #991b1b;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Data Loading & Caching
# -----------------------------------------------------------------------------
@st.cache_data
def get_cached_data(use_live: bool = False, cutoff: str = BENCHMARK_CUTOFF):
    if use_live:
        try:
            return fetch_live_data()
        except Exception as e:
            st.error(f"Failed to fetch live data from Yahoo Finance: {e}. Falling back to baseline data.")
            return load_monthly_data(cutoff_date=cutoff)
    return load_monthly_data(cutoff_date=cutoff)


# -----------------------------------------------------------------------------
# Sidebar Controls & Global State
# -----------------------------------------------------------------------------
st.sidebar.markdown("## ⛽ Fuel Drivers Analysis")
st.sidebar.markdown(
    "How Brent crude oil and the USD/ZAR exchange rate co-move, and what it means for South African fuel costs."
)
st.sidebar.markdown("---")

# Navigation Menu
view_mode = st.sidebar.radio(
    "Navigate Dashboard:",
    [
        "📊 Executive Summary & KPIs",
        "📈 Macro Trends & Price Levels",
        "🔬 Correlation & Volatility Lab",
        "⚡ Shock Sensitivity Sandbox",
        "🧮 SA Fuel Price Simulator",
        "📋 Data Inspector & Export"
    ],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Data & Range Settings")

# Live fetch toggle
use_live_data = st.sidebar.checkbox(
    "Fetch Live Online Data (Yahoo Finance)",
    value=False,
    help="When unchecked, uses verified benchmark data (Jan 2016 - Sep 2026). When checked, fetches live updates from Yahoo Finance."
)

raw_df = get_cached_data(use_live=use_live_data, cutoff=None if use_live_data else BENCHMARK_CUTOFF)

# Date filtering
min_date = raw_df.index.min().to_pydatetime()
max_date = raw_df.index.max().to_pydatetime()

selected_range = st.sidebar.date_input(
    "Select Date Horizon:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
    help="Filter the analysis period across all charts and metrics."
)

if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
    start_filter, end_filter = selected_range
else:
    start_filter, end_filter = min_date, max_date

# Sliced DataFrame
df = raw_df.loc[start_filter:end_filter].copy()
if "oil_zar" not in df.columns:
    df["oil_zar"] = df["oil_usd"] * df["usd_zar"]

changes_df = compute_monthly_changes(df)
metrics = compute_summary_metrics(df, changes_df)

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**Dataset status**: {len(df)} months loaded ({df.index.min().strftime('%b %Y')} to {df.index.max().strftime('%b %Y')})."
)


# -----------------------------------------------------------------------------
# View 1: Executive Summary & KPIs
# -----------------------------------------------------------------------------
if view_mode == "📊 Executive Summary & KPIs":
    st.title("⛽ Fuel Drivers Analysis: South Africa")
    st.markdown(
        "### Oil Price vs. USD/ZAR Dynamics (2016 – 2026)\n"
        "South Africa is an oil-importing economy whose pump prices are heavily shaped by international crude and the exchange rate. "
        "This project analyzes ten years of monthly market data to determine **whether oil and the rand move together or offset each other**."
    )

    # Core Finding Banner
    st.info(
        "💡 **Key Analytical Finding:** "
        "While monthly price levels appear weakly positively correlated (**+0.30**), this is merely common long-term trend drift. "
        "On a month-to-month percentage change basis, **the correlation is essentially ZERO (-0.01 outside 2020)**. "
        "The rand does **not** buffer South Africa against international oil spikes—leaving fuel consumers fully exposed to independent swings in both drivers."
    )

    # KPI Row
    latest_month = df.index[-1]
    prev_month = df.index[-2] if len(df) > 1 else latest_month
    latest_oil = df.loc[latest_month, "oil_usd"]
    latest_rand = df.loc[latest_month, "usd_zar"]
    latest_zar_bbl = df.loc[latest_month, "oil_zar"]

    oil_mom = changes_df.loc[latest_month, "oil_change_pct"] if latest_month in changes_df.index else 0.0
    rand_mom = changes_df.loc[latest_month, "rand_change_pct"] if latest_month in changes_df.index else 0.0
    zar_mom = changes_df.loc[latest_month, "oil_zar_change_pct"] if latest_month in changes_df.index else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    with kpi1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Brent Crude (USD)</div>
            <div class="metric-value">${latest_oil:.2f} <span style="font-size:1rem;color:#64748b;">/bbl</span></div>
            <div class="metric-delta {'delta-pos' if oil_mom > 0 else 'delta-neg'}">
                {oil_mom:+.2f}% vs prior month ({latest_month.strftime('%b %Y')})
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">USD / ZAR Exchange Rate</div>
            <div class="metric-value">R {latest_rand:.2f}</div>
            <div class="metric-delta {'delta-pos' if rand_mom > 0 else 'delta-neg'}">
                {rand_mom:+.2f}% vs prior month (deprec = costlier)
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Oil in Rand (ZAR)</div>
            <div class="metric-value">R {latest_zar_bbl:,.0f} <span style="font-size:1rem;color:#64748b;">/bbl</span></div>
            <div class="metric-delta {'delta-pos' if zar_mom > 0 else 'delta-neg'}">
                {zar_mom:+.2f}% MoM combined cost impact
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        level_r = metrics["level_correlation"]
        changes_r = metrics["changes_correlation"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Correlation Contrast</div>
            <div class="metric-value">{changes_r:+.2f} <span style="font-size:1rem;color:#64748b;">(MoM)</span></div>
            <div class="metric-delta delta-neutral">
                Levels Drift: <b>{level_r:+.2f}</b> | MoM: <b>{changes_r:+.2f}</b>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Two column overview charts
    c1, c2 = st.columns([6, 5])
    with c1:
        st.plotly_chart(create_dual_axis_chart(df), use_container_width=True)
    with c2:
        st.plotly_chart(create_volatility_comparison_chart(changes_df), use_container_width=True)

    st.markdown("---")
    st.markdown("### 📌 Summary of Core Empirical Findings")
    f1, f2, f3 = st.columns(3)
    with f1:
        st.markdown(r"""
        **1. Spurious Level Drift (+0.30)**
        Both Brent crude and the Rand experienced upward drift over the decade (oil from $32 to $100+, rand from R14 to R18+). 
        This positive correlation reflects multi-year global macro cycles rather than month-to-month dependency.
        """)
    with f2:
        st.markdown(r"""
        **2. The 2020 COVID Illusion (-0.27)**
        In March 2020, oil collapsed (-39%) while the rand weakened (+10.7%) due to the emerging pandemic. 
        This single shock generates the negative correlation. Removing 2020 brings correlation to **-0.01**.
        """)
    with f3:
        st.markdown(r"""
        **3. Triple Volatility in Crude**
        International oil monthly changes exhibit a standard deviation of **9.35%**, compared to **3.22%** for USD/ZAR. 
        International crude volatility dominates short-term pump price uncertainty.
        """)


# -----------------------------------------------------------------------------
# View 2: Macro Trends & Price Levels
# -----------------------------------------------------------------------------
elif view_mode == "📈 Macro Trends & Price Levels":
    st.title("📈 Macro Trends & Price Levels")
    st.markdown(
        "Examining the historical trajectories of Brent crude oil prices and the USD/ZAR exchange rate, "
        "and their composite cost in South African Rand per barrel."
    )

    st.plotly_chart(create_dual_axis_chart(df), use_container_width=True)

    st.plotly_chart(create_oil_zar_chart(df), use_container_width=True)

    st.markdown("### 🔍 Historical Milestones & Price Extremes")
    e1, e2, e3, e4 = st.columns(4)

    high_oil_val, high_oil_dt = metrics["highest_oil_usd"]
    low_oil_val, low_oil_dt = metrics["lowest_oil_usd"]
    weak_rand_val, weak_rand_dt = metrics["weakest_rand"]
    high_zar_val, high_zar_dt = metrics["highest_oil_zar"]

    e1.metric("Highest Brent Price", f"${high_oil_val:.2f}", high_oil_dt.strftime("%B %Y"))
    e2.metric("Lowest Brent Price", f"${low_oil_val:.2f}", low_oil_dt.strftime("%B %Y"))
    e3.metric("Weakest Rand Level", f"R {weak_rand_val:.2f}", weak_rand_dt.strftime("%B %Y"))
    e4.metric("Highest Rand / Barrel", f"R {high_zar_val:,.0f}", high_zar_dt.strftime("%B %Y"))

    st.markdown(r"""
    > **Note on Oil in Rand:** South African refineries pay for crude in US dollars, which means currency depreciation directly magnifies high oil prices. 
    > In June 2022, Brent hit $117.46 while the rand averaged R15.80, peaking oil in rand at **R 1,856 per barrel**.
    """)


# -----------------------------------------------------------------------------
# View 3: Correlation & Volatility Lab
# -----------------------------------------------------------------------------
elif view_mode == "🔬 Correlation & Volatility Lab":
    st.title("🔬 Correlation & Volatility Laboratory")
    st.markdown(
        "Explore month-to-month dynamics, examine whether oil and currency moves offset each other, "
        "and track how the rolling correlation changes over time."
    )

    col_chart1, col_chart2 = st.columns([6, 5])
    with col_chart1:
        st.plotly_chart(create_changes_scatter_chart(changes_df), use_container_width=True)
    with col_chart2:
        st.markdown("#### Quadrant Dynamics")
        st.markdown("""
        - **Top-Right (Double Hit 🔴):** Oil rises AND Rand weakens. Maximum upward pressure on South African fuel prices.
        - **Bottom-Left (Double Relief 🟢):** Oil falls AND Rand strengthens. South African motorists enjoy large price cuts.
        - **Top-Left (COVID Shock Mode ⚠️):** Oil crashes while Rand weakens. The weakening currency partially cushions the drop.
        - **Bottom-Right:** Oil rises while Rand strengthens. Stronger rand mitigates rising oil costs.
        """)
        st.markdown("---")
        st.markdown("#### Current Selection Statistics")
        st_res = compute_correlation_stats(changes_df["oil_change_pct"], changes_df["rand_change_pct"])
        st.write(f"• **Sample Months (N):** {st_res['n_obs']}")
        st.write(f"• **Pearson Correlation ($r$):** {st_res['pearson_r']:.3f} (p-value: {st_res['pearson_p']:.4f})")
        st.write(f"• **Spearman Rank Correlation ($\\rho$):** {st_res['spearman_rho']:.3f} (p-value: {st_res['spearman_p']:.4f})")
        st.write(f"• **Statistically Significant at 5%?** {'Yes' if st_res['pearson_p'] < 0.05 else 'No'}")

    st.markdown("---")
    st.markdown("### 🔄 Dynamic Rolling Correlation")
    window_choice = st.slider("Select Rolling Correlation Window (Months):", min_value=6, max_value=36, value=24, step=6)
    
    rolling_corr = compute_rolling_correlation(changes_df["oil_change_pct"], changes_df["rand_change_pct"], window=window_choice)
    st.plotly_chart(create_rolling_corr_chart(rolling_corr, window=window_choice), use_container_width=True)

    st.markdown(f"""
    > **Insight on the {window_choice}-Month Rolling Window:** The correlation between oil and rand changes fluctuates wildly over time. 
    > It swung from positive (+0.3) in 2018 to deeply negative (-0.85) when the 2020 crash entered the window, then normalized back to neutral and slightly positive in 2025–2026. 
    > This confirms that there is **no persistent, structural economic rule** tying the rand to oil price shocks.
    """)


# -----------------------------------------------------------------------------
# View 4: Shock Sensitivity Sandbox
# -----------------------------------------------------------------------------
elif view_mode == "⚡ Shock Sensitivity Sandbox":
    st.title("⚡ Shock Sensitivity Sandbox")
    st.markdown(
        "A rigorous econometric analysis must test how sensitive conclusions are to extreme market outliers. "
        "Test predefined regime filters or dynamically exclude specific shock events below."
    )

    st.markdown("### 📊 Standardized Sensitivity Scenarios")
    scenario_table = run_sensitivity_scenarios(compute_monthly_changes(raw_df.loc[:BENCHMARK_CUTOFF]))
    st.dataframe(scenario_table, hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎛️ Interactive Outlier Stripper")
    st.markdown("Toggle specific shocks on and off to see how the Pearson and Spearman correlations immediately update:")

    c_t1, c_t2, c_t3 = st.columns(3)
    ex_2020 = c_t1.checkbox("Exclude All of 2020", value=False)
    ex_covid_crash = c_t2.checkbox("Exclude Only March & April 2020", value=False)
    ex_m26 = c_t3.checkbox("Exclude March 2026 Shipping Crisis", value=False)

    filtered_changes = filter_changes_dynamically(
        changes_df,
        exclude_all_2020=ex_2020,
        exclude_covid_crash_months=ex_covid_crash,
        exclude_march_2026=ex_m26
    )

    st_dyn = compute_correlation_stats(filtered_changes["oil_change_pct"], filtered_changes["rand_change_pct"])

    m_c1, m_c2, m_c3, m_c4 = st.columns(4)
    m_c1.metric("Remaining Months (N)", st_dyn["n_obs"])
    m_c2.metric("Pearson Correlation (r)", f"{st_dyn['pearson_r']:.3f}")
    m_c3.metric("p-value", f"{st_dyn['pearson_p']:.4f}")
    m_c4.metric("Spearman Rank (ρ)", f"{st_dyn['spearman_rho']:.3f}")

    st.plotly_chart(create_changes_scatter_chart(filtered_changes), use_container_width=True)


# -----------------------------------------------------------------------------
# View 5: South African Fuel Price Simulator
# -----------------------------------------------------------------------------
elif view_mode == "🧮 SA Fuel Price Simulator":
    st.title("🧮 South African Fuel Cost 'What-If' Simulator")
    st.markdown(
        "South Africa's Basic Fuel Price (BFP) formula directly incorporates the international price of oil and the rand exchange rate. "
        "Use this simulator to model how various combinations of crude oil prices and currency movements impact the landed cost of crude oil."
    )

    # Latest baseline parameters
    latest_dt = df.index[-1]
    base_oil = float(df.loc[latest_dt, "oil_usd"])
    base_rand = float(df.loc[latest_dt, "usd_zar"])

    st.markdown(f"**Current Baseline:** {latest_dt.strftime('%B %Y')} (Brent: **${base_oil:.2f}/bbl**, Exchange Rate: **R {base_rand:.2f} / $**)")

    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        sim_oil = st.slider("Simulated Brent Crude Price (USD per barrel):", min_value=30.0, max_value=160.0, value=float(round(base_oil, 1)), step=1.0)
    with sim_col2:
        sim_rand = st.slider("Simulated USD/ZAR Exchange Rate (Rands per Dollar):", min_value=12.0, max_value=25.0, value=float(round(base_rand, 2)), step=0.10)

    sim_result = simulate_fuel_cost(base_oil, base_rand, sim_oil, sim_rand)

    st.markdown("### 📊 Projected Impact on Landed Crude Costs")
    res1, res2, res3, res4 = st.columns(4)

    res1.metric(
        "Simulated Oil (ZAR/bbl)",
        f"R {sim_result['sim_zar_bbl']:,.0f}",
        f"{sim_result['pct_change']:+.1f}% vs baseline",
        delta_color="inverse"
    )

    res2.metric(
        "Absolute Cost Variance",
        f"R {sim_result['diff_zar_bbl']:+,.0f} / bbl",
        f"{sim_result['diff_zar_bbl']:+,.0f} ZAR",
        delta_color="inverse"
    )

    res3.metric(
        "Estimated Crude Cost / Litre",
        f"R {sim_result['sim_cpl']:.2f} / L",
        f"R {sim_result['diff_cpl']:+.2f} / L",
        delta_color="inverse"
    )

    # Risk Meter Interpretation
    with res4:
        pct = sim_result["pct_change"]
        if pct > 20:
            badge = "🚨 SEVERE UPWARD PRESSURE"
            desc = "Significant fuel price hikes expected at the pump."
        elif pct > 5:
            badge = "⚠️ MODERATE UPWARD PRESSURE"
            desc = "Noticeable pump price increase."
        elif pct < -20:
            badge = "🎉 SUBSTANTIAL RELIEF"
            desc = "Major fuel price decrease expected."
        elif pct < -5:
            badge = "🟢 MODERATE RELIEF"
            desc = "Welcome price drop for motorists."
        else:
            badge = "⚖️ STABLE / NEUTRAL"
            desc = "Landed crude costs within normal variance."

        st.markdown(f"""
        <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; background: #fff;">
            <div style="font-size:0.8rem; font-weight:700; color:#64748b;">PRICE IMPACT ASSESSMENT</div>
            <div style="font-size:1.0rem; font-weight:700; margin: 4px 0;">{badge}</div>
            <div style="font-size:0.8rem; color:#475569;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### Scenario Matrix: Oil vs Rand Sensitivity")
    # Quick Matrix Table
    oil_steps = [60.0, 80.0, 100.0, 120.0, 140.0]
    rand_steps = [15.0, 16.5, 18.0, 19.5, 21.0]

    matrix_data = {}
    for r in rand_steps:
        row_vals = []
        for o in oil_steps:
            zar_cost = o * r
            row_vals.append(f"R {zar_cost:,.0f}")
        matrix_data[f"USD/ZAR R{r:.1f}"] = row_vals

    matrix_df = pd.DataFrame(matrix_data, index=[f"Brent ${o:.0f}" for o in oil_steps])
    st.markdown("**Projected Oil Price in Rand per Barrel (ZAR/bbl):**")
    st.dataframe(matrix_df, use_container_width=True)


# -----------------------------------------------------------------------------
# View 6: Data Inspector & Export
# -----------------------------------------------------------------------------
elif view_mode == "📋 Data Inspector & Export":
    st.title("📋 Data Inspector & Export")
    st.markdown("Inspect the underlying monthly time series, percentage changes, and download the data in CSV format.")

    tab_data, tab_changes = st.tabs(["Monthly Average Prices", "Month-over-Month % Changes"])

    with tab_data:
        disp_df = df.copy()
        disp_df.index = disp_df.index.strftime("%Y-%m-%d")
        disp_df.columns = ["Brent Crude (USD)", "USD/ZAR Rate", "Oil Price in Rand (ZAR)"]
        st.dataframe(disp_df.style.format({
            "Brent Crude (USD)": "${:.2f}",
            "USD/ZAR Rate": "R {:.2f}",
            "Oil Price in Rand (ZAR)": "R {:,.2f}"
        }), use_container_width=True)

        csv_data = df.to_csv().encode("utf-8")
        st.download_button(
            label="📥 Download Monthly Prices CSV",
            data=csv_data,
            file_name="monthly_oil_rand_data.csv",
            mime="text/csv"
        )

    with tab_changes:
        disp_chg = changes_df.copy()
        disp_chg.index = disp_chg.index.strftime("%Y-%m-%d")
        disp_chg.columns = ["Oil % Change", "Rand % Change", "Oil in ZAR % Change"]
        st.dataframe(disp_chg.style.format("{:+.2f}%"), use_container_width=True)

        csv_chg = changes_df.to_csv().encode("utf-8")
        st.download_button(
            label="📥 Download Monthly Changes CSV",
            data=csv_chg,
            file_name="monthly_oil_rand_changes.csv",
            mime="text/csv"
        )
