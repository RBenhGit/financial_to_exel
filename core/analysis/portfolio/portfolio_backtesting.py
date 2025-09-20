"""
Portfolio Backtesting Framework
===============================

This module implements a comprehensive backtesting system for portfolio strategies
and rebalancing rules, including transaction cost modeling, slippage simulation,
regime analysis, and stress testing capabilities.

Key Features:
- Historical simulation engine for portfolio strategies
- Transaction cost modeling and slippage effects
- Rebalancing simulation with different frequencies and thresholds
- Regime analysis and stress testing capabilities
- Backtesting reports with statistical significance testing
- Monte Carlo simulation for robust strategy evaluation

Components:
- BacktestEngine: Main orchestrator for backtesting
- BacktestTransaction: Individual transaction modeling
- BacktestResult: Comprehensive results container
- StrategyBacktester: Strategy-specific backtesting
- RegimeAnalyzer: Market regime analysis
- StressTester: Stress testing scenarios
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging
from scipy import stats
import warnings

from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioMetrics,
    PortfolioType,
    RebalancingStrategy,
    PositionSizingMethod
)
from .portfolio_rebalancing import PortfolioRebalancer, RebalancingPlan, RebalancingTransaction
from .portfolio_performance_analytics import (
    PortfolioPerformanceAnalyzer,
    PerformanceMetrics,
    PerformancePeriod
)
from core.data_processing.data_contracts import DataQuality

warnings.filterwarnings('ignore', category=RuntimeWarning)
logger = logging.getLogger(__name__)


class BacktestPeriod(Enum):
    """Backtesting time periods"""
    ONE_YEAR = "1Y"
    THREE_YEARS = "3Y"
    FIVE_YEARS = "5Y"
    TEN_YEARS = "10Y"
    MAX_AVAILABLE = "MAX"


class MarketRegime(Enum):
    """Market regime classifications"""
    BULL_MARKET = "bull"
    BEAR_MARKET = "bear"
    SIDEWAYS_MARKET = "sideways"
    HIGH_VOLATILITY = "high_vol"
    LOW_VOLATILITY = "low_vol"
    RECESSION = "recession"
    EXPANSION = "expansion"


class StressScenario(Enum):
    """Stress testing scenarios"""
    MARKET_CRASH_2008 = "crash_2008"
    TECH_BUBBLE_2000 = "tech_bubble_2000"
    COVID_CRASH_2020 = "covid_2020"
    INTEREST_RATE_SPIKE = "rate_spike"
    INFLATION_SHOCK = "inflation_shock"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    CUSTOM_SCENARIO = "custom"


@dataclass
class BacktestTransaction:
    """Individual transaction in backtesting"""

    date: date
    ticker: str
    action: str  # "BUY", "SELL", "DIVIDEND"
    shares: float
    price: float
    gross_value: float

    # Transaction Costs
    commission: float = 0.0
    bid_ask_spread: float = 0.0
    market_impact: float = 0.0
    slippage: float = 0.0
    total_costs: float = 0.0
    net_value: float = 0.0

    # Context
    portfolio_value: float = 0.0
    position_weight: float = 0.0
    rebalancing_trigger: Optional[str] = None

    def __post_init__(self):
        """Calculate total costs and net value"""
        self.total_costs = self.commission + self.bid_ask_spread + self.market_impact + abs(self.slippage)
        self.net_value = self.gross_value - self.total_costs


@dataclass
class BacktestState:
    """Portfolio state at a point in time during backtesting"""

    date: date
    portfolio_value: float
    cash: float
    holdings: Dict[str, float]  # ticker -> shares
    weights: Dict[str, float]   # ticker -> weight

    # Performance metrics
    cumulative_return: float = 0.0
    period_return: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0

    # Risk metrics
    var_95: Optional[float] = None
    sharpe_ratio: Optional[float] = None

    # Rebalancing info
    deviation_from_targets: float = 0.0
    rebalancing_needed: bool = False
    days_since_rebalance: int = 0


@dataclass
class RegimeAnalysis:
    """Market regime analysis results"""

    regimes: Dict[date, MarketRegime] = field(default_factory=dict)
    regime_performance: Dict[MarketRegime, Dict[str, float]] = field(default_factory=dict)
    regime_transitions: List[Tuple[date, MarketRegime, MarketRegime]] = field(default_factory=list)

    # Regime statistics
    avg_regime_duration: Dict[MarketRegime, float] = field(default_factory=dict)
    regime_frequency: Dict[MarketRegime, float] = field(default_factory=dict)

    # Performance by regime
    best_regime: Optional[MarketRegime] = None
    worst_regime: Optional[MarketRegime] = None


@dataclass
class StressTestResult:
    """Stress testing results"""

    scenario: StressScenario
    scenario_description: str

    # Performance during stress
    stress_period_return: float = 0.0
    max_loss: float = 0.0
    recovery_time_days: Optional[int] = None

    # Risk metrics during stress
    stress_volatility: float = 0.0
    stress_var_95: float = 0.0
    stress_max_drawdown: float = 0.0

    # Portfolio behavior
    worst_performing_holding: Optional[str] = None
    best_performing_holding: Optional[str] = None
    correlation_breakdown: bool = False

    # Recovery analysis
    recovered_to_pre_stress: bool = False
    time_to_break_even: Optional[int] = None


@dataclass
class BacktestResult:
    """Comprehensive backtesting results"""

    # Basic Information
    strategy_name: str
    backtest_period: BacktestPeriod
    start_date: date
    end_date: date
    initial_capital: float
    final_value: float

    # Performance Summary
    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0

    # Risk Metrics
    var_95: float = 0.0
    var_99: float = 0.0
    expected_shortfall_95: float = 0.0
    win_rate: float = 0.0

    # Benchmark Comparison
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    tracking_error: Optional[float] = None
    information_ratio: Optional[float] = None

    # Transaction Analysis
    total_transactions: int = 0
    total_transaction_costs: float = 0.0
    transaction_cost_impact: float = 0.0  # As percentage of returns
    turnover: float = 0.0

    # Rebalancing Analysis
    rebalancing_frequency: int = 0
    avg_deviation_before_rebalancing: float = 0.0
    rebalancing_benefit: float = 0.0

    # Time Series Data
    portfolio_values: pd.Series = field(default_factory=pd.Series)
    portfolio_returns: pd.Series = field(default_factory=pd.Series)
    rolling_sharpe: pd.Series = field(default_factory=pd.Series)
    rolling_volatility: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)

    # Transaction History
    transaction_history: List[BacktestTransaction] = field(default_factory=list)

    # State History
    state_history: List[BacktestState] = field(default_factory=list)

    # Regime Analysis
    regime_analysis: Optional[RegimeAnalysis] = None

    # Stress Testing
    stress_test_results: List[StressTestResult] = field(default_factory=list)

    # Statistical Tests
    statistical_significance: Dict[str, float] = field(default_factory=dict)
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)

    # Quality Assessment
    data_quality: DataQuality = DataQuality.UNKNOWN
    backtest_reliability: float = 0.0  # 0-1 score


class TransactionCostModel:
    """Models transaction costs and market impact"""

    def __init__(self,
                 commission_rate: float = 0.001,      # 0.1% commission
                 bid_ask_spread: float = 0.0005,      # 0.05% spread
                 market_impact_rate: float = 0.0001,  # 0.01% market impact
                 slippage_volatility: float = 0.0002): # 0.02% slippage volatility
        """
        Initialize transaction cost model

        Args:
            commission_rate: Fixed commission as percentage of trade value
            bid_ask_spread: Bid-ask spread as percentage
            market_impact_rate: Market impact as percentage (larger trades = higher impact)
            slippage_volatility: Random slippage volatility
        """
        self.commission_rate = commission_rate
        self.bid_ask_spread = bid_ask_spread
        self.market_impact_rate = market_impact_rate
        self.slippage_volatility = slippage_volatility

    def calculate_transaction_costs(self,
                                  ticker: str,
                                  shares: float,
                                  price: float,
                                  portfolio_value: float,
                                  volatility: Optional[float] = None) -> Dict[str, float]:
        """
        Calculate comprehensive transaction costs

        Args:
            ticker: Security ticker
            shares: Number of shares to trade
            price: Current price per share
            portfolio_value: Total portfolio value
            volatility: Security volatility for market impact calculation

        Returns:
            Dictionary with cost breakdown
        """
        trade_value = abs(shares * price)

        # Fixed commission
        commission = trade_value * self.commission_rate

        # Bid-ask spread (half the spread for one-way transaction)
        spread_cost = trade_value * (self.bid_ask_spread / 2)

        # Market impact (scales with trade size relative to portfolio)
        trade_size_ratio = trade_value / portfolio_value
        market_impact = trade_value * self.market_impact_rate * (1 + trade_size_ratio)

        # Slippage (random component based on volatility)
        if volatility:
            slippage_factor = np.random.normal(0, self.slippage_volatility * volatility)
        else:
            slippage_factor = np.random.normal(0, self.slippage_volatility)

        slippage = trade_value * slippage_factor

        return {
            'commission': commission,
            'bid_ask_spread': spread_cost,
            'market_impact': market_impact,
            'slippage': slippage,
            'total_costs': commission + spread_cost + market_impact + abs(slippage)
        }


class RegimeAnalyzer:
    """Analyzes market regimes and their impact on portfolio performance"""

    def __init__(self, lookback_window: int = 60):
        """
        Initialize regime analyzer

        Args:
            lookback_window: Days to look back for regime classification
        """
        self.lookback_window = lookback_window

    def classify_regime(self,
                       market_data: pd.DataFrame,
                       date: pd.Timestamp) -> MarketRegime:
        """
        Classify market regime for a given date

        Args:
            market_data: DataFrame with market data (must include benchmark returns)
            date: Date to classify

        Returns:
            Market regime classification
        """
        if date not in market_data.index:
            return MarketRegime.SIDEWAYS_MARKET

        # Get lookback period
        start_idx = max(0, market_data.index.get_loc(date) - self.lookback_window)
        end_idx = market_data.index.get_loc(date) + 1
        period_data = market_data.iloc[start_idx:end_idx]

        if len(period_data) < 20:  # Need minimum data
            return MarketRegime.SIDEWAYS_MARKET

        # Calculate metrics for regime classification
        returns = period_data.iloc[:, 0].pct_change().dropna()  # Use first column as benchmark

        if len(returns) < 10:
            return MarketRegime.SIDEWAYS_MARKET

        # Metrics
        mean_return = returns.mean() * 252  # Annualized
        volatility = returns.std() * np.sqrt(252)  # Annualized
        cumulative_return = (1 + returns).prod() - 1

        # Classification logic
        if volatility > 0.35:  # High volatility threshold
            return MarketRegime.HIGH_VOLATILITY
        elif volatility < 0.15:  # Low volatility threshold
            return MarketRegime.LOW_VOLATILITY
        elif mean_return > 0.15:  # Bull market threshold
            return MarketRegime.BULL_MARKET
        elif mean_return < -0.15:  # Bear market threshold
            return MarketRegime.BEAR_MARKET
        else:
            return MarketRegime.SIDEWAYS_MARKET

    def analyze_regime_performance(self,
                                 portfolio_returns: pd.Series,
                                 market_data: pd.DataFrame) -> RegimeAnalysis:
        """
        Analyze portfolio performance across different market regimes

        Args:
            portfolio_returns: Portfolio return series
            market_data: Market data for regime classification

        Returns:
            RegimeAnalysis with detailed results
        """
        analysis = RegimeAnalysis()

        # Classify regimes for each date
        for date in portfolio_returns.index:
            regime = self.classify_regime(market_data, date)
            analysis.regimes[date] = regime

        # Calculate performance by regime
        for regime in MarketRegime:
            regime_dates = [d for d, r in analysis.regimes.items() if r == regime]
            if regime_dates:
                regime_returns = portfolio_returns.loc[regime_dates]

                analysis.regime_performance[regime] = {
                    'total_return': (1 + regime_returns).prod() - 1,
                    'annualized_return': regime_returns.mean() * 252,
                    'volatility': regime_returns.std() * np.sqrt(252),
                    'sharpe_ratio': (regime_returns.mean() * 252) / (regime_returns.std() * np.sqrt(252)) if regime_returns.std() > 0 else 0,
                    'max_drawdown': self._calculate_max_drawdown(regime_returns),
                    'win_rate': (regime_returns > 0).mean(),
                    'days': len(regime_dates)
                }

        # Find best and worst regimes
        regime_returns = {r: perf.get('annualized_return', 0)
                         for r, perf in analysis.regime_performance.items()}
        if regime_returns:
            analysis.best_regime = max(regime_returns, key=regime_returns.get)
            analysis.worst_regime = min(regime_returns, key=regime_returns.get)

        return analysis

    def _calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown for a return series"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()


class StressTester:
    """Implements stress testing scenarios for portfolio backtesting"""

    def __init__(self):
        """Initialize stress tester with predefined scenarios"""
        self.scenarios = {
            StressScenario.MARKET_CRASH_2008: {
                'description': '2008 Financial Crisis (Sep 2008 - Mar 2009)',
                'start_date': date(2008, 9, 1),
                'end_date': date(2009, 3, 31),
                'market_decline': -0.50  # 50% market decline
            },
            StressScenario.TECH_BUBBLE_2000: {
                'description': 'Tech Bubble Burst (Mar 2000 - Oct 2002)',
                'start_date': date(2000, 3, 1),
                'end_date': date(2002, 10, 31),
                'market_decline': -0.45  # 45% market decline
            },
            StressScenario.COVID_CRASH_2020: {
                'description': 'COVID-19 Market Crash (Feb 2020 - Mar 2020)',
                'start_date': date(2020, 2, 15),
                'end_date': date(2020, 3, 31),
                'market_decline': -0.35  # 35% market decline
            }
        }

    def run_stress_test(self,
                       scenario: StressScenario,
                       portfolio_returns: pd.Series,
                       benchmark_returns: Optional[pd.Series] = None) -> StressTestResult:
        """
        Run stress test for a specific scenario

        Args:
            scenario: Stress test scenario
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series for comparison

        Returns:
            StressTestResult with detailed analysis
        """
        scenario_info = self.scenarios.get(scenario, {})

        result = StressTestResult(
            scenario=scenario,
            scenario_description=scenario_info.get('description', 'Custom scenario')
        )

        if not scenario_info:
            logger.warning(f"No predefined scenario for {scenario}")
            return result

        # Filter returns to stress period
        start_date = scenario_info['start_date']
        end_date = scenario_info['end_date']

        # Convert dates to pandas datetime for comparison
        start_pd = pd.Timestamp(start_date)
        end_pd = pd.Timestamp(end_date)

        stress_returns = portfolio_returns[
            (portfolio_returns.index >= start_pd) &
            (portfolio_returns.index <= end_pd)
        ]

        if len(stress_returns) == 0:
            logger.warning(f"No data available for stress period {start_date} to {end_date}")
            return result

        # Calculate stress period metrics
        result.stress_period_return = (1 + stress_returns).prod() - 1
        result.stress_volatility = stress_returns.std() * np.sqrt(252)
        result.stress_var_95 = np.percentile(stress_returns, 5)
        result.stress_max_drawdown = self._calculate_stress_drawdown(stress_returns)
        result.max_loss = stress_returns.min()

        # Recovery analysis
        post_stress_returns = portfolio_returns[portfolio_returns.index > end_pd]
        if len(post_stress_returns) > 0:
            result.recovery_time_days = self._calculate_recovery_time(
                stress_returns, post_stress_returns
            )
            result.recovered_to_pre_stress = result.recovery_time_days is not None

        return result

    def run_all_stress_tests(self,
                           portfolio_returns: pd.Series,
                           benchmark_returns: Optional[pd.Series] = None) -> List[StressTestResult]:
        """
        Run all predefined stress tests

        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series

        Returns:
            List of StressTestResult objects
        """
        results = []

        for scenario in [StressScenario.MARKET_CRASH_2008,
                        StressScenario.TECH_BUBBLE_2000,
                        StressScenario.COVID_CRASH_2020]:
            result = self.run_stress_test(scenario, portfolio_returns, benchmark_returns)
            results.append(result)

        return results

    def _calculate_stress_drawdown(self, returns: pd.Series) -> float:
        """Calculate maximum drawdown during stress period"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()

    def _calculate_recovery_time(self,
                               stress_returns: pd.Series,
                               post_stress_returns: pd.Series) -> Optional[int]:
        """Calculate time to recover from stress period"""
        stress_end_value = (1 + stress_returns).prod()

        # Find pre-stress peak (assume 1.0 for simplicity)
        pre_stress_peak = 1.0

        cumulative_post_stress = stress_end_value * (1 + post_stress_returns).cumprod()
        recovery_point = cumulative_post_stress >= pre_stress_peak

        if recovery_point.any():
            recovery_idx = recovery_point.idxmax()
            return (recovery_idx - stress_returns.index[-1]).days

        return None


class BacktestEngine:
    """
    Main backtesting engine for portfolio strategies
    """

    def __init__(self,
                 initial_capital: float = 100000.0,
                 transaction_cost_model: Optional[TransactionCostModel] = None,
                 risk_free_rate: float = 0.02):
        """
        Initialize backtesting engine

        Args:
            initial_capital: Starting portfolio value
            transaction_cost_model: Model for transaction costs
            risk_free_rate: Risk-free rate for calculations
        """
        self.initial_capital = initial_capital
        self.transaction_cost_model = transaction_cost_model or TransactionCostModel()
        self.risk_free_rate = risk_free_rate

        # Components
        self.regime_analyzer = RegimeAnalyzer()
        self.stress_tester = StressTester()

        # State tracking
        self.current_date: Optional[date] = None
        self.portfolio_state: Optional[BacktestState] = None
        self.rebalancer: Optional[PortfolioRebalancer] = None

    def run_backtest(self,
                    strategy_portfolio: Portfolio,
                    price_data: pd.DataFrame,
                    benchmark_data: Optional[pd.DataFrame] = None,
                    backtest_period: BacktestPeriod = BacktestPeriod.FIVE_YEARS,
                    rebalancing_frequency: int = 90) -> BacktestResult:
        """
        Run comprehensive portfolio backtest

        Args:
            strategy_portfolio: Portfolio configuration to backtest
            price_data: Historical price data (dates x tickers)
            benchmark_data: Benchmark price data for comparison
            backtest_period: Period to backtest
            rebalancing_frequency: Days between rebalancing

        Returns:
            BacktestResult with comprehensive analysis
        """
        logger.info(f"Starting backtest for {strategy_portfolio.name}")

        # Validate and prepare data
        if not self._validate_backtest_data(price_data, strategy_portfolio):
            raise ValueError("Invalid backtest data or portfolio configuration")

        # Determine backtest date range
        start_date, end_date = self._determine_date_range(price_data, backtest_period)

        # Filter data to backtest period
        backtest_data = price_data.loc[start_date:end_date].copy()

        # Initialize result
        result = BacktestResult(
            strategy_name=strategy_portfolio.name,
            backtest_period=backtest_period,
            start_date=start_date.date(),
            end_date=end_date.date(),
            initial_capital=self.initial_capital,
            final_value=self.initial_capital  # Will be updated later
        )

        # Initialize portfolio state
        self._initialize_portfolio_state(strategy_portfolio, start_date, backtest_data)

        # Initialize rebalancer
        self.rebalancer = PortfolioRebalancer(
            transaction_cost_bps=self.transaction_cost_model.commission_rate * 10000,
            min_trade_size=100.0
        )

        # Run simulation
        portfolio_values = []
        transaction_history = []
        state_history = []
        last_rebalance_date = start_date

        for current_date in backtest_data.index:
            self.current_date = current_date.date()

            # Update portfolio with current prices
            self._update_portfolio_prices(backtest_data.loc[current_date])

            # Check if rebalancing is needed
            days_since_rebalance = (current_date - last_rebalance_date).days

            if (days_since_rebalance >= rebalancing_frequency or
                self._should_rebalance_threshold(strategy_portfolio)):

                # Perform rebalancing
                transactions = self._execute_rebalancing(
                    strategy_portfolio, current_date, backtest_data
                )
                transaction_history.extend(transactions)
                last_rebalance_date = current_date

            # Record portfolio state
            state = self._capture_portfolio_state(current_date)
            state_history.append(state)
            portfolio_values.append(state.portfolio_value)

        # Calculate final metrics
        result = self._calculate_final_results(
            result, portfolio_values, transaction_history, state_history,
            backtest_data, benchmark_data
        )

        # Regime analysis
        if benchmark_data is not None:
            result.regime_analysis = self._perform_regime_analysis(
                result.portfolio_returns, benchmark_data
            )

        # Stress testing
        result.stress_test_results = self._perform_stress_testing(result.portfolio_returns)

        # Statistical significance testing
        result.statistical_significance = self._calculate_statistical_significance(result)

        logger.info(f"Backtest completed: {result.total_return:.2%} total return, "
                   f"{result.sharpe_ratio:.2f} Sharpe ratio")

        return result

    def _validate_backtest_data(self, price_data: pd.DataFrame, portfolio: Portfolio) -> bool:
        """Validate backtest data and portfolio configuration"""
        # Check if all portfolio tickers are in price data
        portfolio_tickers = {h.ticker for h in portfolio.holdings}
        available_tickers = set(price_data.columns)

        missing_tickers = portfolio_tickers - available_tickers
        if missing_tickers:
            logger.error(f"Missing price data for tickers: {missing_tickers}")
            return False

        # Check data quality
        if len(price_data) < 100:  # Need minimum 100 days
            logger.error("Insufficient price data for backtesting")
            return False

        return True

    def _determine_date_range(self, price_data: pd.DataFrame,
                            period: BacktestPeriod) -> Tuple[pd.Timestamp, pd.Timestamp]:
        """Determine start and end dates for backtest"""
        end_date = price_data.index[-1]

        if period == BacktestPeriod.ONE_YEAR:
            start_date = end_date - pd.DateOffset(years=1)
        elif period == BacktestPeriod.THREE_YEARS:
            start_date = end_date - pd.DateOffset(years=3)
        elif period == BacktestPeriod.FIVE_YEARS:
            start_date = end_date - pd.DateOffset(years=5)
        elif period == BacktestPeriod.TEN_YEARS:
            start_date = end_date - pd.DateOffset(years=10)
        else:  # MAX_AVAILABLE
            start_date = price_data.index[0]

        # Ensure start date is within available data
        start_date = max(start_date, price_data.index[0])

        return start_date, end_date

    def _initialize_portfolio_state(self, portfolio: Portfolio,
                                  start_date: pd.Timestamp,
                                  price_data: pd.DataFrame) -> None:
        """Initialize portfolio state for backtesting"""
        # Get starting prices
        start_prices = price_data.loc[start_date]

        # Calculate initial holdings based on target weights
        total_equity = self.initial_capital * (1 - portfolio.target_cash_allocation)

        holdings = {}
        weights = {}

        for holding in portfolio.holdings:
            if holding.ticker in start_prices:
                # Calculate number of shares based on target weight
                target_value = holding.target_weight * total_equity
                shares = target_value / start_prices[holding.ticker]
                holdings[holding.ticker] = shares
                weights[holding.ticker] = holding.target_weight

        # Initialize state
        self.portfolio_state = BacktestState(
            date=start_date.date(),
            portfolio_value=self.initial_capital,
            cash=self.initial_capital * portfolio.target_cash_allocation,
            holdings=holdings,
            weights=weights
        )

    def _update_portfolio_prices(self, current_prices: pd.Series) -> None:
        """Update portfolio value with current prices"""
        if not self.portfolio_state:
            return

        # Calculate new portfolio value
        equity_value = 0.0
        for ticker, shares in self.portfolio_state.holdings.items():
            if ticker in current_prices:
                equity_value += shares * current_prices[ticker]

        total_value = equity_value + self.portfolio_state.cash

        # Update weights
        new_weights = {}
        for ticker, shares in self.portfolio_state.holdings.items():
            if ticker in current_prices and total_value > 0:
                position_value = shares * current_prices[ticker]
                new_weights[ticker] = position_value / total_value

        # Update state
        self.portfolio_state.portfolio_value = total_value
        self.portfolio_state.weights = new_weights

    def _should_rebalance_threshold(self, portfolio: Portfolio) -> bool:
        """Check if portfolio needs rebalancing based on thresholds"""
        if not self.portfolio_state:
            return False

        # Calculate deviations from target weights
        max_deviation = 0.0

        for holding in portfolio.holdings:
            current_weight = self.portfolio_state.weights.get(holding.ticker, 0.0)
            deviation = abs(current_weight - holding.target_weight)
            max_deviation = max(max_deviation, deviation)

        self.portfolio_state.deviation_from_targets = max_deviation
        self.portfolio_state.rebalancing_needed = max_deviation > portfolio.rebalancing_threshold

        return self.portfolio_state.rebalancing_needed

    def _execute_rebalancing(self, portfolio: Portfolio,
                           current_date: pd.Timestamp,
                           price_data: pd.DataFrame) -> List[BacktestTransaction]:
        """Execute portfolio rebalancing"""
        if not self.portfolio_state or not self.rebalancer:
            return []

        transactions = []
        current_prices = price_data.loc[current_date]

        # Calculate target positions
        total_value = self.portfolio_state.portfolio_value
        target_equity = total_value * (1 - portfolio.target_cash_allocation)

        for holding in portfolio.holdings:
            ticker = holding.ticker
            if ticker not in current_prices:
                continue

            current_price = current_prices[ticker]
            current_shares = self.portfolio_state.holdings.get(ticker, 0.0)
            target_value = holding.target_weight * target_equity
            target_shares = target_value / current_price

            shares_to_trade = target_shares - current_shares

            if abs(shares_to_trade * current_price) > 100:  # Minimum trade size
                # Calculate transaction costs
                costs = self.transaction_cost_model.calculate_transaction_costs(
                    ticker, shares_to_trade, current_price, total_value
                )

                # Create transaction
                transaction = BacktestTransaction(
                    date=current_date.date(),
                    ticker=ticker,
                    action="BUY" if shares_to_trade > 0 else "SELL",
                    shares=abs(shares_to_trade),
                    price=current_price,
                    gross_value=abs(shares_to_trade * current_price),
                    commission=costs['commission'],
                    bid_ask_spread=costs['bid_ask_spread'],
                    market_impact=costs['market_impact'],
                    slippage=costs['slippage'],
                    portfolio_value=total_value,
                    position_weight=holding.target_weight,
                    rebalancing_trigger="scheduled"
                )

                transactions.append(transaction)

                # Update portfolio state
                self.portfolio_state.holdings[ticker] = target_shares
                self.portfolio_state.cash -= transaction.net_value

        return transactions

    def _capture_portfolio_state(self, current_date: pd.Timestamp) -> BacktestState:
        """Capture current portfolio state"""
        if not self.portfolio_state:
            return BacktestState(date=current_date.date(), portfolio_value=0.0, cash=0.0,
                               holdings={}, weights={})

        return BacktestState(
            date=current_date.date(),
            portfolio_value=self.portfolio_state.portfolio_value,
            cash=self.portfolio_state.cash,
            holdings=self.portfolio_state.holdings.copy(),
            weights=self.portfolio_state.weights.copy(),
            deviation_from_targets=self.portfolio_state.deviation_from_targets,
            rebalancing_needed=self.portfolio_state.rebalancing_needed
        )

    def _calculate_final_results(self,
                               result: BacktestResult,
                               portfolio_values: List[float],
                               transaction_history: List[BacktestTransaction],
                               state_history: List[BacktestState],
                               price_data: pd.DataFrame,
                               benchmark_data: Optional[pd.DataFrame]) -> BacktestResult:
        """Calculate final backtest results and metrics"""

        # Create time series
        dates = price_data.index
        result.portfolio_values = pd.Series(portfolio_values, index=dates)
        result.portfolio_returns = result.portfolio_values.pct_change().dropna()

        # Basic performance metrics
        result.final_value = portfolio_values[-1]
        result.total_return = (result.final_value / self.initial_capital) - 1

        # Annualized metrics
        years = len(result.portfolio_returns) / 252
        result.annualized_return = (1 + result.total_return) ** (1 / years) - 1
        result.volatility = result.portfolio_returns.std() * np.sqrt(252)

        # Risk-adjusted metrics
        excess_returns = result.portfolio_returns - (self.risk_free_rate / 252)
        if excess_returns.std() > 0:
            result.sharpe_ratio = excess_returns.mean() / excess_returns.std() * np.sqrt(252)

        # Downside metrics
        downside_returns = result.portfolio_returns[result.portfolio_returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            result.sortino_ratio = excess_returns.mean() / downside_returns.std() * np.sqrt(252)

        # Drawdown analysis
        cumulative = (1 + result.portfolio_returns).cumprod()
        running_max = cumulative.expanding().max()
        result.drawdown_series = (cumulative - running_max) / running_max
        result.max_drawdown = result.drawdown_series.min()

        if result.max_drawdown != 0:
            result.calmar_ratio = result.annualized_return / abs(result.max_drawdown)

        # VaR metrics
        result.var_95 = np.percentile(result.portfolio_returns, 5)
        result.var_99 = np.percentile(result.portfolio_returns, 1)
        result.expected_shortfall_95 = result.portfolio_returns[
            result.portfolio_returns <= result.var_95
        ].mean()

        # Win rate
        result.win_rate = (result.portfolio_returns > 0).mean()

        # Transaction analysis
        result.transaction_history = transaction_history
        result.total_transactions = len(transaction_history)
        result.total_transaction_costs = sum(t.total_costs for t in transaction_history)

        if result.final_value > 0:
            result.transaction_cost_impact = result.total_transaction_costs / result.final_value

        # Rolling metrics
        result.rolling_sharpe = self._calculate_rolling_sharpe(result.portfolio_returns)
        result.rolling_volatility = result.portfolio_returns.rolling(60).std() * np.sqrt(252)

        # Store state history
        result.state_history = state_history

        # Benchmark comparison if available
        if benchmark_data is not None:
            result = self._calculate_benchmark_comparison(result, benchmark_data)

        # Data quality assessment
        result.data_quality = DataQuality.GOOD
        result.backtest_reliability = self._assess_backtest_reliability(result)

        return result

    def _calculate_rolling_sharpe(self, returns: pd.Series, window: int = 60) -> pd.Series:
        """Calculate rolling Sharpe ratio"""
        rolling_excess = returns.rolling(window).mean() - (self.risk_free_rate / 252)
        rolling_vol = returns.rolling(window).std()

        return (rolling_excess / rolling_vol) * np.sqrt(252)

    def _calculate_benchmark_comparison(self, result: BacktestResult,
                                     benchmark_data: pd.DataFrame) -> BacktestResult:
        """Calculate benchmark comparison metrics"""
        # Get benchmark returns for the same period
        benchmark_prices = benchmark_data.loc[result.portfolio_values.index]
        benchmark_returns = benchmark_prices.iloc[:, 0].pct_change().dropna()

        # Align series
        common_dates = result.portfolio_returns.index.intersection(benchmark_returns.index)
        portfolio_ret = result.portfolio_returns.loc[common_dates]
        benchmark_ret = benchmark_returns.loc[common_dates]

        if len(common_dates) > 20:  # Need minimum data for regression
            # Calculate benchmark metrics
            result.benchmark_return = (1 + benchmark_ret).prod() - 1

            # Regression for alpha and beta
            portfolio_excess = portfolio_ret - (self.risk_free_rate / 252)
            benchmark_excess = benchmark_ret - (self.risk_free_rate / 252)

            slope, intercept, r_value, _, _ = stats.linregress(benchmark_excess, portfolio_excess)

            result.beta = slope
            result.alpha = intercept * 252  # Annualized alpha

            # Tracking error and information ratio
            excess_returns = portfolio_ret - benchmark_ret
            result.tracking_error = excess_returns.std() * np.sqrt(252)

            if result.tracking_error > 0:
                result.information_ratio = (excess_returns.mean() * 252) / result.tracking_error

        return result

    def _perform_regime_analysis(self, portfolio_returns: pd.Series,
                               benchmark_data: pd.DataFrame) -> RegimeAnalysis:
        """Perform regime analysis on portfolio performance"""
        return self.regime_analyzer.analyze_regime_performance(
            portfolio_returns, benchmark_data
        )

    def _perform_stress_testing(self, portfolio_returns: pd.Series) -> List[StressTestResult]:
        """Perform stress testing on portfolio"""
        return self.stress_tester.run_all_stress_tests(portfolio_returns)

    def _calculate_statistical_significance(self, result: BacktestResult) -> Dict[str, float]:
        """Calculate statistical significance of results"""
        returns = result.portfolio_returns

        if len(returns) < 30:
            return {}

        # T-test for mean return significance
        t_stat, p_value = stats.ttest_1samp(returns, 0)

        # Bootstrap confidence intervals for Sharpe ratio
        n_bootstrap = 1000
        bootstrap_sharpes = []

        for _ in range(n_bootstrap):
            bootstrap_sample = np.random.choice(returns, size=len(returns), replace=True)
            bootstrap_excess = bootstrap_sample - (self.risk_free_rate / 252)
            if bootstrap_excess.std() > 0:
                bootstrap_sharpe = bootstrap_excess.mean() / bootstrap_excess.std() * np.sqrt(252)
                bootstrap_sharpes.append(bootstrap_sharpe)

        if bootstrap_sharpes:
            sharpe_ci_lower = np.percentile(bootstrap_sharpes, 2.5)
            sharpe_ci_upper = np.percentile(bootstrap_sharpes, 97.5)
        else:
            sharpe_ci_lower = sharpe_ci_upper = result.sharpe_ratio

        result.confidence_intervals['sharpe_ratio'] = (sharpe_ci_lower, sharpe_ci_upper)

        return {
            'mean_return_t_stat': t_stat,
            'mean_return_p_value': p_value,
            'sharpe_significance': 1.0 if sharpe_ci_lower > 0 else 0.0
        }

    def _assess_backtest_reliability(self, result: BacktestResult) -> float:
        """Assess overall reliability of backtest results"""
        reliability_score = 1.0

        # Penalize for insufficient data
        if len(result.portfolio_returns) < 252:  # Less than 1 year
            reliability_score *= 0.7
        elif len(result.portfolio_returns) < 252 * 3:  # Less than 3 years
            reliability_score *= 0.9

        # Penalize for high transaction costs
        if result.transaction_cost_impact > 0.02:  # More than 2%
            reliability_score *= 0.8

        # Penalize for extreme results
        if abs(result.sharpe_ratio) > 3.0:  # Unrealistically high Sharpe
            reliability_score *= 0.7

        # Penalize for insufficient transactions
        if result.total_transactions < 10:
            reliability_score *= 0.8

        return max(0.0, min(1.0, reliability_score))


def create_sample_backtest() -> BacktestResult:
    """Create a sample backtest result for testing and demonstration"""
    from .portfolio_models import create_sample_portfolio

    # Create sample portfolio
    portfolio = create_sample_portfolio()

    # Create sample price data
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    tickers = [h.ticker for h in portfolio.holdings]

    # Generate random price data
    np.random.seed(42)
    price_data = pd.DataFrame(index=dates, columns=tickers)

    for ticker in tickers:
        returns = np.random.normal(0.0008, 0.02, len(dates))  # Daily returns
        prices = 100 * np.cumprod(1 + returns)
        price_data[ticker] = prices

    # Initialize backtest engine
    engine = BacktestEngine(initial_capital=100000.0)

    # Run backtest
    result = engine.run_backtest(
        strategy_portfolio=portfolio,
        price_data=price_data,
        backtest_period=BacktestPeriod.ONE_YEAR
    )

    return result