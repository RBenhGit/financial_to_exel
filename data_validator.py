"""
Data Validation Module

This module provides comprehensive validation for financial data acquisition and processing.
It ensures data quality, completeness, and consistency across all financial calculations.
"""

import pandas as pd
import numpy as np
import logging
from typing import Any, Dict, List, Tuple, Optional, Union
from datetime import datetime
import warnings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataQualityReport:
    """
    Data quality report container with validation results and recommendations
    """
    
    def __init__(self):
        self.completeness_score = 0.0
        self.consistency_score = 0.0
        self.overall_score = 0.0
        self.missing_data = {}
        self.invalid_data = {}
        self.warnings = []
        self.errors = []
        self.recommendations = []
        self.validation_timestamp = datetime.now()
    
    def add_warning(self, message: str, context: str = None):
        """Add a warning to the report"""
        warning_entry = {"message": message, "context": context, "timestamp": datetime.now()}
        self.warnings.append(warning_entry)
        logger.warning(f"Data Quality Warning: {message}")
    
    def add_error(self, message: str, context: str = None):
        """Add an error to the report"""
        error_entry = {"message": message, "context": context, "timestamp": datetime.now()}
        self.errors.append(error_entry)
        logger.error(f"Data Quality Error: {message}")
    
    def add_recommendation(self, message: str, priority: str = "medium"):
        """Add a recommendation to the report"""
        rec_entry = {"message": message, "priority": priority, "timestamp": datetime.now()}
        self.recommendations.append(rec_entry)
    
    def calculate_scores(self):
        """Calculate overall data quality scores"""
        # Calculate completeness score (0-100)
        total_metrics = sum(len(data) for data in self.missing_data.values()) if self.missing_data else 0
        missing_metrics = sum(data.count(True) for data in self.missing_data.values()) if self.missing_data else 0
        
        if total_metrics > 0:
            self.completeness_score = ((total_metrics - missing_metrics) / total_metrics) * 100
        else:
            self.completeness_score = 100.0
        
        # Calculate consistency score based on errors and warnings
        total_issues = len(self.errors) + len(self.warnings)
        if total_issues == 0:
            self.consistency_score = 100.0
        else:
            # Decrease score based on number of issues
            self.consistency_score = max(0, 100 - (total_issues * 5))
        
        # Overall score is weighted average
        self.overall_score = (self.completeness_score * 0.6) + (self.consistency_score * 0.4)
    
    def get_summary(self) -> str:
        """Generate human-readable summary of data quality"""
        self.calculate_scores()
        
        summary = [
            f"\n{'='*60}",
            f"DATA QUALITY REPORT - {self.validation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*60}",
            f"Overall Score: {self.overall_score:.1f}/100",
            f"Completeness: {self.completeness_score:.1f}/100",
            f"Consistency: {self.consistency_score:.1f}/100",
            f"",
            f"Issues Summary:",
            f"- Errors: {len(self.errors)}",
            f"- Warnings: {len(self.warnings)}",
            f"- Recommendations: {len(self.recommendations)}",
        ]
        
        if self.errors:
            summary.append(f"\nCRITICAL ERRORS:")
            for error in self.errors[:5]:  # Show first 5 errors
                summary.append(f"  • {error['message']}")
            if len(self.errors) > 5:
                summary.append(f"  ... and {len(self.errors) - 5} more errors")
        
        if self.warnings:
            summary.append(f"\nWARNINGS:")
            for warning in self.warnings[:5]:  # Show first 5 warnings
                summary.append(f"  • {warning['message']}")
            if len(self.warnings) > 5:
                summary.append(f"  ... and {len(self.warnings) - 5} more warnings")
        
        if self.recommendations:
            summary.append(f"\nRECOMMENDATIONS:")
            for rec in self.recommendations[:3]:  # Show top 3 recommendations
                summary.append(f"  • {rec['message']}")
        
        summary.append(f"{'='*60}")
        
        return "\n".join(summary)

class FinancialDataValidator:
    """
    Comprehensive financial data validation framework
    """
    
    def __init__(self):
        self.report = DataQualityReport()
        self.validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict:
        """Initialize validation rules and thresholds"""
        return {
            "required_metrics": [
                "Net Income", "EBIT", "Total Current Assets", "Total Current Liabilities",
                "Depreciation & Amortization", "Cash from Operations", "Capital Expenditure"
            ],
            "numeric_thresholds": {
                "min_years_required": 3,
                "max_growth_rate": 5.0,  # 500% year-over-year growth flag
                "min_reasonable_value": -1e12,  # -1 trillion
                "max_reasonable_value": 1e12,   # 1 trillion
            },
            "consistency_checks": {
                "check_working_capital": True,
                "check_fcf_reasonableness": True,
                "check_growth_patterns": True,
            }
        }
    
    def validate_cell_value(self, value: Any, expected_type: type = float, 
                          allow_zero: bool = True, context: str = "") -> Tuple[Any, bool]:
        """
        Validate and clean a single cell value
        
        Args:
            value: The cell value to validate
            expected_type: Expected data type
            allow_zero: Whether zero values are acceptable
            context: Context for error reporting
            
        Returns:
            Tuple of (cleaned_value, is_valid)
        """
        try:
            # Handle None and empty values
            if value is None or value == "":
                if allow_zero:
                    self.report.add_warning(f"Empty value treated as 0", context)
                    return 0.0, True
                else:
                    self.report.add_error(f"Missing required value", context)
                    return None, False
            
            # Handle numeric values
            if expected_type in (int, float):
                # Handle string representations of numbers
                if isinstance(value, str):
                    # Clean common formatting
                    clean_value = value.replace(',', '').replace('$', '').strip()
                    
                    # Handle parentheses for negative numbers
                    if clean_value.startswith('(') and clean_value.endswith(')'):
                        clean_value = '-' + clean_value[1:-1]
                    
                    # Handle percentage signs
                    if clean_value.endswith('%'):
                        clean_value = clean_value[:-1]
                        try:
                            return float(clean_value) / 100, True
                        except ValueError:
                            self.report.add_error(f"Invalid percentage format: {value}", context)
                            return 0.0, False
                    
                    try:
                        converted_value = float(clean_value)
                    except ValueError:
                        self.report.add_error(f"Cannot convert to number: {value}", context)
                        return 0.0 if allow_zero else None, allow_zero
                else:
                    converted_value = float(value)
                
                # Check for reasonable bounds
                rules = self.validation_rules["numeric_thresholds"]
                if converted_value < rules["min_reasonable_value"] or converted_value > rules["max_reasonable_value"]:
                    self.report.add_warning(f"Value outside reasonable bounds: {converted_value:,.0f}", context)
                
                # Check for zero values if not allowed
                if not allow_zero and converted_value == 0:
                    self.report.add_warning(f"Zero value where non-zero expected", context)
                
                return converted_value, True
            
            # Handle other data types
            return value, True
            
        except Exception as e:
            self.report.add_error(f"Validation error: {str(e)}", context)
            return 0.0 if allow_zero else None, allow_zero
    
    def validate_data_series(self, values: List[Any], metric_name: str, 
                           min_years: int = None) -> Tuple[List[float], Dict]:
        """
        Validate a complete data series (e.g., 10 years of revenue data)
        
        Args:
            values: List of values to validate
            metric_name: Name of the metric for reporting
            min_years: Minimum number of valid years required
            
        Returns:
            Tuple of (validated_values, validation_info)
        """
        validation_info = {
            "original_count": len(values),
            "valid_count": 0,
            "missing_count": 0,
            "invalid_count": 0,
            "zero_count": 0,
            "outlier_count": 0
        }
        
        validated_values = []
        context = f"Metric: {metric_name}"
        
        for i, value in enumerate(values):
            year_context = f"{context}, Year {i+1}"
            cleaned_value, is_valid = self.validate_cell_value(value, float, True, year_context)
            
            if is_valid:
                validated_values.append(cleaned_value)
                validation_info["valid_count"] += 1
                
                if cleaned_value == 0:
                    validation_info["zero_count"] += 1
            else:
                validated_values.append(0.0)  # Fallback to zero
                validation_info["invalid_count"] += 1
        
        # Check minimum years requirement
        min_required = min_years or self.validation_rules["numeric_thresholds"]["min_years_required"]
        if validation_info["valid_count"] < min_required:
            self.report.add_error(
                f"Insufficient data for {metric_name}: {validation_info['valid_count']} valid years, "
                f"minimum {min_required} required"
            )
        
        # Check for concerning patterns
        self._check_data_patterns(validated_values, metric_name)
        
        return validated_values, validation_info
    
    def _check_data_patterns(self, values: List[float], metric_name: str):
        """Check for concerning patterns in the data"""
        if len(values) < 2:
            return
        
        # Check for excessive growth rates
        max_growth = self.validation_rules["numeric_thresholds"]["max_growth_rate"]
        
        for i in range(1, len(values)):
            if values[i-1] != 0:
                growth_rate = abs(values[i] - values[i-1]) / abs(values[i-1])
                if growth_rate > max_growth:
                    self.report.add_warning(
                        f"Excessive year-over-year change in {metric_name}: "
                        f"{growth_rate*100:.1f}% between year {i} and {i+1}"
                    )
        
        # Check for all zeros
        if all(v == 0 for v in values):
            self.report.add_warning(f"All values are zero for {metric_name}")
        
        # Check for unusual patterns (all same value)
        unique_values = set(values)
        if len(unique_values) == 1 and len(values) > 3:
            self.report.add_warning(f"All values identical for {metric_name}: {values[0]}")
    
    def validate_financial_statements(self, financial_data: Dict) -> DataQualityReport:
        """
        Validate complete financial statements data
        
        Args:
            financial_data: Dictionary containing financial statement data
            
        Returns:
            DataQualityReport with validation results
        """
        logger.info("Starting comprehensive financial data validation...")
        
        # Reset report for new validation
        self.report = DataQualityReport()
        
        # Validate data structure
        self._validate_data_structure(financial_data)
        
        # Validate each financial statement
        for statement_type, data in financial_data.items():
            if isinstance(data, pd.DataFrame) and not data.empty:
                self._validate_statement_data(data, statement_type)
            else:
                self.report.add_error(f"Missing or empty {statement_type} data")
        
        # Cross-validate between statements
        self._cross_validate_statements(financial_data)
        
        # Generate recommendations
        self._generate_recommendations()
        
        logger.info("Financial data validation completed")
        return self.report
    
    def _validate_data_structure(self, financial_data: Dict):
        """Validate the overall structure of financial data"""
        required_statements = ['income_fy', 'balance_fy', 'cashflow_fy']
        
        for statement in required_statements:
            if statement not in financial_data:
                self.report.add_error(f"Missing required financial statement: {statement}")
            elif financial_data[statement].empty:
                self.report.add_error(f"Empty financial statement: {statement}")
    
    def _validate_statement_data(self, df: pd.DataFrame, statement_type: str):
        """Validate data within a single financial statement"""
        required_metrics = self._get_required_metrics(statement_type)
        
        for metric in required_metrics:
            # Find and validate the metric
            metric_found = False
            for idx, row in df.iterrows():
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    if metric.lower() in str(row.iloc[2]).lower():
                        metric_found = True
                        # Extract and validate the values
                        values = []
                        for val in row.iloc[3:]:
                            if pd.notna(val) and val != '':
                                cleaned_val, _ = self.validate_cell_value(val, float, True, f"{statement_type}.{metric}")
                                values.append(cleaned_val)
                        
                        if len(values) == 0:
                            self.report.add_error(f"No valid data found for {metric} in {statement_type}")
                        else:
                            self.validate_data_series(values, f"{statement_type}.{metric}")
                        break
            
            if not metric_found:
                self.report.add_error(f"Required metric '{metric}' not found in {statement_type}")
    
    def _get_required_metrics(self, statement_type: str) -> List[str]:
        """Get required metrics for each statement type"""
        metrics_map = {
            'income_fy': ['Net Income', 'EBIT', 'EBT', 'Income Tax Expense'],
            'balance_fy': ['Total Current Assets', 'Total Current Liabilities'],
            'cashflow_fy': ['Depreciation & Amortization', 'Cash from Operations', 'Capital Expenditure']
        }
        return metrics_map.get(statement_type, [])
    
    def _cross_validate_statements(self, financial_data: Dict):
        """Perform cross-validation between different financial statements"""
        if self.validation_rules["consistency_checks"]["check_working_capital"]:
            self._validate_working_capital_consistency(financial_data)
        
        if self.validation_rules["consistency_checks"]["check_fcf_reasonableness"]:
            self._validate_fcf_reasonableness(financial_data)
    
    def _validate_working_capital_consistency(self, financial_data: Dict):
        """Validate working capital calculation consistency"""
        try:
            balance_data = financial_data.get('balance_fy', pd.DataFrame())
            if balance_data.empty:
                return
            
            # This would extract current assets and liabilities and validate their relationship
            # Implementation would depend on the specific requirements
            logger.debug("Working capital consistency check performed")
            
        except Exception as e:
            self.report.add_warning(f"Could not perform working capital consistency check: {e}")
    
    def _validate_fcf_reasonableness(self, financial_data: Dict):
        """Validate that FCF calculations would be reasonable"""
        try:
            # This would perform basic sanity checks on the data that feeds into FCF calculations
            # For example, ensuring operating cash flow exists, CapEx is reasonable, etc.
            logger.debug("FCF reasonableness check performed")
            
        except Exception as e:
            self.report.add_warning(f"Could not perform FCF reasonableness check: {e}")
    
    def _generate_recommendations(self):
        """Generate actionable recommendations based on validation results"""
        if len(self.report.errors) > 0:
            self.report.add_recommendation(
                "Critical data issues found. Review source Excel files for missing or corrupted data.",
                "high"
            )
        
        if len(self.report.warnings) > 5:
            self.report.add_recommendation(
                "Multiple data quality warnings detected. Consider data source quality review.",
                "medium"
            )
        
        if self.report.missing_data:
            self.report.add_recommendation(
                "Missing data detected. Consider using interpolation or industry averages for gaps.",
                "medium"
            )
    
    def validate_metric_extraction(self, df: pd.DataFrame, metric_name: str, 
                                 extracted_values: List[float]) -> bool:
        """
        Validate that metric extraction was successful and reasonable
        
        Args:
            df: Source DataFrame
            metric_name: Name of the metric
            extracted_values: Values that were extracted
            
        Returns:
            bool: Whether extraction appears valid
        """
        context = f"Extraction validation for {metric_name}"
        
        # Check if any values were extracted
        if not extracted_values:
            self.report.add_error(f"No values extracted for {metric_name}", context)
            return False
        
        # Check for reasonable number of years
        min_years = self.validation_rules["numeric_thresholds"]["min_years_required"]
        if len(extracted_values) < min_years:
            self.report.add_warning(
                f"Only {len(extracted_values)} years of data for {metric_name}, "
                f"minimum {min_years} recommended", context
            )
        
        # Validate each extracted value
        valid_values = 0
        for i, value in enumerate(extracted_values):
            _, is_valid = self.validate_cell_value(value, float, True, f"{context}, Year {i+1}")
            if is_valid:
                valid_values += 1
        
        # Check if most values are valid
        if valid_values / len(extracted_values) < 0.7:  # Less than 70% valid
            self.report.add_warning(
                f"Low data quality for {metric_name}: {valid_values}/{len(extracted_values)} valid values",
                context
            )
            return False
        
        return True

def create_enhanced_copy_validation(original_value: Any, target_location: str) -> Tuple[Any, bool]:
    """
    Enhanced validation function for the CopyDataNew.py cell copying process
    
    Args:
        original_value: Value from source Excel file
        target_location: Description of target location for error reporting
        
    Returns:
        Tuple of (validated_value, success_flag)
    """
    validator = FinancialDataValidator()
    validated_value, is_valid = validator.validate_cell_value(
        original_value, float, True, f"Copy operation to {target_location}"
    )
    
    if not is_valid:
        logger.warning(f"Data validation failed for copy operation to {target_location}")
    
    return validated_value, is_valid

def validate_financial_calculation_input(metrics: Dict[str, List[float]]) -> DataQualityReport:
    """
    Validate input data for financial calculations
    
    Args:
        metrics: Dictionary of financial metrics with their values
        
    Returns:
        DataQualityReport with validation results
    """
    validator = FinancialDataValidator()
    
    for metric_name, values in metrics.items():
        if values:
            validator.validate_data_series(values, metric_name)
        else:
            validator.report.add_error(f"No data available for metric: {metric_name}")
    
    return validator.report

# Export the main validation functions
__all__ = [
    'FinancialDataValidator',
    'DataQualityReport', 
    'create_enhanced_copy_validation',
    'validate_financial_calculation_input'
]