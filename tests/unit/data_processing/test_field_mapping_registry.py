"""
Tests for Centralized Field Mapping Registry

Validates:
- Field mapping accuracy for each data source
- Case-insensitive lookups
- Fuzzy matching for Excel fields
- Reverse lookups (standard -> source)
- Conflict detection and validation
- Thread safety
"""

import pytest
import threading
from core.data_processing.field_mapping_registry import (
    FieldMappingRegistry,
    get_field_mapping_registry
)


class TestFieldMappingRegistryBasics:
    """Test basic field mapping registry functionality"""

    def test_singleton_pattern(self):
        """Verify singleton pattern works correctly"""
        registry1 = FieldMappingRegistry()
        registry2 = FieldMappingRegistry()
        registry3 = get_field_mapping_registry()

        assert registry1 is registry2
        assert registry2 is registry3

    def test_supported_sources(self):
        """Verify all expected data sources are supported"""
        registry = get_field_mapping_registry()

        expected_sources = ['yfinance', 'fmp', 'excel', 'alpha_vantage', 'polygon']

        for source in expected_sources:
            fields = registry.get_all_source_fields(source)
            assert len(fields) > 0, f"No mappings found for {source}"


class TestYFinanceMappings:
    """Test yfinance field mappings"""

    def test_yfinance_income_statement_mappings(self):
        """Test yfinance income statement field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'totalRevenue': 'revenue',
            'TotalRevenue': 'revenue',
            'Revenue': 'revenue',
            'operatingIncome': 'operating_income',
            'netIncome': 'net_income',
            'grossProfit': 'gross_profit',
            'ebitda': 'ebitda',
            'basicEPS': 'eps_basic',
            'dilutedEPS': 'eps_diluted',
        }

        for yf_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('yfinance', yf_field)
            assert result == expected_std, f"Expected {yf_field} -> {expected_std}, got {result}"

    def test_yfinance_balance_sheet_mappings(self):
        """Test yfinance balance sheet field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'totalAssets': 'total_assets',
            'totalLiabilities': 'total_liabilities',
            'cashAndCashEquivalents': 'cash_and_cash_equivalents',
            'accountsReceivable': 'accounts_receivable',
            'inventory': 'inventory',
            'longTermDebt': 'long_term_debt',
            'totalStockholderEquity': 'total_stockholders_equity',
        }

        for yf_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('yfinance', yf_field)
            assert result == expected_std, f"Expected {yf_field} -> {expected_std}, got {result}"

    def test_yfinance_cash_flow_mappings(self):
        """Test yfinance cash flow statement field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'operatingCashFlow': 'operating_cash_flow',
            'capitalExpenditures': 'capital_expenditures',
            'freeCashFlow': 'free_cash_flow',
            'dividendsPaid': 'dividends_paid',
        }

        for yf_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('yfinance', yf_field)
            assert result == expected_std, f"Expected {yf_field} -> {expected_std}, got {result}"

    def test_yfinance_market_data_mappings(self):
        """Test yfinance market data field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'marketCap': 'market_cap',
            'trailingPE': 'pe_ratio',
            'priceToBook': 'price_to_book',
            'beta': 'beta',
            'dividendYield': 'dividend_yield',
        }

        for yf_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('yfinance', yf_field)
            assert result == expected_std, f"Expected {yf_field} -> {expected_std}, got {result}"


class TestFMPMappings:
    """Test FMP (Financial Modeling Prep) field mappings"""

    def test_fmp_income_statement_mappings(self):
        """Test FMP income statement field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'revenue': 'revenue',
            'costOfRevenue': 'cost_of_revenue',
            'grossProfit': 'gross_profit',
            'operatingIncome': 'operating_income',
            'netIncome': 'net_income',
            'ebitda': 'ebitda',
            'eps': 'eps_basic',
            'epsdiluted': 'eps_diluted',
        }

        for fmp_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('fmp', fmp_field)
            assert result == expected_std, f"Expected {fmp_field} -> {expected_std}, got {result}"

    def test_fmp_balance_sheet_mappings(self):
        """Test FMP balance sheet field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'totalAssets': 'total_assets',
            'totalLiabilities': 'total_liabilities',
            'cashAndCashEquivalents': 'cash_and_cash_equivalents',
            'netReceivables': 'accounts_receivable',
            'inventory': 'inventory',
            'longTermDebt': 'long_term_debt',
            'totalStockholdersEquity': 'total_stockholders_equity',
        }

        for fmp_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('fmp', fmp_field)
            assert result == expected_std, f"Expected {fmp_field} -> {expected_std}, got {result}"

    def test_fmp_cash_flow_mappings(self):
        """Test FMP cash flow statement field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'netCashProvidedByOperatingActivities': 'operating_cash_flow',
            'capitalExpenditure': 'capital_expenditures',
            'freeCashFlow': 'free_cash_flow',
            'dividendsPaid': 'dividends_paid',
        }

        for fmp_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('fmp', fmp_field)
            assert result == expected_std, f"Expected {fmp_field} -> {expected_std}, got {result}"

    def test_fmp_ratio_mappings(self):
        """Test FMP financial ratio field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'peRatio': 'pe_ratio',
            'priceToBookRatio': 'price_to_book',
            'currentRatio': 'current_ratio',
            'quickRatio': 'quick_ratio',
            'debtToEquity': 'debt_to_equity',
            'returnOnEquity': 'return_on_equity',
            'returnOnAssets': 'return_on_assets',
        }

        for fmp_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('fmp', fmp_field)
            assert result == expected_std, f"Expected {fmp_field} -> {expected_std}, got {result}"


class TestExcelMappings:
    """Test Excel field mappings"""

    def test_excel_basic_mappings(self):
        """Test Excel basic field mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'Revenue': 'revenue',
            'Total Revenue': 'revenue',
            'Sales': 'revenue',
            'Net Income': 'net_income',
            'Operating Income': 'operating_income',
            'Total Assets': 'total_assets',
            'Cash': 'cash_and_cash_equivalents',
        }

        for excel_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('excel', excel_field)
            assert result == expected_std, f"Expected {excel_field} -> {expected_std}, got {result}"

    def test_excel_abbreviation_mappings(self):
        """Test Excel abbreviation mappings"""
        registry = get_field_mapping_registry()

        test_cases = {
            'COGS': 'cost_of_revenue',
            'R&D': 'research_and_development',
            'SG&A': 'selling_general_administrative',
            'EBIT': 'ebit',
            'EBITDA': 'ebitda',
            'EPS': 'eps_basic',
            'PP&E': 'property_plant_equipment_net',
            'A/R': 'accounts_receivable',
            'A/P': 'accounts_payable',
            'FCF': 'free_cash_flow',
            'CAPEX': 'capital_expenditures',
            'P/E': 'pe_ratio',
            'ROE': 'return_on_equity',
            'ROA': 'return_on_assets',
        }

        for excel_field, expected_std in test_cases.items():
            result = registry.get_standard_field_name('excel', excel_field)
            assert result == expected_std, f"Expected {excel_field} -> {expected_std}, got {result}"


class TestCaseInsensitiveLookup:
    """Test case-insensitive field lookups"""

    def test_case_insensitive_yfinance(self):
        """Test case-insensitive lookup for yfinance"""
        registry = get_field_mapping_registry()

        # Test various case variations
        test_cases = [
            ('totalrevenue', 'revenue'),
            ('TOTALREVENUE', 'revenue'),
            ('TotalRevenue', 'revenue'),
            ('totalRevenue', 'revenue'),
            ('netincome', 'net_income'),
            ('NETINCOME', 'net_income'),
        ]

        for field, expected in test_cases:
            result = registry.get_standard_field_name('yfinance', field, case_sensitive=False)
            assert result == expected, f"Case-insensitive: {field} -> {expected}, got {result}"

    def test_case_insensitive_excel(self):
        """Test case-insensitive lookup for Excel"""
        registry = get_field_mapping_registry()

        test_cases = [
            ('revenue', 'revenue'),
            ('REVENUE', 'revenue'),
            ('Revenue', 'revenue'),
            ('total assets', 'total_assets'),
            ('TOTAL ASSETS', 'total_assets'),
        ]

        for field, expected in test_cases:
            result = registry.get_standard_field_name('excel', field, case_sensitive=False)
            assert result == expected, f"Case-insensitive: {field} -> {expected}, got {result}"

    def test_case_sensitive_exact_match_required(self):
        """Test that case-sensitive mode requires exact match"""
        registry = get_field_mapping_registry()

        # Should not match with wrong case when case_sensitive=True
        result = registry.get_standard_field_name('yfinance', 'TOTALREVENUE', case_sensitive=True)
        assert result is None, "Should not match with different case in case-sensitive mode"

        # Should match with correct case
        result = registry.get_standard_field_name('yfinance', 'totalRevenue', case_sensitive=True)
        assert result == 'revenue'


class TestFuzzyMatching:
    """Test fuzzy matching for field names"""

    def test_fuzzy_match_excel_typos(self):
        """Test fuzzy matching handles typos in Excel fields"""
        registry = get_field_mapping_registry()

        test_cases = [
            ('Revenu', 'revenue'),  # Missing 'e'
            ('Reveue', 'revenue'),  # Typo
            ('Net Incom', 'net_income'),  # Missing 'e'
            ('Operating Incom', 'operating_income'),  # Missing 'e'
            ('Total Asset', 'total_assets'),  # Missing 's'
        ]

        for field, expected in test_cases:
            result = registry.get_standard_field_name(
                'excel', field,
                fuzzy_match=True,
                fuzzy_threshold=0.8
            )
            assert result == expected, f"Fuzzy match: {field} should match {expected}, got {result}"

    def test_fuzzy_match_threshold(self):
        """Test fuzzy matching respects threshold"""
        registry = get_field_mapping_registry()

        # Close match - should work with low threshold
        result = registry.get_standard_field_name(
            'excel', 'Revenu',
            fuzzy_match=True,
            fuzzy_threshold=0.7
        )
        assert result == 'revenue'

        # Distant match - should fail with high threshold
        result = registry.get_standard_field_name(
            'excel', 'xyz',
            fuzzy_match=True,
            fuzzy_threshold=0.9
        )
        assert result is None

    def test_fuzzy_match_variations(self):
        """Test fuzzy matching with common Excel variations"""
        registry = get_field_mapping_registry()

        test_cases = [
            ('Total Revenues', 'revenue'),
            ('Operating Profit', 'operating_income'),
            ('Cash and Equivalents', 'cash_and_cash_equivalents'),
            ('LongTerm Debt', 'long_term_debt'),
        ]

        for field, expected in test_cases:
            result = registry.get_standard_field_name(
                'excel', field,
                fuzzy_match=True,
                case_sensitive=False,
                fuzzy_threshold=0.75
            )
            assert result == expected, f"Fuzzy match: {field} should match {expected}, got {result}"


class TestReverseLookup:
    """Test reverse lookups (standard -> source)"""

    def test_reverse_lookup_yfinance(self):
        """Test reverse lookup for yfinance"""
        registry = get_field_mapping_registry()

        # Note: Multiple source fields can map to same standard field,
        # so we just verify we get a valid source field back
        test_cases = {
            'revenue': ['totalRevenue', 'TotalRevenue', 'Revenue'],
            'net_income': ['netIncome', 'NetIncome', 'NetIncomeCommonStockholders'],
            'total_assets': ['totalAssets', 'TotalAssets'],
            'operating_cash_flow': ['operatingCashFlow', 'totalCashFromOperatingActivities'],
        }

        for std_field, valid_sources in test_cases.items():
            result = registry.get_source_field_name('yfinance', std_field)
            assert result is not None, f"Should find a source field for {std_field}"
            # Verify the returned field maps back to the standard field
            reverse_check = registry.get_standard_field_name('yfinance', result)
            assert reverse_check == std_field, f"Reverse lookup should be consistent: {result} -> {reverse_check}"

    def test_reverse_lookup_fmp(self):
        """Test reverse lookup for FMP"""
        registry = get_field_mapping_registry()

        # Note: Multiple source fields can map to same standard field
        test_fields = ['revenue', 'total_assets', 'operating_cash_flow']

        for std_field in test_fields:
            result = registry.get_source_field_name('fmp', std_field)
            assert result is not None, f"Should find a source field for {std_field}"
            # Verify the returned field maps back to the standard field
            reverse_check = registry.get_standard_field_name('fmp', result)
            assert reverse_check == std_field, f"Reverse lookup should be consistent"

    def test_reverse_lookup_excel(self):
        """Test reverse lookup for Excel"""
        registry = get_field_mapping_registry()

        # Note: Excel can have multiple source names for same standard,
        # so we just check that we get a valid Excel field back
        test_fields = ['revenue', 'net_income', 'total_assets']

        for std_field in test_fields:
            result = registry.get_source_field_name('excel', std_field)
            assert result is not None, f"Should find Excel field for {std_field}"


class TestMappingValidation:
    """Test mapping validation and conflict detection"""

    def test_validate_mappings_no_conflicts(self):
        """Test that validation passes with no conflicts"""
        registry = get_field_mapping_registry()

        is_valid, issues = registry.validate_mappings()

        if not is_valid:
            for issue in issues:
                print(f"Validation issue: {issue}")

        assert is_valid, f"Mappings should be valid, found issues: {issues}"

    def test_mapping_statistics(self):
        """Test mapping statistics"""
        registry = get_field_mapping_registry()

        stats = registry.get_statistics()

        # Verify we have stats for all sources
        assert 'yfinance' in stats
        assert 'fmp' in stats
        assert 'excel' in stats

        # Verify each source has meaningful mappings
        for source, source_stats in stats.items():
            assert source_stats['total_mappings'] > 0, f"{source} should have mappings"
            assert source_stats['unique_standard_fields'] > 0, f"{source} should map to standard fields"


class TestGetAllFields:
    """Test getting all fields for a source"""

    def test_get_all_source_fields(self):
        """Test getting all source-specific fields"""
        registry = get_field_mapping_registry()

        yf_fields = registry.get_all_source_fields('yfinance')
        assert len(yf_fields) > 50, "yfinance should have many field mappings"
        assert 'totalRevenue' in yf_fields
        assert 'netIncome' in yf_fields

    def test_get_all_standard_fields(self):
        """Test getting all standard fields for a source"""
        registry = get_field_mapping_registry()

        yf_standard = registry.get_all_standard_fields('yfinance')
        assert len(yf_standard) > 0
        assert 'revenue' in yf_standard
        assert 'net_income' in yf_standard

    def test_unknown_source(self):
        """Test behavior with unknown source"""
        registry = get_field_mapping_registry()

        fields = registry.get_all_source_fields('unknown_source')
        assert fields == []

        result = registry.get_standard_field_name('unknown_source', 'somefield')
        assert result is None


class TestThreadSafety:
    """Test thread safety of the registry"""

    def test_concurrent_lookups(self):
        """Test concurrent field lookups are thread-safe"""
        registry = get_field_mapping_registry()
        results = []
        errors = []

        def lookup_fields():
            try:
                for _ in range(100):
                    result = registry.get_standard_field_name('yfinance', 'totalRevenue')
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = [threading.Thread(target=lookup_fields) for _ in range(10)]

        # Start all threads
        for t in threads:
            t.start()

        # Wait for all to complete
        for t in threads:
            t.join()

        # Verify no errors
        assert len(errors) == 0, f"Errors occurred: {errors}"

        # Verify all results are correct
        assert all(r == 'revenue' for r in results), "All lookups should return 'revenue'"
        assert len(results) == 1000, "Should have 1000 results (10 threads * 100 lookups)"


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_field_name(self):
        """Test handling of empty field names"""
        registry = get_field_mapping_registry()

        result = registry.get_standard_field_name('yfinance', '')
        assert result is None

    def test_none_field_name(self):
        """Test handling of None field names"""
        registry = get_field_mapping_registry()

        # Should handle None gracefully
        try:
            result = registry.get_standard_field_name('yfinance', None)
            # Might return None or raise exception - both acceptable
        except (TypeError, AttributeError):
            pass  # Expected behavior

    def test_whitespace_handling(self):
        """Test handling of fields with whitespace"""
        registry = get_field_mapping_registry()

        # Excel fields commonly have spaces
        result = registry.get_standard_field_name('excel', 'Total Revenue')
        assert result == 'revenue'

        # Test with extra whitespace
        result = registry.get_standard_field_name(
            'excel', '  Total Revenue  ',
            fuzzy_match=True
        )
        assert result == 'revenue'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
