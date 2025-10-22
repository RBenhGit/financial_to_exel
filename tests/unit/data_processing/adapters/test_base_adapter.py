"""
Unit Tests for BaseAdapter and Adapter Types
=============================================

Tests the enhanced BaseApiAdapter abstract class, standardized types,
and validation framework.
"""

import pytest
import threading
from datetime import datetime
from unittest.mock import Mock, MagicMock

from core.data_processing.adapters import (
    BaseApiAdapter,
    GeneralizedVariableDict,
    AdapterOutputMetadata,
    ValidationResult,
    AdapterException,
    AdapterStatus,
    AdapterInfo,
    AdapterValidator,
    DataSourceType,
    DataCategory,
    ApiCapabilities
)


class MockAdapter(BaseApiAdapter):
    """Mock adapter for testing BaseApiAdapter functionality"""

    def get_source_type(self) -> DataSourceType:
        return DataSourceType.YFINANCE

    def get_capabilities(self) -> ApiCapabilities:
        return ApiCapabilities(
            source_type=DataSourceType.YFINANCE,
            supported_categories=[DataCategory.MARKET_DATA],
            rate_limit_per_minute=60,
            rate_limit_per_day=None,
            max_historical_years=5,
            requires_api_key=False,
            supports_batch_requests=False,
            real_time_data=True,
            cost_per_request=None,
            reliability_rating=0.9
        )

    def validate_credentials(self) -> bool:
        return True

    def load_symbol_data(self, symbol, categories=None, historical_years=5, validate_data=True):
        return Mock()

    def get_available_data(self, symbol):
        return {}

    def extract_variables(self, symbol, period="latest", historical_years=10) -> GeneralizedVariableDict:
        """Mock implementation returning sample data"""
        return {
            'ticker': symbol,
            'company_name': f'{symbol} Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'December',
            'revenue': 100000.0,
            'net_income': 20000.0,
            'total_assets': 500000.0,
            'market_cap': 1000000.0,
            'stock_price': 150.0
        }

    def get_extraction_metadata(self) -> AdapterOutputMetadata:
        """Return last extraction metadata"""
        return self._last_metadata or AdapterOutputMetadata(
            source='test',
            timestamp=datetime.now(),
            quality_score=0.9,
            completeness=0.8,
            validation_errors=[]
        )

    def validate_output(self, variables: GeneralizedVariableDict) -> ValidationResult:
        """Validate output using built-in methods"""
        result = ValidationResult(valid=True)

        # Use parent class validation methods
        required_check = self.validate_required_fields(variables)
        type_check = self.validate_data_types(variables)

        result.merge(required_check)
        result.merge(type_check)

        return result

    def get_supported_variable_categories(self):
        return ['income_statement', 'balance_sheet', 'market_data']


class TestGeneralizedVariableDict:
    """Test GeneralizedVariableDict type definition"""

    def test_create_minimal_dict(self):
        """Test creating dict with only required fields"""
        data: GeneralizedVariableDict = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September'
        }

        assert data['ticker'] == 'AAPL'
        assert data['company_name'] == 'Apple Inc.'

    def test_create_full_dict(self):
        """Test creating dict with many fields"""
        data: GeneralizedVariableDict = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September',
            'revenue': 394328.0,
            'net_income': 96995.0,
            'total_assets': 352755.0,
            'cash_and_cash_equivalents': 62639.0,
            'market_cap': 2900000.0,
            'pe_ratio': 29.5
        }

        assert data['revenue'] == 394328.0
        assert data['pe_ratio'] == 29.5


class TestAdapterOutputMetadata:
    """Test AdapterOutputMetadata dataclass"""

    def test_create_metadata(self):
        """Test creating metadata object"""
        metadata = AdapterOutputMetadata(
            source='yfinance',
            timestamp=datetime(2025, 1, 1),
            quality_score=0.95,
            completeness=0.88,
            validation_errors=['minor issue'],
            extraction_time=1.5
        )

        assert metadata.source == 'yfinance'
        assert metadata.quality_score == 0.95
        assert metadata.completeness == 0.88
        assert len(metadata.validation_errors) == 1

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary"""
        metadata = AdapterOutputMetadata(
            source='fmp',
            timestamp=datetime(2025, 1, 1),
            quality_score=0.9,
            completeness=0.85
        )

        result = metadata.to_dict()

        assert result['source'] == 'fmp'
        assert result['quality_score'] == 0.9
        assert isinstance(result['timestamp'], str)


class TestValidationResult:
    """Test ValidationResult dataclass"""

    def test_create_valid_result(self):
        """Test creating valid result"""
        result = ValidationResult(valid=True)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_add_error(self):
        """Test adding error marks result invalid"""
        result = ValidationResult(valid=True)
        result.add_error("Test error")

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "Test error"

    def test_merge_results(self):
        """Test merging multiple validation results"""
        result1 = ValidationResult(valid=True)
        result1.add_warning("Warning 1")

        result2 = ValidationResult(valid=False)
        result2.add_error("Error 1")

        result1.merge(result2)

        assert result1.valid is False
        assert len(result1.errors) == 1
        assert len(result1.warnings) == 1


class TestAdapterException:
    """Test AdapterException class"""

    def test_create_exception(self):
        """Test creating adapter exception"""
        exc = AdapterException(
            "Test error",
            source="yfinance",
            details={'symbol': 'AAPL'}
        )

        assert str(exc).startswith("Test error")
        assert exc.source == "yfinance"
        assert exc.details['symbol'] == 'AAPL'

    def test_exception_with_original(self):
        """Test exception wrapping another exception"""
        original = ValueError("Original error")
        exc = AdapterException(
            "Wrapped error",
            original_exception=original
        )

        assert exc.original_exception == original
        assert "Original error" in str(exc)


class TestBaseApiAdapter:
    """Test BaseApiAdapter abstract class"""

    def test_adapter_initialization(self):
        """Test adapter initializes correctly"""
        adapter = MockAdapter()

        assert adapter.timeout == 30
        assert adapter.max_retries == 3
        assert adapter._status == AdapterStatus.READY
        assert isinstance(adapter._lock, type(threading.RLock()))

    def test_normalize_symbol(self):
        """Test symbol normalization"""
        adapter = MockAdapter()

        assert adapter.normalize_symbol('aapl') == 'AAPL'
        assert adapter.normalize_symbol('  msft  ') == 'MSFT'

    def test_thread_safe_status(self):
        """Test thread-safe status management"""
        adapter = MockAdapter()

        assert adapter.get_status() == AdapterStatus.READY

        adapter.set_status(AdapterStatus.BUSY)
        assert adapter.get_status() == AdapterStatus.BUSY

    def test_get_adapter_info(self):
        """Test getting adapter information"""
        adapter = MockAdapter()
        info = adapter.get_adapter_info()

        assert isinstance(info, AdapterInfo)
        assert info.adapter_type == 'yfinance'
        assert info.status == AdapterStatus.READY
        assert info.requires_api_key is False

    def test_validate_required_fields(self):
        """Test required fields validation"""
        adapter = MockAdapter()

        # Valid data
        valid_data = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September'
        }

        result = adapter.validate_required_fields(valid_data)
        assert result.valid is True

        # Missing field
        invalid_data = {
            'ticker': 'AAPL',
            'currency': 'USD'
        }

        result = adapter.validate_required_fields(invalid_data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_calculate_completeness_score(self):
        """Test completeness score calculation"""
        adapter = MockAdapter()

        # Minimal data
        minimal_data = {
            'ticker': 'AAPL',
            'company_name': 'Apple',
            'currency': 'USD',
            'fiscal_year_end': 'Dec'
        }

        score = adapter.calculate_completeness_score(minimal_data)
        assert 0.0 <= score <= 1.0
        assert score < 0.1  # Very few optional fields

        # More complete data
        complete_data = minimal_data.copy()
        complete_data.update({
            'revenue': 100000.0,
            'net_income': 20000.0,
            'total_assets': 500000.0,
            'total_liabilities': 300000.0,
            'operating_cash_flow': 30000.0,
            'market_cap': 2000000.0,
            'stock_price': 150.0
        })

        score2 = adapter.calculate_completeness_score(complete_data)
        assert score2 > score  # Should be more complete

    def test_generate_composite_variables(self):
        """Test composite variable generation"""
        adapter = MockAdapter()

        variables = {
            'operating_cash_flow': 30000.0,
            'capital_expenditures': -5000.0,
            'revenue': 100000.0,
            'cost_of_revenue': 60000.0,
            'total_current_assets': 50000.0,
            'total_current_liabilities': 30000.0
        }

        composite = adapter.generate_composite_variables(variables)

        # Should generate FCF, gross profit, working capital
        assert 'free_cash_flow' in composite
        assert composite['free_cash_flow'] == 35000.0  # 30000 - (-5000)

        assert 'gross_profit' in composite
        assert composite['gross_profit'] == 40000.0  # 100000 - 60000

        assert 'working_capital' in composite
        assert composite['working_capital'] == 20000.0  # 50000 - 30000

    def test_safe_extract_with_lock(self):
        """Test thread-safe extraction wrapper"""
        adapter = MockAdapter()

        result = adapter.safe_extract_with_lock('AAPL')

        assert result['ticker'] == 'AAPL'
        assert adapter.get_status() == AdapterStatus.READY
        assert adapter._last_metadata is not None


class TestAdapterValidator:
    """Test AdapterValidator class"""

    def test_validator_initialization(self):
        """Test validator initializes"""
        validator = AdapterValidator()
        assert validator is not None

    def test_validate_required_fields(self):
        """Test required field validation"""
        validator = AdapterValidator()

        valid_data = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September'
        }

        result = validator.validate_required_fields(valid_data)
        assert result.valid is True

        invalid_data = {'ticker': 'AAPL'}
        result = validator.validate_required_fields(invalid_data)
        assert result.valid is False

    def test_validate_value_ranges(self):
        """Test value range validation"""
        validator = AdapterValidator()

        # Valid ranges
        valid_data = {
            'ticker': 'AAPL',
            'company_name': 'Apple',
            'currency': 'USD',
            'fiscal_year_end': 'Dec',
            'revenue': 100000.0,
            'total_assets': 500000.0,
            'market_cap': 2000000.0,
            'stock_price': 150.0,
            'pe_ratio': 25.0
        }

        result = validator.validate_value_ranges(valid_data)
        assert result.valid is True

        # Negative values where shouldn't be
        invalid_data = valid_data.copy()
        invalid_data['revenue'] = -100000.0

        result = validator.validate_value_ranges(invalid_data)
        assert result.valid is False
        assert len(result.errors) > 0

    def test_validate_completeness(self):
        """Test completeness validation"""
        validator = AdapterValidator()

        minimal_data = {
            'ticker': 'AAPL',
            'company_name': 'Apple',
            'currency': 'USD',
            'fiscal_year_end': 'Dec'
        }

        result = validator.validate_completeness(minimal_data)
        # Should have low completeness but still be valid
        assert 'overall_completeness' in result.details
        assert result.details['overall_completeness'] < 0.1

    def test_validate_all(self):
        """Test comprehensive validation"""
        validator = AdapterValidator()

        data = {
            'ticker': 'AAPL',
            'company_name': 'Apple Inc.',
            'currency': 'USD',
            'fiscal_year_end': 'September',
            'revenue': 394328.0,
            'net_income': 96995.0,
            'total_assets': 352755.0,
            'market_cap': 2900000.0,
            'pe_ratio': 29.5
        }

        result = validator.validate_all(data)

        assert 'total_fields' in result.details
        assert 'total_errors' in result.details
        assert result.details['total_fields'] == len(data)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
