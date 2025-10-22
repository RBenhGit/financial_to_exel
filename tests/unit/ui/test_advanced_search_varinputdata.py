"""
Test VarInputData Integration in Advanced Search Filter
========================================================

Tests to verify that advanced_search_filter.py correctly uses VarInputData
for fetching company metadata, search functionality, and filtering.

Task 234: Standardize Export Layer Data Access
Related File: ui/streamlit/advanced_search_filter.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import pickle

# Import the search filter components
from ui.streamlit.advanced_search_filter import (
    CompanyInfo,
    FilterCriteria,
    CompanyDataCache,
    AdvancedSearchFilter
)


class TestCompanyInfoVarInputDataIntegration:
    """Test CompanyInfo creation from VarInputData"""

    def test_company_info_dataclass_structure(self):
        """Test that CompanyInfo dataclass has all required fields"""
        company = CompanyInfo(
            symbol="AAPL",
            name="Apple Inc.",
            sector="Technology",
            industry="Consumer Electronics",
            market_cap=2500000000000,
            country="United States",
            exchange="NASDAQ",
            currency="USD",
            employees=164000,
            website="https://www.apple.com",
            description="Technology company"
        )

        assert company.symbol == "AAPL"
        assert company.name == "Apple Inc."
        assert company.sector == "Technology"
        assert company.market_cap == 2500000000000

    def test_company_info_to_dict(self):
        """Test CompanyInfo conversion to dictionary"""
        company = CompanyInfo(
            symbol="AAPL",
            name="Apple Inc."
        )

        company_dict = company.to_dict()
        assert isinstance(company_dict, dict)
        assert company_dict['symbol'] == "AAPL"
        assert company_dict['name'] == "Apple Inc."

    def test_company_info_from_dict(self):
        """Test CompanyInfo creation from dictionary"""
        data = {
            'symbol': 'MSFT',
            'name': 'Microsoft Corporation',
            'sector': 'Technology'
        }

        company = CompanyInfo.from_dict(data)
        assert company.symbol == 'MSFT'
        assert company.name == 'Microsoft Corporation'
        assert company.sector == 'Technology'


class TestAdvancedSearchFilterVarInputDataFetch:
    """Test AdvancedSearchFilter VarInputData integration"""

    def test_fetch_company_info_uses_varinputdata(self):
        """Test that fetch_company_info correctly uses VarInputData"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            # Mock VarInputData instance
            mock_instance = Mock()

            # Setup mock returns for all 11 fields
            mock_instance.get_variable.side_effect = lambda symbol, field, period='latest': {
                'company_name': 'Apple Inc.',
                'company_short_name': 'Apple',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'market_cap': 2500000000000,
                'country': 'United States',
                'exchange': 'NASDAQ',
                'currency': 'USD',
                'employees': 164000,
                'website': 'https://www.apple.com',
                'description': 'Technology company that designs and manufactures consumer electronics'
            }.get(field)

            mock_var_data.return_value = mock_instance

            company_info = search_filter.fetch_company_info('AAPL')

            # Verify VarInputData was called
            mock_var_data.assert_called_once()

            # Verify get_variable was called for each field
            assert mock_instance.get_variable.call_count == 11

            # Verify CompanyInfo was created correctly
            assert company_info is not None
            assert company_info.symbol == 'AAPL'
            assert company_info.name == 'Apple Inc.'
            assert company_info.sector == 'Technology'
            assert company_info.market_cap == 2500000000000

    def test_fetch_company_info_with_missing_fields(self):
        """Test graceful handling when VarInputData returns None for some fields"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_instance = Mock()

            # Some fields return None
            mock_instance.get_variable.side_effect = lambda symbol, field, period='latest': {
                'company_name': 'Apple Inc.',
                'sector': None,  # Missing
                'market_cap': None,  # Missing
            }.get(field)

            mock_var_data.return_value = mock_instance

            company_info = search_filter.fetch_company_info('AAPL')

            assert company_info is not None
            assert company_info.name == 'Apple Inc.'
            assert company_info.sector == 'Unknown'  # Fallback value
            assert company_info.market_cap == 0  # Fallback value

    def test_fetch_company_info_with_cache(self):
        """Test that cached company info is used when available"""
        search_filter = AdvancedSearchFilter()

        # Add company to cache
        cached_company = CompanyInfo(
            symbol='AAPL',
            name='Apple Inc. (Cached)'
        )
        search_filter.company_cache.add_company('AAPL', cached_company)

        # Don't force refresh - should use cache
        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            company_info = search_filter.fetch_company_info('AAPL', force_refresh=False)

            # VarInputData should NOT be called (using cache)
            mock_var_data.assert_not_called()

            # Should get cached company
            assert company_info.name == 'Apple Inc. (Cached)'

    def test_fetch_company_info_force_refresh_bypasses_cache(self):
        """Test that force_refresh=True bypasses cache and fetches from VarInputData"""
        search_filter = AdvancedSearchFilter()

        # Add company to cache
        cached_company = CompanyInfo(
            symbol='AAPL',
            name='Apple Inc. (Cached)'
        )
        search_filter.company_cache.add_company('AAPL', cached_company)

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.side_effect = lambda symbol, field, period='latest': {
                'company_name': 'Apple Inc. (Fresh)',
            }.get(field)
            mock_var_data.return_value = mock_instance

            company_info = search_filter.fetch_company_info('AAPL', force_refresh=True)

            # VarInputData SHOULD be called (forced refresh)
            mock_var_data.assert_called_once()

            # Should get fresh data, not cached
            assert company_info.name == 'Apple Inc. (Fresh)'

    def test_fetch_company_info_error_handling(self):
        """Test graceful error handling when VarInputData fails"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_var_data.side_effect = Exception("VarInputData unavailable")

            company_info = search_filter.fetch_company_info('INVALID')

            # Should return None on error
            assert company_info is None

    def test_fetch_company_info_symbol_normalization(self):
        """Test that symbols are normalized to uppercase"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.return_value = 'Apple Inc.'
            mock_var_data.return_value = mock_instance

            # Pass lowercase symbol
            company_info = search_filter.fetch_company_info('aapl')

            # Should be normalized to uppercase
            assert company_info.symbol == 'AAPL'

    def test_fetch_company_info_description_truncation(self):
        """Test that long descriptions are truncated"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_instance = Mock()

            # Return very long description
            long_description = "A" * 1000
            mock_instance.get_variable.side_effect = lambda symbol, field, period='latest': {
                'company_name': 'Test Company',
                'description': long_description
            }.get(field)
            mock_var_data.return_value = mock_instance

            company_info = search_filter.fetch_company_info('TEST')

            # Description should be truncated to 500 chars + "..."
            assert len(company_info.description) == 503  # 500 + "..."
            assert company_info.description.endswith('...')


class TestBatchFetchVarInputData:
    """Test batch fetching with VarInputData"""

    def test_batch_fetch_companies(self):
        """Test parallel batch fetching of multiple companies"""
        search_filter = AdvancedSearchFilter()

        with patch('ui.streamlit.advanced_search_filter.get_var_input_data') as mock_var_data:
            mock_instance = Mock()
            mock_instance.get_variable.side_effect = lambda symbol, field, period='latest': {
                'company_name': f'{symbol} Company'
            }.get(field)
            mock_var_data.return_value = mock_instance

            # Batch fetch 3 companies
            results = search_filter.batch_fetch_companies(['AAPL', 'MSFT', 'GOOGL'])

            # Should have 3 results
            assert len(results) == 3
            assert 'AAPL' in results
            assert 'MSFT' in results
            assert 'GOOGL' in results

    def test_batch_fetch_handles_errors(self):
        """Test that batch fetch continues even if some symbols fail"""
        search_filter = AdvancedSearchFilter()

        call_count = [0]
        def mock_fetch(symbol):
            call_count[0] += 1
            if symbol == 'INVALID':
                raise Exception("Failed to fetch")
            return CompanyInfo(symbol=symbol, name=f"{symbol} Company")

        with patch.object(search_filter, 'fetch_company_info', side_effect=mock_fetch):
            results = search_filter.batch_fetch_companies(['AAPL', 'INVALID', 'MSFT'])

            # Should have 2 successful results (INVALID failed)
            assert len(results) == 2
            assert 'AAPL' in results
            assert 'MSFT' in results
            assert 'INVALID' not in results


class TestCompanyDataCache:
    """Test company data caching functionality"""

    def test_add_and_get_company(self, tmp_path):
        """Test adding and retrieving company from cache"""
        cache = CompanyDataCache(cache_dir=str(tmp_path))

        company = CompanyInfo(symbol='AAPL', name='Apple Inc.')
        cache.add_company('AAPL', company)

        retrieved = cache.get_company('AAPL')
        assert retrieved is not None
        assert retrieved.symbol == 'AAPL'
        assert retrieved.name == 'Apple Inc.'

    def test_cache_save_and_load(self, tmp_path):
        """Test cache persistence"""
        cache_dir = str(tmp_path)

        # Create cache and add company
        cache1 = CompanyDataCache(cache_dir=cache_dir)
        company = CompanyInfo(symbol='MSFT', name='Microsoft')
        cache1.add_company('MSFT', company)
        cache1.save_cache()

        # Create new cache instance (should load from disk)
        cache2 = CompanyDataCache(cache_dir=cache_dir)
        retrieved = cache2.get_company('MSFT')

        assert retrieved is not None
        assert retrieved.name == 'Microsoft'

    def test_cache_is_stale(self, tmp_path):
        """Test cache staleness detection"""
        cache = CompanyDataCache(cache_dir=str(tmp_path))

        # New cache should be stale
        assert cache.is_cache_stale(hours=24) is True

        # Set recent update time
        cache.last_updated = datetime.now()
        assert cache.is_cache_stale(hours=24) is False

        # Set old update time
        cache.last_updated = datetime.now() - timedelta(hours=25)
        assert cache.is_cache_stale(hours=24) is True


class TestFilterCriteria:
    """Test filter criteria functionality"""

    def test_filter_criteria_initialization(self):
        """Test FilterCriteria initialization with defaults"""
        criteria = FilterCriteria()

        assert criteria.sectors == []
        assert criteria.countries == []
        assert criteria.exchanges == []
        assert criteria.search_text == ""

    def test_filter_criteria_with_values(self):
        """Test FilterCriteria with custom values"""
        criteria = FilterCriteria(
            sectors=['Technology', 'Finance'],
            market_cap_min=1000000000,
            market_cap_max=10000000000,
            search_text="apple"
        )

        assert len(criteria.sectors) == 2
        assert criteria.market_cap_min == 1000000000
        assert criteria.search_text == "apple"


class TestCompanyFiltering:
    """Test company filtering with VarInputData-fetched data"""

    def test_filter_companies_by_sector(self):
        """Test filtering companies by sector"""
        search_filter = AdvancedSearchFilter()

        # Add test companies
        search_filter.company_cache.add_company('AAPL', CompanyInfo(
            symbol='AAPL', name='Apple', sector='Technology'
        ))
        search_filter.company_cache.add_company('JPM', CompanyInfo(
            symbol='JPM', name='JPMorgan', sector='Finance'
        ))

        criteria = FilterCriteria(sectors=['Technology'])
        results = search_filter.filter_companies(criteria)

        assert len(results) == 1
        assert results[0].symbol == 'AAPL'

    def test_filter_companies_by_market_cap_range(self):
        """Test filtering by market cap range"""
        search_filter = AdvancedSearchFilter()

        search_filter.company_cache.add_company('LARGE', CompanyInfo(
            symbol='LARGE', name='Large Cap', market_cap=500000000000
        ))
        search_filter.company_cache.add_company('SMALL', CompanyInfo(
            symbol='SMALL', name='Small Cap', market_cap=1000000000
        ))

        criteria = FilterCriteria(
            market_cap_min=100000000000,
            market_cap_max=1000000000000
        )
        results = search_filter.filter_companies(criteria)

        assert len(results) == 1
        assert results[0].symbol == 'LARGE'

    def test_filter_companies_by_search_text(self):
        """Test text-based search filtering"""
        search_filter = AdvancedSearchFilter()

        search_filter.company_cache.add_company('AAPL', CompanyInfo(
            symbol='AAPL', name='Apple Inc.', sector='Technology'
        ))
        search_filter.company_cache.add_company('MSFT', CompanyInfo(
            symbol='MSFT', name='Microsoft', sector='Technology'
        ))

        criteria = FilterCriteria(search_text="apple")
        results = search_filter.filter_companies(criteria)

        assert len(results) == 1
        assert results[0].symbol == 'AAPL'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
