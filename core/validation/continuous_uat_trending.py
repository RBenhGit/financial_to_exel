"""
Continuous UAT Results Trending System

This module provides continuous trending and analysis of UAT results,
building on the successful 88.9% UAT achievement to maintain and improve
test success rates over time.
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
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Import logging utilities
try:
    from utils.logging_config import get_streamlit_logger
    logger = get_streamlit_logger()
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


@dataclass
class UATTrendPoint:
    """Single data point in UAT trending analysis."""
    timestamp: datetime
    success_rate: float
    total_tests: int
    passed_tests: int
    failed_tests: int
    avg_duration: float
    test_details: Dict[str, Any]
    environment: str = "production"
    version: str = "current"


@dataclass
class TrendingAnalysis:
    """Analysis results from UAT trending data."""
    current_success_rate: float
    trend_direction: str  # "improving", "stable", "declining"
    trend_magnitude: float
    risk_level: str  # "low", "medium", "high"
    recommendations: List[str]
    forecast_7days: float
    forecast_30days: float


class ContinuousUATTrending:
    """
    Continuous UAT results trending system that monitors and analyzes
    test success rates over time, building on the 88.9% baseline achievement.
    """

    def __init__(self, project_root: Optional[str] = None):
        """Initialize the continuous UAT trending system."""
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.uat_reports_dir = self.project_root / "reports" / "user_acceptance"
        self.trending_db_path = self.project_root / "data" / "uat_trending.db"

        # Ensure directories exist
        self.uat_reports_dir.mkdir(parents=True, exist_ok=True)
        self.trending_db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._init_database()

        # Load baseline (88.9% success rate achievement)
        self.baseline_success_rate = 88.9
        self.target_success_rate = 95.0  # Aspirational target

    def _init_database(self):
        """Initialize SQLite database for trending data storage."""

        with sqlite3.connect(self.trending_db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS uat_trending (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    success_rate REAL NOT NULL,
                    total_tests INTEGER NOT NULL,
                    passed_tests INTEGER NOT NULL,
                    failed_tests INTEGER NOT NULL,
                    avg_duration REAL NOT NULL,
                    test_details TEXT NOT NULL,
                    environment TEXT DEFAULT 'production',
                    version TEXT DEFAULT 'current',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON uat_trending(timestamp)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_success_rate
                ON uat_trending(success_rate)
            ''')

    def collect_uat_results(self) -> Optional[UATTrendPoint]:
        """Collect the latest UAT results from reports directory."""

        if not self.uat_reports_dir.exists():
            logger.warning("UAT reports directory not found")
            return None

        # Find latest test results file
        json_files = list(self.uat_reports_dir.glob("test_results_*.json"))
        if not json_files:
            logger.warning("No UAT result files found")
            return None

        latest_file = max(json_files, key=lambda f: f.stat().st_mtime)

        try:
            with open(latest_file, 'r') as f:
                results = json.load(f)

            # Calculate metrics
            total_tests = len(results)
            passed_tests = sum(1 for r in results if r.get('status') == 'PASS')
            failed_tests = total_tests - passed_tests
            success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

            # Calculate average duration
            durations = [r.get('duration', 0) for r in results if r.get('duration')]
            avg_duration = sum(durations) / len(durations) if durations else 0

            # Extract timestamp from filename or use file modification time
            timestamp_str = latest_file.stem.replace('test_results_', '')
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
            except ValueError:
                timestamp = datetime.fromtimestamp(latest_file.stat().st_mtime)

            return UATTrendPoint(
                timestamp=timestamp,
                success_rate=success_rate,
                total_tests=total_tests,
                passed_tests=passed_tests,
                failed_tests=failed_tests,
                avg_duration=avg_duration,
                test_details={"raw_results": results},
                environment="production",
                version="current"
            )

        except Exception as e:
            logger.error(f"Error processing UAT results from {latest_file}: {e}")
            return None

    def store_trend_point(self, trend_point: UATTrendPoint):
        """Store a UAT trend point in the database."""

        with sqlite3.connect(self.trending_db_path) as conn:
            # Check if this timestamp already exists
            existing = conn.execute(
                "SELECT id FROM uat_trending WHERE timestamp = ?",
                (trend_point.timestamp.isoformat(),)
            ).fetchone()

            if existing:
                # Update existing record
                conn.execute('''
                    UPDATE uat_trending
                    SET success_rate = ?, total_tests = ?, passed_tests = ?,
                        failed_tests = ?, avg_duration = ?, test_details = ?,
                        environment = ?, version = ?
                    WHERE timestamp = ?
                ''', (
                    trend_point.success_rate,
                    trend_point.total_tests,
                    trend_point.passed_tests,
                    trend_point.failed_tests,
                    trend_point.avg_duration,
                    json.dumps(trend_point.test_details),
                    trend_point.environment,
                    trend_point.version,
                    trend_point.timestamp.isoformat()
                ))
                logger.info(f"Updated UAT trend point for {trend_point.timestamp}")
            else:
                # Insert new record
                conn.execute('''
                    INSERT INTO uat_trending
                    (timestamp, success_rate, total_tests, passed_tests,
                     failed_tests, avg_duration, test_details, environment, version)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trend_point.timestamp.isoformat(),
                    trend_point.success_rate,
                    trend_point.total_tests,
                    trend_point.passed_tests,
                    trend_point.failed_tests,
                    trend_point.avg_duration,
                    json.dumps(trend_point.test_details),
                    trend_point.environment,
                    trend_point.version
                ))
                logger.info(f"Stored new UAT trend point for {trend_point.timestamp}")

    def get_trending_data(self, days: int = 30) -> pd.DataFrame:
        """Retrieve trending data from the database."""

        cutoff_date = datetime.now() - timedelta(days=days)

        with sqlite3.connect(self.trending_db_path) as conn:
            query = '''
                SELECT timestamp, success_rate, total_tests, passed_tests,
                       failed_tests, avg_duration, environment, version
                FROM uat_trending
                WHERE timestamp >= ?
                ORDER BY timestamp
            '''

            df = pd.read_sql_query(query, conn, params=(cutoff_date.isoformat(),))

            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp')

            return df

    def analyze_trends(self, days: int = 30) -> TrendingAnalysis:
        """Analyze UAT success rate trends and provide insights."""

        df = self.get_trending_data(days)

        if df.empty:
            return TrendingAnalysis(
                current_success_rate=self.baseline_success_rate,
                trend_direction="stable",
                trend_magnitude=0.0,
                risk_level="medium",
                recommendations=["No trend data available - collect more UAT results"],
                forecast_7days=self.baseline_success_rate,
                forecast_30days=self.baseline_success_rate
            )

        current_success_rate = df['success_rate'].iloc[-1]

        # Calculate trend direction and magnitude
        if len(df) >= 2:
            # Use linear regression for trend analysis
            df_numeric = df.copy()
            df_numeric['days_ago'] = (df_numeric['timestamp'].max() - df_numeric['timestamp']).dt.days

            # Simple trend calculation
            first_half_avg = df[:len(df)//2]['success_rate'].mean()
            second_half_avg = df[len(df)//2:]['success_rate'].mean()
            trend_magnitude = second_half_avg - first_half_avg

            if abs(trend_magnitude) < 1.0:
                trend_direction = "stable"
            elif trend_magnitude > 0:
                trend_direction = "improving"
            else:
                trend_direction = "declining"
        else:
            trend_magnitude = 0.0
            trend_direction = "stable"

        # Determine risk level
        if current_success_rate >= self.target_success_rate:
            risk_level = "low"
        elif current_success_rate >= self.baseline_success_rate:
            risk_level = "medium"
        else:
            risk_level = "high"

        # Generate recommendations
        recommendations = []

        if trend_direction == "declining":
            recommendations.append("⚠️ Declining UAT success rate - investigate failing test patterns")
            recommendations.append("Review recent code changes for impact on test stability")

        if current_success_rate < self.baseline_success_rate:
            recommendations.append(f"🚨 Below baseline ({self.baseline_success_rate}%) - immediate attention needed")

        if current_success_rate < 90.0:
            recommendations.append("Focus on improving most frequently failing test scenarios")

        if trend_direction == "improving":
            recommendations.append("✅ Positive trend - maintain current development practices")

        if not recommendations:
            recommendations.append("💯 UAT success rate is healthy - continue monitoring")

        # Simple forecasting (linear projection)
        if len(df) >= 3:
            recent_trend = (df['success_rate'].iloc[-1] - df['success_rate'].iloc[-3]) / 2
            forecast_7days = min(100, max(0, current_success_rate + (recent_trend * 3.5)))
            forecast_30days = min(100, max(0, current_success_rate + (recent_trend * 15)))
        else:
            forecast_7days = current_success_rate
            forecast_30days = current_success_rate

        return TrendingAnalysis(
            current_success_rate=current_success_rate,
            trend_direction=trend_direction,
            trend_magnitude=trend_magnitude,
            risk_level=risk_level,
            recommendations=recommendations,
            forecast_7days=forecast_7days,
            forecast_30days=forecast_30days
        )

    def create_trending_visualizations(self, days: int = 30) -> Dict[str, Any]:
        """Create comprehensive trending visualizations."""

        df = self.get_trending_data(days)
        analysis = self.analyze_trends(days)
        visualizations = {}

        if df.empty:
            # Create placeholder visualization
            fig = go.Figure()
            fig.add_annotation(
                text="No trending data available<br>Run UAT tests to populate trends",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font_size=16
            )
            fig.update_layout(title="UAT Success Rate Trending")
            visualizations["main_trend"] = fig
            return visualizations

        # 1. Main trending chart
        fig_main = go.Figure()

        # Add actual data
        fig_main.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['success_rate'],
            mode='lines+markers',
            name='UAT Success Rate',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))

        # Add baseline reference
        fig_main.add_hline(
            y=self.baseline_success_rate,
            line_dash="dash",
            line_color="green",
            annotation_text=f"Baseline: {self.baseline_success_rate}%"
        )

        # Add target reference
        fig_main.add_hline(
            y=self.target_success_rate,
            line_dash="dot",
            line_color="orange",
            annotation_text=f"Target: {self.target_success_rate}%"
        )

        # Add forecast
        if len(df) >= 2:
            future_dates = pd.date_range(
                start=df['timestamp'].max() + timedelta(days=1),
                periods=7,
                freq='D'
            )

            forecast_values = [analysis.forecast_7days] * len(future_dates)

            fig_main.add_trace(go.Scatter(
                x=future_dates,
                y=forecast_values,
                mode='lines',
                name='7-day Forecast',
                line=dict(color='red', dash='dot', width=2),
                opacity=0.7
            ))

        fig_main.update_layout(
            title=f"UAT Success Rate Trending ({days} days)",
            xaxis_title="Date",
            yaxis_title="Success Rate (%)",
            yaxis=dict(range=[0, 100]),
            hovermode='x unified'
        )
        visualizations["main_trend"] = fig_main

        # 2. Test volume trending
        fig_volume = go.Figure()

        fig_volume.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['passed_tests'],
            name='Passed Tests',
            marker_color='green'
        ))

        fig_volume.add_trace(go.Bar(
            x=df['timestamp'],
            y=df['failed_tests'],
            name='Failed Tests',
            marker_color='red'
        ))

        fig_volume.update_layout(
            title="Test Volume Trending",
            xaxis_title="Date",
            yaxis_title="Number of Tests",
            barmode='stack'
        )
        visualizations["volume_trend"] = fig_volume

        # 3. Performance trending (average duration)
        fig_perf = px.line(
            df,
            x='timestamp',
            y='avg_duration',
            title="Test Duration Trending",
            labels={'avg_duration': 'Average Duration (s)', 'timestamp': 'Date'}
        )
        visualizations["performance_trend"] = fig_perf

        # 4. Trend analysis summary
        colors = {"low": "green", "medium": "orange", "high": "red"}

        fig_summary = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=analysis.current_success_rate,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': f"Current Success Rate<br>Risk Level: {analysis.risk_level.title()}"},
            delta={'reference': self.baseline_success_rate},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': colors[analysis.risk_level]},
                'steps': [
                    {'range': [0, 80], 'color': "lightgray"},
                    {'range': [80, 90], 'color': "yellow"},
                    {'range': [90, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': self.baseline_success_rate
                }
            }
        ))
        visualizations["summary_gauge"] = fig_summary

        return visualizations

    def update_trending_data(self):
        """Update trending database with latest UAT results."""

        logger.info("Updating UAT trending data...")

        trend_point = self.collect_uat_results()
        if trend_point:
            self.store_trend_point(trend_point)
            logger.info(f"UAT trending updated: {trend_point.success_rate:.1f}% success rate")
            return trend_point
        else:
            logger.warning("No new UAT results found to update trending")
            return None

    def generate_trending_report(self, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive trending report."""

        analysis = self.analyze_trends(days)
        df = self.get_trending_data(days)

        report = {
            "report_id": f"UAT_TREND_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "period_days": days,
            "baseline_success_rate": self.baseline_success_rate,
            "target_success_rate": self.target_success_rate,
            "analysis": asdict(analysis),
            "data_points": len(df),
            "date_range": {
                "start": df['timestamp'].min().isoformat() if not df.empty else None,
                "end": df['timestamp'].max().isoformat() if not df.empty else None
            },
            "summary_statistics": {
                "mean_success_rate": df['success_rate'].mean() if not df.empty else None,
                "std_success_rate": df['success_rate'].std() if not df.empty else None,
                "min_success_rate": df['success_rate'].min() if not df.empty else None,
                "max_success_rate": df['success_rate'].max() if not df.empty else None
            }
        }

        # Save report
        reports_dir = self.project_root / "reports" / "uat_trending"
        reports_dir.mkdir(parents=True, exist_ok=True)

        report_file = reports_dir / f"uat_trending_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"UAT trending report generated: {report_file}")
        return report


if __name__ == "__main__":
    trending_system = ContinuousUATTrending()

    # Update with latest results
    trending_system.update_trending_data()

    # Generate analysis
    analysis = trending_system.analyze_trends()
    print(f"Current Success Rate: {analysis.current_success_rate:.1f}%")
    print(f"Trend Direction: {analysis.trend_direction}")
    print(f"Risk Level: {analysis.risk_level}")
    print("Recommendations:")
    for rec in analysis.recommendations:
        print(f"  - {rec}")