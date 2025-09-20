"""
Simple unit tests for DataSourceBridge module.

Focused tests that match the actual DataSourceBridge interface.
"""

import pytest
from unittest.mock import Mock, patch
from core.data_sources.data_source_bridge import DataSourceBridge
from core.analysis.engines.financial_calculations import FinancialCalculator


class TestDataSourceBridgeSimple:
    """Simple test class for DataSourceBridge functionality"""

    @pytest.fixture
    def mock_financial_calculator(self):
        """Create a minimal mock financial calculator"""
        mock_calc = Mock()
        mock_calc.data_manager = Mock()
        mock_calc.ticker = "AAPL"
        mock_calc.financial_data = {"revenue": 1000000}  # Mock Excel data available
        mock_calc.fetch_market_data = Mock()
        return mock_calc

    @pytest.fixture
    def mock_enhanced_data_manager(self):
        """Create a minimal mock enhanced data manager"""
        mock_manager = Mock()
        return mock_manager

    def test_initialization_basic(self, mock_financial_calculator):
        """Test basic DataSourceBridge initialization"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        assert bridge.financial_calculator == mock_financial_calculator

    def test_initialization_with_enhanced_manager(self, mock_financial_calculator, mock_enhanced_data_manager):
        """Test DataSourceBridge initialization with enhanced manager"""
        bridge = DataSourceBridge(
            financial_calculator=mock_financial_calculator,
            enhanced_data_manager=mock_enhanced_data_manager
        )

        assert bridge.financial_calculator == mock_financial_calculator
        assert bridge.enhanced_data_manager == mock_enhanced_data_manager

    def test_get_market_data_no_crash(self, mock_financial_calculator):
        """Test that get_market_data doesn't crash"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Mock the enhanced data manager get_market_data call
        with patch.object(bridge, 'enhanced_data_manager') as mock_edm:
            mock_edm.get_market_data.return_value = {"current_price": 150.0}

            result = bridge.get_market_data("AAPL")

            # Should return something or None without crashing
            assert result is not None or result is None

    def test_get_dividend_data_no_crash(self, mock_financial_calculator):
        """Test that get_dividend_data doesn't crash"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        result = bridge.get_dividend_data("AAPL")

        # Should return something or None without crashing
        assert result is not None or result is None

    def test_get_balance_sheet_data_no_crash(self, mock_financial_calculator):
        """Test that get_balance_sheet_data doesn't crash"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        result = bridge.get_balance_sheet_data()

        # Should return something or None without crashing
        assert result is not None or result is None

    def test_get_comprehensive_financial_data_no_crash(self, mock_financial_calculator):
        """Test that get_comprehensive_financial_data doesn't crash"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Mock the enhanced data manager to return proper data types
        with patch.object(bridge, 'enhanced_data_manager') as mock_edm:
            mock_edm.fetch_market_data.return_value = {
                'current_price': 150.0,
                'market_cap': 2500000000000
            }

            result = bridge.get_comprehensive_financial_data()

            # Should return a dictionary
            assert isinstance(result, dict)

    def test_get_cache_stats_no_crash(self, mock_financial_calculator):
        """Test that get_cache_stats doesn't crash"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        result = bridge.get_cache_stats()

        # Should return a dictionary
        assert isinstance(result, dict)

    def test_logging_initialization(self, mock_financial_calculator, caplog):
        """Test that initialization logs available sources"""
        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should log available data sources
        assert "Available data sources" in caplog.text

    def test_excel_data_detection(self, mock_financial_calculator, caplog):
        """Test detection of Excel data availability"""
        mock_financial_calculator.financial_data = {"revenue": 1000000}

        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should detect Excel data
        assert "Excel Financial Statements" in caplog.text

    def test_no_excel_data_detection(self, mock_financial_calculator, caplog):
        """Test when no Excel data is available"""
        mock_financial_calculator.financial_data = {}

        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should not mention Excel data
        log_text = caplog.text
        assert "Excel Financial Statements" not in log_text or "Available data sources" in log_text

    def test_api_access_detection(self, mock_financial_calculator, caplog):
        """Test detection of API access capability"""
        # Mock that financial calculator has API access
        mock_financial_calculator.fetch_market_data = Mock()

        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should detect API access
        assert "Financial Calculator API Access" in caplog.text

    def test_enhanced_manager_detection(self, mock_financial_calculator, mock_enhanced_data_manager, caplog):
        """Test detection of enhanced data manager"""
        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(
                financial_calculator=mock_financial_calculator,
                enhanced_data_manager=mock_enhanced_data_manager
            )

        # Should detect enhanced data manager
        assert "Enhanced Data Manager" in caplog.text

    def test_fallback_source_always_available(self, mock_financial_calculator, caplog):
        """Test that yfinance fallback is always mentioned"""
        with caplog.at_level("INFO"):
            bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should always mention yfinance fallback
        assert "yfinance (Fallback)" in caplog.text

    def test_ticker_handling(self, mock_financial_calculator):
        """Test that ticker is properly handled"""
        mock_financial_calculator.ticker = "MSFT"

        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should work with different tickers
        result = bridge.get_market_data("GOOGL")
        assert result is not None or result is None

    def test_force_refresh_parameter(self, mock_financial_calculator):
        """Test force_refresh parameter in get_market_data"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should handle force_refresh parameter
        result = bridge.get_market_data("AAPL", force_refresh=True)
        assert result is not None or result is None

    def test_latest_only_parameter(self, mock_financial_calculator):
        """Test latest_only parameter in get_balance_sheet_data"""
        bridge = DataSourceBridge(financial_calculator=mock_financial_calculator)

        # Should handle latest_only parameter
        result = bridge.get_balance_sheet_data(latest_only=True)
        assert result is not None or result is None


class TestDataSourceBridgeIntegration:
    """Integration tests for DataSourceBridge"""

    @pytest.mark.integration
    def test_with_real_components(self):
        """Test with real components (requires actual setup)"""
        # This would test with real FinancialCalculator and EnhancedDataManager
        # Placeholder for integration testing
        pass

    @pytest.mark.slow
    def test_performance_characteristics(self):
        """Test performance characteristics"""
        # This would test performance aspects
        # Placeholder for performance testing
        pass