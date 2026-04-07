import math
from dataclasses import dataclass

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Tax Drag Comparison",
    page_icon="%",
    layout="wide",
)


ACCENT = "#000000"
ACCENT_ALT = "rgb(150,140,131)"
HIGHLIGHT = "rgb(150,140,131)"
SUCCESS = "#000000"
PAPER = "#FFFFFF"
INK = "#000000"
MUTED = "#5D6B7A"
CARD = "#FFFFFF"
BORDER = "#000000"


st.markdown(
    f"""
    <style>
        .stApp {{
            background: #FFFFFF;
            color: {INK};
        }}
        .block-container {{
            padding-top: 2.25rem;
            padding-bottom: 2rem;
            max-width: 1380px;
        }}
        h1, h2, h3 {{
            color: {INK};
            letter-spacing: -0.02em;
        }}
        p, div, span, label {{
            color: {INK};
        }}
        .hero {{
            background: rgb(150,140,131);
            border: 1px solid {BORDER};
            border-radius: 24px;
            padding: 28px 30px 24px 30px;
            color: {INK};
            box-shadow: none;
            margin-bottom: 1.25rem;
        }}
        .hero-kicker {{
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.76rem;
            opacity: 0.72;
            margin-bottom: 10px;
        }}
        .hero h1 {{
            color: {INK};
            font-size: 2.4rem;
            margin: 0;
        }}
        .hero p {{
            font-size: 1rem;
            max-width: 920px;
            opacity: 1;
            margin-top: 0.8rem;
            margin-bottom: 0;
        }}
        .metric-card {{
            background: {CARD};
            border: 1px solid {BORDER};
            border-radius: 20px;
            padding: 20px 22px;
            min-height: 128px;
            box-shadow: none;
        }}
        .metric-label {{
            color: {MUTED};
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 12px;
        }}
        .metric-value {{
            color: {INK};
            font-size: 2rem;
            font-weight: 700;
            line-height: 1.1;
        }}
        .metric-sub {{
            color: {INK};
            font-size: 0.95rem;
            margin-top: 8px;
        }}
        .section-card {{
            background: #FFFFFF;
            border: 1px solid {BORDER};
            border-radius: 22px;
            padding: 18px 20px 20px 20px;
            box-shadow: none;
        }}
        [data-testid="stSidebar"] {{
            background: #FFFFFF;
            border-right: 1px solid {BORDER};
        }}
        [data-testid="stMetricValue"] {{
            color: {INK};
        }}
        [data-testid="stMetricLabel"] {{
            color: {INK};
        }}
        div[data-testid="stDataFrame"] {{
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid {BORDER};
            background: #FFFFFF;
        }}
        [data-testid="stDataFrame"] table {{
            background: #FFFFFF !important;
            border-collapse: separate !important;
        }}
        [data-testid="stDataFrame"] th,
        [data-testid="stDataFrame"] td {{
            background: #FFFFFF !important;
            border: none !important;
        }}
        .stPlotlyChart {{
            background: #FFFFFF;
            border-radius: 0;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)


@dataclass
class Scenario:
    start_value: float
    annual_return: float
    years: int
    turnover: float
    federal_tax_rate: float
    state_tax_rate: float

    @property
    def combined_tax_rate(self) -> float:
        return self.federal_tax_rate + self.state_tax_rate


def currency(value: float) -> str:
    return f"${value:,.0f}"


def percent(value: float, digits: int = 1) -> str:
    return f"{value:.{digits}f}%"


def build_deferred_stream(start_value: float, annual_return: float, years: int) -> pd.DataFrame:
    records = [
        {
            "Year": 0,
            "Deferred Account Value": start_value,
            "Deferred Taxes Paid": 0.0,
            "Deferred Cost Basis": start_value,
            "Deferred Cumulative Return": 0.0,
        }
    ]
    value = start_value
    for year in range(1, years + 1):
        value *= 1 + annual_return
        cumulative_return = (value / start_value - 1) if start_value else 0.0
        records.append(
            {
                "Year": year,
                "Deferred Account Value": value,
                "Deferred Taxes Paid": 0.0,
                "Deferred Cost Basis": start_value,
                "Deferred Cumulative Return": cumulative_return,
            }
        )
    return pd.DataFrame(records)


def build_turnover_stream(scenario: Scenario) -> pd.DataFrame:
    records = [
        {
            "Year": 0,
            "Taxable Account Value": scenario.start_value,
            "Taxable Cost Basis": scenario.start_value,
            "Taxable Unrealized Gain": 0.0,
            "Taxes Paid This Year": 0.0,
            "Cumulative Taxes Paid": 0.0,
            "Taxable Cumulative Return": 0.0,
        }
    ]
    value = scenario.start_value
    basis = scenario.start_value
    cumulative_taxes = 0.0

    for year in range(1, scenario.years + 1):
        value_before_sale = value * (1 + scenario.annual_return)
        realized_gain = max(scenario.turnover * (value_before_sale - basis), 0.0)
        taxes_due = realized_gain * scenario.combined_tax_rate
        cumulative_taxes += taxes_due

        value = value_before_sale - taxes_due
        basis = basis + realized_gain - taxes_due
        cumulative_return = (value / scenario.start_value - 1) if scenario.start_value else 0.0
        unrealized_gain = value - basis
        records.append(
            {
                "Year": year,
                "Taxable Account Value": value,
                "Taxable Cost Basis": basis,
                "Taxable Unrealized Gain": unrealized_gain,
                "Taxes Paid This Year": taxes_due,
                "Cumulative Taxes Paid": cumulative_taxes,
                "Taxable Cumulative Return": cumulative_return,
            }
        )

    return pd.DataFrame(records)


def metric_card(label: str, value: str, subtext: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{subtext}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


with st.sidebar:
    st.markdown("## Assumptions")

    default_start = 3_000_000.0
    start_deferred = st.number_input(
        "Tax-Aware Portfolio starting value",
        min_value=0.0,
        value=default_start,
        step=100_000.0,
        format="%.0f",
    )
    start_taxable = st.number_input(
        "Non-Tax-Aware Portfolio starting value",
        min_value=0.0,
        value=default_start,
        step=100_000.0,
        format="%.0f",
    )
    annual_return_pct = st.number_input(
        "Annual gross return (%)",
        min_value=-100.0,
        max_value=100.0,
        value=10.0,
        step=0.5,
    )
    years = st.slider("Time horizon (years)", min_value=1, max_value=50, value=20)
    turnover_pct = st.slider("Annual turnover ratio (%)", min_value=0, max_value=100, value=30)

    st.markdown("## Tax Rates")
    federal_tax_pct = st.number_input(
        "Federal capital gains tax (%)",
        min_value=0.0,
        max_value=50.0,
        value=20.0,
        step=0.5,
    )
    state_tax_pct = st.number_input(
        "State tax (%)",
        min_value=0.0,
        max_value=20.0,
        value=5.0,
        step=0.5,
    )

    st.markdown("## Presentation")
    show_table = st.checkbox("Show yearly detail table", value=True)
    show_basis = st.checkbox("Show cost basis chart", value=False)


annual_return = annual_return_pct / 100
turnover = turnover_pct / 100
federal_tax_rate = federal_tax_pct / 100
state_tax_rate = state_tax_pct / 100

scenario = Scenario(
    start_value=start_taxable,
    annual_return=annual_return,
    years=years,
    turnover=turnover,
    federal_tax_rate=federal_tax_rate,
    state_tax_rate=state_tax_rate,
)

deferred_df = build_deferred_stream(start_deferred, annual_return, years)
taxable_df = build_turnover_stream(scenario)
comparison_df = deferred_df.merge(taxable_df, on="Year", how="inner")

comparison_df["Value Gap"] = (
    comparison_df["Deferred Account Value"] - comparison_df["Taxable Account Value"]
)
comparison_df["Relative Advantage"] = comparison_df["Value Gap"] / comparison_df[
    "Taxable Account Value"
].replace(0, math.nan)

ending_deferred = float(comparison_df["Deferred Account Value"].iloc[-1])
ending_taxable = float(comparison_df["Taxable Account Value"].iloc[-1])
ending_gap = float(comparison_df["Value Gap"].iloc[-1])
ending_taxes = float(comparison_df["Cumulative Taxes Paid"].iloc[-1])
deferred_cagr = ((ending_deferred / start_deferred) ** (1 / years) - 1) if start_deferred > 0 else 0.0
taxable_cagr = ((ending_taxable / start_taxable) ** (1 / years) - 1) if start_taxable > 0 else 0.0
tax_drag_bps = (deferred_cagr - taxable_cagr) * 10_000
combined_tax_rate_pct = (federal_tax_rate + state_tax_rate) * 100

st.markdown(
    """
    <div class="hero">
        <div class="hero-kicker">Tax-Aware Investing Analysis</div>
        <h1>Compare tax-aware investing against annual turnover-driven realization.</h1>
        <p>
            This model isolates the effect of realizing capital gains during the investment horizon.
            The Tax-Aware Portfolio compounds without annual tax drag, while the Non-Tax-Aware Portfolio
            applies end-of-year taxes on realized gains based on the turnover ratio and user-defined tax rates.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)


top_cols = st.columns(4)
with top_cols[0]:
    metric_card(
        "Tax-Aware Portfolio",
        currency(ending_deferred),
        f"{percent(comparison_df['Deferred Cumulative Return'].iloc[-1] * 100)} cumulative growth",
    )
with top_cols[1]:
    metric_card(
        "Non-Tax-Aware Portfolio",
        currency(ending_taxable),
        f"{percent(comparison_df['Taxable Cumulative Return'].iloc[-1] * 100)} after annual tax drag",
    )
with top_cols[2]:
    metric_card(
        "Wealth Advantage",
        currency(ending_gap),
        f"{percent((ending_gap / ending_taxable * 100) if ending_taxable else 0.0)} more dollars",
    )
with top_cols[3]:
    metric_card(
        "Cumulative Taxes Paid",
        currency(ending_taxes),
        f"{percent(combined_tax_rate_pct)} combined tax rate",
    )


chart_col, context_col = st.columns([1.65, 1])

with chart_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Growth of Portfolio")

    growth_fig = go.Figure()
    growth_fig.add_trace(
        go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Deferred Account Value"],
            mode="lines",
            name="Tax-Aware Portfolio",
            line=dict(color=ACCENT, width=4),
        )
    )
    growth_fig.add_trace(
        go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Taxable Account Value"],
            mode="lines",
            name="Non-Tax-Aware Portfolio",
            line=dict(color=HIGHLIGHT, width=4),
        )
    )
    growth_fig.update_layout(
        height=480,
        margin=dict(l=10, r=10, t=70, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.08,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(color=INK),
        ),
        xaxis_title="Year",
        yaxis_title="Account Value ($)",
        yaxis_tickprefix="$",
        font=dict(color=INK),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
        yaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
    )
    st.plotly_chart(growth_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with context_col:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Model Summary")
    st.markdown(
        f"""
        - Starting values: Tax-Aware Portfolio {currency(start_deferred)} and Non-Tax-Aware Portfolio {currency(start_taxable)}
        - Gross return assumption: {percent(annual_return_pct)}
        - Horizon: {years} years
        - Annual turnover in Non-Tax-Aware Portfolio: {percent(turnover_pct)}
        - Combined capital gains tax rate: {percent(combined_tax_rate_pct)}
        - Approximate annualized tax drag: {tax_drag_bps:,.0f} bps
        """
    )
    st.markdown("### Assumption Notes")
    st.markdown(
        """
        - Taxes are paid at year-end only in the Non-Tax-Aware Portfolio.
        - Realized gains are modeled on a pro-rata basis using the account's embedded appreciation at the time of sale.
        - The Tax-Aware Portfolio assumes no interim capital gains realization.
        - This version does not force liquidation at the end of the horizon, so it emphasizes the value of tax deferral during the holding period.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)


bottom_left, bottom_right = st.columns([1.4, 1])

with bottom_left:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Tax Drag Over Time")
    gap_fig = go.Figure()
    gap_fig.add_trace(
        go.Bar(
            x=comparison_df["Year"],
            y=comparison_df["Value Gap"],
            name="Tax-Aware wealth advantage",
            marker_color=ACCENT_ALT,
        )
    )
    gap_fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis_title="Year",
        yaxis_title="Value Difference ($)",
        yaxis_tickprefix="$",
        font=dict(color=INK),
        legend=dict(
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(color=INK),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
        yaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
    )
    st.plotly_chart(gap_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with bottom_right:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Cumulative Taxes")
    tax_fig = go.Figure()
    tax_fig.add_trace(
        go.Scatter(
            x=comparison_df["Year"],
            y=comparison_df["Cumulative Taxes Paid"],
            mode="lines+markers",
            name="Taxes paid",
            line=dict(color=SUCCESS, width=3),
        )
    )
    if show_basis:
        tax_fig.add_trace(
            go.Scatter(
                x=comparison_df["Year"],
                y=comparison_df["Taxable Cost Basis"],
                mode="lines",
                name="Non-Tax-Aware cost basis",
                line=dict(color=ACCENT_ALT, width=2, dash="dash"),
            )
        )
    tax_fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=50, b=10),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        xaxis_title="Year",
        yaxis_title="Dollars ($)",
        yaxis_tickprefix="$",
        font=dict(color=INK),
        legend=dict(
            yanchor="bottom",
            y=1.06,
            xanchor="left",
            x=0,
            bgcolor="rgba(255,255,255,0)",
            borderwidth=0,
            font=dict(color=INK),
        ),
        xaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
        yaxis=dict(showgrid=False, zeroline=False, showline=True, linewidth=1, linecolor=BORDER, mirror=True),
    )
    st.plotly_chart(tax_fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


if show_table:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Year-by-Year Detail")
    display_df = comparison_df[
        [
            "Year",
            "Deferred Account Value",
            "Taxable Account Value",
            "Value Gap",
            "Taxes Paid This Year",
            "Cumulative Taxes Paid",
            "Taxable Cost Basis",
        ]
    ].copy()
    display_df = display_df.rename(
        columns={
            "Deferred Account Value": "Tax-Aware Portfolio",
            "Taxable Account Value": "Non-Tax-Aware Portfolio",
            "Taxable Cost Basis": "Non-Tax-Aware Cost Basis",
        }
    )

    st.dataframe(
        display_df.style.format(
            {
                "Tax-Aware Portfolio": "${:,.0f}",
                "Non-Tax-Aware Portfolio": "${:,.0f}",
                "Value Gap": "${:,.0f}",
                "Taxes Paid This Year": "${:,.0f}",
                "Cumulative Taxes Paid": "${:,.0f}",
                "Non-Tax-Aware Cost Basis": "${:,.0f}",
            }
        ).set_table_styles(
            [
                {"selector": "th", "props": [("border", "none"), ("background-color", "#FFFFFF")]},
                {"selector": "td", "props": [("border", "none"), ("background-color", "#FFFFFF")]},
                {"selector": "table", "props": [("border-collapse", "separate"), ("background-color", "#FFFFFF")]},
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)
