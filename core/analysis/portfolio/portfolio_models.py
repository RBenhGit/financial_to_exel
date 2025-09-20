"""
Portfolio Data Models
====================

This module defines comprehensive data models for portfolio management and analysis,
following the standardized data contract patterns established in the project.

Key Features:
- Portfolio structure with holdings and metadata
- PortfolioHolding for individual positions
- Portfolio types and rebalancing strategies
- Performance metrics and analysis results
- Integration with existing FinancialStatement and MarketData contracts

Design Principles:
- Follows existing data_contracts.py patterns
- Type-safe with comprehensive validation
- Extensible for different portfolio strategies
- Compatible with existing calculation engines
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Dict, List, Optional, Union, Literal, Tuple
from enum import Enum
from decimal import Decimal

from core.data_processing.data_contracts import (
    MetadataInfo,
    DataQuality,
    CurrencyCode,
    FinancialStatement,
    MarketData,
    CalculationResult
)


class PortfolioType(Enum):
    """Portfolio strategy types"""
    GROWTH = "growth"                    # Growth-focused stocks
    VALUE = "value"                      # Value investing approach
    DIVIDEND = "dividend"                # Dividend-focused portfolio
    BALANCED = "balanced"                # Mixed growth and value
    AGGRESSIVE = "aggressive"            # High-risk, high-reward
    CONSERVATIVE = "conservative"        # Low-risk, stable returns
    ESG = "esg"                         # ESG-focused investing
    SECTOR_ROTATION = "sector_rotation"  # Sector-based allocation
    CUSTOM = "custom"                    # User-defined strategy


class RebalancingStrategy(Enum):
    """Portfolio rebalancing approaches"""
    NONE = "none"                        # No automatic rebalancing
    PERIODIC = "periodic"                # Time-based rebalancing
    THRESHOLD = "threshold"              # Deviation-based rebalancing
    MOMENTUM = "momentum"                # Momentum-based adjustments
    MEAN_REVERSION = "mean_reversion"    # Mean reversion strategy
    VOLATILITY_TARGET = "volatility_target"  # Target volatility approach


class PositionSizingMethod(Enum):
    """Position sizing methodologies"""
    EQUAL_WEIGHT = "equal_weight"        # Equal allocation to all positions
    MARKET_CAP_WEIGHT = "market_cap"     # Market capitalization weighted
    RISK_PARITY = "risk_parity"         # Risk-adjusted equal contribution
    OPTIMIZATION = "optimization"        # Optimization-based sizing
    CUSTOM_WEIGHTS = "custom"            # User-defined weights
    MOMENTUM_WEIGHT = "momentum"         # Momentum-based weighting


@dataclass
class PortfolioHolding:
    """Individual holding within a portfolio"""

    # Basic Information
    ticker: str
    company_name: Optional[str] = None

    # Position Details
    shares: float = 0.0                  # Number of shares held
    current_price: Optional[float] = None
    market_value: Optional[float] = None  # Current market value
    cost_basis: Optional[float] = None    # Original purchase price per share
    total_cost: Optional[float] = None    # Total amount invested

    # Portfolio Allocation
    target_weight: float = 0.0           # Target allocation percentage (0-1)
    current_weight: float = 0.0          # Current allocation percentage (0-1)
    weight_deviation: float = 0.0        # Deviation from target weight

    # Performance Metrics
    unrealized_gain_loss: Optional[float] = None     # Unrealized P&L
    unrealized_gain_loss_pct: Optional[float] = None # Unrealized P&L %
    dividend_yield: Optional[float] = None            # Current dividend yield
    total_dividends_received: float = 0.0             # Cumulative dividends

    # Risk Metrics
    beta: Optional[float] = None         # Beta relative to market
    volatility: Optional[float] = None   # Historical volatility
    var_contribution: Optional[float] = None  # Contribution to portfolio VaR

    # Transaction History
    purchase_date: Optional[date] = None
    last_rebalance_date: Optional[date] = None

    # Integration with Existing Analysis
    financial_data: Optional[FinancialStatement] = None
    market_data: Optional[MarketData] = None
    valuation_result: Optional[CalculationResult] = None

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)

    def __post_init__(self):
        """Calculate derived metrics after initialization"""
        # Calculate market value if not provided
        if self.market_value is None and self.current_price and self.shares:
            self.market_value = self.current_price * self.shares

        # Calculate unrealized gain/loss
        if self.market_value and self.total_cost:
            self.unrealized_gain_loss = self.market_value - self.total_cost
            self.unrealized_gain_loss_pct = (self.unrealized_gain_loss / self.total_cost) * 100

        # Sync market data if available
        if self.market_data:
            if not self.current_price:
                self.current_price = self.market_data.price
            if not self.beta:
                self.beta = self.market_data.beta
            if not self.dividend_yield:
                self.dividend_yield = self.market_data.dividend_yield


@dataclass
class PortfolioMetrics:
    """Portfolio-level performance and risk metrics"""

    # Basic Portfolio Information
    total_value: float = 0.0             # Total portfolio market value
    total_cost: float = 0.0              # Total amount invested
    cash_position: float = 0.0           # Cash holdings
    number_of_holdings: int = 0          # Number of individual positions

    # Performance Metrics
    total_return: Optional[float] = None          # Total return %
    annualized_return: Optional[float] = None     # Annualized return %
    unrealized_gain_loss: Optional[float] = None # Total unrealized P&L
    unrealized_gain_loss_pct: Optional[float] = None # Total unrealized P&L %

    # Risk Metrics
    volatility: Optional[float] = None           # Portfolio volatility
    sharpe_ratio: Optional[float] = None         # Risk-adjusted return
    beta: Optional[float] = None                 # Portfolio beta
    value_at_risk_95: Optional[float] = None     # 95% VaR
    value_at_risk_99: Optional[float] = None     # 99% VaR
    max_drawdown: Optional[float] = None         # Maximum drawdown %

    # Diversification Metrics
    correlation_avg: Optional[float] = None      # Average correlation between holdings
    concentration_risk: Optional[float] = None   # Largest position weight
    sector_concentration: Dict[str, float] = field(default_factory=dict)

    # Income Metrics
    dividend_yield: Optional[float] = None       # Portfolio dividend yield
    annual_dividend_income: Optional[float] = None

    # Allocation Analysis
    top_holdings: List[Tuple[str, float]] = field(default_factory=list)  # Top 10 holdings
    rebalancing_needed: bool = False             # Whether rebalancing is recommended
    deviation_from_targets: float = 0.0         # Average deviation from target weights

    # Benchmark Comparison
    benchmark_return: Optional[float] = None     # Benchmark return for period
    alpha: Optional[float] = None                # Portfolio alpha
    tracking_error: Optional[float] = None       # Tracking error vs benchmark
    information_ratio: Optional[float] = None    # Information ratio

    # Metadata
    calculation_date: datetime = field(default_factory=datetime.now)
    benchmark_used: Optional[str] = None         # e.g., "S&P 500", "NASDAQ"
    period_analyzed: Optional[str] = None        # e.g., "1Y", "3Y", "5Y"


@dataclass
class Portfolio:
    """Main portfolio data structure"""

    # Portfolio Identity
    portfolio_id: str
    name: str
    description: Optional[str] = None
    portfolio_type: PortfolioType = PortfolioType.BALANCED
    base_currency: CurrencyCode = CurrencyCode.USD

    # Portfolio Strategy
    rebalancing_strategy: RebalancingStrategy = RebalancingStrategy.THRESHOLD
    position_sizing_method: PositionSizingMethod = PositionSizingMethod.EQUAL_WEIGHT
    rebalancing_threshold: float = 0.05          # 5% deviation threshold
    rebalancing_frequency_days: int = 90         # Quarterly rebalancing

    # Holdings
    holdings: List[PortfolioHolding] = field(default_factory=list)
    cash_position: float = 0.0
    target_cash_allocation: float = 0.05         # 5% cash target

    # Portfolio Constraints
    max_position_weight: float = 0.20            # 20% max per position
    min_position_weight: float = 0.01            # 1% minimum per position
    max_sector_weight: float = 0.30              # 30% max per sector
    min_holdings: int = 10                       # Minimum diversification
    max_holdings: int = 50                       # Maximum complexity

    # Risk Management
    risk_tolerance: Literal["conservative", "moderate", "aggressive"] = "moderate"
    target_volatility: Optional[float] = None    # Target portfolio volatility
    max_drawdown_limit: float = 0.20             # 20% max drawdown limit
    stop_loss_threshold: Optional[float] = None  # Individual position stop loss

    # Performance Tracking
    inception_date: date = field(default_factory=date.today)
    last_rebalance_date: Optional[date] = None
    benchmark_ticker: str = "SPY"                # Default to S&P 500 ETF

    # Current State
    portfolio_metrics: PortfolioMetrics = field(default_factory=PortfolioMetrics)
    last_update: datetime = field(default_factory=datetime.now)

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)

    def __post_init__(self):
        """Validate and calculate portfolio metrics after initialization"""
        self._validate_constraints()
        self._calculate_weights()
        self._update_portfolio_metrics()

    def _validate_constraints(self):
        """Validate portfolio constraints and settings"""
        if self.max_position_weight <= self.min_position_weight:
            raise ValueError("Max position weight must be greater than min position weight")

        if self.max_holdings < self.min_holdings:
            raise ValueError("Max holdings must be greater than or equal to min holdings")

        if not 0 <= self.target_cash_allocation <= 1:
            raise ValueError("Target cash allocation must be between 0 and 1")

    def _calculate_weights(self):
        """Calculate current weights for all holdings"""
        total_invested_value = sum(holding.market_value or 0 for holding in self.holdings)
        total_portfolio_value = total_invested_value + self.cash_position

        if total_portfolio_value > 0:
            for holding in self.holdings:
                if holding.market_value:
                    holding.current_weight = holding.market_value / total_portfolio_value
                    holding.weight_deviation = holding.current_weight - holding.target_weight

    def _update_portfolio_metrics(self):
        """Update portfolio-level metrics"""
        if not self.holdings:
            return

        # Basic metrics
        self.portfolio_metrics.number_of_holdings = len(self.holdings)
        self.portfolio_metrics.total_value = sum(h.market_value or 0 for h in self.holdings)
        self.portfolio_metrics.total_cost = sum(h.total_cost or 0 for h in self.holdings)
        self.portfolio_metrics.cash_position = self.cash_position

        # Performance metrics
        if self.portfolio_metrics.total_cost > 0:
            unrealized_pl = self.portfolio_metrics.total_value - self.portfolio_metrics.total_cost
            self.portfolio_metrics.unrealized_gain_loss = unrealized_pl
            self.portfolio_metrics.unrealized_gain_loss_pct = (unrealized_pl / self.portfolio_metrics.total_cost) * 100

        # Risk metrics
        self.portfolio_metrics.concentration_risk = max(
            (h.current_weight for h in self.holdings), default=0.0
        )

        # Top holdings
        holdings_by_weight = sorted(
            [(h.ticker, h.current_weight) for h in self.holdings],
            key=lambda x: x[1], reverse=True
        )
        self.portfolio_metrics.top_holdings = holdings_by_weight[:10]

        # Rebalancing analysis
        total_deviation = sum(abs(h.weight_deviation) for h in self.holdings)
        self.portfolio_metrics.deviation_from_targets = total_deviation / len(self.holdings) if self.holdings else 0
        self.portfolio_metrics.rebalancing_needed = self.portfolio_metrics.deviation_from_targets > self.rebalancing_threshold

    def add_holding(self, holding: PortfolioHolding) -> None:
        """Add a new holding to the portfolio"""
        # Check if holding already exists
        existing = next((h for h in self.holdings if h.ticker == holding.ticker), None)
        if existing:
            raise ValueError(f"Holding for {holding.ticker} already exists in portfolio")

        # Validate constraints
        if len(self.holdings) >= self.max_holdings:
            raise ValueError(f"Portfolio already at maximum holdings limit ({self.max_holdings})")

        self.holdings.append(holding)
        self._calculate_weights()
        self._update_portfolio_metrics()

    def remove_holding(self, ticker: str) -> bool:
        """Remove a holding from the portfolio"""
        original_count = len(self.holdings)
        self.holdings = [h for h in self.holdings if h.ticker != ticker]

        if len(self.holdings) < original_count:
            self._calculate_weights()
            self._update_portfolio_metrics()
            return True
        return False

    def get_holding(self, ticker: str) -> Optional[PortfolioHolding]:
        """Get a specific holding by ticker"""
        return next((h for h in self.holdings if h.ticker == ticker), None)

    def update_holding_prices(self, price_data: Dict[str, float]) -> None:
        """Update current prices for holdings"""
        for holding in self.holdings:
            if holding.ticker in price_data:
                holding.current_price = price_data[holding.ticker]
                if holding.shares:
                    holding.market_value = holding.current_price * holding.shares

        self._calculate_weights()
        self._update_portfolio_metrics()

    def set_target_weights(self, target_weights: Dict[str, float]) -> None:
        """Set target weights for holdings"""
        total_weight = sum(target_weights.values())
        if abs(total_weight - 1.0) > 0.01:  # Allow 1% tolerance
            raise ValueError(f"Target weights must sum to 1.0, got {total_weight}")

        for holding in self.holdings:
            if holding.ticker in target_weights:
                holding.target_weight = target_weights[holding.ticker]
                holding.weight_deviation = holding.current_weight - holding.target_weight

        self._update_portfolio_metrics()


@dataclass
class PortfolioAnalysisResult:
    """Result of comprehensive portfolio analysis"""

    # Portfolio Identity
    portfolio_id: str
    analysis_date: datetime = field(default_factory=datetime.now)
    analysis_type: str = "comprehensive"

    # Portfolio State
    portfolio: Portfolio = None

    # Performance Analysis
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    risk_metrics: Dict[str, float] = field(default_factory=dict)
    attribution_analysis: Dict[str, float] = field(default_factory=dict)

    # Comparison Analysis
    benchmark_comparison: Dict[str, float] = field(default_factory=dict)
    peer_comparison: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Optimization Recommendations
    rebalancing_recommendations: List[Dict[str, Union[str, float]]] = field(default_factory=list)
    optimization_suggestions: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)

    # Scenario Analysis
    stress_test_results: Dict[str, float] = field(default_factory=dict)
    monte_carlo_results: Dict[str, Union[float, List[float]]] = field(default_factory=dict)

    # Quality Assessment
    analysis_quality: DataQuality = DataQuality.UNKNOWN
    data_completeness: float = 0.0
    confidence_level: float = 0.0

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


# Validation functions following existing patterns
def validate_portfolio(portfolio: Portfolio) -> List[str]:
    """
    Validate portfolio structure and constraints

    Args:
        portfolio: Portfolio instance to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Basic validations
    if not portfolio.portfolio_id or not portfolio.portfolio_id.strip():
        errors.append("Portfolio ID is required")

    if not portfolio.name or not portfolio.name.strip():
        errors.append("Portfolio name is required")

    # Holdings validation
    if len(portfolio.holdings) < portfolio.min_holdings:
        errors.append(f"Portfolio has {len(portfolio.holdings)} holdings, minimum is {portfolio.min_holdings}")

    if len(portfolio.holdings) > portfolio.max_holdings:
        errors.append(f"Portfolio has {len(portfolio.holdings)} holdings, maximum is {portfolio.max_holdings}")

    # Weight validation
    total_target_weight = sum(h.target_weight for h in portfolio.holdings)
    available_weight = 1.0 - portfolio.target_cash_allocation

    if abs(total_target_weight - available_weight) > 0.01:  # 1% tolerance
        errors.append(f"Target weights sum to {total_target_weight:.3f}, should sum to {available_weight:.3f}")

    # Individual position validation
    for holding in portfolio.holdings:
        if holding.target_weight > portfolio.max_position_weight:
            errors.append(f"{holding.ticker} target weight {holding.target_weight:.3f} exceeds maximum {portfolio.max_position_weight:.3f}")

        if holding.target_weight < portfolio.min_position_weight:
            errors.append(f"{holding.ticker} target weight {holding.target_weight:.3f} below minimum {portfolio.min_position_weight:.3f}")

        # Data consistency checks
        if holding.shares and holding.current_price and holding.market_value:
            calculated_value = holding.shares * holding.current_price
            if abs(calculated_value - holding.market_value) / holding.market_value > 0.01:  # 1% tolerance
                errors.append(f"{holding.ticker} market value inconsistent with shares × price")

    return errors


def create_sample_portfolio() -> Portfolio:
    """Create a sample portfolio for testing and demonstration"""

    # Create sample holdings
    holdings = [
        PortfolioHolding(
            ticker="AAPL",
            company_name="Apple Inc.",
            shares=100,
            current_price=175.00,
            market_value=17500.00,
            cost_basis=150.00,
            total_cost=15000.00,
            target_weight=0.15
        ),
        PortfolioHolding(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            shares=50,
            current_price=350.00,
            market_value=17500.00,
            cost_basis=300.00,
            total_cost=15000.00,
            target_weight=0.15
        ),
        PortfolioHolding(
            ticker="GOOGL",
            company_name="Alphabet Inc.",
            shares=25,
            current_price=140.00,
            market_value=3500.00,
            cost_basis=120.00,
            total_cost=3000.00,
            target_weight=0.10
        )
    ]

    portfolio = Portfolio(
        portfolio_id="sample_001",
        name="Diversified Growth Portfolio",
        description="Sample growth-focused portfolio with large-cap technology stocks",
        portfolio_type=PortfolioType.GROWTH,
        holdings=holdings,
        cash_position=5000.00,
        target_cash_allocation=0.05
    )

    return portfolio