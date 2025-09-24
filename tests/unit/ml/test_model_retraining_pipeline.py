"""
Unit tests for ModelRetrainingPipeline.

Tests automated retraining, performance monitoring, and drift detection.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, mock_open
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

from core.analysis.ml.automation.model_retraining_pipeline import ModelRetrainingPipeline


class TestModelRetrainingPipeline:
    """Unit tests for ModelRetrainingPipeline class."""

    @pytest.fixture
    def temp_model_storage(self):
        """Create temporary model storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.fixture
    def sample_data(self):
        """Create sample training data."""
        np.random.seed(42)
        return pd.DataFrame({
            'feature1': np.random.randn(100),
            'feature2': np.random.randn(100),
            'feature3': np.random.randn(100),
            'target': np.random.randn(100)
        })

    @pytest.fixture
    def trained_model(self, sample_data):
        """Create a trained model for testing."""
        X = sample_data[['feature1', 'feature2', 'feature3']]
        y = sample_data['target']

        model = LinearRegression()
        model.fit(X, y)
        return model

    @pytest.fixture
    def pipeline(self, temp_model_storage):
        """Create ModelRetrainingPipeline with temporary storage."""
        return ModelRetrainingPipeline(
            model_storage_path=temp_model_storage,
            performance_threshold=0.8,
            drift_threshold=0.1
        )

    def test_initialization(self, temp_model_storage):
        """Test ModelRetrainingPipeline initialization."""
        pipeline = ModelRetrainingPipeline(
            model_storage_path=temp_model_storage,
            performance_threshold=0.85,
            drift_threshold=0.15,
            max_retrain_interval_days=14
        )

        assert pipeline.model_storage_path == temp_model_storage
        assert pipeline.performance_threshold == 0.85
        assert pipeline.drift_threshold == 0.15
        assert pipeline.max_retrain_interval_days == 14
        assert pipeline.models == {}
        assert pipeline.performance_history == {}
        assert pipeline.last_training_dates == {}

    def test_initialize_model(self, pipeline, trained_model):
        """Test model initialization."""
        ticker = "TEST"

        pipeline.initialize_model(ticker, trained_model)

        assert ticker in pipeline.models
        assert pipeline.models[ticker] == trained_model
        assert ticker in pipeline.last_training_dates
        assert isinstance(pipeline.last_training_dates[ticker], datetime)

        # Verify model file is saved
        model_path = Path(pipeline.model_storage_path) / f"{ticker}_model.pkl"
        assert model_path.exists()

    def test_should_retrain_model_performance_threshold(self, pipeline, trained_model, sample_data):
        """Test retraining decision based on performance threshold."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Add poor performance history
        pipeline.performance_history[ticker] = [0.7, 0.65, 0.6]  # Below threshold

        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is True

        # Add good performance history
        pipeline.performance_history[ticker] = [0.9, 0.85, 0.88]  # Above threshold

        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is False

    def test_should_retrain_model_time_threshold(self, pipeline, trained_model, sample_data):
        """Test retraining decision based on time threshold."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Set last training date to old date
        old_date = datetime.now() - timedelta(days=pipeline.max_retrain_interval_days + 1)
        pipeline.last_training_dates[ticker] = old_date

        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is True

        # Set recent training date
        recent_date = datetime.now() - timedelta(days=1)
        pipeline.last_training_dates[ticker] = recent_date

        # Should still consider retraining based on performance if poor
        pipeline.performance_history[ticker] = [0.5, 0.4, 0.3]  # Very poor performance
        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is True

    def test_should_retrain_model_drift_detection(self, pipeline, trained_model, sample_data):
        """Test retraining decision based on data drift."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Mock drift detection to return high drift
        with patch.object(pipeline, '_detect_data_drift', return_value=0.5):  # High drift
            result = pipeline.should_retrain_model(ticker, sample_data)
            assert result is True

        # Mock drift detection to return low drift
        with patch.object(pipeline, '_detect_data_drift', return_value=0.05):  # Low drift
            # Also ensure good performance so it doesn't retrain for other reasons
            pipeline.performance_history[ticker] = [0.9, 0.85, 0.88]
            pipeline.last_training_dates[ticker] = datetime.now()  # Recent training

            result = pipeline.should_retrain_model(ticker, sample_data)
            assert result is False

    def test_detect_data_drift(self, pipeline, sample_data):
        """Test data drift detection."""
        # Create reference data
        reference_data = sample_data.copy()

        # Create current data with drift
        current_data = sample_data.copy()
        current_data['feature1'] = current_data['feature1'] + 2.0  # Shift distribution

        drift_score = pipeline._detect_data_drift(reference_data, current_data)

        assert isinstance(drift_score, float)
        assert drift_score >= 0.0
        assert drift_score > 0.1  # Should detect significant drift

        # Test with identical data
        no_drift_score = pipeline._detect_data_drift(reference_data, reference_data)
        assert no_drift_score < drift_score  # Should be lower

    def test_calculate_recent_performance(self, pipeline):
        """Test recent performance calculation."""
        ticker = "TEST"

        # Test with no history
        performance = pipeline._calculate_recent_performance(ticker)
        assert performance is None

        # Test with performance history
        pipeline.performance_history[ticker] = [0.8, 0.85, 0.82, 0.88, 0.9]
        performance = pipeline._calculate_recent_performance(ticker, window=3)

        assert isinstance(performance, float)
        # Should be average of last 3 scores
        expected = np.mean([0.82, 0.88, 0.9])
        assert abs(performance - expected) < 1e-6

    @patch('core.analysis.ml.automation.model_retraining_pipeline.FinancialForecaster')
    def test_retrain_model_success(self, mock_forecaster_class, pipeline, trained_model, sample_data):
        """Test successful model retraining."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Mock forecaster
        mock_forecaster = Mock()
        mock_forecaster.train_fcf_model.return_value = (trained_model, {'r2_score': 0.9})
        mock_forecaster_class.return_value = mock_forecaster

        # Create backup before retraining
        original_training_date = pipeline.last_training_dates[ticker]

        new_model = pipeline.retrain_model(ticker, sample_data)

        assert new_model is not None
        assert pipeline.models[ticker] == new_model
        assert pipeline.last_training_dates[ticker] > original_training_date

        # Verify performance history updated
        assert ticker in pipeline.performance_history
        assert 0.9 in pipeline.performance_history[ticker]

    @patch('core.analysis.ml.automation.model_retraining_pipeline.FinancialForecaster')
    def test_retrain_model_failure_rollback(self, mock_forecaster_class, pipeline, trained_model, sample_data):
        """Test model retraining failure and rollback."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Mock forecaster to raise exception
        mock_forecaster = Mock()
        mock_forecaster.train_fcf_model.side_effect = Exception("Training failed")
        mock_forecaster_class.return_value = mock_forecaster

        # Store original state
        original_model = pipeline.models[ticker]
        original_date = pipeline.last_training_dates[ticker]

        # Attempt retraining
        new_model = pipeline.retrain_model(ticker, sample_data)

        # Should return None on failure
        assert new_model is None

        # Original model should be restored
        assert pipeline.models[ticker] == original_model
        assert pipeline.last_training_dates[ticker] == original_date

    def test_backup_and_restore_model(self, pipeline, trained_model):
        """Test model backup and restore functionality."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Create backup
        backup_path = pipeline._backup_model(ticker)
        assert backup_path is not None
        assert Path(backup_path).exists()

        # Modify current model state
        pipeline.models[ticker] = None
        pipeline.last_training_dates[ticker] = datetime.now()

        # Restore from backup
        success = pipeline._restore_model_from_backup(ticker, backup_path)
        assert success is True
        assert pipeline.models[ticker] is not None

    def test_save_and_load_pipeline_state(self, pipeline, trained_model):
        """Test pipeline state persistence."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)
        pipeline.performance_history[ticker] = [0.8, 0.85, 0.9]

        # Save state
        pipeline.save_pipeline_state()

        # Create new pipeline and load state
        new_pipeline = ModelRetrainingPipeline(model_storage_path=pipeline.model_storage_path)
        new_pipeline.load_pipeline_state()

        # Verify state loaded correctly
        assert ticker in new_pipeline.performance_history
        assert new_pipeline.performance_history[ticker] == [0.8, 0.85, 0.9]
        assert ticker in new_pipeline.last_training_dates

    @patch('core.analysis.ml.automation.model_retraining_pipeline.schedule')
    def test_schedule_automatic_retraining(self, mock_schedule, pipeline):
        """Test automatic retraining scheduling."""
        pipeline.schedule_automatic_retraining(interval_hours=24)

        # Verify schedule was called
        mock_schedule.every.assert_called_once()

    def test_get_pipeline_status(self, pipeline, trained_model):
        """Test pipeline status reporting."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)
        pipeline.performance_history[ticker] = [0.8, 0.85, 0.9]

        status = pipeline.get_pipeline_status()

        assert isinstance(status, dict)
        assert 'models' in status
        assert 'performance_summary' in status
        assert 'last_training_dates' in status

        assert ticker in status['models']
        assert ticker in status['performance_summary']
        assert ticker in status['last_training_dates']

    def test_cleanup_old_backups(self, pipeline, trained_model):
        """Test cleanup of old backup files."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Create multiple backups
        backup_paths = []
        for i in range(5):
            backup_path = pipeline._backup_model(ticker)
            backup_paths.append(backup_path)

        # Verify backups exist
        for path in backup_paths:
            assert Path(path).exists()

        # Cleanup with max_backups=2
        pipeline._cleanup_old_backups(ticker, max_backups=2)

        # Count remaining backups
        backup_dir = Path(pipeline.model_storage_path)
        remaining_backups = list(backup_dir.glob(f"{ticker}_model_backup_*.pkl"))
        assert len(remaining_backups) <= 2

    def test_model_not_initialized_error(self, pipeline, sample_data):
        """Test error handling when model not initialized."""
        ticker = "UNINITIALIZED"

        # Should return False for uninitialized model
        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is False

        # Should return None when trying to retrain uninitialized model
        result = pipeline.retrain_model(ticker, sample_data)
        assert result is None

    def test_invalid_data_handling(self, pipeline, trained_model):
        """Test handling of invalid training data."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Test with empty dataframe
        empty_data = pd.DataFrame()
        result = pipeline.should_retrain_model(ticker, empty_data)
        assert result is False

        # Test with dataframe missing required columns
        invalid_data = pd.DataFrame({'wrong_column': [1, 2, 3]})
        result = pipeline.should_retrain_model(ticker, invalid_data)
        assert result is False

    def test_performance_threshold_edge_cases(self, pipeline, trained_model, sample_data):
        """Test edge cases for performance threshold."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Test exactly at threshold
        pipeline.performance_history[ticker] = [0.8, 0.8, 0.8]  # Exactly at threshold
        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is False  # Should not retrain at threshold

        # Test just below threshold
        pipeline.performance_history[ticker] = [0.79, 0.79, 0.79]  # Just below
        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is True  # Should retrain below threshold

    def test_concurrent_retraining_prevention(self, pipeline, trained_model, sample_data):
        """Test prevention of concurrent retraining."""
        ticker = "TEST"
        pipeline.initialize_model(ticker, trained_model)

        # Simulate retraining in progress
        pipeline._retraining_in_progress = {ticker: True}

        result = pipeline.should_retrain_model(ticker, sample_data)
        assert result is False  # Should not retrain if already in progress

        # Clear retraining flag
        pipeline._retraining_in_progress = {}

        result = pipeline.should_retrain_model(ticker, sample_data)
        # Result depends on other conditions, but shouldn't be blocked by retraining flag