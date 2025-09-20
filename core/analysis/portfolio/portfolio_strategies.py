"""
Portfolio Strategy Templates and Implementation
==============================================

This module provides predefined portfolio strategies and templates for different
investment approaches, making it easy to create portfolios aligned with specific
investment philosophies and risk tolerances.

Supported Strategy Types:
- Growth: High-growth companies with strong earnings expansion
- Value: Undervalued companies trading below intrinsic value
- Dividend: Income-focused with consistent dividend payments
- Balanced: Mix of growth and value across market caps
- Conservative: Low-risk, stable companies with predictable returns
- Aggressive: High-risk, high-reward growth opportunities
- ESG: Environmental, Social, and Governance focused investing
- Sector Rotation: Dynamic allocation based on economic cycles

Features:
- Predefined allocation models for each strategy
- Screening criteria for stock selection
- Risk management parameters
- Performance benchmarks
- Customizable templates
"""

from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from .portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    RebalancingStrategy,
    PositionSizingMethod,
    CurrencyCode
)
from core.data_processing.data_contracts import FinancialStatement, MarketData

logger = logging.getLogger(__name__)


@dataclass
class PortfolioTemplate:
    """Template for creating portfolios with specific strategies"""

    name: str
    portfolio_type: PortfolioType
    description: str

    # Strategy Parameters
    position_sizing_method: PositionSizingMethod = PositionSizingMethod.EQUAL_WEIGHT
    rebalancing_strategy: RebalancingStrategy = RebalancingStrategy.THRESHOLD
    rebalancing_threshold: float = 0.05
    rebalancing_frequency_days: int = 90

    # Position Constraints
    max_position_weight: float = 0.20
    min_position_weight: float = 0.01
    max_sector_weight: float = 0.30
    min_holdings: int = 10
    max_holdings: int = 50
    target_cash_allocation: float = 0.05

    # Risk Management
    risk_tolerance: str = "moderate"
    target_volatility: Optional[float] = None
    max_drawdown_limit: float = 0.20
    stop_loss_threshold: Optional[float] = None

    # Screening Criteria
    fundamental_criteria: Dict[str, Tuple[float, float]] = field(default_factory=dict)  # metric: (min, max)
    market_criteria: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    sector_preferences: Dict[str, float] = field(default_factory=dict)  # sector: max_weight
    exclude_sectors: List[str] = field(default_factory=list)

    # Benchmark
    benchmark_ticker: str = "SPY"


class PortfolioStrategyFactory:
    """
    Factory class for creating portfolio strategies and templates
    """

    @staticmethod
    def create_growth_strategy() -> PortfolioTemplate:
        """Create growth strategy template"""
        return PortfolioTemplate(
            name="Growth Strategy",
            portfolio_type=PortfolioType.GROWTH,
            description="Focus on companies with high earnings growth and revenue expansion",
            position_sizing_method=PositionSizingMethod.OPTIMIZATION,
            rebalancing_strategy=RebalancingStrategy.MOMENTUM,
            rebalancing_threshold=0.08,  # Higher threshold for growth stocks
            max_position_weight=0.25,  # Allow larger positions in high-conviction growth names
            min_holdings=8,
            max_holdings=25,
            target_cash_allocation=0.03,  # Lower cash for full equity exposure
            risk_tolerance="aggressive",
            max_drawdown_limit=0.30,  # Higher tolerance for volatility
            fundamental_criteria={
                'revenue_growth_rate': (0.15, float('inf')),  # Min 15% revenue growth
                'earnings_growth_rate': (0.20, float('inf')),  # Min 20% earnings growth
                'roe': (0.15, float('inf')),  # Min 15% ROE
                'debt_to_equity': (0.0, 0.5),  # Max 50% debt-to-equity
                'free_cash_flow_yield': (0.02, float('inf'))  # Min 2% FCF yield
            },
            market_criteria={
                'pe_ratio': (0.0, 40.0),  # Max P/E of 40
                'peg_ratio': (0.0, 2.0),  # Max PEG of 2.0
                'market_cap': (1e9, float('inf'))  # Min $1B market cap
            },
            sector_preferences={
                'Technology': 0.40,
                'Healthcare': 0.25,
                'Consumer Discretionary': 0.20,
                'Communication Services': 0.15
            },
            exclude_sectors=['Utilities', 'Real Estate'],
            benchmark_ticker="QQQ"  # NASDAQ-100 for growth comparison
        )

    @staticmethod
    def create_value_strategy() -> PortfolioTemplate:
        """Create value strategy template"""
        return PortfolioTemplate(
            name="Value Strategy",
            portfolio_type=PortfolioType.VALUE,
            description="Focus on undervalued companies trading below intrinsic value",
            position_sizing_method=PositionSizingMethod.RISK_PARITY,
            rebalancing_strategy=RebalancingStrategy.MEAN_REVERSION,
            rebalancing_threshold=0.10,  # Higher threshold to avoid overtrading
            max_position_weight=0.15,
            min_holdings=15,
            max_holdings=40,
            target_cash_allocation=0.10,  # Higher cash for opportunistic purchases
            risk_tolerance="moderate",
            max_drawdown_limit=0.20,
            fundamental_criteria={
                'pb_ratio': (0.1, 2.0),  # Low price-to-book
                'pe_ratio': (3.0, 15.0),  # Low P/E ratio
                'ev_ebitda': (3.0, 12.0),  # Low EV/EBITDA
                'roe': (0.10, float('inf')),  # Min 10% ROE
                'debt_to_equity': (0.0, 0.8),  # Max 80% debt-to-equity
                'dividend_yield': (0.02, 0.10)  # 2-10% dividend yield
            },
            market_criteria={
                'market_cap': (500e6, float('inf')),  # Min $500M market cap
                'price_to_52w_high': (0.5, 0.8)  # Trading below recent highs
            },
            sector_preferences={
                'Financials': 0.25,
                'Energy': 0.20,
                'Industrials': 0.20,
                'Materials': 0.15,
                'Consumer Staples': 0.20
            },
            exclude_sectors=['Technology'],  # Typically avoid high-growth tech
            benchmark_ticker="VTV"  # Vanguard Value ETF
        )

    @staticmethod
    def create_dividend_strategy() -> PortfolioTemplate:
        """Create dividend-focused strategy template"""
        return PortfolioTemplate(
            name="Dividend Strategy",
            portfolio_type=PortfolioType.DIVIDEND,
            description="Focus on companies with consistent dividend payments and growth",
            position_sizing_method=PositionSizingMethod.MARKET_CAP_WEIGHT,
            rebalancing_strategy=RebalancingStrategy.PERIODIC,
            rebalancing_frequency_days=180,  # Semi-annual rebalancing
            rebalancing_threshold=0.12,
            max_position_weight=0.18,
            min_holdings=20,
            max_holdings=60,
            target_cash_allocation=0.08,
            risk_tolerance="conservative",
            max_drawdown_limit=0.15,
            fundamental_criteria={
                'dividend_yield': (0.03, 0.08),  # 3-8% dividend yield
                'dividend_payout_ratio': (0.2, 0.7),  # Sustainable payout
                'dividend_growth_rate': (0.05, float('inf')),  # Min 5% dividend growth
                'free_cash_flow_yield': (0.05, float('inf')),  # Strong FCF
                'debt_to_equity': (0.0, 0.6),  # Conservative debt levels
                'roe': (0.12, float('inf'))  # Min 12% ROE
            },
            market_criteria={
                'market_cap': (2e9, float('inf')),  # Min $2B market cap
                'beta': (0.3, 1.2)  # Lower volatility preference
            },
            sector_preferences={
                'Utilities': 0.25,
                'Consumer Staples': 0.20,
                'Financials': 0.20,
                'Real Estate': 0.15,
                'Telecommunications': 0.20
            },
            exclude_sectors=['Technology', 'Biotechnology'],
            benchmark_ticker="VYM"  # Vanguard High Dividend Yield ETF
        )

    @staticmethod
    def create_balanced_strategy() -> PortfolioTemplate:
        """Create balanced strategy template"""
        return PortfolioTemplate(
            name="Balanced Strategy",
            portfolio_type=PortfolioType.BALANCED,
            description="Balanced approach combining growth and value across market caps",
            position_sizing_method=PositionSizingMethod.OPTIMIZATION,
            rebalancing_strategy=RebalancingStrategy.THRESHOLD,
            rebalancing_threshold=0.06,
            max_position_weight=0.12,
            min_holdings=25,
            max_holdings=75,
            target_cash_allocation=0.05,
            risk_tolerance="moderate",
            max_drawdown_limit=0.18,
            fundamental_criteria={
                'roe': (0.12, float('inf')),  # Min 12% ROE
                'debt_to_equity': (0.0, 0.7),  # Max 70% debt-to-equity
                'revenue_growth_rate': (0.05, float('inf')),  # Min 5% revenue growth
                'free_cash_flow_yield': (0.03, float('inf'))  # Min 3% FCF yield
            },
            market_criteria={
                'pe_ratio': (5.0, 25.0),  # Reasonable P/E range
                'market_cap': (1e9, float('inf')),  # Min $1B market cap
                'beta': (0.5, 1.5)  # Moderate volatility range
            },
            sector_preferences={
                'Technology': 0.22,
                'Healthcare': 0.15,
                'Financials': 0.15,
                'Consumer Discretionary': 0.12,
                'Industrials': 0.12,
                'Consumer Staples': 0.10,
                'Energy': 0.08,
                'Materials': 0.06
            },
            benchmark_ticker="SPY"  # S&P 500
        )

    @staticmethod
    def create_conservative_strategy() -> PortfolioTemplate:
        """Create conservative strategy template"""
        return PortfolioTemplate(
            name="Conservative Strategy",
            portfolio_type=PortfolioType.CONSERVATIVE,
            description="Low-risk approach focusing on stability and capital preservation",
            position_sizing_method=PositionSizingMethod.RISK_PARITY,
            rebalancing_strategy=RebalancingStrategy.PERIODIC,
            rebalancing_frequency_days=120,  # Quarterly rebalancing
            rebalancing_threshold=0.08,
            max_position_weight=0.10,
            min_holdings=30,
            max_holdings=100,
            target_cash_allocation=0.15,  # Higher cash buffer
            risk_tolerance="conservative",
            max_drawdown_limit=0.12,
            stop_loss_threshold=0.15,  # 15% stop loss
            fundamental_criteria={
                'roe': (0.10, float('inf')),  # Min 10% ROE
                'debt_to_equity': (0.0, 0.4),  # Low debt
                'current_ratio': (1.5, float('inf')),  # Strong liquidity
                'dividend_yield': (0.02, float('inf')),  # Dividend paying
                'earnings_stability': (0.8, float('inf'))  # Stable earnings
            },
            market_criteria={
                'market_cap': (5e9, float('inf')),  # Large cap only
                'beta': (0.3, 1.0),  # Low volatility
                'price_volatility': (0.0, 0.25)  # Max 25% volatility
            },
            sector_preferences={
                'Consumer Staples': 0.25,
                'Utilities': 0.25,
                'Healthcare': 0.20,
                'Financials': 0.15,
                'Telecommunications': 0.15
            },
            exclude_sectors=['Technology', 'Energy', 'Materials', 'Biotechnology'],
            benchmark_ticker="USMV"  # Minimum Volatility ETF
        )

    @staticmethod
    def create_aggressive_strategy() -> PortfolioTemplate:
        """Create aggressive growth strategy template"""
        return PortfolioTemplate(
            name="Aggressive Growth Strategy",
            portfolio_type=PortfolioType.AGGRESSIVE,
            description="High-risk, high-reward approach targeting maximum growth",
            position_sizing_method=PositionSizingMethod.MOMENTUM_WEIGHT,
            rebalancing_strategy=RebalancingStrategy.MOMENTUM,
            rebalancing_threshold=0.12,
            max_position_weight=0.35,  # Allow high concentration
            min_holdings=5,
            max_holdings=20,
            target_cash_allocation=0.02,  # Minimal cash
            risk_tolerance="aggressive",
            max_drawdown_limit=0.40,  # High volatility tolerance
            target_volatility=0.30,
            fundamental_criteria={
                'revenue_growth_rate': (0.25, float('inf')),  # Min 25% revenue growth
                'earnings_growth_rate': (0.30, float('inf')),  # Min 30% earnings growth
                'roe': (0.20, float('inf')),  # Min 20% ROE
                'gross_margin': (0.40, float('inf')),  # High margin businesses
            },
            market_criteria={
                'pe_ratio': (15.0, 100.0),  # Accept high valuations for growth
                'peg_ratio': (0.5, 3.0),  # Growth at reasonable price
                'market_cap': (100e6, 50e9),  # Small to mid-cap focus
                'beta': (1.2, 3.0)  # High beta stocks
            },
            sector_preferences={
                'Technology': 0.50,
                'Biotechnology': 0.20,
                'Consumer Discretionary': 0.15,
                'Communication Services': 0.15
            },
            exclude_sectors=['Utilities', 'Consumer Staples', 'Real Estate'],
            benchmark_ticker="ARKK"  # Innovation ETF
        )

    @staticmethod
    def get_all_strategies() -> Dict[str, PortfolioTemplate]:
        """Get all predefined strategy templates"""
        return {
            'growth': PortfolioStrategyFactory.create_growth_strategy(),
            'value': PortfolioStrategyFactory.create_value_strategy(),
            'dividend': PortfolioStrategyFactory.create_dividend_strategy(),
            'balanced': PortfolioStrategyFactory.create_balanced_strategy(),
            'conservative': PortfolioStrategyFactory.create_conservative_strategy(),
            'aggressive': PortfolioStrategyFactory.create_aggressive_strategy()
        }


class PortfolioScreener:
    """
    Screen stocks based on portfolio strategy criteria
    """

    def __init__(self, template: PortfolioTemplate):
        self.template = template

    def screen_fundamental_criteria(self, financial_data: FinancialStatement) -> Tuple[bool, List[str]]:
        """
        Screen based on fundamental criteria

        Args:
            financial_data: Financial statement data

        Returns:
            Tuple of (passes_screen, list_of_failed_criteria)
        """
        passes = True
        failed_criteria = []

        for criterion, (min_val, max_val) in self.template.fundamental_criteria.items():
            value = self._get_financial_metric(financial_data, criterion)

            if value is None:
                failed_criteria.append(f"{criterion}: No data available")
                passes = False
                continue

            if not (min_val <= value <= max_val):
                failed_criteria.append(f"{criterion}: {value:.3f} not in range [{min_val:.3f}, {max_val:.3f}]")
                passes = False

        return passes, failed_criteria

    def screen_market_criteria(self, market_data: MarketData) -> Tuple[bool, List[str]]:
        """
        Screen based on market criteria

        Args:
            market_data: Market data

        Returns:
            Tuple of (passes_screen, list_of_failed_criteria)
        """
        passes = True
        failed_criteria = []

        for criterion, (min_val, max_val) in self.template.market_criteria.items():
            value = self._get_market_metric(market_data, criterion)

            if value is None:
                failed_criteria.append(f"{criterion}: No data available")
                passes = False
                continue

            if not (min_val <= value <= max_val):
                failed_criteria.append(f"{criterion}: {value:.3f} not in range [{min_val:.3f}, {max_val:.3f}]")
                passes = False

        return passes, failed_criteria

    def _get_financial_metric(self, financial_data: FinancialStatement, metric: str) -> Optional[float]:
        """Get financial metric value from financial data"""
        metric_map = {
            'revenue_growth_rate': self._calculate_revenue_growth,
            'earnings_growth_rate': self._calculate_earnings_growth,
            'roe': self._calculate_roe,
            'debt_to_equity': self._calculate_debt_to_equity,
            'free_cash_flow_yield': self._calculate_fcf_yield,
            'pb_ratio': lambda fd: getattr(fd, 'pb_ratio', None),
            'pe_ratio': lambda fd: getattr(fd, 'pe_ratio', None),
            'ev_ebitda': lambda fd: getattr(fd, 'ev_ebitda', None),
            'dividend_yield': lambda fd: getattr(fd, 'dividend_yield', None),
            'dividend_payout_ratio': self._calculate_payout_ratio,
            'current_ratio': self._calculate_current_ratio,
            'gross_margin': self._calculate_gross_margin
        }

        calculator = metric_map.get(metric)
        if calculator:
            try:
                return calculator(financial_data)
            except Exception as e:
                logger.warning(f"Failed to calculate {metric}: {str(e)}")

        return None

    def _get_market_metric(self, market_data: MarketData, metric: str) -> Optional[float]:
        """Get market metric value from market data"""
        metric_map = {
            'pe_ratio': 'pe_ratio',
            'pb_ratio': 'pb_ratio',
            'market_cap': 'market_cap',
            'beta': 'beta',
            'peg_ratio': 'peg_ratio',
            'dividend_yield': 'dividend_yield'
        }

        field_name = metric_map.get(metric, metric)
        return getattr(market_data, field_name, None)

    def _calculate_revenue_growth(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate revenue growth rate (placeholder - needs historical data)"""
        # This would need historical data to calculate properly
        # For now, return None to indicate calculation not available
        return None

    def _calculate_earnings_growth(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate earnings growth rate (placeholder - needs historical data)"""
        # This would need historical data to calculate properly
        return None

    def _calculate_roe(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate Return on Equity"""
        if financial_data.net_income and financial_data.shareholders_equity and financial_data.shareholders_equity != 0:
            return financial_data.net_income / financial_data.shareholders_equity
        return None

    def _calculate_debt_to_equity(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate debt-to-equity ratio"""
        if financial_data.total_debt and financial_data.shareholders_equity and financial_data.shareholders_equity != 0:
            return financial_data.total_debt / financial_data.shareholders_equity
        return None

    def _calculate_fcf_yield(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate free cash flow yield (needs market cap)"""
        # This would need market cap to calculate properly
        return None

    def _calculate_payout_ratio(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate dividend payout ratio (needs dividend data)"""
        # This would need dividend per share data
        return None

    def _calculate_current_ratio(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate current ratio"""
        if financial_data.current_assets and financial_data.current_liabilities and financial_data.current_liabilities != 0:
            return financial_data.current_assets / financial_data.current_liabilities
        return None

    def _calculate_gross_margin(self, financial_data: FinancialStatement) -> Optional[float]:
        """Calculate gross margin"""
        if financial_data.gross_profit and financial_data.revenue and financial_data.revenue != 0:
            return financial_data.gross_profit / financial_data.revenue
        return None


def create_portfolio_from_template(template: PortfolioTemplate,
                                 holdings_data: List[Dict],
                                 portfolio_id: str,
                                 name: Optional[str] = None) -> Portfolio:
    """
    Create a portfolio from a strategy template and holdings data

    Args:
        template: Portfolio strategy template
        holdings_data: List of dictionaries with holding information
        portfolio_id: Unique identifier for portfolio
        name: Optional custom name (uses template name if not provided)

    Returns:
        Portfolio instance configured according to template
    """
    # Create holdings from data
    holdings = []
    for holding_data in holdings_data:
        holding = PortfolioHolding(
            ticker=holding_data['ticker'],
            company_name=holding_data.get('company_name'),
            shares=holding_data.get('shares', 0.0),
            current_price=holding_data.get('current_price'),
            target_weight=holding_data.get('target_weight', 0.0)
        )
        holdings.append(holding)

    # Create portfolio
    portfolio = Portfolio(
        portfolio_id=portfolio_id,
        name=name or template.name,
        description=template.description,
        portfolio_type=template.portfolio_type,
        holdings=holdings,
        position_sizing_method=template.position_sizing_method,
        rebalancing_strategy=template.rebalancing_strategy,
        rebalancing_threshold=template.rebalancing_threshold,
        rebalancing_frequency_days=template.rebalancing_frequency_days,
        max_position_weight=template.max_position_weight,
        min_position_weight=template.min_position_weight,
        max_sector_weight=template.max_sector_weight,
        min_holdings=template.min_holdings,
        max_holdings=template.max_holdings,
        target_cash_allocation=template.target_cash_allocation,
        risk_tolerance=template.risk_tolerance,
        target_volatility=template.target_volatility,
        max_drawdown_limit=template.max_drawdown_limit,
        stop_loss_threshold=template.stop_loss_threshold,
        benchmark_ticker=template.benchmark_ticker
    )

    return portfolio