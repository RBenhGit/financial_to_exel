"""
ML Model Manager
===============

Central manager for machine learning model lifecycle including training,
validation, deployment, and monitoring within the financial analysis framework.

This manager integrates with the existing FinancialCalculator and data processing
systems to provide seamless ML capabilities while maintaining the project's
architectural principles.
"""

import logging
import pickle
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score, classification_report
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline

# Import existing framework components
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.data_processing.error_handler import handle_calculation_error

logger = logging.getLogger(__name__)

class ModelType(Enum):
    """Supported ML model types"""
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
    TIME_SERIES = "time_series"
    ENSEMBLE = "ensemble"

class ModelStatus(Enum):
    """Model lifecycle status"""
    TRAINING = "training"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"

@dataclass
class ModelMetadata:
    """Model metadata and performance tracking"""
    model_id: str
    model_type: ModelType
    target_variable: str
    features: List[str]
    training_date: datetime
    status: ModelStatus
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    validation_results: Dict[str, Any] = field(default_factory=dict)
    bias_test_results: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class PredictionResult:
    """ML model prediction result with confidence metrics"""
    prediction: Union[float, np.ndarray]
    confidence_interval: Optional[Tuple[float, float]] = None
    prediction_date: datetime = field(default_factory=datetime.now)
    model_id: str = ""
    feature_importance: Optional[Dict[str, float]] = None
    uncertainty_score: Optional[float] = None

class MLModelManager:
    """
    Central manager for ML model lifecycle and deployment

    This class provides a unified interface for training, validating, and deploying
    machine learning models within the financial analysis framework.

    Features:
    - Model training with cross-validation
    - Automated feature engineering from financial data
    - Model validation and bias testing
    - Performance monitoring and alerting
    - Integration with existing data processing pipeline
    """

    def __init__(self,
                 financial_calculator: Optional[FinancialCalculator] = None,
                 model_storage_path: str = "data/models"):
        """
        Initialize ML Model Manager

        Parameters:
        -----------
        financial_calculator : FinancialCalculator, optional
            Existing financial calculator for data integration
        model_storage_path : str
            Path for storing trained models and metadata
        """
        self.financial_calculator = financial_calculator
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)

        # Model registry
        self.models: Dict[str, Any] = {}
        self.metadata: Dict[str, ModelMetadata] = {}
        self.scalers: Dict[str, StandardScaler] = {}

        # Load existing models
        self._load_existing_models()

        logger.info(f"MLModelManager initialized with storage: {self.model_storage_path}")

    def train_financial_predictor(self,
                                 target_variable: str,
                                 feature_columns: List[str],
                                 data: Optional[pd.DataFrame] = None,
                                 ticker: Optional[str] = None,
                                 model_type: str = "random_forest",
                                 test_size: float = 0.2,
                                 cv_folds: int = 5) -> str:
        """
        Train a financial prediction model

        Parameters:
        -----------
        target_variable : str
            Target variable to predict (e.g., 'fcf_growth', 'stock_return')
        feature_columns : List[str]
            List of feature column names
        data : pd.DataFrame, optional
            Training data. If None, will extract from financial_calculator
        ticker : str, optional
            Ticker symbol for data extraction
        model_type : str
            Type of model ('random_forest', 'linear', 'gradient_boost')
        test_size : float
            Proportion of data for testing
        cv_folds : int
            Number of cross-validation folds

        Returns:
        --------
        str
            Model ID for the trained model
        """
        try:
            # Data preparation
            if data is None and ticker and self.financial_calculator:
                data = self._extract_training_data(ticker)

            if data is None or data.empty:
                raise ValueError("No training data available")

            # Feature and target preparation
            X = data[feature_columns].copy()
            y = data[target_variable].copy()

            # Handle missing values
            X = X.fillna(X.median())
            y = y.fillna(y.median())

            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Create and train model
            model_id = f"{target_variable}_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            model, scaler = self._create_model_pipeline(model_type, X_train, y_train)

            # Cross-validation
            cv_scores = cross_val_score(model, X_train, y_train, cv=cv_folds, scoring='r2')

            # Final training on full training set
            model.fit(X_train, y_train)

            # Predictions and metrics
            y_pred = model.predict(X_test)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)

            # Store model and metadata
            self.models[model_id] = model
            self.scalers[model_id] = scaler

            metadata = ModelMetadata(
                model_id=model_id,
                model_type=ModelType.REGRESSION,
                target_variable=target_variable,
                features=feature_columns,
                training_date=datetime.now(),
                status=ModelStatus.VALIDATED,
                performance_metrics={
                    'mse': mse,
                    'r2': r2,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std()
                },
                description=f"Financial predictor for {target_variable} using {model_type}"
            )

            self.metadata[model_id] = metadata

            # Save model to disk
            self._save_model(model_id)

            logger.info(f"Model {model_id} trained successfully. R² Score: {r2:.4f}")

            return model_id

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return handle_calculation_error(e, "ML model training")

    def predict(self,
                model_id: str,
                features: Union[Dict[str, float], pd.DataFrame]) -> PredictionResult:
        """
        Make predictions using a trained model

        Parameters:
        -----------
        model_id : str
            ID of the trained model
        features : Dict or DataFrame
            Feature values for prediction

        Returns:
        --------
        PredictionResult
            Prediction result with confidence metrics
        """
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model = self.models[model_id]
            scaler = self.scalers.get(model_id)
            metadata = self.metadata[model_id]

            # Prepare features
            if isinstance(features, dict):
                X = pd.DataFrame([features])
            else:
                X = features.copy()

            # Ensure feature order matches training
            X = X[metadata.features]

            # Handle missing values
            X = X.fillna(X.median())

            # Scale features if scaler exists
            if scaler:
                X_scaled = scaler.transform(X)
            else:
                X_scaled = X

            # Make prediction
            prediction = model.predict(X_scaled)

            # Calculate feature importance (for tree-based models)
            feature_importance = None
            if hasattr(model, 'feature_importances_'):
                feature_importance = dict(zip(metadata.features, model.feature_importances_))

            # Calculate prediction confidence (simplified approach)
            uncertainty_score = None
            if hasattr(model, 'predict_proba'):
                # For classification models
                proba = model.predict_proba(X_scaled)
                uncertainty_score = 1 - np.max(proba)

            result = PredictionResult(
                prediction=prediction[0] if len(prediction) == 1 else prediction,
                model_id=model_id,
                feature_importance=feature_importance,
                uncertainty_score=uncertainty_score
            )

            logger.info(f"Prediction made using model {model_id}")

            return result

        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return handle_calculation_error(e, "ML model prediction")

    def validate_model_bias(self, model_id: str, test_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Perform bias testing on a trained model

        Parameters:
        -----------
        model_id : str
            ID of the model to test
        test_data : pd.DataFrame
            Test dataset for bias analysis

        Returns:
        --------
        Dict[str, Any]
            Bias test results and recommendations
        """
        try:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            model = self.models[model_id]
            metadata = self.metadata[model_id]

            # Prepare test data
            X_test = test_data[metadata.features]
            y_test = test_data[metadata.target_variable]

            # Make predictions
            y_pred = model.predict(X_test)

            # Bias analysis
            bias_results = {
                'overall_bias': np.mean(y_pred - y_test),
                'prediction_variance': np.var(y_pred),
                'residual_analysis': {
                    'mean_residual': np.mean(y_test - y_pred),
                    'residual_std': np.std(y_test - y_pred)
                },
                'feature_bias': {}
            }

            # Feature-level bias analysis
            for feature in metadata.features:
                if feature in test_data.columns:
                    feature_values = test_data[feature]
                    # Analyze bias across feature value ranges
                    if len(feature_values.unique()) > 10:
                        # Continuous feature: split into quantiles
                        quartiles = pd.qcut(feature_values, q=4, duplicates='drop')
                        bias_by_quartile = []
                        for quartile in quartiles.cat.categories:
                            mask = quartiles == quartile
                            if mask.sum() > 0:
                                quartile_bias = np.mean(y_pred[mask] - y_test[mask])
                                bias_by_quartile.append(quartile_bias)
                        bias_results['feature_bias'][feature] = {
                            'quartile_bias': bias_by_quartile,
                            'max_bias_difference': max(bias_by_quartile) - min(bias_by_quartile) if bias_by_quartile else 0
                        }

            # Store bias results
            self.metadata[model_id].bias_test_results = bias_results

            logger.info(f"Bias testing completed for model {model_id}")

            return bias_results

        except Exception as e:
            logger.error(f"Error in bias testing: {e}")
            return handle_calculation_error(e, "ML model bias testing")

    def get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get comprehensive model performance metrics"""
        if model_id not in self.metadata:
            raise ValueError(f"Model {model_id} not found")

        metadata = self.metadata[model_id]
        return {
            'model_id': model_id,
            'model_type': metadata.model_type.value,
            'target_variable': metadata.target_variable,
            'training_date': metadata.training_date.isoformat(),
            'status': metadata.status.value,
            'performance_metrics': metadata.performance_metrics,
            'bias_test_results': metadata.bias_test_results,
            'features': metadata.features
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models with their metadata"""
        return [self.get_model_performance(model_id) for model_id in self.models.keys()]

    def _create_model_pipeline(self, model_type: str, X_train: pd.DataFrame, y_train: pd.Series):
        """Create and configure ML model pipeline"""
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_train)

        if model_type == "random_forest":
            model = RandomForestRegressor(n_estimators=100, random_state=42)
        elif model_type == "linear":
            model = LinearRegression()
        else:
            # Default to random forest
            model = RandomForestRegressor(n_estimators=100, random_state=42)

        return model, scaler

    def _extract_training_data(self, ticker: str) -> pd.DataFrame:
        """Extract training data from financial calculator"""
        if not self.financial_calculator:
            return pd.DataFrame()

        try:
            # Use financial calculator to get historical data
            # This would integrate with existing data extraction methods
            data = pd.DataFrame()  # Placeholder - implement based on existing data structure
            return data
        except Exception as e:
            logger.error(f"Error extracting training data: {e}")
            return pd.DataFrame()

    def _save_model(self, model_id: str):
        """Save model and metadata to disk"""
        try:
            model_path = self.model_storage_path / f"{model_id}.pkl"
            metadata_path = self.model_storage_path / f"{model_id}_metadata.json"
            scaler_path = self.model_storage_path / f"{model_id}_scaler.pkl"

            # Save model
            with open(model_path, 'wb') as f:
                pickle.dump(self.models[model_id], f)

            # Save scaler
            if model_id in self.scalers:
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scalers[model_id], f)

            # Save metadata
            metadata_dict = {
                'model_id': self.metadata[model_id].model_id,
                'model_type': self.metadata[model_id].model_type.value,
                'target_variable': self.metadata[model_id].target_variable,
                'features': self.metadata[model_id].features,
                'training_date': self.metadata[model_id].training_date.isoformat(),
                'status': self.metadata[model_id].status.value,
                'performance_metrics': self.metadata[model_id].performance_metrics,
                'validation_results': self.metadata[model_id].validation_results,
                'bias_test_results': self.metadata[model_id].bias_test_results,
                'description': self.metadata[model_id].description
            }

            with open(metadata_path, 'w') as f:
                json.dump(metadata_dict, f, indent=2)

            logger.info(f"Model {model_id} saved to disk")

        except Exception as e:
            logger.error(f"Error saving model {model_id}: {e}")

    def _load_existing_models(self):
        """Load existing models from disk"""
        try:
            for model_file in self.model_storage_path.glob("*.pkl"):
                if not model_file.name.endswith("_scaler.pkl"):
                    model_id = model_file.stem
                    metadata_file = self.model_storage_path / f"{model_id}_metadata.json"
                    scaler_file = self.model_storage_path / f"{model_id}_scaler.pkl"

                    if metadata_file.exists():
                        # Load model
                        with open(model_file, 'rb') as f:
                            self.models[model_id] = pickle.load(f)

                        # Load scaler if exists
                        if scaler_file.exists():
                            with open(scaler_file, 'rb') as f:
                                self.scalers[model_id] = pickle.load(f)

                        # Load metadata
                        with open(metadata_file, 'r') as f:
                            metadata_dict = json.load(f)

                        metadata = ModelMetadata(
                            model_id=metadata_dict['model_id'],
                            model_type=ModelType(metadata_dict['model_type']),
                            target_variable=metadata_dict['target_variable'],
                            features=metadata_dict['features'],
                            training_date=datetime.fromisoformat(metadata_dict['training_date']),
                            status=ModelStatus(metadata_dict['status']),
                            performance_metrics=metadata_dict.get('performance_metrics', {}),
                            validation_results=metadata_dict.get('validation_results', {}),
                            bias_test_results=metadata_dict.get('bias_test_results', {}),
                            description=metadata_dict.get('description', '')
                        )

                        self.metadata[model_id] = metadata

                        logger.info(f"Loaded existing model: {model_id}")

        except Exception as e:
            logger.error(f"Error loading existing models: {e}")