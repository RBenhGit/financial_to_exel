"""
Peer Comparison Engine
======================

Provides comprehensive peer comparison capabilities for financial ratio analysis,
including relative ranking, peer group analysis, and competitive positioning.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import numpy as np
import pandas as pd
from datetime import datetime
from .industry_benchmarks import IndustryBenchmarkManager, IndustryBenchmark

logger = logging.getLogger(__name__)


@dataclass
class PeerMetrics:
    """Peer company metrics for comparison"""
    ticker: str
    company_name: str
    industry: str
    ratios: Dict[str, float] = field(default_factory=dict)
    market_cap: Optional[float] = None
    revenue: Optional[float] = None
    last_updated: Optional[datetime] = None


@dataclass
class ComparisonResult:
    """Results of peer comparison for a specific ratio"""
    ratio_name: str
    company_value: float
    peer_values: Dict[str, float]  # ticker -> value
    ranking: int  # 1 = best, higher = worse
    total_peers: int
    percentile_rank: float  # 0-100
    industry_position: str  # "leader", "above_average", "below_average", "laggard"
    best_performer: str  # Ticker of best performing peer
    worst_performer: str  # Ticker of worst performing peer


@dataclass
class PeerAnalysisReport:
    """Comprehensive peer analysis report"""
    company_ticker: str
    peer_group: List[str]
    analysis_date: datetime
    ratio_comparisons: Dict[str, ComparisonResult] = field(default_factory=dict)
    overall_ranking: Optional[int] = None
    strength_areas: List[str] = field(default_factory=list)
    weakness_areas: List[str] = field(default_factory=list)
    competitive_summary: str = ""


class PeerComparisonEngine:
    """Engine for conducting comprehensive peer analysis"""

    def __init__(self, benchmark_manager: Optional[IndustryBenchmarkManager] = None):
        """Initialize with benchmark manager"""
        self.benchmark_manager = benchmark_manager or IndustryBenchmarkManager()
        self._peer_data: Dict[str, PeerMetrics] = {}

    def add_peer_data(self, ticker: str, company_name: str, industry: str,
                     ratios: Dict[str, float], market_cap: Optional[float] = None,
                     revenue: Optional[float] = None) -> None:
        """Add peer company data for comparison"""
        peer_metrics = PeerMetrics(
            ticker=ticker.upper(),
            company_name=company_name,
            industry=industry,
            ratios=ratios,
            market_cap=market_cap,
            revenue=revenue,
            last_updated=datetime.now()
        )

        self._peer_data[ticker.upper()] = peer_metrics
        logger.info(f"Added peer data for {ticker}: {len(ratios)} ratios")

    def load_peer_data_from_dict(self, peer_data: Dict[str, Dict[str, Any]]) -> None:
        """Load multiple peer companies from dictionary format"""
        for ticker, data in peer_data.items():
            self.add_peer_data(
                ticker=ticker,
                company_name=data.get('company_name', ticker),
                industry=data.get('industry', 'Unknown'),
                ratios=data.get('ratios', {}),
                market_cap=data.get('market_cap'),
                revenue=data.get('revenue')
            )

    def compare_ratio(self, company_ticker: str, ratio_name: str, company_value: float,
                     peer_group: Optional[List[str]] = None,
                     higher_is_better: bool = True) -> ComparisonResult:
        """
        Compare a specific ratio against peer group

        Args:
            company_ticker: Ticker of the company being analyzed
            ratio_name: Name of the ratio
            company_value: Company's ratio value
            peer_group: Optional specific peer group (if None, uses all peers in same industry)
            higher_is_better: Whether higher values are better for this ratio

        Returns:
            ComparisonResult with detailed comparison
        """
        # Determine peer group
        if peer_group is None:
            company_industry = self._get_company_industry(company_ticker)
            peer_group = self._get_industry_peers(company_industry)

        # Get peer values
        peer_values = {}
        valid_peers = []

        for peer_ticker in peer_group:
            if peer_ticker.upper() in self._peer_data:
                peer_metrics = self._peer_data[peer_ticker.upper()]
                if ratio_name in peer_metrics.ratios:
                    peer_value = peer_metrics.ratios[ratio_name]
                    if isinstance(peer_value, (int, float)) and np.isfinite(peer_value):
                        peer_values[peer_ticker.upper()] = peer_value
                        valid_peers.append(peer_ticker.upper())

        if not peer_values:
            logger.warning(f"No peer data available for ratio {ratio_name}")
            return ComparisonResult(
                ratio_name=ratio_name,
                company_value=company_value,
                peer_values={},
                ranking=1,
                total_peers=1,
                percentile_rank=50.0,
                industry_position="unknown",
                best_performer=company_ticker,
                worst_performer=company_ticker
            )

        # Include company value in comparison
        all_values = list(peer_values.values()) + [company_value]
        all_tickers = valid_peers + [company_ticker.upper()]

        # Calculate ranking
        if higher_is_better:
            sorted_pairs = sorted(zip(all_values, all_tickers), key=lambda x: x[0], reverse=True)
        else:
            sorted_pairs = sorted(zip(all_values, all_tickers), key=lambda x: x[0])

        # Find company ranking
        ranking = next(i + 1 for i, (_, ticker) in enumerate(sorted_pairs)
                      if ticker == company_ticker.upper())

        total_companies = len(all_values)
        percentile_rank = (total_companies - ranking) / (total_companies - 1) * 100 if total_companies > 1 else 50.0

        # Determine industry position
        if percentile_rank >= 75:
            industry_position = "leader"
        elif percentile_rank >= 50:
            industry_position = "above_average"
        elif percentile_rank >= 25:
            industry_position = "below_average"
        else:
            industry_position = "laggard"

        # Identify best and worst performers
        best_performer = sorted_pairs[0][1]
        worst_performer = sorted_pairs[-1][1]

        return ComparisonResult(
            ratio_name=ratio_name,
            company_value=company_value,
            peer_values=peer_values,
            ranking=ranking,
            total_peers=total_companies,
            percentile_rank=percentile_rank,
            industry_position=industry_position,
            best_performer=best_performer,
            worst_performer=worst_performer
        )

    def generate_comprehensive_analysis(self, company_ticker: str, company_ratios: Dict[str, float],
                                      peer_group: Optional[List[str]] = None,
                                      ratio_preferences: Optional[Dict[str, bool]] = None) -> PeerAnalysisReport:
        """
        Generate comprehensive peer analysis report

        Args:
            company_ticker: Company being analyzed
            company_ratios: Company's ratio values
            peer_group: Optional specific peer group
            ratio_preferences: Dict of ratio_name -> higher_is_better

        Returns:
            Comprehensive peer analysis report
        """
        # Default ratio preferences
        default_preferences = {
            'roe': True, 'roa': True, 'gross_margin': True, 'operating_margin': True,
            'net_margin': True, 'current_ratio': True, 'quick_ratio': True,
            'asset_turnover': True, 'inventory_turnover': True, 'interest_coverage': True,
            'debt_to_equity': False, 'debt_to_assets': False,  # Lower is better
            'revenue_growth': True, 'fcf_growth': True, 'earnings_growth': True
        }

        preferences = ratio_preferences or default_preferences

        report = PeerAnalysisReport(
            company_ticker=company_ticker.upper(),
            peer_group=peer_group or self._get_industry_peers(self._get_company_industry(company_ticker)),
            analysis_date=datetime.now()
        )

        # Analyze each ratio
        ratio_scores = []

        for ratio_name, ratio_value in company_ratios.items():
            if isinstance(ratio_value, (int, float)) and np.isfinite(ratio_value):
                higher_is_better = preferences.get(ratio_name, True)

                comparison = self.compare_ratio(
                    company_ticker=company_ticker,
                    ratio_name=ratio_name,
                    company_value=ratio_value,
                    peer_group=report.peer_group,
                    higher_is_better=higher_is_better
                )

                report.ratio_comparisons[ratio_name] = comparison
                ratio_scores.append(comparison.percentile_rank)

                # Identify strengths and weaknesses
                if comparison.percentile_rank >= 75:
                    report.strength_areas.append(ratio_name)
                elif comparison.percentile_rank <= 25:
                    report.weakness_areas.append(ratio_name)

        # Calculate overall ranking
        if ratio_scores:
            average_percentile = np.mean(ratio_scores)
            # Convert percentile to ranking (approximate)
            total_peers = len(report.peer_group) + 1
            report.overall_ranking = max(1, int((100 - average_percentile) / 100 * total_peers))

        # Generate competitive summary
        report.competitive_summary = self._generate_competitive_summary(report)

        logger.info(f"Generated peer analysis for {company_ticker}: "
                   f"{len(report.ratio_comparisons)} ratios analyzed")

        return report

    def get_industry_leaders(self, industry: str, ratio_name: str,
                           higher_is_better: bool = True, top_n: int = 3) -> List[Tuple[str, float]]:
        """
        Get top performing companies in industry for specific ratio

        Args:
            industry: Industry name
            ratio_name: Ratio to analyze
            higher_is_better: Performance direction
            top_n: Number of top performers to return

        Returns:
            List of (ticker, ratio_value) tuples
        """
        industry_peers = self._get_industry_peers(industry)
        peer_values = []

        for peer_ticker in industry_peers:
            if peer_ticker in self._peer_data:
                peer_metrics = self._peer_data[peer_ticker]
                if ratio_name in peer_metrics.ratios:
                    value = peer_metrics.ratios[ratio_name]
                    if isinstance(value, (int, float)) and np.isfinite(value):
                        peer_values.append((peer_ticker, value))

        if not peer_values:
            return []

        # Sort based on performance direction
        peer_values.sort(key=lambda x: x[1], reverse=higher_is_better)

        return peer_values[:top_n]

    def calculate_competitive_moat_score(self, company_ticker: str,
                                       company_ratios: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate competitive moat score based on sustained competitive advantages

        Args:
            company_ticker: Company ticker
            company_ratios: Company's ratios

        Returns:
            Dictionary with moat analysis results
        """
        # Key moat indicators with weights
        moat_ratios = {
            'roe': {'weight': 0.25, 'threshold': 15.0, 'higher_better': True},
            'gross_margin': {'weight': 0.20, 'threshold': 40.0, 'higher_better': True},
            'operating_margin': {'weight': 0.15, 'threshold': 20.0, 'higher_better': True},
            'asset_turnover': {'weight': 0.15, 'threshold': 1.0, 'higher_better': True},
            'current_ratio': {'weight': 0.10, 'threshold': 1.5, 'higher_better': True},
            'debt_to_equity': {'weight': 0.10, 'threshold': 0.5, 'higher_better': False},
            'interest_coverage': {'weight': 0.05, 'threshold': 5.0, 'higher_better': True}
        }

        moat_score = 0.0
        max_score = 0.0
        contributing_factors = []
        weakness_factors = []

        for ratio_name, config in moat_ratios.items():
            max_score += config['weight']

            if ratio_name in company_ratios:
                value = company_ratios[ratio_name]
                threshold = config['threshold']
                weight = config['weight']

                if config['higher_better']:
                    if value >= threshold * 1.5:  # Exceptional
                        moat_score += weight
                        contributing_factors.append(f"Exceptional {ratio_name}")
                    elif value >= threshold:  # Good
                        moat_score += weight * 0.7
                        contributing_factors.append(f"Strong {ratio_name}")
                    elif value >= threshold * 0.8:  # Adequate
                        moat_score += weight * 0.4
                    else:  # Below threshold
                        weakness_factors.append(f"Weak {ratio_name}")
                else:  # Lower is better
                    if value <= threshold * 0.5:  # Exceptional
                        moat_score += weight
                        contributing_factors.append(f"Low {ratio_name}")
                    elif value <= threshold:  # Good
                        moat_score += weight * 0.7
                        contributing_factors.append(f"Reasonable {ratio_name}")
                    elif value <= threshold * 1.2:  # Adequate
                        moat_score += weight * 0.4
                    else:  # Above threshold
                        weakness_factors.append(f"High {ratio_name}")

        # Normalize to 0-100 scale
        normalized_score = (moat_score / max_score * 100) if max_score > 0 else 0

        # Determine moat strength
        if normalized_score >= 80:
            moat_strength = "Very Strong"
        elif normalized_score >= 60:
            moat_strength = "Strong"
        elif normalized_score >= 40:
            moat_strength = "Moderate"
        elif normalized_score >= 20:
            moat_strength = "Weak"
        else:
            moat_strength = "Very Weak"

        return {
            'moat_score': normalized_score,
            'moat_strength': moat_strength,
            'contributing_factors': contributing_factors,
            'weakness_factors': weakness_factors,
            'analysis_date': datetime.now().isoformat()
        }

    def _get_company_industry(self, ticker: str) -> str:
        """Get industry for a company ticker"""
        ticker_upper = ticker.upper()
        if ticker_upper in self._peer_data:
            return self._peer_data[ticker_upper].industry

        # Default industry classification based on ticker (simplified)
        tech_tickers = {'MSFT', 'AAPL', 'GOOGL', 'NVDA', 'META', 'AMZN', 'TSLA'}
        if ticker_upper in tech_tickers:
            return 'Technology'

        return 'Unknown'

    def _get_industry_peers(self, industry: str) -> List[str]:
        """Get all peer tickers in an industry"""
        peers = []
        for ticker, metrics in self._peer_data.items():
            if metrics.industry == industry:
                peers.append(ticker)

        # Also get peers from benchmark manager
        benchmark_peers = self.benchmark_manager.get_peer_companies(industry)
        peers.extend([p.upper() for p in benchmark_peers if p.upper() not in peers])

        return peers

    def _generate_competitive_summary(self, report: PeerAnalysisReport) -> str:
        """Generate competitive positioning summary"""
        total_ratios = len(report.ratio_comparisons)
        strengths = len(report.strength_areas)
        weaknesses = len(report.weakness_areas)

        if total_ratios == 0:
            return "Insufficient data for competitive analysis."

        strength_pct = (strengths / total_ratios) * 100
        weakness_pct = (weaknesses / total_ratios) * 100

        if strength_pct >= 50:
            competitive_position = "strong competitive position"
        elif strength_pct >= 30:
            competitive_position = "solid competitive position"
        elif weakness_pct >= 50:
            competitive_position = "challenging competitive position"
        else:
            competitive_position = "mixed competitive position"

        summary = f"{report.company_ticker} maintains a {competitive_position} "
        summary += f"with {strengths} key strengths and {weaknesses} areas for improvement "
        summary += f"out of {total_ratios} metrics analyzed."

        if report.overall_ranking:
            total_peers = len(report.peer_group) + 1
            summary += f" Overall ranking: #{report.overall_ranking} out of {total_peers} companies."

        return summary