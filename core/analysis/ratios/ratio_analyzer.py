"""
Advanced Ratio Analyzer
=======================

Main integration class that combines industry benchmarking, statistical analysis,
and peer comparison for comprehensive financial ratio analysis.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
import numpy as np
from datetime import datetime
from pathlib import Path

from .industry_benchmarks import IndustryBenchmarkManager, IndustryBenchmark, IndustryProfile
from .statistical_analysis import (
    RatioStatisticalAnalysis, TrendAnalysis, VolatilityMetrics,
    SeasonalityAnalysis, CorrelationMatrix
)
from .peer_comparison import PeerComparisonEngine, PeerAnalysisReport, ComparisonResult
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine

logger = logging.getLogger(__name__)


@dataclass
class EnhancedRatioMetric:
    """Enhanced ratio metric with comprehensive analysis"""
    name: str
    current_value: float
    historical_values: List[float] = field(default_factory=list)
    industry_benchmark: Optional[IndustryBenchmark] = None
    trend_analysis: Optional[TrendAnalysis] = None
    volatility_metrics: Optional[VolatilityMetrics] = None
    peer_comparison: Optional[ComparisonResult] = None
    industry_position: str = "unknown"
    performance_score: float = 0.0  # 0-100 composite score
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveRatioReport:
    """Comprehensive ratio analysis report"""
    company_ticker: str
    company_name: str
    industry: str
    analysis_date: datetime
    enhanced_ratios: Dict[str, EnhancedRatioMetric] = field(default_factory=dict)
    peer_analysis: Optional[PeerAnalysisReport] = None
    statistical_summary: Dict[str, Any] = field(default_factory=dict)
    overall_financial_health: Dict[str, Any] = field(default_factory=dict)
    strategic_insights: List[str] = field(default_factory=list)
    risk_assessment: Dict[str, Any] = field(default_factory=dict)


class AdvancedRatioAnalyzer:
    """Main class for advanced financial ratio analysis"""

    def __init__(self, data_path: Optional[Path] = None):
        """Initialize with optional custom data path"""
        self.benchmark_manager = IndustryBenchmarkManager(data_path)
        self.statistical_analyzer = RatioStatisticalAnalysis()
        self.peer_engine = PeerComparisonEngine(self.benchmark_manager)
        self.calculation_engine = FinancialCalculationEngine()

        self._industry_weights = self._load_industry_weights()

    def analyze_company(self,
                       company_ticker: str,
                       company_name: str,
                       industry: str,
                       current_ratios: Dict[str, float],
                       historical_ratios: Optional[Dict[str, List[float]]] = None,
                       periods: Optional[List[datetime]] = None,
                       peer_data: Optional[Dict[str, Dict[str, Any]]] = None) -> ComprehensiveRatioReport:
        """
        Perform comprehensive ratio analysis for a company

        Args:
            company_ticker: Company ticker symbol
            company_name: Company name
            industry: Industry classification
            current_ratios: Current period ratios
            historical_ratios: Historical ratio data
            periods: Date periods for historical data
            peer_data: Peer company data for comparison

        Returns:
            Comprehensive analysis report
        """
        logger.info(f"Starting comprehensive analysis for {company_ticker}")

        # Load peer data if provided
        if peer_data:
            self.peer_engine.load_peer_data_from_dict(peer_data)

        # Initialize report
        report = ComprehensiveRatioReport(
            company_ticker=company_ticker.upper(),
            company_name=company_name,
            industry=industry,
            analysis_date=datetime.now()
        )

        # Analyze each ratio
        enhanced_ratios = {}

        for ratio_name, current_value in current_ratios.items():
            if isinstance(current_value, (int, float)) and np.isfinite(current_value):
                enhanced_ratio = self._analyze_single_ratio(
                    ratio_name=ratio_name,
                    current_value=current_value,
                    historical_values=historical_ratios.get(ratio_name, []) if historical_ratios else [],
                    industry=industry,
                    company_ticker=company_ticker,
                    periods=periods
                )

                enhanced_ratios[ratio_name] = enhanced_ratio

        report.enhanced_ratios = enhanced_ratios

        # Generate peer analysis
        if peer_data:
            try:
                report.peer_analysis = self.peer_engine.generate_comprehensive_analysis(
                    company_ticker=company_ticker,
                    company_ratios=current_ratios
                )
            except Exception as e:
                logger.error(f"Error in peer analysis: {e}")

        # Generate statistical summary
        if historical_ratios:
            try:
                report.statistical_summary = self.statistical_analyzer.generate_comprehensive_report(
                    ratios_data=historical_ratios,
                    periods=periods
                )
            except Exception as e:
                logger.error(f"Error in statistical analysis: {e}")

        # Calculate overall financial health
        report.overall_financial_health = self._calculate_overall_health(enhanced_ratios)

        # Generate strategic insights
        report.strategic_insights = self._generate_strategic_insights(report)

        # Assess risks
        report.risk_assessment = self._assess_risks(enhanced_ratios, report.peer_analysis)

        logger.info(f"Completed comprehensive analysis for {company_ticker}: "
                   f"{len(enhanced_ratios)} ratios analyzed")

        return report

    def analyze_company_from_statements(self,
                                       company_ticker: str,
                                       company_name: str,
                                       industry: str,
                                       financial_statements: Dict[str, Any],
                                       historical_statements: Optional[List[Dict[str, Any]]] = None,
                                       periods: Optional[List[datetime]] = None,
                                       peer_data: Optional[Dict[str, Dict[str, Any]]] = None,
                                       field_mappings: Optional[Dict[str, str]] = None) -> ComprehensiveRatioReport:
        """
        Perform comprehensive ratio analysis from financial statement data using FinancialCalculationEngine.

        This method integrates with the enhanced FinancialCalculationEngine to calculate
        comprehensive ratios from standardized financial statements.

        Args:
            company_ticker: Company ticker symbol
            company_name: Company name
            industry: Industry classification
            financial_statements: Current period financial statements with standardized fields
            historical_statements: List of historical financial statements (optional)
            periods: Date periods for historical data (optional)
            peer_data: Peer company data for comparison (optional)
            field_mappings: Custom field name mappings (optional)

        Returns:
            Comprehensive analysis report with ratios calculated from financial statements

        Example:
            >>> analyzer = AdvancedRatioAnalyzer()
            >>> statements = {
            ...     'revenue': 100000, 'net_income': 15000,
            ...     'total_assets': 500000, 'current_assets': 150000,
            ...     'current_liabilities': 80000
            ... }
            >>> report = analyzer.analyze_company_from_statements(
            ...     'AAPL', 'Apple Inc', 'Technology', statements
            ... )
        """
        logger.info(f"Starting comprehensive analysis from statements for {company_ticker}")

        # Calculate current period ratios using FinancialCalculationEngine
        ratio_result = self.calculation_engine.calculate_ratios_from_statements(
            financial_statements,
            field_mappings=field_mappings,
            metadata_tracking=True
        )

        if not ratio_result.is_valid:
            logger.error(f"Failed to calculate ratios: {ratio_result.error_message}")
            # Return empty report if calculation fails
            return ComprehensiveRatioReport(
                company_ticker=company_ticker.upper(),
                company_name=company_name,
                industry=industry,
                analysis_date=datetime.now()
            )

        # Flatten calculated ratios into a single dictionary
        current_ratios = {}
        for category, ratios in ratio_result.value.items():
            current_ratios.update(ratios)

        # Calculate historical ratios if historical statements provided
        historical_ratios = {}
        if historical_statements:
            for ratio_name in current_ratios.keys():
                historical_ratios[ratio_name] = []

            for hist_statement in historical_statements:
                hist_ratio_result = self.calculation_engine.calculate_ratios_from_statements(
                    hist_statement,
                    field_mappings=field_mappings,
                    metadata_tracking=False
                )

                if hist_ratio_result.is_valid:
                    for category, ratios in hist_ratio_result.value.items():
                        for ratio_name, value in ratios.items():
                            if ratio_name in historical_ratios:
                                historical_ratios[ratio_name].append(value)

        # Use the existing analyze_company method with calculated ratios
        return self.analyze_company(
            company_ticker=company_ticker,
            company_name=company_name,
            industry=industry,
            current_ratios=current_ratios,
            historical_ratios=historical_ratios if historical_ratios else None,
            periods=periods,
            peer_data=peer_data
        )

    def _analyze_single_ratio(self, ratio_name: str, current_value: float,
                             historical_values: List[float], industry: str,
                             company_ticker: str, periods: Optional[List[datetime]] = None) -> EnhancedRatioMetric:
        """Analyze a single ratio comprehensively"""

        enhanced_ratio = EnhancedRatioMetric(
            name=ratio_name,
            current_value=current_value,
            historical_values=historical_values
        )

        # Get industry benchmark
        enhanced_ratio.industry_benchmark = self.benchmark_manager.get_industry_benchmark(
            industry, ratio_name
        )

        # Trend analysis (if historical data available)
        if len(historical_values) >= 3:
            enhanced_ratio.trend_analysis = self.statistical_analyzer.analyze_trend(
                historical_values, periods, ratio_name
            )

            # Volatility analysis
            enhanced_ratio.volatility_metrics = self.statistical_analyzer.analyze_volatility(
                historical_values, ratio_name,
                enhanced_ratio.industry_benchmark.std_deviation if enhanced_ratio.industry_benchmark else None
            )

        # Industry position
        if enhanced_ratio.industry_benchmark:
            performance_level, percentile = self.benchmark_manager.classify_performance(
                industry, ratio_name, current_value
            )
            enhanced_ratio.industry_position = performance_level

            # Calculate performance score
            enhanced_ratio.performance_score = percentile

        # Peer comparison (if data available)
        try:
            enhanced_ratio.peer_comparison = self.peer_engine.compare_ratio(
                company_ticker=company_ticker,
                ratio_name=ratio_name,
                company_value=current_value,
                higher_is_better=self._is_higher_better(ratio_name)
            )
        except Exception as e:
            logger.debug(f"Peer comparison not available for {ratio_name}: {e}")

        # Generate recommendations
        enhanced_ratio.recommendations = self._generate_ratio_recommendations(enhanced_ratio)

        return enhanced_ratio

    def _calculate_overall_health(self, enhanced_ratios: Dict[str, EnhancedRatioMetric]) -> Dict[str, Any]:
        """Calculate overall financial health metrics"""

        if not enhanced_ratios:
            return {'score': 0, 'grade': 'Unknown', 'summary': 'No data available'}

        # Category weights (updated to include valuation)
        category_weights = {
            'profitability': 0.25,
            'liquidity': 0.20,
            'efficiency': 0.15,
            'leverage': 0.20,
            'valuation': 0.10,
            'growth': 0.10
        }

        # Ratio categorization (expanded with comprehensive ratio set)
        ratio_categories = {
            'profitability': [
                'roe', 'roa', 'return_on_equity', 'return_on_assets',
                'gross_margin', 'operating_margin', 'net_margin',
                'gross_profit_margin', 'operating_profit_margin', 'net_profit_margin'
            ],
            'liquidity': [
                'current_ratio', 'quick_ratio', 'cash_ratio'
            ],
            'efficiency': [
                'asset_turnover', 'inventory_turnover', 'receivables_turnover',
                'days_inventory_outstanding', 'days_sales_outstanding',
                'days_payables_outstanding', 'cash_conversion_cycle'
            ],
            'leverage': [
                'debt_to_equity', 'debt_to_assets', 'interest_coverage',
                'debt_service_coverage_ratio', 'equity_ratio'
            ],
            'valuation': [
                'pe_ratio', 'pb_ratio', 'price_to_book', 'price_to_earnings',
                'price_to_sales', 'price_to_cash_flow', 'enterprise_value_to_ebitda'
            ],
            'growth': [
                'revenue_growth', 'earnings_growth', 'fcf_growth',
                'dividend_growth', 'book_value_growth'
            ]
        }

        category_scores = {}
        overall_score = 0.0
        total_weight = 0.0

        for category, ratios in ratio_categories.items():
            category_ratio_scores = []

            for ratio_name in ratios:
                if ratio_name in enhanced_ratios:
                    ratio_score = enhanced_ratios[ratio_name].performance_score
                    category_ratio_scores.append(ratio_score)

            if category_ratio_scores:
                category_score = np.mean(category_ratio_scores)
                category_scores[category] = category_score

                weight = category_weights.get(category, 0.1)
                overall_score += category_score * weight
                total_weight += weight

        # Normalize overall score
        if total_weight > 0:
            overall_score = overall_score / total_weight
        else:
            overall_score = 50.0  # Default neutral score

        # Assign grade
        if overall_score >= 90:
            grade = 'A+'
        elif overall_score >= 85:
            grade = 'A'
        elif overall_score >= 80:
            grade = 'A-'
        elif overall_score >= 75:
            grade = 'B+'
        elif overall_score >= 70:
            grade = 'B'
        elif overall_score >= 65:
            grade = 'B-'
        elif overall_score >= 60:
            grade = 'C+'
        elif overall_score >= 55:
            grade = 'C'
        elif overall_score >= 50:
            grade = 'C-'
        elif overall_score >= 45:
            grade = 'D+'
        elif overall_score >= 40:
            grade = 'D'
        else:
            grade = 'F'

        # Generate summary
        strong_categories = [cat for cat, score in category_scores.items() if score >= 70]
        weak_categories = [cat for cat, score in category_scores.items() if score <= 40]

        summary = f"Overall financial health grade: {grade}. "
        if strong_categories:
            summary += f"Strong performance in {', '.join(strong_categories)}. "
        if weak_categories:
            summary += f"Improvement needed in {', '.join(weak_categories)}."

        return {
            'score': round(overall_score, 1),
            'grade': grade,
            'category_scores': category_scores,
            'summary': summary,
            'strong_areas': strong_categories,
            'weak_areas': weak_categories
        }

    def _generate_strategic_insights(self, report: ComprehensiveRatioReport) -> List[str]:
        """Generate strategic insights from the analysis"""
        insights = []

        # Analyze trends
        improving_ratios = []
        declining_ratios = []

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.trend_analysis:
                if enhanced_ratio.trend_analysis.trend_direction == "improving":
                    improving_ratios.append(ratio_name)
                elif enhanced_ratio.trend_analysis.trend_direction == "declining":
                    declining_ratios.append(ratio_name)

        if improving_ratios:
            insights.append(f"Positive momentum in {', '.join(improving_ratios[:3])} indicates strengthening operational performance.")

        if declining_ratios:
            insights.append(f"Declining trends in {', '.join(declining_ratios[:3])} require management attention and strategic intervention.")

        # Industry positioning insights
        leaders = []
        laggards = []

        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.industry_position == "leader":
                leaders.append(ratio_name)
            elif enhanced_ratio.industry_position == "laggard":
                laggards.append(ratio_name)

        if leaders:
            insights.append(f"Industry leadership in {', '.join(leaders[:3])} provides competitive advantages and market positioning strength.")

        if laggards:
            insights.append(f"Below-industry performance in {', '.join(laggards[:3])} presents opportunities for operational improvements.")

        # Volatility insights
        high_volatility_ratios = []
        for ratio_name, enhanced_ratio in report.enhanced_ratios.items():
            if enhanced_ratio.volatility_metrics and enhanced_ratio.volatility_metrics.coefficient_of_variation > 0.3:
                high_volatility_ratios.append(ratio_name)

        if high_volatility_ratios:
            insights.append(f"High volatility in {', '.join(high_volatility_ratios[:2])} suggests business model stability concerns requiring strategic focus.")

        # Peer comparison insights
        if report.peer_analysis:
            if len(report.peer_analysis.strength_areas) > len(report.peer_analysis.weakness_areas):
                insights.append("Strong relative peer performance indicates competitive positioning advantages in the current market environment.")
            elif len(report.peer_analysis.weakness_areas) > len(report.peer_analysis.strength_areas):
                insights.append("Relative underperformance versus peers suggests need for strategic repositioning and operational efficiency improvements.")

        return insights[:5]  # Limit to top 5 insights

    def _assess_risks(self, enhanced_ratios: Dict[str, EnhancedRatioMetric],
                     peer_analysis: Optional[PeerAnalysisReport] = None) -> Dict[str, Any]:
        """Assess financial and operational risks"""

        risk_factors = []
        risk_score = 0  # 0 = low risk, 100 = high risk

        # Liquidity risk
        liquidity_ratios = ['current_ratio', 'quick_ratio']
        liquidity_issues = []

        for ratio_name in liquidity_ratios:
            if ratio_name in enhanced_ratios:
                enhanced_ratio = enhanced_ratios[ratio_name]
                if enhanced_ratio.industry_position in ["poor", "laggard"]:
                    liquidity_issues.append(ratio_name)
                    risk_score += 15

        if liquidity_issues:
            risk_factors.append(f"Liquidity concerns identified in {', '.join(liquidity_issues)}")

        # Leverage risk
        leverage_ratios = ['debt_to_equity', 'interest_coverage']
        leverage_issues = []

        for ratio_name in leverage_ratios:
            if ratio_name in enhanced_ratios:
                enhanced_ratio = enhanced_ratios[ratio_name]
                if ratio_name == 'debt_to_equity' and enhanced_ratio.current_value > 1.0:
                    leverage_issues.append("high_debt")
                    risk_score += 20
                elif ratio_name == 'interest_coverage' and enhanced_ratio.current_value < 3.0:
                    leverage_issues.append("low_coverage")
                    risk_score += 15

        if leverage_issues:
            risk_factors.append("Financial leverage risks require monitoring")

        # Profitability risk
        profitability_declining = []
        for ratio_name in ['roe', 'roa', 'operating_margin']:
            if ratio_name in enhanced_ratios:
                enhanced_ratio = enhanced_ratios[ratio_name]
                if (enhanced_ratio.trend_analysis and
                    enhanced_ratio.trend_analysis.trend_direction == "declining"):
                    profitability_declining.append(ratio_name)
                    risk_score += 10

        if profitability_declining:
            risk_factors.append(f"Declining profitability trends in {', '.join(profitability_declining)}")

        # Volatility risk
        high_volatility_count = sum(1 for enhanced_ratio in enhanced_ratios.values()
                                   if enhanced_ratio.volatility_metrics and
                                   enhanced_ratio.volatility_metrics.coefficient_of_variation > 0.4)

        if high_volatility_count >= 3:
            risk_factors.append("High earnings volatility indicates business model instability")
            risk_score += 15

        # Competitive risk
        if peer_analysis and len(peer_analysis.weakness_areas) > 3:
            risk_factors.append("Competitive positioning challenges versus peer group")
            risk_score += 10

        # Risk level classification
        if risk_score <= 20:
            risk_level = "Low"
        elif risk_score <= 40:
            risk_level = "Moderate"
        elif risk_score <= 60:
            risk_level = "High"
        else:
            risk_level = "Very High"

        return {
            'risk_score': min(risk_score, 100),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'assessment_date': datetime.now().isoformat()
        }

    def _generate_ratio_recommendations(self, enhanced_ratio: EnhancedRatioMetric) -> List[str]:
        """Generate specific recommendations for a ratio"""
        recommendations = []
        ratio_name = enhanced_ratio.name
        current_value = enhanced_ratio.current_value

        # Industry position recommendations
        if enhanced_ratio.industry_position == "poor":
            if ratio_name == 'current_ratio':
                recommendations.append("Improve working capital management and cash flow timing")
            elif ratio_name in ['roe', 'roa']:
                recommendations.append("Focus on operational efficiency and asset utilization improvements")
            elif ratio_name == 'debt_to_equity':
                recommendations.append("Consider debt reduction strategies and capital structure optimization")

        # Trend-based recommendations
        if enhanced_ratio.trend_analysis:
            if enhanced_ratio.trend_analysis.trend_direction == "declining":
                recommendations.append(f"Address declining {ratio_name} trend through strategic initiatives")

        # Volatility recommendations
        if (enhanced_ratio.volatility_metrics and
            enhanced_ratio.volatility_metrics.coefficient_of_variation > 0.3):
            recommendations.append("Implement measures to reduce earnings volatility and improve predictability")

        return recommendations[:2]  # Limit to top 2 recommendations

    def _is_higher_better(self, ratio_name: str) -> bool:
        """Determine if higher values are better for a ratio"""
        lower_is_better = {'debt_to_equity', 'debt_to_assets', 'debt_ratio'}
        return ratio_name not in lower_is_better

    def _load_industry_weights(self) -> Dict[str, Dict[str, float]]:
        """Load industry-specific ratio weights"""
        # Default weights by industry (can be loaded from config file)
        return {
            'Technology': {
                'roe': 0.25, 'gross_margin': 0.20, 'operating_margin': 0.15,
                'current_ratio': 0.10, 'debt_to_equity': 0.10,
                'asset_turnover': 0.10, 'revenue_growth': 0.10
            },
            'Manufacturing': {
                'roe': 0.20, 'asset_turnover': 0.20, 'current_ratio': 0.15,
                'debt_to_equity': 0.15, 'operating_margin': 0.15,
                'inventory_turnover': 0.10, 'interest_coverage': 0.05
            },
            'Retail': {
                'inventory_turnover': 0.25, 'gross_margin': 0.20, 'roe': 0.15,
                'current_ratio': 0.15, 'asset_turnover': 0.15,
                'debt_to_equity': 0.10
            },
            'Financial Services': {
                'roe': 0.30, 'roa': 0.25, 'equity_ratio': 0.20,
                'efficiency_ratio': 0.15, 'loan_loss_ratio': 0.10
            }
        }

    def export_report(self, report: ComprehensiveRatioReport, file_path: Path,
                     format_type: str = 'json') -> None:
        """Export analysis report to file"""
        try:
            if format_type.lower() == 'json':
                import json

                # Convert report to serializable format
                report_dict = {
                    'company_ticker': report.company_ticker,
                    'company_name': report.company_name,
                    'industry': report.industry,
                    'analysis_date': report.analysis_date.isoformat(),
                    'overall_financial_health': report.overall_financial_health,
                    'strategic_insights': report.strategic_insights,
                    'risk_assessment': report.risk_assessment
                }

                with open(file_path, 'w') as f:
                    json.dump(report_dict, f, indent=2)

            logger.info(f"Report exported to {file_path}")

        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            raise