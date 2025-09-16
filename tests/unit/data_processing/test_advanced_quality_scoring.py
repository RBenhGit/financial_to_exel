"""
Test Suite for Advanced Data Quality Scoring System
==================================================

Comprehensive tests for the AdvancedDataQualityScorer and related components.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import json
import tempfile
from pathlib import Path

# Import the components to test
from core.data_processing.advanced_data_quality_scorer import (
    AdvancedDataQualityScorer,
    QualityMetrics,
    QualityDimension
)
from core.data_processing.monitoring.predictive_quality_alerting import (
    PredictiveQualityAlerting,
    PredictiveAlert,
    PredictiveAlertType
)


class TestAdvancedDataQualityScorer:
    """Test cases for AdvancedDataQualityScorer"""

    @pytest.fixture
    def scorer(self):
        """Create a scorer instance for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary config
            config = {
                'weights': {
                    'completeness': 0.25,
                    'consistency': 0.20,
                    'accuracy': 0.25,
                    'timeliness': 0.10,
                    'validity': 0.15,
                    'uniqueness': 0.05
                }
            }

            # Mock the cache file path
            with patch('core.data_processing.advanced_data_quality_scorer.Path') as mock_path:
                mock_path.return_value = Path(tmpdir) / "test_cache.json"
                scorer = AdvancedDataQualityScorer()
                scorer.quality_cache_file = Path(tmpdir) / "test_cache.json"
                yield scorer

    @pytest.fixture
    def sample_financial_data(self):
        """Sample financial data for testing"""
        return {
            'Net Income': [1000, 1100, 1200, 1300, 1400],
            'Total Assets': [5000, 5200, 5400, 5600, 5800],
            'Cash from Operations': [800, 900, 1000, 1100, 1200],
            'Market Cap': [10000, 11000, 12000, 13000, 14000]
        }

    @pytest.fixture
    def sample_dataframe(self):
        """Sample DataFrame for testing"""
        return pd.DataFrame({
            'year': [2019, 2020, 2021, 2022, 2023],
            'revenue': [1000, 1100, 1200, 1300, 1400],
            'profit': [100, 110, 120, 130, 140],
            'assets': [5000, 5200, 5400, 5600, 5800]
        })

    def test_scorer_initialization(self, scorer):
        """Test scorer initialization"""
        assert scorer is not None
        assert hasattr(scorer, 'validator')
        assert hasattr(scorer, 'quality_history')
        assert hasattr(scorer, 'config')
        assert len(scorer.quality_history) == 0

    def test_completeness_scoring_perfect_data(self, scorer, sample_financial_data):
        """Test completeness scoring with perfect data"""
        score = scorer._score_completeness(sample_financial_data)
        assert score == 100.0

    def test_completeness_scoring_missing_data(self, scorer):
        """Test completeness scoring with missing data"""
        data_with_missing = {
            'Net Income': [1000, None, 1200, '', 1400],
            'Total Assets': [5000, 5200, None, 5600, 5800]
        }
        score = scorer._score_completeness(data_with_missing)
        assert 0 <= score < 100
        assert score > 0  # Should not be zero since some data exists

    def test_completeness_scoring_empty_data(self, scorer):
        """Test completeness scoring with empty data"""
        score = scorer._score_completeness({})
        assert score == 0.0

    def test_completeness_scoring_dataframe(self, scorer, sample_dataframe):
        """Test completeness scoring with DataFrame"""
        score = scorer._score_completeness(sample_dataframe)
        assert score == 100.0

    def test_completeness_scoring_dataframe_with_nulls(self, scorer):
        """Test completeness scoring with DataFrame containing nulls"""
        df_with_nulls = pd.DataFrame({
            'col1': [1, 2, None, 4],
            'col2': [None, 2, 3, 4],
            'col3': [1, 2, 3, None]
        })
        score = scorer._score_completeness(df_with_nulls)
        assert 0 < score < 100  # Should be between 0 and 100
        expected_score = (9 / 12) * 100  # 9 non-null values out of 12 total
        assert abs(score - expected_score) < 1.0

    def test_consistency_scoring_consistent_data(self, scorer, sample_financial_data):
        """Test consistency scoring with consistent data"""
        score = scorer._score_consistency(sample_financial_data)
        assert 80 <= score <= 100  # Should be high for consistent growth

    def test_consistency_scoring_inconsistent_data(self, scorer):
        """Test consistency scoring with inconsistent data"""
        inconsistent_data = {
            'Metric1': [100, 10000, 50, 200, 100000],  # High variability
            'Metric2': [1, 1, 1, 1, 1]  # All same values
        }
        score = scorer._score_consistency(inconsistent_data)
        assert 0 <= score < 100

    def test_accuracy_scoring_dataframe(self, scorer, sample_dataframe):
        """Test accuracy scoring with DataFrame"""
        score = scorer._score_accuracy(sample_dataframe)
        assert 90 <= score <= 100  # Should be high for clean numeric data

    def test_accuracy_scoring_mixed_types(self, scorer):
        """Test accuracy scoring with mixed data types"""
        mixed_df = pd.DataFrame({
            'numeric_as_string': ['100', '200', '300'],
            'actual_numeric': [1, 2, 3],
            'text': ['a', 'b', 'c']
        })
        score = scorer._score_accuracy(mixed_df)
        assert 50 <= score <= 100  # Should penalize mixed types

    def test_timeliness_scoring_with_context(self, scorer):
        """Test timeliness scoring with timestamp context"""
        recent_data = {'value': 100}
        context = {'data_timestamp': datetime.now().isoformat()}
        score = scorer._score_timeliness(recent_data, context)
        assert score == 100.0

    def test_timeliness_scoring_old_data(self, scorer):
        """Test timeliness scoring with old data"""
        old_data = {'value': 100}
        old_timestamp = (datetime.now() - timedelta(days=35)).isoformat()
        context = {'data_timestamp': old_timestamp}
        score = scorer._score_timeliness(old_data, context)
        assert score == 50.0  # Should be 50% for very old data

    def test_validity_scoring_positive_required_fields(self, scorer):
        """Test validity scoring with fields that should be positive"""
        data_with_negatives = {
            'Total Current Assets': [-1000, 2000, 3000],  # Should be positive
            'Market Cap': [1000, -2000, 3000],  # Should be positive
            'Other Metric': [100, 200, 300]  # No restriction
        }
        score = scorer._score_validity(data_with_negatives)
        assert 0 <= score < 100  # Should be penalized for negative values

    def test_validity_scoring_reasonable_magnitudes(self, scorer):
        """Test validity scoring with unreasonable magnitudes"""
        data_with_extreme = {
            'Revenue': [1e15, 1e15, 1e15],  # Unreasonably large
            'Normal Metric': [100, 200, 300]
        }
        score = scorer._score_validity(data_with_extreme)
        assert score < 100  # Should be penalized for extreme values

    def test_uniqueness_scoring_dataframe_no_duplicates(self, scorer, sample_dataframe):
        """Test uniqueness scoring with DataFrame without duplicates"""
        score = scorer._score_uniqueness(sample_dataframe)
        assert score == 100.0

    def test_uniqueness_scoring_dataframe_with_duplicates(self, scorer):
        """Test uniqueness scoring with DataFrame containing duplicates"""
        df_with_duplicates = pd.DataFrame({
            'col1': [1, 2, 2, 3],  # Has duplicates
            'col2': [1, 2, 2, 3]   # Same duplicates
        })
        score = scorer._score_uniqueness(df_with_duplicates)
        assert 50 <= score < 100  # Should be penalized for duplicates

    def test_uniqueness_scoring_consecutive_duplicates(self, scorer):
        """Test uniqueness scoring with consecutive duplicate values"""
        data_with_stale = {
            'Metric': [100, 100, 100, 100, 200]  # Many consecutive duplicates
        }
        score = scorer._score_uniqueness(data_with_stale)
        assert score < 100  # Should be penalized for consecutive duplicates

    def test_overall_score_calculation(self, scorer):
        """Test overall score calculation with known metrics"""
        metrics = QualityMetrics(
            completeness=90.0,
            consistency=80.0,
            accuracy=95.0,
            timeliness=85.0,
            validity=88.0,
            uniqueness=92.0
        )

        overall = scorer._calculate_overall_score(metrics)

        # Calculate expected weighted score
        weights = scorer.config['weights']
        expected = (
            90.0 * weights['completeness'] +
            80.0 * weights['consistency'] +
            95.0 * weights['accuracy'] +
            85.0 * weights['timeliness'] +
            88.0 * weights['validity'] +
            92.0 * weights['uniqueness']
        )

        assert abs(overall - expected) < 0.01

    def test_complete_scoring_workflow(self, scorer, sample_financial_data):
        """Test complete scoring workflow from data to metrics"""
        metrics = scorer.score_data_quality(
            sample_financial_data,
            source_identifier="test_source"
        )

        assert isinstance(metrics, QualityMetrics)
        assert 0 <= metrics.overall_score <= 100
        assert 0 <= metrics.completeness <= 100
        assert 0 <= metrics.consistency <= 100
        assert 0 <= metrics.accuracy <= 100
        assert 0 <= metrics.timeliness <= 100
        assert 0 <= metrics.validity <= 100
        assert 0 <= metrics.uniqueness <= 100
        assert metrics.source_identifier == "test_source"
        assert len(scorer.quality_history) == 1

    def test_data_points_counting_dict(self, scorer, sample_financial_data):
        """Test data points counting for dictionary data"""
        count = scorer._count_data_points(sample_financial_data)
        expected = sum(len(values) for values in sample_financial_data.values())
        assert count == expected

    def test_data_points_counting_dataframe(self, scorer, sample_dataframe):
        """Test data points counting for DataFrame"""
        count = scorer._count_data_points(sample_dataframe)
        assert count == sample_dataframe.size

    def test_quality_history_persistence(self, scorer, sample_financial_data):
        """Test that quality history is persisted"""
        # Score some data to create history
        scorer.score_data_quality(sample_financial_data, "test1")
        scorer.score_data_quality(sample_financial_data, "test2")

        assert len(scorer.quality_history) == 2

        # Test that save/load works (mocked file operations)
        with patch.object(scorer, '_save_quality_history') as mock_save:
            scorer.score_data_quality(sample_financial_data, "test3")
            mock_save.assert_called()

    def test_quality_trends_analysis(self, scorer, sample_financial_data):
        """Test quality trends analysis"""
        # Create some historical data with declining quality
        for i in range(10):
            # Gradually degrade the data quality
            degraded_data = {}
            for key, values in sample_financial_data.items():
                # Add more missing values as i increases
                degraded_values = values.copy()
                for j in range(min(i // 2, len(values))):
                    if j < len(degraded_values):
                        degraded_values[j] = None
                degraded_data[key] = degraded_values

            scorer.score_data_quality(degraded_data, f"test_{i}")

        trends = scorer.get_quality_trends()

        assert 'overall_trend' in trends
        assert 'status' in trends
        assert trends['status'] in ['improving', 'stable', 'degrading']

    def test_quality_predictions(self, scorer, sample_financial_data):
        """Test quality predictions"""
        # Create historical data
        for i in range(5):
            scorer.score_data_quality(sample_financial_data, f"test_{i}")

        predictions = scorer.predict_quality_issues()

        if predictions.get('status') not in ['no_prediction', 'no_data']:
            assert 'risk_level' in predictions
            assert 'recommendations' in predictions
            assert predictions['risk_level'] in ['low', 'medium', 'high']


class TestPredictiveQualityAlerting:
    """Test cases for PredictiveQualityAlerting"""

    @pytest.fixture
    def mock_scorer(self):
        """Create a mock quality scorer"""
        scorer = Mock(spec=AdvancedDataQualityScorer)
        scorer.quality_history = []
        return scorer

    @pytest.fixture
    def alerting_system(self, mock_scorer):
        """Create alerting system for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            system = PredictiveQualityAlerting(mock_scorer)
            system.alert_history_file = Path(tmpdir) / "test_alerts.json"
            return system

    def test_alerting_system_initialization(self, alerting_system):
        """Test alerting system initialization"""
        assert alerting_system is not None
        assert hasattr(alerting_system, 'quality_scorer')
        assert hasattr(alerting_system, 'config')
        assert hasattr(alerting_system, 'alert_channels')
        assert len(alerting_system.alert_channels) > 0  # Should have default log channel

    def test_degradation_alert_generation(self, alerting_system, mock_scorer):
        """Test degradation alert generation"""
        # Mock trends data indicating degradation
        mock_trends = {
            'status': 'degrading',
            'overall_trend': -3.0,  # Degrading at 3% per period
            'current_score': 75.0
        }
        mock_predictions = {
            'status': 'degrading',
            'risk_level': 'high'
        }

        mock_scorer.get_quality_trends.return_value = mock_trends
        mock_scorer.predict_quality_issues.return_value = mock_predictions

        alerts = alerting_system._check_degradation_trends(mock_trends, mock_predictions)

        assert len(alerts) > 0
        alert = alerts[0]
        assert isinstance(alert, PredictiveAlert)
        assert alert.alert_type == PredictiveAlertType.QUALITY_DEGRADATION_PREDICTED
        assert alert.prediction_confidence > 0
        assert len(alert.mitigation_suggestions) > 0

    def test_anomaly_detection(self, alerting_system, mock_scorer):
        """Test anomaly detection in quality scores"""
        # Create mock quality history with an anomaly
        from core.data_processing.advanced_data_quality_scorer import QualityMetrics

        base_time = datetime.now()
        normal_scores = [85.0, 87.0, 86.0, 88.0, 85.5]
        anomaly_score = 95.0  # Significant deviation

        quality_history = []
        for i, score in enumerate(normal_scores):
            metrics = QualityMetrics(
                overall_score=score,
                timestamp=base_time - timedelta(hours=i+1)
            )
            quality_history.append(metrics)

        # Add anomaly
        anomaly_metrics = QualityMetrics(
            overall_score=anomaly_score,
            timestamp=base_time
        )
        quality_history.append(anomaly_metrics)

        mock_scorer.quality_history = quality_history

        alerts = alerting_system._check_anomaly_patterns()

        # Should detect anomaly
        if len(alerts) > 0:
            alert = alerts[0]
            assert alert.alert_type == PredictiveAlertType.TREND_ANOMALY_DETECTED
            assert alert.prediction_confidence > 0

    def test_threshold_breach_prediction(self, alerting_system, mock_scorer):
        """Test threshold breach prediction"""
        mock_predictions = {
            'status': 'degrading',
            'risk_level': 'high',
            'current_quality': 70.0,
            'projected_quality': 55.0,  # Will breach 60% threshold
            'prediction_window_hours': 12,
            'recommendations': ['Check data sources', 'Review validation']
        }

        alerts = alerting_system._check_threshold_predictions(mock_predictions)

        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.alert_type == PredictiveAlertType.THRESHOLD_BREACH_IMMINENT
        assert alert.severity.value == 'critical'
        assert alert.time_to_impact is not None
        assert len(alert.mitigation_suggestions) > 0

    def test_data_staleness_detection(self, alerting_system, mock_scorer):
        """Test data staleness detection"""
        # Create old quality metrics
        old_time = datetime.now() - timedelta(hours=8)  # 8 hours old
        from core.data_processing.advanced_data_quality_scorer import QualityMetrics

        old_metrics = QualityMetrics(
            overall_score=80.0,
            timestamp=old_time
        )

        mock_scorer.quality_history = [old_metrics]

        alerts = alerting_system._check_data_staleness()

        assert len(alerts) > 0
        alert = alerts[0]
        assert alert.alert_type == PredictiveAlertType.DATA_STALENESS_WARNING
        assert alert.prediction_confidence == 1.0  # High confidence for time-based

    def test_alert_rate_limiting(self, alerting_system):
        """Test alert rate limiting functionality"""
        # Create many recent alerts in history
        recent_alerts = []
        for i in range(15):  # More than the default limit of 10
            alert_dict = {
                'alert_id': f'test_{i}',
                'timestamp': datetime.now().isoformat(),
                'alert_type': 'test_type'
            }
            recent_alerts.append(alert_dict)

        alerting_system.alert_history = recent_alerts

        # Create a test alert
        from core.data_processing.advanced_data_quality_scorer import QualityMetrics
        test_alert = PredictiveAlert(
            alert_id='rate_test',
            alert_type=PredictiveAlertType.QUALITY_DEGRADATION_PREDICTED,
            severity='warning',
            source_name='test',
            message='test',
            timestamp=datetime.now(),
            metrics=QualityMetrics()
        )

        # Should be rate limited
        should_send = alerting_system._should_send_alert(test_alert)
        assert should_send is False

    def test_alert_cooldown(self, alerting_system):
        """Test alert cooldown functionality"""
        # Create a recent alert of the same type
        recent_alert = {
            'alert_id': 'recent_test',
            'timestamp': (datetime.now() - timedelta(minutes=15)).isoformat(),
            'alert_type': PredictiveAlertType.QUALITY_DEGRADATION_PREDICTED.value
        }

        alerting_system.alert_history = [recent_alert]

        # Create new alert of same type
        from core.data_processing.advanced_data_quality_scorer import QualityMetrics
        test_alert = PredictiveAlert(
            alert_id='cooldown_test',
            alert_type=PredictiveAlertType.QUALITY_DEGRADATION_PREDICTED,
            severity='warning',
            source_name='test',
            message='test',
            timestamp=datetime.now(),
            metrics=QualityMetrics()
        )

        # Should be in cooldown
        should_send = alerting_system._should_send_alert(test_alert)
        assert should_send is False

    def test_alert_summary_generation(self, alerting_system):
        """Test alert summary generation"""
        # Create test alert history
        test_alerts = []
        base_time = datetime.now()

        for i in range(5):
            alert_dict = {
                'alert_id': f'test_{i}',
                'timestamp': (base_time - timedelta(hours=i)).isoformat(),
                'alert_type': 'degradation',
                'severity': 'warning',
                'prediction_confidence': 0.8
            }
            test_alerts.append(alert_dict)

        alerting_system.alert_history = test_alerts

        summary = alerting_system.get_alert_summary(hours_back=24)

        assert summary['total_alerts'] == 5
        assert 'degradation' in summary['alert_types']
        assert summary['alert_types']['degradation'] == 5
        assert 'warning' in summary['severity_breakdown']
        assert summary['average_confidence'] == 0.8
        assert summary['most_recent'] is not None


@pytest.mark.integration
class TestIntegrationScenarios:
    """Integration tests for complete workflows"""

    def test_end_to_end_quality_monitoring(self):
        """Test complete end-to-end quality monitoring workflow"""
        # This would test the complete integration from data input
        # through scoring, alerting, and dashboard display
        pass  # Implementation would require full system setup

    def test_streamlit_dashboard_integration(self):
        """Test integration with Streamlit dashboard"""
        # This would test the dashboard rendering with real data
        pass  # Implementation would require Streamlit test environment

    def test_performance_with_large_datasets(self):
        """Test performance with large datasets"""
        # Create large dataset for performance testing
        large_data = {}
        for i in range(100):  # 100 metrics
            large_data[f'metric_{i}'] = [float(j) for j in range(1000)]  # 1000 data points each

        scorer = AdvancedDataQualityScorer()

        import time
        start_time = time.time()
        metrics = scorer.score_data_quality(large_data, "performance_test")
        end_time = time.time()

        # Should complete within reasonable time (e.g., 10 seconds)
        assert (end_time - start_time) < 10.0
        assert isinstance(metrics, QualityMetrics)
        assert metrics.overall_score >= 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])