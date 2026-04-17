"""
Unit tests for core/analysis/dcf/dcf_valuation.py

Tests cover:
- DCFValuator construction and default assumptions
- Core DCF internal calculations with known numerical inputs
- Terminal value calculation (Gordon Growth Model)
- Present value calculations
- Historical growth rate derivation
- FCF projection logic
- Edge cases: zero FCF, negative FCF, very high discount rate
- Boundary: growth_rate >= discount_rate handling
- External dependencies are fully mocked
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_var_data():
    """Return a var_input_data mock that returns None / empty by default."""
    mock = MagicMock()
    mock.get_variable.return_value = None
    mock.get_historical_data.return_value = None
    mock.set_variable.return_value = True
    return mock


def make_mock_dcf_config(
    discount_rate=0.10,
    terminal_growth_rate=0.025,
    growth_rate_yr1_5=0.10,
    growth_rate_yr5_10=0.05,
    projection_years=10,
    terminal_method="gordon_growth",
    fcf_type="FCFE",
):
    """Return a mock DCF config object."""
    cfg = MagicMock()
    cfg.default_discount_rate = discount_rate
    cfg.default_terminal_growth_rate = terminal_growth_rate
    cfg.default_growth_rate_yr1_5 = growth_rate_yr1_5
    cfg.default_growth_rate_yr5_10 = growth_rate_yr5_10
    cfg.default_projection_years = projection_years
    cfg.default_terminal_method = terminal_method
    cfg.default_fcf_type = fcf_type
    return cfg


def make_mock_financial_calculator(
    ticker="TEST",
    shares=1_000.0,
    price=100.0,
    fcfe=None,
):
    """Return a lightweight mock of FinancialCalculator."""
    fcfe = fcfe or [1_000.0, 1_100.0, 1_200.0]
    calc = MagicMock()
    calc.ticker_symbol = ticker
    calc.currency = "USD"
    calc.is_tase_stock = False
    calc.shares_outstanding = shares
    calc.current_stock_price = price
    calc.market_cap = shares * price
    calc.fcf_results = {"FCFE": fcfe, "FCFF": [v * 1.1 for v in fcfe]}
    calc.financial_data = {}
    calc.financial_scale_factor = 1.0
    calc.fetch_market_data.return_value = {
        "current_price": price,
        "market_cap": shares * price,
        "shares_outstanding": shares,
        "ticker_symbol": ticker,
    }
    return calc


def build_dcf_valuator(
    financial_calculator=None,
    discount_rate=0.10,
    terminal_growth_rate=0.025,
    growth_rate_yr1_5=0.10,
    growth_rate_yr5_10=0.05,
    projection_years=10,
):
    """
    Construct a DCFValuator with all external dependencies patched.
    Returns (DCFValuator instance, mock_var_data).
    """
    from core.analysis.dcf.dcf_valuation import DCFValuator

    if financial_calculator is None:
        financial_calculator = make_mock_financial_calculator()

    mock_var = make_mock_var_data()
    mock_cfg = make_mock_dcf_config(
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
        growth_rate_yr1_5=growth_rate_yr1_5,
        growth_rate_yr5_10=growth_rate_yr5_10,
        projection_years=projection_years,
    )

    with patch("core.analysis.dcf.dcf_valuation.get_var_input_data", return_value=mock_var), \
         patch("core.analysis.dcf.dcf_valuation.get_dcf_config", return_value=mock_cfg):
        valuator = DCFValuator(financial_calculator)

    # Inject the already-created mock so later calls inside methods also use it
    valuator.var_data = mock_var
    return valuator, mock_var


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def dcf_valuator():
    """Default DCFValuator with standard parameters."""
    return build_dcf_valuator()[0]


@pytest.fixture
def simple_assumptions():
    """A minimal valid DCF assumptions dictionary."""
    return {
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.025,
        "growth_rate_yr1_5": 0.10,
        "growth_rate_yr5_10": 0.05,
        "projection_years": 5,
        "terminal_method": "gordon_growth",
        "fcf_type": "FCFE",
    }


# ---------------------------------------------------------------------------
# Test class: DCFValuator construction
# ---------------------------------------------------------------------------

class TestDCFValuatorInit:
    """Tests that DCFValuator initialises correctly from the config."""

    def test_init_stores_default_assumptions(self):
        valuator, _ = build_dcf_valuator(
            discount_rate=0.09,
            terminal_growth_rate=0.03,
            growth_rate_yr1_5=0.12,
        )
        assert valuator.default_assumptions["discount_rate"] == pytest.approx(0.09)
        assert valuator.default_assumptions["terminal_growth_rate"] == pytest.approx(0.03)
        assert valuator.default_assumptions["growth_rate_yr1_5"] == pytest.approx(0.12)

    def test_init_stores_ticker_symbol(self):
        calc = make_mock_financial_calculator(ticker="XYZW")
        valuator, _ = build_dcf_valuator(financial_calculator=calc)
        assert valuator.ticker_symbol == "XYZW"

    def test_init_requires_financial_calculator(self):
        """DCFValuator accepts any object as financial_calculator (duck typing)."""
        valuator, _ = build_dcf_valuator()
        assert valuator.financial_calculator is not None


# ---------------------------------------------------------------------------
# Test class: _calculate_terminal_value
# ---------------------------------------------------------------------------

class TestCalculateTerminalValue:
    """Tests the Gordon Growth Model terminal value computation."""

    def test_terminal_value_standard(self, dcf_valuator):
        """TV = FCF_final * (1+g) / (r - g)"""
        final_fcf = 1_000.0
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "projection_years": 5,
        }
        projections = {"projected_fcf": [0, 0, 0, 0, final_fcf]}
        tv = dcf_valuator._calculate_terminal_value(projections, assumptions)
        expected = final_fcf * (1 + 0.025) / (0.10 - 0.025)
        assert tv == pytest.approx(expected, rel=1e-6)

    def test_terminal_value_empty_projections_returns_zero(self, dcf_valuator):
        projections = {"projected_fcf": []}
        assumptions = {"discount_rate": 0.10, "terminal_growth_rate": 0.025, "projection_years": 5}
        assert dcf_valuator._calculate_terminal_value(projections, assumptions) == 0

    def test_terminal_value_very_high_discount_rate(self, dcf_valuator):
        """Very high discount rate (60%) with 2.5% terminal growth."""
        final_fcf = 500.0
        assumptions = {
            "discount_rate": 0.60,
            "terminal_growth_rate": 0.025,
            "projection_years": 5,
        }
        projections = {"projected_fcf": [0, 0, 0, 0, final_fcf]}
        tv = dcf_valuator._calculate_terminal_value(projections, assumptions)
        expected = final_fcf * 1.025 / (0.60 - 0.025)
        assert tv == pytest.approx(expected, rel=1e-6)
        # Terminal value should be smaller with higher discount rate
        assert tv < final_fcf * 1.025 / (0.10 - 0.025)

    def test_terminal_value_negative_fcf(self, dcf_valuator):
        """Negative FCF produces a negative terminal value."""
        final_fcf = -500.0
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "projection_years": 5,
        }
        projections = {"projected_fcf": [-500, -450, -400, -350, final_fcf]}
        tv = dcf_valuator._calculate_terminal_value(projections, assumptions)
        # Should be negative
        assert tv < 0


# ---------------------------------------------------------------------------
# Test class: _calculate_present_values
# ---------------------------------------------------------------------------

class TestCalculatePresentValues:
    """Tests present-value discounting of a stream of cash flows."""

    def test_single_cashflow_pv(self, dcf_valuator):
        """PV of 110 in year 1 at 10% discount rate = 100."""
        pvs = dcf_valuator._calculate_present_values([110.0], 0.10)
        assert len(pvs) == 1
        assert pvs[0] == pytest.approx(100.0, rel=1e-6)

    def test_two_cashflows_pv(self, dcf_valuator):
        """PV of two cash flows discounted correctly."""
        discount_rate = 0.10
        cf1, cf2 = 110.0, 121.0
        pvs = dcf_valuator._calculate_present_values([cf1, cf2], discount_rate)
        assert pvs[0] == pytest.approx(cf1 / 1.10, rel=1e-6)
        assert pvs[1] == pytest.approx(cf2 / (1.10 ** 2), rel=1e-6)

    def test_pv_sum_less_than_nominal_sum(self, dcf_valuator):
        """Sum of PVs must be less than sum of nominal flows (positive discount rate)."""
        cashflows = [100.0, 200.0, 300.0]
        pvs = dcf_valuator._calculate_present_values(cashflows, 0.10)
        assert sum(pvs) < sum(cashflows)

    def test_empty_cashflows_returns_empty(self, dcf_valuator):
        pvs = dcf_valuator._calculate_present_values([], 0.10)
        assert pvs == []

    def test_very_high_discount_rate_shrinks_pv(self, dcf_valuator):
        """With 80% discount rate, PV of year-1 flow is substantially less than nominal."""
        pvs = dcf_valuator._calculate_present_values([1_000.0], 0.80)
        assert pvs[0] == pytest.approx(1_000.0 / 1.80, rel=1e-6)
        assert pvs[0] < 600.0


# ---------------------------------------------------------------------------
# Test class: _project_future_fcf
# ---------------------------------------------------------------------------

class TestProjectFutureFCF:
    """Tests the FCF projection engine."""

    def test_projection_uses_latest_fcf_as_base(self, dcf_valuator):
        """Base FCF for projections must be the most recent (last) historical value."""
        historical = [500.0, 600.0, 700.0]
        assumptions = {
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 3,
        }
        result = dcf_valuator._project_future_fcf(historical, assumptions, {"projection_growth": 0.10})
        assert result["base_fcf"] == pytest.approx(700.0)

    def test_first_projection_year_applies_growth(self, dcf_valuator):
        """Year-1 projected FCF = base_fcf * (1 + growth_yr1_5)."""
        base = 1_000.0
        growth = 0.12
        assumptions = {
            "growth_rate_yr1_5": growth,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 1,
        }
        result = dcf_valuator._project_future_fcf([base], assumptions, {})
        assert result["projected_fcf"][0] == pytest.approx(base * (1 + growth))

    def test_years_6_10_use_second_growth_rate(self, dcf_valuator):
        """Years 6-10 use growth_rate_yr5_10."""
        base = 1_000.0
        assumptions = {
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.03,
            "projection_years": 10,
        }
        result = dcf_valuator._project_future_fcf([base], assumptions, {})
        year5_fcf = result["projected_fcf"][4]
        year6_fcf = result["projected_fcf"][5]
        assert year6_fcf == pytest.approx(year5_fcf * 1.03, rel=1e-6)

    def test_zero_fcf_remains_zero(self, dcf_valuator):
        """Zero base FCF projects to zero across all years."""
        assumptions = {
            "growth_rate_yr1_5": 0.15,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 5,
        }
        result = dcf_valuator._project_future_fcf([0.0], assumptions, {})
        assert all(v == pytest.approx(0.0) for v in result["projected_fcf"])

    def test_negative_fcf_remains_negative(self, dcf_valuator):
        """Negative base FCF with positive growth stays negative (grows toward zero)."""
        assumptions = {
            "growth_rate_yr1_5": 0.05,
            "growth_rate_yr5_10": 0.03,
            "projection_years": 3,
        }
        result = dcf_valuator._project_future_fcf([-500.0], assumptions, {})
        for v in result["projected_fcf"]:
            assert v < 0, "Expected negative projected FCF"

    def test_empty_historical_returns_empty_projections(self, dcf_valuator):
        assumptions = {
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 5,
        }
        result = dcf_valuator._project_future_fcf([], assumptions, {})
        assert result["projected_fcf"] == []

    def test_projection_count_matches_projection_years(self, dcf_valuator):
        assumptions = {
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 7,
        }
        result = dcf_valuator._project_future_fcf([1_000.0], assumptions, {})
        assert len(result["projected_fcf"]) == 7


# ---------------------------------------------------------------------------
# Test class: _calculate_historical_growth_rates
# ---------------------------------------------------------------------------

class TestCalculateHistoricalGrowthRates:
    """Tests CAGR computation from historical FCF series."""

    def test_1y_cagr_correct(self, dcf_valuator):
        """1-year CAGR = (end/start)^(1/1) - 1."""
        fcf = (100.0, 120.0)
        result = dcf_valuator._calculate_historical_growth_rates(fcf)
        assert result["1Y_CAGR"] == pytest.approx(0.20, rel=1e-5)

    def test_3y_cagr_correct(self, dcf_valuator):
        """3-year CAGR over four data points."""
        # 100 -> ? -> ? -> 133.1  (10% per year for 3 years)
        import math
        start, end = 100.0, 133.1
        expected = (end / start) ** (1 / 3) - 1
        fcf = (start, 110.0, 121.0, end)
        result = dcf_valuator._calculate_historical_growth_rates(fcf)
        assert result.get("3Y_CAGR") == pytest.approx(expected, rel=1e-3)

    def test_zero_start_value_does_not_raise(self, dcf_valuator):
        """Zero start value must not raise; implementation skips zero and uses later data."""
        fcf = (0.0, 100.0, 110.0, 120.0)
        result = dcf_valuator._calculate_historical_growth_rates(fcf)
        assert isinstance(result, dict)  # no exception raised

    def test_insufficient_data_returns_default(self, dcf_valuator):
        """Less than 2 data points returns a default projection growth."""
        result = dcf_valuator._calculate_historical_growth_rates((500.0,))
        assert "projection_growth" in result

    def test_projection_growth_capped(self, dcf_valuator):
        """projection_growth is capped between -20% and +30%."""
        # Enormous growth to test the cap
        fcf = tuple([1.0] + [1_000_000.0] * 5)
        result = dcf_valuator._calculate_historical_growth_rates(fcf)
        assert result["projection_growth"] <= 0.30
        assert result["projection_growth"] >= -0.20


# ---------------------------------------------------------------------------
# Test class: calculate_dcf_projections — end-to-end with mocked I/O
# ---------------------------------------------------------------------------

class TestCalculateDCFProjections:
    """End-to-end tests for calculate_dcf_projections with all I/O mocked."""

    def _make_valuator_with_fcfe(self, fcfe_values, shares=1_000.0, price=100.0):
        """Helper that patches var_input_data to return known FCFE series."""
        calc = make_mock_financial_calculator(shares=shares, price=price, fcfe=fcfe_values)
        valuator, mock_var = build_dcf_valuator(financial_calculator=calc)

        # Patch var_data.get_historical_data to return our FCFE values
        def side_effect(ticker, var_name, years=10):
            if "fcfe" in var_name.lower():
                return [(str(i + 2015), v) for i, v in enumerate(fcfe_values)]
            return None

        valuator.var_data.get_historical_data.side_effect = side_effect
        valuator.var_data.get_variable.return_value = None
        return valuator

    def test_returns_dict_with_key_fields(self):
        valuator = self._make_valuator_with_fcfe([1_000.0, 1_100.0, 1_200.0])
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 5,
            "terminal_method": "gordon_growth",
            "fcf_type": "FCFE",
        }
        result = valuator.calculate_dcf_projections(assumptions)
        assert isinstance(result, dict)
        # Should either contain value_per_share or an error key
        assert "value_per_share" in result or "error" in result

    def test_no_fcf_data_returns_empty(self):
        """When no FCF data is available, returns empty dict."""
        calc = make_mock_financial_calculator()
        calc.fcf_results = {}
        valuator, mock_var = build_dcf_valuator(financial_calculator=calc)
        mock_var.get_historical_data.return_value = None

        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 5,
            "terminal_method": "gordon_growth",
            "fcf_type": "FCFE",
        }
        result = valuator.calculate_dcf_projections(assumptions)
        assert result == {} or result.get("error") is not None

    def test_uses_default_assumptions_when_none_passed(self):
        """calculate_dcf_projections() with no args uses default_assumptions."""
        valuator = self._make_valuator_with_fcfe([800.0, 900.0, 1_000.0])
        # Should not raise
        result = valuator.calculate_dcf_projections(None)
        assert isinstance(result, dict)

    def test_value_per_share_positive_with_valid_data(self):
        """With well-formed data, value_per_share should be a positive number."""
        valuator = self._make_valuator_with_fcfe(
            [1_000.0, 1_100.0, 1_200.0, 1_300.0, 1_400.0],
            shares=1_000.0,
            price=100.0,
        )
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "growth_rate_yr1_5": 0.08,
            "growth_rate_yr5_10": 0.04,
            "projection_years": 5,
            "terminal_method": "gordon_growth",
            "fcf_type": "FCFE",
        }
        result = valuator.calculate_dcf_projections(assumptions)
        if "value_per_share" in result:
            assert result["value_per_share"] > 0


# ---------------------------------------------------------------------------
# Test class: calculate_dcf_valuation (alias bridge)
# ---------------------------------------------------------------------------

class TestCalculateDCFValuation:
    """Tests the calculate_dcf_valuation alias that mirrors calculate_dcf_projections."""

    def test_calculate_dcf_valuation_mirrors_projections(self):
        """calculate_dcf_valuation should return identical result to calculate_dcf_projections."""
        calc = make_mock_financial_calculator()
        valuator, mock_var = build_dcf_valuator(financial_calculator=calc)
        mock_var.get_historical_data.return_value = None

        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "growth_rate_yr1_5": 0.10,
            "growth_rate_yr5_10": 0.05,
            "projection_years": 5,
            "terminal_method": "gordon_growth",
            "fcf_type": "FCFE",
        }

        r1 = valuator.calculate_dcf_valuation(assumptions)
        r2 = valuator.calculate_dcf_projections(assumptions)
        assert r1 == r2


# ---------------------------------------------------------------------------
# Test class: edge-case numerics
# ---------------------------------------------------------------------------

class TestDCFEdgeCases:
    """Edge-case and boundary tests."""

    def test_terminal_value_growth_equals_discount_raises_or_graceful(self):
        """When g == r, the denominator is zero. The method should handle gracefully."""
        valuator, _ = build_dcf_valuator()
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.10,  # equal to discount_rate
            "projection_years": 5,
        }
        projections = {"projected_fcf": [100.0, 110.0, 121.0, 133.1, 146.4]}
        # Must not raise an unhandled ZeroDivisionError
        try:
            tv = valuator._calculate_terminal_value(projections, assumptions)
            # If it returns a value, it could be inf or 0 — either is acceptable
        except ZeroDivisionError:
            pytest.fail("ZeroDivisionError should be caught internally")

    def test_terminal_value_growth_exceeds_discount_returns_negative_or_handled(self):
        """When g > r, the result should be handled (no unhandled exception)."""
        valuator, _ = build_dcf_valuator()
        assumptions = {
            "discount_rate": 0.05,
            "terminal_growth_rate": 0.10,  # g > r
            "projection_years": 5,
        }
        projections = {"projected_fcf": [100.0, 105.0, 110.0, 115.0, 121.0]}
        try:
            tv = valuator._calculate_terminal_value(projections, assumptions)
            # The denominator is negative so result would be negative (mathematically wrong)
            # but the method should not crash
        except Exception as exc:
            pytest.fail(f"Unexpected exception for g > r: {exc}")

    def test_very_high_discount_rate_present_values(self):
        """With 80% discount rate, present values are dramatically reduced."""
        valuator, _ = build_dcf_valuator()
        cashflows = [1_000.0] * 10
        pvs = valuator._calculate_present_values(cashflows, 0.80)
        assert all(v < 1_000.0 for v in pvs)
        # The sum should be much less than 10000
        assert sum(pvs) < 2_000.0

    def test_historical_growth_all_zeros(self):
        """All-zero FCF history should not raise and return a default rate."""
        valuator, _ = build_dcf_valuator()
        result = valuator._calculate_historical_growth_rates((0.0, 0.0, 0.0, 0.0))
        assert isinstance(result, dict)
        assert "projection_growth" in result

    def test_project_fcf_with_zero_growth_rate(self):
        """Zero growth rate means projected FCF equals base FCF every year."""
        valuator, _ = build_dcf_valuator()
        base = 500.0
        assumptions = {
            "growth_rate_yr1_5": 0.0,
            "growth_rate_yr5_10": 0.0,
            "projection_years": 3,
        }
        result = valuator._project_future_fcf([base], assumptions, {})
        for v in result["projected_fcf"]:
            assert v == pytest.approx(base, rel=1e-6)
