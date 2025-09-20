"""
Relative Valuation Analysis Module
=================================

This module provides sophisticated relative valuation analysis tools for comparing
companies based on valuation multiples, growth rates, and industry benchmarks.

Key Features:
- Comprehensive valuation multiple analysis (P/E, P/B, EV/EBITDA, P/S)
- Sector and industry benchmarking
- Growth-adjusted valuations (PEG ratios, growth-adjusted P/B)
- Statistical valuation models
- Fair value estimation based on peer comparisons
- Outlier detection and analysis

Integration:
- Works with existing financial analysis infrastructure
- Supports portfolio-level valuation analysis
- Provides inputs for portfolio optimization
- Enables sector rotation strategies
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import logging
import statistics

import numpy as np
import pandas as pd
from scipy import stats

from .company_comparison import CompanyMetrics, MultiCompanyComparator, ComparisonMetric
from core.data_processing.data_contracts import CalculationResult, MetadataInfo

logger = logging.getLogger(__name__)


class ValuationMultiple(Enum):
    """Supported valuation multiples"""
    PRICE_TO_EARNINGS = "pe_ratio"
    PRICE_TO_BOOK = "pb_ratio"
    PRICE_TO_SALES = "ps_ratio"
    EV_TO_REVENUE = "ev_revenue"
    EV_TO_EBITDA = "ev_ebitda"
    PRICE_TO_FCF = "price_to_fcf"
    EV_TO_FCF = "ev_to_fcf"
    PEG_RATIO = "peg_ratio"


class GrowthMetric(Enum):
    """Growth metrics for trend analysis"""
    REVENUE_GROWTH = "revenue_growth"
    EARNINGS_GROWTH = "earnings_growth"
    FCF_GROWTH = "fcf_growth"
    DIVIDEND_GROWTH = "dividend_growth"
    BOOK_VALUE_GROWTH = "book_value_growth"


@dataclass
class ValuationBenchmark:
    """Industry/sector valuation benchmarks"""

    sector: str
    industry: Optional[str] = None
    benchmark_date: datetime = field(default_factory=datetime.now)

    # Valuation Multiple Benchmarks
    pe_percentiles: Dict[str, float] = field(default_factory=dict)  # 25th, 50th, 75th percentiles
    pb_percentiles: Dict[str, float] = field(default_factory=dict)
    ps_percentiles: Dict[str, float] = field(default_factory=dict)
    ev_ebitda_percentiles: Dict[str, float] = field(default_factory=dict)

    # Growth Benchmarks
    revenue_growth_stats: Dict[str, float] = field(default_factory=dict)
    earnings_growth_stats: Dict[str, float] = field(default_factory=dict)

    # Risk Benchmarks
    beta_stats: Dict[str, float] = field(default_factory=dict)
    debt_equity_stats: Dict[str, float] = field(default_factory=dict)

    # Sample size and quality
    sample_size: int = 0
    data_quality_score: float = 0.0

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


@dataclass
class RelativeValuationResult:
    """Result of relative valuation analysis"""

    ticker: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Current Valuation Multiples
    current_multiples: Dict[str, float] = field(default_factory=dict)

    # Peer Comparison
    peer_multiples: Dict[str, Dict[str, float]] = field(default_factory=dict)  # peer_ticker -> multiples
    multiple_percentiles: Dict[str, float] = field(default_factory=dict)  # where company ranks vs peers

    # Sector/Industry Comparison
    sector_comparison: Dict[str, float] = field(default_factory=dict)  # vs sector averages
    industry_comparison: Dict[str, float] = field(default_factory=dict)  # vs industry averages

    # Fair Value Estimates
    peer_based_fair_values: Dict[str, float] = field(default_factory=dict)  # method -> fair_value
    sector_based_fair_values: Dict[str, float] = field(default_factory=dict)
    blended_fair_value: Optional[float] = None

    # Growth-Adjusted Analysis
    peg_analysis: Dict[str, float] = field(default_factory=dict)
    growth_adjusted_pb: Optional[float] = None

    # Statistical Analysis
    valuation_z_scores: Dict[str, float] = field(default_factory=dict)  # how many std devs from mean
    outlier_flags: Dict[str, bool] = field(default_factory=dict)  # which multiples are outliers

    # Investment Recommendation
    relative_valuation_score: float = 0.0  # 0-100 score
    recommendation: str = "HOLD"  # BUY, HOLD, SELL
    confidence_level: float = 0.0  # 0-1 confidence in recommendation

    # Supporting Data
    peer_tickers: List[str] = field(default_factory=list)
    benchmark_data: Optional[ValuationBenchmark] = None

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


class RelativeValuationAnalyzer:
    """
    Comprehensive relative valuation analysis engine
    """

    def __init__(self):
        self.comparator = MultiCompanyComparator()
        self.benchmark_cache: Dict[str, ValuationBenchmark] = {}

    def analyze_relative_valuation(self,
                                 target_ticker: str,
                                 peer_tickers: List[str],
                                 sector: Optional[str] = None) -> RelativeValuationResult:
        """
        Perform comprehensive relative valuation analysis

        Args:
            target_ticker: Company to analyze
            peer_tickers: Peer companies for comparison
            sector: Sector for benchmarking (optional)

        Returns:
            RelativeValuationResult with complete analysis
        """
        logger.info(f"Starting relative valuation analysis for {target_ticker}")

        # Load company data
        all_tickers = [target_ticker] + peer_tickers
        company_data = self.comparator.load_company_metrics(all_tickers)

        target_company = company_data.get(target_ticker)
        if not target_company:
            raise ValueError(f"Could not load data for target company {target_ticker}")

        # Initialize result
        result = RelativeValuationResult(
            ticker=target_ticker,
            peer_tickers=peer_tickers
        )

        # Calculate current multiples
        result.current_multiples = self._calculate_valuation_multiples(target_company)

        # Peer comparison analysis
        result.peer_multiples = self._calculate_peer_multiples(company_data, peer_tickers)
        result.multiple_percentiles = self._calculate_multiple_percentiles(
            target_ticker, company_data, all_tickers
        )

        # Sector/industry benchmarking
        if sector:
            benchmark = self._get_sector_benchmark(sector, company_data)
            result.benchmark_data = benchmark
            result.sector_comparison = self._compare_to_benchmark(
                result.current_multiples, benchmark
            )

        # Fair value estimation
        result.peer_based_fair_values = self._estimate_peer_based_fair_values(
            target_company, result.peer_multiples
        )

        if result.benchmark_data:
            result.sector_based_fair_values = self._estimate_sector_based_fair_values(
                target_company, result.benchmark_data
            )

        result.blended_fair_value = self._calculate_blended_fair_value(
            result.peer_based_fair_values, result.sector_based_fair_values
        )

        # Growth-adjusted analysis
        result.peg_analysis = self._calculate_peg_analysis(target_company, company_data, peer_tickers)
        result.growth_adjusted_pb = self._calculate_growth_adjusted_pb(target_company)

        # Statistical analysis
        result.valuation_z_scores = self._calculate_valuation_z_scores(
            target_ticker, company_data, all_tickers
        )
        result.outlier_flags = self._detect_valuation_outliers(result.valuation_z_scores)

        # Investment recommendation
        result.relative_valuation_score = self._calculate_valuation_score(result)
        result.recommendation, result.confidence_level = self._generate_recommendation(result)

        logger.info(f"Completed relative valuation analysis for {target_ticker}")
        return result

    def _calculate_valuation_multiples(self, company: CompanyMetrics) -> Dict[str, float]:
        """Calculate all valuation multiples for a company"""
        multiples = {}

        # Basic multiples from market data
        if company.market_data:
            for field in ['pe_ratio', 'pb_ratio', 'ps_ratio', 'peg_ratio']:
                value = getattr(company.market_data, field, None)
                if value is not None:
                    multiples[field] = value

        # Calculate additional multiples
        if company.financial_statement and company.market_data:
            fs = company.financial_statement
            md = company.market_data

            # Price to FCF
            if fs.free_cash_flow and md.market_cap and fs.free_cash_flow > 0:
                multiples['price_to_fcf'] = md.market_cap / fs.free_cash_flow

            # EV multiples (if we have enterprise value)
            if md.enterprise_value:
                if fs.revenue and fs.revenue > 0:
                    multiples['ev_revenue'] = md.enterprise_value / fs.revenue
                if fs.ebitda and fs.ebitda > 0:
                    multiples['ev_ebitda'] = md.enterprise_value / fs.ebitda
                if fs.free_cash_flow and fs.free_cash_flow > 0:
                    multiples['ev_to_fcf'] = md.enterprise_value / fs.free_cash_flow

        return multiples

    def _calculate_peer_multiples(self,
                                company_data: Dict[str, CompanyMetrics],
                                peer_tickers: List[str]) -> Dict[str, Dict[str, float]]:
        """Calculate multiples for all peer companies"""
        peer_multiples = {}

        for ticker in peer_tickers:
            if ticker in company_data:
                peer_multiples[ticker] = self._calculate_valuation_multiples(company_data[ticker])

        return peer_multiples

    def _calculate_multiple_percentiles(self,
                                      target_ticker: str,
                                      company_data: Dict[str, CompanyMetrics],
                                      all_tickers: List[str]) -> Dict[str, float]:
        """Calculate where target company ranks vs peers for each multiple"""
        percentiles = {}
        target_multiples = self._calculate_valuation_multiples(company_data[target_ticker])

        for multiple_name in target_multiples:
            target_value = target_multiples[multiple_name]
            peer_values = []

            for ticker in all_tickers:
                if ticker != target_ticker and ticker in company_data:
                    peer_multiples = self._calculate_valuation_multiples(company_data[ticker])
                    if multiple_name in peer_multiples:
                        peer_values.append(peer_multiples[multiple_name])

            if peer_values and target_value is not None:
                # Calculate percentile rank
                peer_values.append(target_value)
                peer_values.sort()
                rank = peer_values.index(target_value) + 1
                percentile = (rank / len(peer_values)) * 100
                percentiles[multiple_name] = percentile

        return percentiles

    def _get_sector_benchmark(self,
                            sector: str,
                            company_data: Dict[str, CompanyMetrics]) -> ValuationBenchmark:
        """Get or create sector benchmark"""
        if sector in self.benchmark_cache:
            return self.benchmark_cache[sector]

        # Create benchmark from available data
        benchmark = ValuationBenchmark(sector=sector)

        # Collect sector companies
        sector_companies = [c for c in company_data.values() if c.sector == sector]
        benchmark.sample_size = len(sector_companies)

        if sector_companies:
            # Calculate valuation multiple percentiles
            for multiple_type in ['pe_ratio', 'pb_ratio', 'ps_ratio']:
                values = []
                for company in sector_companies:
                    multiples = self._calculate_valuation_multiples(company)
                    if multiple_type in multiples:
                        values.append(multiples[multiple_type])

                if values:
                    benchmark.__dict__[f"{multiple_type.split('_')[0]}_percentiles"] = {
                        '25th': np.percentile(values, 25),
                        '50th': np.percentile(values, 50),
                        '75th': np.percentile(values, 75),
                        'mean': np.mean(values),
                        'std': np.std(values)
                    }

        self.benchmark_cache[sector] = benchmark
        return benchmark

    def _compare_to_benchmark(self,
                            current_multiples: Dict[str, float],
                            benchmark: ValuationBenchmark) -> Dict[str, float]:
        """Compare company multiples to sector benchmark"""
        comparison = {}

        for multiple_name, value in current_multiples.items():
            if value is None:
                continue

            # Map multiple name to benchmark field
            benchmark_field = f"{multiple_name.split('_')[0]}_percentiles"
            if hasattr(benchmark, benchmark_field):
                percentiles = getattr(benchmark, benchmark_field)
                if percentiles and '50th' in percentiles:
                    # Calculate ratio to median
                    median = percentiles['50th']
                    if median != 0:
                        comparison[f"{multiple_name}_vs_sector"] = value / median

                    # Calculate z-score if std available
                    if 'mean' in percentiles and 'std' in percentiles and percentiles['std'] != 0:
                        z_score = (value - percentiles['mean']) / percentiles['std']
                        comparison[f"{multiple_name}_z_score"] = z_score

        return comparison

    def _estimate_peer_based_fair_values(self,
                                       target_company: CompanyMetrics,
                                       peer_multiples: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        """Estimate fair values based on peer multiples"""
        fair_values = {}

        if not target_company.financial_statement or not target_company.market_data:
            return fair_values

        fs = target_company.financial_statement
        md = target_company.market_data

        # Calculate median peer multiples
        multiple_medians = {}
        for multiple_name in ['pe_ratio', 'pb_ratio', 'ps_ratio', 'price_to_fcf']:
            values = []
            for peer_data in peer_multiples.values():
                if multiple_name in peer_data:
                    values.append(peer_data[multiple_name])
            if values:
                multiple_medians[multiple_name] = statistics.median(values)

        # Apply median multiples to target company fundamentals
        if 'pe_ratio' in multiple_medians and fs.earnings_per_share:
            fair_values['pe_based'] = multiple_medians['pe_ratio'] * fs.earnings_per_share

        if 'pb_ratio' in multiple_medians and fs.book_value and fs.shares_outstanding:
            book_value_per_share = fs.book_value / fs.shares_outstanding
            fair_values['pb_based'] = multiple_medians['pb_ratio'] * book_value_per_share

        if 'ps_ratio' in multiple_medians and fs.revenue and fs.shares_outstanding:
            sales_per_share = fs.revenue / fs.shares_outstanding
            fair_values['ps_based'] = multiple_medians['ps_ratio'] * sales_per_share

        if 'price_to_fcf' in multiple_medians and fs.free_cash_flow and fs.shares_outstanding:
            fcf_per_share = fs.free_cash_flow / fs.shares_outstanding
            fair_values['fcf_based'] = multiple_medians['price_to_fcf'] * fcf_per_share

        return fair_values

    def _estimate_sector_based_fair_values(self,
                                         target_company: CompanyMetrics,
                                         benchmark: ValuationBenchmark) -> Dict[str, float]:
        """Estimate fair values based on sector benchmarks"""
        fair_values = {}

        if not target_company.financial_statement:
            return fair_values

        fs = target_company.financial_statement

        # Use sector median multiples
        if benchmark.pe_percentiles and '50th' in benchmark.pe_percentiles and fs.earnings_per_share:
            sector_pe = benchmark.pe_percentiles['50th']
            fair_values['sector_pe_based'] = sector_pe * fs.earnings_per_share

        if benchmark.pb_percentiles and '50th' in benchmark.pb_percentiles:
            if fs.book_value and fs.shares_outstanding:
                sector_pb = benchmark.pb_percentiles['50th']
                book_value_per_share = fs.book_value / fs.shares_outstanding
                fair_values['sector_pb_based'] = sector_pb * book_value_per_share

        if benchmark.ps_percentiles and '50th' in benchmark.ps_percentiles:
            if fs.revenue and fs.shares_outstanding:
                sector_ps = benchmark.ps_percentiles['50th']
                sales_per_share = fs.revenue / fs.shares_outstanding
                fair_values['sector_ps_based'] = sector_ps * sales_per_share

        return fair_values

    def _calculate_blended_fair_value(self,
                                    peer_values: Dict[str, float],
                                    sector_values: Dict[str, float]) -> Optional[float]:
        """Calculate blended fair value from multiple methods"""
        all_values = list(peer_values.values()) + list(sector_values.values())

        if not all_values:
            return None

        # Remove outliers (values more than 2 std devs from mean)
        if len(all_values) > 2:
            mean_val = statistics.mean(all_values)
            std_val = statistics.stdev(all_values)
            filtered_values = [v for v in all_values if abs(v - mean_val) <= 2 * std_val]
            if filtered_values:
                all_values = filtered_values

        # Return median of remaining values
        return statistics.median(all_values)

    def _calculate_peg_analysis(self,
                              target_company: CompanyMetrics,
                              company_data: Dict[str, CompanyMetrics],
                              peer_tickers: List[str]) -> Dict[str, float]:
        """Calculate PEG ratio analysis"""
        peg_analysis = {}

        # Get target PEG if available
        if target_company.market_data and target_company.market_data.peg_ratio:
            peg_analysis['target_peg'] = target_company.market_data.peg_ratio

        # Calculate peer PEG statistics
        peer_pegs = []
        for ticker in peer_tickers:
            if ticker in company_data:
                peer = company_data[ticker]
                if peer.market_data and peer.market_data.peg_ratio:
                    peer_pegs.append(peer.market_data.peg_ratio)

        if peer_pegs:
            peg_analysis['peer_peg_median'] = statistics.median(peer_pegs)
            peg_analysis['peer_peg_mean'] = statistics.mean(peer_pegs)
            if len(peer_pegs) > 1:
                peg_analysis['peer_peg_std'] = statistics.stdev(peer_pegs)

        return peg_analysis

    def _calculate_growth_adjusted_pb(self, target_company: CompanyMetrics) -> Optional[float]:
        """Calculate growth-adjusted P/B ratio (placeholder for full implementation)"""
        # This would require historical growth data
        # For now, return None to indicate calculation not available
        return None

    def _calculate_valuation_z_scores(self,
                                    target_ticker: str,
                                    company_data: Dict[str, CompanyMetrics],
                                    all_tickers: List[str]) -> Dict[str, float]:
        """Calculate z-scores for valuation multiples"""
        z_scores = {}
        target_multiples = self._calculate_valuation_multiples(company_data[target_ticker])

        for multiple_name in target_multiples:
            target_value = target_multiples[multiple_name]
            peer_values = []

            for ticker in all_tickers:
                if ticker != target_ticker and ticker in company_data:
                    peer_multiples = self._calculate_valuation_multiples(company_data[ticker])
                    if multiple_name in peer_multiples:
                        peer_values.append(peer_multiples[multiple_name])

            if len(peer_values) > 1 and target_value is not None:
                peer_mean = statistics.mean(peer_values)
                peer_std = statistics.stdev(peer_values)
                if peer_std != 0:
                    z_scores[multiple_name] = (target_value - peer_mean) / peer_std

        return z_scores

    def _detect_valuation_outliers(self, z_scores: Dict[str, float]) -> Dict[str, bool]:
        """Detect outlier valuations (z-score > 2 or < -2)"""
        outliers = {}
        for multiple_name, z_score in z_scores.items():
            outliers[multiple_name] = abs(z_score) > 2.0
        return outliers

    def _calculate_valuation_score(self, result: RelativeValuationResult) -> float:
        """Calculate overall relative valuation score (0-100)"""
        score_components = []

        # Percentile-based scoring (lower percentiles = better value)
        for multiple, percentile in result.multiple_percentiles.items():
            if multiple in ['pe_ratio', 'pb_ratio', 'ps_ratio']:  # Lower is better
                component_score = 100 - percentile
            else:  # Higher might be better for some metrics
                component_score = percentile
            score_components.append(component_score)

        # Fair value based scoring
        if result.blended_fair_value and result.blended_fair_value > 0:
            # Assuming current price is available (would need market data)
            # For now, add neutral score
            score_components.append(50.0)

        # PEG-based scoring
        if 'target_peg' in result.peg_analysis and 'peer_peg_median' in result.peg_analysis:
            target_peg = result.peg_analysis['target_peg']
            peer_peg = result.peg_analysis['peer_peg_median']
            if peer_peg > 0:
                peg_score = max(0, min(100, 100 * (peer_peg / target_peg)))
                score_components.append(peg_score)

        return statistics.mean(score_components) if score_components else 50.0

    def _generate_recommendation(self, result: RelativeValuationResult) -> Tuple[str, float]:
        """Generate investment recommendation based on relative valuation"""
        score = result.relative_valuation_score
        confidence = 0.5  # Base confidence

        # Adjust confidence based on data quality
        outlier_count = sum(result.outlier_flags.values())
        if outlier_count == 0:
            confidence += 0.2

        # Sample size consideration
        if len(result.peer_tickers) >= 5:
            confidence += 0.2

        # Score-based recommendation
        if score >= 70:
            recommendation = "BUY"
            confidence += 0.1
        elif score <= 30:
            recommendation = "SELL"
            confidence += 0.1
        else:
            recommendation = "HOLD"

        return recommendation, min(1.0, confidence)