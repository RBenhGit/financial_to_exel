"""
Unit tests for profitability ratio calculations in FinancialCalculationEngine.

Tests comprehensive profitability ratio calculations including:
- Gross Profit Margin
- Operating Profit Margin

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
import math
from core.analysis.engines.financial_calculation_engine import FinancialCalculationEngine, CalculationResult


class TestProfitabilityRatios:
    """Test suite for profitability ratio calculations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialCalculationEngine()

    # =====================
    # Gross Profit Margin Tests
    # =====================

    def test_calculate_gross_profit_margin_normal_case(self):
        """Test gross profit margin calculation with normal values"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=400000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.4
        assert result.metadata['gross_profit'] == 400000
        assert result.metadata['revenue'] == 1000000
        assert result.metadata['calculation_method'] == 'Gross Profit Margin = Gross Profit / Revenue'
        assert result.metadata['interpretation'] == "Strong gross margin"

    def test_calculate_gross_profit_margin_excellent_margin(self):
        """Test gross profit margin calculation with excellent margin"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=700000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.7
        assert result.metadata['interpretation'] == "Excellent gross margin"

    def test_calculate_gross_profit_margin_moderate_margin(self):
        """Test gross profit margin calculation with moderate margin"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=250000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.25
        assert result.metadata['interpretation'] == "Moderate gross margin"

    def test_calculate_gross_profit_margin_low_margin(self):
        """Test gross profit margin calculation with low margin"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=100000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.1
        assert result.metadata['interpretation'] == "Low gross margin"

    def test_calculate_gross_profit_margin_negative_margin(self):
        """Test gross profit margin calculation with negative margin"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=-50000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == -0.05
        assert result.metadata['interpretation'] == "Negative gross margin - cost of goods sold exceeds revenue"

    def test_calculate_gross_profit_margin_zero_revenue(self):
        """Test gross profit margin with zero revenue"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=100000,
            revenue=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue cannot be zero" in result.error_message

    def test_calculate_gross_profit_margin_none_inputs(self):
        """Test gross profit margin with None inputs"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=None,
            revenue=1000000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

        result = self.engine.calculate_gross_profit_margin(
            gross_profit=400000,
            revenue=None
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    def test_calculate_gross_profit_margin_negative_revenue(self):
        """Test gross profit margin with negative revenue (should warn but calculate)"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=100000,
            revenue=-500000
        )

        assert result.is_valid is True
        assert result.value == -0.2

    def test_calculate_gross_profit_margin_very_high_margin(self):
        """Test gross profit margin with very high margin (should warn)"""
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=900000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.9
        assert result.metadata['interpretation'] == "Excellent gross margin"

    # =====================
    # Operating Profit Margin Tests
    # =====================

    def test_calculate_operating_profit_margin_normal_case(self):
        """Test operating profit margin calculation with normal values"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=200000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.2
        assert result.metadata['operating_income'] == 200000
        assert result.metadata['revenue'] == 1000000
        assert result.metadata['calculation_method'] == 'Operating Profit Margin = Operating Income / Revenue'
        assert result.metadata['interpretation'] == "Strong operating efficiency"

    def test_calculate_operating_profit_margin_excellent_efficiency(self):
        """Test operating profit margin calculation with excellent efficiency"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=300000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.3
        assert result.metadata['interpretation'] == "Excellent operating efficiency"

    def test_calculate_operating_profit_margin_moderate_efficiency(self):
        """Test operating profit margin calculation with moderate efficiency"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=80000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.08
        assert result.metadata['interpretation'] == "Moderate operating efficiency"

    def test_calculate_operating_profit_margin_low_efficiency(self):
        """Test operating profit margin calculation with low efficiency"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=20000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.02
        assert result.metadata['interpretation'] == "Low operating efficiency"

    def test_calculate_operating_profit_margin_negative_margin(self):
        """Test operating profit margin calculation with negative margin"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=-50000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == -0.05
        assert result.metadata['interpretation'] == "Negative operating margin - operating expenses exceed gross profit"

    def test_calculate_operating_profit_margin_zero_revenue(self):
        """Test operating profit margin with zero revenue"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=100000,
            revenue=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue cannot be zero" in result.error_message

    def test_calculate_operating_profit_margin_none_inputs(self):
        """Test operating profit margin with None inputs"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=None,
            revenue=1000000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

        result = self.engine.calculate_operating_profit_margin(
            operating_income=200000,
            revenue=None
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    def test_calculate_operating_profit_margin_negative_revenue(self):
        """Test operating profit margin with negative revenue (should warn but calculate)"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=100000,
            revenue=-500000
        )

        assert result.is_valid is True
        assert result.value == -0.2

    def test_calculate_operating_profit_margin_very_high_margin(self):
        """Test operating profit margin with very high margin (should warn)"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=600000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.6
        assert result.metadata['interpretation'] == "Excellent operating efficiency"

    def test_calculate_operating_profit_margin_zero_operating_income(self):
        """Test operating profit margin with zero operating income"""
        result = self.engine.calculate_operating_profit_margin(
            operating_income=0,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.0
        assert result.metadata['interpretation'] == "Low operating efficiency"

    # =====================
    # Net Profit Margin Tests
    # =====================

    def test_calculate_net_profit_margin_normal_case(self):
        """Test net profit margin calculation with normal values"""
        result = self.engine.calculate_net_profit_margin(
            net_income=150000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.15
        assert result.metadata['net_income'] == 150000
        assert result.metadata['revenue'] == 1000000
        assert result.metadata['calculation_method'] == 'Net Profit Margin = Net Income / Revenue'
        assert result.metadata['interpretation'] == "Strong net profitability"

    def test_calculate_net_profit_margin_excellent_profitability(self):
        """Test net profit margin calculation with excellent profitability"""
        result = self.engine.calculate_net_profit_margin(
            net_income=250000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.25
        assert result.metadata['interpretation'] == "Excellent net profitability"

    def test_calculate_net_profit_margin_moderate_profitability(self):
        """Test net profit margin calculation with moderate profitability"""
        result = self.engine.calculate_net_profit_margin(
            net_income=70000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.07
        assert result.metadata['interpretation'] == "Moderate net profitability"

    def test_calculate_net_profit_margin_low_profitability(self):
        """Test net profit margin calculation with low profitability"""
        result = self.engine.calculate_net_profit_margin(
            net_income=20000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.02
        assert result.metadata['interpretation'] == "Low net profitability"

    def test_calculate_net_profit_margin_negative_margin(self):
        """Test net profit margin calculation with negative margin (loss)"""
        result = self.engine.calculate_net_profit_margin(
            net_income=-50000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == -0.05
        assert result.metadata['interpretation'] == "Negative net margin - company is losing money"

    def test_calculate_net_profit_margin_zero_revenue(self):
        """Test net profit margin with zero revenue"""
        result = self.engine.calculate_net_profit_margin(
            net_income=100000,
            revenue=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Revenue cannot be zero" in result.error_message

    def test_calculate_net_profit_margin_none_inputs(self):
        """Test net profit margin with None inputs"""
        result = self.engine.calculate_net_profit_margin(
            net_income=None,
            revenue=1000000
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

        result = self.engine.calculate_net_profit_margin(
            net_income=150000,
            revenue=None
        )

        assert result.is_valid is False
        assert "Input values cannot be None" in result.error_message

    def test_calculate_net_profit_margin_negative_revenue(self):
        """Test net profit margin with negative revenue (should warn but calculate)"""
        result = self.engine.calculate_net_profit_margin(
            net_income=100000,
            revenue=-500000
        )

        assert result.is_valid is True
        assert result.value == -0.2

    def test_calculate_net_profit_margin_very_high_margin(self):
        """Test net profit margin with very high margin (should warn)"""
        result = self.engine.calculate_net_profit_margin(
            net_income=400000,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.4
        assert result.metadata['interpretation'] == "Excellent net profitability"

    def test_calculate_net_profit_margin_zero_net_income(self):
        """Test net profit margin with zero net income (break-even)"""
        result = self.engine.calculate_net_profit_margin(
            net_income=0,
            revenue=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.0
        assert result.metadata['interpretation'] == "Low net profitability"

    # =====================
    # Integration Tests
    # =====================

    def test_profitability_ratios_consistency(self):
        """Test that profitability ratios are consistent with logical relationships"""
        revenue = 1000000
        gross_profit = 400000
        operating_income = 200000
        net_income = 150000

        gross_margin = self.engine.calculate_gross_profit_margin(gross_profit, revenue)
        operating_margin = self.engine.calculate_operating_profit_margin(operating_income, revenue)
        net_margin = self.engine.calculate_net_profit_margin(net_income, revenue)

        # All should be valid
        assert all([gross_margin.is_valid, operating_margin.is_valid, net_margin.is_valid])

        # Logical relationship: Gross Margin ≥ Operating Margin ≥ Net Margin
        # (due to operating expenses and taxes reducing profit at each level)
        assert gross_margin.value >= operating_margin.value
        assert operating_margin.value >= net_margin.value

    @pytest.mark.parametrize("gross_profit,revenue,expected_margin", [
        (400000, 1000000, 0.4),
        (250000, 500000, 0.5),
        (150000, 1000000, 0.15),
        (600000, 800000, 0.75),
        (0, 1000000, 0.0),
    ])
    def test_gross_profit_margin_parametrized(self, gross_profit, revenue, expected_margin):
        """Parametrized test for gross profit margin calculations"""
        result = self.engine.calculate_gross_profit_margin(gross_profit, revenue)
        assert result.is_valid is True
        assert abs(result.value - expected_margin) < 0.001  # Handle floating point precision

    @pytest.mark.parametrize("operating_income,revenue,expected_margin", [
        (200000, 1000000, 0.2),
        (150000, 500000, 0.3),
        (50000, 1000000, 0.05),
        (300000, 800000, 0.375),
        (0, 1000000, 0.0),
        (-25000, 1000000, -0.025),
    ])
    def test_operating_profit_margin_parametrized(self, operating_income, revenue, expected_margin):
        """Parametrized test for operating profit margin calculations"""
        result = self.engine.calculate_operating_profit_margin(operating_income, revenue)
        assert result.is_valid is True
        assert abs(result.value - expected_margin) < 0.001  # Handle floating point precision

    @pytest.mark.parametrize("net_income,revenue,expected_margin", [
        (150000, 1000000, 0.15),
        (100000, 500000, 0.2),
        (25000, 1000000, 0.025),
        (200000, 800000, 0.25),
        (0, 1000000, 0.0),
        (-50000, 1000000, -0.05),
        (75000, 750000, 0.1),
    ])
    def test_net_profit_margin_parametrized(self, net_income, revenue, expected_margin):
        """Parametrized test for net profit margin calculations"""
        result = self.engine.calculate_net_profit_margin(net_income, revenue)
        assert result.is_valid is True
        assert abs(result.value - expected_margin) < 0.001  # Handle floating point precision

    def test_profitability_margin_extreme_values(self):
        """Test profitability margins with extreme values"""
        # Very large numbers
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=1e9,
            revenue=2e9
        )
        assert result.is_valid is True
        assert result.value == 0.5

        # Very small numbers
        result = self.engine.calculate_operating_profit_margin(
            operating_income=0.01,
            revenue=0.1
        )
        assert result.is_valid is True
        assert abs(result.value - 0.1) < 0.001  # Handle floating point precision

    def test_profitability_margin_edge_cases(self):
        """Test profitability margins with edge cases"""
        # Gross profit equals revenue (100% margin)
        result = self.engine.calculate_gross_profit_margin(
            gross_profit=1000000,
            revenue=1000000
        )
        assert result.is_valid is True
        assert result.value == 1.0

        # Operating income equals revenue (100% margin)
        result = self.engine.calculate_operating_profit_margin(
            operating_income=1000000,
            revenue=1000000
        )
        assert result.is_valid is True
        assert result.value == 1.0

    def test_profitability_margin_real_world_scenarios(self):
        """Test profitability margins with realistic business scenarios"""
        # Technology company with high margins
        tech_gross = self.engine.calculate_gross_profit_margin(
            gross_profit=800000,
            revenue=1000000
        )
        tech_operating = self.engine.calculate_operating_profit_margin(
            operating_income=300000,
            revenue=1000000
        )
        tech_net = self.engine.calculate_net_profit_margin(
            net_income=220000,
            revenue=1000000
        )

        assert all([tech_gross.is_valid, tech_operating.is_valid, tech_net.is_valid])
        assert tech_gross.value == 0.8
        assert tech_operating.value == 0.3
        assert tech_net.value == 0.22
        assert tech_gross.metadata['interpretation'] == "Excellent gross margin"
        assert tech_operating.metadata['interpretation'] == "Excellent operating efficiency"
        assert tech_net.metadata['interpretation'] == "Excellent net profitability"

        # Retail company with lower margins
        retail_gross = self.engine.calculate_gross_profit_margin(
            gross_profit=250000,
            revenue=1000000
        )
        retail_operating = self.engine.calculate_operating_profit_margin(
            operating_income=50000,
            revenue=1000000
        )
        retail_net = self.engine.calculate_net_profit_margin(
            net_income=30000,
            revenue=1000000
        )

        assert all([retail_gross.is_valid, retail_operating.is_valid, retail_net.is_valid])
        assert retail_gross.value == 0.25
        assert retail_operating.value == 0.05
        assert retail_net.value == 0.03
        assert retail_gross.metadata['interpretation'] == "Moderate gross margin"
        assert retail_operating.metadata['interpretation'] == "Moderate operating efficiency"
        assert retail_net.metadata['interpretation'] == "Low net profitability"

        # Loss-making company scenario
        loss_net = self.engine.calculate_net_profit_margin(
            net_income=-100000,
            revenue=1000000
        )
        assert loss_net.is_valid
        assert loss_net.value == -0.1
        assert loss_net.metadata['interpretation'] == "Negative net margin - company is losing money"

    # =====================
    # Return on Assets (ROA) Tests
    # =====================

    def test_calculate_return_on_assets_normal_case(self):
        """Test ROA calculation with normal values"""
        result = self.engine.calculate_return_on_assets(
            net_income=120000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.12
        assert result.metadata['net_income'] == 120000
        assert result.metadata['total_assets'] == 1000000
        assert result.metadata['average_assets'] is None
        assert result.metadata['assets_used'] == 1000000
        assert result.metadata['calculation_method'] == 'ROA = Net Income / Total Assets'
        assert result.metadata['interpretation'] == "Strong asset efficiency"

    def test_calculate_return_on_assets_with_average_assets(self):
        """Test ROA calculation using average assets"""
        result = self.engine.calculate_return_on_assets(
            net_income=150000,
            total_assets=1200000,
            average_assets=1100000
        )

        assert result.is_valid is True
        assert abs(result.value - (150000 / 1100000)) < 0.001
        assert result.metadata['average_assets'] == 1100000
        assert result.metadata['assets_used'] == 1100000
        assert result.metadata['calculation_method'] == 'ROA = Net Income / Average Assets'

    def test_calculate_return_on_assets_excellent_efficiency(self):
        """Test ROA calculation with excellent asset efficiency"""
        result = self.engine.calculate_return_on_assets(
            net_income=180000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.18
        assert result.metadata['interpretation'] == "Excellent asset efficiency"

    def test_calculate_return_on_assets_moderate_efficiency(self):
        """Test ROA calculation with moderate asset efficiency"""
        result = self.engine.calculate_return_on_assets(
            net_income=80000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.08
        assert result.metadata['interpretation'] == "Moderate asset efficiency"

    def test_calculate_return_on_assets_low_efficiency(self):
        """Test ROA calculation with low asset efficiency"""
        result = self.engine.calculate_return_on_assets(
            net_income=30000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.03
        assert result.metadata['interpretation'] == "Low asset efficiency"

    def test_calculate_return_on_assets_negative_roa(self):
        """Test ROA calculation with negative return (loss)"""
        result = self.engine.calculate_return_on_assets(
            net_income=-60000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == -0.06
        assert result.metadata['interpretation'] == "Negative ROA - assets are not generating positive returns"

    def test_calculate_return_on_assets_zero_assets(self):
        """Test ROA calculation with zero total assets"""
        result = self.engine.calculate_return_on_assets(
            net_income=100000,
            total_assets=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Assets denominator cannot be zero" in result.error_message

    def test_calculate_return_on_assets_zero_average_assets(self):
        """Test ROA calculation with zero average assets"""
        result = self.engine.calculate_return_on_assets(
            net_income=100000,
            total_assets=1000000,
            average_assets=0
        )

        assert result.is_valid is False
        assert result.value == 0.0
        assert "Assets denominator cannot be zero" in result.error_message

    def test_calculate_return_on_assets_none_inputs(self):
        """Test ROA calculation with None inputs"""
        result = self.engine.calculate_return_on_assets(
            net_income=None,
            total_assets=1000000
        )

        assert result.is_valid is False
        assert "Net income and total assets cannot be None" in result.error_message

        result = self.engine.calculate_return_on_assets(
            net_income=120000,
            total_assets=None
        )

        assert result.is_valid is False
        assert "Net income and total assets cannot be None" in result.error_message

    def test_calculate_return_on_assets_negative_assets(self):
        """Test ROA calculation with negative assets (financial distress scenario)"""
        result = self.engine.calculate_return_on_assets(
            net_income=50000,
            total_assets=-200000
        )

        assert result.is_valid is True
        assert result.value == -0.25

    def test_calculate_return_on_assets_very_high_roa(self):
        """Test ROA calculation with very high ROA (should warn)"""
        result = self.engine.calculate_return_on_assets(
            net_income=250000,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.25
        assert result.metadata['interpretation'] == "Excellent asset efficiency"

    def test_calculate_return_on_assets_zero_net_income(self):
        """Test ROA calculation with zero net income (break-even)"""
        result = self.engine.calculate_return_on_assets(
            net_income=0,
            total_assets=1000000
        )

        assert result.is_valid is True
        assert result.value == 0.0
        assert result.metadata['interpretation'] == "Low asset efficiency"

    @pytest.mark.parametrize("net_income,total_assets,expected_roa", [
        (120000, 1000000, 0.12),
        (80000, 800000, 0.10),
        (150000, 1500000, 0.10),
        (200000, 2000000, 0.10),
        (0, 1000000, 0.0),
        (-50000, 1000000, -0.05),
        (300000, 2000000, 0.15),
    ])
    def test_return_on_assets_parametrized(self, net_income, total_assets, expected_roa):
        """Parametrized test for ROA calculations"""
        result = self.engine.calculate_return_on_assets(net_income, total_assets)
        assert result.is_valid is True
        assert abs(result.value - expected_roa) < 0.001  # Handle floating point precision

    def test_return_on_assets_with_average_vs_period_end(self):
        """Test ROA calculation comparing average assets vs period-end assets"""
        net_income = 120000
        beginning_assets = 900000
        ending_assets = 1100000
        average_assets = (beginning_assets + ending_assets) / 2

        # Using period-end assets
        result_period_end = self.engine.calculate_return_on_assets(
            net_income=net_income,
            total_assets=ending_assets
        )

        # Using average assets
        result_average = self.engine.calculate_return_on_assets(
            net_income=net_income,
            total_assets=ending_assets,
            average_assets=average_assets
        )

        assert result_period_end.is_valid is True
        assert result_average.is_valid is True

        # Average assets method should be more accurate
        assert result_period_end.value == net_income / ending_assets
        assert result_average.value == net_income / average_assets

        # Verify metadata reflects the calculation method used
        assert "Total Assets" in result_period_end.metadata['calculation_method']
        assert "Average Assets" in result_average.metadata['calculation_method']

    def test_return_on_assets_extreme_values(self):
        """Test ROA calculation with extreme values"""
        # Very large numbers
        result = self.engine.calculate_return_on_assets(
            net_income=1e8,
            total_assets=1e9
        )
        assert result.is_valid is True
        assert result.value == 0.1

        # Very small numbers
        result = self.engine.calculate_return_on_assets(
            net_income=0.01,
            total_assets=0.1
        )
        assert result.is_valid is True
        assert abs(result.value - 0.1) < 0.001

    def test_return_on_assets_real_world_scenarios(self):
        """Test ROA calculation with realistic business scenarios"""
        # High-performing tech company
        tech_roa = self.engine.calculate_return_on_assets(
            net_income=200000,
            total_assets=1000000
        )
        assert tech_roa.is_valid is True
        assert tech_roa.value == 0.2
        assert tech_roa.metadata['interpretation'] == "Excellent asset efficiency"

        # Asset-heavy manufacturing company (lower ROA expected)
        manufacturing_roa = self.engine.calculate_return_on_assets(
            net_income=150000,
            total_assets=3000000
        )
        assert manufacturing_roa.is_valid is True
        assert manufacturing_roa.value == 0.05
        assert manufacturing_roa.metadata['interpretation'] == "Moderate asset efficiency"

        # Financial services company
        financial_roa = self.engine.calculate_return_on_assets(
            net_income=80000,
            total_assets=8000000
        )
        assert financial_roa.is_valid is True
        assert financial_roa.value == 0.01
        assert financial_roa.metadata['interpretation'] == "Low asset efficiency"

        # Distressed company with losses
        distressed_roa = self.engine.calculate_return_on_assets(
            net_income=-100000,
            total_assets=2000000
        )
        assert distressed_roa.is_valid is True
        assert distressed_roa.value == -0.05
        assert distressed_roa.metadata['interpretation'] == "Negative ROA - assets are not generating positive returns"