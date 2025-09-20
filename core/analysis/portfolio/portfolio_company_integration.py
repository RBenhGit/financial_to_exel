"""
Portfolio-Company Integration Module
===================================

This module provides integration between portfolio holdings and the existing
financial analysis system, enabling portfolio-level analysis to leverage
individual company financial data, valuations, and market metrics.

Key Features:
- Links PortfolioHolding to FinancialCalculator results
- Aggregates individual company analysis to portfolio level
- Provides portfolio-weighted financial metrics
- Enables portfolio-level DCF and valuation analysis
- Integrates with existing data sources and calculation engines

Integration Points:
- FinancialCalculator for individual company analysis
- Enhanced Data Manager for multi-company data loading
- Market data integration for real-time portfolio valuation
- Excel data loading for comprehensive financial analysis
"""

from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, date
from dataclasses import dataclass, field
import logging

from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.data_contracts import (
    FinancialStatement,
    MarketData,
    CalculationResult,
    DataRequest,
    DataResponse,
    MetadataInfo
)
from .portfolio_models import Portfolio, PortfolioHolding, PortfolioAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class PortfolioCompanyData:
    """Complete financial data for a portfolio company"""

    ticker: str
    portfolio_weight: float

    # Financial Analysis Results
    financial_calculator: Optional[FinancialCalculator] = None
    latest_financials: Optional[FinancialStatement] = None
    market_data: Optional[MarketData] = None
    dcf_valuation: Optional[CalculationResult] = None
    ddm_valuation: Optional[CalculationResult] = None
    pb_analysis: Optional[CalculationResult] = None

    # Portfolio-Specific Metrics
    contribution_to_return: Optional[float] = None
    contribution_to_risk: Optional[float] = None
    weight_adjusted_metrics: Dict[str, float] = field(default_factory=dict)

    # Data Quality
    data_completeness: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: MetadataInfo = field(default_factory=MetadataInfo)

    def calculate_weighted_metrics(self) -> None:
        """Calculate portfolio-weighted financial metrics"""
        if not self.latest_financials:
            return

        # Weight-adjusted fundamental metrics
        metrics = {
            'revenue': self.latest_financials.revenue,
            'net_income': self.latest_financials.net_income,
            'operating_cash_flow': self.latest_financials.operating_cash_flow,
            'free_cash_flow': self.latest_financials.free_cash_flow,
            'total_assets': self.latest_financials.total_assets,
            'shareholders_equity': self.latest_financials.shareholders_equity
        }

        # Apply portfolio weight to each metric
        for metric_name, value in metrics.items():
            if value is not None:
                self.weight_adjusted_metrics[metric_name] = value * self.portfolio_weight

        # Add market data weighted metrics
        if self.market_data:
            market_metrics = {
                'market_cap': self.market_data.market_cap,
                'pe_ratio': self.market_data.pe_ratio,
                'pb_ratio': self.market_data.pb_ratio,
                'dividend_yield': self.market_data.dividend_yield,
                'beta': self.market_data.beta
            }

            for metric_name, value in market_metrics.items():
                if value is not None:
                    self.weight_adjusted_metrics[f"market_{metric_name}"] = value * self.portfolio_weight


class PortfolioCompanyIntegrator:
    """
    Integrates portfolio holdings with comprehensive financial analysis
    """

    def __init__(self):
        self.company_data_cache: Dict[str, PortfolioCompanyData] = {}
        self.financial_calculators: Dict[str, FinancialCalculator] = {}

    def load_portfolio_company_data(self, portfolio: Portfolio) -> Dict[str, PortfolioCompanyData]:
        """
        Load comprehensive financial data for all portfolio companies

        Args:
            portfolio: Portfolio instance with holdings

        Returns:
            Dictionary mapping ticker to PortfolioCompanyData
        """
        company_data = {}

        for holding in portfolio.holdings:
            try:
                logger.info(f"Loading financial data for {holding.ticker}")

                # Get or create financial calculator for the company
                calculator = self._get_financial_calculator(holding.ticker)

                # Create portfolio company data container
                portfolio_company = PortfolioCompanyData(
                    ticker=holding.ticker,
                    portfolio_weight=holding.current_weight,
                    financial_calculator=calculator
                )

                # Load financial statements
                portfolio_company.latest_financials = self._load_latest_financials(calculator)

                # Load market data
                portfolio_company.market_data = self._load_market_data(holding)

                # Run valuations if data is available
                if portfolio_company.latest_financials:
                    portfolio_company.dcf_valuation = self._run_dcf_valuation(calculator)
                    portfolio_company.ddm_valuation = self._run_ddm_valuation(calculator)
                    portfolio_company.pb_analysis = self._run_pb_analysis(calculator)

                # Calculate weighted metrics
                portfolio_company.calculate_weighted_metrics()

                # Assess data completeness
                portfolio_company.data_completeness = self._assess_data_completeness(portfolio_company)

                company_data[holding.ticker] = portfolio_company
                self.company_data_cache[holding.ticker] = portfolio_company

                # Update holding with analysis results
                self._update_holding_with_analysis(holding, portfolio_company)

            except Exception as e:
                logger.error(f"Failed to load data for {holding.ticker}: {str(e)}")
                # Create minimal data structure to avoid breaking portfolio analysis
                company_data[holding.ticker] = PortfolioCompanyData(
                    ticker=holding.ticker,
                    portfolio_weight=holding.current_weight,
                    data_completeness=0.0
                )

        return company_data

    def _get_financial_calculator(self, ticker: str) -> FinancialCalculator:
        """Get or create FinancialCalculator for a company"""
        if ticker not in self.financial_calculators:
            try:
                # Try to initialize with Excel data first
                calculator = FinancialCalculator(ticker=ticker)
                self.financial_calculators[ticker] = calculator
                logger.info(f"Created FinancialCalculator for {ticker}")
            except Exception as e:
                logger.warning(f"Failed to create FinancialCalculator for {ticker}: {str(e)}")
                # Create minimal calculator without Excel data
                calculator = FinancialCalculator(ticker=ticker, load_excel_data=False)
                self.financial_calculators[ticker] = calculator

        return self.financial_calculators[ticker]

    def _load_latest_financials(self, calculator: FinancialCalculator) -> Optional[FinancialStatement]:
        """Load latest financial statement data"""
        try:
            # Try to get financial data from the calculator
            if hasattr(calculator, 'get_financial_statement'):
                return calculator.get_financial_statement()
            elif hasattr(calculator, 'financial_data') and calculator.financial_data:
                # Convert calculator's internal data to FinancialStatement
                data = calculator.financial_data
                return FinancialStatement(
                    ticker=calculator.ticker,
                    revenue=data.get('revenue'),
                    net_income=data.get('net_income'),
                    operating_cash_flow=data.get('operating_cash_flow'),
                    free_cash_flow=data.get('free_cash_flow'),
                    total_assets=data.get('total_assets'),
                    shareholders_equity=data.get('shareholders_equity'),
                    shares_outstanding=data.get('shares_outstanding')
                )
        except Exception as e:
            logger.warning(f"Failed to load financials for {calculator.ticker}: {str(e)}")

        return None

    def _load_market_data(self, holding: PortfolioHolding) -> Optional[MarketData]:
        """Load market data for a holding"""
        try:
            # Use existing market data if available
            if holding.market_data:
                return holding.market_data

            # Create market data from holding information
            return MarketData(
                ticker=holding.ticker,
                price=holding.current_price,
                market_cap=holding.market_value if holding.shares else None,
                beta=holding.beta,
                dividend_yield=holding.dividend_yield
            )
        except Exception as e:
            logger.warning(f"Failed to load market data for {holding.ticker}: {str(e)}")
            return None

    def _run_dcf_valuation(self, calculator: FinancialCalculator) -> Optional[CalculationResult]:
        """Run DCF valuation analysis"""
        try:
            if hasattr(calculator, 'calculate_dcf'):
                dcf_result = calculator.calculate_dcf()
                if dcf_result:
                    return CalculationResult(
                        ticker=calculator.ticker,
                        calculation_type="DCF",
                        fair_value=dcf_result.get('intrinsic_value'),
                        current_price=dcf_result.get('current_price'),
                        discount_rate=dcf_result.get('wacc'),
                        terminal_growth_rate=dcf_result.get('terminal_growth_rate')
                    )
        except Exception as e:
            logger.warning(f"Failed to run DCF for {calculator.ticker}: {str(e)}")

        return None

    def _run_ddm_valuation(self, calculator: FinancialCalculator) -> Optional[CalculationResult]:
        """Run Dividend Discount Model valuation"""
        try:
            if hasattr(calculator, 'calculate_ddm'):
                ddm_result = calculator.calculate_ddm()
                if ddm_result:
                    return CalculationResult(
                        ticker=calculator.ticker,
                        calculation_type="DDM",
                        fair_value=ddm_result.get('fair_value'),
                        current_price=ddm_result.get('current_price'),
                        discount_rate=ddm_result.get('required_return')
                    )
        except Exception as e:
            logger.warning(f"Failed to run DDM for {calculator.ticker}: {str(e)}")

        return None

    def _run_pb_analysis(self, calculator: FinancialCalculator) -> Optional[CalculationResult]:
        """Run Price-to-Book analysis"""
        try:
            if hasattr(calculator, 'calculate_pb_analysis'):
                pb_result = calculator.calculate_pb_analysis()
                if pb_result:
                    return CalculationResult(
                        ticker=calculator.ticker,
                        calculation_type="P/B Analysis",
                        fair_value=pb_result.get('fair_value'),
                        current_price=pb_result.get('current_price')
                    )
        except Exception as e:
            logger.warning(f"Failed to run P/B analysis for {calculator.ticker}: {str(e)}")

        return None

    def _assess_data_completeness(self, portfolio_company: PortfolioCompanyData) -> float:
        """Assess the completeness of data for a portfolio company"""
        total_components = 5  # financials, market_data, dcf, ddm, pb
        available_components = 0

        if portfolio_company.latest_financials:
            available_components += 1
        if portfolio_company.market_data:
            available_components += 1
        if portfolio_company.dcf_valuation:
            available_components += 1
        if portfolio_company.ddm_valuation:
            available_components += 1
        if portfolio_company.pb_analysis:
            available_components += 1

        return available_components / total_components

    def _update_holding_with_analysis(self, holding: PortfolioHolding, portfolio_company: PortfolioCompanyData) -> None:
        """Update holding with analysis results"""
        # Update with financial data
        if portfolio_company.latest_financials:
            holding.financial_data = portfolio_company.latest_financials

        # Update with market data
        if portfolio_company.market_data:
            holding.market_data = portfolio_company.market_data
            if not holding.beta and portfolio_company.market_data.beta:
                holding.beta = portfolio_company.market_data.beta
            if not holding.dividend_yield and portfolio_company.market_data.dividend_yield:
                holding.dividend_yield = portfolio_company.market_data.dividend_yield

        # Update with best available valuation
        if portfolio_company.dcf_valuation:
            holding.valuation_result = portfolio_company.dcf_valuation
        elif portfolio_company.ddm_valuation:
            holding.valuation_result = portfolio_company.ddm_valuation
        elif portfolio_company.pb_analysis:
            holding.valuation_result = portfolio_company.pb_analysis

    def calculate_portfolio_weighted_metrics(self, portfolio: Portfolio,
                                           company_data: Dict[str, PortfolioCompanyData]) -> Dict[str, float]:
        """
        Calculate portfolio-level weighted financial metrics

        Args:
            portfolio: Portfolio instance
            company_data: Company data dictionary

        Returns:
            Dictionary of portfolio-weighted metrics
        """
        weighted_metrics = {}

        # Aggregate weighted metrics across all holdings
        for holding in portfolio.holdings:
            if holding.ticker in company_data:
                company = company_data[holding.ticker]
                for metric_name, value in company.weight_adjusted_metrics.items():
                    if metric_name not in weighted_metrics:
                        weighted_metrics[metric_name] = 0.0
                    weighted_metrics[metric_name] += value

        # Calculate portfolio-level ratios
        if 'market_cap' in weighted_metrics and weighted_metrics['market_cap'] > 0:
            # Portfolio-weighted P/E ratio
            if 'net_income' in weighted_metrics and weighted_metrics['net_income'] > 0:
                weighted_metrics['portfolio_pe'] = weighted_metrics['market_cap'] / weighted_metrics['net_income']

            # Portfolio-weighted P/B ratio
            if 'shareholders_equity' in weighted_metrics and weighted_metrics['shareholders_equity'] > 0:
                weighted_metrics['portfolio_pb'] = weighted_metrics['market_cap'] / weighted_metrics['shareholders_equity']

        # Portfolio beta (weighted average)
        total_weight = 0.0
        weighted_beta = 0.0
        for holding in portfolio.holdings:
            if holding.beta and holding.current_weight:
                weighted_beta += holding.beta * holding.current_weight
                total_weight += holding.current_weight

        if total_weight > 0:
            weighted_metrics['portfolio_beta'] = weighted_beta / total_weight

        return weighted_metrics

    def create_portfolio_analysis_result(self, portfolio: Portfolio) -> PortfolioAnalysisResult:
        """
        Create comprehensive portfolio analysis result

        Args:
            portfolio: Portfolio to analyze

        Returns:
            PortfolioAnalysisResult with complete analysis
        """
        # Load company data
        company_data = self.load_portfolio_company_data(portfolio)

        # Calculate weighted metrics
        weighted_metrics = self.calculate_portfolio_weighted_metrics(portfolio, company_data)

        # Create analysis result
        analysis = PortfolioAnalysisResult(
            portfolio_id=portfolio.portfolio_id,
            portfolio=portfolio,
            performance_metrics=weighted_metrics
        )

        # Add data completeness assessment
        if company_data:
            total_completeness = sum(cd.data_completeness for cd in company_data.values())
            analysis.data_completeness = total_completeness / len(company_data)

        # Add optimization recommendations
        analysis.optimization_suggestions = self._generate_optimization_suggestions(portfolio, company_data)

        # Add risk warnings
        analysis.risk_warnings = self._generate_risk_warnings(portfolio, company_data)

        return analysis

    def _generate_optimization_suggestions(self, portfolio: Portfolio,
                                         company_data: Dict[str, PortfolioCompanyData]) -> List[str]:
        """Generate portfolio optimization suggestions"""
        suggestions = []

        # Check concentration risk
        if portfolio.portfolio_metrics.concentration_risk > 0.25:
            suggestions.append(f"Consider reducing concentration risk - largest position is {portfolio.portfolio_metrics.concentration_risk:.1%}")

        # Check rebalancing needs
        if portfolio.portfolio_metrics.rebalancing_needed:
            suggestions.append(f"Portfolio deviates {portfolio.portfolio_metrics.deviation_from_targets:.1%} from targets - consider rebalancing")

        # Check undervalued holdings
        undervalued_count = 0
        for ticker, company in company_data.items():
            if company.dcf_valuation and company.dcf_valuation.upside_downside and company.dcf_valuation.upside_downside > 20:
                undervalued_count += 1

        if undervalued_count > 0:
            suggestions.append(f"{undervalued_count} holdings appear undervalued based on DCF analysis")

        return suggestions

    def _generate_risk_warnings(self, portfolio: Portfolio,
                               company_data: Dict[str, PortfolioCompanyData]) -> List[str]:
        """Generate risk warnings for the portfolio"""
        warnings = []

        # Data quality warnings
        low_quality_count = sum(1 for cd in company_data.values() if cd.data_completeness < 0.5)
        if low_quality_count > 0:
            warnings.append(f"{low_quality_count} holdings have incomplete financial data")

        # Diversification warnings
        if len(portfolio.holdings) < portfolio.min_holdings:
            warnings.append(f"Portfolio below minimum diversification threshold ({len(portfolio.holdings)} < {portfolio.min_holdings})")

        # High beta warning
        high_beta_count = sum(1 for h in portfolio.holdings if h.beta and h.beta > 1.5)
        if high_beta_count > len(portfolio.holdings) * 0.5:  # More than 50% high beta
            warnings.append("More than 50% of holdings have high beta (>1.5) - portfolio may be volatile")

        return warnings