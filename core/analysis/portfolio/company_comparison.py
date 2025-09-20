"""
Multi-Company Comparison Engine
==============================

This module provides comprehensive tools for comparing multiple companies across
various financial metrics, enabling portfolio-level analysis and relative valuation.

Key Features:
- Side-by-side financial metric comparisons
- Relative valuation analysis (P/E, P/B, EV/EBITDA)
- Sector and industry benchmarking
- Growth rate and trend analysis
- Ranking and scoring systems
- Statistical analysis and outlier detection

Integration:
- Works with existing FinancialCalculator and data contracts
- Supports portfolio holdings comparison
- Provides data for portfolio optimization
- Enables sector rotation strategies
"""

from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import logging
import statistics
from collections import defaultdict

import numpy as np
import pandas as pd

from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.data_contracts import (
    FinancialStatement,
    MarketData,
    CalculationResult,
    DataQuality,
    MetadataInfo
)
from .portfolio_models import Portfolio, PortfolioHolding
from .portfolio_company_integration import PortfolioCompanyData, PortfolioCompanyIntegrator

logger = logging.getLogger(__name__)


class ComparisonMetric(Enum):
    """Supported comparison metrics"""
    # Financial Statement Metrics
    REVENUE = "revenue"
    NET_INCOME = "net_income"
    OPERATING_CASH_FLOW = "operating_cash_flow"
    FREE_CASH_FLOW = "free_cash_flow"
    TOTAL_ASSETS = "total_assets"
    SHAREHOLDERS_EQUITY = "shareholders_equity"
    TOTAL_DEBT = "total_debt"

    # Market Metrics
    MARKET_CAP = "market_cap"
    ENTERPRISE_VALUE = "enterprise_value"
    PRICE = "price"

    # Valuation Ratios
    PE_RATIO = "pe_ratio"
    PB_RATIO = "pb_ratio"
    PS_RATIO = "ps_ratio"
    EV_REVENUE = "ev_revenue"
    EV_EBITDA = "ev_ebitda"

    # Profitability Ratios
    ROE = "roe"
    ROA = "roa"
    GROSS_MARGIN = "gross_margin"
    OPERATING_MARGIN = "operating_margin"
    NET_MARGIN = "net_margin"

    # Growth Metrics
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    FCF_GROWTH = "fcf_growth"

    # Risk Metrics
    BETA = "beta"
    DEBT_TO_EQUITY = "debt_to_equity"
    CURRENT_RATIO = "current_ratio"

    # Dividend Metrics
    DIVIDEND_YIELD = "dividend_yield"
    PAYOUT_RATIO = "payout_ratio"


class ComparisonType(Enum):
    """Types of comparisons"""
    ABSOLUTE = "absolute"              # Raw values
    RELATIVE = "relative"             # Percentiles/rankings
    NORMALIZED = "normalized"         # Z-scores
    RATIO_ANALYSIS = "ratio_analysis" # Ratio-based comparison


@dataclass
class CompanyMetrics:
    """Complete metrics for a single company"""

    ticker: str
    company_name: Optional[str] = None

    # Raw Financial Data
    financial_statement: Optional[FinancialStatement] = None
    market_data: Optional[MarketData] = None
    valuation_results: Dict[str, CalculationResult] = field(default_factory=dict)

    # Calculated Metrics
    calculated_metrics: Dict[str, float] = field(default_factory=dict)

    # Comparison Scores
    percentile_scores: Dict[str, float] = field(default_factory=dict)
    z_scores: Dict[str, float] = field(default_factory=dict)

    # Industry/Sector Context
    sector: Optional[str] = None
    industry: Optional[str] = None

    # Data Quality
    data_completeness: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: MetadataInfo = field(default_factory=MetadataInfo)

    def get_metric_value(self, metric: ComparisonMetric) -> Optional[float]:
        """Get the value for a specific metric"""
        # Check calculated metrics first
        if metric.value in self.calculated_metrics:
            return self.calculated_metrics[metric.value]

        # Check financial statement
        if self.financial_statement:
            if hasattr(self.financial_statement, metric.value):
                return getattr(self.financial_statement, metric.value)

        # Check market data
        if self.market_data:
            if hasattr(self.market_data, metric.value):
                return getattr(self.market_data, metric.value)

        return None

    def calculate_derived_metrics(self) -> None:
        """Calculate derived financial metrics"""
        if not self.financial_statement:
            return

        fs = self.financial_statement
        md = self.market_data

        # Profitability ratios
        if fs.net_income and fs.shareholders_equity and fs.shareholders_equity != 0:
            self.calculated_metrics['roe'] = fs.net_income / fs.shareholders_equity

        if fs.net_income and fs.total_assets and fs.total_assets != 0:
            self.calculated_metrics['roa'] = fs.net_income / fs.total_assets

        if fs.gross_profit and fs.revenue and fs.revenue != 0:
            self.calculated_metrics['gross_margin'] = fs.gross_profit / fs.revenue

        if fs.operating_income and fs.revenue and fs.revenue != 0:
            self.calculated_metrics['operating_margin'] = fs.operating_income / fs.revenue

        if fs.net_income and fs.revenue and fs.revenue != 0:
            self.calculated_metrics['net_margin'] = fs.net_income / fs.revenue

        # Leverage ratios
        if fs.total_debt and fs.shareholders_equity and fs.shareholders_equity != 0:
            self.calculated_metrics['debt_to_equity'] = fs.total_debt / fs.shareholders_equity

        if fs.current_assets and fs.current_liabilities and fs.current_liabilities != 0:
            self.calculated_metrics['current_ratio'] = fs.current_assets / fs.current_liabilities

        # Market-based ratios
        if md and md.market_cap and fs.revenue and fs.revenue != 0:
            self.calculated_metrics['ps_ratio'] = md.market_cap / fs.revenue


@dataclass
class ComparisonMatrix:
    """Multi-company comparison matrix"""

    comparison_id: str
    comparison_date: datetime = field(default_factory=datetime.now)
    comparison_type: ComparisonType = ComparisonType.ABSOLUTE

    # Companies and Metrics
    companies: List[CompanyMetrics] = field(default_factory=list)
    metrics: List[ComparisonMetric] = field(default_factory=list)

    # Comparison Results
    comparison_table: pd.DataFrame = field(default_factory=pd.DataFrame)
    rankings: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)
    sector_averages: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Statistical Analysis
    correlation_matrix: Optional[pd.DataFrame] = None
    outliers: Dict[str, List[str]] = field(default_factory=dict)  # metric -> list of outlier tickers

    # Metadata
    data_quality: DataQuality = DataQuality.UNKNOWN
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


class MultiCompanyComparator:
    """
    Engine for multi-company financial analysis and comparison
    """

    def __init__(self):
        self.company_integrator = PortfolioCompanyIntegrator()
        self.cached_company_data: Dict[str, CompanyMetrics] = {}

    def load_company_metrics(self, tickers: List[str]) -> Dict[str, CompanyMetrics]:
        """
        Load comprehensive metrics for multiple companies

        Args:
            tickers: List of ticker symbols

        Returns:
            Dictionary mapping ticker to CompanyMetrics
        """
        company_metrics = {}

        for ticker in tickers:
            try:
                logger.info(f"Loading metrics for {ticker}")

                # Check cache first
                if ticker in self.cached_company_data:
                    company_metrics[ticker] = self.cached_company_data[ticker]
                    continue

                # Create company metrics
                metrics = CompanyMetrics(ticker=ticker)

                # Load financial calculator and data
                calculator = self.company_integrator._get_financial_calculator(ticker)

                # Load financial statements
                metrics.financial_statement = self.company_integrator._load_latest_financials(calculator)

                # Load market data
                if hasattr(calculator, 'get_market_data'):
                    try:
                        market_data = calculator.get_market_data()
                        if market_data:
                            metrics.market_data = market_data
                    except Exception as e:
                        logger.warning(f"Failed to load market data for {ticker}: {str(e)}")

                # Load valuation results
                for valuation_type in ['dcf', 'ddm', 'pb']:
                    try:
                        if hasattr(calculator, f'calculate_{valuation_type}'):
                            result = getattr(calculator, f'calculate_{valuation_type}')()
                            if result:
                                calc_result = CalculationResult(
                                    ticker=ticker,
                                    calculation_type=valuation_type.upper(),
                                    fair_value=result.get('fair_value') or result.get('intrinsic_value'),
                                    current_price=result.get('current_price')
                                )
                                metrics.valuation_results[valuation_type] = calc_result
                    except Exception as e:
                        logger.warning(f"Failed to calculate {valuation_type} for {ticker}: {str(e)}")

                # Calculate derived metrics
                metrics.calculate_derived_metrics()

                # Assess data completeness
                metrics.data_completeness = self._assess_data_completeness(metrics)

                company_metrics[ticker] = metrics
                self.cached_company_data[ticker] = metrics

            except Exception as e:
                logger.error(f"Failed to load metrics for {ticker}: {str(e)}")
                # Create minimal metrics to avoid breaking comparison
                company_metrics[ticker] = CompanyMetrics(ticker=ticker, data_completeness=0.0)

        return company_metrics

    def create_comparison_matrix(self,
                                tickers: List[str],
                                metrics: List[ComparisonMetric],
                                comparison_type: ComparisonType = ComparisonType.ABSOLUTE) -> ComparisonMatrix:
        """
        Create comprehensive comparison matrix

        Args:
            tickers: List of company tickers to compare
            metrics: List of metrics to include in comparison
            comparison_type: Type of comparison to perform

        Returns:
            ComparisonMatrix with results
        """
        # Load company data
        company_data = self.load_company_metrics(tickers)

        # Create comparison matrix
        matrix = ComparisonMatrix(
            comparison_id=f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            comparison_type=comparison_type,
            companies=[company_data[ticker] for ticker in tickers],
            metrics=metrics
        )

        # Build comparison table
        matrix.comparison_table = self._build_comparison_table(company_data, metrics, comparison_type)

        # Calculate rankings
        matrix.rankings = self._calculate_rankings(company_data, metrics)

        # Calculate sector averages
        matrix.sector_averages = self._calculate_sector_averages(company_data, metrics)

        # Statistical analysis
        matrix.correlation_matrix = self._calculate_correlation_matrix(matrix.comparison_table)
        matrix.outliers = self._detect_outliers(matrix.comparison_table)

        # Assess overall data quality
        matrix.data_quality = self._assess_comparison_quality(company_data)

        return matrix

    def _build_comparison_table(self,
                               company_data: Dict[str, CompanyMetrics],
                               metrics: List[ComparisonMetric],
                               comparison_type: ComparisonType) -> pd.DataFrame:
        """Build the main comparison table"""

        # Create base table with raw values
        data = {}
        for ticker, company in company_data.items():
            data[ticker] = {}
            for metric in metrics:
                value = company.get_metric_value(metric)
                data[ticker][metric.value] = value

        df = pd.DataFrame(data).T  # Transpose so companies are rows

        # Apply comparison type transformations
        if comparison_type == ComparisonType.RELATIVE:
            # Convert to percentiles
            for col in df.columns:
                df[col] = df[col].rank(pct=True, na_option='keep') * 100

        elif comparison_type == ComparisonType.NORMALIZED:
            # Convert to z-scores
            for col in df.columns:
                if df[col].std() != 0:
                    df[col] = (df[col] - df[col].mean()) / df[col].std()

        elif comparison_type == ComparisonType.RATIO_ANALYSIS:
            # Convert to ratios vs median
            for col in df.columns:
                median_val = df[col].median()
                if median_val != 0 and not pd.isna(median_val):
                    df[col] = df[col] / median_val

        return df

    def _calculate_rankings(self,
                           company_data: Dict[str, CompanyMetrics],
                           metrics: List[ComparisonMetric]) -> Dict[str, List[Tuple[str, float]]]:
        """Calculate rankings for each metric"""
        rankings = {}

        for metric in metrics:
            metric_values = []
            for ticker, company in company_data.items():
                value = company.get_metric_value(metric)
                if value is not None:
                    metric_values.append((ticker, value))

            # Sort based on metric type (higher is better for most, lower for some)
            reverse_sort = metric not in [ComparisonMetric.PE_RATIO, ComparisonMetric.PB_RATIO,
                                        ComparisonMetric.DEBT_TO_EQUITY, ComparisonMetric.BETA]

            metric_values.sort(key=lambda x: x[1], reverse=reverse_sort)
            rankings[metric.value] = metric_values

        return rankings

    def _calculate_sector_averages(self,
                                  company_data: Dict[str, CompanyMetrics],
                                  metrics: List[ComparisonMetric]) -> Dict[str, Dict[str, float]]:
        """Calculate sector average metrics"""
        sector_data = defaultdict(lambda: defaultdict(list))

        # Group data by sector
        for company in company_data.values():
            sector = company.sector or "Unknown"
            for metric in metrics:
                value = company.get_metric_value(metric)
                if value is not None:
                    sector_data[sector][metric.value].append(value)

        # Calculate averages
        sector_averages = {}
        for sector, metrics_data in sector_data.items():
            sector_averages[sector] = {}
            for metric_name, values in metrics_data.items():
                if values:
                    sector_averages[sector][metric_name] = statistics.mean(values)

        return sector_averages

    def _calculate_correlation_matrix(self, comparison_table: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix between metrics"""
        try:
            # Only include numeric columns with sufficient data
            numeric_cols = comparison_table.select_dtypes(include=[np.number]).columns
            correlation_data = comparison_table[numeric_cols].dropna(thresh=2)  # At least 2 non-null values

            if len(correlation_data) >= 2:
                return correlation_data.corr()
        except Exception as e:
            logger.warning(f"Failed to calculate correlation matrix: {str(e)}")

        return pd.DataFrame()

    def _detect_outliers(self, comparison_table: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect outliers using IQR method"""
        outliers = {}

        for col in comparison_table.select_dtypes(include=[np.number]).columns:
            column_data = comparison_table[col].dropna()
            if len(column_data) >= 4:  # Need at least 4 values for quartiles
                Q1 = column_data.quantile(0.25)
                Q3 = column_data.quantile(0.75)
                IQR = Q3 - Q1

                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outlier_tickers = []
                for ticker, value in column_data.items():
                    if value < lower_bound or value > upper_bound:
                        outlier_tickers.append(ticker)

                if outlier_tickers:
                    outliers[col] = outlier_tickers

        return outliers

    def _assess_data_completeness(self, company_metrics: CompanyMetrics) -> float:
        """Assess data completeness for a company"""
        total_fields = 0
        complete_fields = 0

        # Check financial statement completeness
        if company_metrics.financial_statement:
            fs_fields = ['revenue', 'net_income', 'operating_cash_flow', 'free_cash_flow',
                        'total_assets', 'shareholders_equity', 'total_debt']
            for field in fs_fields:
                total_fields += 1
                if getattr(company_metrics.financial_statement, field, None) is not None:
                    complete_fields += 1

        # Check market data completeness
        if company_metrics.market_data:
            md_fields = ['price', 'market_cap', 'pe_ratio', 'pb_ratio', 'beta']
            for field in md_fields:
                total_fields += 1
                if getattr(company_metrics.market_data, field, None) is not None:
                    complete_fields += 1

        # Check valuation results
        total_fields += 3  # DCF, DDM, P/B
        complete_fields += len(company_metrics.valuation_results)

        return complete_fields / total_fields if total_fields > 0 else 0.0

    def _assess_comparison_quality(self, company_data: Dict[str, CompanyMetrics]) -> DataQuality:
        """Assess overall comparison data quality"""
        if not company_data:
            return DataQuality.POOR

        avg_completeness = sum(c.data_completeness for c in company_data.values()) / len(company_data)

        if avg_completeness >= 0.8:
            return DataQuality.EXCELLENT
        elif avg_completeness >= 0.6:
            return DataQuality.GOOD
        elif avg_completeness >= 0.4:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR

    def compare_portfolio_holdings(self, portfolio: Portfolio) -> ComparisonMatrix:
        """
        Compare all holdings within a portfolio

        Args:
            portfolio: Portfolio to analyze

        Returns:
            ComparisonMatrix comparing all holdings
        """
        tickers = [holding.ticker for holding in portfolio.holdings]

        # Standard metrics for portfolio comparison
        metrics = [
            ComparisonMetric.MARKET_CAP,
            ComparisonMetric.PE_RATIO,
            ComparisonMetric.PB_RATIO,
            ComparisonMetric.ROE,
            ComparisonMetric.DEBT_TO_EQUITY,
            ComparisonMetric.REVENUE_GROWTH,
            ComparisonMetric.FREE_CASH_FLOW,
            ComparisonMetric.BETA,
            ComparisonMetric.DIVIDEND_YIELD
        ]

        return self.create_comparison_matrix(tickers, metrics, ComparisonType.ABSOLUTE)

    def find_similar_companies(self,
                              reference_ticker: str,
                              candidate_tickers: List[str],
                              similarity_metrics: Optional[List[ComparisonMetric]] = None) -> List[Tuple[str, float]]:
        """
        Find companies similar to a reference company

        Args:
            reference_ticker: Reference company ticker
            candidate_tickers: List of candidate tickers to compare
            similarity_metrics: Metrics to use for similarity calculation

        Returns:
            List of (ticker, similarity_score) tuples, sorted by similarity
        """
        if similarity_metrics is None:
            similarity_metrics = [
                ComparisonMetric.PE_RATIO,
                ComparisonMetric.PB_RATIO,
                ComparisonMetric.ROE,
                ComparisonMetric.DEBT_TO_EQUITY,
                ComparisonMetric.MARKET_CAP
            ]

        # Load data for all companies
        all_tickers = [reference_ticker] + candidate_tickers
        company_data = self.load_company_metrics(all_tickers)

        reference_company = company_data.get(reference_ticker)
        if not reference_company:
            return []

        # Calculate similarity scores
        similarity_scores = []

        for ticker in candidate_tickers:
            candidate = company_data.get(ticker)
            if not candidate:
                continue

            # Calculate Euclidean distance in normalized space
            distances = []
            for metric in similarity_metrics:
                ref_value = reference_company.get_metric_value(metric)
                cand_value = candidate.get_metric_value(metric)

                if ref_value is not None and cand_value is not None and ref_value != 0:
                    # Normalize by reference value
                    normalized_distance = abs((cand_value - ref_value) / ref_value)
                    distances.append(normalized_distance)

            if distances:
                # Convert distance to similarity (0-1, where 1 is most similar)
                avg_distance = sum(distances) / len(distances)
                similarity = 1.0 / (1.0 + avg_distance)
                similarity_scores.append((ticker, similarity))

        # Sort by similarity (highest first)
        similarity_scores.sort(key=lambda x: x[1], reverse=True)

        return similarity_scores

    def generate_comparison_summary(self, matrix: ComparisonMatrix) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of the comparison

        Args:
            matrix: ComparisonMatrix to summarize

        Returns:
            Dictionary with summary statistics and insights
        """
        summary = {
            'comparison_overview': {
                'companies_analyzed': len(matrix.companies),
                'metrics_compared': len(matrix.metrics),
                'comparison_type': matrix.comparison_type.value,
                'data_quality': matrix.data_quality.value,
                'analysis_date': matrix.comparison_date
            },
            'top_performers': {},
            'sector_leaders': {},
            'valuation_insights': {},
            'risk_assessment': {},
            'correlations': {},
            'outliers': matrix.outliers
        }

        # Top performers by metric
        for metric_name, rankings in matrix.rankings.items():
            if rankings:
                summary['top_performers'][metric_name] = rankings[:3]  # Top 3

        # Sector analysis
        for sector, averages in matrix.sector_averages.items():
            summary['sector_leaders'][sector] = averages

        # Valuation insights
        if not matrix.comparison_table.empty:
            valuation_metrics = ['pe_ratio', 'pb_ratio', 'ps_ratio']
            for metric in valuation_metrics:
                if metric in matrix.comparison_table.columns:
                    col_data = matrix.comparison_table[metric].dropna()
                    if len(col_data) > 0:
                        summary['valuation_insights'][metric] = {
                            'median': float(col_data.median()),
                            'min': float(col_data.min()),
                            'max': float(col_data.max()),
                            'std': float(col_data.std()) if len(col_data) > 1 else 0.0
                        }

        # Risk assessment
        risk_metrics = ['beta', 'debt_to_equity']
        for metric in risk_metrics:
            if metric in matrix.comparison_table.columns:
                col_data = matrix.comparison_table[metric].dropna()
                if len(col_data) > 0:
                    high_risk_threshold = col_data.quantile(0.75)
                    high_risk_companies = matrix.comparison_table[
                        matrix.comparison_table[metric] > high_risk_threshold
                    ].index.tolist()
                    summary['risk_assessment'][f'high_{metric}'] = high_risk_companies

        # Key correlations
        if matrix.correlation_matrix is not None and not matrix.correlation_matrix.empty:
            corr_pairs = []
            for i in range(len(matrix.correlation_matrix.columns)):
                for j in range(i+1, len(matrix.correlation_matrix.columns)):
                    metric1 = matrix.correlation_matrix.columns[i]
                    metric2 = matrix.correlation_matrix.columns[j]
                    corr_value = matrix.correlation_matrix.iloc[i, j]
                    if not pd.isna(corr_value) and abs(corr_value) > 0.5:
                        corr_pairs.append((metric1, metric2, float(corr_value)))

            summary['correlations']['strong_correlations'] = sorted(
                corr_pairs, key=lambda x: abs(x[2]), reverse=True
            )[:5]  # Top 5 strongest correlations

        return summary