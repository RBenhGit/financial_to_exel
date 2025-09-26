"""
Feature Adoption Analytics System

This module tracks and analyzes feature adoption patterns across the 6 validated
UAT scenarios, providing insights into user behavior, feature utilization,
and optimization opportunities for the financial analysis application.
"""

import os
import sys
import json
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import numpy as np

# Import logging utilities
try:
    from utils.logging_config import get_streamlit_logger
    logger = get_streamlit_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class FeatureUsageEvent:
    """Single feature usage event."""
    event_id: str
    feature_name: str
    scenario_category: str
    user_session: Optional[str]
    timestamp: datetime
    duration: Optional[float]
    success: bool
    interaction_count: int
    user_skill_level: str  # "beginner", "intermediate", "expert"
    context_data: Dict[str, Any]


@dataclass
class FeatureAdoptionMetrics:
    """Feature adoption metrics for analysis."""
    feature_name: str
    total_usage_count: int
    unique_user_count: int
    adoption_rate_percent: float
    avg_session_duration: float
    success_rate_percent: float
    user_retention_rate: float
    skill_level_distribution: Dict[str, int]
    peak_usage_hours: List[int]
    trend_direction: str


@dataclass
class ScenarioAdoptionAnalysis:
    """Adoption analysis for a specific UAT scenario."""
    scenario_name: str
    overall_adoption_rate: float
    feature_adoption_rates: Dict[str, float]
    user_journey_completion_rate: float
    drop_off_points: List[str]
    optimization_opportunities: List[str]
    user_satisfaction_correlation: float


class FeatureAdoptionAnalytics:
    """
    Feature adoption analytics system for the 6 validated UAT scenarios:
    1. FCF Analysis Workflow
    2. DCF Valuation Analysis
    3. DDM Analysis
    4. P/B Historical Analysis
    5. Multi-Company Portfolio Analysis
    6. Watch List Management
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the feature adoption analytics system."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.adoption_db_path = self.project_root / "data" / "feature_adoption.db"
        self.reports_dir = self.project_root / "reports" / "adoption_analytics"

        # Ensure directories exist
        self.adoption_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Define feature mapping for the 6 validated scenarios
        self._init_feature_mapping()

    def _init_database(self):
        """Initialize SQLite database for feature adoption tracking."""

        with sqlite3.connect(self.adoption_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS feature_usage_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    feature_name TEXT NOT NULL,
                    scenario_category TEXT NOT NULL,
                    user_session TEXT,
                    timestamp TEXT NOT NULL,
                    duration REAL,
                    success INTEGER NOT NULL,
                    interaction_count INTEGER DEFAULT 1,
                    user_skill_level TEXT DEFAULT 'intermediate',
                    context_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    skill_level TEXT DEFAULT 'intermediate',
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    scenarios_completed TEXT,
                    total_features_used INTEGER DEFAULT 0,
                    session_success INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create indexes
            conn.execute('CREATE INDEX IF NOT EXISTS idx_feature_timestamp ON feature_usage_events(feature_name, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_scenario_timestamp ON feature_usage_events(scenario_category, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_session_timestamp ON feature_usage_events(user_session, timestamp)')

    def _init_feature_mapping(self):
        """Initialize feature mapping for the 6 validated UAT scenarios."""

        self.scenario_features = {
            "fcf_analysis": {
                "scenario_name": "Basic FCF Analysis Workflow",
                "features": [
                    "data_import_excel",
                    "financial_data_validation",
                    "fcf_calculation",
                    "fcf_visualization",
                    "results_export",
                    "sensitivity_analysis"
                ]
            },
            "dcf_valuation": {
                "scenario_name": "DCF Valuation Analysis",
                "features": [
                    "cash_flow_projection",
                    "discount_rate_calculation",
                    "terminal_value_estimation",
                    "dcf_model_execution",
                    "valuation_visualization",
                    "scenario_modeling",
                    "results_summary"
                ]
            },
            "ddm_analysis": {
                "scenario_name": "Dividend Discount Model (DDM) Analysis",
                "features": [
                    "dividend_data_collection",
                    "dividend_growth_analysis",
                    "ddm_calculation",
                    "dividend_yield_analysis",
                    "payout_ratio_analysis",
                    "ddm_visualization"
                ]
            },
            "pb_analysis": {
                "scenario_name": "Price-to-Book (P/B) Historical Analysis",
                "features": [
                    "book_value_calculation",
                    "pb_ratio_analysis",
                    "historical_pb_comparison",
                    "industry_pb_benchmarking",
                    "pb_trend_visualization",
                    "valuation_assessment"
                ]
            },
            "portfolio_analysis": {
                "scenario_name": "Multi-Company Portfolio Analysis",
                "features": [
                    "multi_company_data_import",
                    "portfolio_composition",
                    "comparative_analysis",
                    "risk_assessment",
                    "portfolio_optimization",
                    "diversification_analysis",
                    "portfolio_reporting"
                ]
            },
            "watchlist_management": {
                "scenario_name": "Watch List Management",
                "features": [
                    "company_search",
                    "watchlist_add_remove",
                    "watchlist_organization",
                    "alert_configuration",
                    "watchlist_monitoring",
                    "quick_analysis_access"
                ]
            }
        }

        # Create reverse mapping
        self.feature_to_scenario = {}
        for scenario, config in self.scenario_features.items():
            for feature in config["features"]:
                self.feature_to_scenario[feature] = scenario

    def track_feature_usage(self, feature_name: str, user_session: Optional[str] = None,
                           duration: Optional[float] = None, success: bool = True,
                           interaction_count: int = 1, user_skill_level: str = "intermediate",
                           context_data: Optional[Dict[str, Any]] = None) -> str:
        """Track a feature usage event."""

        # Determine scenario category
        scenario_category = self.feature_to_scenario.get(feature_name, "unknown")

        # Generate event ID
        event_id = f"{feature_name}_{user_session or 'anonymous'}_{int(datetime.now().timestamp())}"

        # Create usage event
        event = FeatureUsageEvent(
            event_id=event_id,
            feature_name=feature_name,
            scenario_category=scenario_category,
            user_session=user_session,
            timestamp=datetime.now(),
            duration=duration,
            success=success,
            interaction_count=interaction_count,
            user_skill_level=user_skill_level,
            context_data=context_data or {}
        )

        # Store in database
        self._store_usage_event(event)

        logger.info(f"Tracked feature usage: {feature_name} in {scenario_category}")
        return event_id

    def _store_usage_event(self, event: FeatureUsageEvent):
        """Store feature usage event in database."""

        with sqlite3.connect(self.adoption_db_path) as conn:
            try:
                conn.execute('''
                    INSERT INTO feature_usage_events
                    (event_id, feature_name, scenario_category, user_session,
                     timestamp, duration, success, interaction_count,
                     user_skill_level, context_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_id,
                    event.feature_name,
                    event.scenario_category,
                    event.user_session,
                    event.timestamp.isoformat(),
                    event.duration,
                    1 if event.success else 0,
                    event.interaction_count,
                    event.user_skill_level,
                    json.dumps(event.context_data)
                ))
            except sqlite3.IntegrityError:
                logger.warning(f"Duplicate event ID: {event.event_id}")

    def get_adoption_data(self, scenario: Optional[str] = None,
                         days: int = 30) -> pd.DataFrame:
        """Retrieve feature adoption data from database."""

        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.adoption_db_path) as conn:
            if scenario:
                query = '''
                    SELECT * FROM feature_usage_events
                    WHERE scenario_category = ? AND timestamp >= ?
                    ORDER BY timestamp
                '''
                params = (scenario, cutoff_date.isoformat())
            else:
                query = '''
                    SELECT * FROM feature_usage_events
                    WHERE timestamp >= ?
                    ORDER BY timestamp
                '''
                params = (cutoff_date.isoformat(),)

            df = pd.read_sql_query(query, conn, params=params)

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df['success'] = df['success'].astype(bool)
                df['hour'] = df['timestamp'].dt.hour

            return df

    def analyze_feature_adoption(self, feature_name: str, days: int = 30) -> FeatureAdoptionMetrics:
        """Analyze adoption metrics for a specific feature."""

        df = self.get_adoption_data(days=days)
        feature_df = df[df['feature_name'] == feature_name]

        if feature_df.empty:
            return FeatureAdoptionMetrics(
                feature_name=feature_name,
                total_usage_count=0,
                unique_user_count=0,
                adoption_rate_percent=0.0,
                avg_session_duration=0.0,
                success_rate_percent=0.0,
                user_retention_rate=0.0,
                skill_level_distribution={},
                peak_usage_hours=[],
                trend_direction="no_data"
            )

        # Calculate metrics
        total_usage_count = len(feature_df)
        unique_user_count = feature_df['user_session'].nunique()

        # Calculate adoption rate (users who used this feature vs total users in period)
        total_users = df['user_session'].nunique() if not df.empty else 1
        adoption_rate_percent = (unique_user_count / total_users) * 100

        # Average session duration
        duration_df = feature_df[feature_df['duration'].notna()]
        avg_session_duration = duration_df['duration'].mean() if not duration_df.empty else 0.0

        # Success rate
        success_rate_percent = (feature_df['success'].sum() / len(feature_df)) * 100

        # User retention (users who used feature more than once)
        user_usage_counts = feature_df['user_session'].value_counts()
        repeat_users = (user_usage_counts > 1).sum()
        user_retention_rate = (repeat_users / unique_user_count) * 100 if unique_user_count > 0 else 0

        # Skill level distribution
        skill_level_distribution = feature_df['user_skill_level'].value_counts().to_dict()

        # Peak usage hours
        hourly_usage = feature_df['hour'].value_counts()
        peak_hours = hourly_usage.nlargest(3).index.tolist()

        # Trend analysis
        if len(feature_df) > 1:
            feature_df_sorted = feature_df.sort_values('timestamp')
            first_half = feature_df_sorted[:len(feature_df_sorted)//2]
            second_half = feature_df_sorted[len(feature_df_sorted)//2:]

            first_half_daily = first_half.groupby(first_half['timestamp'].dt.date).size().mean()
            second_half_daily = second_half.groupby(second_half['timestamp'].dt.date).size().mean()

            if second_half_daily > first_half_daily * 1.1:
                trend_direction = "increasing"
            elif second_half_daily < first_half_daily * 0.9:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
        else:
            trend_direction = "insufficient_data"

        return FeatureAdoptionMetrics(
            feature_name=feature_name,
            total_usage_count=total_usage_count,
            unique_user_count=unique_user_count,
            adoption_rate_percent=adoption_rate_percent,
            avg_session_duration=avg_session_duration,
            success_rate_percent=success_rate_percent,
            user_retention_rate=user_retention_rate,
            skill_level_distribution=skill_level_distribution,
            peak_usage_hours=peak_hours,
            trend_direction=trend_direction
        )

    def analyze_scenario_adoption(self, scenario: str, days: int = 30) -> ScenarioAdoptionAnalysis:
        """Analyze adoption patterns for a complete UAT scenario."""

        if scenario not in self.scenario_features:
            raise ValueError(f"Unknown scenario: {scenario}")

        scenario_config = self.scenario_features[scenario]
        scenario_features = scenario_config["features"]

        # Get all usage data for this scenario
        df = self.get_adoption_data(scenario, days)

        if df.empty:
            return ScenarioAdoptionAnalysis(
                scenario_name=scenario_config["scenario_name"],
                overall_adoption_rate=0.0,
                feature_adoption_rates={},
                user_journey_completion_rate=0.0,
                drop_off_points=[],
                optimization_opportunities=[],
                user_satisfaction_correlation=0.0
            )

        # Calculate overall adoption rate
        total_users = df['user_session'].nunique()
        users_who_used_scenario = df['user_session'].nunique()  # Already filtered by scenario
        overall_adoption_rate = (users_who_used_scenario / max(1, total_users)) * 100

        # Feature-level adoption rates
        feature_adoption_rates = {}
        for feature in scenario_features:
            feature_metrics = self.analyze_feature_adoption(feature, days)
            feature_adoption_rates[feature] = feature_metrics.adoption_rate_percent

        # User journey completion analysis
        user_feature_counts = df.groupby('user_session')['feature_name'].nunique()
        users_using_most_features = (user_feature_counts >= len(scenario_features) * 0.8).sum()
        user_journey_completion_rate = (users_using_most_features / total_users) * 100 if total_users > 0 else 0

        # Identify drop-off points (features with low adoption relative to scenario average)
        avg_adoption = np.mean(list(feature_adoption_rates.values()))
        drop_off_points = [
            feature for feature, rate in feature_adoption_rates.items()
            if rate < avg_adoption * 0.7  # 30% below average
        ]

        # Generate optimization opportunities
        optimization_opportunities = []

        if user_journey_completion_rate < 70:
            optimization_opportunities.append(f"Low completion rate ({user_journey_completion_rate:.1f}%) - improve user flow")

        if drop_off_points:
            optimization_opportunities.append(f"Address drop-off points: {', '.join(drop_off_points)}")

        low_success_features = []
        for feature in scenario_features:
            feature_data = df[df['feature_name'] == feature]
            if not feature_data.empty:
                success_rate = feature_data['success'].mean() * 100
                if success_rate < 90:
                    low_success_features.append(f"{feature} ({success_rate:.1f}%)")

        if low_success_features:
            optimization_opportunities.append(f"Improve reliability: {', '.join(low_success_features)}")

        if not optimization_opportunities:
            optimization_opportunities.append("Scenario performing well - maintain current standards")

        # User satisfaction correlation (simplified)
        # In a real implementation, this would correlate with actual satisfaction scores
        avg_success_rate = df['success'].mean() * 100 if not df.empty else 0
        user_satisfaction_correlation = min(1.0, avg_success_rate / 90.0)  # Normalize to 0-1

        return ScenarioAdoptionAnalysis(
            scenario_name=scenario_config["scenario_name"],
            overall_adoption_rate=overall_adoption_rate,
            feature_adoption_rates=feature_adoption_rates,
            user_journey_completion_rate=user_journey_completion_rate,
            drop_off_points=drop_off_points,
            optimization_opportunities=optimization_opportunities,
            user_satisfaction_correlation=user_satisfaction_correlation
        )

    def generate_comprehensive_adoption_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive feature adoption report across all 6 scenarios."""

        report = {
            "report_id": f"ADOPTION_ANALYTICS_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "analysis_period_days": days,
            "uat_scenarios": {},
            "overall_analytics": {},
            "cross_scenario_insights": {},
            "recommendations": []
        }

        # Analyze each UAT scenario
        scenario_analyses = {}
        for scenario_key in self.scenario_features.keys():
            try:
                analysis = self.analyze_scenario_adoption(scenario_key, days)
                scenario_analyses[scenario_key] = analysis
                report["uat_scenarios"][scenario_key] = asdict(analysis)
            except Exception as e:
                logger.error(f"Error analyzing scenario {scenario_key}: {e}")

        # Overall analytics
        if scenario_analyses:
            all_adoption_rates = [a.overall_adoption_rate for a in scenario_analyses.values()]
            all_completion_rates = [a.user_journey_completion_rate for a in scenario_analyses.values()]

            report["overall_analytics"] = {
                "scenarios_analyzed": len(scenario_analyses),
                "average_adoption_rate": np.mean(all_adoption_rates),
                "average_completion_rate": np.mean(all_completion_rates),
                "highest_adoption_scenario": max(scenario_analyses.items(), key=lambda x: x[1].overall_adoption_rate)[0],
                "lowest_adoption_scenario": min(scenario_analyses.items(), key=lambda x: x[1].overall_adoption_rate)[0],
                "total_optimization_opportunities": sum(len(a.optimization_opportunities) for a in scenario_analyses.values())
            }

        # Cross-scenario insights
        all_features = {}
        for scenario_key, scenario_config in self.scenario_features.items():
            for feature in scenario_config["features"]:
                metrics = self.analyze_feature_adoption(feature, days)
                all_features[feature] = metrics

        if all_features:
            top_adopted_features = sorted(all_features.items(), key=lambda x: x[1].adoption_rate_percent, reverse=True)[:5]
            least_adopted_features = sorted(all_features.items(), key=lambda x: x[1].adoption_rate_percent)[:5]

            report["cross_scenario_insights"] = {
                "most_adopted_features": [(f[0], f[1].adoption_rate_percent) for f in top_adopted_features],
                "least_adopted_features": [(f[0], f[1].adoption_rate_percent) for f in least_adopted_features],
                "features_with_high_retention": [
                    (name, metrics.user_retention_rate) for name, metrics in all_features.items()
                    if metrics.user_retention_rate > 60
                ],
                "features_needing_attention": [
                    name for name, metrics in all_features.items()
                    if metrics.success_rate_percent < 90 or metrics.adoption_rate_percent < 30
                ]
            }

        # Generate recommendations
        recommendations = []

        # Scenario-level recommendations
        for scenario_key, analysis in scenario_analyses.items():
            if analysis.overall_adoption_rate < 50:
                recommendations.append(f"Low adoption in {scenario_key} scenario ({analysis.overall_adoption_rate:.1f}%) - investigate barriers")

            if analysis.user_journey_completion_rate < 60:
                recommendations.append(f"Improve user flow in {scenario_key} - completion rate only {analysis.user_journey_completion_rate:.1f}%")

        # Feature-level recommendations
        if "features_needing_attention" in report["cross_scenario_insights"]:
            problem_features = report["cross_scenario_insights"]["features_needing_attention"]
            if problem_features:
                recommendations.append(f"Focus on improving: {', '.join(problem_features[:3])}")

        # Positive reinforcement
        if report["overall_analytics"].get("average_adoption_rate", 0) > 70:
            recommendations.append("Strong adoption rates across scenarios - maintain current user experience quality")

        if not recommendations:
            recommendations.append("Feature adoption analysis complete - continue monitoring user behavior")

        report["recommendations"] = recommendations

        # Save report
        report_file = self.reports_dir / f"adoption_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Feature adoption analytics report generated: {report_file}")
        return report

    def simulate_usage_data(self, days: int = 30, users_per_day: int = 10):
        """Simulate realistic usage data for testing (development/demo purposes)."""

        logger.info(f"Simulating {days} days of usage data with ~{users_per_day} users per day...")

        import random

        # User skill level distribution
        skill_levels = ["beginner", "intermediate", "expert"]
        skill_weights = [0.3, 0.5, 0.2]

        # Scenario popularity (based on UAT success rates)
        scenario_weights = {
            "fcf_analysis": 0.25,
            "dcf_valuation": 0.20,
            "pb_analysis": 0.18,
            "ddm_analysis": 0.15,
            "watchlist_management": 0.12,
            "portfolio_analysis": 0.10
        }

        for day in range(days):
            date = datetime.now() - timedelta(days=days-day)

            # Generate users for this day
            daily_users = random.randint(max(1, users_per_day-5), users_per_day+5)

            for user_num in range(daily_users):
                user_session = f"user_{date.strftime('%Y%m%d')}_{user_num:03d}"
                user_skill = random.choices(skill_levels, weights=skill_weights)[0]

                # Choose scenarios for this user (some users do multiple scenarios)
                num_scenarios = random.choices([1, 2, 3], weights=[0.6, 0.3, 0.1])[0]
                chosen_scenarios = random.choices(
                    list(scenario_weights.keys()),
                    weights=list(scenario_weights.values()),
                    k=num_scenarios
                )

                # Simulate feature usage within each scenario
                for scenario in chosen_scenarios:
                    scenario_features = self.scenario_features[scenario]["features"]

                    # User journey completion based on skill level
                    if user_skill == "expert":
                        features_to_use = random.sample(scenario_features,
                                                      random.randint(len(scenario_features)-1, len(scenario_features)))
                    elif user_skill == "intermediate":
                        features_to_use = random.sample(scenario_features,
                                                      random.randint(max(1, len(scenario_features)//2), len(scenario_features)-1))
                    else:  # beginner
                        features_to_use = random.sample(scenario_features,
                                                      random.randint(1, max(1, len(scenario_features)//2)))

                    # Simulate feature usage
                    session_start_time = date + timedelta(
                        hours=random.randint(8, 20),
                        minutes=random.randint(0, 59)
                    )

                    for i, feature in enumerate(features_to_use):
                        # Simulate time between features
                        feature_time = session_start_time + timedelta(minutes=i * random.randint(2, 10))

                        # Simulate feature duration (varies by complexity)
                        base_duration = {
                            "data_import_excel": 30,
                            "financial_data_validation": 15,
                            "fcf_calculation": 45,
                            "dcf_model_execution": 60,
                            "portfolio_optimization": 90,
                            "watchlist_add_remove": 10
                        }.get(feature, 30)

                        # Adjust duration by skill level
                        skill_multiplier = {"expert": 0.7, "intermediate": 1.0, "beginner": 1.5}[user_skill]
                        duration = base_duration * skill_multiplier * random.uniform(0.5, 2.0)

                        # Success rate varies by skill and feature complexity
                        base_success_rate = 0.95
                        if user_skill == "beginner":
                            base_success_rate = 0.85
                        elif user_skill == "intermediate":
                            base_success_rate = 0.92

                        success = random.random() < base_success_rate

                        # Create usage event with backdated timestamp
                        event = FeatureUsageEvent(
                            event_id=f"{feature}_{user_session}_{int(feature_time.timestamp())}",
                            feature_name=feature,
                            scenario_category=scenario,
                            user_session=user_session,
                            timestamp=feature_time,
                            duration=duration,
                            success=success,
                            interaction_count=random.randint(1, 5),
                            user_skill_level=user_skill,
                            context_data={"simulated": True, "day": day}
                        )

                        self._store_usage_event(event)

        logger.info(f"Simulation complete: generated usage data for {days} days")


if __name__ == "__main__":
    analytics = FeatureAdoptionAnalytics()

    # Simulate some usage data for testing
    analytics.simulate_usage_data(days=30, users_per_day=15)

    # Generate comprehensive report
    report = analytics.generate_comprehensive_adoption_report(days=30)
    print(f"Generated adoption analytics report: {report['report_id']}")
    print(f"Scenarios analyzed: {report['overall_analytics']['scenarios_analyzed']}")
    print(f"Average adoption rate: {report['overall_analytics']['average_adoption_rate']:.1f}%")