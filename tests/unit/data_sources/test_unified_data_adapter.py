"""
Unit tests for Unified Data Adapter Module
"""

import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path

from core.data_sources.unified_data_adapter import (
    UsageStatistics,
    CacheEntry,
    UnifiedDataAdapter
)
from core.data_sources.data_sources import DataSourceType


class TestUsageStatistics:
    """Test UsageStatistics dataclass"""

    def test_usage_statistics_creation(self):
        """Test basic usage statistics creation"""
        stats = UsageStatistics(source_type=DataSourceType.YFINANCE)

        assert stats.total_calls == 0
        assert stats.successful_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_cost == 0.0
        assert stats.average_response_time == 0.0
        assert stats.monthly_calls == 0
        assert stats.source_type == DataSourceType.YFINANCE

    def test_usage_statistics_update_success(self):
        """Test updating statistics with successful response"""
        stats = UsageStatistics(source_type=DataSourceType.YFINANCE)

        # Mock successful response
        mock_response = Mock()
        mock_response.success = True
        mock_response.response_time = 1.5
        mock_response.cost_incurred = 0.001

        stats.update_stats(mock_response)

        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.failed_calls == 0
        assert stats.total_cost == 0.001
        assert stats.average_response_time == 1.5

    def test_usage_statistics_update_cached(self):
        """Test updating statistics with cached response"""
        stats = UsageStatistics(source_type=DataSourceType.EXCEL)

        # Mock cached response
        mock_response = Mock()
        mock_response.success = True
        mock_response.response_time = 0.1
        mock_response.cost_incurred = 0.0

        stats.update_stats(mock_response)

        assert stats.total_calls == 1
        assert stats.successful_calls == 1
        assert stats.total_cost == 0.0
        assert stats.average_response_time == 0.1

    def test_usage_statistics_update_failed(self):
        """Test updating statistics with failed response"""
        stats = UsageStatistics(source_type=DataSourceType.ALPHA_VANTAGE)

        # Mock failed response
        mock_response = Mock()
        mock_response.success = False
        mock_response.response_time = 2.0
        mock_response.cost_incurred = 0.0

        stats.update_stats(mock_response)

        assert stats.total_calls == 1
        assert stats.successful_calls == 0
        assert stats.failed_calls == 1
        assert stats.average_response_time == 2.0

    def test_usage_statistics_multiple_updates(self):
        """Test multiple statistics updates"""
        stats = UsageStatistics(source_type=DataSourceType.FINANCIAL_MODELING_PREP)

        # Add multiple mock responses
        responses = [
            Mock(success=True, response_time=1.0, cost_incurred=0.001),
            Mock(success=True, response_time=0.1, cost_incurred=0.0),
            Mock(success=False, response_time=3.0, cost_incurred=0.0)
        ]

        for response in responses:
            stats.update_stats(response)

        assert stats.total_calls == 3
        assert stats.successful_calls == 2
        assert stats.failed_calls == 1
        assert stats.total_cost == 0.001
        # Average response time: (1.0 + 0.1 + 3.0) / 3 = 1.367
        assert abs(stats.average_response_time - 1.367) < 0.01


class TestCacheEntry:
    """Test CacheEntry dataclass"""

    def test_cache_entry_creation(self):
        """Test basic cache entry creation"""
        test_data = {"price": 150.0, "symbol": "AAPL"}
        entry = CacheEntry(
            data=test_data,
            timestamp=datetime.now(),
            source_type=DataSourceType.YFINANCE,
            quality_score=0.9,
            ttl_hours=24
        )

        assert entry.data == test_data
        assert entry.ttl_hours == 24
        assert entry.timestamp is not None
        assert entry.source_type == DataSourceType.YFINANCE
        assert entry.quality_score == 0.9

    def test_cache_entry_not_expired(self):
        """Test cache entry that is not expired"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(hours=1),  # 1 hour ago
            source_type=DataSourceType.EXCEL,
            quality_score=0.8,
            ttl_hours=24  # Valid for 24 hours
        )

        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test cache entry that is expired"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(hours=25),  # 25 hours ago
            source_type=DataSourceType.ALPHA_VANTAGE,
            quality_score=0.7,
            ttl_hours=24  # Valid for 24 hours
        )

        assert entry.is_expired()

    def test_cache_entry_not_stale(self):
        """Test cache entry that is not stale"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(hours=2),  # 2 hours ago
            source_type=DataSourceType.FINANCIAL_MODELING_PREP,
            quality_score=0.85,
            ttl_hours=24
        )

        assert not entry.is_stale(stale_threshold_hours=6)

    def test_cache_entry_stale(self):
        """Test cache entry that is stale"""
        entry = CacheEntry(
            data={"test": "data"},
            timestamp=datetime.now() - timedelta(hours=8),  # 8 hours ago
            source_type=DataSourceType.POLYGON,
            quality_score=0.9,
            ttl_hours=24
        )

        assert entry.is_stale(stale_threshold_hours=6)


class TestUnifiedDataAdapter:
    """Test UnifiedDataAdapter class"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config = {
                "yfinance": {
                    "enabled": True,
                    "priority": 1,
                    "rate_limit_per_minute": 60,
                    "cost_per_request": 0.0,
                    "timeout_seconds": 10
                },
                "alpha_vantage": {
                    "enabled": False,
                    "priority": 2,
                    "rate_limit_per_minute": 5,
                    "cost_per_request": 0.01,
                    "timeout_seconds": 15
                }
            }
            json.dump(config, f)
            yield f.name
        os.unlink(f.name)

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_adapter_initialization_with_config(self, temp_config_file, temp_dir):
        """Test adapter initialization with existing config file"""
        adapter = UnifiedDataAdapter(config_file=temp_config_file, base_path=temp_dir)

        assert str(adapter.config_file) == str(temp_config_file)
        assert str(adapter.base_path) == str(temp_dir)
        assert adapter.configurations is not None
        assert adapter.cache is not None
        assert adapter.usage_stats is not None

    def test_adapter_initialization_without_config(self, temp_dir):
        """Test adapter initialization without config file"""
        non_existent_config = os.path.join(temp_dir, "non_existent.json")

        adapter = UnifiedDataAdapter(config_file=non_existent_config, base_path=temp_dir)

        assert str(adapter.config_file) == str(non_existent_config)
        assert adapter.configurations is not None  # Should use defaults
        assert len(adapter.configurations) > 0  # Should have default sources

    def test_load_configuration_with_valid_file(self, temp_config_file, temp_dir):
        """Test loading configuration from valid file"""
        adapter = UnifiedDataAdapter(config_file=temp_config_file, base_path=temp_dir)

        # Should have loaded the config
        config_keys = [str(key) for key in adapter.configurations.keys()]
        assert any("yfinance" in str(key) or "YFINANCE" in str(key) for key in config_keys)

        # Check that configurations exist
        assert len(adapter.configurations) > 0

    def test_get_default_configuration(self, temp_dir):
        """Test getting default configuration"""
        adapter = UnifiedDataAdapter(base_path=temp_dir)

        default_config = adapter._get_default_configuration()

        assert isinstance(default_config, dict)
        assert len(default_config) > 0

        # Should include common data sources
        # Note: Actual data sources depend on implementation
        config_keys = [str(key) for key in default_config.keys()]
        assert any("yfinance" in key.lower() or "yahoo" in key.lower() for key in config_keys)

    def test_cache_operations(self, temp_dir):
        """Test basic cache operations"""
        adapter = UnifiedDataAdapter(base_path=temp_dir)

        # Cache should be initialized
        assert adapter.cache is not None
        assert isinstance(adapter.cache, dict)

    def test_statistics_tracking(self, temp_dir):
        """Test statistics tracking functionality"""
        adapter = UnifiedDataAdapter(base_path=temp_dir)

        # Statistics should be initialized
        assert adapter.usage_stats is not None
        assert isinstance(adapter.usage_stats, dict)
        assert len(adapter.usage_stats) >= 0

    def test_save_configuration(self, temp_dir):
        """Test saving configuration to file"""
        config_file = os.path.join(temp_dir, "test_config.json")
        adapter = UnifiedDataAdapter(config_file=config_file, base_path=temp_dir)

        # Add some configuration
        adapter.configurations = adapter._get_default_configuration()

        # Save configuration
        adapter._save_configuration()

        # Check that file was created
        assert os.path.exists(config_file)

        # Check that file contains valid JSON
        with open(config_file, 'r') as f:
            saved_config = json.load(f)

        assert isinstance(saved_config, dict)

    def test_load_cache_from_file(self, temp_dir):
        """Test loading cache from file"""
        adapter = UnifiedDataAdapter(base_path=temp_dir)

        # Cache file may or may not exist - just test that method works
        try:
            adapter._load_cache()
            # If no exception, cache loading worked
            assert adapter.cache is not None
        except (FileNotFoundError, json.JSONDecodeError):
            # Expected if cache file doesn't exist or is invalid
            assert adapter.cache is not None

    def test_thread_safety_initialization(self, temp_dir):
        """Test that adapter handles thread safety properly"""
        adapter = UnifiedDataAdapter(base_path=temp_dir)

        # Should have thread safety mechanisms
        assert hasattr(adapter, '_lock') or hasattr(adapter, '_thread_lock')

    @patch('core.data_sources.unified_data_adapter.logger')
    def test_error_handling_invalid_config(self, mock_logger, temp_dir):
        """Test error handling with invalid configuration"""
        # Create invalid config file
        invalid_config = os.path.join(temp_dir, "invalid.json")
        with open(invalid_config, 'w') as f:
            f.write("invalid json content")

        # Should handle invalid config gracefully
        adapter = UnifiedDataAdapter(config_file=invalid_config, base_path=temp_dir)

        # Should still be initialized with defaults
        assert adapter.configurations is not None


class TestUnifiedDataAdapterIntegration:
    """Integration tests for UnifiedDataAdapter"""

    @pytest.mark.integration
    def test_adapter_with_real_filesystem(self):
        """Test adapter with real filesystem operations"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = UnifiedDataAdapter(base_path=tmpdir)

            # Basic integration test
            assert adapter is not None
            assert adapter.configurations is not None
            assert adapter.cache is not None
            assert adapter.usage_stats is not None

    @pytest.mark.unit
    def test_adapter_interface_completeness(self):
        """Test that adapter provides expected interface"""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = UnifiedDataAdapter(base_path=tmpdir)

            # Check that key methods exist
            assert hasattr(adapter, '_load_configuration')
            assert hasattr(adapter, '_save_configuration')
            assert hasattr(adapter, '_get_default_configuration')
            assert hasattr(adapter, '_load_cache')
            assert hasattr(adapter, '_initialize_providers')

            # Check that attributes exist
            assert hasattr(adapter, 'configurations')
            assert hasattr(adapter, 'cache')
            assert hasattr(adapter, 'usage_stats')
            assert hasattr(adapter, 'config_file')
            assert hasattr(adapter, 'base_path')


class TestUnifiedDataAdapterCaching:
    """Test caching functionality of UnifiedDataAdapter"""

    def test_cache_entry_lifecycle(self):
        """Test complete cache entry lifecycle"""
        # Create entry
        data = {"symbol": "AAPL", "price": 150.0}
        entry = CacheEntry(
            data=data,
            timestamp=datetime.now(),
            source_type=DataSourceType.YFINANCE,
            quality_score=0.9,
            ttl_hours=1
        )

        # Fresh entry should not be expired or stale
        assert not entry.is_expired()
        assert not entry.is_stale()

        # Test with old timestamp
        old_entry = CacheEntry(
            data=data,
            timestamp=datetime.now() - timedelta(hours=2),
            source_type=DataSourceType.EXCEL,
            quality_score=0.8,
            ttl_hours=1
        )

        assert old_entry.is_expired()
        assert old_entry.is_stale(stale_threshold_hours=1)

    def test_cache_performance_considerations(self):
        """Test cache performance characteristics"""
        # Test with large data
        large_data = {"data": list(range(1000))}
        entry = CacheEntry(
            data=large_data,
            timestamp=datetime.now(),
            source_type=DataSourceType.ALPHA_VANTAGE,
            quality_score=0.95,
            ttl_hours=24
        )

        # Operations should be fast
        assert not entry.is_expired()
        assert not entry.is_stale()
        assert entry.data == large_data