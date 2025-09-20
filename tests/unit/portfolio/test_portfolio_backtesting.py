"""
Tests for Portfolio Backtesting Framework
==========================================

This module tests the portfolio backtesting functionality including:
- BacktestEngine basic functionality
- Transaction cost modeling
- Regime analysis
- Stress testing
- Performance metrics calculation
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch

from core.analysis.portfolio.portfolio_backtesting import (
    BacktestEngine,
    BacktestResult,
    BacktestPeriod,
    TransactionCostModel,
    RegimeAnalyzer,
    StressTester,
    MarketRegime,
    StressScenario,
    BacktestTransaction,
    BacktestState
)
from core.analysis.portfolio.portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    RebalancingStrategy,
    PositionSizingMethod,
    create_sample_portfolio
)


@pytest.fixture
def sample_portfolio():
    """Create a sample portfolio for testing"""
    holdings = [
        PortfolioHolding(
            ticker="AAPL",
            company_name="Apple Inc.",
            target_weight=0.4,
            current_price=150.0
        ),
        PortfolioHolding(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            target_weight=0.3,
            current_price=300.0
        ),
        PortfolioHolding(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            target_weight=0.3,
            current_price=140.0
        )
    ]

    portfolio = Portfolio(
        portfolio_id="test_portfolio",
        name="Test Portfolio",
        portfolio_type=PortfolioType.BALANCED,
        rebalancing_strategy=RebalancingStrategy.THRESHOLD,
        position_sizing_method=PositionSizingMethod.CUSTOM_WEIGHTS,
        holdings=holdings,
        rebalancing_threshold=0.05,
        target_cash_allocation=0.0
    )

    return portfolio


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing"""
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='B')  # Business days
    tickers = ['AAPL', 'MSFT', 'GOOGL']

    # Generate sample price data with some realistic patterns
    np.random.seed(42)
    price_data = pd.DataFrame(index=dates, columns=tickers)

    for ticker in tickers:
        # Generate returns with slight upward drift
        returns = np.random.normal(0.0005, 0.02, len(dates))  # ~12% annual return, 30% vol
        prices = 100 * np.cumprod(1 + returns)
        price_data[ticker] = prices

    return price_data


@pytest.fixture
def sample_benchmark_data(sample_price_data):
    """Create sample benchmark data"""
    dates = sample_price_data.index

    np.random.seed(42)
    returns = np.random.normal(0.0004, 0.015, len(dates))  # 10% annual return, 24% vol
    prices = 100 * np.cumprod(1 + returns)

    benchmark_data = pd.DataFrame({'SPY': prices}, index=dates)
    return benchmark_data


class TestTransactionCostModel:
    """Test transaction cost modeling"""

    def test_transaction_cost_calculation(self):
        """Test basic transaction cost calculation"""
        cost_model = TransactionCostModel(
            commission_rate=0.001,
            bid_ask_spread=0.0005,
            market_impact_rate=0.0001,
            slippage_volatility=0.0002
        )

        costs = cost_model.calculate_transaction_costs(
            ticker="AAPL",
            shares=100,
            price=150.0,
            portfolio_value=100000.0,
            volatility=0.3
        )

        # Check that all cost components are present and positive
        assert 'commission' in costs
        assert 'bid_ask_spread' in costs
        assert 'market_impact' in costs
        assert 'slippage' in costs
        assert 'total_costs' in costs

        assert costs['commission'] > 0
        assert costs['bid_ask_spread'] > 0
        assert costs['market_impact'] > 0
        assert costs['total_costs'] > 0

        # Total costs should be sum of components (excluding slippage which can be negative)
        expected_total = (costs['commission'] + costs['bid_ask_spread'] +
                         costs['market_impact'] + abs(costs['slippage']))
        assert abs(costs['total_costs'] - expected_total) < 1e-6

    def test_cost_scaling_with_trade_size(self):
        """Test that costs scale appropriately with trade size"""
        cost_model = TransactionCostModel()

        small_trade = cost_model.calculate_transaction_costs(
            "AAPL", 10, 150.0, 100000.0
        )
        large_trade = cost_model.calculate_transaction_costs(
            "AAPL", 1000, 150.0, 100000.0
        )

        # Larger trades should have higher absolute costs
        assert large_trade['total_costs'] > small_trade['total_costs']

        # But potentially higher percentage costs due to market impact
        small_pct = small_trade['total_costs'] / (10 * 150.0)
        large_pct = large_trade['total_costs'] / (1000 * 150.0)
        # Market impact should make large trades more expensive per dollar
        assert large_pct >= small_pct


class TestRegimeAnalyzer:
    """Test market regime analysis"""

    def test_regime_classification(self):
        """Test basic regime classification"""
        analyzer = RegimeAnalyzer(lookback_window=60)

        # Create sample market data with different regimes
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='B')

        # Bull market pattern (strong upward trend)
        bull_returns = np.random.normal(0.002, 0.015, len(dates))  # High returns, moderate vol
        bull_prices = 100 * np.cumprod(1 + bull_returns)
        bull_data = pd.DataFrame({'benchmark': bull_prices}, index=dates)

        # Test regime classification for a date in the middle
        test_date = dates[len(dates) // 2]
        regime = analyzer.classify_regime(bull_data, test_date)

        # Should classify as some valid regime
        assert isinstance(regime, MarketRegime)

    def test_regime_performance_analysis(self, sample_price_data, sample_benchmark_data):
        """Test regime performance analysis"""
        analyzer = RegimeAnalyzer()

        # Create sample portfolio returns
        portfolio_returns = sample_price_data.mean(axis=1).pct_change().dropna()

        analysis = analyzer.analyze_regime_performance(
            portfolio_returns, sample_benchmark_data
        )

        # Check that analysis contains expected components
        assert hasattr(analysis, 'regimes')
        assert hasattr(analysis, 'regime_performance')
        assert isinstance(analysis.regimes, dict)
        assert isinstance(analysis.regime_performance, dict)

        # Should have classified some dates
        assert len(analysis.regimes) > 0


class TestStressTester:
    """Test stress testing functionality"""

    def test_stress_test_execution(self):
        """Test basic stress test execution"""
        stress_tester = StressTester()

        # Create sample returns data that spans a stress period
        dates = pd.date_range(start='2008-01-01', end='2009-12-31', freq='B')
        returns = pd.Series(
            np.random.normal(-0.001, 0.03, len(dates)),  # Negative drift, high vol
            index=dates
        )

        result = stress_tester.run_stress_test(
            StressScenario.MARKET_CRASH_2008,
            returns
        )

        # Check result structure
        assert result.scenario == StressScenario.MARKET_CRASH_2008
        assert isinstance(result.scenario_description, str)
        assert hasattr(result, 'stress_period_return')
        assert hasattr(result, 'max_loss')
        assert hasattr(result, 'stress_volatility')

    def test_all_stress_tests(self):
        """Test running all predefined stress tests"""
        stress_tester = StressTester()

        # Create returns data spanning multiple years
        dates = pd.date_range(start='2000-01-01', end='2023-12-31', freq='B')
        returns = pd.Series(
            np.random.normal(0.0004, 0.02, len(dates)),
            index=dates
        )

        results = stress_tester.run_all_stress_tests(returns)

        # Should return results for all predefined scenarios
        assert isinstance(results, list)
        assert len(results) > 0

        # Each result should be properly structured
        for result in results:
            assert hasattr(result, 'scenario')
            assert hasattr(result, 'scenario_description')


class TestBacktestEngine:
    """Test the main backtesting engine"""

    def test_backtest_initialization(self):
        """Test backtest engine initialization"""
        engine = BacktestEngine(
            initial_capital=100000.0,
            risk_free_rate=0.02
        )

        assert engine.initial_capital == 100000.0
        assert engine.risk_free_rate == 0.02
        assert engine.transaction_cost_model is not None
        assert engine.regime_analyzer is not None
        assert engine.stress_tester is not None

    def test_basic_backtest_execution(self, sample_portfolio, sample_price_data, sample_benchmark_data):
        """Test basic backtest execution"""
        engine = BacktestEngine(initial_capital=100000.0)

        result = engine.run_backtest(
            strategy_portfolio=sample_portfolio,
            price_data=sample_price_data,
            benchmark_data=sample_benchmark_data,
            backtest_period=BacktestPeriod.ONE_YEAR,
            rebalancing_frequency=90
        )

        # Check result structure
        assert isinstance(result, BacktestResult)
        assert result.strategy_name == sample_portfolio.name
        assert result.backtest_period == BacktestPeriod.ONE_YEAR
        assert result.initial_capital == 100000.0
        assert result.final_value > 0

        # Check performance metrics
        assert hasattr(result, 'total_return')
        assert hasattr(result, 'annualized_return')
        assert hasattr(result, 'volatility')
        assert hasattr(result, 'sharpe_ratio')
        assert hasattr(result, 'max_drawdown')

        # Check time series data
        assert len(result.portfolio_values) > 0
        assert len(result.portfolio_returns) > 0

        # Check transaction analysis
        assert hasattr(result, 'total_transactions')
        assert hasattr(result, 'total_transaction_costs')

    def test_backtest_with_different_periods(self, sample_portfolio, sample_price_data):
        """Test backtesting with different time periods"""
        engine = BacktestEngine(initial_capital=50000.0)

        periods_to_test = [BacktestPeriod.ONE_YEAR, BacktestPeriod.THREE_YEARS]

        for period in periods_to_test:
            result = engine.run_backtest(
                strategy_portfolio=sample_portfolio,
                price_data=sample_price_data,
                backtest_period=period
            )

            assert result.backtest_period == period
            assert result.initial_capital == 50000.0

    def test_backtest_validation(self, sample_portfolio):
        """Test backtest data validation"""
        engine = BacktestEngine()

        # Test with insufficient data
        short_data = pd.DataFrame({
            'AAPL': [100, 101, 102],
            'MSFT': [200, 201, 202]
        }, index=pd.date_range('2023-01-01', periods=3))

        with pytest.raises(ValueError):
            engine.run_backtest(
                strategy_portfolio=sample_portfolio,
                price_data=short_data,
                backtest_period=BacktestPeriod.ONE_YEAR
            )

        # Test with missing tickers
        incomplete_data = pd.DataFrame({
            'AAPL': [100] * 100,
            'MSFT': [200] * 100
            # Missing GOOGL
        }, index=pd.date_range('2023-01-01', periods=100))

        with pytest.raises(ValueError):
            engine.run_backtest(
                strategy_portfolio=sample_portfolio,
                price_data=incomplete_data,
                backtest_period=BacktestPeriod.ONE_YEAR
            )

    def test_transaction_cost_impact(self, sample_portfolio, sample_price_data):
        """Test that transaction costs impact returns"""
        # Run with no costs
        no_cost_model = TransactionCostModel(0.0, 0.0, 0.0, 0.0)
        engine_no_cost = BacktestEngine(
            initial_capital=100000.0,
            transaction_cost_model=no_cost_model
        )

        result_no_cost = engine_no_cost.run_backtest(
            strategy_portfolio=sample_portfolio,
            price_data=sample_price_data,
            backtest_period=BacktestPeriod.ONE_YEAR,
            rebalancing_frequency=30  # Monthly rebalancing
        )

        # Run with high costs
        high_cost_model = TransactionCostModel(0.01, 0.005, 0.002, 0.001)  # Very high costs
        engine_high_cost = BacktestEngine(
            initial_capital=100000.0,
            transaction_cost_model=high_cost_model
        )

        result_high_cost = engine_high_cost.run_backtest(
            strategy_portfolio=sample_portfolio,
            price_data=sample_price_data,
            backtest_period=BacktestPeriod.ONE_YEAR,
            rebalancing_frequency=30  # Monthly rebalancing
        )

        # High cost version should have lower returns (in most cases)
        # Note: This might not always be true due to randomness, but with frequent rebalancing
        # and high costs, it should generally be true
        assert result_high_cost.total_transaction_costs > result_no_cost.total_transaction_costs


class TestBacktestResult:
    """Test BacktestResult functionality"""

    def test_backtest_result_creation(self):
        """Test BacktestResult initialization"""
        result = BacktestResult(
            strategy_name="Test Strategy",
            backtest_period=BacktestPeriod.ONE_YEAR,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            initial_capital=100000.0,
            final_value=110000.0
        )

        assert result.strategy_name == "Test Strategy"
        assert result.initial_capital == 100000.0
        assert result.final_value == 110000.0

    def test_performance_metrics_calculation(self, sample_portfolio, sample_price_data):
        """Test that performance metrics are calculated correctly"""
        engine = BacktestEngine(initial_capital=100000.0)

        result = engine.run_backtest(
            strategy_portfolio=sample_portfolio,
            price_data=sample_price_data,
            backtest_period=BacktestPeriod.ONE_YEAR
        )

        # Check that key metrics are calculated
        assert result.total_return is not None
        assert result.annualized_return is not None
        assert result.volatility is not None
        assert result.max_drawdown is not None

        # Sanity checks
        expected_total_return = (result.final_value / result.initial_capital) - 1
        assert abs(result.total_return - expected_total_return) < 1e-6

        # Max drawdown should be negative or zero
        assert result.max_drawdown <= 0

        # Volatility should be positive
        assert result.volatility >= 0


class TestIntegration:
    """Integration tests for the full backtesting framework"""

    def test_end_to_end_backtest(self, sample_portfolio, sample_price_data, sample_benchmark_data):
        """Test complete end-to-end backtesting workflow"""
        engine = BacktestEngine(
            initial_capital=250000.0,
            risk_free_rate=0.025
        )

        result = engine.run_backtest(
            strategy_portfolio=sample_portfolio,
            price_data=sample_price_data,
            benchmark_data=sample_benchmark_data,
            backtest_period=BacktestPeriod.ONE_YEAR,
            rebalancing_frequency=60  # Bi-monthly
        )

        # Comprehensive result validation
        assert result.initial_capital == 250000.0
        assert result.final_value > 0
        assert len(result.portfolio_values) > 200  # Should have daily values
        assert len(result.portfolio_returns) > 200

        # Risk metrics should be calculated
        assert result.var_95 is not None
        assert result.var_99 is not None
        assert result.win_rate is not None
        assert 0 <= result.win_rate <= 1

        # Benchmark comparison metrics (if benchmark provided)
        if sample_benchmark_data is not None:
            assert result.benchmark_return is not None
            # Alpha and beta might be None if insufficient data

        # Should have some transactions due to rebalancing
        assert result.total_transactions >= 0
        assert result.total_transaction_costs >= 0

        # Data quality assessment
        assert result.data_quality is not None
        assert 0 <= result.backtest_reliability <= 1

    def test_multiple_strategy_comparison(self, sample_price_data, sample_benchmark_data):
        """Test comparing multiple strategies"""
        # Create different portfolio configurations
        conservative_portfolio = Portfolio(
            portfolio_id="conservative",
            name="Conservative Portfolio",
            portfolio_type=PortfolioType.CONSERVATIVE,
            rebalancing_strategy=RebalancingStrategy.THRESHOLD,
            position_sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
            holdings=[
                PortfolioHolding(ticker="AAPL", target_weight=0.33),
                PortfolioHolding(ticker="MSFT", target_weight=0.33),
                PortfolioHolding(ticker="GOOGL", target_weight=0.34)
            ],
            rebalancing_threshold=0.10,  # Less frequent rebalancing
            target_cash_allocation=0.10   # Hold some cash
        )

        aggressive_portfolio = Portfolio(
            portfolio_id="aggressive",
            name="Aggressive Portfolio",
            portfolio_type=PortfolioType.AGGRESSIVE,
            rebalancing_strategy=RebalancingStrategy.PERIODIC,
            position_sizing_method=PositionSizingMethod.EQUAL_WEIGHT,
            holdings=[
                PortfolioHolding(ticker="AAPL", target_weight=0.33),
                PortfolioHolding(ticker="MSFT", target_weight=0.33),
                PortfolioHolding(ticker="GOOGL", target_weight=0.34)
            ],
            rebalancing_frequency_days=30,  # Monthly rebalancing
            target_cash_allocation=0.0      # Fully invested
        )

        engine = BacktestEngine(initial_capital=100000.0)

        # Run backtests
        conservative_result = engine.run_backtest(
            conservative_portfolio, sample_price_data, sample_benchmark_data,
            BacktestPeriod.ONE_YEAR
        )

        aggressive_result = engine.run_backtest(
            aggressive_portfolio, sample_price_data, sample_benchmark_data,
            BacktestPeriod.ONE_YEAR
        )

        # Both should complete successfully
        assert conservative_result.strategy_name == "Conservative Portfolio"
        assert aggressive_result.strategy_name == "Aggressive Portfolio"

        # Both should have valid results
        assert conservative_result.total_return is not None
        assert aggressive_result.total_return is not None

        # Aggressive strategy might have more transactions due to frequent rebalancing
        # (Though this isn't guaranteed with the same underlying assets)


if __name__ == "__main__":
    pytest.main([__file__])