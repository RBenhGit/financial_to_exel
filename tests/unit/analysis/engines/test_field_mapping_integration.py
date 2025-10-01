"""
Unit Tests for Field Mapping Integration in FinancialCalculationEngine
=======================================================================

Tests the new calculate_ratios_from_statements() method and field mapping
integration added in Task 179.
"""

import pytest
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class TestFieldMappingIntegration:
    """Test suite for field mapping integration with FinancialCalculationEngine"""

    @pytest.fixture
    def engine(self):
        """Create FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    @pytest.fixture
    def complete_financial_statements(self):
        """Complete financial statement data with all required fields"""
        return {
            # Income Statement
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'gross_profit': 40000,
            'operating_income': 25000,
            'net_income': 15000,
            'interest_expense': 2000,

            # Balance Sheet
            'total_assets': 500000,
            'current_assets': 150000,
            'cash_and_equivalents': 50000,
            'inventory': 30000,
            'total_liabilities': 200000,
            'current_liabilities': 80000,
            'shareholders_equity': 300000
        }

    @pytest.fixture
    def partial_financial_statements(self):
        """Partial financial statement data with missing fields"""
        return {
            'revenue': 100000,
            'net_income': 15000,
            'total_assets': 500000,
            'current_assets': 150000,
            'current_liabilities': 80000
        }

    def test_calculate_ratios_with_complete_data(self, engine, complete_financial_statements):
        """Test ratio calculation with complete financial statement data"""
        result = engine.calculate_ratios_from_statements(complete_financial_statements)

        # Verify successful calculation
        assert result.is_valid is True
        assert isinstance(result.value, dict)

        # Verify ratio categories
        assert 'liquidity' in result.value
        assert 'profitability' in result.value
        assert 'leverage' in result.value

        # Verify some specific ratios
        assert 'current_ratio' in result.value['liquidity']
        assert 'gross_profit_margin' in result.value['profitability']
        assert 'debt_to_assets' in result.value['leverage']

        # Verify metadata
        assert result.metadata is not None
        assert 'success_rate' in result.metadata
        assert result.metadata['success_rate'] > 0.5  # At least 50% success

    def test_calculate_ratios_with_partial_data(self, engine, partial_financial_statements):
        """Test graceful handling of missing fields"""
        result = engine.calculate_ratios_from_statements(partial_financial_statements)

        # Should still be valid, but with fewer ratios calculated
        assert result.is_valid is True

        # Check metadata for missing fields
        assert 'fields_missing' in result.metadata
        assert len(result.metadata['fields_missing']) > 0

        # Some calculations should still succeed
        assert result.metadata['calculations_successful'] > 0

    def test_liquidity_ratios(self, engine, complete_financial_statements):
        """Test all liquidity ratio calculations"""
        result = engine.calculate_ratios_from_statements(complete_financial_statements)

        liquidity = result.value['liquidity']

        # Current Ratio = Current Assets / Current Liabilities
        assert 'current_ratio' in liquidity
        expected_current_ratio = 150000 / 80000
        assert abs(liquidity['current_ratio'] - expected_current_ratio) < 0.01

        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        assert 'quick_ratio' in liquidity
        expected_quick_ratio = (150000 - 30000) / 80000
        assert abs(liquidity['quick_ratio'] - expected_quick_ratio) < 0.01

        # Cash Ratio = Cash / Current Liabilities
        assert 'cash_ratio' in liquidity
        expected_cash_ratio = 50000 / 80000
        assert abs(liquidity['cash_ratio'] - expected_cash_ratio) < 0.01

    def test_profitability_ratios(self, engine, complete_financial_statements):
        """Test all profitability ratio calculations"""
        result = engine.calculate_ratios_from_statements(complete_financial_statements)

        profitability = result.value['profitability']

        # Gross Profit Margin = Gross Profit / Revenue
        assert 'gross_profit_margin' in profitability
        expected_gpm = 40000 / 100000  # gross_profit / revenue
        assert abs(profitability['gross_profit_margin'] - expected_gpm) < 0.01

        # Operating Profit Margin = Operating Income / Revenue
        assert 'operating_profit_margin' in profitability
        expected_opm = 25000 / 100000
        assert abs(profitability['operating_profit_margin'] - expected_opm) < 0.01

        # Net Profit Margin = Net Income / Revenue
        assert 'net_profit_margin' in profitability
        expected_npm = 15000 / 100000
        assert abs(profitability['net_profit_margin'] - expected_npm) < 0.01

        # ROA = Net Income / Total Assets
        assert 'return_on_assets' in profitability
        expected_roa = 15000 / 500000
        assert abs(profitability['return_on_assets'] - expected_roa) < 0.01

        # ROE = Net Income / Shareholders Equity
        assert 'return_on_equity' in profitability
        expected_roe = 15000 / 300000
        assert abs(profitability['return_on_equity'] - expected_roe) < 0.01

    def test_leverage_ratios(self, engine, complete_financial_statements):
        """Test all leverage ratio calculations"""
        result = engine.calculate_ratios_from_statements(complete_financial_statements)

        leverage = result.value['leverage']

        # Debt to Assets = Total Liabilities / Total Assets
        assert 'debt_to_assets' in leverage
        expected_d2a = 200000 / 500000
        assert abs(leverage['debt_to_assets'] - expected_d2a) < 0.01

        # Debt to Equity = Total Liabilities / Shareholders Equity
        assert 'debt_to_equity' in leverage
        expected_d2e = 200000 / 300000
        assert abs(leverage['debt_to_equity'] - expected_d2e) < 0.01

        # Interest Coverage = Operating Income / Interest Expense
        assert 'interest_coverage' in leverage
        expected_ic = 25000 / 2000
        assert abs(leverage['interest_coverage'] - expected_ic) < 0.01

    def test_custom_field_mappings(self, engine):
        """Test custom field name mappings"""
        # Data with custom field names
        custom_statements = {
            'total_revenue': 100000,  # Custom name for 'revenue'
            'earnings': 15000,         # Custom name for 'net_income'
            'total_assets': 500000,
            'shareholders_equity': 300000
        }

        # Define field mappings
        field_mappings = {
            'revenue': 'total_revenue',
            'net_income': 'earnings'
        }

        result = engine.calculate_ratios_from_statements(
            custom_statements,
            field_mappings=field_mappings
        )

        assert result.is_valid is True
        assert 'net_profit_margin' in result.value['profitability']
        assert 'return_on_assets' in result.value['profitability']
        assert 'return_on_equity' in result.value['profitability']

    def test_metadata_tracking_enabled(self, engine, complete_financial_statements):
        """Test that metadata tracking works when enabled"""
        result = engine.calculate_ratios_from_statements(
            complete_financial_statements,
            metadata_tracking=True
        )

        assert result.metadata is not None
        assert 'fields_used' in result.metadata
        assert 'fields_missing' in result.metadata
        assert 'calculations_attempted' in result.metadata
        assert 'calculations_successful' in result.metadata
        assert 'success_rate' in result.metadata

    def test_metadata_tracking_disabled(self, engine, complete_financial_statements):
        """Test that metadata tracking can be disabled"""
        result = engine.calculate_ratios_from_statements(
            complete_financial_statements,
            metadata_tracking=False
        )

        assert result.is_valid is True
        assert result.metadata is None

    def test_missing_required_fields(self, engine):
        """Test handling of completely missing required fields"""
        incomplete_statements = {
            'revenue': 100000
            # Missing all other fields
        }

        result = engine.calculate_ratios_from_statements(incomplete_statements)

        # Should still be valid but with low success rate
        assert result.is_valid is True
        assert result.metadata['success_rate'] == 0.0
        assert len(result.metadata['fields_missing']) > 0

    def test_none_values_handling(self, engine):
        """Test handling of None values in fields"""
        statements_with_nones = {
            'revenue': 100000,
            'cost_of_revenue': None,  # None value
            'net_income': 15000,
            'total_assets': 500000,
            'current_assets': None,
            'current_liabilities': 80000
        }

        result = engine.calculate_ratios_from_statements(statements_with_nones)

        # Should handle None values gracefully
        assert result.is_valid is True
        # Some calculations should fail due to None values
        assert result.metadata['calculations_successful'] < result.metadata['calculations_attempted']

    def test_backward_compatibility(self, engine):
        """Test that existing calculation methods still work (backward compatibility)"""
        # Test that original methods are not affected
        current_ratio_result = engine.calculate_current_ratio(150000, 80000)
        assert current_ratio_result.is_valid is True
        assert abs(current_ratio_result.value - 1.875) < 0.01

        # Gross Profit Margin = Gross Profit / Revenue
        gross_margin_result = engine.calculate_gross_profit_margin(40000, 100000)
        assert gross_margin_result.is_valid is True
        assert abs(gross_margin_result.value - 0.40) < 0.01

    def test_empty_statements(self, engine):
        """Test handling of empty financial statements"""
        result = engine.calculate_ratios_from_statements({})

        assert result.is_valid is True
        assert result.metadata['success_rate'] == 0.0
        assert result.metadata['calculations_successful'] == 0

    def test_integration_with_field_mapper(self, engine):
        """Test integration scenario with StatementFieldMapper output format"""
        # Simulating output from StatementFieldMapper.standardize_financial_data()
        standardized_data = {
            'revenue': 100000,
            'cost_of_revenue': 60000,
            'operating_income': 25000,
            'net_income': 15000,
            'total_assets': 500000,
            'current_assets': 150000,
            'current_liabilities': 80000,
            'total_liabilities': 200000,
            'shareholders_equity': 300000,
            'cash_and_equivalents': 50000,
            'inventory': 30000,
            'interest_expense': 2000
        }

        result = engine.calculate_ratios_from_statements(standardized_data)

        # Should successfully calculate all available ratios
        assert result.is_valid is True
        assert result.metadata['success_rate'] > 0.8  # At least 80% success
        assert len(result.metadata['fields_used']) >= 10  # Most fields should be used

    def test_fields_used_tracking(self, engine, complete_financial_statements):
        """Test that fields_used is correctly tracked"""
        result = engine.calculate_ratios_from_statements(complete_financial_statements)

        fields_used = result.metadata['fields_used']

        # Verify commonly used fields are tracked
        assert 'revenue' in fields_used
        assert 'net_income' in fields_used
        assert 'total_assets' in fields_used
        assert 'current_assets' in fields_used
        assert 'current_liabilities' in fields_used

    def test_success_rate_calculation(self, engine, partial_financial_statements):
        """Test success rate calculation is accurate"""
        result = engine.calculate_ratios_from_statements(partial_financial_statements)

        calculations_attempted = result.metadata['calculations_attempted']
        calculations_successful = result.metadata['calculations_successful']
        success_rate = result.metadata['success_rate']

        # Verify success rate calculation
        if calculations_attempted > 0:
            expected_success_rate = calculations_successful / calculations_attempted
            assert abs(success_rate - expected_success_rate) < 0.001
        else:
            assert success_rate == 0.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
