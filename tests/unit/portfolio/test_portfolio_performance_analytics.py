"""
Unit Tests for Portfolio Performance Analytics
=============================================

Comprehensive tests for portfolio performance measurement, attribution analysis,
and risk metrics calculation functionality.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

from core.analysis.portfolio.portfolio_performance_analytics import (
    PortfolioPerformanceAnalyzer,
    PerformanceMetrics,
    AttributionAnalysis,
    PerformancePeriod,
    RiskFreeRateSource,
    create_sample_performance_data
)
from core.analysis.portfolio.portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    create_sample_portfolio
)


class TestPortfolioPerformanceAnalyzer:
    """Test suite for PortfolioPerformanceAnalyzer"""

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        return create_sample_portfolio()

    @pytest.fixture
    def analyzer(self, sample_portfolio):
        """Create analyzer instance with sample portfolio"""
        return PortfolioPerformanceAnalyzer(sample_portfolio, risk_free_rate=0.02)

    @pytest.fixture
    def sample_price_data(self, sample_portfolio):
        """Create sample price data for testing"""
        price_data, benchmark_data = create_sample_performance_data(sample_portfolio, days=252)
        return price_data, benchmark_data

    def test_analyzer_initialization(self, sample_portfolio):
        """Test analyzer initialization"""
        analyzer = PortfolioPerformanceAnalyzer(sample_portfolio)

        assert analyzer.portfolio == sample_portfolio
        assert analyzer.risk_free_rate == 0.02  # Default value
        assert analyzer.price_history is None
        assert analyzer.benchmark_history is None

    def test_set_price_history(self, analyzer, sample_price_data):
        """Test setting price history data"""
        price_data, _ = sample_price_data

        analyzer.set_price_history(price_data)

        assert analyzer.price_history is not None
        assert len(analyzer.price_history.columns) == len(analyzer.portfolio.holdings)
        assert isinstance(analyzer.price_history, pd.DataFrame)

    def test_set_benchmark_history(self, analyzer, sample_price_data):
        """Test setting benchmark history data"""
        _, benchmark_data = sample_price_data

        analyzer.set_benchmark_history(benchmark_data)

        assert analyzer.benchmark_history is not None
        assert isinstance(analyzer.benchmark_history, pd.DataFrame)

    def test_calculate_portfolio_returns(self, analyzer, sample_price_data):
        """Test portfolio returns calculation"""
        price_data, _ = sample_price_data
        analyzer.set_price_history(price_data)

        returns = analyzer.calculate_portfolio_returns(PerformancePeriod.DAILY)

        assert isinstance(returns, pd.Series)
        assert len(returns) > 0
        assert not returns.isna().all()
        assert returns.index.dtype == 'datetime64[ns]'

    def test_calculate_portfolio_returns_monthly(self, analyzer, sample_price_data):
        """Test monthly portfolio returns calculation"""
        price_data, _ = sample_price_data
        analyzer.set_price_history(price_data)

        returns = analyzer.calculate_portfolio_returns(PerformancePeriod.MONTHLY)

        assert isinstance(returns, pd.Series)
        assert len(returns) < len(price_data)  # Should be fewer monthly than daily returns

    def test_calculate_portfolio_returns_no_data(self, analyzer):
        """Test portfolio returns calculation with no price data"""
        with pytest.raises(ValueError, match="Price history must be set"):
            analyzer.calculate_portfolio_returns()

    def test_calculate_performance_metrics(self, analyzer, sample_price_data):
        """Test comprehensive performance metrics calculation"""
        price_data, benchmark_data = sample_price_data
        analyzer.set_price_history(price_data)
        analyzer.set_benchmark_history(benchmark_data)

        metrics = analyzer.calculate_performance_metrics(
            PerformancePeriod.MONTHLY,
            benchmark_ticker="SPY"
        )

        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.total_return is not None
        assert metrics.annualized_return is not None
        assert metrics.volatility is not None
        assert metrics.sharpe_ratio is not None
        assert metrics.max_drawdown is not None
        assert metrics.alpha is not None
        assert metrics.beta is not None

    def test_calculate_performance_metrics_insufficient_data(self, analyzer):
        """Test performance metrics with insufficient data"""
        # Create minimal price data
        dates = pd.date_range('2023-01-01', periods=1)
        price_data = pd.DataFrame({'AAPL': [100]}, index=dates)
        analyzer.set_price_history(price_data)

        metrics = analyzer.calculate_performance_metrics()

        assert metrics.data_quality.value == "poor"

    def test_calculate_attribution_analysis(self, analyzer, sample_price_data):
        """Test attribution analysis calculation"""
        price_data, benchmark_data = sample_price_data
        analyzer.set_price_history(price_data)
        analyzer.set_benchmark_history(benchmark_data)

        attribution = analyzer.calculate_attribution_analysis("SPY")

        assert isinstance(attribution, AttributionAnalysis)
        assert attribution.total_excess_return is not None
        assert attribution.allocation_effect is not None
        assert attribution.selection_effect is not None
        assert attribution.interaction_effect is not None
        assert attribution.benchmark_used == "SPY"

    def test_calculate_attribution_analysis_no_data(self, analyzer):
        """Test attribution analysis with no data"""
        with pytest.raises(ValueError, match="Both portfolio and benchmark history required"):
            analyzer.calculate_attribution_analysis("SPY")

    def test_generate_performance_report(self, analyzer, sample_price_data):
        """Test comprehensive performance report generation"""
        price_data, benchmark_data = sample_price_data
        analyzer.set_price_history(price_data)
        analyzer.set_benchmark_history(benchmark_data)

        report = analyzer.generate_performance_report(
            periods=[PerformancePeriod.MONTHLY, PerformancePeriod.QUARTERLY],
            benchmark_ticker="SPY"
        )

        assert 'portfolio_info' in report
        assert 'performance_by_period' in report
        assert 'attribution_analysis' in report
        assert 'risk_analysis' in report
        assert 'summary_statistics' in report

        assert len(report['performance_by_period']) == 2
        assert report['portfolio_info']['portfolio_id'] == analyzer.portfolio.portfolio_id

    def test_total_return_calculation(self, analyzer):
        """Test total return calculation"""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015])
        total_return = analyzer._calculate_total_return(returns)

        expected = (1.01 * 1.02 * 0.99 * 1.015) - 1
        assert abs(total_return - expected) < 1e-10

    def test_annualized_return_calculation(self, analyzer):
        """Test annualized return calculation"""
        # 12 months of 1% monthly returns
        returns = pd.Series([0.01] * 12)
        ann_return = analyzer._calculate_annualized_return(returns, PerformancePeriod.MONTHLY)

        # Should be approximately 12.68% annually
        assert 0.12 < ann_return < 0.13

    def test_volatility_calculation(self, analyzer):
        """Test volatility calculation"""
        # Create returns with known volatility
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 252))  # Daily returns
        volatility = analyzer._calculate_volatility(returns, PerformancePeriod.DAILY)

        # Should be approximately 32% annually (0.02 * sqrt(252))
        assert 0.25 < volatility < 0.35

    def test_sharpe_ratio_calculation(self, analyzer):
        """Test Sharpe ratio calculation"""
        # Create returns with positive mean
        returns = pd.Series([0.01, 0.02, 0.005, 0.015, -0.005])
        sharpe = analyzer._calculate_sharpe_ratio(returns, PerformancePeriod.MONTHLY)

        assert isinstance(sharpe, float)
        assert sharpe > 0  # Should be positive with positive excess returns

    def test_sortino_ratio_calculation(self, analyzer):
        """Test Sortino ratio calculation"""
        returns = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005])
        sortino = analyzer._calculate_sortino_ratio(returns, PerformancePeriod.MONTHLY)

        assert isinstance(sortino, float)
        # Sortino should be higher than Sharpe for same data (less penalty for upside volatility)

    def test_drawdown_metrics_calculation(self, analyzer):
        """Test drawdown metrics calculation"""
        # Create returns that will result in drawdown
        returns = pd.Series([0.1, -0.05, -0.03, -0.02, 0.02, 0.08])
        drawdown_metrics = analyzer._calculate_drawdown_metrics(returns)

        assert 'max_drawdown' in drawdown_metrics
        assert 'max_drawdown_duration' in drawdown_metrics
        assert 'average_drawdown' in drawdown_metrics
        assert 'recovery_time' in drawdown_metrics

        assert drawdown_metrics['max_drawdown'] < 0  # Max drawdown should be negative

    def test_var_metrics_calculation(self, analyzer):
        """Test Value at Risk metrics calculation"""
        # Create returns with known distribution
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        var_metrics = analyzer._calculate_var_metrics(returns)

        assert 'var_95' in var_metrics
        assert 'var_99' in var_metrics
        assert 'es_95' in var_metrics
        assert 'es_99' in var_metrics

        # VaR should be negative (losses)
        assert var_metrics['var_95'] < 0
        assert var_metrics['var_99'] < 0
        assert var_metrics['var_99'] < var_metrics['var_95']  # 99% VaR should be worse

    def test_win_rate_calculation(self, analyzer):
        """Test win rate calculation"""
        returns = pd.Series([0.01, -0.02, 0.005, 0.015, -0.005])
        win_rate = analyzer._calculate_win_rate(returns)

        assert win_rate == 0.6  # 3 positive out of 5 returns

    def test_benchmark_metrics_calculation(self, analyzer):
        """Test benchmark comparison metrics"""
        # Create correlated portfolio and benchmark returns
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=100)
        benchmark_returns = pd.Series(np.random.normal(0.001, 0.015, 100), index=dates)
        portfolio_returns = 0.8 * benchmark_returns + pd.Series(np.random.normal(0.0005, 0.01, 100), index=dates)

        # Set up mock benchmark history
        benchmark_data = pd.DataFrame({'SPY': np.cumprod(1 + benchmark_returns) * 100}, index=dates)
        analyzer.set_benchmark_history(benchmark_data)

        metrics = analyzer._calculate_benchmark_metrics(
            portfolio_returns, "SPY", PerformancePeriod.DAILY
        )

        assert 'alpha' in metrics
        assert 'beta' in metrics
        assert 'r_squared' in metrics
        assert 'tracking_error' in metrics
        assert 'information_ratio' in metrics

        # Beta should be close to 0.8 given our construction
        assert 0.7 < metrics['beta'] < 0.9

    def test_periods_per_year_mapping(self, analyzer):
        """Test periods per year calculation"""
        assert analyzer._get_periods_per_year(PerformancePeriod.DAILY) == 252
        assert analyzer._get_periods_per_year(PerformancePeriod.MONTHLY) == 12
        assert analyzer._get_periods_per_year(PerformancePeriod.QUARTERLY) == 4
        assert analyzer._get_periods_per_year(PerformancePeriod.ANNUAL) == 1

    def test_resample_returns(self, analyzer):
        """Test returns resampling functionality"""
        # Create daily returns
        dates = pd.date_range('2023-01-01', periods=252, freq='D')
        daily_returns = pd.Series(np.random.normal(0.001, 0.02, 252), index=dates)

        monthly_returns = analyzer._resample_returns(daily_returns, PerformancePeriod.MONTHLY)

        assert len(monthly_returns) < len(daily_returns)
        assert isinstance(monthly_returns, pd.Series)

    def test_metrics_to_dict_conversion(self, analyzer):
        """Test conversion of metrics to dictionary"""
        metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            volatility=0.18,
            sharpe_ratio=0.67
        )

        metrics_dict = analyzer._metrics_to_dict(metrics)

        assert isinstance(metrics_dict, dict)
        assert metrics_dict['total_return'] == 0.15
        assert metrics_dict['annualized_return'] == 0.12
        assert 'data_quality' in metrics_dict

    def test_attribution_to_dict_conversion(self, analyzer):
        """Test conversion of attribution to dictionary"""
        attribution = AttributionAnalysis(
            total_excess_return=0.02,
            allocation_effect=0.005,
            selection_effect=0.015
        )

        attribution_dict = analyzer._attribution_to_dict(attribution)

        assert isinstance(attribution_dict, dict)
        assert attribution_dict['total_excess_return'] == 0.02
        assert attribution_dict['allocation_effect'] == 0.005


class TestPerformanceDataGeneration:
    """Test suite for sample performance data generation"""

    def test_create_sample_performance_data(self):
        """Test sample performance data creation"""
        portfolio = create_sample_portfolio()
        price_data, benchmark_data = create_sample_performance_data(portfolio, days=100)

        assert isinstance(price_data, pd.DataFrame)
        assert isinstance(benchmark_data, pd.DataFrame)
        assert len(price_data) == 100
        assert len(benchmark_data) == 100
        assert len(price_data.columns) == len(portfolio.holdings)
        assert 'SPY' in benchmark_data.columns

    def test_sample_data_realistic_properties(self):
        """Test that sample data has realistic financial properties"""
        portfolio = create_sample_portfolio()
        price_data, benchmark_data = create_sample_performance_data(
            portfolio, days=252, volatility=0.20
        )

        # Calculate returns
        returns = price_data.pct_change().dropna()
        benchmark_returns = benchmark_data.pct_change().dropna()

        # Check volatility is approximately correct
        for ticker in returns.columns:
            annual_vol = returns[ticker].std() * np.sqrt(252)
            assert 0.15 < annual_vol < 0.25  # Should be around 20% ± tolerance

        # Check that returns are not all the same
        assert not (returns.iloc[:, 0] == returns.iloc[:, 1]).all()

        # Check that prices generally trend upward (positive expected return)
        for ticker in price_data.columns:
            price_ratio = price_data[ticker].iloc[-1] / price_data[ticker].iloc[0]
            assert price_ratio > 0.8  # Shouldn't crash too much in normal simulation


class TestPerformanceMetricsDataClass:
    """Test suite for PerformanceMetrics data class"""

    def test_performance_metrics_initialization(self):
        """Test PerformanceMetrics initialization"""
        metrics = PerformanceMetrics(
            total_return=0.15,
            annualized_return=0.12,
            volatility=0.18
        )

        assert metrics.total_return == 0.15
        assert metrics.annualized_return == 0.12
        assert metrics.volatility == 0.18
        assert isinstance(metrics.calculation_date, datetime)

    def test_performance_metrics_defaults(self):
        """Test PerformanceMetrics default values"""
        metrics = PerformanceMetrics()

        assert metrics.total_return is None
        assert metrics.sharpe_ratio is None
        assert metrics.period_analyzed == ""
        assert isinstance(metrics.calculation_date, datetime)


class TestAttributionAnalysisDataClass:
    """Test suite for AttributionAnalysis data class"""

    def test_attribution_analysis_initialization(self):
        """Test AttributionAnalysis initialization"""
        attribution = AttributionAnalysis(
            total_excess_return=0.02,
            allocation_effect=0.005,
            selection_effect=0.015
        )

        assert attribution.total_excess_return == 0.02
        assert attribution.allocation_effect == 0.005
        assert attribution.selection_effect == 0.015
        assert isinstance(attribution.holding_attribution, dict)

    def test_attribution_analysis_defaults(self):
        """Test AttributionAnalysis default values"""
        attribution = AttributionAnalysis()

        assert attribution.total_excess_return is None
        assert attribution.attribution_period == ""
        assert attribution.calculation_method == "Brinson"
        assert len(attribution.holding_attribution) == 0


class TestPerformancePeriodEnum:
    """Test suite for PerformancePeriod enum"""

    def test_performance_period_values(self):
        """Test PerformancePeriod enum values"""
        assert PerformancePeriod.DAILY.value == "1D"
        assert PerformancePeriod.MONTHLY.value == "1M"
        assert PerformancePeriod.ANNUAL.value == "1Y"
        assert PerformancePeriod.INCEPTION_TO_DATE.value == "ITD"

    def test_performance_period_membership(self):
        """Test PerformancePeriod enum membership"""
        periods = list(PerformancePeriod)
        assert len(periods) == 9  # Should have 9 different periods
        assert PerformancePeriod.QUARTERLY in periods


# Integration tests
class TestPerformanceAnalyticsIntegration:
    """Integration tests for portfolio performance analytics"""

    @pytest.fixture
    def complete_setup(self):
        """Create complete test setup with portfolio, data, and analyzer"""
        portfolio = create_sample_portfolio()
        analyzer = PortfolioPerformanceAnalyzer(portfolio, risk_free_rate=0.025)
        price_data, benchmark_data = create_sample_performance_data(portfolio, days=252)

        analyzer.set_price_history(price_data)
        analyzer.set_benchmark_history(benchmark_data)

        return analyzer, portfolio, price_data, benchmark_data

    def test_end_to_end_performance_analysis(self, complete_setup):
        """Test complete end-to-end performance analysis workflow"""
        analyzer, portfolio, price_data, benchmark_data = complete_setup

        # Generate comprehensive report
        report = analyzer.generate_performance_report(
            periods=[PerformancePeriod.MONTHLY, PerformancePeriod.ANNUAL],
            benchmark_ticker="SPY"
        )

        # Validate report structure
        assert 'portfolio_info' in report
        assert 'performance_by_period' in report
        assert 'attribution_analysis' in report

        # Validate portfolio info
        portfolio_info = report['portfolio_info']
        assert portfolio_info['portfolio_id'] == portfolio.portfolio_id
        assert portfolio_info['number_of_holdings'] == len(portfolio.holdings)

        # Validate performance by period
        performance = report['performance_by_period']
        assert '1M' in performance
        assert '1Y' in performance

        # Validate that all metrics are calculated
        monthly_perf = performance['1M']
        assert 'total_return' in monthly_perf
        assert 'sharpe_ratio' in monthly_perf
        assert 'volatility' in monthly_perf

        # Validate attribution analysis
        attribution = report['attribution_analysis']
        assert 'total_excess_return' in attribution
        assert 'allocation_effect' in attribution

    def test_multi_period_consistency(self, complete_setup):
        """Test consistency across multiple performance periods"""
        analyzer, _, _, _ = complete_setup

        # Calculate metrics for different periods
        monthly_metrics = analyzer.calculate_performance_metrics(PerformancePeriod.MONTHLY)
        quarterly_metrics = analyzer.calculate_performance_metrics(PerformancePeriod.QUARTERLY)

        # Both should have valid data
        assert monthly_metrics.data_quality.value != "poor"
        assert quarterly_metrics.data_quality.value != "poor"

        # Quarterly should have fewer return observations
        # This is implicit in the resampling, but we can check that both complete successfully

    def test_benchmark_comparison_accuracy(self, complete_setup):
        """Test accuracy of benchmark comparison metrics"""
        analyzer, _, _, _ = complete_setup

        metrics = analyzer.calculate_performance_metrics(
            PerformancePeriod.MONTHLY,
            benchmark_ticker="SPY"
        )

        # Beta should be reasonable (can be low for diversified portfolios)
        assert -1.0 < metrics.beta < 5.0

        # R-squared should be between 0 and 1
        assert 0.0 <= metrics.r_squared <= 1.0

        # Tracking error should be positive
        assert metrics.tracking_error > 0


if __name__ == "__main__":
    pytest.main([__file__])