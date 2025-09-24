"""
Automated Model Retraining Pipeline
====================================

Automated pipeline for monitoring model performance and retraining ML models
when performance degradation is detected or new data becomes available.

This module provides intelligent model lifecycle management with automated
decision-making for when to retrain models based on multiple factors.
"""

import logging
try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False
    schedule = None
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np
import json

# Import ML framework components
from ..models.model_manager import MLModelManager, ModelMetadata, ModelStatus
from ..validation.model_validator import ModelValidator, ValidationResult
from ..forecasting.financial_forecaster import FinancialForecaster
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.error_handler import EnhancedErrorHandler

logger = logging.getLogger(__name__)

class RetrainingTrigger(Enum):
    """Reasons that can trigger model retraining"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    NEW_DATA_AVAILABLE = "new_data_available"
    SCHEDULED_RETRAIN = "scheduled_retrain"
    MODEL_DRIFT_DETECTED = "model_drift_detected"
    VALIDATION_FAILURE = "validation_failure"
    MANUAL_TRIGGER = "manual_trigger"

@dataclass
class RetrainingConfig:
    """Configuration for automated retraining"""
    enabled: bool = True
    schedule_frequency: str = "weekly"  # daily, weekly, monthly
    performance_threshold: float = 0.6  # Minimum R² score
    drift_threshold: float = 0.1  # Maximum acceptable drift
    min_data_age_days: int = 7  # Minimum days between retraining
    max_model_age_days: int = 90  # Maximum model age before mandatory retrain
    validation_required: bool = True
    backup_models: bool = True
    notification_enabled: bool = True

@dataclass
class RetrainingEvent:
    """Record of a retraining event"""
    timestamp: datetime
    trigger: RetrainingTrigger
    model_id: str
    old_performance: Dict[str, float]
    new_performance: Dict[str, float]
    success: bool
    error_message: Optional[str] = None
    duration_seconds: float = 0.0

class ModelRetrainingPipeline:
    """
    Automated model retraining pipeline

    This class provides comprehensive automated model lifecycle management
    including performance monitoring, drift detection, and intelligent
    retraining decisions.

    Features:
    - Automated performance monitoring
    - Model drift detection
    - Intelligent retraining scheduling
    - Validation-based deployment
    - Performance regression detection
    - Backup and rollback capabilities
    """

    def __init__(self,
                 ml_manager: MLModelManager,
                 validator: ModelValidator,
                 config: Optional[RetrainingConfig] = None,
                 storage_path: str = "data/retraining"):
        """
        Initialize the retraining pipeline

        Parameters:
        -----------
        ml_manager : MLModelManager
            ML model manager instance
        validator : ModelValidator
            Model validator instance
        config : RetrainingConfig, optional
            Retraining configuration
        storage_path : str
            Path for storing retraining logs and backups
        """
        self.ml_manager = ml_manager
        self.validator = validator
        self.config = config or RetrainingConfig()

        # Setup storage
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Retraining history
        self.retraining_history: List[RetrainingEvent] = []
        self.load_retraining_history()

        # Performance tracking
        self.performance_history: Dict[str, List[Dict[str, Any]]] = {}
        self.load_performance_history()

        # Pipeline status
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None

        logger.info("Model retraining pipeline initialized")

    def start_pipeline(self):
        """Start the automated retraining pipeline"""
        if not self.config.enabled:
            logger.info("Retraining pipeline is disabled")
            return

        if self.is_running:
            logger.warning("Retraining pipeline is already running")
            return

        self.is_running = True

        # Setup scheduled retraining
        self.setup_schedule()

        # Start scheduler in separate thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.scheduler_thread.start()

        logger.info(f"Retraining pipeline started with {self.config.schedule_frequency} schedule")

    def stop_pipeline(self):
        """Stop the automated retraining pipeline"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        schedule.clear()
        logger.info("Retraining pipeline stopped")

    def setup_schedule(self):
        """Setup the retraining schedule"""
        schedule.clear()

        if self.config.schedule_frequency == "daily":
            schedule.every().day.at("02:00").do(self.run_scheduled_retraining)
        elif self.config.schedule_frequency == "weekly":
            schedule.every().sunday.at("02:00").do(self.run_scheduled_retraining)
        elif self.config.schedule_frequency == "monthly":
            schedule.every(30).days.at("02:00").do(self.run_scheduled_retraining)

    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

    def run_scheduled_retraining(self):
        """Run scheduled retraining for all models"""
        logger.info("Running scheduled retraining check")

        try:
            models = self.ml_manager.list_models()

            for model_info in models:
                model_id = model_info['model_id']

                # Check if model needs retraining
                if self.should_retrain_model(model_id, RetrainingTrigger.SCHEDULED_RETRAIN):
                    self.retrain_model(model_id, RetrainingTrigger.SCHEDULED_RETRAIN)

        except Exception as e:
            logger.error(f"Error in scheduled retraining: {e}")

    def should_retrain_model(self, model_id: str, trigger: RetrainingTrigger) -> bool:
        """
        Determine if a model should be retrained

        Parameters:
        -----------
        model_id : str
            Model identifier
        trigger : RetrainingTrigger
            Reason for potential retraining

        Returns:
        --------
        bool
            True if model should be retrained
        """
        try:
            if model_id not in self.ml_manager.metadata:
                return False

            metadata = self.ml_manager.metadata[model_id]

            # Check model age
            model_age = (datetime.now() - metadata.training_date).days
            if model_age > self.config.max_model_age_days:
                logger.info(f"Model {model_id} is {model_age} days old, triggering retrain")
                return True

            # Check last retraining
            last_retrain = self.get_last_retraining_date(model_id)
            if last_retrain:
                days_since_retrain = (datetime.now() - last_retrain).days
                if days_since_retrain < self.config.min_data_age_days:
                    return False

            # Check performance degradation
            if trigger == RetrainingTrigger.PERFORMANCE_DEGRADATION:
                current_performance = metadata.performance_metrics.get('r2_score', 0)
                if current_performance < self.config.performance_threshold:
                    logger.info(f"Model {model_id} performance {current_performance} below threshold")
                    return True

            # Check for model drift
            if self.detect_model_drift(model_id):
                logger.info(f"Model drift detected for {model_id}")
                return True

            # Check for new data availability
            if trigger == RetrainingTrigger.NEW_DATA_AVAILABLE:
                if self.has_new_training_data(model_id):
                    logger.info(f"New training data available for {model_id}")
                    return True

            return trigger == RetrainingTrigger.MANUAL_TRIGGER

        except Exception as e:
            logger.error(f"Error checking retrain condition for {model_id}: {e}")
            return False

    def retrain_model(self, model_id: str, trigger: RetrainingTrigger) -> bool:
        """
        Retrain a specific model

        Parameters:
        -----------
        model_id : str
            Model identifier
        trigger : RetrainingTrigger
            Reason for retraining

        Returns:
        --------
        bool
            True if retraining was successful
        """
        start_time = datetime.now()

        try:
            logger.info(f"Starting retraining for model {model_id} (trigger: {trigger.value})")

            # Get current model metadata
            if model_id not in self.ml_manager.metadata:
                raise ValueError(f"Model {model_id} not found")

            metadata = self.ml_manager.metadata[model_id]
            old_performance = metadata.performance_metrics.copy()

            # Backup current model if enabled
            if self.config.backup_models:
                self.backup_model(model_id)

            # Prepare training data
            training_data = self.prepare_retraining_data(model_id, metadata)

            if training_data.empty:
                raise ValueError("No training data available for retraining")

            # Train new model
            new_model_id = self.ml_manager.train_financial_predictor(
                target_variable=metadata.target_variable,
                feature_columns=metadata.features,
                data=training_data,
                ticker=None,  # Generic retraining
                model_type="random_forest"  # Could be made configurable
            )

            if not new_model_id:
                raise RuntimeError("Model training failed")

            # Validate new model
            if self.config.validation_required:
                new_model = self.ml_manager.models[new_model_id]
                X = training_data[metadata.features]
                y = training_data[metadata.target_variable]

                validation_result = self.validator.validate_model(
                    new_model, X, y, new_model_id
                )

                if not validation_result.passed_validation:
                    logger.warning(f"New model {new_model_id} failed validation")
                    # Could implement rollback logic here
                    self.log_retraining_event(
                        RetrainingEvent(
                            timestamp=start_time,
                            trigger=trigger,
                            model_id=model_id,
                            old_performance=old_performance,
                            new_performance={},
                            success=False,
                            error_message="Validation failed",
                            duration_seconds=(datetime.now() - start_time).total_seconds()
                        )
                    )
                    return False

            # Get new performance metrics
            new_metadata = self.ml_manager.metadata[new_model_id]
            new_performance = new_metadata.performance_metrics.copy()

            # Replace old model with new one
            self.replace_model(model_id, new_model_id)

            # Log successful retraining
            duration = (datetime.now() - start_time).total_seconds()

            self.log_retraining_event(
                RetrainingEvent(
                    timestamp=start_time,
                    trigger=trigger,
                    model_id=model_id,
                    old_performance=old_performance,
                    new_performance=new_performance,
                    success=True,
                    duration_seconds=duration
                )
            )

            # Update performance history
            self.update_performance_history(model_id, new_performance)

            logger.info(f"Model {model_id} retrained successfully in {duration:.2f}s")

            # Send notification if enabled
            if self.config.notification_enabled:
                self.send_retraining_notification(model_id, old_performance, new_performance)

            return True

        except Exception as e:
            logger.error(f"Error retraining model {model_id}: {e}")

            # Log failed retraining
            self.log_retraining_event(
                RetrainingEvent(
                    timestamp=start_time,
                    trigger=trigger,
                    model_id=model_id,
                    old_performance=old_performance if 'old_performance' in locals() else {},
                    new_performance={},
                    success=False,
                    error_message=str(e),
                    duration_seconds=(datetime.now() - start_time).total_seconds()
                )
            )

            return False

    def detect_model_drift(self, model_id: str) -> bool:
        """Detect model drift using performance history"""
        try:
            if model_id not in self.performance_history:
                return False

            history = self.performance_history[model_id]
            if len(history) < 3:  # Need at least 3 data points
                return False

            # Get recent performance metrics
            recent_scores = [h.get('r2_score', 0) for h in history[-5:]]
            baseline_scores = [h.get('r2_score', 0) for h in history[-10:-5]] if len(history) >= 10 else recent_scores

            if not recent_scores or not baseline_scores:
                return False

            # Calculate drift as difference in mean performance
            recent_mean = np.mean(recent_scores)
            baseline_mean = np.mean(baseline_scores)

            drift = abs(baseline_mean - recent_mean)

            return drift > self.config.drift_threshold

        except Exception as e:
            logger.error(f"Error detecting drift for model {model_id}: {e}")
            return False

    def has_new_training_data(self, model_id: str) -> bool:
        """Check if new training data is available"""
        try:
            # Simple heuristic: check if it's been more than min_data_age_days
            # since last training and we have recent data

            if model_id not in self.ml_manager.metadata:
                return False

            metadata = self.ml_manager.metadata[model_id]
            days_since_training = (datetime.now() - metadata.training_date).days

            return days_since_training >= self.config.min_data_age_days

        except Exception as e:
            logger.error(f"Error checking new data for model {model_id}: {e}")
            return False

    def prepare_retraining_data(self, model_id: str, metadata: ModelMetadata) -> pd.DataFrame:
        """Prepare data for model retraining"""
        try:
            # This is a simplified implementation
            # In practice, this would fetch the latest data from the same sources
            # used for initial training

            # For now, return empty DataFrame - would be implemented based on
            # specific data source integration
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Error preparing retraining data for {model_id}: {e}")
            return pd.DataFrame()

    def backup_model(self, model_id: str):
        """Create backup of existing model"""
        try:
            backup_dir = self.storage_path / "backups" / model_id
            backup_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"model_backup_{timestamp}.json"

            # Create backup metadata
            backup_data = {
                'model_id': model_id,
                'backup_timestamp': timestamp,
                'metadata': self.ml_manager.get_model_performance(model_id)
            }

            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)

            logger.info(f"Model {model_id} backed up to {backup_file}")

        except Exception as e:
            logger.error(f"Error backing up model {model_id}: {e}")

    def replace_model(self, old_model_id: str, new_model_id: str):
        """Replace old model with new model"""
        try:
            # Copy the new model to replace the old one
            if old_model_id in self.ml_manager.models and new_model_id in self.ml_manager.models:
                self.ml_manager.models[old_model_id] = self.ml_manager.models[new_model_id]
                self.ml_manager.metadata[old_model_id] = self.ml_manager.metadata[new_model_id]

                # Update the model ID in metadata
                self.ml_manager.metadata[old_model_id].model_id = old_model_id

                # Save the updated model
                self.ml_manager._save_model(old_model_id)

                # Clean up the temporary new model
                if new_model_id != old_model_id:
                    del self.ml_manager.models[new_model_id]
                    del self.ml_manager.metadata[new_model_id]

        except Exception as e:
            logger.error(f"Error replacing model {old_model_id} with {new_model_id}: {e}")

    def get_last_retraining_date(self, model_id: str) -> Optional[datetime]:
        """Get the date of last retraining for a model"""
        model_events = [event for event in self.retraining_history
                       if event.model_id == model_id and event.success]

        if model_events:
            return max(event.timestamp for event in model_events)

        return None

    def log_retraining_event(self, event: RetrainingEvent):
        """Log a retraining event"""
        self.retraining_history.append(event)
        self.save_retraining_history()

    def update_performance_history(self, model_id: str, performance: Dict[str, float]):
        """Update performance history for a model"""
        if model_id not in self.performance_history:
            self.performance_history[model_id] = []

        performance_entry = {
            'timestamp': datetime.now().isoformat(),
            **performance
        }

        self.performance_history[model_id].append(performance_entry)

        # Keep only last 50 entries per model
        self.performance_history[model_id] = self.performance_history[model_id][-50:]

        self.save_performance_history()

    def send_retraining_notification(self, model_id: str,
                                   old_performance: Dict[str, float],
                                   new_performance: Dict[str, float]):
        """Send notification about model retraining"""
        try:
            # Simple logging notification - could be extended to email, Slack, etc.
            old_r2 = old_performance.get('r2_score', 0)
            new_r2 = new_performance.get('r2_score', 0)

            improvement = new_r2 - old_r2

            logger.info(f"Model Retraining Notification - {model_id}")
            logger.info(f"Old R² Score: {old_r2:.4f}")
            logger.info(f"New R² Score: {new_r2:.4f}")
            logger.info(f"Improvement: {improvement:+.4f}")

        except Exception as e:
            logger.error(f"Error sending notification: {e}")

    def get_retraining_summary(self) -> Dict[str, Any]:
        """Get summary of retraining activity"""
        try:
            total_events = len(self.retraining_history)
            successful_events = len([e for e in self.retraining_history if e.success])

            recent_events = [e for e in self.retraining_history
                           if e.timestamp > datetime.now() - timedelta(days=30)]

            trigger_counts = {}
            for event in self.retraining_history:
                trigger = event.trigger.value
                trigger_counts[trigger] = trigger_counts.get(trigger, 0) + 1

            return {
                'total_retraining_events': total_events,
                'successful_events': successful_events,
                'success_rate': successful_events / total_events if total_events > 0 else 0,
                'recent_events_30d': len(recent_events),
                'trigger_distribution': trigger_counts,
                'pipeline_status': 'running' if self.is_running else 'stopped',
                'last_scheduled_run': max([e.timestamp for e in self.retraining_history
                                         if e.trigger == RetrainingTrigger.SCHEDULED_RETRAIN],
                                        default=None)
            }

        except Exception as e:
            logger.error(f"Error generating retraining summary: {e}")
            return {}

    def save_retraining_history(self):
        """Save retraining history to disk"""
        try:
            history_file = self.storage_path / "retraining_history.json"

            # Convert events to dictionaries for JSON serialization
            history_data = []
            for event in self.retraining_history:
                event_data = {
                    'timestamp': event.timestamp.isoformat(),
                    'trigger': event.trigger.value,
                    'model_id': event.model_id,
                    'old_performance': event.old_performance,
                    'new_performance': event.new_performance,
                    'success': event.success,
                    'error_message': event.error_message,
                    'duration_seconds': event.duration_seconds
                }
                history_data.append(event_data)

            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving retraining history: {e}")

    def load_retraining_history(self):
        """Load retraining history from disk"""
        try:
            history_file = self.storage_path / "retraining_history.json"

            if not history_file.exists():
                return

            with open(history_file, 'r') as f:
                history_data = json.load(f)

            self.retraining_history = []
            for event_data in history_data:
                event = RetrainingEvent(
                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                    trigger=RetrainingTrigger(event_data['trigger']),
                    model_id=event_data['model_id'],
                    old_performance=event_data['old_performance'],
                    new_performance=event_data['new_performance'],
                    success=event_data['success'],
                    error_message=event_data.get('error_message'),
                    duration_seconds=event_data.get('duration_seconds', 0.0)
                )
                self.retraining_history.append(event)

        except Exception as e:
            logger.error(f"Error loading retraining history: {e}")

    def save_performance_history(self):
        """Save performance history to disk"""
        try:
            performance_file = self.storage_path / "performance_history.json"

            with open(performance_file, 'w') as f:
                json.dump(self.performance_history, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error saving performance history: {e}")

    def load_performance_history(self):
        """Load performance history from disk"""
        try:
            performance_file = self.storage_path / "performance_history.json"

            if not performance_file.exists():
                return

            with open(performance_file, 'r') as f:
                self.performance_history = json.load(f)

        except Exception as e:
            logger.error(f"Error loading performance history: {e}")

# Convenience functions for pipeline management

def create_retraining_pipeline(financial_calculator: Optional[FinancialCalculator] = None,
                              config: Optional[RetrainingConfig] = None) -> ModelRetrainingPipeline:
    """Create a configured retraining pipeline"""
    ml_manager = MLModelManager(financial_calculator)
    validator = ModelValidator()

    return ModelRetrainingPipeline(ml_manager, validator, config)

def start_background_retraining(financial_calculator: Optional[FinancialCalculator] = None,
                               config: Optional[RetrainingConfig] = None) -> ModelRetrainingPipeline:
    """Start background retraining pipeline"""
    pipeline = create_retraining_pipeline(financial_calculator, config)
    pipeline.start_pipeline()
    return pipeline