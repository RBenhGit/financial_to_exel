"""
Unit tests for Days Inventory Outstanding (DIO) calculation in FinancialCalculationEngine.

Tests cover:
- Basic DIO calculation using pre-calculated inventory turnover
- DIO calculation with automatic inventory turnover computation
- Different period lengths (annual, quarterly, monthly)
- Edge cases (zero turnover, infinite turnover, negative values)
- Just-in-time inventory scenarios
- High and low DIO warnings
"""

import pytest
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine


class TestDaysInventoryOutstanding:
    """Test suite for Days Inventory Outstanding (DIO) calculations"""

    @pytest.fixture
    def calculator(self):
        """Create a FinancialCalculationEngine instance for testing"""
        return FinancialCalculationEngine()

    # =====================
    # Basic DIO Calculations
    # =====================

    def test_dio_with_provided_turnover(self, calculator):
        """Test DIO calculation using pre-calculated inventory turnover"""
        # Inventory turnover of 12 means inventory is sold and replaced 12 times per year
        # DIO = 365 / 12 = 30.42 days
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=12.0,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.42, rel=0.01)
        assert result.metadata['inventory_turnover'] == 12.0
        assert result.metadata['days_in_period'] == 365
        assert 'inventory efficiency' in result.metadata['interpretation']

    def test_dio_with_calculated_turnover(self, calculator):
        """Test DIO calculation with automatic inventory turnover computation"""
        # COGS: 1,200,000, Inventory: 100,000
        # Inventory turnover = 1,200,000 / 100,000 = 12
        # DIO = 365 / 12 = 30.42 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_200_000,
            inventory=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.42, rel=0.01)
        assert result.metadata['cogs'] == 1_200_000
        assert result.metadata['inventory'] == 100_000

    def test_dio_with_average_inventory(self, calculator):
        """Test DIO calculation using average inventory"""
        # COGS: 1,200,000, Average Inventory: 150,000
        # Inventory turnover = 1,200,000 / 150,000 = 8
        # DIO = 365 / 8 = 45.625 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_200_000,
            average_inventory=150_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(45.625, rel=0.01)
        assert result.metadata['average_inventory'] == 150_000
        assert 'inventory efficiency' in result.metadata['interpretation']

    def test_dio_with_beginning_and_ending_inventory(self, calculator):
        """Test DIO calculation using beginning and ending inventory"""
        # COGS: 1,200,000, Beginning: 120,000, Ending: 180,000
        # Average Inventory = (120,000 + 180,000) / 2 = 150,000
        # Inventory turnover = 1,200,000 / 150,000 = 8
        # DIO = 365 / 8 = 45.625 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_200_000,
            beginning_inventory=120_000,
            ending_inventory=180_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(45.625, rel=0.01)

    # =====================
    # Different Period Lengths
    # =====================

    def test_dio_quarterly_period(self, calculator):
        """Test DIO calculation for quarterly period"""
        # Inventory turnover of 3 in a quarter (12 annualized)
        # DIO = 90 / 3 = 30 days
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=3.0,
            days_in_period=90
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.0, rel=0.01)
        assert result.metadata['days_in_period'] == 90

    def test_dio_monthly_period(self, calculator):
        """Test DIO calculation for monthly period"""
        # Inventory turnover of 1 in a month (12 annualized)
        # DIO = 30 / 1 = 30 days
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=1.0,
            days_in_period=30
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.0, rel=0.01)
        assert result.metadata['days_in_period'] == 30

    # =====================
    # Edge Cases
    # =====================

    def test_dio_zero_turnover(self, calculator):
        """Test DIO with zero inventory turnover"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=0.0,
            days_in_period=365
        )

        assert not result.is_valid
        assert "Inventory turnover cannot be zero" in result.error_message

    def test_dio_infinite_turnover_jit_inventory(self, calculator):
        """Test DIO with infinite turnover (just-in-time inventory system)"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=float('inf'),
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == 0.0
        assert 'no inventory' in result.metadata['interpretation'].lower() or 'just-in-time' in result.metadata['interpretation'].lower()

    def test_dio_negative_turnover(self, calculator, caplog):
        """Test DIO with negative inventory turnover"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=-5.0,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 0
        # Check that warning was logged
        assert "Negative inventory turnover" in caplog.text

    def test_dio_invalid_days_period(self, calculator):
        """Test DIO with invalid days in period"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=12.0,
            days_in_period=0
        )

        assert not result.is_valid
        assert "Days in period must be positive" in result.error_message

    def test_dio_negative_days_period(self, calculator):
        """Test DIO with negative days in period"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=12.0,
            days_in_period=-365
        )

        assert not result.is_valid
        assert "Days in period must be positive" in result.error_message

    # =====================
    # Missing Input Cases
    # =====================

    def test_dio_missing_all_inputs(self, calculator):
        """Test DIO with missing all required inputs"""
        result = calculator.calculate_days_inventory_outstanding(
            days_in_period=365
        )

        assert not result.is_valid
        assert "Failed to calculate inventory turnover" in result.error_message

    def test_dio_missing_cogs(self, calculator):
        """Test DIO with missing COGS"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory=100_000,
            days_in_period=365
        )

        assert not result.is_valid
        assert "Failed to calculate inventory turnover" in result.error_message

    # =====================
    # Warning Thresholds
    # =====================

    def test_dio_high_value_warning(self, calculator, caplog):
        """Test DIO with high value triggers warning"""
        # Very low turnover results in high DIO
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=2.5,  # 365 / 2.5 = 146 days
            days_in_period=365
        )

        assert result.is_valid
        assert result.value > 120
        assert "DIO" in caplog.text and "very high" in caplog.text
        assert 'Poor inventory efficiency' in result.metadata['interpretation']

    def test_dio_moderate_high_value_warning(self, calculator, caplog):
        """Test DIO with moderately high value triggers warning"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=3.5,  # 365 / 3.5 = 104.3 days
            days_in_period=365
        )

        assert result.is_valid
        assert 90 < result.value <= 120
        assert "DIO" in caplog.text and "high" in caplog.text
        assert 'Below average inventory efficiency' in result.metadata['interpretation']

    def test_dio_low_value_warning(self, calculator, caplog):
        """Test DIO with very low value triggers warning"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=30.0,  # 365 / 30 = 12.17 days
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 15
        assert "DIO" in caplog.text and "very low" in caplog.text

    # =====================
    # Industry Scenarios
    # =====================

    def test_dio_retail_fast_moving_goods(self, calculator):
        """Test DIO for retail with fast-moving consumer goods"""
        # COGS: 12,000,000, Inventory: 1,000,000
        # Turnover = 12,000,000 / 1,000,000 = 12
        # DIO = 365 / 12 = 30.42 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=12_000_000,
            inventory=1_000_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(30.42, rel=0.01)
        assert 'Strong inventory efficiency' in result.metadata['interpretation']

    def test_dio_manufacturing_slow_moving(self, calculator):
        """Test DIO for manufacturing with slow-moving inventory"""
        # COGS: 5,000,000, Inventory: 2,000,000
        # Turnover = 5,000,000 / 2,000,000 = 2.5
        # DIO = 365 / 2.5 = 146 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=5_000_000,
            inventory=2_000_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(146.0, rel=0.01)
        assert 'Poor inventory efficiency' in result.metadata['interpretation']

    def test_dio_grocery_store_perishables(self, calculator):
        """Test DIO for grocery store with perishable goods"""
        # COGS: 36,500,000, Inventory: 500,000
        # Turnover = 36,500,000 / 500,000 = 73
        # DIO = 365 / 73 = 5 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=36_500_000,
            inventory=500_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value < 10
        # Very low DIO indicates rapid inventory turnover (perishables)

    def test_dio_luxury_goods_slow_turnover(self, calculator):
        """Test DIO for luxury goods with slow turnover"""
        # COGS: 1,000,000, Inventory: 500,000
        # Turnover = 1,000,000 / 500,000 = 2
        # DIO = 365 / 2 = 182.5 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_000_000,
            inventory=500_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value > 150
        assert 'Poor inventory efficiency' in result.metadata['interpretation']

    def test_dio_automotive_parts(self, calculator):
        """Test DIO for automotive parts distributor"""
        # COGS: 6,000,000, Inventory: 1,000,000
        # Turnover = 6,000,000 / 1,000,000 = 6
        # DIO = 365 / 6 = 60.83 days
        result = calculator.calculate_days_inventory_outstanding(
            cogs=6_000_000,
            inventory=1_000_000,
            days_in_period=365
        )

        assert result.is_valid
        assert result.value == pytest.approx(60.83, rel=0.01)
        assert 'Moderate inventory efficiency' in result.metadata['interpretation']

    # =====================
    # Metadata Validation
    # =====================

    def test_dio_metadata_completeness(self, calculator):
        """Test that DIO result includes complete metadata"""
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_200_000,
            inventory=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert 'inventory_turnover' in result.metadata
        assert 'days_in_period' in result.metadata
        assert 'cogs' in result.metadata
        assert 'inventory' in result.metadata
        assert 'calculation_method' in result.metadata
        assert 'interpretation' in result.metadata

    def test_dio_calculation_method_provided_turnover(self, calculator):
        """Test calculation method when turnover is provided"""
        result = calculator.calculate_days_inventory_outstanding(
            inventory_turnover=12.0,
            days_in_period=365
        )

        assert result.is_valid
        assert 'provided inventory turnover' in result.metadata['calculation_method']

    def test_dio_calculation_method_calculated_turnover(self, calculator):
        """Test calculation method when turnover is calculated"""
        result = calculator.calculate_days_inventory_outstanding(
            cogs=1_200_000,
            inventory=100_000,
            days_in_period=365
        )

        assert result.is_valid
        assert 'calculated from COGS and inventory' in result.metadata['calculation_method']
