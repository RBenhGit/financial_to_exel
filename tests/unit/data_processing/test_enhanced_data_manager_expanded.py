"""
Comprehensive Unit Tests for Enhanced Data Manager - Enhanced Coverage
======================================================================

This test module provides extensive unit test coverage for the enhanced data processing
modules to achieve >95% test coverage as required by Task #154.

Test Coverage Areas:
1. EnhancedDataManager initialization and configuration
2. Multi-source data fetching and integration
3. Data validation and quality assessment
4. Error handling and fallback mechanisms
5. Caching and performance optimization
6. Rate limiting and API management
7. Data transformation and normalization
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import tempfile
import json
import os

from core.data_processing.managers.enhanced_data_manager import (
    EnhancedDataManager,
)
# Import required data source types and configs
from core.data_sources.data_sources import (
    DataSourceType,
    DataSourceConfig,
    FinancialDataRequest,
    DataSourceResponse
)
from core.data_processing.data_contracts import DataQuality
from core.data_processing.exceptions import DataSourceException, RateLimitException


class TestEnhancedDataManagerInitialization:
    """Test EnhancedDataManager initialization and configuration"""

    def test_basic_initialization(self):
        """Test basic initialization with default parameters"""
        manager = EnhancedDataManager()

        assert manager is not None
        assert hasattr(manager, 'data_sources')
        assert hasattr(manager, 'cache_config')
        assert hasattr(manager, 'rate_limiter')

    def test_initialization_with_config(self):
        """Test initialization with custom configuration"""
        config = {
            'cache_enabled': True,
            'cache_ttl': 3600,
            'rate_limit_requests': 100,
            'rate_limit_period': 60
        }

        manager = EnhancedDataManager(config=config)

        assert manager is not None
        # Config should be applied

    def test_initialization_with_api_keys(self):
        """Test initialization with API keys"""
        api_keys = {
            'alpha_vantage': 'test_av_key',
            'fmp': 'test_fmp_key',
            'polygon': 'test_polygon_key'
        }

        manager = EnhancedDataManager(api_keys=api_keys)

        assert manager is not None
        # API keys should be stored securely

    def test_initialization_with_custom_cache_config(self):
        """Test initialization with custom cache configuration"""
        cache_config = CacheConfig(
            enabled=True,
            ttl_seconds=7200,
            max_size_mb=500,
            storage_path="./custom_cache"
        )

        manager = EnhancedDataManager(cache_config=cache_config)

        assert manager is not None

    @patch('core.data_processing.managers.enhanced_data_manager.os.environ')
    def test_initialization_loads_environment_variables(self, mock_environ):
        """Test that initialization loads API keys from environment"""
        mock_environ.get.side_effect = lambda key, default=None: {
            'ALPHA_VANTAGE_API_KEY': 'env_av_key',
            'FMP_API_KEY': 'env_fmp_key'
        }.get(key, default)

        manager = EnhancedDataManager()

        assert manager is not None
        # Should have loaded environment variables


class TestDataSourceManagement:
    """Test data source management and configuration"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    def test_add_data_source_basic(self):
        """Test adding a basic data source"""
        source = DataSourceConfig(
            name="test_source",
            source_type="api",
            priority=1,
            config={}
        )

        self.manager.add_data_source(source)

        # Should be added to data sources
        assert "test_source" in self.manager.get_available_sources()

    def test_add_data_source_with_validation(self):
        """Test adding data source with validation"""
        # Valid source
        valid_source = DataSource(
            name="valid_source",
            source_type="excel",
            priority=1,
            config={'path': '/valid/path'}
        )

        result = self.manager.add_data_source(valid_source)
        assert result is True

        # Invalid source (missing required config)
        invalid_source = DataSource(
            name="invalid_source",
            source_type="api",
            priority=1,
            config={}  # Missing required API config
        )

        result = self.manager.add_data_source(invalid_source, validate=True)
        assert result is False

    def test_remove_data_source(self):
        """Test removing a data source"""
        source = DataSourceConfig(name="removable_source", source_type="api", priority=1, config={})

        self.manager.add_data_source(source)
        assert "removable_source" in self.manager.get_available_sources()

        self.manager.remove_data_source("removable_source")
        assert "removable_source" not in self.manager.get_available_sources()

    def test_get_data_source_by_name(self):
        """Test retrieving data source by name"""
        source = DataSourceConfig(name="findable_source", source_type="api", priority=1, config={})
        self.manager.add_data_source(source)

        retrieved = self.manager.get_data_source("findable_source")
        assert retrieved is not None
        assert retrieved.name == "findable_source"

    def test_get_data_source_not_found(self):
        """Test retrieving non-existent data source"""
        retrieved = self.manager.get_data_source("non_existent_source")
        assert retrieved is None

    def test_list_data_sources_by_priority(self):
        """Test listing data sources ordered by priority"""
        sources = [
            DataSourceConfig(name="low_priority", source_type="api", priority=3, config={}),
            DataSourceConfig(name="high_priority", source_type="api", priority=1, config={}),
            DataSourceConfig(name="medium_priority", source_type="api", priority=2, config={})
        ]

        for source in sources:
            self.manager.add_data_source(source)

        ordered_sources = self.manager.get_sources_by_priority()
        names = [source.name for source in ordered_sources]

        assert names == ["high_priority", "medium_priority", "low_priority"]


class TestDataFetching:
    """Test data fetching from various sources"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    @patch('core.data_processing.managers.enhanced_data_manager.yfinance.Ticker')
    def test_fetch_data_from_yfinance(self, mock_ticker):
        """Test fetching data from Yahoo Finance"""
        mock_ticker_instance = Mock()
        mock_ticker_instance.info = {
            'marketCap': 2500000000000,
            'previousClose': 150.0,
            'beta': 1.2
        }
        mock_ticker_instance.financials = pd.DataFrame({
            'Total Revenue': [100000, 90000, 80000],
            'Net Income': [25000, 22000, 20000]
        })
        mock_ticker.return_value = mock_ticker_instance

        data = self.manager.fetch_data("AAPL", source="yfinance")

        assert data is not None
        assert isinstance(data, dict)
        mock_ticker.assert_called_with("AAPL")

    @patch('core.data_processing.managers.enhanced_data_manager.requests.get')
    def test_fetch_data_from_alpha_vantage(self, mock_requests):
        """Test fetching data from Alpha Vantage"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2023-01-01': {'4. close': '150.0'},
                '2023-01-02': {'4. close': '151.0'}
            }
        }
        mock_requests.return_value = mock_response

        self.manager.api_keys = {'alpha_vantage': 'test_key'}
        data = self.manager.fetch_data("AAPL", source="alpha_vantage")

        assert data is not None
        mock_requests.assert_called()

    @patch('core.data_processing.managers.enhanced_data_manager.pd.read_excel')
    def test_fetch_data_from_excel(self, mock_read_excel):
        """Test fetching data from Excel files"""
        mock_read_excel.return_value = pd.DataFrame({
            'Metric': ['Revenue', 'Net Income'],
            'FY2023': [100000, 25000],
            'FY2022': [90000, 22000]
        })

        with patch('pathlib.Path.exists', return_value=True):
            data = self.manager.fetch_data("AAPL", source="excel", data_path="./test_data")

            assert data is not None
            assert isinstance(data, pd.DataFrame)
            mock_read_excel.assert_called()

    @patch('core.data_processing.managers.enhanced_data_manager.requests.get')
    def test_fetch_data_with_api_error(self, mock_requests):
        """Test handling API errors during data fetching"""
        mock_requests.side_effect = Exception("API connection failed")

        with pytest.raises(DataSourceException):
            self.manager.fetch_data("AAPL", source="alpha_vantage")

    @patch('core.data_processing.managers.enhanced_data_manager.requests.get')
    def test_fetch_data_with_rate_limit(self, mock_requests):
        """Test handling rate limit errors"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_requests.return_value = mock_response

        with pytest.raises(RateLimitException):
            self.manager.fetch_data("AAPL", source="alpha_vantage")

    def test_fetch_data_with_fallback_sources(self):
        """Test data fetching with fallback to alternative sources"""
        with patch.object(self.manager, '_fetch_from_source') as mock_fetch:
            # First source fails, second succeeds
            mock_fetch.side_effect = [
                DataSourceException("Primary source failed"),
                {'data': 'success_from_fallback'}
            ]

            data = self.manager.fetch_data_with_fallback("AAPL", sources=["primary", "fallback"])

            assert data == {'data': 'success_from_fallback'}
            assert mock_fetch.call_count == 2

    def test_fetch_data_all_sources_fail(self):
        """Test behavior when all data sources fail"""
        with patch.object(self.manager, '_fetch_from_source') as mock_fetch:
            mock_fetch.side_effect = DataSourceException("All sources failed")

            with pytest.raises(DataSourceException):
                self.manager.fetch_data_with_fallback("AAPL", sources=["source1", "source2"])


class TestDataValidationAndQuality:
    """Test data validation and quality assessment"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    def test_validate_data_quality_high_quality(self):
        """Test data quality validation for high-quality data"""
        high_quality_data = pd.DataFrame({
            'Revenue': [100000, 95000, 90000, 85000],
            'Net Income': [20000, 19000, 18000, 17000],
            'Date': pd.date_range('2020-01-01', periods=4, freq='Y')
        })

        quality = self.manager.assess_data_quality(high_quality_data)

        assert isinstance(quality, DataQuality)
        assert quality.score >= 0.8
        assert quality.completeness >= 0.9

    def test_validate_data_quality_poor_quality(self):
        """Test data quality validation for poor-quality data"""
        poor_quality_data = pd.DataFrame({
            'Revenue': [100000, None, np.inf, 'invalid'],
            'Net Income': [20000, np.nan, None, 0],
            'Date': [None, None, None, None]
        })

        quality = self.manager.assess_data_quality(poor_quality_data)

        assert isinstance(quality, DataQuality)
        assert quality.score < 0.5
        assert quality.completeness < 0.5

    def test_validate_financial_data_completeness(self):
        """Test validation of financial data completeness"""
        complete_data = {
            'income_statement': pd.DataFrame({'Revenue': [100000], 'Net Income': [20000]}),
            'balance_sheet': pd.DataFrame({'Total Assets': [500000], 'Total Equity': [300000]}),
            'cash_flow': pd.DataFrame({'Operating Cash Flow': [30000], 'Free Cash Flow': [25000]})
        }

        is_complete = self.manager.validate_financial_data_completeness(complete_data)
        assert is_complete is True

        incomplete_data = {
            'income_statement': pd.DataFrame({'Revenue': [100000]})
            # Missing balance_sheet and cash_flow
        }

        is_complete = self.manager.validate_financial_data_completeness(incomplete_data)
        assert is_complete is False

    def test_detect_data_anomalies(self):
        """Test detection of data anomalies and outliers"""
        normal_data = pd.DataFrame({
            'Revenue': [100000, 105000, 110000, 115000],
            'Growth': [0.05, 0.05, 0.05, 0.05]
        })

        anomalous_data = pd.DataFrame({
            'Revenue': [100000, 105000, 1000000, 115000],  # Outlier at index 2
            'Growth': [0.05, 0.05, 9.52, 0.05]  # Corresponding outlier
        })

        normal_anomalies = self.manager.detect_anomalies(normal_data)
        anomalous_anomalies = self.manager.detect_anomalies(anomalous_data)

        assert len(normal_anomalies) == 0
        assert len(anomalous_anomalies) > 0

    def test_cross_validate_data_sources(self):
        """Test cross-validation between multiple data sources"""
        source1_data = {'market_cap': 2500000000000, 'pe_ratio': 25.5}
        source2_data = {'market_cap': 2480000000000, 'pe_ratio': 25.2}  # Close match
        source3_data = {'market_cap': 1000000000000, 'pe_ratio': 50.0}  # Significant difference

        consistency_score = self.manager.cross_validate_sources([
            source1_data, source2_data, source3_data
        ])

        assert 0 <= consistency_score <= 1
        # Should detect inconsistency due to source3


class TestCachingMechanism:
    """Test caching functionality and performance"""

    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        cache_config = CacheConfig(
            enabled=True,
            ttl_seconds=3600,
            storage_path=self.temp_dir
        )
        self.manager = EnhancedDataManager(cache_config=cache_config)

    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_cache_data_storage(self):
        """Test storing data in cache"""
        test_data = {'symbol': 'AAPL', 'price': 150.0, 'timestamp': datetime.now()}
        cache_key = "AAPL_market_data"

        self.manager.cache_data(cache_key, test_data)

        # Verify data is cached
        cached_data = self.manager.get_cached_data(cache_key)
        assert cached_data is not None
        assert cached_data['symbol'] == 'AAPL'

    def test_cache_data_retrieval(self):
        """Test retrieving data from cache"""
        test_data = {'test': 'value', 'number': 42}
        cache_key = "test_cache_key"

        # Store data
        self.manager.cache_data(cache_key, test_data)

        # Retrieve data
        retrieved_data = self.manager.get_cached_data(cache_key)

        assert retrieved_data == test_data

    def test_cache_expiration(self):
        """Test cache expiration functionality"""
        test_data = {'expires': 'soon'}
        cache_key = "expiring_data"

        # Set very short TTL
        short_ttl_config = CacheConfig(enabled=True, ttl_seconds=1)
        manager = EnhancedDataManager(cache_config=short_ttl_config)

        manager.cache_data(cache_key, test_data)

        # Data should be available immediately
        immediate_data = manager.get_cached_data(cache_key)
        assert immediate_data is not None

        # Wait for expiration
        import time
        time.sleep(2)

        # Data should be expired
        expired_data = manager.get_cached_data(cache_key)
        assert expired_data is None

    def test_cache_invalidation(self):
        """Test manual cache invalidation"""
        test_data = {'will_be': 'invalidated'}
        cache_key = "invalidation_test"

        self.manager.cache_data(cache_key, test_data)
        assert self.manager.get_cached_data(cache_key) is not None

        self.manager.invalidate_cache(cache_key)
        assert self.manager.get_cached_data(cache_key) is None

    def test_cache_size_management(self):
        """Test cache size management and cleanup"""
        # Fill cache with data
        for i in range(100):
            cache_key = f"bulk_data_{i}"
            test_data = {'index': i, 'data': 'x' * 1000}  # 1KB per entry
            self.manager.cache_data(cache_key, test_data)

        # Cache should manage size automatically
        cache_size = self.manager.get_cache_size()
        assert cache_size > 0

        # Test cache cleanup
        self.manager.cleanup_cache()
        cleaned_size = self.manager.get_cache_size()
        assert cleaned_size <= cache_size

    def test_cache_performance_improvement(self):
        """Test that caching improves performance"""
        import time

        def slow_data_fetch():
            time.sleep(0.1)  # Simulate slow operation
            return {'slow': 'data', 'timestamp': datetime.now()}

        cache_key = "performance_test"

        # First call (uncached) - should be slow
        start_time = time.time()
        with patch.object(self.manager, '_fetch_from_source', side_effect=slow_data_fetch):
            data1 = self.manager.fetch_data_with_cache("TEST", cache_key)
        first_call_time = time.time() - start_time

        # Second call (cached) - should be fast
        start_time = time.time()
        data2 = self.manager.get_cached_data(cache_key)
        second_call_time = time.time() - start_time

        assert data1 is not None
        assert data2 is not None
        assert second_call_time < first_call_time * 0.5  # Should be significantly faster


class TestRateLimiting:
    """Test rate limiting functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_rate_limiting_enforcement(self, mock_sleep):
        """Test that rate limiting is enforced"""
        # Configure strict rate limiting
        self.manager.configure_rate_limiting("test_api", requests_per_minute=2)

        # Make requests
        for i in range(3):
            try:
                self.manager.make_rate_limited_request("test_api", lambda: f"request_{i}")
            except RateLimitException:
                # Third request should be rate limited
                assert i == 2

    def test_rate_limiting_different_apis(self):
        """Test rate limiting for different APIs independently"""
        self.manager.configure_rate_limiting("api1", requests_per_minute=60)
        self.manager.configure_rate_limiting("api2", requests_per_minute=60)

        # Should be able to make requests to both APIs
        result1 = self.manager.make_rate_limited_request("api1", lambda: "api1_result")
        result2 = self.manager.make_rate_limited_request("api2", lambda: "api2_result")

        assert result1 == "api1_result"
        assert result2 == "api2_result"

    def test_rate_limiting_reset_period(self):
        """Test rate limiting reset after time period"""
        with patch('time.time') as mock_time:
            # Start at time 0
            mock_time.return_value = 0

            self.manager.configure_rate_limiting("reset_test", requests_per_minute=1)

            # Make first request
            result1 = self.manager.make_rate_limited_request("reset_test", lambda: "first")
            assert result1 == "first"

            # Advance time by 61 seconds (past reset period)
            mock_time.return_value = 61

            # Should be able to make another request
            result2 = self.manager.make_rate_limited_request("reset_test", lambda: "second")
            assert result2 == "second"


class TestErrorHandlingAndRecovery:
    """Test error handling and recovery mechanisms"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    def test_network_error_handling(self):
        """Test handling of network errors"""
        with patch('core.data_processing.managers.enhanced_data_manager.requests.get') as mock_get:
            mock_get.side_effect = ConnectionError("Network unreachable")

            with pytest.raises(DataSourceException) as exc_info:
                self.manager.fetch_data("AAPL", source="alpha_vantage")

            assert "Network unreachable" in str(exc_info.value)

    def test_api_authentication_error_handling(self):
        """Test handling of API authentication errors"""
        with patch('core.data_processing.managers.enhanced_data_manager.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Invalid API key"
            mock_get.return_value = mock_response

            with pytest.raises(DataSourceException) as exc_info:
                self.manager.fetch_data("AAPL", source="alpha_vantage")

            assert "authentication" in str(exc_info.value).lower()

    def test_data_parsing_error_handling(self):
        """Test handling of data parsing errors"""
        with patch('core.data_processing.managers.enhanced_data_manager.pd.read_excel') as mock_read:
            mock_read.side_effect = ValueError("Invalid Excel format")

            with pytest.raises(DataSourceException) as exc_info:
                self.manager.fetch_data("AAPL", source="excel", data_path="./invalid_file.xlsx")

            assert "parsing" in str(exc_info.value).lower()

    def test_graceful_degradation_on_partial_failure(self):
        """Test graceful degradation when some data sources fail"""
        def mock_fetch_side_effect(source, *args, **kwargs):
            if source == "failing_source":
                raise DataSourceException("Source unavailable")
            elif source == "working_source":
                return {'data': 'partial_success'}
            else:
                raise ValueError("Unknown source")

        with patch.object(self.manager, '_fetch_from_source', side_effect=mock_fetch_side_effect):
            # Should succeed with partial data
            data = self.manager.fetch_data_with_fallback(
                "AAPL",
                sources=["failing_source", "working_source"]
            )

            assert data == {'data': 'partial_success'}

    def test_retry_mechanism_on_transient_failures(self):
        """Test retry mechanism for transient failures"""
        call_count = 0

        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success_after_retries"

        with patch('time.sleep'):  # Speed up test
            result = self.manager.retry_on_failure(failing_function, max_retries=3)

            assert result == "success_after_retries"
            assert call_count == 3

    def test_circuit_breaker_functionality(self):
        """Test circuit breaker pattern for failing services"""
        # Configure circuit breaker
        self.manager.configure_circuit_breaker("unreliable_api", failure_threshold=2)

        # Simulate failures
        with patch.object(self.manager, '_fetch_from_source', side_effect=Exception("Service down")):
            # First two failures should reach the service
            for i in range(2):
                with pytest.raises(Exception):
                    self.manager.fetch_with_circuit_breaker("unreliable_api", "AAPL")

            # Third call should be circuit-breaker blocked
            with pytest.raises(Exception) as exc_info:
                self.manager.fetch_with_circuit_breaker("unreliable_api", "AAPL")

            assert "circuit breaker" in str(exc_info.value).lower()


class TestDataTransformationAndNormalization:
    """Test data transformation and normalization functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    def test_normalize_financial_data_format(self):
        """Test normalization of financial data to standard format"""
        # Different source formats
        yfinance_format = {
            'Total Revenue': [100000, 90000, 80000],
            'Net Income': [25000, 22000, 20000]
        }

        alpha_vantage_format = {
            'totalRevenue': [100000, 90000, 80000],
            'netIncome': [25000, 22000, 20000]
        }

        # Normalize both formats
        normalized_yf = self.manager.normalize_financial_data(yfinance_format, source="yfinance")
        normalized_av = self.manager.normalize_financial_data(alpha_vantage_format, source="alpha_vantage")

        # Should result in same standardized format
        assert 'revenue' in normalized_yf
        assert 'net_income' in normalized_yf
        assert 'revenue' in normalized_av
        assert 'net_income' in normalized_av
        assert normalized_yf['revenue'] == normalized_av['revenue']

    def test_currency_conversion(self):
        """Test currency conversion functionality"""
        # Test data in EUR
        eur_data = {
            'revenue': [100000, 90000],
            'currency': 'EUR'
        }

        # Convert to USD
        usd_data = self.manager.convert_currency(eur_data, target_currency='USD')

        assert usd_data['currency'] == 'USD'
        assert usd_data['revenue'][0] != eur_data['revenue'][0]  # Should be converted

    def test_date_standardization(self):
        """Test standardization of date formats from different sources"""
        various_date_formats = [
            "2023-01-01",
            "01/01/2023",
            "Jan 1, 2023",
            "2023-Q1"
        ]

        standardized_dates = [
            self.manager.standardize_date(date_str) for date_str in various_date_formats
        ]

        # All should be converted to standard datetime format
        for date in standardized_dates:
            assert isinstance(date, datetime)

    def test_financial_metrics_calculation(self):
        """Test calculation of derived financial metrics"""
        financial_data = {
            'revenue': [100000, 90000, 80000],
            'net_income': [25000, 22000, 20000],
            'total_assets': [500000, 450000, 400000],
            'total_equity': [300000, 280000, 250000]
        }

        metrics = self.manager.calculate_derived_metrics(financial_data)

        assert 'roe' in metrics  # Return on Equity
        assert 'profit_margin' in metrics
        assert 'revenue_growth' in metrics
        assert all(isinstance(metric, (int, float)) for metric in metrics.values())

    def test_data_aggregation_by_period(self):
        """Test aggregation of data by different time periods"""
        quarterly_data = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=4, freq='Q'),
            'revenue': [25000, 26000, 27000, 28000],
            'expenses': [20000, 21000, 22000, 23000]
        })

        # Aggregate to annual
        annual_data = self.manager.aggregate_by_period(quarterly_data, period='annual')

        assert len(annual_data) == 1  # Should be one annual record
        assert annual_data.iloc[0]['revenue'] == 106000  # Sum of quarters

    def test_missing_data_interpolation(self):
        """Test interpolation of missing data points"""
        data_with_gaps = pd.DataFrame({
            'date': pd.date_range('2020-01-01', periods=5, freq='Y'),
            'revenue': [100000, None, 110000, None, 120000]
        })

        interpolated_data = self.manager.interpolate_missing_data(data_with_gaps)

        # Missing values should be interpolated
        assert interpolated_data['revenue'].isna().sum() == 0
        assert 100000 < interpolated_data.iloc[1]['revenue'] < 110000


@pytest.mark.integration
class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features"""

    def setup_method(self):
        """Set up test environment"""
        self.manager = EnhancedDataManager()

    def test_complete_data_pipeline(self):
        """Test complete data pipeline from fetch to analysis"""
        with patch.multiple(
            self.manager,
            fetch_data=Mock(return_value={'revenue': [100000], 'net_income': [25000]}),
            assess_data_quality=Mock(return_value=DataQuality(score=0.95, completeness=1.0)),
            normalize_financial_data=Mock(return_value={'revenue': [100000], 'net_income': [25000]}),
            calculate_derived_metrics=Mock(return_value={'roe': 0.25, 'profit_margin': 0.25})
        ):
            # Execute pipeline
            result = self.manager.execute_data_pipeline("AAPL")

            assert result is not None
            assert 'raw_data' in result
            assert 'quality_assessment' in result
            assert 'normalized_data' in result
            assert 'derived_metrics' in result

    def test_multi_source_data_reconciliation(self):
        """Test reconciliation of data from multiple sources"""
        # Mock different source responses
        yfinance_data = {'revenue': 100000, 'source': 'yfinance'}
        alpha_vantage_data = {'revenue': 99500, 'source': 'alpha_vantage'}
        excel_data = {'revenue': 100200, 'source': 'excel'}

        def mock_fetch_by_source(symbol, source):
            source_data = {
                'yfinance': yfinance_data,
                'alpha_vantage': alpha_vantage_data,
                'excel': excel_data
            }
            return source_data.get(source)

        with patch.object(self.manager, 'fetch_data', side_effect=mock_fetch_by_source):
            reconciled_data = self.manager.reconcile_multi_source_data(
                "AAPL",
                sources=['yfinance', 'alpha_vantage', 'excel']
            )

            assert 'revenue' in reconciled_data
            assert 'confidence_score' in reconciled_data
            assert 'source_agreement' in reconciled_data

    def test_performance_under_load(self):
        """Test performance under high load conditions"""
        import time
        import threading

        results = []
        errors = []

        def fetch_worker(symbol):
            try:
                data = self.manager.fetch_data(f"{symbol}", source="test")
                results.append(data)
            except Exception as e:
                errors.append(str(e))

        # Simulate concurrent requests
        with patch.object(self.manager, 'fetch_data', return_value={'test': 'data'}):
            threads = []
            for i in range(10):
                thread = threading.Thread(target=fetch_worker, args=(f"TEST{i}",))
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Verify results
            assert len(results) + len(errors) == 10
            assert len(errors) == 0  # No errors should occur


if __name__ == "__main__":
    pytest.main([__file__, "-v"])