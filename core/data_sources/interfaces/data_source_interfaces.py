"""
Data Source Interfaces
=====================

Abstract interfaces and base classes for data sources in the Universal Data Registry.
This module defines the contracts that all data sources must implement to integrate
with the centralized data management system.

Classes:
    DataSourceInterface: Abstract base class for all data sources
    ExcelDataSource: Interface for Excel-based financial data
    APIDataSource: Base class for API-based data sources
    DataSourceFactory: Factory for creating data source instances
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass

from ...data_processing.universal_data_registry import (
    DataRequest, DataResponse, DataLineage, DataSourceType, ValidationLevel
)

logger = logging.getLogger(__name__)

class DataSourceInterface(ABC):
    """
    Abstract base class that all data sources must implement.
    
    This interface ensures consistent behavior across all data sources
    and provides the contract for integration with the Universal Data Registry.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize data source with configuration"""
        self.config = config or {}
        self.is_available = True
        self.last_error = None
        self.request_count = 0
        self.success_count = 0
    
    @abstractmethod
    def fetch_data(self, request: DataRequest) -> DataResponse:
        """
        Fetch data according to the request specification.
        
        Args:
            request: DataRequest containing the data specification
            
        Returns:
            DataResponse with the requested data and metadata
            
        Raises:
            Exception: If data cannot be fetched
        """
        pass
    
    @abstractmethod
    def supports_request(self, request: DataRequest) -> bool:
        """
        Check if this data source can handle the given request.
        
        Args:
            request: DataRequest to check
            
        Returns:
            bool: True if this source can handle the request
        """
        pass
    
    @abstractmethod
    def get_source_type(self) -> DataSourceType:
        """Return the type of this data source"""
        pass
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of this data source.
        
        Returns:
            Dict containing health status information
        """
        success_rate = 0.0
        if self.request_count > 0:
            success_rate = self.success_count / self.request_count
        
        return {
            'available': self.is_available,
            'request_count': self.request_count,
            'success_count': self.success_count,
            'success_rate': success_rate,
            'last_error': str(self.last_error) if self.last_error else None
        }
    
    def _update_metrics(self, success: bool, error: Exception = None):
        """Update internal metrics for monitoring"""
        self.request_count += 1
        if success:
            self.success_count += 1
            self.last_error = None
        else:
            self.last_error = error
            # Mark as unavailable if too many consecutive failures
            if self.request_count > 10 and (self.success_count / self.request_count) < 0.1:
                self.is_available = False


class ExcelDataSource(DataSourceInterface):
    """
    Data source for Excel-based financial statements.
    
    This class handles loading and processing financial data from Excel files,
    providing standardized access to historical financial statements.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.company_folder = self.config.get('company_folder', './data')
        self.excel_files_cache = {}
    
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.EXCEL
    
    def supports_request(self, request: DataRequest) -> bool:
        """Check if Excel data source can handle the request"""
        supported_types = ['financial_statements', 'historical_ratios']
        return (
            request.data_type in supported_types and
            request.period in ['annual', 'quarterly'] and
            self._excel_file_exists(request.symbol)
        )
    
    def _excel_file_exists(self, symbol: str) -> bool:
        """Check if Excel file exists for the given symbol"""
        company_dir = os.path.join(self.company_folder, symbol)
        if not os.path.exists(company_dir):
            return False
        
        # Look for common Excel file patterns
        excel_patterns = [
            f"{symbol}_financial_statements.xlsx",
            f"{symbol}_financials.xlsx",
            "financial_statements.xlsx",
            "financials.xlsx"
        ]
        
        for pattern in excel_patterns:
            if os.path.exists(os.path.join(company_dir, pattern)):
                return True
        
        return False
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        """
        Fetch financial data from Excel files.
        
        Args:
            request: DataRequest specifying what data to fetch
            
        Returns:
            DataResponse containing the Excel data
        """
        try:
            if not self.supports_request(request):
                raise ValueError(f"Request not supported: {request}")
            
            # Import here to avoid circular dependencies
            from core.analysis.engines.financial_calculations import FinancialCalculator
            
            # Create temporary calculator to load Excel data
            calculator = FinancialCalculator(
                company_folder=os.path.join(self.company_folder, request.symbol),
                symbol=request.symbol
            )
            
            # Load financial statements
            calculator.load_financial_statements()
            
            # Extract the requested data type
            data = self._extract_data_by_type(calculator, request)
            
            # Create lineage information
            lineage = DataLineage(
                source_type=self.get_source_type(),
                source_details=f"Excel file for {request.symbol}",
                timestamp=datetime.now(),
                quality_score=self._calculate_quality_score(data)
            )
            
            response = DataResponse(
                data=data,
                source=self.get_source_type(),
                timestamp=datetime.now(),
                quality_score=lineage.quality_score,
                cache_hit=False,
                lineage=lineage
            )
            
            self._update_metrics(True)
            return response
            
        except Exception as e:
            self._update_metrics(False, e)
            raise e
    
    def _extract_data_by_type(self, calculator, request: DataRequest) -> Dict[str, Any]:
        """Extract specific data type from the financial calculator"""
        if request.data_type == 'financial_statements':
            return {
                'income_statement': getattr(calculator, 'income_statement_data', {}),
                'balance_sheet': getattr(calculator, 'balance_sheet_data', {}),
                'cash_flow': getattr(calculator, 'cash_flow_data', {}),
                'dates': getattr(calculator, 'data_point_dates', {})
            }
        elif request.data_type == 'historical_ratios':
            # Calculate basic ratios if available
            return self._calculate_basic_ratios(calculator)
        else:
            raise ValueError(f"Unsupported data type: {request.data_type}")
    
    def _calculate_basic_ratios(self, calculator) -> Dict[str, Any]:
        """Calculate basic financial ratios from loaded data"""
        # This would implement ratio calculations
        # For now, return placeholder
        return {
            'profitability_ratios': {},
            'liquidity_ratios': {},
            'leverage_ratios': {},
            'efficiency_ratios': {}
        }
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate data quality score based on completeness and consistency"""
        if not data:
            return 0.0
        
        # Simple quality scoring based on data completeness
        total_fields = 0
        filled_fields = 0
        
        for section, section_data in data.items():
            if isinstance(section_data, dict):
                for field, values in section_data.items():
                    total_fields += 1
                    if values and any(v is not None for v in (values if isinstance(values, list) else [values])):
                        filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0


class APIDataSource(DataSourceInterface):
    """
    Base class for API-based data sources.
    
    This class provides common functionality for all API data sources,
    including rate limiting, error handling, and response standardization.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.base_url = self.config.get('base_url', '')
        self.rate_limit = self.config.get('rate_limit', 100)  # requests per hour
        self.timeout = self.config.get('timeout', 30)
        
        # Rate limiting tracking
        self.request_timestamps = []
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = datetime.now()
        # Remove timestamps older than 1 hour
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if (now - ts).seconds < 3600
        ]
        
        return len(self.request_timestamps) < self.rate_limit
    
    def _record_request(self):
        """Record a new API request for rate limiting"""
        self.request_timestamps.append(datetime.now())
    
    @abstractmethod
    def _make_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make the actual API call. Must be implemented by subclasses.
        
        Args:
            endpoint: API endpoint to call
            params: Parameters for the API call
            
        Returns:
            Raw API response data
        """
        pass
    
    def _standardize_response(self, raw_data: Dict[str, Any], request: DataRequest) -> Dict[str, Any]:
        """
        Standardize API response format. Can be overridden by subclasses.
        
        Args:
            raw_data: Raw API response
            request: Original data request
            
        Returns:
            Standardized data format
        """
        return raw_data
    
    def _calculate_api_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate quality score for API data"""
        if not data:
            return 0.0
        
        # Basic quality assessment
        score = 0.8  # Base score for API data
        
        # Check for common error indicators
        if 'error' in data or 'Error' in str(data):
            score -= 0.5
        
        # Check data completeness
        if isinstance(data, dict) and len(data) > 0:
            score += 0.2
        
        return min(1.0, max(0.0, score))


class YahooFinanceDataSource(APIDataSource):
    """Yahoo Finance API data source implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
    
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.YFINANCE
    
    def supports_request(self, request: DataRequest) -> bool:
        """Check if Yahoo Finance can handle the request"""
        supported_types = ['market_data', 'stock_price', 'historical_prices']
        return request.data_type in supported_types
    
    def _make_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make Yahoo Finance API call"""
        import requests
        
        if not self._check_rate_limit():
            raise Exception("Rate limit exceeded for Yahoo Finance API")
        
        self._record_request()
        
        try:
            response = requests.get(endpoint, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise Exception(f"Yahoo Finance API error: {str(e)}")
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        """Fetch data from Yahoo Finance API"""
        try:
            if not self.supports_request(request):
                raise ValueError(f"Request not supported: {request}")
            
            # Build API endpoint and parameters
            endpoint = f"{self.base_url}{request.symbol}"
            params = {
                'interval': self._map_period_to_interval(request.period),
                'range': request.additional_params.get('range', '1y')
            }
            
            # Make API call
            raw_data = self._make_api_call(endpoint, params)
            
            # Standardize response
            standardized_data = self._standardize_response(raw_data, request)
            
            # Create lineage
            lineage = DataLineage(
                source_type=self.get_source_type(),
                source_details=f"Yahoo Finance API for {request.symbol}",
                timestamp=datetime.now(),
                quality_score=self._calculate_api_quality_score(standardized_data)
            )
            
            response = DataResponse(
                data=standardized_data,
                source=self.get_source_type(),
                timestamp=datetime.now(),
                quality_score=lineage.quality_score,
                cache_hit=False,
                lineage=lineage
            )
            
            self._update_metrics(True)
            return response
            
        except Exception as e:
            self._update_metrics(False, e)
            raise e
    
    def _map_period_to_interval(self, period: str) -> str:
        """Map request period to Yahoo Finance interval"""
        mapping = {
            'daily': '1d',
            'weekly': '1wk',
            'monthly': '1mo',
            'quarterly': '3mo',
            'yearly': '1y'
        }
        return mapping.get(period, '1d')


class DataSourceFactory:
    """
    Factory class for creating data source instances.
    
    This factory provides a centralized way to create and configure
    data source instances based on configuration and requirements.
    """
    
    @staticmethod
    def create_data_source(source_type: DataSourceType, config: Dict[str, Any] = None) -> DataSourceInterface:
        """
        Create a data source instance of the specified type.
        
        Args:
            source_type: Type of data source to create
            config: Configuration for the data source
            
        Returns:
            Configured data source instance
            
        Raises:
            ValueError: If source type is not supported
        """
        config = config or {}
        
        if source_type == DataSourceType.EXCEL:
            return ExcelDataSource(config)
        elif source_type == DataSourceType.YFINANCE:
            return YahooFinanceDataSource(config)
        elif source_type == DataSourceType.FINANCIAL_MODELING_PREP:
            return FMPDataSource(config)
        elif source_type == DataSourceType.ALPHA_VANTAGE:
            return AlphaVantageDataSource(config)
        elif source_type == DataSourceType.POLYGON:
            return PolygonDataSource(config)
        else:
            raise ValueError(f"Unsupported data source type: {source_type}")
    
    @staticmethod
    def create_all_sources(config: Dict[str, Any] = None) -> Dict[DataSourceType, DataSourceInterface]:
        """
        Create instances of all available data sources.
        
        Args:
            config: Global configuration containing source-specific configs
            
        Returns:
            Dictionary mapping source types to instances
        """
        config = config or {}
        sources = {}
        
        # Define available source types
        available_types = [
            DataSourceType.EXCEL,
            DataSourceType.YFINANCE,
            DataSourceType.FINANCIAL_MODELING_PREP,
            DataSourceType.ALPHA_VANTAGE,
            DataSourceType.POLYGON
        ]
        
        for source_type in available_types:
            try:
                source_config = config.get(source_type.value, {})
                if source_config.get('enabled', True):
                    source = DataSourceFactory.create_data_source(source_type, source_config)
                    sources[source_type] = source
            except Exception as e:
                logger.warning(f"Failed to create data source {source_type}: {e}")
        
        return sources


# Placeholder implementations for other API sources
class FMPDataSource(APIDataSource):
    """Financial Modeling Prep API data source"""
    
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.FINANCIAL_MODELING_PREP
    
    def supports_request(self, request: DataRequest) -> bool:
        return request.data_type in ['financial_statements', 'ratios', 'market_data']
    
    def _make_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder implementation
        raise NotImplementedError("FMP API implementation pending")
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        # Placeholder implementation
        raise NotImplementedError("FMP data fetching implementation pending")


class AlphaVantageDataSource(APIDataSource):
    """Alpha Vantage API data source"""
    
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.ALPHA_VANTAGE
    
    def supports_request(self, request: DataRequest) -> bool:
        return request.data_type in ['market_data', 'fundamentals']
    
    def _make_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder implementation
        raise NotImplementedError("Alpha Vantage API implementation pending")
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        # Placeholder implementation
        raise NotImplementedError("Alpha Vantage data fetching implementation pending")


class PolygonDataSource(APIDataSource):
    """Polygon.io API data source"""
    
    def get_source_type(self) -> DataSourceType:
        return DataSourceType.POLYGON
    
    def supports_request(self, request: DataRequest) -> bool:
        return request.data_type in ['market_data', 'stock_price']
    
    def _make_api_call(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder implementation
        raise NotImplementedError("Polygon API implementation pending")
    
    def fetch_data(self, request: DataRequest) -> DataResponse:
        # Placeholder implementation
        raise NotImplementedError("Polygon data fetching implementation pending")


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Create data sources using factory
    sources = DataSourceFactory.create_all_sources({
        'excel': {'company_folder': './data'},
        'api_yahoo': {'enabled': True}
    })
    
    print(f"Created {len(sources)} data sources:")
    for source_type, source in sources.items():
        print(f"  - {source_type}: {type(source).__name__}")
        print(f"    Health: {source.health_check()}")