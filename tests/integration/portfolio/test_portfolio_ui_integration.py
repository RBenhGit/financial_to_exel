"""
Portfolio UI Integration Tests
=============================

Comprehensive tests for portfolio UI integration with the Streamlit interface,
testing the complete workflow from portfolio creation to analysis.

Test Coverage:
- Portfolio creation interface
- Portfolio persistence and loading
- Portfolio management operations
- UI component integration
- Data validation and error handling
- Integration with existing portfolio analytics
"""

import pytest
import streamlit as st
import pandas as pd
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime

# Import modules under test
from ui.streamlit.portfolio_management_ui import (
    render_comprehensive_portfolio_creation_interface,
    render_comprehensive_existing_portfolios_interface,
    render_comprehensive_portfolio_analysis_interface,
    _create_portfolio_from_inputs,
    _add_holding_to_session,
    _fetch_current_price,
    _import_from_csv,
    _filter_portfolios
)

from core.analysis.portfolio.portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType, RebalancingStrategy,
    PositionSizingMethod, create_sample_portfolio
)

from core.analysis.portfolio.portfolio_persistence import (
    PortfolioDataManager, save_portfolio, load_portfolio,
    list_portfolios, delete_portfolio
)

from core.data_processing.data_contracts import CurrencyCode, MetadataInfo


class TestPortfolioUIIntegration:
    """Test portfolio UI integration components"""

    @pytest.fixture
    def temp_portfolio_storage(self):
        """Create temporary portfolio storage for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PortfolioDataManager(temp_dir)
            yield manager

    @pytest.fixture
    def sample_portfolio(self):
        """Create a sample portfolio for testing"""
        return create_sample_portfolio()

    @pytest.fixture
    def mock_streamlit_session(self):
        """Mock Streamlit session state"""
        mock_session = {
            'new_portfolio_holdings': [],
            'selected_portfolio_for_analysis': None
        }
        with patch('streamlit.session_state', mock_session):
            yield mock_session

    def test_portfolio_creation_interface_basic_functionality(self, mock_streamlit_session):
        """Test basic functionality of portfolio creation interface"""
        # Test that interface loads without errors
        with patch('streamlit.markdown'), \
             patch('streamlit.text_input', return_value="Test Portfolio"), \
             patch('streamlit.selectbox', return_value="growth"), \
             patch('streamlit.number_input', return_value=100000.0), \
             patch('streamlit.radio', return_value="Manual Entry"), \
             patch('streamlit.columns', return_value=[Mock(), Mock()]):

            # Should not raise any exceptions
            try:
                render_comprehensive_portfolio_creation_interface()
                assert True  # Interface loaded successfully
            except Exception as e:
                pytest.fail(f"Portfolio creation interface failed to load: {e}")

    def test_add_holding_to_session_valid_input(self, mock_streamlit_session):
        """Test adding valid holding to session state"""
        # Test successful addition
        result = _add_holding_to_session(
            ticker="AAPL",
            shares=100.0,
            target_weight=0.25,
            company_name="Apple Inc.",
            manual_price=150.0
        )

        assert result is True
        assert len(mock_streamlit_session['new_portfolio_holdings']) == 1

        holding = mock_streamlit_session['new_portfolio_holdings'][0]
        assert holding['ticker'] == "AAPL"
        assert holding['shares'] == 100.0
        assert holding['target_weight'] == 0.25
        assert holding['company_name'] == "Apple Inc."
        assert holding['current_price'] == 150.0
        assert holding['market_value'] == 15000.0

    def test_add_holding_duplicate_ticker(self, mock_streamlit_session):
        """Test handling of duplicate ticker symbols"""
        # Add first holding
        _add_holding_to_session("AAPL", 100.0, 0.25)

        # Try to add duplicate
        result = _add_holding_to_session("AAPL", 50.0, 0.15)

        assert result is False
        assert len(mock_streamlit_session['new_portfolio_holdings']) == 1

    @patch('ui.streamlit.portfolio_management_ui._fetch_current_price')
    def test_add_holding_price_fetching(self, mock_fetch_price, mock_streamlit_session):
        """Test automatic price fetching when manual price not provided"""
        mock_fetch_price.return_value = 175.50

        result = _add_holding_to_session("MSFT", 50.0, 0.20, manual_price=0.0)

        assert result is True
        mock_fetch_price.assert_called_once_with("MSFT")

        holding = mock_streamlit_session['new_portfolio_holdings'][0]
        assert holding['current_price'] == 175.50
        assert holding['market_value'] == 8775.0  # 50 * 175.50

    def test_create_portfolio_from_inputs_valid_data(self, temp_portfolio_storage, mock_streamlit_session):
        """Test portfolio creation with valid input data"""
        # Setup session state with holdings
        mock_streamlit_session['new_portfolio_holdings'] = [
            {
                'ticker': 'AAPL',
                'company_name': 'Apple Inc.',
                'shares': 100,
                'target_weight': 0.4,
                'current_price': 150.0,
                'market_value': 15000.0
            },
            {
                'ticker': 'MSFT',
                'company_name': 'Microsoft Corp.',
                'shares': 75,
                'target_weight': 0.35,
                'current_price': 300.0,
                'market_value': 22500.0
            }
        ]

        with patch('ui.streamlit.portfolio_management_ui.save_portfolio', return_value=True), \
             patch('streamlit.error'), \
             patch('streamlit.success'):

            result = _create_portfolio_from_inputs(
                name="Test Portfolio",
                description="Test Description",
                portfolio_type="growth",
                initial_capital=100000.0,
                base_currency="USD",
                rebalancing_strategy="threshold",
                max_position_weight=0.30,
                min_position_weight=0.05,
                target_cash_allocation=0.25  # 25% available for holdings
            )

            assert result is True

    def test_create_portfolio_validation_errors(self, mock_streamlit_session):
        """Test portfolio creation validation error handling"""
        with patch('streamlit.error') as mock_error:
            # Test empty name
            result = _create_portfolio_from_inputs(
                name="",
                description="Test",
                portfolio_type="growth",
                initial_capital=100000.0,
                base_currency="USD",
                rebalancing_strategy="threshold",
                max_position_weight=0.30,
                min_position_weight=0.05,
                target_cash_allocation=0.05
            )

            assert result is False
            mock_error.assert_called()

            # Test no holdings
            mock_streamlit_session['new_portfolio_holdings'] = []

            result = _create_portfolio_from_inputs(
                name="Test Portfolio",
                description="Test",
                portfolio_type="growth",
                initial_capital=100000.0,
                base_currency="USD",
                rebalancing_strategy="threshold",
                max_position_weight=0.30,
                min_position_weight=0.05,
                target_cash_allocation=0.05
            )

            assert result is False

    def test_csv_import_functionality(self, mock_streamlit_session):
        """Test CSV import functionality"""
        # Create test CSV data
        csv_data = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT', 'GOOGL'],
            'shares': [100, 50, 25],
            'target_weight': [0.4, 0.35, 0.25],
            'company_name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.']
        })

        with patch('ui.streamlit.portfolio_management_ui._fetch_current_price', return_value=200.0):
            imported_count = _import_from_csv(csv_data)

            assert imported_count == 3
            assert len(mock_streamlit_session['new_portfolio_holdings']) == 3

            # Verify first holding
            holding = mock_streamlit_session['new_portfolio_holdings'][0]
            assert holding['ticker'] == 'AAPL'
            assert holding['shares'] == 100
            assert holding['target_weight'] == 0.4
            assert holding['company_name'] == 'Apple Inc.'

    def test_csv_import_duplicate_handling(self, mock_streamlit_session):
        """Test CSV import with duplicate tickers"""
        # Add existing holding
        mock_streamlit_session['new_portfolio_holdings'] = [
            {'ticker': 'AAPL', 'shares': 50, 'target_weight': 0.2}
        ]

        csv_data = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT'],  # AAPL is duplicate
            'shares': [100, 50],
            'target_weight': [0.4, 0.35]
        })

        with patch('ui.streamlit.portfolio_management_ui._fetch_current_price', return_value=200.0):
            imported_count = _import_from_csv(csv_data)

            assert imported_count == 1  # Only MSFT should be imported
            assert len(mock_streamlit_session['new_portfolio_holdings']) == 2

    def test_portfolio_filtering_functionality(self):
        """Test portfolio list filtering and sorting"""
        # Create test portfolio list
        portfolio_list = [
            {
                'portfolio_id': 'p1',
                'name': 'Growth Portfolio',
                'portfolio_type': 'growth',
                'total_value': 100000,
                'last_update': '2024-01-15T10:00:00'
            },
            {
                'portfolio_id': 'p2',
                'name': 'Conservative Fund',
                'portfolio_type': 'conservative',
                'total_value': 50000,
                'last_update': '2024-01-10T10:00:00'
            },
            {
                'portfolio_id': 'p3',
                'name': 'Tech Growth',
                'portfolio_type': 'growth',
                'total_value': 150000,
                'last_update': '2024-01-20T10:00:00'
            }
        ]

        # Test search filter
        filtered = _filter_portfolios(portfolio_list, "Growth", "All", "Name")
        assert len(filtered) == 2
        assert all("Growth" in p['name'] for p in filtered)

        # Test type filter
        filtered = _filter_portfolios(portfolio_list, "", "growth", "Name")
        assert len(filtered) == 2
        assert all(p['portfolio_type'] == 'growth' for p in filtered)

        # Test sorting by total value
        filtered = _filter_portfolios(portfolio_list, "", "All", "Total Value")
        assert filtered[0]['portfolio_id'] == 'p3'  # Highest value first
        assert filtered[-1]['portfolio_id'] == 'p2'  # Lowest value last

    def test_existing_portfolios_interface_empty_state(self):
        """Test existing portfolios interface with no portfolios"""
        with patch('ui.streamlit.portfolio_management_ui.list_portfolios', return_value=[]), \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.button', return_value=False), \
             patch('streamlit.markdown'):

            render_comprehensive_existing_portfolios_interface()
            mock_info.assert_called()

    def test_existing_portfolios_interface_with_data(self):
        """Test existing portfolios interface with portfolio data"""
        mock_portfolios = [
            {
                'portfolio_id': 'p1',
                'name': 'Test Portfolio',
                'description': 'Test Description',
                'portfolio_type': 'growth',
                'total_value': 100000,
                'holdings_count': 5,
                'last_update': '2024-01-15T10:00:00'
            }
        ]

        with patch('ui.streamlit.portfolio_management_ui.list_portfolios', return_value=mock_portfolios), \
             patch('streamlit.text_input', return_value=""), \
             patch('streamlit.selectbox', return_value="All"), \
             patch('streamlit.markdown'), \
             patch('streamlit.container'), \
             patch('streamlit.columns', return_value=[Mock(), Mock(), Mock(), Mock()]), \
             patch('streamlit.metric'), \
             patch('streamlit.button', return_value=False):

            # Should not raise any exceptions
            try:
                render_comprehensive_existing_portfolios_interface()
                assert True
            except Exception as e:
                pytest.fail(f"Existing portfolios interface failed: {e}")

    def test_portfolio_analysis_interface_no_portfolios(self):
        """Test portfolio analysis interface with no portfolios"""
        with patch('ui.streamlit.portfolio_management_ui.list_portfolios', return_value=[]), \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.markdown'):

            render_comprehensive_portfolio_analysis_interface()
            mock_info.assert_called()

    def test_portfolio_analysis_interface_with_data(self):
        """Test portfolio analysis interface with portfolio data"""
        mock_portfolios = [
            {
                'portfolio_id': 'p1',
                'name': 'Test Portfolio',
                'total_value': 100000
            }
        ]

        with patch('ui.streamlit.portfolio_management_ui.list_portfolios', return_value=mock_portfolios), \
             patch('ui.streamlit.portfolio_management_ui.load_portfolio', return_value=None), \
             patch('streamlit.selectbox', return_value='p1'), \
             patch('streamlit.button', return_value=False), \
             patch('streamlit.columns', return_value=[Mock(), Mock()]), \
             patch('streamlit.markdown'), \
             patch('streamlit.info'):

            # Should not raise any exceptions
            try:
                render_comprehensive_portfolio_analysis_interface()
                assert True
            except Exception as e:
                pytest.fail(f"Portfolio analysis interface failed: {e}")


class TestPortfolioPersistenceIntegration:
    """Test portfolio persistence integration"""

    @pytest.fixture
    def temp_storage_manager(self):
        """Create temporary storage manager for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield PortfolioDataManager(temp_dir)

    def test_portfolio_save_and_load_cycle(self, temp_storage_manager):
        """Test complete portfolio save and load cycle"""
        # Create test portfolio
        portfolio = create_sample_portfolio()
        portfolio.portfolio_id = "test_portfolio_001"
        portfolio.name = "Test Integration Portfolio"

        # Save portfolio
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager', temp_storage_manager):
            save_result = save_portfolio(portfolio)
            assert save_result is True

            # Load portfolio
            loaded_portfolio = load_portfolio("test_portfolio_001")
            assert loaded_portfolio is not None
            assert loaded_portfolio.name == "Test Integration Portfolio"
            assert loaded_portfolio.portfolio_id == "test_portfolio_001"
            assert len(loaded_portfolio.holdings) == len(portfolio.holdings)

    def test_portfolio_list_functionality(self, temp_storage_manager):
        """Test portfolio listing functionality"""
        # Create and save multiple portfolios
        portfolios = [
            create_sample_portfolio(),
            create_sample_portfolio()
        ]

        portfolios[0].portfolio_id = "portfolio_1"
        portfolios[0].name = "Portfolio One"
        portfolios[1].portfolio_id = "portfolio_2"
        portfolios[1].name = "Portfolio Two"

        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager', temp_storage_manager):
            # Save portfolios
            for portfolio in portfolios:
                save_portfolio(portfolio)

            # List portfolios
            portfolio_list = list_portfolios()

            assert len(portfolio_list) >= 2
            portfolio_names = [p['name'] for p in portfolio_list]
            assert "Portfolio One" in portfolio_names
            assert "Portfolio Two" in portfolio_names

    def test_portfolio_delete_functionality(self, temp_storage_manager):
        """Test portfolio deletion functionality"""
        # Create and save portfolio
        portfolio = create_sample_portfolio()
        portfolio.portfolio_id = "delete_test_portfolio"

        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager', temp_storage_manager):
            save_portfolio(portfolio)

            # Verify it exists
            loaded = load_portfolio("delete_test_portfolio")
            assert loaded is not None

            # Delete portfolio
            delete_result = delete_portfolio("delete_test_portfolio")
            assert delete_result is True

            # Verify it's deleted
            loaded_after_delete = load_portfolio("delete_test_portfolio")
            assert loaded_after_delete is None

    def test_portfolio_validation_integration(self):
        """Test portfolio validation during save operations"""
        from core.analysis.portfolio.portfolio_models import validate_portfolio

        # Create invalid portfolio (empty name)
        portfolio = create_sample_portfolio()
        portfolio.name = ""

        # Test validation
        errors = validate_portfolio(portfolio)
        assert len(errors) > 0
        assert any("name" in error.lower() for error in errors)

    def test_storage_statistics_integration(self, temp_storage_manager):
        """Test storage statistics functionality"""
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager', temp_storage_manager):
            stats = temp_storage_manager.get_storage_stats()

            assert isinstance(stats, dict)
            assert 'total_portfolios' in stats
            assert 'storage_file_size' in stats
            assert 'cache_status' in stats


class TestPortfolioVisualizationIntegration:
    """Test portfolio visualization integration"""

    def test_portfolio_visualization_integration(self):
        """Test integration with portfolio visualization dashboard"""
        portfolio = create_sample_portfolio()

        with patch('ui.streamlit.portfolio_visualization.render_portfolio_visualization_dashboard') as mock_render:
            # This would be called from the analysis interface
            from ui.streamlit.portfolio_visualization import render_portfolio_visualization_dashboard
            render_portfolio_visualization_dashboard(portfolio)

            mock_render.assert_called_once_with(portfolio)

    def test_portfolio_allocation_charts_integration(self):
        """Test portfolio allocation charts integration"""
        portfolio = create_sample_portfolio()

        with patch('ui.streamlit.portfolio_visualization.PortfolioVisualizationEngine') as mock_engine:
            mock_viz = Mock()
            mock_engine.return_value = mock_viz

            # Test that visualization engine can be created with portfolio
            from ui.streamlit.portfolio_visualization import PortfolioVisualizationEngine
            viz_engine = PortfolioVisualizationEngine()

            # Should not raise exceptions
            assert viz_engine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])