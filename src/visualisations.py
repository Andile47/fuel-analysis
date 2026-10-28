import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_dual_axis_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create dual-axis interactive time-series chart for Oil (USD) and USD/ZAR.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Brent Crude trace
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["oil_usd"],
            name="Brent Crude (USD/bbl)",
            line=dict(color="#1f2937", width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>Brent Crude: $%{y:.2f}/bbl<extra></extra>"
        ),
        secondary_y=False
    )

    # USD/ZAR trace
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["usd_zar"],
            name="USD / ZAR Exchange Rate",
            line=dict(color="#059669", width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>USD/ZAR: R %{y:.2f}<extra></extra>"
        ),
        secondary_y=True
    )

    # Event annotations
    events = [
        ("2020-03-01", "COVID Crash", "bottom left"),
        ("2022-06-01", "Ukraine War Peak", "top left"),
        ("2026-03-01", "Hormuz Shipping Shock", "top right")
    ]
    for date_str, text, anchor in events:
        dt = pd.to_datetime(date_str)
        if dt in df.index:
            fig.add_vline(x=dt, line_width=1, line_dash="dash", line_color="#9ca3af")

    fig.update_layout(
        title=dict(
            text="<b>Brent Crude Oil Price vs. USD/ZAR Exchange Rate (2016 – 2026)</b>",
            font=dict(size=16)
        ),
        xaxis=dict(title="Month", showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(
            title="Brent Crude (USD per barrel)",
            title_font=dict(color="#1f2937"),
            tickfont=dict(color="#1f2937"),
            showgrid=True,
            gridcolor="#f3f4f6"
        ),
        yaxis2=dict(
            title="Rand per US Dollar (ZAR)",
            title_font=dict(color="#059669"),
            tickfont=dict(color="#059669"),
            overlaying="y",
            side="right",
            showgrid=False
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        template="plotly_white",
        height=480
    )
    return fig


def create_oil_zar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create chart of Brent Crude in South African Rand per barrel.
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["oil_zar"],
            name="Oil in Rand (ZAR/bbl)",
            line=dict(color="#b91c1c", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(185, 28, 28, 0.08)",
            hovertemplate="<b>%{x|%b %Y}</b><br>Oil Price: R %{y:,.2f} per barrel<extra></extra>"
        )
    )

    # Highlight historical maximum and minimum
    max_idx = df["oil_zar"].idxmax()
    max_val = df["oil_zar"].max()
    min_idx = df["oil_zar"].idxmin()
    min_val = df["oil_zar"].min()

    fig.add_annotation(
        x=max_idx,
        y=max_val,
        text=f"All-time High: R {max_val:,.0f}<br>({max_idx.strftime('%b %Y')})",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#b91c1c",
        yshift=10,
        font=dict(size=11, color="#b91c1c"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="#b91c1c"
    )

    fig.add_annotation(
        x=min_idx,
        y=min_val,
        text=f"Trough: R {min_val:,.0f}<br>({min_idx.strftime('%b %Y')})",
        showarrow=True,
        arrowhead=2,
        arrowcolor="#4b5563",
        yshift=-10,
        font=dict(size=11, color="#4b5563"),
        bgcolor="rgba(255, 255, 255, 0.9)",
        bordercolor="#9ca3af"
    )

    fig.update_layout(
        title=dict(
            text="<b>Brent Crude Converted to Rand per Barrel (Monthly Average)</b>",
            font=dict(size=16)
        ),
        xaxis=dict(title="Month", showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(title="Rand per Barrel (ZAR)", showgrid=True, gridcolor="#f3f4f6"),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=420
    )
    return fig


def create_changes_scatter_chart(changes_df: pd.DataFrame) -> go.Figure:
    """
    Create scatter plot of monthly % changes with quadrant context and OLS trendline.
    """
    fig = go.Figure()

    df = changes_df.copy()
    
    # Categorize shock outliers for distinct styling
    shock_dates = [pd.to_datetime("2020-03-01"), pd.to_datetime("2020-04-01"), pd.to_datetime("2026-03-01")]
    df["is_shock"] = df.index.isin(shock_dates)
    
    regular = df[~df["is_shock"]]
    shocks = df[df["is_shock"]]

    # Regular points
    fig.add_trace(
        go.Scatter(
            x=regular["oil_change_pct"],
            y=regular["rand_change_pct"],
            mode="markers",
            name="Regular Months",
            marker=dict(size=8, color="#2563eb", opacity=0.65),
            customdata=regular.index.strftime("%b %Y"),
            hovertemplate="<b>%{customdata}</b><br>Oil Change: %{x:+.2f}%<br>Rand Change: %{y:+.2f}%<extra></extra>"
        )
    )

    # Outlier points
    if not shocks.empty:
        fig.add_trace(
            go.Scatter(
                x=shocks["oil_change_pct"],
                y=shocks["rand_change_pct"],
                mode="markers+text",
                name="Key Shock Months",
                text=shocks.index.strftime("%b %Y"),
                textposition="top center",
                textfont=dict(size=11, color="#dc2626"),
                marker=dict(size=13, color="#dc2626", symbol="diamond", line=dict(width=1.5, color="#7f1d1d")),
                customdata=shocks.index.strftime("%b %Y"),
                hovertemplate="<b>%{customdata} [SHOCK]</b><br>Oil Change: %{x:+.2f}%<br>Rand Change: %{y:+.2f}%<extra></extra>"
            )
        )

    # Regression Trendline
    if len(df) > 1:
        x_vals = df["oil_change_pct"]
        y_vals = df["rand_change_pct"]
        slope, intercept = np.polyfit(x_vals, y_vals, 1)
        x_range = np.linspace(x_vals.min(), x_vals.max(), 50)
        y_trend = slope * x_range + intercept

        fig.add_trace(
            go.Scatter(
                x=x_range,
                y=y_trend,
                mode="lines",
                name=f"Linear Fit (Slope: {slope:.2f})",
                line=dict(color="#4b5563", width=1.5, dash="dash"),
                hoverinfo="skip"
            )
        )

    # Reference crosshairs
    fig.add_hline(y=0, line_width=1, line_color="#9ca3af")
    fig.add_vline(x=0, line_width=1, line_color="#9ca3af")

    fig.update_layout(
        title=dict(
            text="<b>Month-over-Month % Change: Oil vs. USD/ZAR</b>",
            font=dict(size=16)
        ),
        xaxis=dict(
            title="Brent Oil Monthly Change (%)",
            zeroline=False,
            showgrid=True,
            gridcolor="#f3f4f6"
        ),
        yaxis=dict(
            title="USD/ZAR Monthly Change (%) [Positive = Rand Weaker]",
            zeroline=False,
            showgrid=True,
            gridcolor="#f3f4f6"
        ),
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        height=480
    )
    return fig


def create_rolling_corr_chart(rolling_series: pd.Series, window: int = 24) -> go.Figure:
    """
    Create rolling correlation chart with zero reference line and regime boundaries.
    """
    fig = go.Figure()

    clean_series = rolling_series.dropna()

    fig.add_trace(
        go.Scatter(
            x=clean_series.index,
            y=clean_series,
            mode="lines",
            name=f"{window}-Month Rolling Correlation",
            line=dict(color="#7c3aed", width=2.5),
            hovertemplate="<b>%{x|%b %Y}</b><br>Rolling Correlation: %{y:.3f}<extra></extra>"
        )
    )

    fig.add_hline(y=0, line_width=1.5, line_color="#4b5563", line_dash="solid")
    fig.add_hrect(y0=0, y1=1, fillcolor="rgba(34, 197, 94, 0.05)", line_width=0)
    fig.add_hrect(y0=-1, y1=0, fillcolor="rgba(239, 68, 68, 0.05)", line_width=0)

    fig.update_layout(
        title=dict(
            text=f"<b>{window}-Month Rolling Correlation of Monthly Percentage Changes</b>",
            font=dict(size=16)
        ),
        xaxis=dict(title="Window End Month", showgrid=True, gridcolor="#f3f4f6"),
        yaxis=dict(
            title="Pearson Correlation Coefficient (r)",
            range=[-1.0, 1.0],
            showgrid=True,
            gridcolor="#f3f4f6"
        ),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=420
    )
    return fig


def create_volatility_comparison_chart(changes_df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart comparing the standard deviations of monthly changes.
    """
    labels = ["Rand Change (USD/ZAR)", "Oil Change (USD)", "Combined Oil in Rand (ZAR)"]
    std_rand = changes_df["rand_change_pct"].std()
    std_oil = changes_df["oil_change_pct"].std()
    std_zar = changes_df["oil_zar_change_pct"].std() if "oil_zar_change_pct" in changes_df.columns else np.nan

    values = [std_rand, std_oil, std_zar]
    colors = ["#10b981", "#3b82f6", "#ef4444"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker=dict(color=colors),
                text=[f"{v:.2f}%" for v in values],
                textposition="outside"
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="<b>Volatility Comparison: Standard Deviation of Monthly % Changes</b>",
            font=dict(size=16)
        ),
        xaxis=dict(title="Driver Series"),
        yaxis=dict(title="Standard Deviation (%)", showgrid=True, gridcolor="#f3f4f6"),
        template="plotly_white",
        margin=dict(l=40, r=40, t=60, b=40),
        height=380
    )
    return fig
