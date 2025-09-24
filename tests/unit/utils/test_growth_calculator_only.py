"""
Unit Tests for Growth Calculator Only - Minimal Dependencies
============================================================

This test module provides unit test coverage for the growth calculator
without importing modules that have complex dependencies.
"""

import pytest
import pandas as pd
from utils.growth_calculator import GrowthRateCalculator


class TestGrowthRateCalculator:
    """Test GrowthRateCalculator functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.calculator = GrowthRateCalculator()

    def test_growth_calculator_initialization(self):
        """Test GrowthRateCalculator initialization"""
        assert self.calculator is not None
        assert hasattr(self.calculator, 'calculate_cagr')

    def test_calculate_cagr_basic(self):
        """Test basic CAGR calculation"""
        cagr = self.calculator.calculate_cagr(1000, 1500, 3)
        assert isinstance(cagr, float)
        assert cagr > 0

    def test_calculate_cagr_negative_growth(self):
        """Test CAGR calculation with negative growth"""
        cagr = self.calculator.calculate_cagr(1000, 800, 2)
        assert isinstance(cagr, float)
        assert cagr < 0

    def test_validate_growth_rate(self):
        """Test growth rate validation"""
        is_valid = self.calculator.validate_growth_rate(0.10)
        assert isinstance(is_valid, bool)

    def test_format_growth_rate(self):
        """Test growth rate formatting"""
        formatted = self.calculator.format_growth_rate(0.1234)
        assert isinstance(formatted, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])