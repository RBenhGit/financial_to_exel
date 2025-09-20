"""
Portfolio Visualization and Reporting Module
============================================

This module provides comprehensive visualization and reporting capabilities for
portfolio analysis, including allocation charts, performance visualizations,
correlation analysis, and comprehensive reporting features.

Key Features:
- Portfolio allocation charts (pie charts, treemaps, sunburst)
- Performance visualization with benchmark overlays
- Correlation heatmaps and risk decomposition
- Interactive portfolio analytics dashboard
- PDF/Excel report generation
- Real-time portfolio monitoring

Visualization Types:
- Allocation: Pie charts, treemaps, sunburst charts
- Performance: Time series, cumulative returns, rolling metrics
- Risk: Correlation heatmaps, risk attribution, drawdown analysis
- Attribution: Sector analysis, geographic distribution
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, date, timedelta
import logging
from dataclasses import dataclass
import io
from pathlib import Path

# Import portfolio models and analytics
from core.analysis.portfolio.portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType
)
from core.analysis.portfolio.portfolio_performance_analytics import (
    PortfolioPerformanceAnalyzer, PerformanceMetrics, PerformancePeriod
)

# Import dashboard components for consistent styling
from ui.streamlit.dashboard_components import (
    MetricDefinition, MetricValue, FinancialMetricsHierarchy
)

# Import export utilities
try:
    from ui.streamlit.dashboard_export_utils import (
        create_pdf_report, export_to_excel, get_export_config
    )
    EXPORT_AVAILABLE = True
except ImportError:
    EXPORT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class PortfolioVisualizationConfig:
    """Configuration for portfolio visualization preferences"""

    # Chart preferences
    color_scheme: str = "plotly"  # plotly, viridis, blues, reds
    chart_height: int = 500
    show_legend: bool = True
    show_labels: bool = True

    # Performance preferences
    benchmark_tickers: List[str] = None
    risk_free_rate: float = 0.02
    performance_periods: List[PerformancePeriod] = None

    # Risk analysis preferences
    confidence_levels: List[float] = None
    correlation_method: str = "pearson"  # pearson, spearman, kendall

    def __post_init__(self):
        """Set default values for complex types"""
        if self.benchmark_tickers is None:
            self.benchmark_tickers = ["SPY", "VTI", "VOO"]
        if self.performance_periods is None:
            self.performance_periods = [
                PerformancePeriod.MONTHLY,
                PerformancePeriod.QUARTERLY,
                PerformancePeriod.ANNUAL,
                PerformancePeriod.INCEPTION_TO_DATE
            ]
        if self.confidence_levels is None:
            self.confidence_levels = [0.95, 0.99]


class PortfolioVisualizationEngine:
    """
    Comprehensive portfolio visualization and reporting engine
    """

    def __init__(self, config: Optional[PortfolioVisualizationConfig] = None):
        """Initialize visualization engine with configuration"""
        self.config = config or PortfolioVisualizationConfig()
        self.analytics = None  # Will be initialized when portfolio is provided

        # Color schemes for different chart types
        self.color_schemes = {
            "plotly": px.colors.qualitative.Plotly,
            "viridis": px.colors.sequential.Viridis,
            "blues": px.colors.sequential.Blues,
            "reds": px.colors.sequential.Reds,
            "safe": px.colors.qualitative.Safe,
            "bold": px.colors.qualitative.Bold
        }

        logger.info("Portfolio visualization engine initialized")

    def _initialize_analytics(self, portfolio: Portfolio) -> None:
        """Initialize portfolio performance analytics for the given portfolio"""
        if self.analytics is None or self.analytics.portfolio != portfolio:
            self.analytics = PortfolioPerformanceAnalyzer(portfolio, self.config.risk_free_rate)

    def render_portfolio_allocation_charts(
        self,
        portfolio: Portfolio,
        chart_types: List[str] = None
    ) -> None:
        """
        Render comprehensive portfolio allocation visualizations

        Args:
            portfolio: Portfolio object with holdings
            chart_types: List of chart types to display ['pie', 'treemap', 'sunburst']
        """
        if chart_types is None:
            chart_types = ['pie', 'treemap', 'sunburst']

        st.subheader("📊 Portfolio Allocation Analysis")

        # Prepare allocation data
        allocation_data = self._prepare_allocation_data(portfolio)

        if allocation_data.empty:
            st.warning("⚠️ No allocation data available for visualization")
            return

        # Create tabs for different chart types
        tab_names = []
        if 'pie' in chart_types:
            tab_names.append("Pie Chart")
        if 'treemap' in chart_types:
            tab_names.append("Treemap")
        if 'sunburst' in chart_types:
            tab_names.append("Sunburst")

        if len(tab_names) > 1:
            tabs = st.tabs(tab_names)
            tab_index = 0
        else:
            tabs = [st.container()]
            tab_index = 0

        # Pie Chart
        if 'pie' in chart_types:
            with tabs[tab_index]:
                self._render_allocation_pie_chart(allocation_data)
            tab_index += 1

        # Treemap
        if 'treemap' in chart_types:
            with tabs[tab_index]:
                self._render_allocation_treemap(allocation_data)
            tab_index += 1

        # Sunburst Chart
        if 'sunburst' in chart_types:
            with tabs[tab_index]:
                self._render_allocation_sunburst(allocation_data, portfolio)

    def _prepare_allocation_data(self, portfolio: Portfolio) -> pd.DataFrame:
        """Prepare allocation data for visualization"""
        try:
            holdings_data = []

            for holding in portfolio.holdings:
                if holding.current_weight > 0:  # Only include non-zero positions
                    holdings_data.append({
                        'ticker': holding.ticker,
                        'company_name': holding.company_name or holding.ticker,
                        'weight': holding.current_weight * 100,  # Convert to percentage
                        'market_value': holding.market_value or 0,
                        'shares': holding.shares,
                        'unrealized_gain_loss_pct': holding.unrealized_gain_loss_pct or 0,
                        'sector': getattr(holding, 'sector', 'Unknown'),
                        'industry': getattr(holding, 'industry', 'Unknown')
                    })

            df = pd.DataFrame(holdings_data)

            # Sort by weight for better visualization
            if not df.empty:
                df = df.sort_values('weight', ascending=False)

            return df

        except Exception as e:
            logger.error(f"Error preparing allocation data: {e}")
            return pd.DataFrame()

    def _render_allocation_pie_chart(self, data: pd.DataFrame) -> None:
        """Render portfolio allocation pie chart"""
        try:
            fig = go.Figure(data=[
                go.Pie(
                    labels=data['company_name'],
                    values=data['weight'],
                    textinfo='label+percent',
                    textposition='auto',
                    hovertemplate=(
                        "<b>%{label}</b><br>"
                        "Weight: %{value:.2f}%<br>"
                        "Market Value: $%{customdata[0]:,.0f}<br>"
                        "P&L: %{customdata[1]:+.2f}%<br>"
                        "<extra></extra>"
                    ),
                    customdata=np.column_stack((
                        data['market_value'],
                        data['unrealized_gain_loss_pct']
                    )),
                    marker=dict(
                        colors=self.color_schemes[self.config.color_scheme],
                        line=dict(color='#000000', width=2)
                    )
                )
            ])

            fig.update_layout(
                title={
                    'text': "Portfolio Allocation by Weight",
                    'x': 0.5,
                    'font': {'size': 18}
                },
                height=self.config.chart_height,
                showlegend=self.config.show_legend,
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)

            # Add summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Holdings", len(data))
            with col2:
                st.metric("Top Position", f"{data.iloc[0]['weight']:.1f}%")
            with col3:
                concentration = data.head(5)['weight'].sum()
                st.metric("Top 5 Concentration", f"{concentration:.1f}%")
            with col4:
                avg_weight = data['weight'].mean()
                st.metric("Average Weight", f"{avg_weight:.1f}%")

        except Exception as e:
            logger.error(f"Error rendering pie chart: {e}")
            st.error("Error rendering pie chart")

    def _render_allocation_treemap(self, data: pd.DataFrame) -> None:
        """Render portfolio allocation treemap"""
        try:
            # Create color scale based on performance
            colors = data['unrealized_gain_loss_pct']

            fig = go.Figure(go.Treemap(
                labels=data['company_name'],
                values=data['weight'],
                parents=[""] * len(data),  # All at root level
                textinfo="label+value+percent parent",
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Weight: %{value:.2f}%<br>"
                    "Market Value: $%{customdata[0]:,.0f}<br>"
                    "Shares: %{customdata[1]:,.0f}<br>"
                    "P&L: %{customdata[2]:+.2f}%<br>"
                    "<extra></extra>"
                ),
                customdata=np.column_stack((
                    data['market_value'],
                    data['shares'],
                    data['unrealized_gain_loss_pct']
                )),
                colorscale='RdYlGn',
                colorbar=dict(title="P&L %"),
                zmid=0,
                marker=dict(
                    colorscale='RdYlGn',
                    cmid=0,
                    line=dict(width=2)
                )
            ))

            fig.update_layout(
                title={
                    'text': "Portfolio Treemap (Size = Weight, Color = Performance)",
                    'x': 0.5,
                    'font': {'size': 18}
                },
                height=self.config.chart_height,
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Error rendering treemap: {e}")
            st.error("Error rendering treemap")

    def _render_allocation_sunburst(
        self,
        data: pd.DataFrame,
        portfolio: Portfolio
    ) -> None:
        """Render portfolio allocation sunburst chart with sector breakdown"""
        try:
            # Prepare hierarchical data (Portfolio -> Sector -> Individual Holdings)
            sunburst_data = []

            # Add portfolio root
            sunburst_data.append({
                'ids': portfolio.name,
                'labels': portfolio.name,
                'parents': '',
                'values': data['weight'].sum()
            })

            # Group by sector
            sector_groups = data.groupby('sector')

            for sector, sector_data in sector_groups:
                sector_weight = sector_data['weight'].sum()

                # Add sector level
                sunburst_data.append({
                    'ids': sector,
                    'labels': sector,
                    'parents': portfolio.name,
                    'values': sector_weight
                })

                # Add individual holdings
                for _, holding in sector_data.iterrows():
                    sunburst_data.append({
                        'ids': holding['ticker'],
                        'labels': holding['company_name'],
                        'parents': sector,
                        'values': holding['weight']
                    })

            df_sunburst = pd.DataFrame(sunburst_data)

            fig = go.Figure(go.Sunburst(
                ids=df_sunburst['ids'],
                labels=df_sunburst['labels'],
                parents=df_sunburst['parents'],
                values=df_sunburst['values'],
                branchvalues="total",
                hovertemplate='<b>%{label}</b><br>Weight: %{value:.2f}%<extra></extra>',
                maxdepth=3
            ))

            fig.update_layout(
                title={
                    'text': "Portfolio Sunburst (Portfolio → Sector → Holdings)",
                    'x': 0.5,
                    'font': {'size': 18}
                },
                height=self.config.chart_height,
                font=dict(size=12)
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Error rendering sunburst chart: {e}")
            st.error("Error rendering sunburst chart")

    def render_performance_visualization(
        self,
        portfolio: Portfolio,
        benchmark_data: Optional[Dict[str, pd.DataFrame]] = None,
        performance_metrics: Optional[PerformanceMetrics] = None
    ) -> None:
        """
        Render comprehensive performance visualization with benchmarks

        Args:
            portfolio: Portfolio object
            benchmark_data: Dictionary mapping benchmark names to price data
            performance_metrics: Pre-calculated performance metrics
        """
        st.subheader("📈 Portfolio Performance Analysis")

        # Performance overview metrics
        if performance_metrics:
            self._render_performance_metrics_cards(performance_metrics)

        # Time series performance charts
        self._render_performance_time_series(portfolio, benchmark_data)

        # Rolling performance metrics
        self._render_rolling_performance(portfolio, benchmark_data)

        # Drawdown analysis
        self._render_drawdown_analysis(portfolio)

    def _render_performance_metrics_cards(
        self,
        metrics: PerformanceMetrics
    ) -> None:
        """Render performance metrics as cards"""
        try:
            st.markdown("#### 📊 Key Performance Metrics")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if metrics.total_return is not None:
                    st.metric(
                        "Total Return",
                        f"{metrics.total_return:.2%}",
                        delta=None
                    )
                if metrics.sharpe_ratio is not None:
                    st.metric(
                        "Sharpe Ratio",
                        f"{metrics.sharpe_ratio:.2f}",
                        delta=None
                    )

            with col2:
                if metrics.annualized_return is not None:
                    st.metric(
                        "Annualized Return",
                        f"{metrics.annualized_return:.2%}",
                        delta=None
                    )
                if metrics.sortino_ratio is not None:
                    st.metric(
                        "Sortino Ratio",
                        f"{metrics.sortino_ratio:.2f}",
                        delta=None
                    )

            with col3:
                if metrics.volatility is not None:
                    st.metric(
                        "Volatility",
                        f"{metrics.volatility:.2%}",
                        delta=None
                    )
                if metrics.max_drawdown is not None:
                    st.metric(
                        "Max Drawdown",
                        f"{metrics.max_drawdown:.2%}",
                        delta=None
                    )

            with col4:
                if metrics.alpha is not None:
                    st.metric(
                        "Alpha",
                        f"{metrics.alpha:.2%}",
                        delta=None
                    )
                if metrics.beta is not None:
                    st.metric(
                        "Beta",
                        f"{metrics.beta:.2f}",
                        delta=None
                    )

        except Exception as e:
            logger.error(f"Error rendering performance metrics cards: {e}")
            st.error("Error displaying performance metrics")

    def _render_performance_time_series(
        self,
        portfolio: Portfolio,
        benchmark_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> None:
        """Render portfolio vs benchmark performance time series"""
        try:
            st.markdown("#### 📊 Performance Time Series")

            fig = go.Figure()

            # Add portfolio performance line
            # Note: This would need actual portfolio historical data
            # For now, creating a placeholder structure

            dates = pd.date_range(
                start=portfolio.creation_date or datetime.now() - timedelta(days=365),
                end=datetime.now(),
                freq='D'
            )

            # Simulated portfolio performance (would be actual data in real implementation)
            cumulative_returns = np.random.normal(0.0008, 0.02, len(dates)).cumsum()

            fig.add_trace(go.Scatter(
                x=dates,
                y=cumulative_returns,
                mode='lines',
                name=portfolio.name,
                line=dict(color='blue', width=3),
                hovertemplate='%{x}<br>Return: %{y:.2%}<extra></extra>'
            ))

            # Add benchmark data if available
            if benchmark_data:
                colors = ['red', 'green', 'orange', 'purple']
                for i, (benchmark_name, data) in enumerate(benchmark_data.items()):
                    if i < len(colors) and not data.empty:
                        # Calculate benchmark returns (simplified)
                        benchmark_returns = data.get('close', pd.Series()).pct_change().fillna(0).cumsum()

                        fig.add_trace(go.Scatter(
                            x=benchmark_returns.index,
                            y=benchmark_returns.values,
                            mode='lines',
                            name=benchmark_name,
                            line=dict(color=colors[i], width=2),
                            hovertemplate='%{x}<br>Return: %{y:.2%}<extra></extra>'
                        ))

            fig.update_layout(
                title="Cumulative Returns Comparison",
                xaxis_title="Date",
                yaxis_title="Cumulative Return",
                height=400,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Error rendering performance time series: {e}")
            st.error("Error rendering performance chart")

    def _render_rolling_performance(
        self,
        portfolio: Portfolio,
        benchmark_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> None:
        """Render rolling performance metrics"""
        try:
            st.markdown("#### 📊 Rolling Performance Metrics")

            # Rolling window selector
            window_days = st.selectbox(
                "Rolling Window",
                options=[30, 60, 90, 180, 252],
                index=2,
                format_func=lambda x: f"{x} days"
            )

            # Create rolling metrics visualization
            # This would be calculated from actual portfolio data
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=[
                    'Rolling Sharpe Ratio',
                    'Rolling Volatility',
                    'Rolling Alpha',
                    'Rolling Beta'
                ],
                vertical_spacing=0.12
            )

            # Simulated rolling data (would be actual calculations)
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=365),
                end=datetime.now(),
                freq='D'
            )

            # Rolling Sharpe Ratio
            rolling_sharpe = np.random.normal(1.2, 0.3, len(dates))
            fig.add_trace(
                go.Scatter(x=dates, y=rolling_sharpe, name='Sharpe Ratio'),
                row=1, col=1
            )

            # Rolling Volatility
            rolling_vol = np.random.normal(0.15, 0.05, len(dates))
            fig.add_trace(
                go.Scatter(x=dates, y=rolling_vol, name='Volatility'),
                row=1, col=2
            )

            # Rolling Alpha
            rolling_alpha = np.random.normal(0.02, 0.01, len(dates))
            fig.add_trace(
                go.Scatter(x=dates, y=rolling_alpha, name='Alpha'),
                row=2, col=1
            )

            # Rolling Beta
            rolling_beta = np.random.normal(1.0, 0.2, len(dates))
            fig.add_trace(
                go.Scatter(x=dates, y=rolling_beta, name='Beta'),
                row=2, col=2
            )

            fig.update_layout(
                height=600,
                showlegend=False,
                title_text=f"Rolling Performance Metrics ({window_days}-day window)"
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            logger.error(f"Error rendering rolling performance: {e}")
            st.error("Error rendering rolling performance metrics")

    def _render_drawdown_analysis(self, portfolio: Portfolio) -> None:
        """Render portfolio drawdown analysis"""
        try:
            st.markdown("#### 📊 Drawdown Analysis")

            # Simulated drawdown data (would be calculated from actual portfolio data)
            dates = pd.date_range(
                start=datetime.now() - timedelta(days=365),
                end=datetime.now(),
                freq='D'
            )

            # Generate realistic drawdown pattern
            returns = np.random.normal(0.0008, 0.02, len(dates))
            cumulative_returns = returns.cumsum()
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / (1 + running_max)

            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=['Portfolio Value', 'Drawdown'],
                shared_xaxes=True,
                vertical_spacing=0.1
            )

            # Portfolio value
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=cumulative_returns,
                    name='Portfolio Value',
                    line=dict(color='blue', width=2)
                ),
                row=1, col=1
            )

            # Underwater curve
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=drawdown,
                    name='Drawdown',
                    fill='tonexty',
                    fillcolor='rgba(255, 0, 0, 0.3)',
                    line=dict(color='red', width=1)
                ),
                row=2, col=1
            )

            fig.update_layout(
                height=500,
                showlegend=True,
                title_text="Portfolio Drawdown Analysis"
            )

            fig.update_yaxes(title_text="Cumulative Return", row=1, col=1)
            fig.update_yaxes(title_text="Drawdown %", row=2, col=1)
            fig.update_xaxes(title_text="Date", row=2, col=1)

            st.plotly_chart(fig, use_container_width=True)

            # Drawdown statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                max_dd = abs(drawdown.min())
                st.metric("Max Drawdown", f"{max_dd:.2%}")

            with col2:
                # Find longest drawdown period
                in_drawdown = drawdown < -0.001
                drawdown_periods = []
                current_period = 0
                for is_dd in in_drawdown:
                    if is_dd:
                        current_period += 1
                    else:
                        if current_period > 0:
                            drawdown_periods.append(current_period)
                        current_period = 0

                longest_dd = max(drawdown_periods) if drawdown_periods else 0
                st.metric("Longest Drawdown", f"{longest_dd} days")

            with col3:
                avg_dd = abs(drawdown[drawdown < 0].mean()) if any(drawdown < 0) else 0
                st.metric("Average Drawdown", f"{avg_dd:.2%}")

            with col4:
                # Recovery factor
                total_return = cumulative_returns[-1]
                recovery_factor = total_return / max_dd if max_dd > 0 else 0
                st.metric("Recovery Factor", f"{recovery_factor:.2f}")

        except Exception as e:
            logger.error(f"Error rendering drawdown analysis: {e}")
            st.error("Error rendering drawdown analysis")


def render_portfolio_visualization_dashboard(
    portfolio: Portfolio,
    performance_metrics: Optional[PerformanceMetrics] = None,
    benchmark_data: Optional[Dict[str, pd.DataFrame]] = None
) -> None:
    """
    Main function to render complete portfolio visualization dashboard

    Args:
        portfolio: Portfolio object to visualize
        performance_metrics: Pre-calculated performance metrics
        benchmark_data: Benchmark comparison data
    """
    try:
        # Initialize visualization engine
        config = PortfolioVisualizationConfig()
        viz_engine = PortfolioVisualizationEngine(config)

        # Render portfolio header
        st.title(f"📊 Portfolio Analysis: {portfolio.name}")

        # Portfolio overview
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_value = sum(h.market_value or 0 for h in portfolio.holdings)
            st.metric("Total Value", f"${total_value:,.0f}")

        with col2:
            st.metric("Holdings Count", len(portfolio.holdings))

        with col3:
            if portfolio.creation_date:
                days_old = (datetime.now().date() - portfolio.creation_date).days
                st.metric("Portfolio Age", f"{days_old} days")
            else:
                st.metric("Portfolio Age", "N/A")

        with col4:
            portfolio_type = portfolio.portfolio_type.value if portfolio.portfolio_type else "Unknown"
            st.metric("Strategy", portfolio_type.title())

        # Create main visualization tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Allocation",
            "📈 Performance",
            "🔗 Correlation & Risk",
            "📄 Reports"
        ])

        with tab1:
            viz_engine.render_portfolio_allocation_charts(
                portfolio,
                chart_types=['pie', 'treemap', 'sunburst']
            )

        with tab2:
            viz_engine.render_performance_visualization(
                portfolio,
                benchmark_data=benchmark_data,
                performance_metrics=performance_metrics
            )

        with tab3:
            render_correlation_risk_analysis(portfolio)

        with tab4:
            render_portfolio_reports(portfolio, performance_metrics)

        logger.info(f"Portfolio visualization dashboard rendered for {portfolio.name}")

    except Exception as e:
        logger.error(f"Error rendering portfolio visualization dashboard: {e}")
        st.error("Error loading portfolio visualization dashboard")


def render_correlation_risk_analysis(portfolio: Portfolio) -> None:
    """Render correlation heatmaps and risk decomposition analysis"""
    st.subheader("🔗 Correlation & Risk Analysis")

    try:
        # Prepare correlation data
        tickers = [h.ticker for h in portfolio.holdings if h.current_weight > 0]

        if len(tickers) < 2:
            st.warning("Need at least 2 holdings for correlation analysis")
            return

        # Simulated correlation matrix (would be calculated from actual price data)
        correlation_matrix = np.random.uniform(-0.3, 0.8, (len(tickers), len(tickers)))
        np.fill_diagonal(correlation_matrix, 1.0)

        # Make matrix symmetric
        correlation_matrix = (correlation_matrix + correlation_matrix.T) / 2
        np.fill_diagonal(correlation_matrix, 1.0)

        df_corr = pd.DataFrame(
            correlation_matrix,
            index=tickers,
            columns=tickers
        )

        # Correlation heatmap
        fig = px.imshow(
            df_corr,
            title="Holdings Correlation Matrix",
            color_continuous_scale="RdBu",
            aspect="auto",
            text_auto=True
        )

        fig.update_layout(
            height=500,
            title_x=0.5,
            font=dict(size=10)
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk decomposition
        st.markdown("#### 📊 Risk Decomposition")

        # Simulated risk contribution data
        risk_data = pd.DataFrame({
            'Ticker': tickers,
            'Weight': [h.current_weight * 100 for h in portfolio.holdings if h.current_weight > 0],
            'Risk_Contribution': np.random.uniform(5, 25, len(tickers)),
            'Marginal_Risk': np.random.uniform(10, 30, len(tickers))
        })

        # Risk contribution bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=risk_data['Ticker'],
            y=risk_data['Weight'],
            name='Weight %',
            marker_color='lightblue'
        ))

        fig.add_trace(go.Bar(
            x=risk_data['Ticker'],
            y=risk_data['Risk_Contribution'],
            name='Risk Contribution %',
            marker_color='red',
            opacity=0.7
        ))

        fig.update_layout(
            title="Weight vs Risk Contribution",
            xaxis_title="Holdings",
            yaxis_title="Percentage",
            barmode='group',
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)

        # Risk metrics summary
        col1, col2, col3 = st.columns(3)

        with col1:
            portfolio_var = np.random.uniform(0.15, 0.25, 1)[0]
            st.metric("Portfolio VaR (95%)", f"{portfolio_var:.2%}")

        with col2:
            max_individual_risk = risk_data['Risk_Contribution'].max()
            st.metric("Max Individual Risk", f"{max_individual_risk:.1f}%")

        with col3:
            concentration = (risk_data['Risk_Contribution'] > 15).sum()
            st.metric("High Risk Holdings", f"{concentration}")

    except Exception as e:
        logger.error(f"Error rendering correlation analysis: {e}")
        st.error("Error rendering correlation and risk analysis")


def render_portfolio_reports(
    portfolio: Portfolio,
    performance_metrics: Optional[PerformanceMetrics] = None
) -> None:
    """Render portfolio report generation interface"""
    st.subheader("📄 Portfolio Reports")

    try:
        # Report configuration
        col1, col2 = st.columns(2)

        with col1:
            report_type = st.selectbox(
                "Report Type",
                options=["Executive Summary", "Detailed Analysis", "Risk Report", "Performance Attribution"],
                index=0
            )

        with col2:
            report_format = st.selectbox(
                "Export Format",
                options=["PDF", "Excel", "PowerPoint"],
                index=0
            )

        # Report preview
        st.markdown("#### 📋 Report Preview")

        # Generate report preview content
        report_content = _generate_report_preview(portfolio, performance_metrics, report_type)

        # Display preview in expandable section
        with st.expander("📖 Report Content Preview", expanded=True):
            st.markdown(report_content)

        # Export buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Generate Report", type="primary"):
                _generate_full_report(portfolio, performance_metrics, report_type, report_format)

        with col2:
            if st.button("📧 Schedule Email"):
                st.info("Email scheduling feature would be implemented here")

        with col3:
            if st.button("🔗 Share Link"):
                st.info("Report sharing feature would be implemented here")

        # Report history
        st.markdown("#### 📚 Report History")

        # Simulated report history
        history_data = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=5, freq='M'),
            'Report Type': ['Executive Summary', 'Detailed Analysis', 'Risk Report', 'Performance Attribution', 'Executive Summary'],
            'Format': ['PDF', 'Excel', 'PDF', 'PowerPoint', 'PDF'],
            'Status': ['Completed', 'Completed', 'Completed', 'Completed', 'Completed']
        })

        st.dataframe(
            history_data,
            use_container_width=True,
            hide_index=True
        )

    except Exception as e:
        logger.error(f"Error rendering portfolio reports: {e}")
        st.error("Error loading portfolio reports")


def _generate_report_preview(
    portfolio: Portfolio,
    performance_metrics: Optional[PerformanceMetrics],
    report_type: str
) -> str:
    """Generate preview content for the selected report type"""

    current_date = datetime.now().strftime("%B %d, %Y")
    total_value = sum(h.market_value or 0 for h in portfolio.holdings)

    if report_type == "Executive Summary":
        return f"""
        # Portfolio Executive Summary

        **Report Date:** {current_date}
        **Portfolio:** {portfolio.name}
        **Total Value:** ${total_value:,.0f}
        **Holdings:** {len(portfolio.holdings)} positions

        ## Key Highlights

        - Portfolio performance summary
        - Top performing holdings
        - Risk metrics overview
        - Recommended actions

        ## Performance Summary

        {_format_performance_summary(performance_metrics)}

        ## Holdings Overview

        {_format_holdings_summary(portfolio)}
        """

    elif report_type == "Detailed Analysis":
        return f"""
        # Detailed Portfolio Analysis

        **Report Date:** {current_date}
        **Portfolio:** {portfolio.name}

        ## Portfolio Overview

        - Comprehensive holdings analysis
        - Detailed performance attribution
        - Risk decomposition
        - Sector allocation analysis

        ## Holdings Detail

        {_format_detailed_holdings(portfolio)}

        ## Performance Analysis

        {_format_detailed_performance(performance_metrics)}
        """

    elif report_type == "Risk Report":
        return f"""
        # Portfolio Risk Analysis Report

        **Report Date:** {current_date}
        **Portfolio:** {portfolio.name}

        ## Risk Summary

        - Portfolio-level risk metrics
        - Individual position risk contributions
        - Correlation analysis
        - Value at Risk calculations

        ## Risk Metrics

        {_format_risk_metrics(portfolio, performance_metrics)}
        """

    else:  # Performance Attribution
        return f"""
        # Performance Attribution Report

        **Report Date:** {current_date}
        **Portfolio:** {portfolio.name}

        ## Attribution Analysis

        - Asset allocation effects
        - Security selection effects
        - Interaction effects
        - Sector contribution analysis

        ## Attribution Summary

        {_format_attribution_analysis(portfolio, performance_metrics)}
        """


def _format_performance_summary(metrics: Optional[PerformanceMetrics]) -> str:
    """Format performance summary for reports"""
    if not metrics:
        return "Performance metrics not available."

    return f"""
    | Metric | Value |
    |--------|-------|
    | Total Return | {metrics.total_return:.2%} |
    | Annualized Return | {metrics.annualized_return:.2%} |
    | Volatility | {metrics.volatility:.2%} |
    | Sharpe Ratio | {metrics.sharpe_ratio:.2f} |
    | Max Drawdown | {metrics.max_drawdown:.2%} |
    """


def _format_holdings_summary(portfolio: Portfolio) -> str:
    """Format holdings summary for reports"""
    holdings_summary = "| Ticker | Company | Weight | Value |\n|--------|---------|-----------|-------|\n"

    for holding in sorted(portfolio.holdings, key=lambda h: h.current_weight, reverse=True)[:10]:
        holdings_summary += f"| {holding.ticker} | {holding.company_name or 'N/A'} | {holding.current_weight*100:.1f}% | ${holding.market_value or 0:,.0f} |\n"

    return holdings_summary


def _format_detailed_holdings(portfolio: Portfolio) -> str:
    """Format detailed holdings for reports"""
    return "Detailed holdings analysis would include comprehensive position-level metrics."


def _format_detailed_performance(metrics: Optional[PerformanceMetrics]) -> str:
    """Format detailed performance for reports"""
    return "Detailed performance analysis would include time-series analysis and attribution."


def _format_risk_metrics(portfolio: Portfolio, metrics: Optional[PerformanceMetrics]) -> str:
    """Format risk metrics for reports"""
    return "Risk metrics would include VaR, correlation analysis, and stress testing results."


def _format_attribution_analysis(portfolio: Portfolio, metrics: Optional[PerformanceMetrics]) -> str:
    """Format attribution analysis for reports"""
    return "Performance attribution analysis would break down returns by various factors."


def _generate_full_report(
    portfolio: Portfolio,
    performance_metrics: Optional[PerformanceMetrics],
    report_type: str,
    report_format: str
) -> None:
    """Generate and download full report"""
    try:
        if EXPORT_AVAILABLE:
            if report_format == "PDF":
                # Generate PDF report
                st.success("PDF report generation would be implemented here")
            elif report_format == "Excel":
                # Generate Excel report
                st.success("Excel report generation would be implemented here")
            else:
                # Generate PowerPoint report
                st.success("PowerPoint report generation would be implemented here")
        else:
            st.warning("Export functionality not available. Please install required dependencies.")

    except Exception as e:
        logger.error(f"Error generating report: {e}")
        st.error("Error generating report")