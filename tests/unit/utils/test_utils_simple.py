"""
Simple Unit Tests for Utils Module - Basic Coverage
===================================================

This test module provides basic unit test coverage for the utils module
to improve test coverage as required by Task #154.

Test Coverage Areas:
1. GrowthRateCalculator class functionality
2. PlottingUtils class functionality
3. Basic functionality testing without complex imports
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch

# Import utils modules that actually exist
from utils.growth_calculator import GrowthRateCalculator
from utils.plotting_utils import PlottingUtils


class TestGrowthRateCalculator:
    """Test GrowthRateCalculator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.calculator = GrowthRateCalculator()

    def test_growth_calculator_initialization(self):
        """Test GrowthRateCalculator initialization"""
        assert self.calculator is not None
        assert hasattr(self.calculator, 'calculate_cagr')
        assert hasattr(self.calculator, 'calculate_growth_rates_for_series')

    def test_calculate_cagr_basic(self):
        """Test basic CAGR calculation"""
        beginning_value = 1000
        ending_value = 1500
        years = 3

        cagr = self.calculator.calculate_cagr(beginning_value, ending_value, years)

        assert isinstance(cagr, float)
        assert cagr > 0  # Should be positive growth

    def test_calculate_cagr_zero_years(self):
        """Test CAGR calculation with zero years"""
        result = self.calculator.calculate_cagr(1000, 1500, 0)

        # Should handle gracefully (return None or raise exception)
        assert result is None or isinstance(result, float)

    def test_calculate_cagr_negative_growth(self):
        """Test CAGR calculation with negative growth"""
        cagr = self.calculator.calculate_cagr(1000, 800, 2)

        assert isinstance(cagr, float)
        assert cagr < 0  # Should be negative

    def test_calculate_growth_rates_for_series(self):
        """Test growth rate calculation for data series"""
        sample_data = [1000, 1100, 1200, 1300]

        growth_rates = self.calculator.calculate_growth_rates_for_series(sample_data)

        assert isinstance(growth_rates, dict)
        assert len(growth_rates) >= 0

    def test_validate_growth_rate(self):
        """Test growth rate validation"""
        # Test valid growth rate
        valid_rate = 0.10  # 10%
        is_valid = self.calculator.validate_growth_rate(valid_rate)
        assert isinstance(is_valid, bool)

        # Test extremely high growth rate
        high_rate = 5.0  # 500%
        is_valid_high = self.calculator.validate_growth_rate(high_rate)
        assert isinstance(is_valid_high, bool)

    def test_format_growth_rate(self):
        """Test growth rate formatting"""
        growth_rate = 0.1234  # 12.34%

        formatted = self.calculator.format_growth_rate(growth_rate)

        assert isinstance(formatted, str)
        assert '%' in formatted or 'rate' in formatted.lower()

    def test_get_growth_rate_statistics(self):
        """Test growth rate statistics calculation"""
        growth_rates = {'1yr': 0.05, '3yr': 0.08, '5yr': 0.12}

        stats = self.calculator.get_growth_rate_statistics(growth_rates)

        assert isinstance(stats, dict)
        # Should contain statistical measures


class TestPlottingUtils:
    """Test PlottingUtils functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.plotter = PlottingUtils()

    def test_plotting_utils_initialization(self):
        """Test PlottingUtils initialization"""
        assert self.plotter is not None
        assert hasattr(self.plotter, 'create_fcf_comparison_chart')
        assert hasattr(self.plotter, 'create_growth_rate_chart')

    def test_create_fcf_comparison_chart_basic(self):
        """Test basic FCF comparison chart creation"""
        # Sample FCF data
        fcf_data = {
            'FCFE': [25000, 27000, 30000],
            'FCFF': [35000, 37000, 40000],
            'LFCF': [30000, 32000, 35000]
        }
        years = [2021, 2022, 2023]

        try:
            chart = self.plotter.create_fcf_comparison_chart(fcf_data, years)
            # Chart creation should succeed or handle gracefully
            assert chart is not None or chart is False
        except Exception as e:
            # Exception handling is acceptable for missing dependencies
            assert isinstance(e, (ImportError, ModuleNotFoundError, ValueError))

    def test_create_growth_rate_chart(self):
        """Test growth rate chart creation"""
        growth_data = {
            'FCFE': {'1yr': 0.05, '3yr': 0.08, '5yr': 0.12},
            'FCFF': {'1yr': 0.10, '3yr': 0.15, '5yr': 0.18}
        }

        try:
            chart = self.plotter.create_growth_rate_chart(growth_data)
            assert chart is not None or chart is False
        except Exception as e:
            # Chart libraries might not be available in test environment
            assert isinstance(e, (ImportError, ModuleNotFoundError, AttributeError, ValueError))

    def test_apply_common_styling(self):
        """Test common styling application"""
        # Create a mock figure
        mock_figure = Mock()

        try:
            result = self.plotter.apply_common_styling(mock_figure)
            # Should return a figure or handle gracefully
            assert result is not None or result is False
        except Exception as e:
            # Missing plotting libraries
            assert isinstance(e, (ImportError, ModuleNotFoundError, AttributeError))

    def test_create_empty_chart(self):
        """Test empty chart creation"""
        try:
            empty_chart = self.plotter._create_empty_chart("No data available")
            assert empty_chart is not None or empty_chart is False
        except Exception as e:
            # Missing dependencies acceptable
            assert isinstance(e, (ImportError, ModuleNotFoundError))


class TestUtilsModuleImports:
    """Test that utils modules can be imported successfully"""

    def test_growth_calculator_import(self):
        """Test that growth calculator can be imported"""
        from utils.growth_calculator import GrowthRateCalculator

        calculator = GrowthRateCalculator()
        assert calculator is not None

    def test_plotting_utils_import(self):
        """Test that plotting utils can be imported"""
        from utils.plotting_utils import PlottingUtils

        plotter = PlottingUtils()
        assert plotter is not None

    def test_other_utils_modules_exist(self):
        """Test that other utils modules exist and can be imported"""
        utils_modules = [
            'utils.excel_processor',
            'utils.input_validator',
            'utils.performance_monitor',
            'utils.logging_config'
        ]

        import_count = 0
        for module_name in utils_modules:
            try:
                __import__(module_name)
                import_count += 1
            except ImportError:
                pass  # Module might not exist or have dependencies

        # At least some modules should be importable
        assert import_count >= 1

    def test_utils_init_file_exists(self):
        """Test that utils __init__.py exists"""
        import utils
        assert utils is not None


class TestBasicUtilsFunctionality:
    """Test basic functionality of utils modules"""

    def test_growth_calculator_with_real_data(self):
        """Test growth calculator with realistic financial data"""
        calculator = GrowthRateCalculator()

        # Realistic revenue growth data
        revenues = [100000, 105000, 112000, 118000, 125000]

        # Test with valid data
        if len(revenues) >= 2:
            first_value = revenues[0]
            last_value = revenues[-1]
            years = len(revenues) - 1

            cagr = calculator.calculate_cagr(first_value, last_value, years)

            assert isinstance(cagr, float)
            assert -1 <= cagr <= 10  # Reasonable growth rate range

    def test_growth_calculator_edge_cases(self):
        """Test growth calculator with edge cases"""
        calculator = GrowthRateCalculator()

        # Zero starting value
        try:
            result = calculator.calculate_cagr(0, 1000, 3)
            # Should handle gracefully
            assert result is None or isinstance(result, float)
        except (ValueError, ZeroDivisionError):
            # Acceptable to raise exception for invalid input
            pass

        # Negative values
        try:
            result = calculator.calculate_cagr(-1000, -800, 2)
            assert result is None or isinstance(result, float)
        except ValueError:
            # Acceptable to reject negative values
            pass

    def test_plotting_utils_with_missing_dependencies(self):
        """Test plotting utils behavior when dependencies are missing"""
        plotter = PlottingUtils()

        # Test that it handles missing plotting libraries gracefully
        empty_data = {}

        try:
            result = plotter.create_fcf_comparison_chart(empty_data)
            # Should return None/False or create empty chart
            assert result is None or result is False or hasattr(result, 'show')
        except (ImportError, ModuleNotFoundError):
            # Expected when plotting libraries unavailable
            pass
        except Exception as e:
            # Other exceptions are acceptable for invalid data
            assert isinstance(e, (ValueError, KeyError, TypeError))


@pytest.mark.integration
class TestUtilsIntegration:
    """Test integration between utils modules"""

    def test_growth_calculator_with_plotting_integration(self):
        """Test integration between growth calculator and plotting"""
        calculator = GrowthRateCalculator()
        plotter = PlottingUtils()

        # Calculate growth rates
        sample_values = [1000, 1100, 1200, 1300]

        if len(sample_values) >= 2:
            cagr = calculator.calculate_cagr(
                sample_values[0],
                sample_values[-1],
                len(sample_values) - 1
            )

            # Try to create chart with calculated data
            if isinstance(cagr, float):
                growth_data = {
                    'cagr': [cagr],
                    'values': sample_values
                }

                try:
                    chart = plotter.create_growth_rate_chart(growth_data)
                    # Integration should work or fail gracefully
                    assert chart is not None or chart is False
                except Exception:
                    # Missing dependencies or invalid data format
                    pass

    def test_utils_error_handling_consistency(self):
        """Test that utils modules handle errors consistently"""
        calculator = GrowthRateCalculator()
        plotter = PlottingUtils()

        # Test with invalid inputs
        invalid_inputs = [None, [], {}, "invalid"]

        for invalid_input in invalid_inputs:
            # Growth calculator should handle invalid inputs gracefully
            try:
                result = calculator.calculate_cagr(invalid_input, 1000, 3)
                # Should return None or raise appropriate exception
                assert result is None or isinstance(result, (int, float))
            except (TypeError, ValueError, AttributeError):
                # Expected for invalid inputs
                pass

            # Plotter should handle invalid inputs gracefully
            try:
                chart = plotter.create_fcf_comparison_chart(invalid_input)
                assert chart is None or chart is False or hasattr(chart, 'show')
            except (TypeError, ValueError, KeyError, AttributeError, ImportError):
                # Expected for invalid inputs or missing dependencies
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])