"""
Unit tests for DataSourceManager module.

This module tests the command-line and programmatic interface for managing
financial data sources, including configuration, testing, and monitoring.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime

from core.data_sources.data_source_manager import DataSourceManager
from core.data_sources.unified_data_adapter import UnifiedDataAdapter
from core.data_sources.data_sources import DataSourceType, FinancialDataRequest


class TestDataSourceManager:
    """Test class for DataSourceManager functionality"""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for testing"""
        return tmp_path

    @pytest.fixture
    def mock_adapter(self):
        """Create a mock UnifiedDataAdapter"""
        return Mock(spec=UnifiedDataAdapter)

    @pytest.fixture
    def data_source_manager(self, temp_dir, mock_adapter):
        """Create a DataSourceManager instance with mocked dependencies"""
        with patch('core.data_sources.data_source_manager.UnifiedDataAdapter') as mock_adapter_class:
            mock_adapter_class.return_value = mock_adapter
            manager = DataSourceManager(base_path=str(temp_dir))
            manager.adapter = mock_adapter
            return manager

    def test_initialization_default_path(self):
        """Test DataSourceManager initialization with default path"""
        with patch('core.data_sources.data_source_manager.UnifiedDataAdapter') as mock_adapter_class:
            manager = DataSourceManager()

            assert manager.base_path == Path(".")
            mock_adapter_class.assert_called_once_with(
                config_file="./config/data_sources_config.json",
                base_path="."
            )

    def test_initialization_custom_path(self, temp_dir):
        """Test DataSourceManager initialization with custom path"""
        with patch('core.data_sources.data_source_manager.UnifiedDataAdapter') as mock_adapter_class:
            manager = DataSourceManager(base_path=str(temp_dir))

            assert manager.base_path == temp_dir
            mock_adapter_class.assert_called_once_with(
                config_file=str(temp_dir / "config/data_sources_config.json"),
                base_path=str(temp_dir)
            )

    @patch('builtins.input')
    @patch('builtins.print')
    def test_interactive_setup_api_configuration(self, mock_print, mock_input, data_source_manager):
        """Test interactive setup for API configuration"""
        # Mock user inputs for API key configuration
        mock_input.side_effect = [
            'y',  # Configure Alpha Vantage
            'test_alpha_key',  # Alpha Vantage API key
            'n',  # Don't configure FMP
            'n',  # Don't configure Polygon
            'y'   # Save configuration
        ]

        with patch.object(data_source_manager, '_validate_api_key') as mock_validate:
            mock_validate.return_value = True

            data_source_manager.interactive_setup()

            # Verify that validation was called
            mock_validate.assert_called()

            # Verify print calls for setup messages
            mock_print.assert_any_call("🔧 Financial Data Sources Configuration")

    @patch('builtins.input')
    def test_interactive_setup_skip_all(self, mock_input, data_source_manager):
        """Test interactive setup when user skips all configurations"""
        # Mock user inputs to skip all configurations
        mock_input.side_effect = [
            'n',  # Don't configure Alpha Vantage
            'n',  # Don't configure FMP
            'n',  # Don't configure Polygon
            'n'   # Don't save configuration
        ]

        data_source_manager.interactive_setup()

        # Should complete without errors

    def test_validate_api_key_alpha_vantage(self, data_source_manager):
        """Test API key validation for Alpha Vantage"""
        with patch('requests.get') as mock_get:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "Global Quote": {
                    "01. symbol": "AAPL"
                }
            }
            mock_get.return_value = mock_response

            result = data_source_manager._validate_api_key("alpha_vantage", "test_key")

            assert result is True
            mock_get.assert_called_once()

    def test_validate_api_key_invalid(self, data_source_manager):
        """Test API key validation with invalid key"""
        with patch('requests.get') as mock_get:
            # Mock failed API response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_get.return_value = mock_response

            result = data_source_manager._validate_api_key("alpha_vantage", "invalid_key")

            assert result is False

    def test_validate_api_key_network_error(self, data_source_manager):
        """Test API key validation with network error"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")

            result = data_source_manager._validate_api_key("alpha_vantage", "test_key")

            assert result is False

    def test_save_configuration(self, data_source_manager, temp_dir):
        """Test configuration saving functionality"""
        config_data = {
            "alpha_vantage": {"api_key": "test_key"},
            "fmp": {"api_key": "fmp_key"}
        }

        config_dir = temp_dir / "config"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "data_sources_config.json"

        with patch('builtins.open', mock_open()) as mock_file:
            data_source_manager._save_configuration(config_data)

            # Verify file was opened for writing
            mock_file.assert_called()

    def test_load_configuration_existing(self, data_source_manager, temp_dir):
        """Test loading existing configuration"""
        config_data = {
            "alpha_vantage": {"api_key": "test_key"},
            "fmp": {"api_key": "fmp_key"}
        }

        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            with patch('os.path.exists', return_value=True):
                result = data_source_manager._load_configuration()

                assert result == config_data

    def test_load_configuration_missing(self, data_source_manager):
        """Test loading configuration when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = data_source_manager._load_configuration()

            assert result == {}

    def test_load_configuration_invalid_json(self, data_source_manager):
        """Test loading configuration with invalid JSON"""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('os.path.exists', return_value=True):
                result = data_source_manager._load_configuration()

                assert result == {}

    def test_test_all_sources(self, data_source_manager, mock_adapter):
        """Test functionality to test all configured data sources"""
        mock_adapter.test_connection.return_value = True

        result = data_source_manager.test_all_sources()

        assert "test_results" in result
        mock_adapter.test_connection.assert_called()

    def test_test_specific_source(self, data_source_manager, mock_adapter):
        """Test functionality to test a specific data source"""
        mock_adapter.test_connection.return_value = True

        result = data_source_manager.test_source("alpha_vantage")

        assert result is True
        mock_adapter.test_connection.assert_called_with("alpha_vantage")

    def test_get_usage_statistics(self, data_source_manager, mock_adapter):
        """Test retrieving usage statistics"""
        mock_stats = {
            "alpha_vantage": {
                "requests_today": 50,
                "requests_this_month": 1000,
                "last_request": datetime.now().isoformat()
            }
        }
        mock_adapter.get_usage_stats.return_value = mock_stats

        result = data_source_manager.get_usage_statistics()

        assert result == mock_stats
        mock_adapter.get_usage_stats.assert_called_once()

    def test_monitor_costs(self, data_source_manager, mock_adapter):
        """Test cost monitoring functionality"""
        mock_costs = {
            "alpha_vantage": {"daily_cost": 0.0, "monthly_cost": 0.0},
            "fmp": {"daily_cost": 2.50, "monthly_cost": 75.0}
        }
        mock_adapter.calculate_costs.return_value = mock_costs

        result = data_source_manager.monitor_costs()

        assert result == mock_costs
        mock_adapter.calculate_costs.assert_called_once()

    def test_generate_usage_report(self, data_source_manager, mock_adapter):
        """Test usage report generation"""
        mock_stats = {
            "alpha_vantage": {"requests_today": 50},
            "fmp": {"requests_today": 25}
        }
        mock_costs = {
            "alpha_vantage": {"daily_cost": 0.0},
            "fmp": {"daily_cost": 2.50}
        }

        mock_adapter.get_usage_stats.return_value = mock_stats
        mock_adapter.calculate_costs.return_value = mock_costs

        with patch('builtins.open', mock_open()) as mock_file:
            data_source_manager.generate_usage_report()

            # Verify report file was created
            mock_file.assert_called()

    def test_set_usage_limits(self, data_source_manager, mock_adapter):
        """Test setting usage limits for data sources"""
        limits = {
            "alpha_vantage": {"daily_limit": 500, "monthly_limit": 15000},
            "fmp": {"daily_limit": 100, "monthly_limit": 3000}
        }

        data_source_manager.set_usage_limits(limits)

        mock_adapter.set_usage_limits.assert_called_once_with(limits)

    def test_check_usage_alerts(self, data_source_manager, mock_adapter):
        """Test usage alert checking"""
        mock_alerts = [
            {
                "source": "fmp",
                "type": "daily_limit_warning",
                "usage_percent": 85,
                "message": "FMP approaching daily limit"
            }
        ]
        mock_adapter.check_usage_alerts.return_value = mock_alerts

        result = data_source_manager.check_usage_alerts()

        assert result == mock_alerts
        mock_adapter.check_usage_alerts.assert_called_once()

    def test_reset_usage_counters(self, data_source_manager, mock_adapter):
        """Test resetting usage counters"""
        data_source_manager.reset_usage_counters()

        mock_adapter.reset_usage_counters.assert_called_once()

    def test_export_configuration(self, data_source_manager, temp_dir):
        """Test configuration export functionality"""
        config_data = {
            "alpha_vantage": {"api_key": "***masked***"},
            "fmp": {"api_key": "***masked***"}
        }

        with patch.object(data_source_manager, '_load_configuration') as mock_load:
            mock_load.return_value = {
                "alpha_vantage": {"api_key": "real_key"},
                "fmp": {"api_key": "real_fmp_key"}
            }

            export_file = temp_dir / "exported_config.json"

            with patch('builtins.open', mock_open()) as mock_file:
                data_source_manager.export_configuration(str(export_file))

                mock_file.assert_called()

    def test_import_configuration(self, data_source_manager, temp_dir):
        """Test configuration import functionality"""
        import_data = {
            "alpha_vantage": {"api_key": "imported_key"},
            "fmp": {"api_key": "imported_fmp_key"}
        }

        import_file = temp_dir / "import_config.json"

        with patch('builtins.open', mock_open(read_data=json.dumps(import_data))):
            with patch.object(data_source_manager, '_save_configuration') as mock_save:
                data_source_manager.import_configuration(str(import_file))

                mock_save.assert_called_once_with(import_data)

    def test_backup_configuration(self, data_source_manager, temp_dir):
        """Test configuration backup functionality"""
        config_data = {
            "alpha_vantage": {"api_key": "test_key"}
        }

        with patch.object(data_source_manager, '_load_configuration') as mock_load:
            mock_load.return_value = config_data

            with patch('builtins.open', mock_open()) as mock_file:
                backup_file = data_source_manager.backup_configuration()

                assert "backup" in backup_file
                mock_file.assert_called()

    def test_list_available_sources(self, data_source_manager, mock_adapter):
        """Test listing available data sources"""
        mock_sources = {
            "alpha_vantage": {"status": "configured", "last_test": "2023-01-01"},
            "fmp": {"status": "not_configured", "last_test": None},
            "polygon": {"status": "configured", "last_test": "2023-01-01"}
        }
        mock_adapter.list_sources.return_value = mock_sources

        result = data_source_manager.list_available_sources()

        assert result == mock_sources
        mock_adapter.list_sources.assert_called_once()

    def test_validate_all_configurations(self, data_source_manager, mock_adapter):
        """Test validating all configured data sources"""
        mock_validation = {
            "alpha_vantage": {"valid": True, "error": None},
            "fmp": {"valid": False, "error": "Invalid API key"}
        }
        mock_adapter.validate_all_configs.return_value = mock_validation

        result = data_source_manager.validate_all_configurations()

        assert result == mock_validation
        mock_adapter.validate_all_configs.assert_called_once()


class TestDataSourceManagerCLI:
    """Test class for DataSourceManager CLI functionality"""

    @pytest.fixture
    def mock_manager(self):
        """Create a mock DataSourceManager for CLI testing"""
        return Mock(spec=DataSourceManager)

    def test_cli_interactive_setup(self, mock_manager):
        """Test CLI command for interactive setup"""
        with patch('core.data_sources.data_source_manager.DataSourceManager') as mock_class:
            mock_class.return_value = mock_manager

            # Test would involve calling CLI with setup command
            # This is a placeholder for actual CLI testing
            pass

    def test_cli_test_sources(self, mock_manager):
        """Test CLI command for testing sources"""
        mock_manager.test_all_sources.return_value = {
            "test_results": {"alpha_vantage": True, "fmp": False}
        }

        # Test would involve calling CLI with test command
        # This is a placeholder for actual CLI testing
        pass

    def test_cli_usage_report(self, mock_manager):
        """Test CLI command for generating usage reports"""
        mock_manager.generate_usage_report.return_value = "report.json"

        # Test would involve calling CLI with report command
        # This is a placeholder for actual CLI testing
        pass


class TestDataSourceManagerErrorHandling:
    """Test error handling scenarios in DataSourceManager"""

    @pytest.fixture
    def data_source_manager(self, tmp_path):
        """Create a DataSourceManager with minimal mocking for error testing"""
        with patch('core.data_sources.data_source_manager.UnifiedDataAdapter'):
            return DataSourceManager(base_path=str(tmp_path))

    def test_permission_error_handling(self, data_source_manager):
        """Test handling of permission errors when saving configuration"""
        with patch('builtins.open', side_effect=PermissionError("Access denied")):
            # Should handle permission error gracefully
            result = data_source_manager._save_configuration({})
            assert result is False

    def test_disk_space_error_handling(self, data_source_manager):
        """Test handling of disk space errors"""
        with patch('builtins.open', side_effect=OSError("No space left on device")):
            # Should handle disk space error gracefully
            result = data_source_manager._save_configuration({})
            assert result is False

    def test_network_timeout_handling(self, data_source_manager):
        """Test handling of network timeouts during API validation"""
        import requests

        with patch('requests.get', side_effect=requests.Timeout("Request timeout")):
            result = data_source_manager._validate_api_key("alpha_vantage", "test_key")
            assert result is False

    def test_corrupted_config_file_handling(self, data_source_manager):
        """Test handling of corrupted configuration files"""
        with patch('builtins.open', mock_open(read_data="corrupted data {")):
            with patch('os.path.exists', return_value=True):
                result = data_source_manager._load_configuration()
                assert result == {}  # Should return empty dict on error


class TestDataSourceManagerIntegration:
    """Integration tests for DataSourceManager"""

    @pytest.mark.integration
    def test_full_configuration_workflow(self, tmp_path):
        """Test complete configuration workflow from setup to validation"""
        # This would test the complete workflow with real components
        pass

    @pytest.mark.slow
    def test_performance_with_multiple_sources(self, tmp_path):
        """Test performance when managing multiple data sources"""
        # This would test performance characteristics
        pass

    @pytest.mark.api_dependent
    def test_real_api_validation(self):
        """Test API validation with real API endpoints"""
        # This would test with actual API keys (in CI/CD environment)
        pass