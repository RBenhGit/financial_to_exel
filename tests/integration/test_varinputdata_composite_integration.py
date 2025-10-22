"""
Integration Tests for VarInputData and CompositeVariableCalculator
==================================================================

Tests the seamless integration between VarInputData and CompositeVariableCalculator,
ensuring automatic calculation of composite variables when base variables are updated.

Test Coverage:
--------------
1. Automatic composite calculation on set_variable()
2. Lazy calculation on get_variable() for missing composite variables
3. Manual calculation via calculate_composite_variables()
4. Thread-safety for concurrent variable updates
5. Configuration options (enable/disable auto-calculation)
6. Metadata tracking for calculated variables
7. Caching behavior and performance
8. Event emission for composite variable changes
"""

import pytest
import threading
import time
from datetime import datetime
from typing import Dict, Any

from core.data_processing.var_input_data import (
    VarInputData,
    get_var_input_data,
    VariableMetadata,
    DataChangeEvent,
    LazyLoadConfig
)


@pytest.fixture
def var_data():
    """Create a fresh VarInputData instance for each test."""
    # Reset singleton for testing
    VarInputData._instance = None
    VarInputData._VarInputData__initialized = False  # Reset the __initialized flag

    # Register all standard variables
    from core.data_processing.standard_financial_variables import register_all_variables
    from core.data_processing.financial_variable_registry import get_registry, FinancialVariableRegistry

    # Reset registry singleton
    FinancialVariableRegistry._instance = None
    registry = get_registry()
    register_all_variables(registry)

    instance = get_var_input_data()
    # Manually set enable_auto_calculation if needed
    instance._enable_auto_calculation = True
    if not instance._composite_calculator:
        from core.data_processing.composite_variable_registry import create_standard_calculator
        instance._composite_calculator = create_standard_calculator(
            enable_caching=True,
            enable_parallel=True
        )
    yield instance
    # Cleanup
    instance.clear_cache()


@pytest.fixture
def var_data_no_auto_calc():
    """Create VarInputData without automatic calculation."""
    VarInputData._instance = None
    VarInputData._VarInputData__initialized = False  # Reset the __initialized flag

    # Register all standard variables
    from core.data_processing.standard_financial_variables import register_all_variables
    from core.data_processing.financial_variable_registry import get_registry, FinancialVariableRegistry

    # Reset registry singleton
    FinancialVariableRegistry._instance = None
    registry = get_registry()
    register_all_variables(registry)

    instance = get_var_input_data()
    # Disable auto-calculation
    instance._enable_auto_calculation = False
    instance._composite_calculator = None
    yield instance
    instance.clear_cache()


class TestAutomaticCompositeCalculation:
    """Test automatic calculation of composite variables."""

    def test_basic_auto_calculation(self, var_data):
        """Test that setting base variables automatically calculates composites."""
        symbol = "AAPL"
        period = "2023"

        # Set base variables
        var_data.set_variable(symbol, "revenue", 394328, period=period, source="test")
        var_data.set_variable(symbol, "cost_of_revenue", 223546, period=period, source="test")

        # Composite variables should be automatically calculated
        gross_profit = var_data.get_variable(symbol, "gross_profit", period=period)
        assert gross_profit is not None
        assert gross_profit == pytest.approx(394328 - 223546)

        gross_margin = var_data.get_variable(symbol, "gross_margin", period=period)
        assert gross_margin is not None
        assert gross_margin == pytest.approx((394328 - 223546) / 394328)

    def test_metadata_for_composite_variables(self, var_data):
        """Test that composite variables have correct metadata."""
        symbol = "TSLA"
        period = "2023"

        # Set base variables
        var_data.set_variable(symbol, "net_income", 15000, period=period, source="test")
        var_data.set_variable(symbol, "shareholders_equity", 100000, period=period, source="test")

        # Get composite variable with metadata
        roe, metadata = var_data.get_variable(symbol, "roe", period=period, include_metadata=True)

        assert roe is not None
        assert roe == pytest.approx(0.15)  # 15000 / 100000

        # Check metadata
        assert metadata.source == "calculated"
        assert metadata.calculation_method == "CompositeVariableCalculator"
        assert metadata.validation_passed is True
        assert "shareholders_equity" in metadata.dependencies or "net_income" in metadata.dependencies

    def test_multiple_composite_variables(self, var_data):
        """Test calculation of multiple related composite variables."""
        symbol = "GOOGL"
        period = "2023"

        # Set comprehensive base data
        var_data.set_variable(symbol, "revenue", 300000, period=period, source="test")
        var_data.set_variable(symbol, "cost_of_revenue", 120000, period=period, source="test")
        var_data.set_variable(symbol, "operating_income", 90000, period=period, source="test")
        var_data.set_variable(symbol, "net_income", 75000, period=period, source="test")
        var_data.set_variable(symbol, "total_assets", 500000, period=period, source="test")
        var_data.set_variable(symbol, "shareholders_equity", 300000, period=period, source="test")

        # Check multiple composite variables
        gross_profit = var_data.get_variable(symbol, "gross_profit", period=period)
        assert gross_profit == pytest.approx(180000)  # revenue - cost_of_revenue

        gross_margin = var_data.get_variable(symbol, "gross_margin", period=period)
        assert gross_margin == pytest.approx(0.6)  # gross_profit / revenue

        operating_margin = var_data.get_variable(symbol, "operating_margin", period=period)
        assert operating_margin == pytest.approx(0.3)  # operating_income / revenue

        net_margin = var_data.get_variable(symbol, "net_margin", period=period)
        assert net_margin == pytest.approx(0.25)  # net_income / revenue

        roe = var_data.get_variable(symbol, "roe", period=period)
        assert roe == pytest.approx(0.25)  # net_income / shareholders_equity

        roa = var_data.get_variable(symbol, "roa", period=period)
        assert roa == pytest.approx(0.15)  # net_income / total_assets


class TestLazyCalculation:
    """Test lazy calculation of composite variables."""

    def test_lazy_calculation_on_get(self, var_data):
        """Test that composite variables are calculated on demand when accessed."""
        symbol = "MSFT"
        period = "2023"

        # Set base variables without triggering auto-calculation
        var_data.set_variable(symbol, "revenue", 200000, period=period, source="test",
                            trigger_composite_calculation=False)
        var_data.set_variable(symbol, "net_income", 50000, period=period, source="test",
                            trigger_composite_calculation=False)

        # Composite variable should not exist yet
        net_margin_initial = var_data.get_variable(symbol, "net_margin", period=period,
                                                   calculate_if_missing=False)
        assert net_margin_initial is None

        # Request composite variable with lazy calculation enabled
        net_margin = var_data.get_variable(symbol, "net_margin", period=period,
                                          calculate_if_missing=True)

        # Should be calculated on demand
        assert net_margin is not None
        assert net_margin == pytest.approx(0.25)  # 50000 / 200000


class TestManualCalculation:
    """Test manual triggering of composite variable calculation."""

    def test_manual_calculation_method(self, var_data_no_auto_calc):
        """Test manually triggering composite calculation."""
        symbol = "AMZN"
        period = "2023"

        # Re-enable calculator for manual calculation (even though auto is disabled)
        from core.data_processing.composite_variable_registry import create_standard_calculator
        var_data_no_auto_calc._composite_calculator = create_standard_calculator(
            enable_caching=True,
            enable_parallel=True
        )

        # Set base variables (no auto-calculation)
        var_data_no_auto_calc.set_variable(symbol, "revenue", 500000, period=period, source="test")
        var_data_no_auto_calc.set_variable(symbol, "net_income", 25000, period=period, source="test")

        # Composite variables should not be calculated yet (auto-calc is disabled)
        net_margin_before = var_data_no_auto_calc.get_variable(symbol, "net_margin", period=period,
                                                               calculate_if_missing=False)
        assert net_margin_before is None

        # Manually trigger calculation
        results = var_data_no_auto_calc.calculate_composite_variables(symbol, period)

        assert "net_margin" in results
        assert results["net_margin"] == pytest.approx(0.05)

        # Now it should be available
        net_margin_after = var_data_no_auto_calc.get_variable(symbol, "net_margin", period=period)
        assert net_margin_after == pytest.approx(0.05)

    def test_force_recalculation(self, var_data):
        """Test force recalculation of existing composite variables."""
        symbol = "META"
        period = "2023"

        # Set initial base variables
        var_data.set_variable(symbol, "revenue", 100000, period=period, source="test")
        var_data.set_variable(symbol, "net_income", 20000, period=period, source="test")

        initial_margin = var_data.get_variable(symbol, "net_margin", period=period)
        assert initial_margin == pytest.approx(0.2)

        # Update base variable
        var_data.set_variable(symbol, "net_income", 30000, period=period, source="test")

        # Force recalculation
        results = var_data.calculate_composite_variables(symbol, period, force_recalculate=True)

        # Check updated value
        updated_margin = var_data.get_variable(symbol, "net_margin", period=period)
        assert updated_margin == pytest.approx(0.3)  # 30000 / 100000


class TestThreadSafety:
    """Test thread-safety for concurrent variable updates."""

    def test_concurrent_variable_updates(self, var_data):
        """Test that concurrent updates from multiple threads work correctly."""
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "META"]
        period = "2023"
        num_threads = 5
        updates_per_thread = 10

        def update_variables(symbol):
            """Update variables for a symbol multiple times."""
            for i in range(updates_per_thread):
                revenue = 100000 + i * 1000
                net_income = 20000 + i * 500
                var_data.set_variable(symbol, "revenue", revenue, period=period, source="test")
                var_data.set_variable(symbol, "net_income", net_income, period=period, source="test")
                time.sleep(0.001)  # Small delay to encourage interleaving

        # Create and start threads
        threads = []
        for symbol in symbols:
            thread = threading.Thread(target=update_variables, args=(symbol,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all data is present and consistent
        for symbol in symbols:
            revenue = var_data.get_variable(symbol, "revenue", period=period)
            net_income = var_data.get_variable(symbol, "net_income", period=period)
            net_margin = var_data.get_variable(symbol, "net_margin", period=period)

            assert revenue is not None
            assert net_income is not None
            assert net_margin is not None
            assert net_margin == pytest.approx(net_income / revenue)


class TestConfigurationOptions:
    """Test configuration options for composite calculation."""

    def test_enable_disable_auto_calculation(self, var_data_no_auto_calc):
        """Test toggling auto-calculation on and off."""
        symbol = "NVDA"
        period = "2023"

        # Auto-calculation is disabled initially
        var_data_no_auto_calc.set_variable(symbol, "revenue", 50000, period=period, source="test")
        var_data_no_auto_calc.set_variable(symbol, "net_income", 15000, period=period, source="test")

        # No composite variables should be calculated
        net_margin_before = var_data_no_auto_calc.get_variable(symbol, "net_margin", period=period,
                                                               calculate_if_missing=False)
        assert net_margin_before is None

        # Enable auto-calculation
        var_data_no_auto_calc.set_auto_calculation(True)

        # Set another variable to trigger calculation
        var_data_no_auto_calc.set_variable(symbol, "total_assets", 100000, period=period, source="test")

        # Now composite variables should be available
        net_margin_after = var_data_no_auto_calc.get_variable(symbol, "net_margin", period=period)
        assert net_margin_after == pytest.approx(0.3)


class TestEventEmission:
    """Test event emission for composite variable changes."""

    def test_composite_variable_events(self, var_data):
        """Test that events are emitted when composite variables are calculated."""
        symbol = "TSLA"
        period = "2023"
        events_received = []

        def event_handler(event_type, **kwargs):
            """Collect events."""
            events_received.append({
                'event_type': event_type,
                'symbol': kwargs.get('symbol'),
                'variable_name': kwargs.get('variable_name'),
                'value': kwargs.get('value')
            })

        # Subscribe to events
        var_data.subscribe_to_events(DataChangeEvent.VARIABLE_SET, event_handler)

        # Set base variables
        var_data.set_variable(symbol, "revenue", 100000, period=period, source="test")
        var_data.set_variable(symbol, "net_income", 25000, period=period, source="test")

        # Check events
        # Should have events for both base variables AND composite variables
        assert len(events_received) > 2  # At least base + some composites

        # Check that composite variables are in the events
        variable_names = [e['variable_name'] for e in events_received]
        assert 'revenue' in variable_names
        assert 'net_income' in variable_names
        # At least one composite variable should be calculated
        composite_vars = {'net_margin', 'gross_profit', 'gross_margin'}
        assert any(var in variable_names for var in composite_vars)


class TestStatistics:
    """Test statistics tracking for composite calculations."""

    def test_composite_calculation_statistics(self, var_data):
        """Test that statistics track composite calculations."""
        symbol = "AAPL"
        period = "2023"

        # Get initial statistics
        stats_before = var_data.get_statistics()
        initial_calculations = stats_before['composite_calculation']['total_calculations']

        # Set variables to trigger calculation
        var_data.set_variable(symbol, "revenue", 394328, period=period, source="test")
        var_data.set_variable(symbol, "net_income", 99803, period=period, source="test")

        # Get updated statistics
        stats_after = var_data.get_statistics()

        # Should show composite calculations occurred
        assert stats_after['composite_calculation']['enabled'] is True
        assert stats_after['composite_calculation']['calculator_available'] is True
        assert stats_after['composite_calculation']['total_calculations'] > initial_calculations

        # Check calculator-specific statistics
        calc_stats = stats_after['composite_calculation']['calculator_stats']
        assert 'total_calculations' in calc_stats
        assert calc_stats['total_calculations'] > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_missing_dependencies(self, var_data):
        """Test behavior when some dependencies are missing."""
        symbol = "NFLX"
        period = "2023"

        # Set only one of the required base variables
        var_data.set_variable(symbol, "revenue", 100000, period=period, source="test")

        # Try to get a composite that requires missing dependencies
        net_margin = var_data.get_variable(symbol, "net_margin", period=period,
                                          calculate_if_missing=True)

        # Should return None since net_income is missing
        # The calculation should handle missing data gracefully without errors
        assert net_margin is None  # Missing net_income dependency

    def test_zero_division_handling(self, var_data):
        """Test that division by zero is handled gracefully."""
        symbol = "TEST"
        period = "2023"

        # Set revenue to zero
        var_data.set_variable(symbol, "revenue", 0, period=period, source="test")
        var_data.set_variable(symbol, "net_income", 10000, period=period, source="test")

        # Get margin (should handle division by zero)
        net_margin = var_data.get_variable(symbol, "net_margin", period=period)

        # Should return 0 or None, not raise an exception
        assert net_margin == 0 or net_margin is None

    def test_calculation_with_no_calculator(self, var_data_no_auto_calc):
        """Test behavior when calculator is not available."""
        symbol = "AMD"
        period = "2023"

        # Disable auto-calculation and ensure calculator is None
        var_data_no_auto_calc.set_auto_calculation(False)

        var_data_no_auto_calc.set_variable(symbol, "revenue", 100000, period=period, source="test")

        # Try to manually calculate without calculator
        results = var_data_no_auto_calc.calculate_composite_variables(symbol, period)

        # Should return empty dict
        assert results == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
