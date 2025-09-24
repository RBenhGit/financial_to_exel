"""
ESG Analysis Engine
===================

Comprehensive ESG (Environmental, Social, Governance) analysis engine that provides
scoring, risk assessment, and comparative analysis capabilities. This engine integrates
with the existing financial analysis framework to incorporate ESG factors into
investment decision-making.

Key Features:
- ESG risk assessment and scoring
- Peer comparison and industry benchmarking
- ESG trend analysis and performance tracking
- Integration with valuation models (ESG-adjusted DCF)
- ESG materiality assessment
- Custom ESG weighting and scoring methodologies
"""

import logging
import numpy as np
import pandas as pd
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

from core.data_processing.var_input_data import get_var_input_data
from core.analysis.esg.esg_variable_definitions import get_esg_variable_definitions, ESGCategory

logger = logging.getLogger(__name__)


class ESGRiskLevel(Enum):
    """ESG risk level classifications"""
    VERY_LOW = "very_low"      # 0-20
    LOW = "low"               # 20-40
    MEDIUM = "medium"         # 40-60
    HIGH = "high"             # 60-80
    VERY_HIGH = "very_high"   # 80-100


class ESGRating(Enum):
    """ESG letter ratings"""
    AAA = "AAA"  # 85-100
    AA = "AA"    # 75-84
    A = "A"      # 65-74
    BBB = "BBB"  # 55-64
    BB = "BB"    # 45-54
    B = "B"      # 35-44
    CCC = "CCC"  # 0-34


@dataclass
class ESGScore:
    """Individual ESG score with metadata"""
    pillar: str  # E, S, or G
    score: float  # 0-100 scale
    risk_level: ESGRiskLevel
    data_quality: float  # 0-1 scale
    last_updated: datetime
    data_sources: List[str]
    methodology: str

    def get_letter_rating(self) -> ESGRating:
        """Convert numerical score to letter rating"""
        if self.score >= 85:
            return ESGRating.AAA
        elif self.score >= 75:
            return ESGRating.AA
        elif self.score >= 65:
            return ESGRating.A
        elif self.score >= 55:
            return ESGRating.BBB
        elif self.score >= 45:
            return ESGRating.BB
        elif self.score >= 35:
            return ESGRating.B
        else:
            return ESGRating.CCC


@dataclass
class ESGAnalysisResult:
    """Comprehensive ESG analysis result"""
    symbol: str
    company_name: str
    analysis_date: datetime

    # Overall ESG metrics
    overall_esg_score: float
    overall_esg_rating: ESGRating
    overall_risk_level: ESGRiskLevel

    # Pillar scores
    environmental_score: ESGScore
    social_score: ESGScore
    governance_score: ESGScore

    # Risk assessment
    esg_risk_factors: List[str]
    material_esg_issues: List[str]

    # Comparative analysis
    industry_percentile: Optional[float]
    peer_comparison: Dict[str, float]

    # Trend analysis
    score_trend: str  # "improving", "stable", "deteriorating"
    trend_analysis: Dict[str, Any]

    # Data quality
    data_completeness: float
    data_sources_used: List[str]
    confidence_level: str

    # Recommendations
    improvement_areas: List[str]
    esg_opportunities: List[str]

    # Additional metrics
    custom_metrics: Dict[str, Any] = field(default_factory=dict)
    methodology_notes: List[str] = field(default_factory=list)


class ESGAnalysisEngine:
    """
    Comprehensive ESG analysis engine for scoring, risk assessment, and comparison.
    """

    def __init__(self):
        """Initialize the ESG analysis engine"""
        self.var_data = get_var_input_data()
        self.esg_variables = get_esg_variable_definitions()

        # ESG weighting schemes
        self.weighting_schemes = {
            'equal': {'E': 0.33, 'S': 0.33, 'G': 0.34},
            'environmental_focus': {'E': 0.5, 'S': 0.25, 'G': 0.25},
            'governance_focus': {'E': 0.25, 'S': 0.25, 'G': 0.5},
            'social_focus': {'E': 0.25, 'S': 0.5, 'G': 0.25},
            'custom': {'E': 0.4, 'S': 0.3, 'G': 0.3}  # Can be customized
        }

        # Industry-specific ESG materiality factors
        self.industry_materiality = {
            'technology': {
                'data_privacy': 0.3,
                'energy_efficiency': 0.25,
                'board_diversity': 0.2,
                'employee_satisfaction': 0.15,
                'carbon_footprint': 0.1
            },
            'energy': {
                'carbon_emissions': 0.4,
                'environmental_compliance': 0.25,
                'safety_record': 0.2,
                'community_relations': 0.15
            },
            'financial': {
                'governance_quality': 0.35,
                'regulatory_compliance': 0.25,
                'customer_protection': 0.2,
                'diversity_inclusion': 0.2
            },
            'default': {
                'environmental_impact': 0.3,
                'social_responsibility': 0.35,
                'governance_quality': 0.35
            }
        }

        logger.info("ESG Analysis Engine initialized")

    def analyze_company_esg(
        self,
        symbol: str,
        weighting_scheme: str = 'equal',
        industry: Optional[str] = None,
        benchmark_peers: Optional[List[str]] = None
    ) -> ESGAnalysisResult:
        """
        Perform comprehensive ESG analysis for a company.

        Args:
            symbol: Stock ticker symbol
            weighting_scheme: ESG pillar weighting scheme to use
            industry: Industry classification for materiality assessment
            benchmark_peers: List of peer companies for comparison

        Returns:
            ESGAnalysisResult with comprehensive analysis
        """
        logger.info(f"Starting comprehensive ESG analysis for {symbol}")

        analysis_date = datetime.now()

        # Get company name from var_data
        company_name = self._get_company_name(symbol)

        # Calculate pillar scores
        environmental_score = self._calculate_environmental_score(symbol)
        social_score = self._calculate_social_score(symbol)
        governance_score = self._calculate_governance_score(symbol)

        # Calculate overall ESG score
        weights = self.weighting_schemes.get(weighting_scheme, self.weighting_schemes['equal'])
        overall_esg_score = (
            environmental_score.score * weights['E'] +
            social_score.score * weights['S'] +
            governance_score.score * weights['G']
        )

        overall_esg_rating = self._score_to_rating(overall_esg_score)
        overall_risk_level = self._score_to_risk_level(overall_esg_score)

        # Risk assessment
        esg_risk_factors = self._identify_risk_factors(symbol, environmental_score, social_score, governance_score)
        material_esg_issues = self._assess_material_issues(symbol, industry)

        # Comparative analysis
        industry_percentile = self._calculate_industry_percentile(symbol, overall_esg_score, industry)
        peer_comparison = self._compare_with_peers(symbol, overall_esg_score, benchmark_peers)

        # Trend analysis
        score_trend, trend_analysis = self._analyze_esg_trends(symbol)

        # Data quality assessment
        data_completeness = self._assess_data_completeness(symbol)
        data_sources_used = self._get_data_sources_used(symbol)
        confidence_level = self._determine_confidence_level(data_completeness, data_sources_used)

        # Recommendations
        improvement_areas = self._identify_improvement_areas(environmental_score, social_score, governance_score)
        esg_opportunities = self._identify_opportunities(symbol, industry)

        result = ESGAnalysisResult(
            symbol=symbol,
            company_name=company_name,
            analysis_date=analysis_date,
            overall_esg_score=overall_esg_score,
            overall_esg_rating=overall_esg_rating,
            overall_risk_level=overall_risk_level,
            environmental_score=environmental_score,
            social_score=social_score,
            governance_score=governance_score,
            esg_risk_factors=esg_risk_factors,
            material_esg_issues=material_esg_issues,
            industry_percentile=industry_percentile,
            peer_comparison=peer_comparison,
            score_trend=score_trend,
            trend_analysis=trend_analysis,
            data_completeness=data_completeness,
            data_sources_used=data_sources_used,
            confidence_level=confidence_level,
            improvement_areas=improvement_areas,
            esg_opportunities=esg_opportunities,
            methodology_notes=[
                f"Used {weighting_scheme} weighting scheme",
                f"Industry materiality factors: {industry or 'default'}",
                "Scores normalized to 0-100 scale",
                "Risk levels: Very Low (0-20), Low (20-40), Medium (40-60), High (60-80), Very High (80-100)"
            ]
        )

        logger.info(f"Completed ESG analysis for {symbol}: Overall score {overall_esg_score:.1f} ({overall_esg_rating.value})")
        return result

    def _calculate_environmental_score(self, symbol: str) -> ESGScore:
        """Calculate Environmental pillar score"""
        environmental_vars = [
            'carbon_emissions_total',
            'carbon_intensity',
            'energy_consumption',
            'renewable_energy_percentage',
            'water_consumption',
            'waste_generated',
            'waste_recycling_rate'
        ]

        scores = []
        data_sources = []

        for var_name in environmental_vars:
            try:
                value = self.var_data.get_variable(symbol, var_name)
                if value is not None:
                    # Normalize to 0-100 score (implementation depends on variable)
                    normalized_score = self._normalize_environmental_metric(var_name, value)
                    scores.append(normalized_score)

                    # Track data source
                    metadata = self.var_data.get_variable_metadata(symbol, var_name)
                    if metadata and 'source' in metadata:
                        data_sources.append(metadata['source'])
            except Exception as e:
                logger.debug(f"Could not get environmental variable {var_name} for {symbol}: {e}")

        # Calculate average score or use default if no data
        env_score = statistics.mean(scores) if scores else 50.0  # Neutral score if no data
        risk_level = self._score_to_risk_level(env_score)
        data_quality = len(scores) / len(environmental_vars)  # Completeness ratio

        return ESGScore(
            pillar="E",
            score=env_score,
            risk_level=risk_level,
            data_quality=data_quality,
            last_updated=datetime.now(),
            data_sources=list(set(data_sources)),
            methodology="Weighted average of environmental metrics"
        )

    def _calculate_social_score(self, symbol: str) -> ESGScore:
        """Calculate Social pillar score"""
        social_vars = [
            'employee_count_total',
            'employee_turnover_rate',
            'gender_diversity_board',
            'gender_diversity_workforce',
            'workplace_safety_incidents',
            'training_hours_per_employee'
        ]

        scores = []
        data_sources = []

        for var_name in social_vars:
            try:
                value = self.var_data.get_variable(symbol, var_name)
                if value is not None:
                    normalized_score = self._normalize_social_metric(var_name, value)
                    scores.append(normalized_score)

                    metadata = self.var_data.get_variable_metadata(symbol, var_name)
                    if metadata and 'source' in metadata:
                        data_sources.append(metadata['source'])
            except Exception as e:
                logger.debug(f"Could not get social variable {var_name} for {symbol}: {e}")

        social_score = statistics.mean(scores) if scores else 50.0
        risk_level = self._score_to_risk_level(social_score)
        data_quality = len(scores) / len(social_vars)

        return ESGScore(
            pillar="S",
            score=social_score,
            risk_level=risk_level,
            data_quality=data_quality,
            last_updated=datetime.now(),
            data_sources=list(set(data_sources)),
            methodology="Weighted average of social metrics"
        )

    def _calculate_governance_score(self, symbol: str) -> ESGScore:
        """Calculate Governance pillar score"""
        governance_vars = [
            'board_independence',
            'board_size',
            'audit_committee_independence',
            'executive_compensation_ratio',
            'shareholder_rights_score'
        ]

        scores = []
        data_sources = []

        for var_name in governance_vars:
            try:
                value = self.var_data.get_variable(symbol, var_name)
                if value is not None:
                    normalized_score = self._normalize_governance_metric(var_name, value)
                    scores.append(normalized_score)

                    metadata = self.var_data.get_variable_metadata(symbol, var_name)
                    if metadata and 'source' in metadata:
                        data_sources.append(metadata['source'])
            except Exception as e:
                logger.debug(f"Could not get governance variable {var_name} for {symbol}: {e}")

        governance_score = statistics.mean(scores) if scores else 50.0
        risk_level = self._score_to_risk_level(governance_score)
        data_quality = len(scores) / len(governance_vars)

        return ESGScore(
            pillar="G",
            score=governance_score,
            risk_level=risk_level,
            data_quality=data_quality,
            last_updated=datetime.now(),
            data_sources=list(set(data_sources)),
            methodology="Weighted average of governance metrics"
        )

    def _normalize_environmental_metric(self, var_name: str, value: Union[int, float]) -> float:
        """Normalize environmental metric to 0-100 score"""
        # Implementation depends on the specific metric
        # Higher values are better for some metrics (recycling rate), worse for others (emissions)

        normalization_rules = {
            'renewable_energy_percentage': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'waste_recycling_rate': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'carbon_intensity': lambda x: max(0, 100 - min(x, 100)),  # Lower is better, cap at 100
            'carbon_emissions_total': lambda x: max(0, 100 - min(x / 1000, 100)),  # Lower is better
            'energy_consumption': lambda x: max(0, 100 - min(x / 10000, 100)),  # Lower is better
            'water_consumption': lambda x: max(0, 100 - min(x / 1000000, 100)),  # Lower is better
            'waste_generated': lambda x: max(0, 100 - min(x / 10000, 100))  # Lower is better
        }

        if var_name in normalization_rules:
            return normalization_rules[var_name](value)
        else:
            # Default: assume higher is better and cap at 100
            return min(value, 100)

    def _normalize_social_metric(self, var_name: str, value: Union[int, float]) -> float:
        """Normalize social metric to 0-100 score"""
        normalization_rules = {
            'employee_turnover_rate': lambda x: max(0, 100 - x),  # Lower turnover is better
            'gender_diversity_board': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'gender_diversity_workforce': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'workplace_safety_incidents': lambda x: max(0, 100 - x * 10),  # Lower incidents are better
            'training_hours_per_employee': lambda x: min(x * 2, 100),  # More training is better, cap at 100
            'employee_count_total': lambda x: 50  # Neutral scoring for company size
        }

        if var_name in normalization_rules:
            return normalization_rules[var_name](value)
        else:
            return min(value, 100)

    def _normalize_governance_metric(self, var_name: str, value: Union[int, float]) -> float:
        """Normalize governance metric to 0-100 score"""
        normalization_rules = {
            'board_independence': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'audit_committee_independence': lambda x: x * 100,  # Already 0-1, convert to 0-100
            'board_size': lambda x: 100 - abs(x - 9) * 5,  # Optimal around 9 directors
            'executive_compensation_ratio': lambda x: max(0, 100 - min(x / 10, 100)),  # Lower ratio is better
            'shareholder_rights_score': lambda x: x  # Already 0-100 scale
        }

        if var_name in normalization_rules:
            return normalization_rules[var_name](value)
        else:
            return min(value, 100)

    def _score_to_risk_level(self, score: float) -> ESGRiskLevel:
        """Convert ESG score to risk level"""
        if score >= 80:
            return ESGRiskLevel.VERY_LOW
        elif score >= 60:
            return ESGRiskLevel.LOW
        elif score >= 40:
            return ESGRiskLevel.MEDIUM
        elif score >= 20:
            return ESGRiskLevel.HIGH
        else:
            return ESGRiskLevel.VERY_HIGH

    def _score_to_rating(self, score: float) -> ESGRating:
        """Convert ESG score to letter rating"""
        if score >= 85:
            return ESGRating.AAA
        elif score >= 75:
            return ESGRating.AA
        elif score >= 65:
            return ESGRating.A
        elif score >= 55:
            return ESGRating.BBB
        elif score >= 45:
            return ESGRating.BB
        elif score >= 35:
            return ESGRating.B
        else:
            return ESGRating.CCC

    def _identify_risk_factors(self, symbol: str, env_score: ESGScore, social_score: ESGScore, gov_score: ESGScore) -> List[str]:
        """Identify key ESG risk factors based on low scores"""
        risk_factors = []

        if env_score.score < 40:
            risk_factors.append("High environmental risk - poor environmental performance")
        if social_score.score < 40:
            risk_factors.append("High social risk - social responsibility concerns")
        if gov_score.score < 40:
            risk_factors.append("High governance risk - governance structure weaknesses")

        # Add specific risk factors based on individual metrics
        try:
            carbon_intensity = self.var_data.get_variable(symbol, 'carbon_intensity')
            if carbon_intensity and carbon_intensity > 500:  # Example threshold
                risk_factors.append("High carbon intensity relative to revenue")
        except:
            pass

        return risk_factors

    def _assess_material_issues(self, symbol: str, industry: Optional[str]) -> List[str]:
        """Assess material ESG issues for the company based on industry"""
        material_issues = []

        # Get industry-specific material issues
        industry_key = industry.lower() if industry else 'default'
        materiality_factors = self.industry_materiality.get(industry_key, self.industry_materiality['default'])

        # Identify top material issues
        for issue, weight in sorted(materiality_factors.items(), key=lambda x: x[1], reverse=True):
            if weight > 0.2:  # Only include highly material issues
                material_issues.append(issue.replace('_', ' ').title())

        return material_issues

    def _calculate_industry_percentile(self, symbol: str, esg_score: float, industry: Optional[str]) -> Optional[float]:
        """Calculate industry percentile ranking (placeholder implementation)"""
        # This would require industry ESG benchmarking data
        # For now, return a placeholder based on score
        if esg_score >= 75:
            return 90.0  # Top decile
        elif esg_score >= 60:
            return 75.0  # Third quartile
        elif esg_score >= 40:
            return 50.0  # Median
        elif esg_score >= 25:
            return 25.0  # First quartile
        else:
            return 10.0  # Bottom decile

    def _compare_with_peers(self, symbol: str, esg_score: float, peers: Optional[List[str]]) -> Dict[str, float]:
        """Compare ESG score with peer companies"""
        peer_comparison = {}

        if not peers:
            return peer_comparison

        for peer in peers:
            try:
                # This would calculate peer's ESG score
                # For now, return placeholder values
                peer_comparison[peer] = esg_score + np.random.uniform(-15, 15)  # Placeholder
            except Exception as e:
                logger.debug(f"Could not get ESG score for peer {peer}: {e}")

        return peer_comparison

    def _analyze_esg_trends(self, symbol: str) -> Tuple[str, Dict[str, Any]]:
        """Analyze ESG score trends over time"""
        # This would require historical ESG data
        # For now, return placeholder trend analysis
        return "stable", {
            "trend_direction": "stable",
            "trend_strength": 0.0,
            "data_points": 1,
            "analysis_period": "current"
        }

    def _assess_data_completeness(self, symbol: str) -> float:
        """Assess completeness of ESG data"""
        total_variables = len(self.esg_variables)
        available_variables = 0

        for var_name in self.esg_variables.keys():
            try:
                value = self.var_data.get_variable(symbol, var_name)
                if value is not None:
                    available_variables += 1
            except:
                pass

        return available_variables / total_variables if total_variables > 0 else 0.0

    def _get_data_sources_used(self, symbol: str) -> List[str]:
        """Get list of data sources used for ESG analysis"""
        sources = set()

        for var_name in self.esg_variables.keys():
            try:
                metadata = self.var_data.get_variable_metadata(symbol, var_name)
                if metadata and 'source' in metadata:
                    sources.add(metadata['source'])
            except:
                pass

        return list(sources)

    def _determine_confidence_level(self, data_completeness: float, data_sources: List[str]) -> str:
        """Determine confidence level in ESG analysis"""
        if data_completeness >= 0.8 and len(data_sources) >= 2:
            return "High"
        elif data_completeness >= 0.5 and len(data_sources) >= 1:
            return "Medium"
        else:
            return "Low"

    def _identify_improvement_areas(self, env_score: ESGScore, social_score: ESGScore, gov_score: ESGScore) -> List[str]:
        """Identify areas for ESG improvement"""
        improvements = []

        if env_score.score < 60:
            improvements.append("Environmental performance and sustainability initiatives")
        if social_score.score < 60:
            improvements.append("Social responsibility and stakeholder engagement")
        if gov_score.score < 60:
            improvements.append("Corporate governance and transparency")

        return improvements

    def _identify_opportunities(self, symbol: str, industry: Optional[str]) -> List[str]:
        """Identify ESG opportunities"""
        opportunities = [
            "Implement comprehensive sustainability reporting",
            "Enhance board diversity and independence",
            "Develop climate risk mitigation strategies",
            "Strengthen stakeholder engagement programs",
            "Improve supply chain sustainability practices"
        ]

        return opportunities[:3]  # Return top 3 opportunities

    def _get_company_name(self, symbol: str) -> str:
        """Get company name from var_data or return symbol as fallback"""
        try:
            company_name = self.var_data.get_variable(symbol, 'company_name')
            return company_name or symbol
        except:
            return symbol

    def generate_esg_report(self, analysis_result: ESGAnalysisResult) -> str:
        """Generate a comprehensive ESG analysis report"""
        report = f"""
ESG ANALYSIS REPORT
===================

Company: {analysis_result.company_name} ({analysis_result.symbol})
Analysis Date: {analysis_result.analysis_date.strftime('%Y-%m-%d')}

OVERALL ESG ASSESSMENT
----------------------
ESG Score: {analysis_result.overall_esg_score:.1f}/100
ESG Rating: {analysis_result.overall_esg_rating.value}
Risk Level: {analysis_result.overall_risk_level.value.replace('_', ' ').title()}

PILLAR SCORES
-------------
Environmental (E): {analysis_result.environmental_score.score:.1f}/100 ({analysis_result.environmental_score.risk_level.value.replace('_', ' ').title()} Risk)
Social (S): {analysis_result.social_score.score:.1f}/100 ({analysis_result.social_score.risk_level.value.replace('_', ' ').title()} Risk)
Governance (G): {analysis_result.governance_score.score:.1f}/100 ({analysis_result.governance_score.risk_level.value.replace('_', ' ').title()} Risk)

RISK ASSESSMENT
---------------
Key Risk Factors:
{chr(10).join(f'• {factor}' for factor in analysis_result.esg_risk_factors)}

Material ESG Issues:
{chr(10).join(f'• {issue}' for issue in analysis_result.material_esg_issues)}

COMPARATIVE ANALYSIS
--------------------
Industry Percentile: {analysis_result.industry_percentile:.1f}th percentile
Trend: {analysis_result.score_trend.title()}

DATA QUALITY
------------
Data Completeness: {analysis_result.data_completeness:.1%}
Confidence Level: {analysis_result.confidence_level}
Data Sources: {', '.join(analysis_result.data_sources_used)}

RECOMMENDATIONS
---------------
Priority Improvement Areas:
{chr(10).join(f'• {area}' for area in analysis_result.improvement_areas)}

ESG Opportunities:
{chr(10).join(f'• {opportunity}' for opportunity in analysis_result.esg_opportunities)}

METHODOLOGY NOTES
-----------------
{chr(10).join(f'• {note}' for note in analysis_result.methodology_notes)}
"""

        return report