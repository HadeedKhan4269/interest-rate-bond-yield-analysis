from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================
from html import escape
from pathlib import Path
from typing import Final

import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st


# =============================================================================
# Theme / Styling
# =============================================================================
APP_TITLE: Final[str] = "Policy Yield Terminal"
APP_SUBTITLE: Final[str] = "A macro-finance dashboard for policy rates and 10-year government bond yields."
FOOTER_TEXT: Final[str] = "Data source: FRED &middot; Federal Reserve Bank of St. Louis"

DATA_FILE: Final[Path] = Path(__file__).with_name("Global_Monetary_Panel_Data.xlsx")
SHEET_NAME: Final[str] = "Panel_Data"
SOURCE_COLUMNS: Final[list[str]] = ["Date", "Country", "Policy Rate", "Bond Yield"]
COUNTRY_ORDER: Final[list[str]] = ["USA", "UK", "Japan", "Euro Area"]
THEME_KEY: Final[str] = "theme"
FONT_STACK: Final[str] = '-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif'
GRID_COLOR: Final[str] = "rgba(0,0,0,0.04)"
SCATTER_COLOR: Final[str] = "rgba(136,135,128,0.35)"
CHART_HEIGHT: Final[int] = 396

ThemeTokens = dict[str, str]
RegressionResult = dict[str, float]

THEMES = {
    "light": {
        "bg": "#F5F5F0",
        "sidebar": "#EEEEE9",
        "card": "#FAFAF8",
        "inner": "#E8E7E2",
        "border": "#D5D4CF",
        "text": "#2C2C2A",
        "muted": "#888780",
        "hint": "#B4B2A9",
    },
    "dark": {
        "bg": "#1A1917",
        "sidebar": "#201F1C",
        "card": "#252422",
        "inner": "#2C2B28",
        "border": "#363430",
        "text": "#D4D2CC",
        "muted": "#8A8885",
        "hint": "#6B6965",
    },
}

COMPARISON_RESULTS = pd.DataFrame(
    {
        "Country": ["USA", "UK", "Euro Area", "Japan"],
        "R^2": ["0.807", "0.887", "0.764", "~0.00"],
        "Coefficient": ["0.536", "0.727", "0.619", "0.000"],
        "P-value": ["~0.000", "~0.000", "~0.000", "N/A"],
    }
)

# Streamlit requires page config before any visible UI is rendered.
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_initial_theme() -> str:
    """Return the browser's initial Streamlit theme when available."""
    theme_type = st.context.theme.get("type") if hasattr(st, "context") else None
    return "dark" if theme_type == "dark" else "light"


def get_theme_mode() -> str:
    """Read the active theme from session state, initializing it once."""
    if THEME_KEY not in st.session_state:
        st.session_state[THEME_KEY] = get_initial_theme()
    return st.session_state[THEME_KEY]


def get_theme_tokens() -> ThemeTokens:
    """Return the current light or dark theme token dictionary."""
    return THEMES[get_theme_mode()]


def css_variables(theme: ThemeTokens) -> str:
    """Convert a theme dictionary into CSS custom properties."""
    return "\n".join(f"            --{key}: {value};" for key, value in theme.items())


def build_css(theme: ThemeTokens) -> str:
    """Build the app stylesheet from the active theme tokens."""
    return f"""
        <style>
        :root {{
{css_variables(theme)}
        }}

        * {{
            box-shadow: none !important;
        }}

        html, body, [class*="css"] {{
            font-family: {FONT_STACK};
            font-weight: 400;
        }}

        .stApp,
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        main,
        .block-container {{
            background: var(--bg) !important;
            color: var(--text) !important;
        }}

        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"],
        [data-testid="stStatusWidget"] {{
            background: transparent !important;
        }}

        .block-container {{
            max-width: 1120px;
            padding: 32px 40px 40px;
        }}

        section[data-testid="stSidebar"] {{
            background: var(--sidebar) !important;
            border-right: 1px solid var(--border);
            flex: 0 0 232px !important;
            min-width: 232px !important;
            width: 232px !important;
        }}

        section[data-testid="stSidebar"] > div {{
            background: var(--sidebar) !important;
            padding: 24px 16px;
            width: 232px !important;
        }}

        section[data-testid="stSidebar"] [data-testid="stVerticalBlock"],
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        [data-testid="column"],
        [data-testid="stElementContainer"],
        [data-testid="stForm"],
        [data-testid="stForm"] > div {{
            background: transparent !important;
            border-color: var(--border) !important;
        }}

        h1, h2, h3, p, label, span, div {{
            letter-spacing: 0;
        }}

        h1 {{
            color: var(--text) !important;
            font-size: 18px !important;
            font-weight: 500 !important;
            letter-spacing: -0.02em !important;
            line-height: 1.35 !important;
            margin: 0 !important;
            padding: 0 !important;
        }}

        h2, h3 {{
            color: var(--text) !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            margin: 0 !important;
        }}

        p, label, [data-testid="stMarkdownContainer"] {{
            color: var(--muted) !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            line-height: 1.5;
        }}

        [data-testid="stMarkdownContainer"] p {{
            margin: 0;
        }}

        .app-subtitle {{
            color: var(--muted) !important;
            font-size: 12px;
            line-height: 1.55;
            margin: 4px 0 24px;
        }}

        .sidebar-brand {{
            margin-bottom: 24px;
        }}

        .sidebar-title {{
            color: var(--text) !important;
            display: block;
            font-size: 15px;
            font-weight: 500;
            letter-spacing: -0.02em;
            line-height: 1.35;
        }}

        .sidebar-subtitle {{
            color: var(--muted) !important;
            display: block;
            font-size: 11px;
            line-height: 1.45;
            margin-top: 6px;
        }}

        .sidebar-nav {{
            border-bottom: 1px solid var(--border);
            border-top: 1px solid var(--border);
            margin: 20px 0;
            padding: 12px 0;
        }}

        .sidebar-nav a {{
            color: var(--muted) !important;
            display: block;
            font-size: 12px;
            padding: 6px 0;
            text-decoration: none;
        }}

        .section-label,
        .metric-label,
        .input-caption {{
            color: var(--hint) !important;
            display: block;
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.07em;
            line-height: 1.2;
            margin-bottom: 8px;
            text-transform: uppercase;
        }}

        .section-label {{
            margin-top: 24px;
        }}

        .section-label.first-section {{
            margin-top: 0;
        }}

        .sidebar-stat {{
            background: var(--inner);
            border: 1px solid var(--border);
            border-radius: 10px;
            margin-bottom: 8px;
            padding: 12px;
        }}

        .sidebar-stat .metric-label {{
            margin-bottom: 6px;
        }}

        .sidebar-stat-value,
        .metric-value,
        .context-value,
        .prediction-value {{
            color: var(--text) !important;
            display: block;
            font-weight: 500;
            letter-spacing: -0.01em;
            line-height: 1.25;
        }}

        .sidebar-stat-value,
        .context-value {{
            font-size: 18px;
        }}

        .metric-value {{
            font-size: 20px;
        }}

        .prediction-value {{
            font-size: 24px;
        }}

        .context-grid,
        .metric-grid {{
            display: grid;
            gap: 8px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin-bottom: 24px;
        }}

        .context-card,
        .metric-card,
        .info-card,
        .equation-card,
        .prediction-card,
        .table-card {{
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
        }}

        .context-card,
        .metric-card {{
            min-height: 78px;
            padding: 18px;
        }}

        .info-card {{
            background: var(--inner);
            color: var(--muted) !important;
            font-size: 12px;
            line-height: 1.55;
            padding: 18px 20px;
        }}

        .info-card strong {{
            color: var(--text) !important;
            font-weight: 500;
        }}

        .equation-card {{
            background: var(--inner);
            color: var(--muted) !important;
            font-family: "SF Mono", "Cascadia Mono", Consolas, monospace;
            font-size: 12px;
            line-height: 1.55;
            margin: 16px 0;
            padding: 16px 18px;
        }}

        .prediction-card {{
            background: var(--inner);
            margin-top: 12px;
            padding: 18px;
        }}

        [data-testid="stPlotlyChart"] {{
            background: var(--card) !important;
            border: 1px solid var(--border);
            border-radius: 12px;
            margin: 0 !important;
            overflow: hidden;
            padding: 16px;
        }}

        [data-testid="stPlotlyChart"] > div,
        [data-testid="stPlotlyChart"] .js-plotly-plot,
        [data-testid="stPlotlyChart"] .plot-container,
        [data-testid="stPlotlyChart"] .svg-container,
        [data-testid="stPlotlyChart"] svg.main-svg,
        [data-testid="stPlotlyChart"] .main-svg .bg {{
            background: transparent !important;
        }}

        .chart-legend {{
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            gap: 8px 16px;
            margin: 8px 0 24px;
            padding-left: 2px;
        }}

        .legend-item {{
            align-items: center;
            color: var(--muted) !important;
            display: inline-flex;
            font-size: 10px;
        }}

        .legend-square {{
            border: 1px solid var(--border);
            border-radius: 2px;
            display: inline-block;
            height: 8px;
            margin-right: 6px;
            width: 8px;
        }}

        .table-card {{
            overflow: hidden;
        }}

        .data-table {{
            background: var(--card);
            border-collapse: collapse;
            color: var(--muted);
            font-size: 12px;
            width: 100%;
        }}

        .data-table th {{
            background: var(--inner);
            border-bottom: 1px solid var(--border);
            color: var(--hint);
            font-size: 10px;
            font-weight: 500;
            letter-spacing: 0.07em;
            padding: 12px 14px;
            text-align: left;
            text-transform: uppercase;
        }}

        .data-table td {{
            background: var(--card);
            border-bottom: 1px solid var(--border);
            color: var(--muted);
            padding: 12px 14px;
            text-align: left;
        }}

        .data-table tr:last-child td {{
            border-bottom: 0;
        }}

        div[data-baseweb="tab-list"] {{
            background: var(--card) !important;
            border: 1px solid var(--border);
            border-radius: 20px;
            gap: 0;
            margin-bottom: 24px;
            padding: 4px;
        }}

        button[data-baseweb="tab"] {{
            background: transparent !important;
            border-radius: 20px !important;
            color: var(--muted) !important;
            font-size: 12px !important;
            font-weight: 400 !important;
            padding: 7px 14px !important;
        }}

        button[data-baseweb="tab"] * {{
            color: inherit !important;
            font-weight: inherit !important;
        }}

        button[data-baseweb="tab"][aria-selected="true"],
        button[data-baseweb="tab"]:hover {{
            background: var(--inner) !important;
            color: var(--text) !important;
            font-weight: 500 !important;
        }}

        [data-baseweb="tab-highlight"],
        [data-baseweb="tab-border"] {{
            background: transparent !important;
        }}

        [data-baseweb="select"],
        [data-baseweb="select"] > div {{
            background: transparent !important;
        }}

        [data-baseweb="select"] > div {{
            background: var(--card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            color: var(--text) !important;
            min-height: 38px;
        }}

        .st-key-prediction-input-group,
        .st-key-prediction_input_group,
        [class*="st-key-prediction-input-group"],
        [class*="st-key-prediction_input_group"] {{
            background: var(--inner) !important;
            border: 1px solid var(--border) !important;
            border-radius: 12px !important;
            box-sizing: border-box !important;
            margin: 16px 0 12px !important;
            padding: 18px !important;
            width: 100% !important;
        }}

        .predictor-message {{
            color: var(--muted) !important;
            font-size: 12px;
            margin: 8px 0 0;
        }}

        [data-baseweb="select"] span,
        [data-baseweb="select"] input {{
            background: transparent !important;
            color: var(--text) !important;
            font-size: 12px !important;
            font-weight: 400 !important;
        }}

        [data-baseweb="select"] svg {{
            fill: var(--muted) !important;
        }}

        [data-baseweb="select"] > div:focus-within {{
            border-color: var(--muted) !important;
            outline: 0 !important;
        }}

        [data-baseweb="popover"],
        [data-baseweb="popover"] > div,
        [data-baseweb="menu"],
        [role="listbox"] {{
            background: var(--card) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            color: var(--text) !important;
        }}

        [role="option"],
        [data-baseweb="menu"] li,
        [data-baseweb="menu"] div {{
            background: var(--card) !important;
            color: var(--muted) !important;
            font-size: 12px !important;
            font-weight: 400 !important;
        }}

        [role="option"]:hover,
        [role="option"][aria-selected="true"] {{
            background: var(--inner) !important;
            color: var(--text) !important;
        }}

        div[data-testid="stButton"] {{
            margin: 0 !important;
        }}

        div[data-testid="stButton"] button {{
            align-items: center !important;
            background: var(--text) !important;
            border: 1px solid var(--text) !important;
            border-radius: 8px !important;
            color: var(--bg) !important;
            display: flex !important;
            font-size: 12px !important;
            font-weight: 500 !important;
            height: 44px !important;
            justify-content: center !important;
            min-height: 44px !important;
            padding: 0 14px;
            width: 100%;
        }}

        div[data-testid="stButton"] button:hover {{
            background: var(--muted) !important;
            border-color: var(--muted) !important;
        }}

        *:focus,
        *:focus-visible {{
            box-shadow: none !important;
            outline-color: var(--muted) !important;
        }}

        .footer {{
            color: var(--muted) !important;
            font-size: 10px;
            margin-top: 32px;
            padding-top: 8px;
            text-align: center;
        }}

        @media (max-width: 900px) {{
            .block-container {{
                padding: 24px 20px 32px;
            }}

            .context-grid,
            .metric-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
    """


def inject_css(theme: ThemeTokens) -> None:
    """Inject the theme-aware stylesheet on every Streamlit rerun."""
    render_html(build_css(theme))


# =============================================================================
# Data Loading
# =============================================================================
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    """Load and clean the first four columns from the Excel panel dataset."""
    data = pd.read_excel(
        DATA_FILE,
        sheet_name=SHEET_NAME,
        usecols=[0, 1, 2, 3],
        engine="openpyxl",
    )
    data = data.iloc[:, :4].copy()
    data.columns = SOURCE_COLUMNS
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Country"] = data["Country"].astype("string").str.strip()
    data["Policy Rate"] = pd.to_numeric(data["Policy Rate"], errors="coerce")
    data["Bond Yield"] = pd.to_numeric(data["Bond Yield"], errors="coerce")
    data = data.dropna(subset=SOURCE_COLUMNS)
    return data.sort_values(["Country", "Date"]).reset_index(drop=True)


# =============================================================================
# Data Processing Helpers
# =============================================================================
def get_country_data(data: pd.DataFrame, country: str) -> pd.DataFrame:
    """Return a copy of rows for one country."""
    return data[data["Country"] == country].copy()


def get_available_countries(data: pd.DataFrame) -> list[str]:
    """Return expected countries that are present in the loaded dataset."""
    available_countries = set(data["Country"])
    return [country for country in COUNTRY_ORDER if country in available_countries]


def compute_summary_stats(country_data: pd.DataFrame) -> pd.DataFrame:
    """Compute mean, min, and max statistics for the two analysis variables."""
    summary = (
        country_data[["Policy Rate", "Bond Yield"]]
        .agg(["mean", "min", "max"])
        .T.rename(columns={"mean": "Mean", "min": "Min", "max": "Max"})
        .reset_index(names="Metric")
    )
    for column in ["Mean", "Min", "Max"]:
        summary[column] = summary[column].map(lambda value: f"{value:.2f}")
    return summary


def format_date_range(data: pd.DataFrame) -> str:
    """Format the inclusive date range displayed in cards."""
    return f"{data['Date'].min():%b %Y} - {data['Date'].max():%b %Y}"


def parse_policy_rate(value: str) -> float | None:
    """Convert user-entered text to a float, or return None for invalid text."""
    try:
        return float(value.strip())
    except ValueError:
        return None


# =============================================================================
# Regression Logic
# =============================================================================
def run_regression(country_data: pd.DataFrame) -> RegressionResult | None:
    """Estimate Bond Yield as a linear function of Policy Rate.

    Returns None when the policy rate has no variation, which is the Japan-safe
    path that prevents statsmodels from fitting an invalid single-variable model.
    """
    model_data = country_data.dropna(subset=["Policy Rate", "Bond Yield"])
    if model_data.empty or model_data["Policy Rate"].nunique(dropna=True) <= 1:
        return None

    x = sm.add_constant(model_data["Policy Rate"], has_constant="add")
    y = model_data["Bond Yield"]
    model = sm.OLS(y, x).fit()
    return {
        "r_squared": float(model.rsquared),
        "intercept": float(model.params["const"]),
        "coefficient": float(model.params["Policy Rate"]),
        "p_value": float(model.pvalues["Policy Rate"]),
    }


def predict_bond_yield(regression: RegressionResult, policy_rate: float) -> float:
    """Return the fitted bond-yield prediction for a policy-rate input."""
    return regression["intercept"] + regression["coefficient"] * policy_rate


def format_p_value(value: float) -> str:
    """Format small regression p-values in a compact dashboard style."""
    return "< 0.001" if value < 0.001 else f"{value:.3f}"


# =============================================================================
# Chart Builders
# =============================================================================
def chart_axis_style(theme: ThemeTokens) -> dict[str, object]:
    """Return the common axis styling used by every chart."""
    return {
        "gridcolor": GRID_COLOR,
        "gridwidth": 0.5,
        "linecolor": theme["border"],
        "tickcolor": theme["border"],
        "tickfont": {"color": theme["muted"], "size": 10},
        "title": {"font": {"color": theme["muted"], "size": 10}},
        "zerolinecolor": GRID_COLOR,
        "zerolinewidth": 0.5,
    }


def build_plotly_template(theme: ThemeTokens) -> go.layout.Template:
    """Create the shared Plotly template for the active theme."""
    axis_style = chart_axis_style(theme)
    return go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font={
                "color": theme["muted"],
                "family": FONT_STACK,
                "size": 10,
            },
            title={"font": {"color": theme["text"], "size": 13}, "x": 0, "xanchor": "left"},
            showlegend=False,
            margin={"l": 48, "r": 24, "t": 46, "b": 44},
            xaxis=axis_style,
            yaxis=axis_style,
            hoverlabel={
                "bgcolor": theme["inner"],
                "bordercolor": theme["border"],
                "font": {"color": theme["text"], "size": 11},
            },
        )
    )


def apply_chart_layout(fig: go.Figure, title: str, x_title: str, y_title: str, theme: ThemeTokens) -> go.Figure:
    """Apply shared titles, sizing, axes, and transparent backgrounds to a chart."""
    fig.update_layout(
        template=build_plotly_template(theme),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        height=CHART_HEIGHT,
        hovermode="x unified",
    )
    axis_style = chart_axis_style(theme)
    fig.update_xaxes(showgrid=True, rangeslider_visible=False, **axis_style)
    fig.update_yaxes(showgrid=True, ticksuffix="%", **axis_style)
    return fig


def build_time_series_chart(country_data: pd.DataFrame, country: str, theme: ThemeTokens) -> go.Figure:
    """Build the country-level Policy Rate and Bond Yield line chart."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=country_data["Date"],
            y=country_data["Policy Rate"],
            mode="lines",
            name="Policy Rate",
            line={"color": theme["text"], "width": 1.8},
        )
    )
    fig.add_trace(
        go.Scatter(
            x=country_data["Date"],
            y=country_data["Bond Yield"],
            mode="lines",
            name="Bond Yield",
            line={"color": theme["muted"], "width": 1.8, "dash": "dash"},
        )
    )
    return apply_chart_layout(fig, f"{country}: policy rate and bond yield", "Date", "Percent", theme)


def build_scatter_chart(
    country_data: pd.DataFrame,
    country: str,
    regression: RegressionResult | None,
    theme: ThemeTokens,
) -> go.Figure:
    """Build the Policy Rate vs. Bond Yield scatter chart with optional OLS fit."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=country_data["Policy Rate"],
            y=country_data["Bond Yield"],
            mode="markers",
            name="Monthly observations",
            marker={"color": SCATTER_COLOR, "size": 7, "line": {"width": 0}},
        )
    )
    if regression is not None:
        x_values = pd.Series([country_data["Policy Rate"].min(), country_data["Policy Rate"].max()])
        y_values = regression["intercept"] + regression["coefficient"] * x_values
        fig.add_trace(
            go.Scatter(
                x=x_values,
                y=y_values,
                mode="lines",
                name="OLS fit",
                line={"color": theme["text"], "width": 1.8},
            )
        )
    fig.update_layout(hovermode="closest")
    return apply_chart_layout(fig, f"{country}: policy rate vs. bond yield", "Policy Rate (%)", "Bond Yield (%)", theme)


def comparison_color(theme: ThemeTokens, index: int) -> str:
    """Cycle restrained theme colors for cross-country overlays."""
    colors = [theme["text"], theme["muted"], theme["hint"], theme["border"]]
    return colors[index % len(colors)]


def build_comparison_chart(data: pd.DataFrame, value_column: str, title: str, theme: ThemeTokens) -> go.Figure:
    """Build a cross-country line chart for one numeric column."""
    fig = go.Figure()
    for index, country in enumerate(COUNTRY_ORDER):
        country_data = get_country_data(data, country)
        if country_data.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=country_data["Date"],
                y=country_data[value_column],
                mode="lines",
                name=country,
                line={"color": comparison_color(theme, index), "width": 1.7},
            )
        )
    return apply_chart_layout(fig, title, "Date", f"{value_column} (%)", theme)


# =============================================================================
# UI Components
# =============================================================================
def render_html(html: str) -> None:
    """Render trusted HTML snippets used for the dashboard card system."""
    st.markdown(html, unsafe_allow_html=True)


def metric_card(label: str, value: str, class_name: str = "metric-card") -> str:
    """Return a small HTML metric card."""
    return (
        f"<div class='{class_name}'>"
        f"<span class='metric-label'>{escape(label)}</span>"
        f"<span class='metric-value'>{escape(value)}</span>"
        "</div>"
    )


def context_card(label: str, value: str) -> str:
    """Return a country-context card used above the charts."""
    return (
        "<div class='context-card'>"
        f"<span class='metric-label'>{escape(label)}</span>"
        f"<span class='context-value'>{escape(value)}</span>"
        "</div>"
    )


def section_label(label: str, anchor: str | None = None, first: bool = False) -> None:
    """Render a compact uppercase section label with an optional anchor."""
    anchor_attr = f" id='{escape(anchor)}'" if anchor else ""
    class_name = "section-label first-section" if first else "section-label"
    render_html(f"<div{anchor_attr} class='{class_name}'>{escape(label)}</div>")


def render_table(table: pd.DataFrame) -> None:
    """Render a DataFrame as the app's compact themed HTML table."""
    headers = "".join(f"<th>{escape(str(column))}</th>" for column in table.columns)
    rows = []
    for _, row in table.iterrows():
        cells = "".join(f"<td>{escape(str(value))}</td>" for value in row)
        rows.append(f"<tr>{cells}</tr>")
    render_html(
        "<div class='table-card'>"
        f"<table class='data-table'><thead><tr>{headers}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
        "</div>"
    )


def render_chart_legend(items: list[tuple[str, str]]) -> None:
    """Render the small custom legend that sits below Plotly charts."""
    legend_items = "".join(
        (
            "<span class='legend-item'>"
            f"<span class='legend-square' style='background:{escape(color)}'></span>"
            f"{escape(label)}"
            "</span>"
        )
        for label, color in items
    )
    render_html(f"<div class='chart-legend'>{legend_items}</div>")


def render_plotly_chart(fig: go.Figure) -> None:
    """Render Plotly charts with the toolbar hidden."""
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# =============================================================================
# Main App Layout / Execution
# =============================================================================
def render_theme_selector() -> None:
    """Render the light/dark theme radio and rerun when it changes."""
    current_theme = st.session_state[THEME_KEY]
    selected_theme = st.sidebar.radio(
        "Theme",
        ["light", "dark"],
        index=["light", "dark"].index(current_theme),
        format_func=str.title,
        horizontal=True,
    )
    if selected_theme != current_theme:
        st.session_state[THEME_KEY] = selected_theme
        st.rerun()


def render_sidebar(data: pd.DataFrame, countries: list[str]) -> str:
    """Render sidebar controls and return the selected country."""
    st.sidebar.markdown(
        (
            "<div class='sidebar-brand'>"
            f"<span class='sidebar-title'>{APP_TITLE}</span>"
            f"<span class='sidebar-subtitle'>{APP_SUBTITLE}</span>"
            "</div>"
            "<div class='sidebar-nav'>"
            "<a href='#country-analysis'>Country analysis</a>"
            "<a href='#cross-country'>Cross-country comparison</a>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )

    render_theme_selector()
    selected_country = st.sidebar.selectbox("Country", countries, index=0)
    st.sidebar.markdown(
        metric_card("Observations", f"{len(data):,}", "sidebar-stat")
        + metric_card("Date range", format_date_range(data), "sidebar-stat"),
        unsafe_allow_html=True,
    )
    return selected_country


def render_header() -> None:
    """Render the page title and subtitle."""
    st.title(APP_TITLE)
    render_html(f"<p class='app-subtitle'>{APP_SUBTITLE}</p>")


def render_country_context(country: str, country_data: pd.DataFrame) -> None:
    """Render selected-country metadata cards."""
    cards = "".join(
        [
            context_card("Selected country", country),
            context_card("Observations", f"{len(country_data):,}"),
            context_card("Date range", format_date_range(country_data)),
        ]
    )
    render_html(f"<div class='context-grid'>{cards}</div>")


def render_charts(country: str, country_data: pd.DataFrame, regression: RegressionResult | None, theme: ThemeTokens) -> None:
    """Render the country time-series and relationship charts."""
    section_label("Time series")
    render_plotly_chart(build_time_series_chart(country_data, country, theme))
    render_chart_legend([("Policy Rate", "var(--text)"), ("Bond Yield", "var(--muted)")])

    section_label("Relationship")
    render_plotly_chart(build_scatter_chart(country_data, country, regression, theme))
    legend = [("Monthly observations", "var(--hint)")]
    if regression is not None:
        legend.append(("OLS fit", "var(--text)"))
    render_chart_legend(legend)


def render_summary_stats(country_data: pd.DataFrame) -> None:
    """Render summary statistics for policy rates and bond yields."""
    section_label("Summary statistics")
    render_table(compute_summary_stats(country_data))


def render_ols_metrics(regression: RegressionResult) -> None:
    """Render R-squared, coefficient, p-value, and fitted equation cards."""
    cards = "".join(
        [
            metric_card("R^2", f"{regression['r_squared']:.3f}"),
            metric_card("Coefficient", f"{regression['coefficient']:.3f}"),
            metric_card("P-value", format_p_value(regression["p_value"])),
        ]
    )
    render_html(f"<div class='metric-grid'>{cards}</div>")
    render_html(
        "<div class='equation-card'>"
        f"Bond Yield = {regression['intercept']:.3f} + {regression['coefficient']:.3f} x Policy Rate"
        "</div>"
    )


def render_prediction_section(country_data: pd.DataFrame, regression: RegressionResult) -> None:
    """Render policy-rate input, validation message, and predicted yield."""
    with st.container(key="prediction-input-group"):
        input_col, button_col, _ = st.columns([0.36, 0.12, 0.52], gap="small", vertical_alignment="bottom")
        default_rate = float(country_data["Policy Rate"].mean())
        policy_rate_text = input_col.text_input(
            "Policy Rate value",
            value=f"{default_rate:.2f}",
        )
        button_col.button("Predict", type="primary")

        policy_rate = parse_policy_rate(policy_rate_text)
        if policy_rate is None:
            render_html("<div class='predictor-message'>Enter a valid policy rate.</div>")
            return

    prediction = predict_bond_yield(regression, policy_rate)
    render_html(
        "<div class='prediction-card'>"
        "<span class='metric-label'>Predicted bond yield</span>"
        f"<span class='prediction-value'>{prediction:.2f}%</span>"
        "</div>"
    )


def render_ols_section(country: str, country_data: pd.DataFrame, regression: RegressionResult | None) -> None:
    """Render OLS output, or the constant-policy-rate message for Japan."""
    section_label("OLS model")
    if regression is None:
        render_html(
            "<div class='info-card'>"
            f"<strong>{escape(country)}:</strong> Policy Rate has zero variance after missing values are removed, "
            "so OLS cannot estimate how Bond Yield changes with Policy Rate."
            "</div>"
        )
        return

    render_ols_metrics(regression)
    render_prediction_section(country_data, regression)


def render_country_analysis(data: pd.DataFrame, country: str, theme: ThemeTokens) -> None:
    """Render the full Country Analysis tab."""
    country_data = get_country_data(data, country)
    regression = run_regression(country_data)

    section_label("Country context", "country-analysis", first=True)
    render_country_context(country, country_data)
    render_charts(country, country_data, regression, theme)
    render_summary_stats(country_data)
    render_ols_section(country, country_data, regression)


def render_cross_country_comparison(data: pd.DataFrame, theme: ThemeTokens) -> None:
    """Render the Cross-Country Comparison tab."""
    section_label("Cross-country comparison", "cross-country", first=True)

    render_plotly_chart(build_comparison_chart(data, "Bond Yield", "Bond yield over time", theme))
    render_chart_legend([(country, comparison_color(theme, index)) for index, country in enumerate(COUNTRY_ORDER)])

    render_plotly_chart(build_comparison_chart(data, "Policy Rate", "Policy rate over time", theme))
    render_chart_legend([(country, comparison_color(theme, index)) for index, country in enumerate(COUNTRY_ORDER)])

    section_label("Regression comparison")
    render_table(COMPARISON_RESULTS)


def render_footer() -> None:
    """Render the centered source note at the bottom of the app."""
    render_html(f"<div class='footer'>{FOOTER_TEXT}</div>")


def main() -> None:
    """Run the Streamlit app."""
    if THEME_KEY not in st.session_state:
        st.session_state[THEME_KEY] = get_initial_theme()

    theme = get_theme_tokens()
    inject_css(theme)
    render_header()

    if not DATA_FILE.exists():
        st.error(f"Could not find {DATA_FILE.name} in the app folder.")
        st.stop()

    data = load_data()
    countries = get_available_countries(data)
    if not countries:
        st.error("No expected countries were found in the first four columns of Panel_Data.")
        st.stop()

    selected_country = render_sidebar(data, countries)
    country_tab, comparison_tab = st.tabs(["Country Analysis", "Cross-Country Comparison"])

    with country_tab:
        render_country_analysis(data, selected_country, theme)

    with comparison_tab:
        render_cross_country_comparison(data, theme)

    render_footer()


if __name__ == "__main__":
    main()
