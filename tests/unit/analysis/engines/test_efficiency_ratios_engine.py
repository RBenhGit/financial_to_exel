"""
Unit tests for efficiency ratio calculations in FinancialRatiosEngine.

Tests comprehensive efficiency/activity ratio calculations including:
- Asset Turnover
- Inventory Turnover
- Receivables Turnover
- Payables Turnover
- Days Sales Outstanding (DSO)
- Days Inventory Outstanding (DIO)
- Days Payable Outstanding (DPO)
- Cash Conversion Cycle (CCC)
- Fixed Asset Turnover
- Working Capital Turnover

Each test covers normal operations, edge cases, error handling, and validation.
"""

import pytest
from core.analysis.engines.financial_ratios_engine import (
    FinancialRatiosEngine,
    RatioInputs,
    RatioResult,
    RatioCategory
)


class TestEfficiencyRatiosEngine:
    """Test suite for efficiency ratio calculations in FinancialRatiosEngine"""

    def setup_method(self):
        """Set up test fixtures"""
        self.engine = FinancialRatiosEngine()

    # ===========================
    # Asset Turnover Tests
    # ===========================

    def test_calculate_asset_turnover_excellent(self):
        """Test asset turnover calculation with excellent efficiency"""
        inputs = RatioInputs(
            revenue=10000000,
            total_assets=4000000
        )

        result = self.engine.calculate_asset_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 2.5
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent asset utilization" in result.interpretation

    def test_calculate_asset_turnover_good(self):
        """Test asset turnover calculation with good efficiency"""
        inputs = RatioInputs(
            revenue=6000000,
            total_assets=5000000
        )

        result = self.engine.calculate_asset_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 1.2
        assert "Good asset utilization" in result.interpretation

    def test_calculate_asset_turnover_zero_assets(self):
        """Test asset turnover with zero total assets"""
        inputs = RatioInputs(
            revenue=1000000,
            total_assets=0
        )

        result = self.engine.calculate_asset_turnover(inputs)

        assert result.is_valid is False
        assert "Total assets cannot be zero" in result.error_message

    # ===========================
    # Inventory Turnover Tests
    # ===========================

    def test_calculate_inventory_turnover_excellent(self):
        """Test inventory turnover calculation with excellent efficiency"""
        inputs = RatioInputs(
            cost_of_goods_sold=12000000,
            inventory=1000000
        )

        result = self.engine.calculate_inventory_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 12.0
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent inventory management" in result.interpretation

    def test_calculate_inventory_turnover_good(self):
        """Test inventory turnover calculation with good efficiency"""
        inputs = RatioInputs(
            cost_of_goods_sold=7000000,
            inventory=1000000
        )

        result = self.engine.calculate_inventory_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 7.0
        assert "Good inventory management" in result.interpretation

    def test_calculate_inventory_turnover_slow(self):
        """Test inventory turnover calculation with slow turnover"""
        inputs = RatioInputs(
            cost_of_goods_sold=3000000,
            inventory=1000000
        )

        result = self.engine.calculate_inventory_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 3.0
        assert "Slow inventory turnover" in result.interpretation

    def test_calculate_inventory_turnover_zero_inventory(self):
        """Test inventory turnover with zero inventory"""
        inputs = RatioInputs(
            cost_of_goods_sold=5000000,
            inventory=0
        )

        result = self.engine.calculate_inventory_turnover(inputs)

        assert result.is_valid is False
        assert result.value == float('inf')

    # ===================================
    # Receivables Turnover Tests
    # ===================================

    def test_calculate_receivables_turnover_excellent(self):
        """Test receivables turnover calculation with excellent collection"""
        inputs = RatioInputs(
            revenue=15000000,
            accounts_receivable=1000000
        )

        result = self.engine.calculate_receivables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 15.0
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent receivables collection" in result.interpretation

    def test_calculate_receivables_turnover_good(self):
        """Test receivables turnover calculation with good collection"""
        inputs = RatioInputs(
            revenue=10000000,
            accounts_receivable=1000000
        )

        result = self.engine.calculate_receivables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 10.0
        assert "Good receivables collection" in result.interpretation

    def test_calculate_receivables_turnover_slow(self):
        """Test receivables turnover calculation with slow collection"""
        inputs = RatioInputs(
            revenue=3000000,
            accounts_receivable=1000000
        )

        result = self.engine.calculate_receivables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 3.0
        assert "Very slow receivables collection" in result.interpretation

    def test_calculate_receivables_turnover_zero_receivables(self):
        """Test receivables turnover with zero accounts receivable (cash business)"""
        inputs = RatioInputs(
            revenue=10000000,
            accounts_receivable=0
        )

        result = self.engine.calculate_receivables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == float('inf')
        assert "cash-based business" in result.interpretation

    # ===============================
    # Payables Turnover Tests
    # ===============================

    def test_calculate_payables_turnover_fast(self):
        """Test payables turnover calculation with fast payment"""
        inputs = RatioInputs(
            cost_of_goods_sold=15000000,
            accounts_payable=1000000
        )

        result = self.engine.calculate_payables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 15.0
        assert result.category == RatioCategory.EFFICIENCY
        assert "Very fast supplier payments" in result.interpretation

    def test_calculate_payables_turnover_good(self):
        """Test payables turnover calculation with good payment timing"""
        inputs = RatioInputs(
            cost_of_goods_sold=9000000,
            accounts_payable=1000000
        )

        result = self.engine.calculate_payables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 9.0
        assert "Good supplier payment efficiency" in result.interpretation

    def test_calculate_payables_turnover_slow(self):
        """Test payables turnover calculation with slow payment"""
        inputs = RatioInputs(
            cost_of_goods_sold=3000000,
            accounts_payable=1000000
        )

        result = self.engine.calculate_payables_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 3.0
        assert "Very slow supplier payments" in result.interpretation

    def test_calculate_payables_turnover_missing_data(self):
        """Test payables turnover with missing accounts payable data"""
        inputs = RatioInputs(
            cost_of_goods_sold=10000000
            # accounts_payable not set
        )

        result = self.engine.calculate_payables_turnover(inputs)

        assert result.is_valid is False
        assert "Missing accounts payable data" in result.error_message

    # ===================================
    # Days Sales Outstanding (DSO) Tests
    # ===================================

    def test_calculate_dso_excellent(self):
        """Test DSO calculation with excellent collection efficiency"""
        inputs = RatioInputs(
            revenue=3650000,  # 10,000 per day
            accounts_receivable=250000  # 25 days
        )

        result = self.engine.calculate_days_sales_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 25.0) < 0.1
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent collection efficiency" in result.interpretation

    def test_calculate_dso_good(self):
        """Test DSO calculation with good collection efficiency"""
        inputs = RatioInputs(
            revenue=3650000,  # 10,000 per day
            accounts_receivable=400000  # ~40 days
        )

        result = self.engine.calculate_days_sales_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 40.0) < 0.1
        assert "Good collection efficiency" in result.interpretation

    def test_calculate_dso_slow(self):
        """Test DSO calculation with slow collection"""
        inputs = RatioInputs(
            revenue=3650000,  # 10,000 per day
            accounts_receivable=800000  # ~80 days
        )

        result = self.engine.calculate_days_sales_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 80.0) < 0.1
        assert "Slow collection" in result.interpretation

    def test_calculate_dso_zero_revenue(self):
        """Test DSO calculation with zero revenue"""
        inputs = RatioInputs(
            revenue=0,
            accounts_receivable=100000
        )

        result = self.engine.calculate_days_sales_outstanding(inputs)

        assert result.is_valid is False
        assert "Revenue cannot be zero" in result.error_message

    # ======================================
    # Days Inventory Outstanding (DIO) Tests
    # ======================================

    def test_calculate_dio_excellent(self):
        """Test DIO calculation with excellent inventory efficiency"""
        inputs = RatioInputs(
            cost_of_goods_sold=7300000,  # 20,000 per day
            inventory=500000  # 25 days
        )

        result = self.engine.calculate_days_inventory_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 25.0) < 0.1
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent inventory efficiency" in result.interpretation

    def test_calculate_dio_good(self):
        """Test DIO calculation with good inventory efficiency"""
        inputs = RatioInputs(
            cost_of_goods_sold=7300000,  # 20,000 per day
            inventory=1000000  # ~50 days
        )

        result = self.engine.calculate_days_inventory_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 50.0) < 0.1
        assert "Good inventory efficiency" in result.interpretation

    def test_calculate_dio_slow(self):
        """Test DIO calculation with slow inventory turnover"""
        inputs = RatioInputs(
            cost_of_goods_sold=3650000,  # 10,000 per day
            inventory=1000000  # 100 days
        )

        result = self.engine.calculate_days_inventory_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 100.0) < 0.1
        assert "Slow inventory turnover" in result.interpretation

    def test_calculate_dio_zero_cogs(self):
        """Test DIO calculation with zero COGS"""
        inputs = RatioInputs(
            cost_of_goods_sold=0,
            inventory=500000
        )

        result = self.engine.calculate_days_inventory_outstanding(inputs)

        assert result.is_valid is False
        assert "Cost of goods sold cannot be zero" in result.error_message

    # =======================================
    # Days Payable Outstanding (DPO) Tests
    # =======================================

    def test_calculate_dpo_extended(self):
        """Test DPO calculation with extended payment terms"""
        inputs = RatioInputs(
            cost_of_goods_sold=3650000,  # 10,000 per day
            accounts_payable=1000000  # ~100 days
        )

        result = self.engine.calculate_days_payable_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 100.0) < 0.1
        assert result.category == RatioCategory.EFFICIENCY
        assert "Extended payment terms" in result.interpretation

    def test_calculate_dpo_good(self):
        """Test DPO calculation with good payment timing"""
        inputs = RatioInputs(
            cost_of_goods_sold=3650000,  # 10,000 per day
            accounts_payable=600000  # ~60 days
        )

        result = self.engine.calculate_days_payable_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 60.0) < 0.1
        assert "Good payment timing" in result.interpretation

    def test_calculate_dpo_fast(self):
        """Test DPO calculation with fast supplier payments"""
        inputs = RatioInputs(
            cost_of_goods_sold=3650000,  # 10,000 per day
            accounts_payable=250000  # ~25 days
        )

        result = self.engine.calculate_days_payable_outstanding(inputs)

        assert result.is_valid is True
        assert abs(result.value - 25.0) < 0.1
        assert "Very fast supplier payments" in result.interpretation

    def test_calculate_dpo_missing_payables(self):
        """Test DPO calculation with missing accounts payable"""
        inputs = RatioInputs(
            cost_of_goods_sold=3650000
            # accounts_payable not set
        )

        result = self.engine.calculate_days_payable_outstanding(inputs)

        assert result.is_valid is False
        assert "Missing accounts payable data" in result.error_message

    # ===================================
    # Cash Conversion Cycle (CCC) Tests
    # ===================================

    def test_calculate_ccc_excellent(self):
        """Test CCC calculation with excellent working capital efficiency"""
        inputs = RatioInputs(
            revenue=3650000,  # For DSO
            accounts_receivable=250000,  # DSO = 25 days
            cost_of_goods_sold=2920000,  # For DIO and DPO
            inventory=200000,  # DIO = 25 days
            accounts_payable=200000  # DPO = 25 days
        )

        result = self.engine.calculate_cash_conversion_cycle(inputs)

        assert result.is_valid is True
        # CCC = DSO + DIO - DPO = 25 + 25 - 25 = 25
        assert abs(result.value - 25.0) < 0.1
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent cash conversion" in result.interpretation

    def test_calculate_ccc_negative(self):
        """Test CCC calculation with negative CCC (exceptional efficiency)"""
        inputs = RatioInputs(
            revenue=3650000,
            accounts_receivable=250000,  # DSO = 25 days
            cost_of_goods_sold=3650000,
            inventory=250000,  # DIO = 25 days
            accounts_payable=2000000  # DPO = 200 days
        )

        result = self.engine.calculate_cash_conversion_cycle(inputs)

        assert result.is_valid is True
        # CCC = 25 + 25 - 200 = -150
        assert result.value < 0
        assert "Negative CCC" in result.interpretation

    def test_calculate_ccc_slow(self):
        """Test CCC calculation with slow cash conversion"""
        inputs = RatioInputs(
            revenue=3650000,
            accounts_receivable=800000,  # DSO = 80 days
            cost_of_goods_sold=3650000,
            inventory=1000000,  # DIO = 100 days
            accounts_payable=400000  # DPO = 40 days
        )

        result = self.engine.calculate_cash_conversion_cycle(inputs)

        assert result.is_valid is True
        # CCC = 80 + 100 - 40 = 140
        assert abs(result.value - 140.0) < 0.1
        assert "Very slow cash conversion" in result.interpretation

    def test_calculate_ccc_missing_component(self):
        """Test CCC calculation with missing DSO component"""
        inputs = RatioInputs(
            # Missing revenue for DSO
            cost_of_goods_sold=3650000,
            inventory=500000,
            accounts_payable=400000
        )

        result = self.engine.calculate_cash_conversion_cycle(inputs)

        assert result.is_valid is False
        assert "DSO" in result.error_message

    # ======================================
    # Fixed Asset Turnover Tests
    # ======================================

    def test_calculate_fixed_asset_turnover_excellent(self):
        """Test fixed asset turnover with excellent utilization"""
        inputs = RatioInputs(
            revenue=20000000,
            net_fixed_assets=3000000
        )

        result = self.engine.calculate_fixed_asset_turnover(inputs)

        assert result.is_valid is True
        assert abs(result.value - 6.67) < 0.1
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent fixed asset utilization" in result.interpretation

    def test_calculate_fixed_asset_turnover_good(self):
        """Test fixed asset turnover with good utilization"""
        inputs = RatioInputs(
            revenue=15000000,
            net_fixed_assets=4000000
        )

        result = self.engine.calculate_fixed_asset_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 3.75
        assert "Good fixed asset utilization" in result.interpretation

    def test_calculate_fixed_asset_turnover_fallback_calculation(self):
        """Test fixed asset turnover with fallback calculation from total/current assets"""
        inputs = RatioInputs(
            revenue=10000000,
            total_assets=8000000,
            current_assets=3000000
            # net_fixed_assets = total - current = 5M
        )

        result = self.engine.calculate_fixed_asset_turnover(inputs)

        assert result.is_valid is True
        assert result.value == 2.0  # 10M / 5M
        assert "Adequate fixed asset utilization" in result.interpretation

    def test_calculate_fixed_asset_turnover_zero_assets(self):
        """Test fixed asset turnover with zero fixed assets (asset-light model)"""
        inputs = RatioInputs(
            revenue=10000000,
            net_fixed_assets=0
        )

        result = self.engine.calculate_fixed_asset_turnover(inputs)

        assert result.is_valid is True
        assert result.value == float('inf')
        assert "asset-light business model" in result.interpretation

    def test_calculate_fixed_asset_turnover_missing_data(self):
        """Test fixed asset turnover with missing fixed assets data"""
        inputs = RatioInputs(
            revenue=10000000
            # No net_fixed_assets, total_assets, or current_assets
        )

        result = self.engine.calculate_fixed_asset_turnover(inputs)

        assert result.is_valid is False
        assert "Missing net fixed assets data" in result.error_message

    # =========================================
    # Working Capital Turnover Tests
    # =========================================

    def test_calculate_working_capital_turnover_excellent(self):
        """Test working capital turnover with excellent efficiency"""
        inputs = RatioInputs(
            revenue=12000000,
            current_assets=3000000,
            current_liabilities=1000000
        )

        result = self.engine.calculate_working_capital_turnover(inputs)

        assert result.is_valid is True
        # Working capital = 3M - 1M = 2M; Turnover = 12M / 2M = 6
        assert result.value == 6.0
        assert result.category == RatioCategory.EFFICIENCY
        assert "Excellent working capital efficiency" in result.interpretation

    def test_calculate_working_capital_turnover_good(self):
        """Test working capital turnover with good efficiency"""
        inputs = RatioInputs(
            revenue=10000000,
            current_assets=4000000,
            current_liabilities=2000000
        )

        result = self.engine.calculate_working_capital_turnover(inputs)

        assert result.is_valid is True
        # Working capital = 4M - 2M = 2M; Turnover = 10M / 2M = 5
        assert result.value == 5.0
        assert "Good working capital efficiency" in result.interpretation

    def test_calculate_working_capital_turnover_negative_wc(self):
        """Test working capital turnover with negative working capital"""
        inputs = RatioInputs(
            revenue=10000000,
            current_assets=1000000,
            current_liabilities=2000000
        )

        result = self.engine.calculate_working_capital_turnover(inputs)

        assert result.is_valid is True
        # Working capital = 1M - 2M = -1M; Turnover uses abs = 10M / 1M = 10
        assert result.value == 10.0
        assert "Negative working capital" in result.interpretation

    def test_calculate_working_capital_turnover_zero_wc(self):
        """Test working capital turnover with zero working capital"""
        inputs = RatioInputs(
            revenue=10000000,
            current_assets=2000000,
            current_liabilities=2000000
        )

        result = self.engine.calculate_working_capital_turnover(inputs)

        assert result.is_valid is False
        assert result.value == float('inf')
        assert "Working capital cannot be zero" in result.error_message

    def test_calculate_working_capital_turnover_missing_data(self):
        """Test working capital turnover with missing current liabilities"""
        inputs = RatioInputs(
            revenue=10000000,
            current_assets=3000000
            # Missing current_liabilities
        )

        result = self.engine.calculate_working_capital_turnover(inputs)

        assert result.is_valid is False
        assert "Missing current assets or current liabilities data" in result.error_message

    # =========================================
    # Integration Tests
    # =========================================

    def test_calculate_all_efficiency_ratios(self):
        """Test comprehensive calculation of all efficiency ratios"""
        inputs = RatioInputs(
            revenue=10000000,
            cost_of_goods_sold=6000000,
            total_assets=8000000,
            current_assets=4000000,
            current_liabilities=2000000,
            accounts_receivable=1000000,
            inventory=500000,
            accounts_payable=600000,
            net_fixed_assets=4000000
        )

        # Calculate all ratios
        all_results = self.engine.calculate_all_ratios(inputs)

        # Verify efficiency ratios are present
        efficiency_ratios = [
            'asset_turnover',
            'inventory_turnover',
            'receivables_turnover',
            'payables_turnover',
            'days_sales_outstanding',
            'days_inventory_outstanding',
            'days_payable_outstanding',
            'cash_conversion_cycle',
            'fixed_asset_turnover',
            'working_capital_turnover'
        ]

        for ratio_name in efficiency_ratios:
            assert ratio_name in all_results
            assert isinstance(all_results[ratio_name], RatioResult)

        # Verify calculations
        assert all_results['asset_turnover'].value == 1.25  # 10M / 8M
        assert all_results['inventory_turnover'].value == 12.0  # 6M / 0.5M
        assert all_results['receivables_turnover'].value == 10.0  # 10M / 1M
        assert all_results['payables_turnover'].value == 10.0  # 6M / 0.6M
        assert abs(all_results['days_sales_outstanding'].value - 36.5) < 0.1
        assert abs(all_results['days_inventory_outstanding'].value - 30.4) < 0.1
        assert abs(all_results['days_payable_outstanding'].value - 36.5) < 0.1
        # CCC = DSO + DIO - DPO ≈ 36.5 + 30.4 - 36.5 ≈ 30.4
        assert abs(all_results['cash_conversion_cycle'].value - 30.4) < 0.1
        assert all_results['fixed_asset_turnover'].value == 2.5  # 10M / 4M
        assert all_results['working_capital_turnover'].value == 5.0  # 10M / (4M-2M)

    def test_efficiency_ratios_with_real_world_data(self):
        """Test efficiency ratios with realistic company data (retail example)"""
        # Simulating a retail company with fast inventory turnover
        inputs = RatioInputs(
            revenue=50000000,
            cost_of_goods_sold=35000000,
            total_assets=30000000,
            current_assets=15000000,
            current_liabilities=10000000,
            accounts_receivable=2000000,
            inventory=3000000,
            accounts_payable=5000000,
            net_fixed_assets=15000000
        )

        result_asset_turnover = self.engine.calculate_asset_turnover(inputs)
        result_inventory_turnover = self.engine.calculate_inventory_turnover(inputs)
        result_ccc = self.engine.calculate_cash_conversion_cycle(inputs)

        # Retail should have high asset turnover
        assert result_asset_turnover.is_valid is True
        assert result_asset_turnover.value > 1.0

        # Retail should have high inventory turnover
        assert result_inventory_turnover.is_valid is True
        assert result_inventory_turnover.value > 10.0  # 35M / 3M ≈ 11.67

        # CCC should be valid for retail (can be negative if very efficient)
        assert result_ccc.is_valid is True
        # Negative CCC is actually possible for efficient retailers
        assert isinstance(result_ccc.value, (int, float))
