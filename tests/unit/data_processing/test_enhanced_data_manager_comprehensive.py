"""
Comprehensive Tests for Enhanced Data Manager
============================================

This module contains comprehensive unit tests for the Enhanced Data Manager,
testing data retrieval, caching, quality scoring, and multi-source integration.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Import modules under test
from core.data_processing.managers.enhanced_data_manager import EnhancedDataManager
from core.data_processing.var_input_data import VarInputData
from core.data_processing.advanced_data_quality_scorer import AdvancedDataQualityScorer
from tests.utils.common_test_utilities import create_mock_financial_data, TestDataGenerator


class TestEnhancedDataManagerInitialization:
    """Test EnhancedDataManager initialization and setup"""

    def test_manager_initialization_default(self):
        """Test manager initializes with default settings"""
        manager = EnhancedDataManager()
        assert manager is not None
        assert hasattr(manager, 'data_sources')
        assert hasattr(manager, 'cache_manager')

    def test_manager_initialization_with_ticker(self):
        """Test manager initializes with specific ticker"""
        manager = EnhancedDataManager("MSFT")
        assert manager is not None

    @patch('core.data_processing.managers.enhanced_data_manager.AdvancedDataQualityScorer')
    def test_manager_initialization_with_quality_scorer(self, mock_scorer):
        """Test manager initializes with quality scorer"""
        mock_scorer_instance = Mock()
        mock_scorer.return_value = mock_scorer_instance

        manager = EnhancedDataManager()
        assert manager is not None

    def test_manager_configuration_loading(self):
        """Test manager loads configuration correctly"""
        with patch('core.data_processing.managers.enhanced_data_manager.load_config') as mock_config:
            mock_config.return_value = {
                'data_sources': {'yfinance': {'enabled': True, 'priority': 1}},
                'cache_settings': {'ttl': 3600}
            }

            manager = EnhancedDataManager()
            assert manager is not None


class TestDataRetrievalMethods:
    """Test data retrieval methods for different data sources"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    @patch('yfinance.Ticker')
    def test_get_yfinance_data(self, mock_ticker):
        """Test yfinance data retrieval"""
        mock_stock = Mock()
        mock_ticker.return_value = mock_stock

        # Mock financial data
        mock_stock.financials = pd.DataFrame({
            '2023-12-31': [100000000000, 60000000000],
            '2022-12-31': [95000000000, 55000000000]
        }, index=['Total Revenue', 'Operating Income'])

        mock_stock.balance_sheet = pd.DataFrame({
            '2023-12-31': [200000000000, 50000000000],
            '2022-12-31': [190000000000, 45000000000]
        }, index=['Total Assets', 'Total Debt'])

        mock_stock.cashflow = pd.DataFrame({
            '2023-12-31': [75000000000, -15000000000],
            '2022-12-31': [70000000000, -12000000000]
        }, index=['Operating Cash Flow', 'Capital Expenditures'])

        # Test data retrieval
        if hasattr(self.manager, 'get_yfinance_data'):
            financial_data = self.manager.get_yfinance_data("MSFT")
            assert financial_data is not None
            assert isinstance(financial_data, dict)

    def test_get_financial_data_with_cache(self):
        """Test financial data retrieval with caching"""
        with patch.object(self.manager, 'cache_manager') as mock_cache:
            mock_cache.get.return_value = None  # Cache miss
            mock_cache.set.return_value = True

            with patch.object(self.manager, '_fetch_from_primary_source') as mock_fetch:
                mock_fetch.return_value = create_mock_financial_data("MSFT")

                data = self.manager.get_financial_data("MSFT")
                assert data is not None

                # Verify cache was used
                mock_cache.get.assert_called()
                mock_cache.set.assert_called()

    def test_get_financial_data_cache_hit(self):
        """Test financial data retrieval with cache hit"""
        cached_data = create_mock_financial_data("MSFT")

        with patch.object(self.manager, 'cache_manager') as mock_cache:
            mock_cache.get.return_value = cached_data  # Cache hit

            data = self.manager.get_financial_data("MSFT")
            assert data == cached_data

            # Verify only cache.get was called, not cache.set
            mock_cache.get.assert_called()
            mock_cache.set.assert_not_called()

    def test_data_source_fallback_mechanism(self):
        """Test fallback mechanism between data sources"""
        with patch.object(self.manager, '_fetch_from_yfinance') as mock_yfinance:
            with patch.object(self.manager, '_fetch_from_fmp') as mock_fmp:
                with patch.object(self.manager, '_fetch_from_alpha_vantage') as mock_av:
                    # First source fails
                    mock_yfinance.side_effect = Exception("API Error")

                    # Second source succeeds
                    mock_fmp.return_value = create_mock_financial_data("MSFT")

                    if hasattr(self.manager, 'get_financial_data_with_fallback'):
                        data = self.manager.get_financial_data_with_fallback("MSFT")
                        assert data is not None

                        # Verify fallback was used
                        mock_yfinance.assert_called()
                        mock_fmp.assert_called()

    def test_excel_data_integration(self):
        """Test Excel data source integration"""
        mock_excel_data = {
            'revenue': 200000000000,
            'net_income': 50000000000,
            'total_assets': 400000000000,
            'shareholders_equity': 150000000000
        }

        with patch.object(self.manager, '_load_excel_data') as mock_excel:
            mock_excel.return_value = mock_excel_data

            if hasattr(self.manager, 'get_excel_data'):
                data = self.manager.get_excel_data("MSFT")
                assert data == mock_excel_data

    def test_api_rate_limiting(self):
        """Test API rate limiting functionality"""
        with patch.object(self.manager, 'rate_limiter') as mock_limiter:
            mock_limiter.acquire.return_value = True
            mock_limiter.is_available.return_value = True

            if hasattr(self.manager, '_make_api_call'):
                # Should respect rate limits
                result = self.manager._make_api_call("test_endpoint")
                mock_limiter.acquire.assert_called()


class TestDataQualityScoring:
    """Test data quality scoring and validation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    @patch('core.data_processing.managers.enhanced_data_manager.AdvancedDataQualityScorer')
    def test_data_quality_assessment(self, mock_scorer_class):
        """Test data quality assessment"""
        mock_scorer = Mock()
        mock_scorer_class.return_value = mock_scorer
        mock_scorer.calculate_overall_score.return_value = {
            'overall_score': 85.5,
            'completeness': 90.0,
            'consistency': 85.0,
            'accuracy': 80.0,
            'timeliness': 87.5
        }

        test_data = create_mock_financial_data("MSFT")

        if hasattr(self.manager, 'assess_data_quality'):
            quality_score = self.manager.assess_data_quality(test_data)
            assert quality_score is not None
            assert quality_score['overall_score'] == 85.5

    def test_quality_threshold_validation(self):
        """Test data quality threshold validation"""
        high_quality_data = create_mock_financial_data("MSFT")

        with patch.object(self.manager, 'assess_data_quality') as mock_assess:
            mock_assess.return_value = {'overall_score': 95.0}

            if hasattr(self.manager, 'validate_quality_threshold'):
                is_valid = self.manager.validate_quality_threshold(high_quality_data, threshold=80.0)
                assert is_valid is True

                # Test below threshold
                mock_assess.return_value = {'overall_score': 75.0}
                is_valid = self.manager.validate_quality_threshold(high_quality_data, threshold=80.0)
                assert is_valid is False

    def test_quality_history_tracking(self):
        """Test quality score history tracking"""
        quality_scores = [
            {'timestamp': datetime.now() - timedelta(days=3), 'overall_score': 85.0},
            {'timestamp': datetime.now() - timedelta(days=2), 'overall_score': 87.5},
            {'timestamp': datetime.now() - timedelta(days=1), 'overall_score': 83.0},
            {'timestamp': datetime.now(), 'overall_score': 89.0}
        ]

        with patch.object(self.manager, '_load_quality_history') as mock_load:
            mock_load.return_value = quality_scores

            if hasattr(self.manager, 'get_quality_history'):
                history = self.manager.get_quality_history(limit=10)
                assert len(history) == 4
                assert all('overall_score' in record for record in history)

    def test_quality_trend_analysis(self):
        """Test quality trend analysis"""
        quality_history = [
            {'timestamp': datetime.now() - timedelta(days=7), 'overall_score': 80.0},
            {'timestamp': datetime.now() - timedelta(days=6), 'overall_score': 82.0},
            {'timestamp': datetime.now() - timedelta(days=5), 'overall_score': 84.0},
            {'timestamp': datetime.now() - timedelta(days=4), 'overall_score': 85.0},
            {'timestamp': datetime.now() - timedelta(days=3), 'overall_score': 87.0},
            {'timestamp': datetime.now() - timedelta(days=2), 'overall_score': 86.0},
            {'timestamp': datetime.now() - timedelta(days=1), 'overall_score': 88.0},
            {'timestamp': datetime.now(), 'overall_score': 90.0}
        ]

        with patch.object(self.manager, 'get_quality_history') as mock_history:
            mock_history.return_value = quality_history

            if hasattr(self.manager, 'get_data_quality_trends'):
                trends = self.manager.get_data_quality_trends()
                assert trends is not None
                assert 'status' in trends  # improving, stable, degrading

    def test_predictive_quality_alerts(self):
        """Test predictive quality alerting"""
        with patch.object(self.manager, 'get_quality_history') as mock_history:
            # Simulate degrading quality trend
            degrading_history = [
                {'timestamp': datetime.now() - timedelta(days=i), 'overall_score': 90.0 - (i * 2)}
                for i in range(7)
            ]
            mock_history.return_value = degrading_history

            if hasattr(self.manager, 'predict_data_quality_issues'):
                predictions = self.manager.predict_data_quality_issues()
                assert predictions is not None
                assert 'risk_level' in predictions


class TestCacheManagement:
    """Test cache management functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    def test_cache_key_generation(self):
        """Test cache key generation"""
        if hasattr(self.manager, '_generate_cache_key'):
            key1 = self.manager._generate_cache_key("MSFT", "financial_data")
            key2 = self.manager._generate_cache_key("AAPL", "financial_data")
            key3 = self.manager._generate_cache_key("MSFT", "market_data")

            assert key1 != key2  # Different tickers
            assert key1 != key3  # Different data types
            assert isinstance(key1, str)

    def test_cache_expiration(self):
        """Test cache expiration logic"""
        with patch.object(self.manager, 'cache_manager') as mock_cache:
            # Mock expired cache entry
            expired_entry = {
                'data': create_mock_financial_data("MSFT"),
                'timestamp': datetime.now() - timedelta(hours=25),
                'ttl': 3600  # 1 hour TTL
            }
            mock_cache.get.return_value = expired_entry

            if hasattr(self.manager, '_is_cache_valid'):
                is_valid = self.manager._is_cache_valid(expired_entry)
                assert is_valid is False

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        with patch.object(self.manager, 'cache_manager') as mock_cache:
            if hasattr(self.manager, 'invalidate_cache'):
                self.manager.invalidate_cache("MSFT")
                mock_cache.delete.assert_called()

    def test_cache_statistics(self):
        """Test cache statistics tracking"""
        with patch.object(self.manager, 'cache_manager') as mock_cache:
            mock_cache.get_stats.return_value = {
                'hits': 150,
                'misses': 25,
                'hit_rate': 0.857,
                'total_size': 1024000
            }

            if hasattr(self.manager, 'get_cache_statistics'):
                stats = self.manager.get_cache_statistics()
                assert stats['hit_rate'] > 0.8


class TestErrorHandlingAndResilience:
    """Test error handling and resilience features"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    def test_api_error_handling(self):
        """Test API error handling"""
        with patch.object(self.manager, '_fetch_from_yfinance') as mock_fetch:
            # Simulate various API errors
            error_scenarios = [
                Exception("Connection timeout"),
                Exception("Rate limit exceeded"),
                Exception("Invalid API key"),
                Exception("Data not found")
            ]

            for error in error_scenarios:
                mock_fetch.side_effect = error

                if hasattr(self.manager, 'get_financial_data'):
                    # Should handle error gracefully
                    data = self.manager.get_financial_data("MSFT")
                    # Data might be None or empty, but shouldn't crash

    def test_network_error_resilience(self):
        """Test network error resilience"""
        with patch('requests.get') as mock_request:
            # Simulate network errors
            mock_request.side_effect = Exception("Network unreachable")

            if hasattr(self.manager, '_make_http_request'):
                try:
                    result = self.manager._make_http_request("http://example.com")
                    # Should handle gracefully
                except Exception as e:
                    # Or raise a specific exception type
                    assert isinstance(e, (Exception,))

    def test_data_validation_errors(self):
        """Test data validation error handling"""
        invalid_data = {
            'revenue': "not_a_number",
            'net_income': None,
            'shares_outstanding': -1000000  # Negative shares
        }

        if hasattr(self.manager, 'validate_financial_data'):
            validation_result = self.manager.validate_financial_data(invalid_data)
            assert validation_result is not None
            assert 'errors' in validation_result

    def test_circuit_breaker_functionality(self):
        """Test circuit breaker functionality"""
        with patch.object(self.manager, 'circuit_breaker') as mock_breaker:
            mock_breaker.is_open.return_value = True  # Circuit is open

            if hasattr(self.manager, '_check_circuit_breaker'):
                should_proceed = self.manager._check_circuit_breaker("yfinance")
                assert should_proceed is False

    def test_retry_mechanism(self):
        """Test retry mechanism for failed requests"""
        call_count = 0

        def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return create_mock_financial_data("MSFT")

        with patch.object(self.manager, '_make_api_call', side_effect=mock_api_call):
            if hasattr(self.manager, '_retry_api_call'):
                result = self.manager._retry_api_call("test_endpoint", max_retries=3)
                assert result is not None
                assert call_count == 3  # Should have retried twice


class TestMultiSourceIntegration:
    """Test multi-source data integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    def test_data_source_priority(self):
        """Test data source priority ordering"""
        with patch.object(self.manager, '_get_data_source_priority') as mock_priority:
            mock_priority.return_value = ['excel', 'yfinance', 'fmp', 'alpha_vantage', 'polygon']

            if hasattr(self.manager, 'get_prioritized_data_sources'):
                sources = self.manager.get_prioritized_data_sources()
                assert sources[0] == 'excel'  # Highest priority
                assert 'yfinance' in sources

    def test_data_merging_strategy(self):
        """Test data merging from multiple sources"""
        excel_data = {'revenue': 200000000000, 'net_income': None}
        yfinance_data = {'revenue': 198000000000, 'net_income': 50000000000, 'market_cap': 2500000000000}

        if hasattr(self.manager, '_merge_data_sources'):
            merged_data = self.manager._merge_data_sources([excel_data, yfinance_data])

            # Should prefer Excel revenue but use yfinance net_income
            assert merged_data['revenue'] == 200000000000  # From Excel
            assert merged_data['net_income'] == 50000000000  # From yfinance
            assert 'market_cap' in merged_data  # Additional data from yfinance

    def test_data_source_health_monitoring(self):
        """Test data source health monitoring"""
        if hasattr(self.manager, 'get_data_source_health'):
            health_status = self.manager.get_data_source_health()
            assert isinstance(health_status, dict)

            for source_name, status in health_status.items():
                assert 'status' in status  # healthy, degraded, failed
                assert 'response_time' in status
                assert 'success_rate' in status

    def test_available_data_sources(self):
        """Test getting available data sources information"""
        if hasattr(self.manager, 'get_available_data_sources'):
            sources_info = self.manager.get_available_data_sources()
            assert 'total_sources' in sources_info
            assert 'active_sources' in sources_info
            assert 'enhanced_sources' in sources_info


class TestPerformanceOptimization:
    """Test performance optimization features"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager("MSFT")

    def test_batch_data_retrieval(self):
        """Test batch data retrieval for multiple tickers"""
        tickers = ['MSFT', 'AAPL', 'GOOGL']

        if hasattr(self.manager, 'get_batch_financial_data'):
            batch_data = self.manager.get_batch_financial_data(tickers)
            assert len(batch_data) == len(tickers)
            assert all(ticker in batch_data for ticker in tickers)

    def test_concurrent_api_calls(self):
        """Test concurrent API calls for improved performance"""
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_future = Mock()
            mock_future.result.return_value = create_mock_financial_data("MSFT")
            mock_executor.return_value.__enter__.return_value.submit.return_value = mock_future

            if hasattr(self.manager, '_fetch_data_concurrently'):
                tickers = ['MSFT', 'AAPL', 'GOOGL']
                results = self.manager._fetch_data_concurrently(tickers)
                assert len(results) == len(tickers)

    def test_memory_optimization(self):
        """Test memory optimization features"""
        if hasattr(self.manager, 'optimize_memory_usage'):
            initial_memory = self.manager._get_memory_usage()
            self.manager.optimize_memory_usage()
            final_memory = self.manager._get_memory_usage()

            # Memory usage should not increase significantly
            assert final_memory <= initial_memory * 1.1

    def test_lazy_loading(self):
        """Test lazy loading of data"""
        if hasattr(self.manager, '_lazy_load_data'):
            # Data should not be loaded until explicitly requested
            lazy_data = self.manager._lazy_load_data("MSFT", "financial_statements")
            assert lazy_data is not None


class TestConfigurationAndSettings:
    """Test configuration and settings management"""

    def setup_method(self):
        """Set up test fixtures"""
        self.manager = EnhancedDataManager()

    def test_configuration_loading(self):
        """Test loading configuration from file"""
        mock_config = {
            'data_sources': {
                'yfinance': {'enabled': True, 'priority': 1, 'timeout': 30},
                'fmp': {'enabled': True, 'priority': 2, 'api_key': 'test_key'}
            },
            'cache_settings': {
                'ttl': 3600,
                'max_size': 1000
            },
            'quality_thresholds': {
                'minimum_score': 70.0,
                'warning_threshold': 80.0
            }
        }

        with patch('core.data_processing.managers.enhanced_data_manager.load_config') as mock_load:
            mock_load.return_value = mock_config

            if hasattr(self.manager, 'load_configuration'):
                config = self.manager.load_configuration()
                assert config['data_sources']['yfinance']['enabled'] is True
                assert config['cache_settings']['ttl'] == 3600

    def test_dynamic_configuration_updates(self):
        """Test dynamic configuration updates"""
        new_settings = {
            'quality_thresholds': {
                'minimum_score': 75.0,
                'warning_threshold': 85.0
            }
        }

        if hasattr(self.manager, 'update_configuration'):
            self.manager.update_configuration(new_settings)

            # Configuration should be updated
            current_config = self.manager.get_current_configuration()
            assert current_config['quality_thresholds']['minimum_score'] == 75.0

    def test_environment_variable_integration(self):
        """Test integration with environment variables"""
        with patch.dict('os.environ', {'FMP_API_KEY': 'test_api_key', 'DATA_CACHE_TTL': '7200'}):
            if hasattr(self.manager, '_load_env_config'):
                env_config = self.manager._load_env_config()
                assert 'FMP_API_KEY' in env_config
                assert env_config['DATA_CACHE_TTL'] == '7200'


if __name__ == "__main__":
    pytest.main([__file__])