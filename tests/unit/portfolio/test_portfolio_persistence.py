"""
Portfolio Persistence Unit Tests
===============================

Unit tests for the portfolio persistence system, testing data storage,
retrieval, validation, and error handling capabilities.

Test Coverage:
- Portfolio serialization and deserialization
- File storage operations
- Data validation and error handling
- Backup and versioning functionality
- Import/export capabilities
- Cache management
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, date
from unittest.mock import Mock, patch, mock_open

from core.analysis.portfolio.portfolio_persistence import (
    PortfolioDataManager, PortfolioStorageError, PortfolioVersionError,
    get_portfolio_manager, save_portfolio, load_portfolio,
    list_portfolios, delete_portfolio
)

from core.analysis.portfolio.portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType, RebalancingStrategy,
    PositionSizingMethod, create_sample_portfolio
)

from core.data_processing.data_contracts import CurrencyCode, MetadataInfo


class TestPortfolioDataManager:
    """Test PortfolioDataManager functionality"""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary directory for storage testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def portfolio_manager(self, temp_storage_path):
        """Create portfolio manager with temporary storage"""
        return PortfolioDataManager(temp_storage_path)

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        return create_sample_portfolio()

    def test_portfolio_manager_initialization(self, temp_storage_path):
        """Test portfolio manager initialization"""
        manager = PortfolioDataManager(temp_storage_path)

        # Check directories are created
        assert Path(temp_storage_path).exists()
        assert (Path(temp_storage_path) / "backups").exists()
        assert (Path(temp_storage_path) / "exports").exists()

        # Check default portfolio file is created
        portfolios_file = Path(temp_storage_path) / "user_portfolios.json"
        assert portfolios_file.exists()

        # Check default data structure
        with open(portfolios_file, 'r') as f:
            data = json.load(f)

        assert 'version' in data
        assert 'portfolios' in data
        assert 'metadata' in data
        assert isinstance(data['portfolios'], dict)

    def test_portfolio_to_dict_conversion(self, portfolio_manager, sample_portfolio):
        """Test portfolio to dictionary conversion"""
        portfolio_dict = portfolio_manager._portfolio_to_dict(sample_portfolio)

        # Check basic structure
        assert isinstance(portfolio_dict, dict)
        assert 'portfolio_id' in portfolio_dict
        assert 'name' in portfolio_dict
        assert 'holdings' in portfolio_dict
        assert '_persistence_metadata' in portfolio_dict

        # Check enum conversions
        assert portfolio_dict['portfolio_type'] == sample_portfolio.portfolio_type.value
        assert portfolio_dict['rebalancing_strategy'] == sample_portfolio.rebalancing_strategy.value

        # Check date conversions
        if sample_portfolio.inception_date:
            assert isinstance(portfolio_dict['inception_date'], str)

    def test_dict_to_portfolio_conversion(self, portfolio_manager, sample_portfolio):
        """Test dictionary to portfolio conversion"""
        # Convert to dict and back
        portfolio_dict = portfolio_manager._portfolio_to_dict(sample_portfolio)
        converted_portfolio = portfolio_manager._dict_to_portfolio(portfolio_dict)

        # Check basic attributes
        assert converted_portfolio.portfolio_id == sample_portfolio.portfolio_id
        assert converted_portfolio.name == sample_portfolio.name
        assert converted_portfolio.portfolio_type == sample_portfolio.portfolio_type
        assert len(converted_portfolio.holdings) == len(sample_portfolio.holdings)

        # Check holdings conversion
        for orig_holding, conv_holding in zip(sample_portfolio.holdings, converted_portfolio.holdings):
            assert orig_holding.ticker == conv_holding.ticker
            assert orig_holding.shares == conv_holding.shares
            assert orig_holding.target_weight == conv_holding.target_weight

    def test_save_portfolio_success(self, portfolio_manager, sample_portfolio):
        """Test successful portfolio save operation"""
        result = portfolio_manager.save_portfolio(sample_portfolio)

        assert result is True

        # Check file was updated
        portfolios_file = portfolio_manager.portfolios_file
        assert portfolios_file.exists()

        with open(portfolios_file, 'r') as f:
            data = json.load(f)

        assert sample_portfolio.portfolio_id in data['portfolios']

    def test_save_portfolio_validation_error(self, portfolio_manager):
        """Test portfolio save with validation errors"""
        # Create invalid portfolio
        invalid_portfolio = Portfolio(
            portfolio_id="",  # Invalid empty ID
            name="",  # Invalid empty name
            holdings=[]
        )

        result = portfolio_manager.save_portfolio(invalid_portfolio)
        assert result is False

    def test_load_portfolio_success(self, portfolio_manager, sample_portfolio):
        """Test successful portfolio load operation"""
        # Save first
        portfolio_manager.save_portfolio(sample_portfolio)

        # Load
        loaded_portfolio = portfolio_manager.load_portfolio(sample_portfolio.portfolio_id)

        assert loaded_portfolio is not None
        assert loaded_portfolio.portfolio_id == sample_portfolio.portfolio_id
        assert loaded_portfolio.name == sample_portfolio.name
        assert len(loaded_portfolio.holdings) == len(sample_portfolio.holdings)

    def test_load_portfolio_not_found(self, portfolio_manager):
        """Test loading non-existent portfolio"""
        loaded_portfolio = portfolio_manager.load_portfolio("non_existent_id")
        assert loaded_portfolio is None

    def test_list_portfolios_empty(self, portfolio_manager):
        """Test listing portfolios when storage is empty"""
        # Clear default sample portfolio
        data = portfolio_manager._load_portfolio_data()
        data['portfolios'] = {}
        portfolio_manager._save_portfolio_data(data)

        portfolio_list = portfolio_manager.list_portfolios()
        assert isinstance(portfolio_list, list)
        assert len(portfolio_list) == 0

    def test_list_portfolios_with_data(self, portfolio_manager, sample_portfolio):
        """Test listing portfolios with data"""
        # Save portfolio
        portfolio_manager.save_portfolio(sample_portfolio)

        portfolio_list = portfolio_manager.list_portfolios()

        assert len(portfolio_list) >= 1
        assert any(p['portfolio_id'] == sample_portfolio.portfolio_id for p in portfolio_list)

        # Check summary structure
        portfolio_summary = next(p for p in portfolio_list if p['portfolio_id'] == sample_portfolio.portfolio_id)
        assert 'name' in portfolio_summary
        assert 'portfolio_type' in portfolio_summary
        assert 'holdings_count' in portfolio_summary
        assert 'total_value' in portfolio_summary

    def test_delete_portfolio_success(self, portfolio_manager, sample_portfolio):
        """Test successful portfolio deletion"""
        # Save first
        portfolio_manager.save_portfolio(sample_portfolio)

        # Delete
        result = portfolio_manager.delete_portfolio(sample_portfolio.portfolio_id)
        assert result is True

        # Verify deletion
        loaded = portfolio_manager.load_portfolio(sample_portfolio.portfolio_id)
        assert loaded is None

    def test_delete_portfolio_not_found(self, portfolio_manager):
        """Test deleting non-existent portfolio"""
        result = portfolio_manager.delete_portfolio("non_existent_id")
        assert result is False

    def test_export_portfolio_json(self, portfolio_manager, sample_portfolio):
        """Test portfolio export to JSON"""
        # Save portfolio first
        portfolio_manager.save_portfolio(sample_portfolio)

        # Export
        export_path = portfolio_manager.export_portfolio(sample_portfolio.portfolio_id, 'json')

        assert export_path is not None
        assert Path(export_path).exists()
        assert export_path.endswith('.json')

        # Verify export content
        with open(export_path, 'r') as f:
            exported_data = json.load(f)

        assert exported_data['portfolio_id'] == sample_portfolio.portfolio_id
        assert exported_data['name'] == sample_portfolio.name

    def test_export_portfolio_not_found(self, portfolio_manager):
        """Test exporting non-existent portfolio"""
        export_path = portfolio_manager.export_portfolio("non_existent_id", 'json')
        assert export_path is None

    def test_import_portfolio_json(self, portfolio_manager, temp_storage_path):
        """Test portfolio import from JSON"""
        # Create test JSON file
        test_portfolio_data = {
            "portfolio_id": "imported_test",
            "name": "Imported Test Portfolio",
            "portfolio_type": "growth",
            "rebalancing_strategy": "threshold",
            "position_sizing_method": "equal_weight",
            "base_currency": "USD",
            "holdings": [],
            "cash_position": 10000.0,
            "target_cash_allocation": 0.1,
            "inception_date": "2024-01-01"
        }

        test_file = Path(temp_storage_path) / "test_import.json"
        with open(test_file, 'w') as f:
            json.dump(test_portfolio_data, f)

        # Import portfolio
        imported_portfolio = portfolio_manager.import_portfolio(str(test_file))

        assert imported_portfolio is not None
        assert imported_portfolio.name == "Imported Test Portfolio"
        assert imported_portfolio.portfolio_type == PortfolioType.GROWTH
        assert imported_portfolio.portfolio_id.startswith("imported_")  # ID should be regenerated

    def test_import_portfolio_file_not_found(self, portfolio_manager):
        """Test importing from non-existent file"""
        imported_portfolio = portfolio_manager.import_portfolio("non_existent_file.json")
        assert imported_portfolio is None

    def test_backup_creation(self, portfolio_manager, sample_portfolio):
        """Test backup file creation"""
        # Save portfolio to create initial file
        portfolio_manager.save_portfolio(sample_portfolio)

        # Create backup manually
        portfolio_manager._create_backup()

        # Check backup was created
        backup_files = list(portfolio_manager.backups_dir.glob("portfolios_backup_*.json"))
        assert len(backup_files) > 0

    def test_backup_cleanup(self, portfolio_manager):
        """Test backup cleanup functionality"""
        # Create multiple backup files
        for i in range(15):  # More than max_backups (10)
            backup_file = portfolio_manager.backups_dir / f"portfolios_backup_test_{i:02d}.json"
            backup_file.write_text('{}')

        # Trigger cleanup
        portfolio_manager._cleanup_old_backups(max_backups=5)

        # Check only 5 backups remain
        backup_files = list(portfolio_manager.backups_dir.glob("portfolios_backup_*.json"))
        assert len(backup_files) == 5

    def test_cache_refresh_functionality(self, portfolio_manager, sample_portfolio):
        """Test cache refresh functionality"""
        # Save portfolio
        portfolio_manager.save_portfolio(sample_portfolio)

        # Load portfolio (should populate cache)
        loaded1 = portfolio_manager.load_portfolio(sample_portfolio.portfolio_id)
        assert loaded1 is not None

        # Verify cache timestamp is set
        assert portfolio_manager._cache_timestamp is not None
        assert sample_portfolio.portfolio_id in portfolio_manager._portfolio_cache

        # Load again (should use cache)
        loaded2 = portfolio_manager.load_portfolio(sample_portfolio.portfolio_id)
        assert loaded2 is not None

    def test_storage_statistics(self, portfolio_manager, sample_portfolio):
        """Test storage statistics functionality"""
        # Save portfolio
        portfolio_manager.save_portfolio(sample_portfolio)

        stats = portfolio_manager.get_storage_stats()

        assert isinstance(stats, dict)
        assert 'total_portfolios' in stats
        assert 'storage_file_size' in stats
        assert 'backup_count' in stats
        assert 'cache_status' in stats

        assert stats['total_portfolios'] >= 1
        assert stats['storage_file_size'] > 0

    def test_json_serializer_custom_objects(self, portfolio_manager):
        """Test custom JSON serializer for special objects"""
        # Test date serialization
        test_date = date(2024, 1, 1)
        result = portfolio_manager._json_serializer(test_date)
        assert result == "2024-01-01"

        # Test datetime serialization
        test_datetime = datetime(2024, 1, 1, 12, 30, 0)
        result = portfolio_manager._json_serializer(test_datetime)
        assert result == "2024-01-01T12:30:00"

        # Test enum serialization
        portfolio_type = PortfolioType.GROWTH
        result = portfolio_manager._json_serializer(portfolio_type)
        assert result == "growth"

    def test_error_handling_corrupted_file(self, portfolio_manager):
        """Test error handling with corrupted portfolio file"""
        # Create corrupted JSON file
        with open(portfolio_manager.portfolios_file, 'w') as f:
            f.write("invalid json content {")

        # Should handle error gracefully
        with pytest.raises(PortfolioStorageError):
            portfolio_manager._load_portfolio_data()

    def test_error_handling_invalid_structure(self, portfolio_manager):
        """Test error handling with invalid data structure"""
        # Create file with invalid structure
        invalid_data = {"invalid": "structure"}
        with open(portfolio_manager.portfolios_file, 'w') as f:
            json.dump(invalid_data, f)

        # Should handle error gracefully
        with pytest.raises(PortfolioStorageError):
            portfolio_manager._load_portfolio_data()


class TestPortfolioPersistenceGlobalFunctions:
    """Test global convenience functions"""

    @pytest.fixture
    def temp_storage_path(self):
        """Create temporary directory for storage testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_global_save_portfolio(self, temp_storage_path):
        """Test global save_portfolio function"""
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.save_portfolio.return_value = True
            mock_manager = mock_manager_instance

            portfolio = create_sample_portfolio()
            result = save_portfolio(portfolio)

            assert result is True
            mock_manager.save_portfolio.assert_called_once_with(portfolio)

    def test_global_load_portfolio(self, temp_storage_path):
        """Test global load_portfolio function"""
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_portfolio = create_sample_portfolio()
            mock_manager_instance.load_portfolio.return_value = mock_portfolio
            mock_manager = mock_manager_instance

            result = load_portfolio("test_id")

            assert result == mock_portfolio
            mock_manager.load_portfolio.assert_called_once_with("test_id")

    def test_global_list_portfolios(self, temp_storage_path):
        """Test global list_portfolios function"""
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_list = [{'portfolio_id': 'test', 'name': 'Test Portfolio'}]
            mock_manager_instance.list_portfolios.return_value = mock_list
            mock_manager = mock_manager_instance

            result = list_portfolios()

            assert result == mock_list
            mock_manager.list_portfolios.assert_called_once()

    def test_global_delete_portfolio(self, temp_storage_path):
        """Test global delete_portfolio function"""
        with patch('core.analysis.portfolio.portfolio_persistence._portfolio_manager') as mock_manager:
            mock_manager_instance = Mock()
            mock_manager_instance.delete_portfolio.return_value = True
            mock_manager = mock_manager_instance

            result = delete_portfolio("test_id")

            assert result is True
            mock_manager.delete_portfolio.assert_called_once_with("test_id")

    def test_get_portfolio_manager_singleton(self):
        """Test that get_portfolio_manager returns singleton instance"""
        manager1 = get_portfolio_manager()
        manager2 = get_portfolio_manager()

        assert manager1 is manager2  # Should be same instance


class TestPortfolioDataValidation:
    """Test portfolio data validation during persistence operations"""

    def test_portfolio_validation_integration(self):
        """Test integration with portfolio validation"""
        from core.analysis.portfolio.portfolio_models import validate_portfolio

        # Create portfolio with validation issues
        portfolio = Portfolio(
            portfolio_id="test",
            name="",  # Empty name should cause validation error
            holdings=[]
        )

        errors = validate_portfolio(portfolio)
        assert len(errors) > 0

    def test_holding_data_integrity(self):
        """Test holding data integrity during serialization"""
        # Create portfolio with complex holdings
        holding = PortfolioHolding(
            ticker="AAPL",
            company_name="Apple Inc.",
            shares=100.5,
            current_price=150.75,
            target_weight=0.25,
            purchase_date=date(2024, 1, 1),
            metadata=MetadataInfo()
        )

        portfolio = Portfolio(
            portfolio_id="integrity_test",
            name="Integrity Test Portfolio",
            holdings=[holding]
        )

        # Test serialization preserves data integrity
        with tempfile.TemporaryDirectory() as temp_dir:
            manager = PortfolioDataManager(temp_dir)
            manager.save_portfolio(portfolio)

            loaded_portfolio = manager.load_portfolio("integrity_test")

            assert loaded_portfolio is not None
            assert len(loaded_portfolio.holdings) == 1

            loaded_holding = loaded_portfolio.holdings[0]
            assert loaded_holding.ticker == "AAPL"
            assert loaded_holding.shares == 100.5
            assert loaded_holding.current_price == 150.75
            assert loaded_holding.target_weight == 0.25
            assert loaded_holding.purchase_date == date(2024, 1, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])