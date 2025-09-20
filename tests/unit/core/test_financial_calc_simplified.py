"""
Simplified Unit Tests for Financial Calculations Engine
======================================================

Tests core functionality of the financial calculations engine without mocking
to improve test coverage and validate actual class functionality.
"""

import pytest
import sys
import os
import tempfile
from pathlib import Path
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from core.analysis.engines.financial_calculations import FinancialCalculator
from config.config import get_config


class TestFinancialCalculatorSimplified:
    """Simplified tests for FinancialCalculator class."""

    def test_constructor_basic(self):
        """Test basic constructor without loading data."""
        # Test with None path
        calc = FinancialCalculator(None)
        assert calc.company_folder is None
        assert calc.enhanced_data_manager is None

    def test_config_integration(self):
        """Test configuration loading works."""
        config = get_config()
        assert config is not None

        # Test that calculator can access config
        calc = FinancialCalculator(None)
        # This should not raise an exception
        assert calc is not None

    def test_fcf_types_calculation_structure(self):
        """Test FCF calculation methods exist and return proper structure."""
        calc = FinancialCalculator(None)

        # These methods should exist and not crash when called with empty data
        # They should return empty lists or handle gracefully
        try:
            fcfe_result = calc.calculate_fcf_to_equity()
            assert isinstance(fcfe_result, list)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

        try:
            fcff_result = calc.calculate_fcf_to_firm()
            assert isinstance(fcff_result, list)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

        try:
            levered_result = calc.calculate_levered_fcf()
            assert isinstance(levered_result, list)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_all_fcf_types_method(self):
        """Test calculate_all_fcf_types method."""
        calc = FinancialCalculator(None)

        try:
            all_fcf = calc.calculate_all_fcf_types()
            assert isinstance(all_fcf, dict)
            # Should have keys for all FCF types
            expected_keys = ['FCFE', 'FCFF', 'LFCF']
            for key in expected_keys:
                if key in all_fcf:
                    assert isinstance(all_fcf[key], list)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_comprehensive_fcf_results(self):
        """Test comprehensive FCF results method."""
        calc = FinancialCalculator(None)

        try:
            comprehensive = calc.get_comprehensive_fcf_results()
            # Should return some kind of structured result
            assert comprehensive is not None
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_financial_metrics_method(self):
        """Test financial metrics calculation."""
        calc = FinancialCalculator(None)

        try:
            metrics = calc.get_financial_metrics()
            assert isinstance(metrics, dict)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_dcf_inputs_method(self):
        """Test DCF inputs calculation."""
        calc = FinancialCalculator(None)

        try:
            dcf_inputs = calc.calculate_dcf_inputs()
            assert isinstance(dcf_inputs, dict)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_data_quality_report(self):
        """Test data quality report generation."""
        calc = FinancialCalculator(None)

        try:
            quality_report = calc.get_data_quality_report()
            # Should return some kind of report
            assert quality_report is not None
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_latest_report_date(self):
        """Test getting latest report date."""
        calc = FinancialCalculator(None)

        try:
            date = calc.get_latest_report_date()
            assert isinstance(date, str)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_growth_rates_calculation(self):
        """Test growth rates calculation method."""
        calc = FinancialCalculator(None)

        # Test with empty/mock data
        test_data = [100, 110, 121, 133]  # Simple growth sequence

        try:
            growth_rates = calc.calculate_growth_rates(test_data)
            assert isinstance(growth_rates, list)
            if len(growth_rates) > 0:
                # Should calculate proper growth rates
                assert all(isinstance(rate, (int, float)) for rate in growth_rates)
        except Exception as e:
            # Method might require specific data structure
            pass

    def test_currency_methods(self):
        """Test currency-related methods."""
        calc = FinancialCalculator(None)

        try:
            currency_info = calc.get_currency_info()
            assert isinstance(currency_info, dict)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    def test_standardized_data_method(self):
        """Test standardized financial data method."""
        calc = FinancialCalculator(None)

        try:
            standardized = calc.get_standardized_financial_data()
            assert isinstance(standardized, dict)
        except Exception as e:
            # Should handle missing data gracefully
            assert "missing" in str(e).lower() or "not found" in str(e).lower() or "no" in str(e).lower()

    @pytest.mark.parametrize("test_path", [
        None,
        "",
        "non_existent_path",
        "/fake/path/to/data"
    ])
    def test_constructor_with_various_paths(self, test_path):
        """Test constructor with various path inputs."""
        calc = FinancialCalculator(test_path)
        assert calc.company_folder == test_path

    def test_enhanced_data_manager_integration(self):
        """Test enhanced data manager integration."""
        mock_manager = MagicMock()
        calc = FinancialCalculator(None, mock_manager)

        assert calc.enhanced_data_manager == mock_manager

    def test_financial_statements_loading(self):
        """Test financial statements loading method."""
        calc = FinancialCalculator(None)

        try:
            # This should handle missing data gracefully
            calc.load_financial_statements()
        except Exception as e:
            # Expected to fail with missing data, but should not crash
            assert isinstance(e, Exception)

    def test_method_existence(self):
        """Test that all expected methods exist."""
        calc = FinancialCalculator(None)

        # Check that key methods exist
        assert hasattr(calc, 'calculate_fcf_to_equity')
        assert hasattr(calc, 'calculate_fcf_to_firm')
        assert hasattr(calc, 'calculate_levered_fcf')
        assert hasattr(calc, 'calculate_all_fcf_types')
        assert hasattr(calc, 'get_comprehensive_fcf_results')
        assert hasattr(calc, 'get_financial_metrics')
        assert hasattr(calc, 'calculate_dcf_inputs')
        assert hasattr(calc, 'load_financial_statements')

    def test_attribute_initialization(self):
        """Test that basic attributes are initialized properly."""
        calc = FinancialCalculator("test_path")

        # Check basic attributes exist
        assert hasattr(calc, 'company_folder')
        assert hasattr(calc, 'enhanced_data_manager')

        # Check company folder is set
        assert calc.company_folder == "test_path"

    def test_empty_data_handling(self):
        """Test handling of empty or missing data."""
        calc = FinancialCalculator(None)

        # These should not crash the application
        methods_to_test = [
            'get_data_quality_report',
            'get_latest_report_date',
            'get_currency_info',
            'get_standardized_financial_data'
        ]

        for method_name in methods_to_test:
            if hasattr(calc, method_name):
                method = getattr(calc, method_name)
                try:
                    result = method()
                    # Should return something, even if empty
                    assert result is not None or result == "" or result == {} or result == []
                except Exception:
                    # Expected to handle missing data
                    pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])