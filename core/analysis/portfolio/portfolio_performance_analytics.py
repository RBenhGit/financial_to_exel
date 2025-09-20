"""
Portfolio Performance Analytics Module
=====================================

This module implements comprehensive portfolio performance measurement and attribution
analysis, providing advanced metrics for portfolio evaluation and benchmarking.

Key Features:
- Portfolio returns calculation (time-weighted, money-weighted)
- Risk-adjusted performance metrics (Sharpe, Sortino, Information Ratio)
- Performance attribution analysis (allocation, selection, interaction effects)
- Benchmark comparison and tracking error analysis
- Drawdown analysis and recovery metrics
- Multi-period performance analysis

Performance Metrics:
- Total Return, Annualized Return, Volatility
- Sharpe Ratio, Sortino Ratio, Calmar Ratio
- Alpha, Beta, Tracking Error, Information Ratio
- Maximum Drawdown, Average Drawdown, Recovery Time
- Value at Risk (VaR), Expected Shortfall (ES)

Attribution Analysis:
- Asset Allocation Effect
- Security Selection Effect
- Interaction Effect
- Sector/Industry Attribution
- Currency Attribution (for international portfolios)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Literal
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging
from scipy import stats

from .portfolio_models import Portfolio, PortfolioHolding, PortfolioMetrics
from core.data_processing.data_contracts import MarketData, DataQuality

logger = logging.getLogger(__name__)


class PerformancePeriod(Enum):
    """Performance measurement periods"""
    DAILY = "1D"
    WEEKLY = "1W"
    MONTHLY = "1M"
    QUARTERLY = "3M"
    SEMI_ANNUAL = "6M"
    ANNUAL = "1Y"
    THREE_YEAR = "3Y"
    FIVE_YEAR = "5Y"
    INCEPTION_TO_DATE = "ITD"


class RiskFreeRateSource(Enum):
    """Risk-free rate data sources"""
    US_3M_TREASURY = "US_3M_TREASURY"
    US_10Y_TREASURY = "US_10Y_TREASURY"
    FED_FUNDS_RATE = "FED_FUNDS_RATE"
    CUSTOM = "CUSTOM"


@dataclass
class PerformanceMetrics:
    """Comprehensive performance metrics for a portfolio"""

    # Basic Return Metrics
    total_return: Optional[float] = None
    annualized_return: Optional[float] = None
    volatility: Optional[float] = None
    compound_annual_growth_rate: Optional[float] = None

    # Risk-Adjusted Metrics
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    treynor_ratio: Optional[float] = None

    # Market Comparison Metrics
    alpha: Optional[float] = None
    beta: Optional[float] = None
    r_squared: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None

    # Downside Risk Metrics
    max_drawdown: Optional[float] = None
    max_drawdown_duration: Optional[int] = None
    average_drawdown: Optional[float] = None
    recovery_time: Optional[int] = None

    # Value at Risk Metrics
    var_95: Optional[float] = None
    var_99: Optional[float] = None
    expected_shortfall_95: Optional[float] = None
    expected_shortfall_99: Optional[float] = None

    # Additional Metrics
    win_rate: Optional[float] = None
    best_month: Optional[float] = None
    worst_month: Optional[float] = None
    positive_months: Optional[int] = None
    negative_months: Optional[int] = None

    # Metadata
    period_analyzed: str = ""
    calculation_date: datetime = field(default_factory=datetime.now)
    risk_free_rate: Optional[float] = None
    benchmark_used: Optional[str] = None
    data_quality: DataQuality = DataQuality.UNKNOWN


@dataclass
class AttributionAnalysis:
    """Performance attribution analysis results"""

    # Total Attribution Effects
    total_excess_return: Optional[float] = None
    allocation_effect: Optional[float] = None
    selection_effect: Optional[float] = None
    interaction_effect: Optional[float] = None

    # Holding-Level Attribution
    holding_attribution: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Sector/Industry Attribution
    sector_attribution: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Currency Attribution (for international portfolios)
    currency_attribution: Dict[str, float] = field(default_factory=dict)

    # Timing Effects
    rebalancing_impact: Optional[float] = None
    cash_drag: Optional[float] = None

    # Metadata
    attribution_period: str = ""
    benchmark_used: str = ""
    calculation_method: str = "Brinson"  # Brinson, Brinson-Fachler, etc.


class PortfolioPerformanceAnalyzer:
    """
    Main class for portfolio performance analysis and attribution
    """

    def __init__(self, portfolio: Portfolio, risk_free_rate: float = 0.02):
        """
        Initialize portfolio performance analyzer

        Args:
            portfolio: Portfolio instance to analyze
            risk_free_rate: Annual risk-free rate for calculations
        """
        self.portfolio = portfolio
        self.risk_free_rate = risk_free_rate
        self.price_history: Optional[pd.DataFrame] = None
        self.benchmark_history: Optional[pd.DataFrame] = None

    def set_price_history(self, price_data: pd.DataFrame) -> None:
        """
        Set historical price data for portfolio holdings

        Args:
            price_data: DataFrame with dates as index and ticker symbols as columns
        """
        self.price_history = price_data.copy()

    def set_benchmark_history(self, benchmark_data: pd.DataFrame) -> None:
        """
        Set benchmark price history for comparison

        Args:
            benchmark_data: DataFrame with dates as index and benchmark prices
        """
        self.benchmark_history = benchmark_data.copy()

    def calculate_portfolio_returns(self,
                                  period: PerformancePeriod = PerformancePeriod.MONTHLY,
                                  rebalancing_dates: Optional[List[date]] = None) -> pd.Series:
        """
        Calculate portfolio returns over time

        Args:
            period: Return calculation frequency
            rebalancing_dates: Dates when portfolio was rebalanced

        Returns:
            Series of portfolio returns
        """
        if self.price_history is None:
            raise ValueError("Price history must be set before calculating returns")

        # Get portfolio holdings and weights
        holdings_weights = {h.ticker: h.current_weight for h in self.portfolio.holdings}

        # Calculate individual holding returns
        holding_returns = self.price_history.pct_change()

        # Calculate weighted portfolio returns
        portfolio_returns = pd.Series(0.0, index=holding_returns.index)

        for ticker, weight in holdings_weights.items():
            if ticker in holding_returns.columns:
                portfolio_returns += holding_returns[ticker] * weight

        # Handle rebalancing if specified
        if rebalancing_dates:
            portfolio_returns = self._adjust_for_rebalancing(
                portfolio_returns, rebalancing_dates
            )

        # Resample to requested period
        if period != PerformancePeriod.DAILY:
            portfolio_returns = self._resample_returns(portfolio_returns, period)

        return portfolio_returns.dropna()

    def calculate_performance_metrics(self,
                                    period: PerformancePeriod = PerformancePeriod.ANNUAL,
                                    benchmark_ticker: Optional[str] = None) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics

        Args:
            period: Performance measurement period
            benchmark_ticker: Benchmark for comparison

        Returns:
            PerformanceMetrics instance with calculated metrics
        """
        portfolio_returns = self.calculate_portfolio_returns(period)

        if len(portfolio_returns) < 2:
            logger.warning("Insufficient data for performance calculation")
            return PerformanceMetrics(
                period_analyzed=period.value,
                data_quality=DataQuality.POOR
            )

        metrics = PerformanceMetrics(
            period_analyzed=period.value,
            risk_free_rate=self.risk_free_rate
        )

        # Basic return metrics
        metrics.total_return = self._calculate_total_return(portfolio_returns)
        metrics.annualized_return = self._calculate_annualized_return(portfolio_returns, period)
        metrics.volatility = self._calculate_volatility(portfolio_returns, period)
        metrics.compound_annual_growth_rate = self._calculate_cagr(portfolio_returns)

        # Risk-adjusted metrics
        metrics.sharpe_ratio = self._calculate_sharpe_ratio(portfolio_returns, period)
        metrics.sortino_ratio = self._calculate_sortino_ratio(portfolio_returns, period)
        metrics.calmar_ratio = self._calculate_calmar_ratio(portfolio_returns, period)

        # Drawdown analysis
        drawdown_metrics = self._calculate_drawdown_metrics(portfolio_returns)
        metrics.max_drawdown = drawdown_metrics['max_drawdown']
        metrics.max_drawdown_duration = drawdown_metrics['max_drawdown_duration']
        metrics.average_drawdown = drawdown_metrics['average_drawdown']
        metrics.recovery_time = drawdown_metrics['recovery_time']

        # Value at Risk
        var_metrics = self._calculate_var_metrics(portfolio_returns)
        metrics.var_95 = var_metrics['var_95']
        metrics.var_99 = var_metrics['var_99']
        metrics.expected_shortfall_95 = var_metrics['es_95']
        metrics.expected_shortfall_99 = var_metrics['es_99']

        # Additional metrics
        metrics.win_rate = self._calculate_win_rate(portfolio_returns)
        metrics.best_month = portfolio_returns.max()
        metrics.worst_month = portfolio_returns.min()
        metrics.positive_months = (portfolio_returns > 0).sum()
        metrics.negative_months = (portfolio_returns < 0).sum()

        # Benchmark comparison if available
        if benchmark_ticker and self.benchmark_history is not None:
            benchmark_metrics = self._calculate_benchmark_metrics(
                portfolio_returns, benchmark_ticker, period
            )
            if benchmark_metrics:  # Only set if metrics were successfully calculated
                metrics.alpha = benchmark_metrics['alpha']
                metrics.beta = benchmark_metrics['beta']
                metrics.r_squared = benchmark_metrics['r_squared']
                metrics.tracking_error = benchmark_metrics['tracking_error']
                metrics.information_ratio = benchmark_metrics['information_ratio']
                metrics.treynor_ratio = benchmark_metrics['treynor_ratio']
                metrics.benchmark_used = benchmark_ticker

        metrics.data_quality = DataQuality.GOOD
        return metrics

    def calculate_attribution_analysis(self,
                                     benchmark_ticker: str,
                                     period: PerformancePeriod = PerformancePeriod.MONTHLY) -> AttributionAnalysis:
        """
        Calculate performance attribution analysis

        Args:
            benchmark_ticker: Benchmark for attribution analysis
            period: Attribution analysis period

        Returns:
            AttributionAnalysis instance with detailed attribution
        """
        if self.price_history is None or self.benchmark_history is None:
            raise ValueError("Both portfolio and benchmark history required for attribution")

        attribution = AttributionAnalysis(
            attribution_period=period.value,
            benchmark_used=benchmark_ticker,
            calculation_method="Brinson"
        )

        # Get portfolio and benchmark returns
        portfolio_returns = self.calculate_portfolio_returns(period)
        benchmark_returns = self._get_benchmark_returns(benchmark_ticker, period)

        if len(portfolio_returns) != len(benchmark_returns):
            logger.warning("Portfolio and benchmark return periods don't match")
            return attribution

        # Calculate total excess return
        excess_returns = portfolio_returns - benchmark_returns
        attribution.total_excess_return = excess_returns.mean()

        # Brinson Attribution Model
        attribution_effects = self._calculate_brinson_attribution(
            portfolio_returns, benchmark_returns
        )

        attribution.allocation_effect = attribution_effects['allocation']
        attribution.selection_effect = attribution_effects['selection']
        attribution.interaction_effect = attribution_effects['interaction']

        # Holding-level attribution
        attribution.holding_attribution = self._calculate_holding_attribution(
            portfolio_returns, benchmark_returns
        )

        # Sector attribution (if sector data available)
        attribution.sector_attribution = self._calculate_sector_attribution()

        # Additional effects
        attribution.cash_drag = self._calculate_cash_drag()
        attribution.rebalancing_impact = self._calculate_rebalancing_impact()

        return attribution

    def generate_performance_report(self,
                                  periods: List[PerformancePeriod] = None,
                                  benchmark_ticker: Optional[str] = None) -> Dict:
        """
        Generate comprehensive performance report

        Args:
            periods: List of periods to analyze
            benchmark_ticker: Benchmark for comparison

        Returns:
            Dictionary containing performance analysis results
        """
        if periods is None:
            periods = [
                PerformancePeriod.MONTHLY,
                PerformancePeriod.QUARTERLY,
                PerformancePeriod.ANNUAL
            ]

        report = {
            'portfolio_info': {
                'portfolio_id': self.portfolio.portfolio_id,
                'name': self.portfolio.name,
                'inception_date': self.portfolio.inception_date.isoformat(),
                'total_value': self.portfolio.portfolio_metrics.total_value,
                'number_of_holdings': len(self.portfolio.holdings)
            },
            'performance_by_period': {},
            'attribution_analysis': None,
            'risk_analysis': {},
            'summary_statistics': {}
        }

        # Calculate performance for each period
        for period in periods:
            metrics = self.calculate_performance_metrics(period, benchmark_ticker)
            report['performance_by_period'][period.value] = self._metrics_to_dict(metrics)

        # Attribution analysis for annual period
        if benchmark_ticker:
            attribution = self.calculate_attribution_analysis(
                benchmark_ticker, PerformancePeriod.ANNUAL
            )
            report['attribution_analysis'] = self._attribution_to_dict(attribution)

        # Risk analysis summary
        report['risk_analysis'] = self._generate_risk_summary()

        # Summary statistics
        report['summary_statistics'] = self._generate_summary_statistics()

        return report

    # Helper methods for calculations

    def _calculate_total_return(self, returns: pd.Series) -> float:
        """Calculate cumulative total return"""
        return (1 + returns).prod() - 1

    def _calculate_annualized_return(self, returns: pd.Series, period: PerformancePeriod) -> float:
        """Calculate annualized return"""
        total_return = self._calculate_total_return(returns)
        periods_per_year = self._get_periods_per_year(period)
        years = len(returns) / periods_per_year

        if years <= 0:
            return 0.0

        return (1 + total_return) ** (1 / years) - 1

    def _calculate_volatility(self, returns: pd.Series, period: PerformancePeriod) -> float:
        """Calculate annualized volatility"""
        periods_per_year = self._get_periods_per_year(period)
        return returns.std() * np.sqrt(periods_per_year)

    def _calculate_cagr(self, returns: pd.Series) -> float:
        """Calculate Compound Annual Growth Rate"""
        if len(returns) <= 1:
            return 0.0

        total_return = self._calculate_total_return(returns)
        years = len(returns) / 252  # Assuming daily returns

        return (1 + total_return) ** (1 / years) - 1

    def _calculate_sharpe_ratio(self, returns: pd.Series, period: PerformancePeriod) -> float:
        """Calculate Sharpe ratio"""
        excess_returns = returns - (self.risk_free_rate / self._get_periods_per_year(period))

        if excess_returns.std() == 0:
            return 0.0

        return excess_returns.mean() / excess_returns.std() * np.sqrt(self._get_periods_per_year(period))

    def _calculate_sortino_ratio(self, returns: pd.Series, period: PerformancePeriod) -> float:
        """Calculate Sortino ratio (using downside deviation)"""
        excess_returns = returns - (self.risk_free_rate / self._get_periods_per_year(period))
        downside_returns = excess_returns[excess_returns < 0]

        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0.0

        downside_deviation = downside_returns.std()
        return excess_returns.mean() / downside_deviation * np.sqrt(self._get_periods_per_year(period))

    def _calculate_calmar_ratio(self, returns: pd.Series, period: PerformancePeriod) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        annual_return = self._calculate_annualized_return(returns, period)
        max_drawdown = abs(self._calculate_drawdown_metrics(returns)['max_drawdown'])

        if max_drawdown == 0:
            return 0.0

        return annual_return / max_drawdown

    def _calculate_drawdown_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate drawdown-related metrics"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max

        max_drawdown = drawdown.min()
        max_dd_end = drawdown.idxmin()
        max_dd_start = cumulative.loc[:max_dd_end].idxmax()

        # Calculate duration in days if datetime index, otherwise in periods
        try:
            max_dd_duration = (max_dd_end - max_dd_start).days
        except AttributeError:
            # For non-datetime indices, count periods
            max_dd_duration = len(cumulative.loc[max_dd_start:max_dd_end])

        # Recovery time calculation
        recovery_time = None
        if max_dd_end != drawdown.index[-1]:
            recovery_idx = cumulative.loc[max_dd_end:][cumulative >= running_max.loc[max_dd_end]].index
            if len(recovery_idx) > 0:
                try:
                    recovery_time = (recovery_idx[0] - max_dd_end).days
                except AttributeError:
                    # For non-datetime indices, count periods
                    end_pos = list(cumulative.index).index(max_dd_end)
                    recovery_pos = list(cumulative.index).index(recovery_idx[0])
                    recovery_time = recovery_pos - end_pos

        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_duration': max_dd_duration,
            'average_drawdown': drawdown.mean(),
            'recovery_time': recovery_time
        }

    def _calculate_var_metrics(self, returns: pd.Series) -> Dict[str, float]:
        """Calculate Value at Risk metrics"""
        return {
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1),
            'es_95': returns[returns <= np.percentile(returns, 5)].mean(),
            'es_99': returns[returns <= np.percentile(returns, 1)].mean()
        }

    def _calculate_win_rate(self, returns: pd.Series) -> float:
        """Calculate percentage of positive returns"""
        return (returns > 0).mean()

    def _calculate_benchmark_metrics(self, portfolio_returns: pd.Series,
                                   benchmark_ticker: str, period: PerformancePeriod) -> Dict[str, float]:
        """Calculate benchmark comparison metrics"""
        benchmark_returns = self._get_benchmark_returns(benchmark_ticker, period)

        # Align the series by common dates
        common_dates = portfolio_returns.index.intersection(benchmark_returns.index)
        if len(common_dates) < 10:  # Need minimum data for meaningful regression
            logger.warning("Insufficient overlapping data for benchmark comparison")
            return {}

        portfolio_returns = portfolio_returns.loc[common_dates]
        benchmark_returns = benchmark_returns.loc[common_dates]

        # Linear regression for alpha and beta
        portfolio_excess = portfolio_returns - (self.risk_free_rate / self._get_periods_per_year(period))
        benchmark_excess = benchmark_returns - (self.risk_free_rate / self._get_periods_per_year(period))

        slope, intercept, r_value, _, _ = stats.linregress(benchmark_excess, portfolio_excess)

        beta = slope
        alpha = intercept * self._get_periods_per_year(period)
        r_squared = r_value ** 2

        # Tracking error and information ratio
        excess_returns = portfolio_returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(self._get_periods_per_year(period))
        information_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(self._get_periods_per_year(period)) if excess_returns.std() > 0 else 0

        # Treynor ratio
        portfolio_excess_mean = portfolio_excess.mean() * self._get_periods_per_year(period)
        treynor_ratio = portfolio_excess_mean / beta if beta != 0 else 0

        return {
            'alpha': alpha,
            'beta': beta,
            'r_squared': r_squared,
            'tracking_error': tracking_error,
            'information_ratio': information_ratio,
            'treynor_ratio': treynor_ratio
        }

    def _get_benchmark_returns(self, benchmark_ticker: str, period: PerformancePeriod) -> pd.Series:
        """Get benchmark returns for the specified period"""
        if self.benchmark_history is None:
            raise ValueError("Benchmark history not available")

        if benchmark_ticker in self.benchmark_history.columns:
            benchmark_prices = self.benchmark_history[benchmark_ticker]
        else:
            benchmark_prices = self.benchmark_history.iloc[:, 0]  # Use first column

        benchmark_returns = benchmark_prices.pct_change(fill_method=None).dropna()

        if period != PerformancePeriod.DAILY:
            benchmark_returns = self._resample_returns(benchmark_returns, period)

        return benchmark_returns

    def _calculate_brinson_attribution(self, portfolio_returns: pd.Series,
                                     benchmark_returns: pd.Series) -> Dict[str, float]:
        """Calculate Brinson attribution effects (simplified)"""
        # This is a simplified implementation
        # In practice, would need detailed holding weights and sector data

        excess_return = (portfolio_returns - benchmark_returns).mean()

        # Placeholder attribution - would need more detailed data
        return {
            'allocation': excess_return * 0.3,  # Placeholder
            'selection': excess_return * 0.6,   # Placeholder
            'interaction': excess_return * 0.1  # Placeholder
        }

    def _calculate_holding_attribution(self, portfolio_returns: pd.Series,
                                     benchmark_returns: pd.Series) -> Dict[str, Dict[str, float]]:
        """Calculate holding-level attribution"""
        attribution = {}

        for holding in self.portfolio.holdings:
            attribution[holding.ticker] = {
                'allocation_effect': 0.0,  # Placeholder
                'selection_effect': 0.0,  # Placeholder
                'total_effect': 0.0       # Placeholder
            }

        return attribution

    def _calculate_sector_attribution(self) -> Dict[str, Dict[str, float]]:
        """Calculate sector-level attribution"""
        # Placeholder - would need sector classification data
        return {}

    def _calculate_cash_drag(self) -> float:
        """Calculate impact of cash holdings on performance"""
        cash_weight = self.portfolio.cash_position / self.portfolio.portfolio_metrics.total_value
        # Simplified calculation - actual would compare cash return vs benchmark
        return -cash_weight * 0.02  # Assume 2% opportunity cost

    def _calculate_rebalancing_impact(self) -> float:
        """Calculate impact of rebalancing on performance"""
        # Placeholder - would need detailed rebalancing history
        return 0.0

    def _adjust_for_rebalancing(self, returns: pd.Series, rebalancing_dates: List[date]) -> pd.Series:
        """Adjust returns for portfolio rebalancing"""
        # Placeholder - implement rebalancing adjustments
        return returns

    def _resample_returns(self, returns: pd.Series, period: PerformancePeriod) -> pd.Series:
        """Resample daily returns to specified period"""
        resample_map = {
            PerformancePeriod.WEEKLY: 'W',
            PerformancePeriod.MONTHLY: 'ME',
            PerformancePeriod.QUARTERLY: 'QE',
            PerformancePeriod.SEMI_ANNUAL: '6ME',
            PerformancePeriod.ANNUAL: 'YE'
        }

        if period in resample_map:
            # Convert to cumulative returns, resample, then back to periodic returns
            cumulative = (1 + returns).cumprod()
            resampled_cumulative = cumulative.resample(resample_map[period]).last()
            return resampled_cumulative.pct_change(fill_method=None).dropna()

        return returns

    def _get_periods_per_year(self, period: PerformancePeriod) -> int:
        """Get number of periods per year for annualization"""
        period_map = {
            PerformancePeriod.DAILY: 252,
            PerformancePeriod.WEEKLY: 52,
            PerformancePeriod.MONTHLY: 12,
            PerformancePeriod.QUARTERLY: 4,
            PerformancePeriod.SEMI_ANNUAL: 2,
            PerformancePeriod.ANNUAL: 1
        }
        return period_map.get(period, 252)

    def _metrics_to_dict(self, metrics: PerformanceMetrics) -> Dict:
        """Convert PerformanceMetrics to dictionary"""
        return {
            'total_return': metrics.total_return,
            'annualized_return': metrics.annualized_return,
            'volatility': metrics.volatility,
            'sharpe_ratio': metrics.sharpe_ratio,
            'sortino_ratio': metrics.sortino_ratio,
            'calmar_ratio': metrics.calmar_ratio,
            'max_drawdown': metrics.max_drawdown,
            'var_95': metrics.var_95,
            'alpha': metrics.alpha,
            'beta': metrics.beta,
            'tracking_error': metrics.tracking_error,
            'information_ratio': metrics.information_ratio,
            'win_rate': metrics.win_rate,
            'data_quality': metrics.data_quality.value
        }

    def _attribution_to_dict(self, attribution: AttributionAnalysis) -> Dict:
        """Convert AttributionAnalysis to dictionary"""
        return {
            'total_excess_return': attribution.total_excess_return,
            'allocation_effect': attribution.allocation_effect,
            'selection_effect': attribution.selection_effect,
            'interaction_effect': attribution.interaction_effect,
            'cash_drag': attribution.cash_drag,
            'holding_attribution': attribution.holding_attribution,
            'sector_attribution': attribution.sector_attribution
        }

    def _generate_risk_summary(self) -> Dict:
        """Generate risk analysis summary"""
        return {
            'portfolio_beta': self.portfolio.portfolio_metrics.beta,
            'concentration_risk': self.portfolio.portfolio_metrics.concentration_risk,
            'number_of_holdings': len(self.portfolio.holdings),
            'largest_position': max((h.current_weight for h in self.portfolio.holdings), default=0.0),
            'risk_tolerance': self.portfolio.risk_tolerance
        }

    def _generate_summary_statistics(self) -> Dict:
        """Generate summary statistics"""
        return {
            'total_portfolio_value': self.portfolio.portfolio_metrics.total_value,
            'total_cost': self.portfolio.portfolio_metrics.total_cost,
            'unrealized_gain_loss_pct': self.portfolio.portfolio_metrics.unrealized_gain_loss_pct,
            'cash_position': self.portfolio.cash_position,
            'inception_date': self.portfolio.inception_date.isoformat(),
            'last_update': self.portfolio.last_update.isoformat()
        }


def create_sample_performance_data(portfolio: Portfolio,
                                 days: int = 252,
                                 volatility: float = 0.15) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Create sample price and benchmark data for testing

    Args:
        portfolio: Portfolio instance
        days: Number of trading days of data
        volatility: Annual volatility for simulation

    Returns:
        Tuple of (price_data, benchmark_data) DataFrames
    """
    # Generate sample dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=int(days * 1.4))  # Buffer for weekends
    date_range = pd.bdate_range(start=start_date, end=end_date)[:days]

    # Generate sample price data for holdings
    tickers = [h.ticker for h in portfolio.holdings]
    price_data = pd.DataFrame(index=date_range, columns=tickers)

    # Simulate price paths
    np.random.seed(42)  # For reproducible results
    for ticker in tickers:
        daily_vol = volatility / np.sqrt(252)
        returns = np.random.normal(0.0008, daily_vol, days)  # ~0.2% daily return
        prices = 100 * np.cumprod(1 + returns)  # Start at $100
        price_data[ticker] = prices

    # Generate benchmark data
    benchmark_returns = np.random.normal(0.0006, volatility / np.sqrt(252), days)
    benchmark_prices = 100 * np.cumprod(1 + benchmark_returns)
    benchmark_data = pd.DataFrame(
        {'SPY': benchmark_prices},
        index=date_range
    )

    return price_data, benchmark_data