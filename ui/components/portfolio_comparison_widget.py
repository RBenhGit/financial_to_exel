"""
Portfolio Comparison Widget
===========================

Advanced portfolio comparison component for side-by-side analysis of multiple stocks,
with sophisticated metrics calculation, risk analysis, and performance visualization.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import math

from .advanced_framework import (
    AdvancedComponent, ComponentConfig, ComponentState,
    InteractionEvent, performance_monitor
)


class ComparisonMetric(Enum):
    """Available comparison metrics"""
    RETURNS = "returns"
    VOLATILITY = "volatility"
    SHARPE_RATIO = "sharpe_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    BETA = "beta"
    ALPHA = "alpha"
    CORRELATION = "correlation"
    VALUE_AT_RISK = "value_at_risk"
    CALMAR_RATIO = "calmar_ratio"
    SORTINO_RATIO = "sortino_ratio"


class ComparisonPeriod(Enum):
    """Time periods for comparison"""
    ONE_MONTH = "1M"
    THREE_MONTHS = "3M"
    SIX_MONTHS = "6M"
    ONE_YEAR = "1Y"
    TWO_YEARS = "2Y"
    FIVE_YEARS = "5Y"
    ALL_TIME = "All"


@dataclass
class PortfolioAsset:
    """Represents a single asset in portfolio comparison"""
    ticker: str
    name: str
    weight: float = 0.0
    sector: str = ""
    market_cap: float = 0.0
    data: pd.DataFrame = field(default_factory=pd.DataFrame)
    metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ComparisonResult:
    """Results of portfolio comparison analysis"""
    assets: List[PortfolioAsset]
    portfolio_metrics: Dict[str, float]
    correlation_matrix: pd.DataFrame
    risk_metrics: Dict[str, float]
    performance_data: pd.DataFrame
    attribution_analysis: Dict[str, Any]


class PortfolioComparisonWidget(AdvancedComponent):
    """
    Advanced portfolio comparison widget with multi-dimensional analysis,
    risk attribution, and sophisticated visualization capabilities
    """

    def __init__(self, config: ComponentConfig):
        super().__init__(config)
        self.assets: List[PortfolioAsset] = []
        self.benchmark_ticker = "SPY"
        self.risk_free_rate = 0.02
        self.comparison_period = ComparisonPeriod.ONE_YEAR

    @performance_monitor
    def render_content(self, data: Dict = None, **kwargs) -> ComparisonResult:
        """Render portfolio comparison widget"""

        # Portfolio setup section
        self._render_portfolio_setup()

        # Asset configuration
        self._render_asset_configuration()

        if len(self.assets) >= 2:
            # Calculate comparison metrics
            comparison_result = self._calculate_portfolio_metrics()

            # Render comparison analysis
            self._render_comparison_analysis(comparison_result)

            # Render performance visualization
            self._render_performance_visualization(comparison_result)

            # Render risk analysis
            self._render_risk_analysis(comparison_result)

            # Render attribution analysis
            self._render_attribution_analysis(comparison_result)

            return comparison_result
        else:
            st.info("Add at least 2 assets to begin portfolio comparison")
            return ComparisonResult(
                assets=[],
                portfolio_metrics={},
                correlation_matrix=pd.DataFrame(),
                risk_metrics={},
                performance_data=pd.DataFrame(),
                attribution_analysis={}
            )

    def _render_portfolio_setup(self):
        """Render portfolio setup controls"""
        st.markdown("### 📊 Portfolio Comparison Setup")

        col1, col2, col3 = st.columns(3)

        with col1:
            self.comparison_period = ComparisonPeriod(st.selectbox(
                "Analysis Period",
                options=[period.value for period in ComparisonPeriod],
                index=3,  # Default to 1Y
                key=f"{self.config.id}_period"
            ))

        with col2:
            self.benchmark_ticker = st.text_input(
                "Benchmark Ticker",
                value=self.benchmark_ticker,
                help="Benchmark for comparison (e.g., SPY, QQQ)",
                key=f"{self.config.id}_benchmark"
            ).upper()

        with col3:
            self.risk_free_rate = st.number_input(
                "Risk-Free Rate (%)",
                min_value=0.0,
                max_value=10.0,
                value=self.risk_free_rate * 100,
                step=0.1,
                key=f"{self.config.id}_risk_free"
            ) / 100

    def _render_asset_configuration(self):
        """Render asset selection and weighting interface"""
        st.markdown("### 🏗️ Portfolio Assets")

        # Asset input section
        with st.expander("Add Assets", expanded=True):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                new_ticker = st.text_input(
                    "Ticker Symbol",
                    placeholder="e.g., AAPL",
                    key=f"{self.config.id}_new_ticker"
                ).upper()

            with col2:
                new_weight = st.number_input(
                    "Weight (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=25.0,
                    step=1.0,
                    key=f"{self.config.id}_new_weight"
                )

            with col3:
                if st.button("➕ Add Asset", key=f"{self.config.id}_add_asset"):
                    if new_ticker and new_ticker not in [asset.ticker for asset in self.assets]:
                        self._add_asset(new_ticker, new_weight / 100)
                        st.rerun()

            with col4:
                if st.button("🔄 Rebalance", key=f"{self.config.id}_rebalance"):
                    self._rebalance_weights()
                    st.rerun()

        # Current assets table
        if self.assets:
            self._render_assets_table()

    def _render_assets_table(self):
        """Render current assets configuration table"""
        assets_data = []
        total_weight = sum(asset.weight for asset in self.assets)

        for i, asset in enumerate(self.assets):
            assets_data.append({
                "Ticker": asset.ticker,
                "Name": asset.name or self._get_asset_name(asset.ticker),
                "Weight (%)": f"{asset.weight * 100:.1f}",
                "Sector": asset.sector or self._get_asset_sector(asset.ticker),
                "Market Cap": self._format_market_cap(asset.market_cap)
            })

        assets_df = pd.DataFrame(assets_data)

        # Display table with styling
        styled_df = assets_df.style.format({
            "Weight (%)": "{:.1f}%"
        }).background_gradient(subset=["Weight (%)"], cmap="Blues")

        st.dataframe(styled_df, use_container_width=True)

        # Weight validation
        if abs(total_weight - 1.0) > 0.01:
            st.warning(f"⚠️ Portfolio weights sum to {total_weight:.1%}. Consider rebalancing.")

        # Asset management controls
        col1, col2, col3 = st.columns(3)

        with col1:
            remove_ticker = st.selectbox(
                "Remove Asset",
                options=["Select..."] + [asset.ticker for asset in self.assets],
                key=f"{self.config.id}_remove_asset"
            )

            if remove_ticker != "Select..." and st.button("🗑️ Remove", key=f"{self.config.id}_confirm_remove"):
                self._remove_asset(remove_ticker)
                st.rerun()

        with col2:
            if st.button("🧹 Clear All", key=f"{self.config.id}_clear_all"):
                self.assets.clear()
                st.rerun()

        with col3:
            preset = st.selectbox(
                "Load Preset",
                options=["Select...", "Tech Giants", "Dividend Aristocrats", "Growth Stocks", "Value Stocks"],
                key=f"{self.config.id}_preset"
            )

            if preset != "Select..." and st.button("📥 Load", key=f"{self.config.id}_load_preset"):
                self._load_preset_portfolio(preset)
                st.rerun()

    def _render_comparison_analysis(self, result: ComparisonResult):
        """Render comparison analysis metrics"""
        st.markdown("### 📈 Performance Comparison")

        if result.assets:
            # Create comparison metrics table
            metrics_data = []

            for asset in result.assets:
                metrics_data.append({
                    "Asset": asset.ticker,
                    "Weight": f"{asset.weight:.1%}",
                    "Return": f"{asset.metrics.get('total_return', 0):.2%}",
                    "Volatility": f"{asset.metrics.get('volatility', 0):.2%}",
                    "Sharpe Ratio": f"{asset.metrics.get('sharpe_ratio', 0):.2f}",
                    "Max Drawdown": f"{asset.metrics.get('max_drawdown', 0):.2%}",
                    "Beta": f"{asset.metrics.get('beta', 0):.2f}"
                })

            # Add portfolio aggregate row
            metrics_data.append({
                "Asset": "PORTFOLIO",
                "Weight": "100.0%",
                "Return": f"{result.portfolio_metrics.get('total_return', 0):.2%}",
                "Volatility": f"{result.portfolio_metrics.get('volatility', 0):.2%}",
                "Sharpe Ratio": f"{result.portfolio_metrics.get('sharpe_ratio', 0):.2f}",
                "Max Drawdown": f"{result.portfolio_metrics.get('max_drawdown', 0):.2%}",
                "Beta": f"{result.portfolio_metrics.get('beta', 0):.2f}"
            })

            metrics_df = pd.DataFrame(metrics_data)

            # Style the table
            def highlight_portfolio(s):
                return ['background-color: lightblue' if s.name == len(s) - 1 else '' for _ in s]

            styled_metrics = metrics_df.style.apply(highlight_portfolio, axis=1)

            st.dataframe(styled_metrics, use_container_width=True)

            # Key insights
            self._render_key_insights(result)

    def _render_key_insights(self, result: ComparisonResult):
        """Render key insights from comparison analysis"""
        st.markdown("#### 🎯 Key Insights")

        col1, col2, col3, col4 = st.columns(4)

        # Best performer
        best_asset = max(result.assets, key=lambda x: x.metrics.get('total_return', 0))
        with col1:
            st.metric(
                "Best Performer",
                best_asset.ticker,
                f"{best_asset.metrics.get('total_return', 0):.2%}"
            )

        # Highest Sharpe ratio
        best_sharpe = max(result.assets, key=lambda x: x.metrics.get('sharpe_ratio', 0))
        with col2:
            st.metric(
                "Best Risk-Adj Return",
                best_sharpe.ticker,
                f"{best_sharpe.metrics.get('sharpe_ratio', 0):.2f}"
            )

        # Most volatile
        most_volatile = max(result.assets, key=lambda x: x.metrics.get('volatility', 0))
        with col3:
            st.metric(
                "Most Volatile",
                most_volatile.ticker,
                f"{most_volatile.metrics.get('volatility', 0):.2%}"
            )

        # Portfolio vs Benchmark
        benchmark_return = result.portfolio_metrics.get('benchmark_return', 0)
        portfolio_return = result.portfolio_metrics.get('total_return', 0)
        with col4:
            st.metric(
                "vs Benchmark",
                f"{portfolio_return:.2%}",
                f"{portfolio_return - benchmark_return:.2%}"
            )

    def _render_performance_visualization(self, result: ComparisonResult):
        """Render performance visualization charts"""
        st.markdown("### 📊 Performance Visualization")

        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs(["Returns", "Risk-Return", "Correlation", "Allocation"])

        with tab1:
            self._render_returns_chart(result)

        with tab2:
            self._render_risk_return_scatter(result)

        with tab3:
            self._render_correlation_heatmap(result)

        with tab4:
            self._render_allocation_charts(result)

    def _render_returns_chart(self, result: ComparisonResult):
        """Render cumulative returns chart"""
        if result.performance_data.empty:
            st.warning("No performance data available")
            return

        fig = go.Figure()

        # Add asset performance lines
        for asset in result.assets:
            if asset.ticker in result.performance_data.columns:
                fig.add_trace(go.Scatter(
                    x=result.performance_data.index,
                    y=result.performance_data[asset.ticker],
                    mode='lines',
                    name=asset.ticker,
                    line=dict(width=2)
                ))

        # Add portfolio performance
        if 'Portfolio' in result.performance_data.columns:
            fig.add_trace(go.Scatter(
                x=result.performance_data.index,
                y=result.performance_data['Portfolio'],
                mode='lines',
                name='Portfolio',
                line=dict(width=3, color='black', dash='dash')
            ))

        # Add benchmark
        if 'Benchmark' in result.performance_data.columns:
            fig.add_trace(go.Scatter(
                x=result.performance_data.index,
                y=result.performance_data['Benchmark'],
                mode='lines',
                name=f'Benchmark ({self.benchmark_ticker})',
                line=dict(width=2, color='gray', dash='dot')
            ))

        fig.update_layout(
            title="Cumulative Returns Comparison",
            xaxis_title="Date",
            yaxis_title="Cumulative Return (%)",
            hovermode='x unified',
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_risk_return_scatter(self, result: ComparisonResult):
        """Render risk-return scatter plot"""
        if not result.assets:
            return

        returns = [asset.metrics.get('total_return', 0) for asset in result.assets]
        volatilities = [asset.metrics.get('volatility', 0) for asset in result.assets]
        tickers = [asset.ticker for asset in result.assets]
        weights = [asset.weight for asset in result.assets]

        fig = go.Figure()

        # Add individual assets
        fig.add_trace(go.Scatter(
            x=volatilities,
            y=returns,
            mode='markers+text',
            text=tickers,
            textposition="top center",
            marker=dict(
                size=[w * 1000 + 10 for w in weights],  # Size based on weight
                color=returns,
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Return (%)")
            ),
            name="Assets",
            hovertemplate="<b>%{text}</b><br>" +
                        "Return: %{y:.2%}<br>" +
                        "Volatility: %{x:.2%}<br>" +
                        "<extra></extra>"
        ))

        # Add portfolio point
        portfolio_return = result.portfolio_metrics.get('total_return', 0)
        portfolio_vol = result.portfolio_metrics.get('volatility', 0)

        fig.add_trace(go.Scatter(
            x=[portfolio_vol],
            y=[portfolio_return],
            mode='markers+text',
            text=['PORTFOLIO'],
            textposition="top center",
            marker=dict(
                size=20,
                color='black',
                symbol='diamond'
            ),
            name="Portfolio"
        ))

        fig.update_layout(
            title="Risk-Return Analysis",
            xaxis_title="Volatility (%)",
            yaxis_title="Return (%)",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_correlation_heatmap(self, result: ComparisonResult):
        """Render correlation heatmap"""
        if result.correlation_matrix.empty:
            st.warning("No correlation data available")
            return

        fig = go.Figure(data=go.Heatmap(
            z=result.correlation_matrix.values,
            x=result.correlation_matrix.columns,
            y=result.correlation_matrix.index,
            colorscale='RdBu',
            zmid=0,
            text=result.correlation_matrix.values.round(3),
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))

        fig.update_layout(
            title="Asset Correlation Matrix",
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def _render_allocation_charts(self, result: ComparisonResult):
        """Render portfolio allocation visualizations"""
        col1, col2 = st.columns(2)

        with col1:
            # Pie chart of asset allocation
            labels = [asset.ticker for asset in result.assets]
            values = [asset.weight for asset in result.assets]

            fig_pie = go.Figure(data=go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                textinfo='label+percent',
                textposition='auto'
            ))

            fig_pie.update_layout(
                title="Asset Allocation",
                height=400
            )

            st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Sector allocation if available
            sector_weights = {}
            for asset in result.assets:
                sector = asset.sector or "Unknown"
                sector_weights[sector] = sector_weights.get(sector, 0) + asset.weight

            if len(sector_weights) > 1:
                fig_sector = go.Figure(data=go.Pie(
                    labels=list(sector_weights.keys()),
                    values=list(sector_weights.values()),
                    hole=0.3,
                    textinfo='label+percent',
                    textposition='auto'
                ))

                fig_sector.update_layout(
                    title="Sector Allocation",
                    height=400
                )

                st.plotly_chart(fig_sector, use_container_width=True)
            else:
                st.info("Sector allocation not available")

    def _render_risk_analysis(self, result: ComparisonResult):
        """Render risk analysis section"""
        st.markdown("### ⚖️ Risk Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Portfolio Risk Metrics")
            risk_metrics = result.risk_metrics

            risk_data = [
                {"Metric": "Value at Risk (95%)", "Value": f"{risk_metrics.get('var_95', 0):.2%}"},
                {"Metric": "Conditional VaR", "Value": f"{risk_metrics.get('cvar_95', 0):.2%}"},
                {"Metric": "Maximum Drawdown", "Value": f"{risk_metrics.get('max_drawdown', 0):.2%}"},
                {"Metric": "Volatility", "Value": f"{risk_metrics.get('volatility', 0):.2%}"},
                {"Metric": "Downside Deviation", "Value": f"{risk_metrics.get('downside_deviation', 0):.2%}"},
                {"Metric": "Beta vs Benchmark", "Value": f"{risk_metrics.get('beta', 0):.2f}"}
            ]

            risk_df = pd.DataFrame(risk_data)
            st.dataframe(risk_df, use_container_width=True, hide_index=True)

        with col2:
            st.subheader("Risk Contribution")
            # Risk contribution by asset
            if result.assets:
                contrib_data = []
                for asset in result.assets:
                    contrib_data.append({
                        "Asset": asset.ticker,
                        "Weight": f"{asset.weight:.1%}",
                        "Risk Contribution": f"{asset.metrics.get('risk_contribution', 0):.1%}",
                        "Marginal VaR": f"{asset.metrics.get('marginal_var', 0):.2%}"
                    })

                contrib_df = pd.DataFrame(contrib_data)
                st.dataframe(contrib_df, use_container_width=True, hide_index=True)

    def _render_attribution_analysis(self, result: ComparisonResult):
        """Render performance attribution analysis"""
        st.markdown("### 🎯 Performance Attribution")

        if result.attribution_analysis:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Return Attribution")
                attribution = result.attribution_analysis

                attr_data = []
                for asset in result.assets:
                    contribution = asset.weight * asset.metrics.get('total_return', 0)
                    attr_data.append({
                        "Asset": asset.ticker,
                        "Return": f"{asset.metrics.get('total_return', 0):.2%}",
                        "Weight": f"{asset.weight:.1%}",
                        "Contribution": f"{contribution:.2%}"
                    })

                attr_df = pd.DataFrame(attr_data)
                st.dataframe(attr_df, use_container_width=True, hide_index=True)

            with col2:
                st.subheader("Attribution Chart")
                contributions = [asset.weight * asset.metrics.get('total_return', 0) for asset in result.assets]
                tickers = [asset.ticker for asset in result.assets]

                fig = go.Figure(data=go.Bar(
                    x=tickers,
                    y=contributions,
                    text=[f"{c:.2%}" for c in contributions],
                    textposition='auto'
                ))

                fig.update_layout(
                    title="Return Contribution by Asset",
                    xaxis_title="Asset",
                    yaxis_title="Contribution (%)",
                    height=400
                )

                st.plotly_chart(fig, use_container_width=True)

    def _add_asset(self, ticker: str, weight: float):
        """Add new asset to portfolio"""
        asset = PortfolioAsset(
            ticker=ticker,
            name=self._get_asset_name(ticker),
            weight=weight,
            sector=self._get_asset_sector(ticker),
            market_cap=self._get_market_cap(ticker)
        )
        self.assets.append(asset)

    def _remove_asset(self, ticker: str):
        """Remove asset from portfolio"""
        self.assets = [asset for asset in self.assets if asset.ticker != ticker]

    def _rebalance_weights(self):
        """Rebalance portfolio weights equally"""
        if self.assets:
            equal_weight = 1.0 / len(self.assets)
            for asset in self.assets:
                asset.weight = equal_weight

    def _calculate_portfolio_metrics(self) -> ComparisonResult:
        """Calculate comprehensive portfolio comparison metrics"""
        # Mock implementation - in production, this would fetch real data
        # and calculate actual metrics

        # Generate mock performance data
        performance_data = self._generate_mock_performance_data()

        # Calculate individual asset metrics
        for asset in self.assets:
            asset.metrics = self._calculate_asset_metrics(asset, performance_data)

        # Calculate portfolio metrics
        portfolio_metrics = self._calculate_portfolio_level_metrics()

        # Calculate correlation matrix
        correlation_matrix = self._calculate_correlation_matrix(performance_data)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics()

        # Calculate attribution analysis
        attribution_analysis = self._calculate_attribution_analysis()

        return ComparisonResult(
            assets=self.assets,
            portfolio_metrics=portfolio_metrics,
            correlation_matrix=correlation_matrix,
            risk_metrics=risk_metrics,
            performance_data=performance_data,
            attribution_analysis=attribution_analysis
        )

    def _generate_mock_performance_data(self) -> pd.DataFrame:
        """Generate mock performance data for demonstration"""
        # Create date range based on comparison period
        end_date = datetime.now()
        if self.comparison_period == ComparisonPeriod.ONE_MONTH:
            start_date = end_date - timedelta(days=30)
        elif self.comparison_period == ComparisonPeriod.THREE_MONTHS:
            start_date = end_date - timedelta(days=90)
        elif self.comparison_period == ComparisonPeriod.SIX_MONTHS:
            start_date = end_date - timedelta(days=180)
        elif self.comparison_period == ComparisonPeriod.ONE_YEAR:
            start_date = end_date - timedelta(days=365)
        elif self.comparison_period == ComparisonPeriod.TWO_YEARS:
            start_date = end_date - timedelta(days=730)
        else:
            start_date = end_date - timedelta(days=365)

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Generate mock returns for each asset
        data = {}
        np.random.seed(42)  # For consistent mock data

        for i, asset in enumerate(self.assets):
            # Generate returns with different characteristics
            daily_returns = np.random.normal(0.0008, 0.02, len(dates))  # ~20% annual vol
            daily_returns[0] = 0  # First day return is 0

            # Add some correlation between assets
            if i > 0:
                correlation_factor = 0.3
                daily_returns += correlation_factor * data[self.assets[0].ticker]

            # Calculate cumulative returns
            cumulative_returns = (1 + pd.Series(daily_returns)).cumprod() - 1
            data[asset.ticker] = cumulative_returns.values

        # Add portfolio performance (weighted average)
        portfolio_returns = np.zeros(len(dates))
        for asset in self.assets:
            portfolio_returns += asset.weight * data[asset.ticker]
        data['Portfolio'] = portfolio_returns

        # Add benchmark performance
        benchmark_returns = np.random.normal(0.0006, 0.015, len(dates))  # Slightly lower vol
        benchmark_returns[0] = 0
        data['Benchmark'] = (1 + pd.Series(benchmark_returns)).cumprod().values - 1

        return pd.DataFrame(data, index=dates)

    def _calculate_asset_metrics(self, asset: PortfolioAsset, performance_data: pd.DataFrame) -> Dict[str, float]:
        """Calculate metrics for individual asset"""
        if asset.ticker not in performance_data.columns:
            return {}

        returns = performance_data[asset.ticker].pct_change().dropna()

        # Mock calculations - replace with actual financial calculations
        return {
            'total_return': np.random.uniform(0.05, 0.25),
            'volatility': np.random.uniform(0.15, 0.35),
            'sharpe_ratio': np.random.uniform(0.5, 1.5),
            'max_drawdown': np.random.uniform(-0.05, -0.25),
            'beta': np.random.uniform(0.7, 1.3),
            'alpha': np.random.uniform(-0.02, 0.05),
            'risk_contribution': asset.weight * np.random.uniform(0.8, 1.2),
            'marginal_var': np.random.uniform(0.01, 0.03)
        }

    def _calculate_portfolio_level_metrics(self) -> Dict[str, float]:
        """Calculate portfolio-level metrics"""
        # Mock portfolio metrics
        return {
            'total_return': np.random.uniform(0.08, 0.18),
            'volatility': np.random.uniform(0.12, 0.25),
            'sharpe_ratio': np.random.uniform(0.6, 1.2),
            'max_drawdown': np.random.uniform(-0.08, -0.15),
            'beta': np.random.uniform(0.85, 1.15),
            'alpha': np.random.uniform(-0.01, 0.03),
            'benchmark_return': np.random.uniform(0.06, 0.12)
        }

    def _calculate_correlation_matrix(self, performance_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix for assets"""
        asset_columns = [asset.ticker for asset in self.assets]
        if all(col in performance_data.columns for col in asset_columns):
            return performance_data[asset_columns].corr()
        return pd.DataFrame()

    def _calculate_risk_metrics(self) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        # Mock risk metrics
        return {
            'var_95': np.random.uniform(-0.02, -0.05),
            'cvar_95': np.random.uniform(-0.03, -0.07),
            'max_drawdown': np.random.uniform(-0.08, -0.15),
            'volatility': np.random.uniform(0.12, 0.25),
            'downside_deviation': np.random.uniform(0.08, 0.18),
            'beta': np.random.uniform(0.85, 1.15)
        }

    def _calculate_attribution_analysis(self) -> Dict[str, Any]:
        """Calculate performance attribution analysis"""
        return {
            'total_attribution': sum(asset.weight * asset.metrics.get('total_return', 0) for asset in self.assets),
            'asset_contributions': {
                asset.ticker: asset.weight * asset.metrics.get('total_return', 0)
                for asset in self.assets
            }
        }

    def _get_asset_name(self, ticker: str) -> str:
        """Get asset name from ticker (mock implementation)"""
        names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'TSLA': 'Tesla Inc.',
            'META': 'Meta Platforms Inc.',
            'NVDA': 'NVIDIA Corporation',
            'SPY': 'SPDR S&P 500 ETF'
        }
        return names.get(ticker, ticker)

    def _get_asset_sector(self, ticker: str) -> str:
        """Get asset sector from ticker (mock implementation)"""
        sectors = {
            'AAPL': 'Technology',
            'MSFT': 'Technology',
            'GOOGL': 'Technology',
            'AMZN': 'Consumer Discretionary',
            'TSLA': 'Consumer Discretionary',
            'META': 'Technology',
            'NVDA': 'Technology',
            'SPY': 'ETF'
        }
        return sectors.get(ticker, 'Unknown')

    def _get_market_cap(self, ticker: str) -> float:
        """Get market cap from ticker (mock implementation)"""
        market_caps = {
            'AAPL': 3000000000000,
            'MSFT': 2800000000000,
            'GOOGL': 1700000000000,
            'AMZN': 1500000000000,
            'TSLA': 800000000000,
            'META': 900000000000,
            'NVDA': 1200000000000
        }
        return market_caps.get(ticker, 0)

    def _format_market_cap(self, market_cap: float) -> str:
        """Format market cap for display"""
        if market_cap == 0:
            return "N/A"
        elif market_cap >= 1e12:
            return f"${market_cap/1e12:.1f}T"
        elif market_cap >= 1e9:
            return f"${market_cap/1e9:.1f}B"
        elif market_cap >= 1e6:
            return f"${market_cap/1e6:.1f}M"
        else:
            return f"${market_cap:.0f}"

    def _load_preset_portfolio(self, preset: str):
        """Load a preset portfolio configuration"""
        self.assets.clear()

        if preset == "Tech Giants":
            presets = [
                ("AAPL", 0.25), ("MSFT", 0.25), ("GOOGL", 0.25), ("AMZN", 0.25)
            ]
        elif preset == "Dividend Aristocrats":
            presets = [
                ("JNJ", 0.20), ("PG", 0.20), ("KO", 0.20), ("PEP", 0.20), ("WMT", 0.20)
            ]
        elif preset == "Growth Stocks":
            presets = [
                ("TSLA", 0.30), ("NVDA", 0.25), ("AMD", 0.25), ("ROKU", 0.20)
            ]
        elif preset == "Value Stocks":
            presets = [
                ("BRK.B", 0.30), ("JPM", 0.25), ("BAC", 0.25), ("V", 0.20)
            ]
        else:
            return

        for ticker, weight in presets:
            self._add_asset(ticker, weight)


# Factory function for creating portfolio comparison widget
def create_portfolio_comparison_widget(component_id: str) -> PortfolioComparisonWidget:
    """Create portfolio comparison widget"""
    config = ComponentConfig(
        id=component_id,
        title="Portfolio Comparison Analysis",
        description="Advanced multi-asset portfolio comparison with risk analysis",
        cache_enabled=True,
        auto_refresh=False
    )
    return PortfolioComparisonWidget(config)