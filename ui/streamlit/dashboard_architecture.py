"""
Advanced Financial Metrics Dashboard Architecture
===============================================

This module defines the architecture and layout structure for the advanced financial
metrics dashboard, providing a comprehensive, responsive design for financial analysis.
"""

import streamlit as st
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DashboardLayout(Enum):
    """Dashboard layout modes"""
    COMPACT = "compact"
    STANDARD = "standard"
    EXPANDED = "expanded"


class MetricType(Enum):
    """Types of financial metrics for categorization"""
    PROFITABILITY = "profitability"
    LIQUIDITY = "liquidity"
    EFFICIENCY = "efficiency"
    LEVERAGE = "leverage"
    VALUATION = "valuation"
    GROWTH = "growth"


@dataclass
class DashboardTheme:
    """Dashboard visual theme configuration"""
    primary_color: str = "#1f77b4"
    secondary_color: str = "#ff7f0e"
    accent_color: str = "#2ca02c"
    warning_color: str = "#d62728"
    background_color: str = "#ffffff"
    text_color: str = "#262730"
    border_color: str = "#e0e0e0"

    # Additional theme properties
    font_family: str = "Arial, sans-serif"
    border_radius: str = "8px"
    shadow: str = "0 2px 4px rgba(0,0,0,0.1)"


@dataclass
class ComponentConfig:
    """Configuration for dashboard components"""
    width: str = "100%"
    height: Optional[str] = None
    padding: str = "1rem"
    margin: str = "0.5rem"
    border: bool = True
    shadow: bool = True


class DashboardArchitecture:
    """Main dashboard architecture class defining layout and component structure"""

    def __init__(self, theme: DashboardTheme = None):
        self.theme = theme or DashboardTheme()
        self.layout_mode = DashboardLayout.STANDARD
        self._initialize_layout_structure()

    def _initialize_layout_structure(self):
        """Initialize the multi-panel dashboard layout structure"""
        self.layout_structure = {
            "header": {
                "height": "80px",
                "components": ["company_selector", "market_data_summary", "refresh_controls"]
            },
            "main_content": {
                "layout": "grid",
                "columns": 3,
                "rows": 2,
                "components": {
                    "overview_panel": {"position": (0, 0), "span": (1, 2)},
                    "ratios_panel": {"position": (0, 1), "span": (1, 1)},
                    "trends_panel": {"position": (1, 0), "span": (2, 1)},
                    "comparison_panel": {"position": (1, 1), "span": (1, 1)},
                    "alerts_panel": {"position": (2, 1), "span": (1, 1)}
                }
            },
            "sidebar": {
                "width": "300px",
                "components": ["filters", "settings", "data_sources", "export_controls"]
            },
            "footer": {
                "height": "60px",
                "components": ["status_bar", "performance_indicators"]
            }
        }

    def get_responsive_columns(self, screen_size: str = "desktop") -> List[float]:
        """Get responsive column ratios based on screen size"""
        column_configs = {
            "mobile": [1.0],  # Single column on mobile
            "tablet": [0.6, 0.4],  # Two columns on tablet
            "desktop": [0.25, 0.5, 0.25],  # Three columns on desktop
            "wide": [0.2, 0.3, 0.3, 0.2]  # Four columns on wide screens
        }
        return column_configs.get(screen_size, column_configs["desktop"])

    def create_metric_card_layout(self, metric_type: MetricType) -> Dict:
        """Create layout configuration for metric cards"""
        card_configs = {
            MetricType.PROFITABILITY: {
                "title": "Profitability Ratios",
                "icon": "📈",
                "color": self.theme.primary_color,
                "metrics": ["ROE", "ROA", "Gross Margin", "Operating Margin", "Net Margin"]
            },
            MetricType.LIQUIDITY: {
                "title": "Liquidity Ratios",
                "icon": "💧",
                "color": self.theme.secondary_color,
                "metrics": ["Current Ratio", "Quick Ratio", "Cash Ratio", "Working Capital"]
            },
            MetricType.EFFICIENCY: {
                "title": "Efficiency Ratios",
                "icon": "⚡",
                "color": self.theme.accent_color,
                "metrics": ["Asset Turnover", "Inventory Turnover", "Receivables Turnover"]
            },
            MetricType.LEVERAGE: {
                "title": "Leverage Ratios",
                "icon": "⚖️",
                "color": self.theme.warning_color,
                "metrics": ["Debt-to-Equity", "Debt-to-Assets", "Interest Coverage"]
            },
            MetricType.VALUATION: {
                "title": "Valuation Metrics",
                "icon": "💰",
                "color": self.theme.primary_color,
                "metrics": ["P/E", "P/B", "P/S", "EV/EBITDA", "PEG Ratio"]
            },
            MetricType.GROWTH: {
                "title": "Growth Metrics",
                "icon": "🚀",
                "color": self.theme.accent_color,
                "metrics": ["Revenue Growth", "Earnings Growth", "FCF Growth", "Dividend Growth"]
            }
        }
        return card_configs.get(metric_type, {})

    def get_dashboard_css(self) -> str:
        """Generate CSS for dashboard styling"""
        return f"""
        <style>
        .dashboard-container {{
            font-family: {self.theme.font_family};
            color: {self.theme.text_color};
            background-color: {self.theme.background_color};
        }}

        .metric-card {{
            background: white;
            border: 1px solid {self.theme.border_color};
            border-radius: {self.theme.border_radius};
            padding: 1rem;
            margin: 0.5rem;
            box-shadow: {self.theme.shadow};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .metric-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}

        .metric-value {{
            font-size: 2rem;
            font-weight: bold;
            margin: 0.5rem 0;
        }}

        .metric-label {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.25rem;
        }}

        .metric-change {{
            font-size: 0.8rem;
            font-weight: 500;
        }}

        .metric-change.positive {{
            color: {self.theme.accent_color};
        }}

        .metric-change.negative {{
            color: {self.theme.warning_color};
        }}

        .dashboard-header {{
            background: linear-gradient(90deg, {self.theme.primary_color}, {self.theme.secondary_color});
            color: white;
            padding: 1rem;
            border-radius: {self.theme.border_radius};
            margin-bottom: 1rem;
        }}

        .panel-title {{
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 1rem;
            color: {self.theme.primary_color};
        }}

        .chart-container {{
            background: white;
            border: 1px solid {self.theme.border_color};
            border-radius: {self.theme.border_radius};
            padding: 1rem;
            margin: 0.5rem 0;
        }}

        .responsive-grid {{
            display: grid;
            gap: 1rem;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        }}

        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 0.5rem;
        }}

        .status-green {{ background-color: {self.theme.accent_color}; }}
        .status-yellow {{ background-color: {self.theme.secondary_color}; }}
        .status-red {{ background-color: {self.theme.warning_color}; }}

        @media (max-width: 768px) {{
            .metric-card {{
                margin: 0.25rem;
                padding: 0.75rem;
            }}

            .metric-value {{
                font-size: 1.5rem;
            }}

            .responsive-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        </style>
        """


class DashboardComponents:
    """Component definitions for dashboard elements"""

    @staticmethod
    def create_header_component(company_name: str, ticker: str, current_price: float = None) -> str:
        """Create dashboard header with company info and controls"""
        price_display = f"${current_price:.2f}" if current_price else "N/A"

        return f"""
        <div class="dashboard-header">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h1 style="margin: 0; font-size: 1.8rem;">{company_name}</h1>
                    <p style="margin: 0; opacity: 0.9;">Ticker: {ticker} | Price: {price_display}</p>
                </div>
                <div style="display: flex; gap: 1rem;">
                    <div class="status-indicator status-green"></div>
                    <span style="font-size: 0.9rem;">Live Data</span>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def create_metric_card(title: str, value: str, change: str = None,
                          trend: str = "neutral", icon: str = "📊") -> str:
        """Create a metric display card"""
        change_class = f"metric-change {trend}" if trend != "neutral" else "metric-change"
        change_display = f'<div class="{change_class}">{change}</div>' if change else ""

        return f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {title}</div>
            <div class="metric-value">{value}</div>
            {change_display}
        </div>
        """

    @staticmethod
    def create_panel_container(title: str, content: str, icon: str = "📊") -> str:
        """Create a panel container with title and content"""
        return f"""
        <div class="chart-container">
            <div class="panel-title">{icon} {title}</div>
            {content}
        </div>
        """


def render_dashboard_layout():
    """Render the main dashboard layout structure using Streamlit"""

    # Initialize architecture
    dashboard = DashboardArchitecture()

    # Apply custom CSS
    st.markdown(dashboard.get_dashboard_css(), unsafe_allow_html=True)

    # Detect screen size (simplified - in production would use JavaScript)
    # For now, use Streamlit's responsive behavior
    cols = st.columns(dashboard.get_responsive_columns("desktop"))

    return dashboard, cols


def create_metrics_grid(metrics_data: Dict, layout_cols: int = 3):
    """Create a responsive grid of metric cards"""

    # Group metrics by type
    grouped_metrics = {}
    for metric_name, metric_data in metrics_data.items():
        metric_type = metric_data.get('type', 'general')
        if metric_type not in grouped_metrics:
            grouped_metrics[metric_type] = []
        grouped_metrics[metric_type].append((metric_name, metric_data))

    # Create columns for responsive layout
    cols = st.columns(layout_cols)

    col_idx = 0
    for metric_type, metrics in grouped_metrics.items():
        with cols[col_idx % layout_cols]:
            st.markdown(f"### {metric_type.title()} Metrics")

            for metric_name, metric_data in metrics:
                value = metric_data.get('value', 'N/A')
                change = metric_data.get('change')
                trend = metric_data.get('trend', 'neutral')
                icon = metric_data.get('icon', '📊')

                card_html = DashboardComponents.create_metric_card(
                    metric_name, str(value), change, trend, icon
                )
                st.markdown(card_html, unsafe_allow_html=True)

        col_idx += 1


if __name__ == "__main__":
    # Example usage and testing
    st.set_page_config(
        page_title="Financial Dashboard Architecture",
        page_icon="📊",
        layout="wide"
    )

    st.title("📊 Dashboard Architecture Preview")

    # Render the dashboard layout
    dashboard, cols = render_dashboard_layout()

    # Example metrics data
    sample_metrics = {
        "ROE": {
            "value": "15.2%",
            "change": "+2.1% YoY",
            "trend": "positive",
            "type": "profitability",
            "icon": "📈"
        },
        "Current Ratio": {
            "value": "2.1",
            "change": "-0.3 QoQ",
            "trend": "negative",
            "type": "liquidity",
            "icon": "💧"
        },
        "P/E Ratio": {
            "value": "18.5",
            "change": "+1.2 vs Industry",
            "trend": "neutral",
            "type": "valuation",
            "icon": "💰"
        }
    }

    # Display example metrics grid
    st.subheader("Example Metrics Grid")
    create_metrics_grid(sample_metrics)

    # Display architecture information
    with st.expander("🏗️ Architecture Details"):
        st.json(dashboard.layout_structure)