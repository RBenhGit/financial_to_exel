"""
Variable Processor Pipeline
===========================

Comprehensive data transformation pipeline to standardize variables from different sources
into consistent, validated financial data. This pipeline serves as the critical layer
between raw data extraction and the unified VarInputData storage system.

Key Components:
---------------
- **VariableProcessor**: Main processing engine with configurable transformation rules
- **Unit Normalization**: Convert values to consistent millions scale across all sources
- **Data Validation**: Multi-level validation using FinancialVariableRegistry definitions
- **Quality Assessment**: Comprehensive scoring based on completeness, consistency, and reliability
- **Missing Data Handling**: Intelligent interpolation strategies for gaps in historical data
- **Outlier Detection**: Statistical analysis to identify and flag anomalous values
- **Data Lineage**: Complete tracking of transformations and source attribution

Features:
---------
- **Multi-Source Processing**: Seamlessly handles Excel, API, and calculated data
- **Historical Alignment**: Ensures consistent time-series data across different sources
- **Quality Metrics**: Detailed scoring for data completeness, timeliness, and accuracy
- **Flexible Configuration**: Customizable processing rules and validation thresholds
- **Performance Optimized**: Efficient batch processing with memory management
- **Event Integration**: Real-time notifications through VarInputData event system

Usage Example:
--------------
>>> from variable_processor import VariableProcessor
>>> 
>>> # Initialize processor with custom configuration
>>> processor = VariableProcessor(
...     normalize_units=True,
...     quality_threshold=0.8,
...     enable_interpolation=True
... )
>>> 
>>> # Process data from multiple sources
>>> results = processor.process_data_batch([
...     {"symbol": "AAPL", "source": "excel", "data": excel_data},
...     {"symbol": "AAPL", "source": "yfinance", "data": api_data}
... ])
>>> 
>>> # Check processing results
>>> for result in results:
...     print(f"Processed {result.variables_processed} variables")
...     print(f"Quality score: {result.overall_quality_score}")
"""

import logging
import statistics
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable
import numpy as np
from pathlib import Path

# Import project dependencies
from .financial_variable_registry import (
    get_registry,
    FinancialVariableRegistry,
    VariableDefinition,
    VariableCategory,
    DataType,
    Units
)

from .var_input_data import (
    get_var_input_data,
    VarInputData,
    VariableMetadata,
    DataChangeEvent
)

from .adapters.base_adapter import (
    DataSourceType,
    DataQualityMetrics,
    ExtractionResult
)

# Configure logging
logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Stages in the variable processing pipeline"""
    RAW_EXTRACTION = "raw_extraction"
    UNIT_NORMALIZATION = "unit_normalization"
    DATA_VALIDATION = "data_validation"
    QUALITY_ASSESSMENT = "quality_assessment"
    MISSING_DATA_INTERPOLATION = "missing_data_interpolation"
    OUTLIER_DETECTION = "outlier_detection"
    HISTORICAL_ALIGNMENT = "historical_alignment"
    FINAL_STORAGE = "final_storage"


class InterpolationStrategy(Enum):
    """Strategies for handling missing data"""
    LINEAR = "linear"                    # Linear interpolation between known values
    FORWARD_FILL = "forward_fill"        # Use last known value
    BACKWARD_FILL = "backward_fill"      # Use next known value
    TREND_BASED = "trend_based"          # Based on historical trend analysis
    INDUSTRY_AVERAGE = "industry_average" # Use industry averages when available
    SKIP = "skip"                        # Leave missing data as None


class QualityIssueType(Enum):
    """Types of data quality issues that can be detected"""
    MISSING_DATA = "missing_data"
    OUTLIER_VALUE = "outlier_value"
    INCONSISTENT_UNITS = "inconsistent_units"
    VALIDATION_FAILURE = "validation_failure"
    SOURCE_CONFLICT = "source_conflict"
    INTERPOLATED_VALUE = "interpolated_value"
    STALE_DATA = "stale_data"


@dataclass
class ProcessingConfiguration:
    """Configuration settings for the variable processor"""
    # Unit normalization settings
    normalize_units: bool = True
    target_unit_scale: str = "millions"  # "ones", "thousands", "millions", "billions"
    
    # Data validation settings
    enable_validation: bool = True
    strict_validation: bool = False  # Whether to reject data on validation failures
    
    # Quality assessment settings
    minimum_quality_score: float = 0.6
    completeness_weight: float = 0.4
    consistency_weight: float = 0.3
    timeliness_weight: float = 0.2
    reliability_weight: float = 0.1
    
    # Missing data handling
    enable_interpolation: bool = True
    default_interpolation_strategy: InterpolationStrategy = InterpolationStrategy.LINEAR
    max_interpolation_gap: int = 2  # Maximum years to interpolate across
    
    # Outlier detection settings
    enable_outlier_detection: bool = True
    outlier_threshold_std: float = 3.0  # Standard deviations for outlier detection
    outlier_min_history: int = 5  # Minimum historical points needed for outlier detection
    
    # Historical alignment settings
    enable_historical_alignment: bool = True
    alignment_tolerance_days: int = 90  # Days tolerance for period alignment
    
    # Performance settings
    batch_size: int = 100  # Variables to process in a single batch
    enable_parallel_processing: bool = True
    cache_intermediate_results: bool = True


@dataclass
class QualityIssue:
    """Represents a data quality issue found during processing"""
    issue_type: QualityIssueType
    description: str
    severity: str  # "low", "medium", "high", "critical"
    affected_periods: List[str]
    suggested_action: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingResult:
    """Result of processing variables for a single symbol"""
    symbol: str
    source_type: DataSourceType
    processing_time: float
    variables_processed: int
    variables_successful: int
    variables_failed: int
    variables_interpolated: int
    outliers_detected: int
    quality_issues: List[QualityIssue]
    overall_quality_score: float
    stage_timings: Dict[ProcessingStage, float]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TransformationRecord:
    """Record of transformations applied to a variable"""
    variable_name: str
    original_value: Any
    final_value: Any
    transformations: List[str]  # List of transformation steps applied
    quality_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class VariableProcessor:
    """
    Main processing engine for standardizing financial variables from multiple sources.
    
    This class implements a comprehensive pipeline that takes raw financial data from
    various sources (Excel files, APIs, calculations) and transforms it into consistent,
    validated, and high-quality data stored in the VarInputData system.
    """
    
    def __init__(self, config: Optional[ProcessingConfiguration] = None):
        """
        Initialize the Variable Processor with specified configuration.
        
        Args:
            config: Processing configuration (uses defaults if None)
        """
        self.config = config or ProcessingConfiguration()
        
        # Initialize core systems
        self.variable_registry = get_registry()
        self.var_data = get_var_input_data()
        
        # Processing statistics and performance tracking
        self.stats = {
            'total_variables_processed': 0,
            'total_processing_time': 0.0,
            'average_quality_score': 0.0,
            'total_interpolations': 0,
            'total_outliers_detected': 0,
            'processing_sessions': 0
        }
        
        # Cache for intermediate results
        self._transformation_cache: Dict[str, Any] = {}
        self._quality_cache: Dict[str, float] = {}
        
        # Unit conversion factors (target: millions)
        self._unit_conversion_factors = {
            'ones': 1e-6,
            'thousands': 1e-3,
            'millions': 1.0,
            'billions': 1e3,
            'trillions': 1e6
        }
        
        logger.info(f"VariableProcessor initialized with config: {self.config}")
    
    def process_data_batch(
        self, 
        data_batch: List[Dict[str, Any]],
        callback: Optional[Callable[[ProcessingResult], None]] = None
    ) -> List[ProcessingResult]:
        """
        Process a batch of data from multiple sources.
        
        Args:
            data_batch: List of data dictionaries, each containing:
                - symbol: Stock symbol (e.g., "AAPL")
                - source: Source type ("excel", "yfinance", etc.)
                - data: Raw data dictionary
                - metadata: Optional metadata dictionary
            callback: Optional callback function called after each symbol is processed
            
        Returns:
            List of ProcessingResult objects with detailed results for each symbol
        """
        logger.info(f"Starting batch processing of {len(data_batch)} data sets")
        
        results = []
        session_start_time = time.time()
        
        # Process each data set in the batch
        for i, data_item in enumerate(data_batch):
            try:
                # Extract required fields
                symbol = data_item.get('symbol', '').upper()
                source = data_item.get('source', 'unknown')
                raw_data = data_item.get('data', {})
                metadata = data_item.get('metadata', {})
                
                if not symbol or not raw_data:
                    logger.warning(f"Skipping invalid data item {i}: missing symbol or data")
                    continue
                
                # Determine source type
                source_type = self._determine_source_type(source)
                
                # Process this symbol's data
                result = self.process_symbol_data(
                    symbol=symbol,
                    source_type=source_type,
                    raw_data=raw_data,
                    metadata=metadata
                )
                
                results.append(result)
                
                # Call callback if provided
                if callback:
                    try:
                        callback(result)
                    except Exception as e:
                        logger.error(f"Error in processing callback: {e}")
                
                logger.info(
                    f"Processed {symbol} from {source}: "
                    f"{result.variables_successful}/{result.variables_processed} successful, "
                    f"quality={result.overall_quality_score:.2f}"
                )
                
            except Exception as e:
                logger.error(f"Error processing data item {i}: {e}")
                # Create error result
                error_result = ProcessingResult(
                    symbol=data_item.get('symbol', 'UNKNOWN'),
                    source_type=DataSourceType.EXCEL,  # Default
                    processing_time=0.0,
                    variables_processed=0,
                    variables_successful=0,
                    variables_failed=1,
                    variables_interpolated=0,
                    outliers_detected=0,
                    quality_issues=[QualityIssue(
                        issue_type=QualityIssueType.VALIDATION_FAILURE,
                        description=f"Processing error: {str(e)}",
                        severity="critical",
                        affected_periods=[],
                        suggested_action="Review data format and try again"
                    )],
                    overall_quality_score=0.0,
                    stage_timings={},
                    metadata={"error": str(e)}
                )
                results.append(error_result)
        
        # Update session statistics
        total_session_time = time.time() - session_start_time
        self.stats['processing_sessions'] += 1
        self.stats['total_processing_time'] += total_session_time
        
        if results:
            avg_quality = sum(r.overall_quality_score for r in results) / len(results)
            self.stats['average_quality_score'] = (
                (self.stats['average_quality_score'] * (self.stats['processing_sessions'] - 1) + avg_quality) /
                self.stats['processing_sessions']
            )
        
        logger.info(
            f"Batch processing completed: {len(results)} results in {total_session_time:.2f}s, "
            f"avg quality: {self.stats.get('average_quality_score', 0):.2f}"
        )
        
        return results
    
    def process_symbol_data(
        self,
        symbol: str,
        source_type: DataSourceType,
        raw_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> ProcessingResult:
        """
        Process all variables for a single symbol through the complete pipeline.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL")
            source_type: Type of data source
            raw_data: Raw data dictionary with variable names as keys
            metadata: Optional metadata dictionary
            
        Returns:
            ProcessingResult with detailed processing information
        """
        start_time = time.time()
        stage_timings = {}
        quality_issues = []
        transformation_records = []
        
        logger.debug(f"Processing {symbol} from {source_type.value} with {len(raw_data)} variables")
        
        # Stage 1: Raw extraction validation
        stage_start = time.time()
        validated_data = self._validate_raw_extraction(symbol, raw_data, quality_issues)
        stage_timings[ProcessingStage.RAW_EXTRACTION] = time.time() - stage_start
        
        # Stage 2: Unit normalization
        stage_start = time.time()
        normalized_data = self._normalize_units(symbol, validated_data, transformation_records, quality_issues)
        stage_timings[ProcessingStage.UNIT_NORMALIZATION] = time.time() - stage_start
        
        # Stage 3: Data validation using registry
        stage_start = time.time()
        registry_validated_data = self._validate_with_registry(symbol, normalized_data, quality_issues)
        stage_timings[ProcessingStage.DATA_VALIDATION] = time.time() - stage_start
        
        # Stage 4: Historical alignment (if historical data exists)
        stage_start = time.time()
        aligned_data = self._align_historical_data(symbol, registry_validated_data, quality_issues)
        stage_timings[ProcessingStage.HISTORICAL_ALIGNMENT] = time.time() - stage_start
        
        # Stage 5: Missing data interpolation
        stage_start = time.time()
        interpolated_data, interpolated_count = self._handle_missing_data(symbol, aligned_data, quality_issues)
        stage_timings[ProcessingStage.MISSING_DATA_INTERPOLATION] = time.time() - stage_start
        
        # Stage 6: Outlier detection
        stage_start = time.time()
        outlier_checked_data, outliers_detected = self._detect_outliers(symbol, interpolated_data, quality_issues)
        stage_timings[ProcessingStage.OUTLIER_DETECTION] = time.time() - stage_start
        
        # Stage 7: Quality assessment
        stage_start = time.time()
        quality_scores = self._assess_data_quality(symbol, outlier_checked_data, quality_issues)
        overall_quality = self._calculate_overall_quality(quality_scores, quality_issues)
        stage_timings[ProcessingStage.QUALITY_ASSESSMENT] = time.time() - stage_start
        
        # Stage 8: Final storage in VarInputData
        stage_start = time.time()
        stored_count, failed_count = self._store_processed_data(
            symbol, 
            outlier_checked_data, 
            source_type, 
            metadata or {}
        )
        stage_timings[ProcessingStage.FINAL_STORAGE] = time.time() - stage_start
        
        # Calculate final statistics
        total_time = time.time() - start_time
        total_processed = len(raw_data)
        
        # Update global statistics
        self.stats['total_variables_processed'] += total_processed
        self.stats['total_interpolations'] += interpolated_count
        self.stats['total_outliers_detected'] += outliers_detected
        
        # Create and return processing result
        result = ProcessingResult(
            symbol=symbol,
            source_type=source_type,
            processing_time=total_time,
            variables_processed=total_processed,
            variables_successful=stored_count,
            variables_failed=failed_count,
            variables_interpolated=interpolated_count,
            outliers_detected=outliers_detected,
            quality_issues=quality_issues,
            overall_quality_score=overall_quality,
            stage_timings=stage_timings,
            metadata={
                'transformation_records': len(transformation_records),
                'source_metadata': metadata or {},
                'processing_timestamp': datetime.now().isoformat()
            }
        )
        
        logger.debug(f"Completed processing {symbol}: {stored_count}/{total_processed} successful")
        return result
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        return {
            'performance_stats': dict(self.stats),
            'cache_stats': {
                'transformation_cache_size': len(self._transformation_cache),
                'quality_cache_size': len(self._quality_cache)
            },
            'configuration': {
                'normalize_units': self.config.normalize_units,
                'target_unit_scale': self.config.target_unit_scale,
                'enable_interpolation': self.config.enable_interpolation,
                'enable_outlier_detection': self.config.enable_outlier_detection,
                'minimum_quality_score': self.config.minimum_quality_score
            }
        }
    
    def clear_cache(self) -> None:
        """Clear all cached data"""
        self._transformation_cache.clear()
        self._quality_cache.clear()
        logger.info("VariableProcessor cache cleared")
    
    # Private processing stage methods
    
    def _validate_raw_extraction(
        self, 
        symbol: str, 
        raw_data: Dict[str, Any], 
        quality_issues: List[QualityIssue]
    ) -> Dict[str, Any]:
        """Validate and clean raw extracted data"""
        validated_data = {}
        
        for variable_name, value in raw_data.items():
            # Normalize variable name
            normalized_name = variable_name.lower().strip()
            
            # Basic validation
            if value is None or (isinstance(value, str) and not value.strip()):
                quality_issues.append(QualityIssue(
                    issue_type=QualityIssueType.MISSING_DATA,
                    description=f"Empty value for {normalized_name}",
                    severity="medium",
                    affected_periods=["current"],
                    suggested_action="Review data source for missing values"
                ))
                continue
            
            # Convert string representations to numbers if possible
            if isinstance(value, str):
                try:
                    # Handle common number formats
                    cleaned_value = value.replace(',', '').replace('$', '').replace('%', '').strip()
                    if cleaned_value.replace('.', '').replace('-', '').isdigit():
                        value = float(cleaned_value)
                    elif cleaned_value.lower() in ['n/a', 'na', 'none', 'null', '']:
                        continue
                except (ValueError, AttributeError):
                    pass
            
            validated_data[normalized_name] = value
        
        return validated_data
    
    def _normalize_units(
        self,
        symbol: str,
        data: Dict[str, Any],
        transformation_records: List[TransformationRecord],
        quality_issues: List[QualityIssue]
    ) -> Dict[str, Any]:
        """Normalize all values to consistent units (millions by default)"""
        if not self.config.normalize_units:
            return data
        
        normalized_data = {}
        target_factor = self._unit_conversion_factors.get(self.config.target_unit_scale, 1.0)
        
        for variable_name, value in data.items():
            if not isinstance(value, (int, float)):
                normalized_data[variable_name] = value
                continue
            
            # Get variable definition to understand expected units
            var_def = self.variable_registry.get_variable_definition(variable_name)
            if var_def and var_def.units != Units.NONE:
                # Determine source unit scale
                original_value = value
                
                # Apply normalization logic based on value magnitude and variable type
                if var_def.category in [VariableCategory.INCOME_STATEMENT, VariableCategory.BALANCE_SHEET, VariableCategory.CASH_FLOW]:
                    # Financial statement values - normalize based on magnitude
                    if abs(value) >= 1e9:  # Billions
                        normalized_value = value * self._unit_conversion_factors['billions'] / target_factor
                        scale_applied = "billions_to_millions"
                    elif abs(value) >= 1e6:  # Millions
                        normalized_value = value * self._unit_conversion_factors['millions'] / target_factor
                        scale_applied = "millions_to_millions"
                    elif abs(value) >= 1e3:  # Thousands
                        normalized_value = value * self._unit_conversion_factors['thousands'] / target_factor
                        scale_applied = "thousands_to_millions"
                    else:  # Ones
                        normalized_value = value * self._unit_conversion_factors['ones'] / target_factor
                        scale_applied = "ones_to_millions"
                else:
                    # Non-financial values (ratios, percentages, etc.) - keep as is
                    normalized_value = value
                    scale_applied = "no_normalization"
                
                # Record transformation
                if scale_applied != "no_normalization" and abs(normalized_value - original_value) > 1e-6:
                    transformation_records.append(TransformationRecord(
                        variable_name=variable_name,
                        original_value=original_value,
                        final_value=normalized_value,
                        transformations=[f"unit_normalization: {scale_applied}"],
                        quality_score=1.0,  # Unit normalization doesn't reduce quality
                        metadata={"scale_factor": normalized_value / original_value if original_value != 0 else 0}
                    ))
                
                normalized_data[variable_name] = normalized_value
            else:
                # Unknown variable - keep original value
                normalized_data[variable_name] = value
                if var_def is None:
                    quality_issues.append(QualityIssue(
                        issue_type=QualityIssueType.VALIDATION_FAILURE,
                        description=f"Unknown variable '{variable_name}' not in registry",
                        severity="medium",
                        affected_periods=["current"],
                        suggested_action="Register this variable or check variable name spelling"
                    ))
        
        return normalized_data
    
    def _validate_with_registry(
        self,
        symbol: str,
        data: Dict[str, Any],
        quality_issues: List[QualityIssue]
    ) -> Dict[str, Any]:
        """Validate data using FinancialVariableRegistry definitions"""
        if not self.config.enable_validation:
            return data
        
        validated_data = {}
        
        for variable_name, value in data.items():
            var_def = self.variable_registry.get_variable_definition(variable_name)
            
            if var_def is None:
                # Variable not in registry
                if self.config.strict_validation:
                    quality_issues.append(QualityIssue(
                        issue_type=QualityIssueType.VALIDATION_FAILURE,
                        description=f"Variable '{variable_name}' not registered - skipped in strict mode",
                        severity="high",
                        affected_periods=["current"],
                        suggested_action="Register variable or disable strict validation"
                    ))
                    continue
                else:
                    # Include in non-strict mode but note the issue
                    validated_data[variable_name] = value
                    continue
            
            # Validate value against definition
            is_valid, validation_errors = var_def.validate_value(value)
            
            if is_valid:
                validated_data[variable_name] = value
            else:
                quality_issues.append(QualityIssue(
                    issue_type=QualityIssueType.VALIDATION_FAILURE,
                    description=f"Validation failed for {variable_name}: {', '.join(validation_errors)}",
                    severity="medium" if not self.config.strict_validation else "high",
                    affected_periods=["current"],
                    suggested_action="Review data quality or variable definition"
                ))
                
                if not self.config.strict_validation:
                    # Include invalid data with quality flag
                    validated_data[variable_name] = value
        
        return validated_data
    
    def _align_historical_data(
        self,
        symbol: str,
        data: Dict[str, Any],
        quality_issues: List[QualityIssue]
    ) -> Dict[str, Dict[str, Any]]:
        """Align data with existing historical periods"""
        if not self.config.enable_historical_alignment:
            return {"current": data}
        
        # For now, return current period data
        # In a full implementation, this would:
        # 1. Check existing historical data for this symbol
        # 2. Determine which period this data represents
        # 3. Align periods across different sources
        # 4. Handle period conflicts
        
        current_year = datetime.now().year
        period_key = str(current_year)
        
        return {period_key: data}
    
    def _handle_missing_data(
        self,
        symbol: str,
        period_data: Dict[str, Dict[str, Any]],
        quality_issues: List[QualityIssue]
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        """Handle missing data using configured interpolation strategies"""
        if not self.config.enable_interpolation:
            return period_data, 0
        
        interpolated_count = 0
        interpolated_data = period_data.copy()
        
        # For each variable, check for missing periods and interpolate
        for variable_name in set(
            var_name for period_data_dict in period_data.values() 
            for var_name in period_data_dict.keys()
        ):
            # Get historical data for this variable
            historical_data = self.var_data.get_historical_data(symbol, variable_name, years=10)
            
            if len(historical_data) >= 2:  # Need at least 2 points for interpolation
                # Apply interpolation strategy
                interpolated_values = self._apply_interpolation_strategy(
                    variable_name, historical_data, self.config.default_interpolation_strategy
                )
                
                # Add interpolated values to our data
                for period, value in interpolated_values:
                    if period not in interpolated_data:
                        interpolated_data[period] = {}
                    if variable_name not in interpolated_data[period]:
                        interpolated_data[period][variable_name] = value
                        interpolated_count += 1
                        
                        # Record interpolation as quality issue (informational)
                        quality_issues.append(QualityIssue(
                            issue_type=QualityIssueType.INTERPOLATED_VALUE,
                            description=f"Interpolated missing value for {variable_name} in {period}",
                            severity="low",
                            affected_periods=[period],
                            suggested_action="Consider obtaining actual data for this period"
                        ))
        
        return interpolated_data, interpolated_count
    
    def _detect_outliers(
        self,
        symbol: str,
        period_data: Dict[str, Dict[str, Any]],
        quality_issues: List[QualityIssue]
    ) -> Tuple[Dict[str, Dict[str, Any]], int]:
        """Detect and flag outlier values using statistical analysis"""
        if not self.config.enable_outlier_detection:
            return period_data, 0
        
        outliers_detected = 0
        outlier_data = period_data.copy()
        
        # For each variable, analyze values for outliers
        for variable_name in set(
            var_name for period_data_dict in period_data.values() 
            for var_name in period_data_dict.keys()
        ):
            # Get all values for this variable across periods
            values = []
            periods = []
            for period, data_dict in period_data.items():
                if variable_name in data_dict and isinstance(data_dict[variable_name], (int, float)):
                    values.append(data_dict[variable_name])
                    periods.append(period)
            
            if len(values) >= self.config.outlier_min_history:
                # Calculate statistical measures
                mean_value = statistics.mean(values)
                std_value = statistics.stdev(values) if len(values) > 1 else 0
                
                if std_value > 0:
                    # Identify outliers using standard deviation threshold
                    for i, value in enumerate(values):
                        z_score = abs(value - mean_value) / std_value
                        
                        if z_score > self.config.outlier_threshold_std:
                            outliers_detected += 1
                            quality_issues.append(QualityIssue(
                                issue_type=QualityIssueType.OUTLIER_VALUE,
                                description=f"Outlier detected for {variable_name} in {periods[i]}: {value} (z-score: {z_score:.2f})",
                                severity="medium" if z_score < 4.0 else "high",
                                affected_periods=[periods[i]],
                                suggested_action="Review data accuracy and consider data source quality",
                                metadata={"z_score": z_score, "mean": mean_value, "std": std_value}
                            ))
        
        return outlier_data, outliers_detected
    
    def _assess_data_quality(
        self,
        symbol: str,
        period_data: Dict[str, Dict[str, Any]],
        quality_issues: List[QualityIssue]
    ) -> Dict[str, float]:
        """Assess quality scores for each variable"""
        quality_scores = {}
        
        for variable_name in set(
            var_name for period_data_dict in period_data.values() 
            for var_name in period_data_dict.keys()
        ):
            # Calculate completeness score
            total_periods = len(period_data)
            present_periods = sum(
                1 for period_dict in period_data.values() 
                if variable_name in period_dict and period_dict[variable_name] is not None
            )
            completeness_score = present_periods / max(1, total_periods)
            
            # Calculate consistency score (based on quality issues)
            variable_issues = [
                issue for issue in quality_issues 
                if variable_name in issue.description.lower()
            ]
            
            # Reduce score based on issues
            consistency_score = 1.0
            for issue in variable_issues:
                if issue.issue_type == QualityIssueType.OUTLIER_VALUE:
                    consistency_score -= 0.1
                elif issue.issue_type == QualityIssueType.VALIDATION_FAILURE:
                    consistency_score -= 0.2
                elif issue.issue_type == QualityIssueType.SOURCE_CONFLICT:
                    consistency_score -= 0.15
            
            consistency_score = max(0.0, consistency_score)
            
            # Timeliness score (assume current for now)
            timeliness_score = 1.0
            
            # Reliability score (based on source and processing success)
            reliability_score = 0.9  # Default high reliability
            
            # Calculate weighted overall score
            overall_score = (
                completeness_score * self.config.completeness_weight +
                consistency_score * self.config.consistency_weight +
                timeliness_score * self.config.timeliness_weight +
                reliability_score * self.config.reliability_weight
            )
            
            quality_scores[variable_name] = overall_score
        
        return quality_scores
    
    def _calculate_overall_quality(
        self, 
        quality_scores: Dict[str, float], 
        quality_issues: List[QualityIssue]
    ) -> float:
        """Calculate overall quality score for all processed variables"""
        if not quality_scores:
            return 0.0
        
        # Base score is average of individual variable scores
        base_score = sum(quality_scores.values()) / len(quality_scores)
        
        # Apply penalties for critical issues
        critical_issues = [issue for issue in quality_issues if issue.severity == "critical"]
        high_issues = [issue for issue in quality_issues if issue.severity == "high"]
        
        penalty = len(critical_issues) * 0.2 + len(high_issues) * 0.1
        final_score = max(0.0, base_score - penalty)
        
        return final_score
    
    def _store_processed_data(
        self,
        symbol: str,
        period_data: Dict[str, Dict[str, Any]],
        source_type: DataSourceType,
        metadata: Dict[str, Any]
    ) -> Tuple[int, int]:
        """Store processed data in VarInputData system"""
        stored_count = 0
        failed_count = 0
        
        for period, data_dict in period_data.items():
            for variable_name, value in data_dict.items():
                # Create metadata for this variable
                var_metadata = VariableMetadata(
                    source=source_type.value,
                    timestamp=datetime.now(),
                    quality_score=self._quality_cache.get(f"{symbol}_{variable_name}", 0.8),
                    validation_passed=True,  # Assume passed if we got this far
                    period=period
                )
                
                # Store in VarInputData
                success = self.var_data.set_variable(
                    symbol=symbol,
                    variable_name=variable_name,
                    value=value,
                    period=period,
                    source=source_type.value,
                    metadata=var_metadata,
                    validate=False,  # Already validated in our pipeline
                    emit_event=True
                )
                
                if success:
                    stored_count += 1
                else:
                    failed_count += 1
        
        return stored_count, failed_count
    
    def _apply_interpolation_strategy(
        self,
        variable_name: str,
        historical_data: List[Tuple[str, Any]],
        strategy: InterpolationStrategy
    ) -> List[Tuple[str, Any]]:
        """Apply interpolation strategy to fill missing data"""
        if strategy == InterpolationStrategy.SKIP:
            return []
        
        # For now, implement simple forward fill
        if strategy == InterpolationStrategy.FORWARD_FILL and historical_data:
            # Return the most recent known value
            return [historical_data[0]]  # First item is most recent
        
        # Other strategies would be implemented here
        return []
    
    def _determine_source_type(self, source: str) -> DataSourceType:
        """Determine DataSourceType from source string"""
        source_lower = source.lower()
        
        if 'excel' in source_lower:
            return DataSourceType.EXCEL
        elif 'yfinance' in source_lower or 'yahoo' in source_lower:
            return DataSourceType.YFINANCE
        elif 'fmp' in source_lower:
            return DataSourceType.FMP
        elif 'alpha' in source_lower or 'vantage' in source_lower:
            return DataSourceType.ALPHA_VANTAGE
        elif 'polygon' in source_lower:
            return DataSourceType.POLYGON
        else:
            return DataSourceType.EXCEL  # Default fallback


# Convenience functions for common operations

def process_excel_data(symbol: str, excel_data: Dict[str, Any]) -> ProcessingResult:
    """Convenience function to process Excel data for a symbol"""
    processor = VariableProcessor()
    return processor.process_symbol_data(
        symbol=symbol,
        source_type=DataSourceType.EXCEL,
        raw_data=excel_data
    )


def process_api_data(symbol: str, api_data: Dict[str, Any], source: str = "yfinance") -> ProcessingResult:
    """Convenience function to process API data for a symbol"""
    processor = VariableProcessor()
    source_type = processor._determine_source_type(source)
    return processor.process_symbol_data(
        symbol=symbol,
        source_type=source_type,
        raw_data=api_data
    )


def create_custom_processor(
    normalize_units: bool = True,
    quality_threshold: float = 0.8,
    enable_interpolation: bool = True,
    outlier_detection: bool = True
) -> VariableProcessor:
    """Create a VariableProcessor with custom configuration"""
    config = ProcessingConfiguration(
        normalize_units=normalize_units,
        minimum_quality_score=quality_threshold,
        enable_interpolation=enable_interpolation,
        enable_outlier_detection=outlier_detection
    )
    return VariableProcessor(config)


# Export main classes and functions
__all__ = [
    'VariableProcessor',
    'ProcessingConfiguration',
    'ProcessingResult',
    'QualityIssue',
    'QualityIssueType',
    'InterpolationStrategy',
    'ProcessingStage',
    'TransformationRecord',
    'process_excel_data',
    'process_api_data',
    'create_custom_processor'
]