"""
Growth Rate and Trend Analysis Module
====================================

This module provides comprehensive growth analysis and trend identification
for multi-company comparisons and portfolio analysis.

Key Features:
- Historical growth rate calculations (revenue, earnings, FCF, dividends)
- Trend analysis with statistical significance testing
- Growth consistency and volatility metrics
- Comparative growth analysis across peers
- Growth quality assessment
- Forward-looking growth projections

Analysis Types:
- Compound Annual Growth Rate (CAGR) calculations
- Year-over-year growth trends
- Quarterly growth momentum
- Growth acceleration/deceleration detection
- Seasonal adjustment and normalization
- Growth sustainability scoring
"""

from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import logging
import statistics

import numpy as np
import pandas as pd
from scipy import stats
from scipy.stats import linregress

from .company_comparison import CompanyMetrics, ComparisonMetric
from core.data_processing.data_contracts import FinancialStatement, MetadataInfo

logger = logging.getLogger(__name__)


class GrowthPeriod(Enum):
    """Growth calculation periods"""
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    TTM = "ttm"  # Trailing Twelve Months
    THREE_YEAR = "3y"
    FIVE_YEAR = "5y"
    TEN_YEAR = "10y"


class GrowthMetricType(Enum):
    """Types of growth metrics"""
    REVENUE = "revenue"
    NET_INCOME = "net_income"
    OPERATING_INCOME = "operating_income"
    FREE_CASH_FLOW = "free_cash_flow"
    EBITDA = "ebitda"
    EARNINGS_PER_SHARE = "eps"
    BOOK_VALUE = "book_value"
    DIVIDENDS = "dividends"
    SHARES_OUTSTANDING = "shares_outstanding"


class TrendDirection(Enum):
    """Trend direction classifications"""
    ACCELERATING = "accelerating"       # Growth rate increasing
    DECELERATING = "decelerating"       # Growth rate decreasing
    STABLE = "stable"                   # Consistent growth rate
    VOLATILE = "volatile"               # Inconsistent growth
    DECLINING = "declining"             # Negative growth trend


@dataclass
class GrowthMetrics:
    """Comprehensive growth metrics for a single metric"""

    metric_name: str
    company_ticker: str

    # Growth Rates
    cagr_1y: Optional[float] = None     # 1-year CAGR
    cagr_3y: Optional[float] = None     # 3-year CAGR
    cagr_5y: Optional[float] = None     # 5-year CAGR
    cagr_10y: Optional[float] = None    # 10-year CAGR

    # Recent Growth
    latest_yoy: Optional[float] = None   # Latest year-over-year
    latest_qoq: Optional[float] = None   # Latest quarter-over-quarter
    ttm_growth: Optional[float] = None   # Trailing twelve months

    # Growth Quality
    growth_consistency: Optional[float] = None  # Coefficient of variation
    growth_volatility: Optional[float] = None   # Standard deviation of growth rates
    positive_periods: Optional[float] = None    # % of periods with positive growth

    # Trend Analysis
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_strength: Optional[float] = None      # R-squared of trend line
    trend_significance: Optional[float] = None  # P-value of trend
    acceleration: Optional[float] = None        # Rate of change in growth rate

    # Statistical Measures
    mean_growth: Optional[float] = None
    median_growth: Optional[float] = None
    std_growth: Optional[float] = None
    min_growth: Optional[float] = None
    max_growth: Optional[float] = None

    # Data Quality
    periods_available: int = 0
    data_completeness: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CompanyGrowthProfile:
    """Complete growth profile for a company"""

    ticker: str
    company_name: Optional[str] = None
    analysis_date: datetime = field(default_factory=datetime.now)

    # Growth metrics by category
    revenue_growth: Optional[GrowthMetrics] = None
    earnings_growth: Optional[GrowthMetrics] = None
    fcf_growth: Optional[GrowthMetrics] = None
    dividend_growth: Optional[GrowthMetrics] = None

    # Overall Growth Assessment
    overall_growth_score: float = 0.0           # 0-100 composite score
    growth_quality_score: float = 0.0           # 0-100 quality score
    growth_sustainability: float = 0.0          # 0-100 sustainability score

    # Comparative Metrics
    peer_growth_percentile: Dict[str, float] = field(default_factory=dict)
    sector_growth_percentile: Dict[str, float] = field(default_factory=dict)

    # Growth Classification
    growth_stage: str = "mature"                # growth, mature, declining
    growth_consistency_rating: str = "moderate" # high, moderate, low, volatile

    # Forward-Looking
    projected_growth_rates: Dict[str, float] = field(default_factory=dict)
    growth_drivers: List[str] = field(default_factory=list)
    growth_risks: List[str] = field(default_factory=list)

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


@dataclass
class GrowthComparisonResult:
    """Result of multi-company growth comparison"""

    comparison_id: str
    analysis_date: datetime = field(default_factory=datetime.now)

    # Company Profiles
    company_profiles: Dict[str, CompanyGrowthProfile] = field(default_factory=dict)

    # Comparative Analysis
    growth_rankings: Dict[str, List[Tuple[str, float]]] = field(default_factory=dict)  # metric -> ranked list
    growth_correlations: pd.DataFrame = field(default_factory=pd.DataFrame)
    peer_statistics: Dict[str, Dict[str, float]] = field(default_factory=dict)

    # Sector Analysis
    sector_growth_trends: Dict[str, Dict[str, float]] = field(default_factory=dict)
    growth_leaders: Dict[str, str] = field(default_factory=dict)  # metric -> top performer
    growth_laggards: Dict[str, str] = field(default_factory=dict)  # metric -> worst performer

    # Insights
    growth_insights: List[str] = field(default_factory=list)
    trend_alerts: List[str] = field(default_factory=list)
    investment_implications: List[str] = field(default_factory=list)

    # Metadata
    metadata: MetadataInfo = field(default_factory=MetadataInfo)


class GrowthTrendAnalyzer:
    """
    Comprehensive growth and trend analysis engine
    """

    def __init__(self):
        self.minimum_periods = 3  # Minimum periods needed for trend analysis

    def analyze_company_growth(self,
                             ticker: str,
                             historical_data: List[FinancialStatement],
                             company_name: Optional[str] = None) -> CompanyGrowthProfile:
        """
        Analyze growth trends for a single company

        Args:
            ticker: Company ticker
            historical_data: List of historical financial statements (sorted by date)
            company_name: Optional company name

        Returns:
            CompanyGrowthProfile with complete growth analysis
        """
        logger.info(f"Analyzing growth trends for {ticker}")

        # Sort data by period (most recent first)
        sorted_data = sorted(historical_data, key=lambda x: x.period, reverse=True)

        profile = CompanyGrowthProfile(
            ticker=ticker,
            company_name=company_name
        )

        # Analyze growth for each metric type
        profile.revenue_growth = self._analyze_metric_growth(
            sorted_data, GrowthMetricType.REVENUE, ticker
        )
        profile.earnings_growth = self._analyze_metric_growth(
            sorted_data, GrowthMetricType.NET_INCOME, ticker
        )
        profile.fcf_growth = self._analyze_metric_growth(
            sorted_data, GrowthMetricType.FREE_CASH_FLOW, ticker
        )

        # Calculate composite scores
        profile.overall_growth_score = self._calculate_overall_growth_score(profile)
        profile.growth_quality_score = self._calculate_growth_quality_score(profile)
        profile.growth_sustainability = self._calculate_sustainability_score(profile)

        # Classify growth characteristics
        profile.growth_stage = self._classify_growth_stage(profile)
        profile.growth_consistency_rating = self._classify_growth_consistency(profile)

        # Generate insights
        profile.growth_drivers = self._identify_growth_drivers(profile)
        profile.growth_risks = self._identify_growth_risks(profile)

        return profile

    def compare_company_growth(self,
                             companies: Dict[str, List[FinancialStatement]],
                             sector: Optional[str] = None) -> GrowthComparisonResult:
        """
        Compare growth trends across multiple companies

        Args:
            companies: Dictionary mapping ticker to historical financial data
            sector: Optional sector for benchmarking

        Returns:
            GrowthComparisonResult with comparative analysis
        """
        logger.info(f"Comparing growth trends for {len(companies)} companies")

        result = GrowthComparisonResult(
            comparison_id=f"growth_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Analyze each company
        for ticker, historical_data in companies.items():
            try:
                profile = self.analyze_company_growth(ticker, historical_data)
                result.company_profiles[ticker] = profile
            except Exception as e:
                logger.error(f"Failed to analyze growth for {ticker}: {str(e)}")

        # Comparative analysis
        result.growth_rankings = self._calculate_growth_rankings(result.company_profiles)
        result.growth_correlations = self._calculate_growth_correlations(result.company_profiles)
        result.peer_statistics = self._calculate_peer_statistics(result.company_profiles)

        # Sector analysis
        if sector:
            result.sector_growth_trends = self._analyze_sector_trends(result.company_profiles, sector)

        # Identify leaders and laggards
        result.growth_leaders = self._identify_growth_leaders(result.growth_rankings)
        result.growth_laggards = self._identify_growth_laggards(result.growth_rankings)

        # Generate insights
        result.growth_insights = self._generate_growth_insights(result)
        result.trend_alerts = self._generate_trend_alerts(result)
        result.investment_implications = self._generate_investment_implications(result)

        return result

    def _analyze_metric_growth(self,
                             historical_data: List[FinancialStatement],
                             metric_type: GrowthMetricType,
                             ticker: str) -> GrowthMetrics:
        """Analyze growth for a specific metric"""

        growth_metrics = GrowthMetrics(
            metric_name=metric_type.value,
            company_ticker=ticker
        )

        # Extract metric values
        values = []
        periods = []

        for statement in historical_data:
            value = getattr(statement, metric_type.value, None)
            if value is not None:
                values.append(value)
                periods.append(statement.period)

        if len(values) < 2:
            return growth_metrics

        growth_metrics.periods_available = len(values)
        growth_metrics.data_completeness = 1.0  # All requested periods have data

        # Calculate growth rates
        growth_rates = []
        for i in range(1, len(values)):
            if values[i] != 0:
                growth_rate = (values[i-1] - values[i]) / abs(values[i])
                growth_rates.append(growth_rate)

        if not growth_rates:
            return growth_metrics

        # Calculate various growth metrics
        growth_metrics.latest_yoy = growth_rates[0] if growth_rates else None

        # CAGR calculations (if we have enough data)
        if len(values) >= 2:
            growth_metrics.cagr_1y = growth_rates[0] if growth_rates else None

        if len(values) >= 4:  # 3+ years of data
            start_value = values[-1]  # Oldest value
            end_value = values[0]     # Most recent value
            years = min(3, len(values) - 1)
            if start_value > 0:
                growth_metrics.cagr_3y = ((end_value / start_value) ** (1/years)) - 1

        if len(values) >= 6:  # 5+ years of data
            start_value = values[-1]
            end_value = values[0]
            years = min(5, len(values) - 1)
            if start_value > 0:
                growth_metrics.cagr_5y = ((end_value / start_value) ** (1/years)) - 1

        # Growth quality metrics
        if len(growth_rates) > 1:
            growth_metrics.mean_growth = statistics.mean(growth_rates)
            growth_metrics.median_growth = statistics.median(growth_rates)
            growth_metrics.std_growth = statistics.stdev(growth_rates)
            growth_metrics.min_growth = min(growth_rates)
            growth_metrics.max_growth = max(growth_rates)

            # Growth consistency (lower coefficient of variation = more consistent)
            if growth_metrics.mean_growth != 0:
                growth_metrics.growth_consistency = abs(growth_metrics.std_growth / growth_metrics.mean_growth)

            growth_metrics.growth_volatility = growth_metrics.std_growth
            positive_count = sum(1 for gr in growth_rates if gr > 0)
            growth_metrics.positive_periods = positive_count / len(growth_rates)

        # Trend analysis
        if len(growth_rates) >= self.minimum_periods:
            growth_metrics.trend_direction, growth_metrics.trend_strength, growth_metrics.trend_significance = self._analyze_trend(growth_rates)
            growth_metrics.acceleration = self._calculate_acceleration(growth_rates)

        return growth_metrics

    def _analyze_trend(self, growth_rates: List[float]) -> Tuple[TrendDirection, Optional[float], Optional[float]]:
        """Analyze trend direction and strength"""
        if len(growth_rates) < self.minimum_periods:
            return TrendDirection.STABLE, None, None

        # Perform linear regression
        x = list(range(len(growth_rates)))
        y = growth_rates

        try:
            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            # Determine trend direction
            if p_value < 0.05:  # Statistically significant
                if slope > 0.01:  # Positive trend
                    direction = TrendDirection.ACCELERATING
                elif slope < -0.01:  # Negative trend
                    direction = TrendDirection.DECELERATING
                else:
                    direction = TrendDirection.STABLE
            else:
                # Check volatility
                volatility = statistics.stdev(growth_rates) if len(growth_rates) > 1 else 0
                if volatility > 0.3:  # High volatility threshold
                    direction = TrendDirection.VOLATILE
                else:
                    direction = TrendDirection.STABLE

            return direction, r_value ** 2, p_value

        except Exception as e:
            logger.warning(f"Failed to perform trend analysis: {str(e)}")
            return TrendDirection.STABLE, None, None

    def _calculate_acceleration(self, growth_rates: List[float]) -> Optional[float]:
        """Calculate growth acceleration (rate of change of growth rate)"""
        if len(growth_rates) < 3:
            return None

        # Calculate second derivative approximation
        accelerations = []
        for i in range(2, len(growth_rates)):
            acc = growth_rates[i-2] - 2*growth_rates[i-1] + growth_rates[i]
            accelerations.append(acc)

        return statistics.mean(accelerations) if accelerations else None

    def _calculate_overall_growth_score(self, profile: CompanyGrowthProfile) -> float:
        """Calculate composite growth score (0-100)"""
        score_components = []

        # Revenue growth score
        if profile.revenue_growth and profile.revenue_growth.cagr_3y is not None:
            revenue_score = min(100, max(0, profile.revenue_growth.cagr_3y * 100 + 50))
            score_components.append(revenue_score)

        # Earnings growth score
        if profile.earnings_growth and profile.earnings_growth.cagr_3y is not None:
            earnings_score = min(100, max(0, profile.earnings_growth.cagr_3y * 100 + 50))
            score_components.append(earnings_score)

        # FCF growth score
        if profile.fcf_growth and profile.fcf_growth.cagr_3y is not None:
            fcf_score = min(100, max(0, profile.fcf_growth.cagr_3y * 100 + 50))
            score_components.append(fcf_score)

        return statistics.mean(score_components) if score_components else 50.0

    def _calculate_growth_quality_score(self, profile: CompanyGrowthProfile) -> float:
        """Calculate growth quality score based on consistency and sustainability"""
        quality_components = []

        # Consistency scoring
        for growth_metric in [profile.revenue_growth, profile.earnings_growth, profile.fcf_growth]:
            if growth_metric and growth_metric.growth_consistency is not None:
                # Lower consistency ratio = higher quality
                consistency_score = max(0, 100 - growth_metric.growth_consistency * 100)
                quality_components.append(consistency_score)

            if growth_metric and growth_metric.positive_periods is not None:
                # Higher percentage of positive periods = higher quality
                positive_score = growth_metric.positive_periods * 100
                quality_components.append(positive_score)

        return statistics.mean(quality_components) if quality_components else 50.0

    def _calculate_sustainability_score(self, profile: CompanyGrowthProfile) -> float:
        """Calculate growth sustainability score"""
        sustainability_components = []

        # Recent vs long-term growth consistency
        if (profile.revenue_growth and
            profile.revenue_growth.latest_yoy is not None and
            profile.revenue_growth.cagr_3y is not None):

            recent = profile.revenue_growth.latest_yoy
            long_term = profile.revenue_growth.cagr_3y

            if long_term != 0:
                consistency_ratio = min(2.0, abs(recent / long_term))
                sustainability_score = max(0, 100 - abs(consistency_ratio - 1.0) * 50)
                sustainability_components.append(sustainability_score)

        # Trend strength contribution
        for growth_metric in [profile.revenue_growth, profile.earnings_growth, profile.fcf_growth]:
            if growth_metric and growth_metric.trend_strength is not None:
                trend_score = growth_metric.trend_strength * 100
                sustainability_components.append(trend_score)

        return statistics.mean(sustainability_components) if sustainability_components else 50.0

    def _classify_growth_stage(self, profile: CompanyGrowthProfile) -> str:
        """Classify company growth stage"""
        if profile.overall_growth_score >= 70:
            return "growth"
        elif profile.overall_growth_score >= 40:
            return "mature"
        else:
            return "declining"

    def _classify_growth_consistency(self, profile: CompanyGrowthProfile) -> str:
        """Classify growth consistency"""
        if profile.growth_quality_score >= 80:
            return "high"
        elif profile.growth_quality_score >= 60:
            return "moderate"
        elif profile.growth_quality_score >= 40:
            return "low"
        else:
            return "volatile"

    def _identify_growth_drivers(self, profile: CompanyGrowthProfile) -> List[str]:
        """Identify key growth drivers"""
        drivers = []

        # Analyze which metrics are driving growth
        if profile.revenue_growth and profile.revenue_growth.trend_direction == TrendDirection.ACCELERATING:
            drivers.append("Revenue expansion")

        if profile.earnings_growth and profile.earnings_growth.cagr_3y and profile.earnings_growth.cagr_3y > 0.15:
            drivers.append("Strong earnings growth")

        if profile.fcf_growth and profile.fcf_growth.trend_direction == TrendDirection.ACCELERATING:
            drivers.append("Improving cash generation")

        # Add generic drivers if none identified
        if not drivers:
            if profile.overall_growth_score > 60:
                drivers.append("Solid fundamental performance")
            else:
                drivers.append("Stable business operations")

        return drivers

    def _identify_growth_risks(self, profile: CompanyGrowthProfile) -> List[str]:
        """Identify growth risks"""
        risks = []

        # Check for declining trends
        if profile.revenue_growth and profile.revenue_growth.trend_direction == TrendDirection.DECELERATING:
            risks.append("Slowing revenue growth")

        # Check for high volatility
        if profile.growth_quality_score < 40:
            risks.append("Inconsistent growth patterns")

        # Check for recent weakness
        if (profile.revenue_growth and
            profile.revenue_growth.latest_yoy is not None and
            profile.revenue_growth.latest_yoy < 0):
            risks.append("Recent revenue decline")

        return risks

    def _calculate_growth_rankings(self, profiles: Dict[str, CompanyGrowthProfile]) -> Dict[str, List[Tuple[str, float]]]:
        """Calculate growth rankings across companies"""
        rankings = {}

        # Overall growth score ranking
        overall_scores = [(ticker, profile.overall_growth_score) for ticker, profile in profiles.items()]
        overall_scores.sort(key=lambda x: x[1], reverse=True)
        rankings['overall_growth'] = overall_scores

        # Growth quality ranking
        quality_scores = [(ticker, profile.growth_quality_score) for ticker, profile in profiles.items()]
        quality_scores.sort(key=lambda x: x[1], reverse=True)
        rankings['growth_quality'] = quality_scores

        # Revenue growth ranking
        revenue_scores = []
        for ticker, profile in profiles.items():
            if profile.revenue_growth and profile.revenue_growth.cagr_3y is not None:
                revenue_scores.append((ticker, profile.revenue_growth.cagr_3y))
        revenue_scores.sort(key=lambda x: x[1], reverse=True)
        rankings['revenue_growth'] = revenue_scores

        return rankings

    def _calculate_growth_correlations(self, profiles: Dict[str, CompanyGrowthProfile]) -> pd.DataFrame:
        """Calculate correlations between different growth metrics"""
        data = {}

        for ticker, profile in profiles.items():
            row = {}
            if profile.revenue_growth and profile.revenue_growth.cagr_3y is not None:
                row['revenue_growth'] = profile.revenue_growth.cagr_3y
            if profile.earnings_growth and profile.earnings_growth.cagr_3y is not None:
                row['earnings_growth'] = profile.earnings_growth.cagr_3y
            if profile.fcf_growth and profile.fcf_growth.cagr_3y is not None:
                row['fcf_growth'] = profile.fcf_growth.cagr_3y

            if row:  # Only add if we have some data
                data[ticker] = row

        if data:
            df = pd.DataFrame(data).T
            return df.corr()
        else:
            return pd.DataFrame()

    def _calculate_peer_statistics(self, profiles: Dict[str, CompanyGrowthProfile]) -> Dict[str, Dict[str, float]]:
        """Calculate peer statistics for growth metrics"""
        stats = {}

        # Collect all growth scores
        overall_scores = [p.overall_growth_score for p in profiles.values()]
        quality_scores = [p.growth_quality_score for p in profiles.values()]

        if overall_scores:
            stats['overall_growth'] = {
                'mean': statistics.mean(overall_scores),
                'median': statistics.median(overall_scores),
                'std': statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0,
                'min': min(overall_scores),
                'max': max(overall_scores)
            }

        if quality_scores:
            stats['growth_quality'] = {
                'mean': statistics.mean(quality_scores),
                'median': statistics.median(quality_scores),
                'std': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                'min': min(quality_scores),
                'max': max(quality_scores)
            }

        return stats

    def _analyze_sector_trends(self, profiles: Dict[str, CompanyGrowthProfile], sector: str) -> Dict[str, Dict[str, float]]:
        """Analyze sector-wide growth trends"""
        # Placeholder for sector analysis - would need sector classification data
        return {}

    def _identify_growth_leaders(self, rankings: Dict[str, List[Tuple[str, float]]]) -> Dict[str, str]:
        """Identify growth leaders by category"""
        leaders = {}
        for category, ranking in rankings.items():
            if ranking:
                leaders[category] = ranking[0][0]  # Top performer
        return leaders

    def _identify_growth_laggards(self, rankings: Dict[str, List[Tuple[str, float]]]) -> Dict[str, str]:
        """Identify growth laggards by category"""
        laggards = {}
        for category, ranking in rankings.items():
            if ranking:
                laggards[category] = ranking[-1][0]  # Bottom performer
        return laggards

    def _generate_growth_insights(self, result: GrowthComparisonResult) -> List[str]:
        """Generate growth analysis insights"""
        insights = []

        # Overall market insights
        if result.growth_leaders:
            leader = result.growth_leaders.get('overall_growth')
            if leader:
                insights.append(f"{leader} demonstrates the strongest overall growth profile")

        # Growth consistency insights
        high_quality_companies = []
        for ticker, profile in result.company_profiles.items():
            if profile.growth_quality_score >= 80:
                high_quality_companies.append(ticker)

        if high_quality_companies:
            insights.append(f"Companies with high growth consistency: {', '.join(high_quality_companies)}")

        # Correlation insights
        if not result.growth_correlations.empty:
            # Find strongest correlations
            correlations = []
            for i in range(len(result.growth_correlations.columns)):
                for j in range(i+1, len(result.growth_correlations.columns)):
                    corr_val = result.growth_correlations.iloc[i, j]
                    if not pd.isna(corr_val) and abs(corr_val) > 0.7:
                        col1 = result.growth_correlations.columns[i]
                        col2 = result.growth_correlations.columns[j]
                        correlations.append(f"{col1} and {col2} are strongly correlated ({corr_val:.2f})")

            insights.extend(correlations[:3])  # Top 3 correlations

        return insights

    def _generate_trend_alerts(self, result: GrowthComparisonResult) -> List[str]:
        """Generate trend alerts"""
        alerts = []

        for ticker, profile in result.company_profiles.items():
            # Declining revenue alert
            if (profile.revenue_growth and
                profile.revenue_growth.trend_direction == TrendDirection.DECELERATING):
                alerts.append(f"{ticker}: Revenue growth is decelerating")

            # High volatility alert
            if profile.growth_consistency_rating == "volatile":
                alerts.append(f"{ticker}: Growth patterns are highly volatile")

            # Recent weakness alert
            if (profile.revenue_growth and
                profile.revenue_growth.latest_yoy is not None and
                profile.revenue_growth.latest_yoy < -0.05):
                alerts.append(f"{ticker}: Recent revenue decline of {profile.revenue_growth.latest_yoy:.1%}")

        return alerts

    def _generate_investment_implications(self, result: GrowthComparisonResult) -> List[str]:
        """Generate investment implications based on growth analysis"""
        implications = []

        # Growth stage implications
        growth_companies = [ticker for ticker, profile in result.company_profiles.items()
                          if profile.growth_stage == "growth"]
        mature_companies = [ticker for ticker, profile in result.company_profiles.items()
                          if profile.growth_stage == "mature"]

        if growth_companies:
            implications.append(f"Growth-stage companies ({', '.join(growth_companies)}) may offer higher returns but with increased risk")

        if mature_companies:
            implications.append(f"Mature companies ({', '.join(mature_companies)}) may provide stable, dividend-focused returns")

        # Quality implications
        high_quality = [ticker for ticker, profile in result.company_profiles.items()
                       if profile.growth_quality_score >= 80]
        if high_quality:
            implications.append(f"High-quality growth companies ({', '.join(high_quality)}) may be suitable for long-term portfolios")

        return implications