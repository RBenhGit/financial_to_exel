"""
FCF Date Correlation Module

This module provides enhanced data structures and utilities for correlating
FCF calculation values with their corresponding report dates.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FCFDataPoint:
    """
    Individual FCF data point with complete correlation metadata
    """
    value: float
    report_date: str  # Date in YYYY-MM-DD format
    source_type: str  # 'FY' or 'LTM'
    source_file: str  # Path to source Excel file
    calculation_method: str = "standard"  # Method used for calculation
    
    def __post_init__(self):
        """Validate the data point"""
        if not isinstance(self.value, (int, float)):
            raise ValueError(f"FCF value must be numeric, got {type(self.value)}")
        
        # Validate date format
        try:
            datetime.strptime(self.report_date, "%Y-%m-%d")
        except ValueError:
            logger.warning(f"Invalid date format: {self.report_date}, should be YYYY-MM-DD")


@dataclass 
class CorrelatedFCFResults:
    """
    Enhanced FCF results structure with complete date correlation
    """
    fcf_type: str  # 'FCFF', 'FCFE', or 'LFCF'
    data_points: List[FCFDataPoint] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize metadata if not provided"""
        if not self.metadata:
            self.metadata = {
                'calculation_date': datetime.now().isoformat(),
                'correlation_validated': False,
                'fy_ltm_pattern': False,
                'total_points': len(self.data_points)
            }
    
    @property
    def values(self) -> List[float]:
        """Get FCF values as a simple list"""
        return [point.value for point in self.data_points]
    
    @property 
    def dates(self) -> List[str]:
        """Get report dates as a simple list"""
        return [point.report_date for point in self.data_points]
    
    @property
    def sources(self) -> List[str]:
        """Get source types as a simple list"""
        return [point.source_type for point in self.data_points]
    
    @property
    def source_files(self) -> List[str]:
        """Get source files as a simple list"""
        return [point.source_file for point in self.data_points]
    
    def add_data_point(self, value: float, report_date: str, source_type: str, 
                       source_file: str, calculation_method: str = "standard") -> None:
        """Add a new data point to the FCF results"""
        try:
            data_point = FCFDataPoint(
                value=value,
                report_date=report_date,
                source_type=source_type,
                source_file=source_file,
                calculation_method=calculation_method
            )
            self.data_points.append(data_point)
            self.metadata['total_points'] = len(self.data_points)
            
            # Check for FY+LTM pattern
            sources = self.sources
            if len(sources) > 1 and sources[-1] == 'LTM' and all(s == 'FY' for s in sources[:-1]):
                self.metadata['fy_ltm_pattern'] = True
                
        except Exception as e:
            logger.error(f"Error adding FCF data point: {e}")
            raise
    
    def validate_correlation(self) -> bool:
        """Validate that all data points have proper correlation"""
        try:
            if not self.data_points:
                return False
            
            # Check that all data points have valid dates and values
            for i, point in enumerate(self.data_points):
                if not isinstance(point.value, (int, float)):
                    logger.warning(f"Invalid value at index {i}: {point.value}")
                    return False
                
                if not point.report_date or point.report_date == "Unknown":
                    logger.warning(f"Missing or invalid date at index {i}: {point.report_date}")
                    return False
                
                if not point.source_type:
                    logger.warning(f"Missing source type at index {i}")
                    return False
            
            # Check for chronological order (dates should be in ascending order)
            dates = [datetime.strptime(point.report_date, "%Y-%m-%d") for point in self.data_points]
            if dates != sorted(dates):
                logger.warning("FCF data points are not in chronological order")
            
            self.metadata['correlation_validated'] = True
            return True
            
        except Exception as e:
            logger.error(f"Error validating FCF correlation: {e}")
            self.metadata['correlation_validated'] = False
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format for compatibility with existing code"""
        return {
            'values': self.values,
            'dates': self.dates,
            'sources': self.sources,
            'source_files': self.source_files,
            'metadata': self.metadata.copy()
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame for analysis"""
        data = []
        for point in self.data_points:
            data.append({
                'fcf_type': self.fcf_type,
                'value': point.value,
                'report_date': point.report_date,
                'source_type': point.source_type,
                'source_file': point.source_file,
                'calculation_method': point.calculation_method
            })
        return pd.DataFrame(data)


@dataclass
class ComprehensiveFCFResults:
    """
    Complete FCF results for all types with date correlation
    """
    results: Dict[str, CorrelatedFCFResults] = field(default_factory=dict)
    company_info: Dict[str, Any] = field(default_factory=dict)
    global_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize global metadata"""
        if not self.global_metadata:
            self.global_metadata = {
                'calculation_timestamp': datetime.now().isoformat(),
                'fcf_types_calculated': list(self.results.keys()),
                'total_data_points': sum(len(fcf.data_points) for fcf in self.results.values()),
                'correlation_status': 'pending'
            }
    
    def add_fcf_results(self, fcf_type: str, correlated_results: CorrelatedFCFResults) -> None:
        """Add FCF results for a specific type"""
        self.results[fcf_type] = correlated_results
        self._update_global_metadata()
    
    def get_fcf_results(self, fcf_type: str) -> Optional[CorrelatedFCFResults]:
        """Get FCF results for a specific type"""
        return self.results.get(fcf_type)
    
    def validate_all_correlations(self) -> bool:
        """Validate correlations for all FCF types"""
        all_valid = True
        for fcf_type, fcf_results in self.results.items():
            if not fcf_results.validate_correlation():
                all_valid = False
                logger.warning(f"Correlation validation failed for {fcf_type}")
        
        self.global_metadata['correlation_status'] = 'valid' if all_valid else 'invalid'
        return all_valid
    
    def _update_global_metadata(self):
        """Update global metadata when results change"""
        self.global_metadata.update({
            'fcf_types_calculated': list(self.results.keys()),
            'total_data_points': sum(len(fcf.data_points) for fcf in self.results.values()),
            'last_updated': datetime.now().isoformat()
        })
    
    def to_legacy_format(self) -> Dict[str, Any]:
        """Convert to legacy format for backward compatibility"""
        legacy_results = {}
        
        # Convert each FCF type to legacy format
        for fcf_type, fcf_results in self.results.items():
            legacy_results[fcf_type] = fcf_results.to_dict()
        
        # Add metadata
        legacy_results['metadata'] = self.global_metadata.copy()
        legacy_results['company_info'] = self.company_info.copy()
        
        return legacy_results
    
    def get_correlated_dates_summary(self) -> Dict[str, Any]:
        """Get summary of date correlations across all FCF types"""
        summary = {
            'common_date_pattern': None,
            'date_ranges': {},
            'source_type_distribution': {},
            'correlation_quality': 'unknown'
        }
        
        if not self.results:
            return summary
        
        try:
            # Get dates from first FCF type as reference
            first_fcf_type = list(self.results.keys())[0]
            reference_dates = self.results[first_fcf_type].dates
            
            # Check if all FCF types have the same dates
            all_same_dates = True
            for fcf_type, fcf_results in self.results.items():
                if fcf_results.dates != reference_dates:
                    all_same_dates = False
                    break
            
            summary['common_date_pattern'] = all_same_dates
            
            # Get date ranges for each FCF type
            for fcf_type, fcf_results in self.results.items():
                if fcf_results.dates:
                    summary['date_ranges'][fcf_type] = {
                        'start_date': min(fcf_results.dates),
                        'end_date': max(fcf_results.dates),
                        'total_periods': len(fcf_results.dates)
                    }
            
            # Analyze source type distribution
            all_sources = []
            for fcf_results in self.results.values():
                all_sources.extend(fcf_results.sources)
            
            source_counts = {}
            for source in all_sources:
                source_counts[source] = source_counts.get(source, 0) + 1
            summary['source_type_distribution'] = source_counts
            
            # Determine correlation quality
            if all_same_dates and all(fcf.metadata.get('correlation_validated', False) 
                                    for fcf in self.results.values()):
                summary['correlation_quality'] = 'excellent'
            elif all_same_dates:
                summary['correlation_quality'] = 'good'
            else:
                summary['correlation_quality'] = 'needs_attention'
                
        except Exception as e:
            logger.error(f"Error creating date correlation summary: {e}")
            summary['correlation_quality'] = 'error'
            summary['error'] = str(e)
        
        return summary


def create_correlated_fcf_from_legacy(fcf_type: str, values: List[float], 
                                    dates: List[str], sources: List[str] = None, 
                                    source_files: List[str] = None) -> CorrelatedFCFResults:
    """
    Create CorrelatedFCFResults from legacy format data
    
    Args:
        fcf_type: Type of FCF ('FCFF', 'FCFE', 'LFCF')
        values: List of FCF values
        dates: List of report dates
        sources: List of source types (optional)
        source_files: List of source files (optional)
    
    Returns:
        CorrelatedFCFResults: Enhanced FCF results structure
    """
    try:
        # Ensure all lists are the same length
        max_length = len(values)
        
        if len(dates) != max_length:
            logger.warning(f"Date list length ({len(dates)}) doesn't match values length ({max_length})")
            dates = dates[:max_length] + ['Unknown'] * (max_length - len(dates))
        
        if sources is None:
            sources = ['Unknown'] * max_length
        elif len(sources) != max_length:
            sources = sources[:max_length] + ['Unknown'] * (max_length - len(sources))
        
        if source_files is None:
            source_files = ['Unknown'] * max_length
        elif len(source_files) != max_length:
            source_files = source_files[:max_length] + ['Unknown'] * (max_length - len(source_files))
        
        # Create correlated results
        correlated_results = CorrelatedFCFResults(fcf_type=fcf_type)
        
        for i in range(max_length):
            correlated_results.add_data_point(
                value=values[i],
                report_date=dates[i],
                source_type=sources[i],
                source_file=source_files[i]
            )
        
        # Validate the correlation
        correlated_results.validate_correlation()
        
        return correlated_results
        
    except Exception as e:
        logger.error(f"Error creating correlated FCF from legacy data: {e}")
        raise