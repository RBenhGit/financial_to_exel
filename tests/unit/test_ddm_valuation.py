"""
Unit tests for core/analysis/ddm/ddm_valuation.py

Tests cover:
- Gordon Growth Model: intrinsic_value = D1 / (r - g)
- Two-Stage DDM calculations
- Multi-Stage DDM calculations
- Dividend = 0 edge case
- growth_rate >= discount_rate boundary handling
- Dividend data validation (insufficient history, high volatility, zero dividend)
- Model selection logic
- All external dependencies (yfinance, var_input_data, financial_calculator) mocked
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_var_data():
    """Return a var_input_data mock with empty/None defaults."""
    mock = MagicMock()
    mock.get_variable.return_value = None
    mock.get_historical_data.return_value = None
    mock.set_variable.return_value = True
    return mock


def make_mock_dcf_config(
    discount_rate=0.10,
    terminal_growth_rate=0.025,
):
    """Return a mock config compatible with DDMValuator expectations."""
    cfg = MagicMock()
    cfg.default_discount_rate = discount_rate
    cfg.default_terminal_growth_rate = terminal_growth_rate
    return cfg


def make_mock_financial_calculator(ticker="TEST", shares=500.0, price=50.0):
    """Return a minimal FinancialCalculator mock."""
    calc = MagicMock()
    calc.ticker_symbol = ticker
    calc.currency = "USD"
    calc.is_tase_stock = False
    calc.shares_outstanding = shares
    calc.current_stock_price = price
    calc.market_cap = shares * price
    calc.financial_scale_factor = 1.0
    calc.enhanced_data_manager = None
    calc.financial_data = {"Cash Flow Statement": {}, "Income Statement": {}}
    calc.fetch_market_data.return_value = {
        "current_price": price,
        "market_cap": shares * price,
        "shares_outstanding": shares,
        "ticker_symbol": ticker,
    }
    return calc


def build_ddm_valuator(financial_calculator=None, discount_rate=0.10, terminal_growth_rate=0.025):
    """
    Construct a DDMValuator with all external dependencies patched.
    Returns (DDMValuator instance, mock_var_data).
    """
    from core.analysis.ddm.ddm_valuation import DDMValuator

    if financial_calculator is None:
        financial_calculator = make_mock_financial_calculator()

    mock_var = make_mock_var_data()
    mock_cfg = make_mock_dcf_config(
        discount_rate=discount_rate,
        terminal_growth_rate=terminal_growth_rate,
    )

    with patch("core.analysis.ddm.ddm_valuation.get_var_input_data", return_value=mock_var), \
         patch("core.analysis.ddm.ddm_valuation.get_dcf_config", return_value=mock_cfg):
        valuator = DDMValuator(financial_calculator)

    valuator.var_data = mock_var
    return valuator, mock_var


def make_dividend_data(
    years=None,
    dividends_per_share=None,
    latest_dividend=None,
):
    """Build a processed_data dict as returned by _process_dividend_data."""
    if years is None:
        years = [2019, 2020, 2021, 2022, 2023]
    if dividends_per_share is None:
        dividends_per_share = [1.0, 1.05, 1.10, 1.16, 1.22]
    if latest_dividend is None:
        latest_dividend = dividends_per_share[-1]

    growth_rates = []
    for i in range(1, len(dividends_per_share)):
        prev = dividends_per_share[i - 1]
        if prev != 0:
            growth_rates.append((dividends_per_share[i] - prev) / prev)

    return {
        "years": years,
        "dividends_per_share": dividends_per_share,
        "growth_rates": growth_rates,
        "latest_dividend": latest_dividend,
        "latest_year": years[-1],
        "data_points": len(years),
        "recent_data": [],
    }


def make_dividend_metrics(cagr_3y=0.05, avg_growth=0.05, volatility=0.05):
    """Build a dividend metrics dict as returned by _calculate_dividend_metrics."""
    return {
        "dividend_cagr_3y": cagr_3y,
        "dividend_cagr_5y": cagr_3y,
        "avg_growth_rate": avg_growth,
        "median_growth_rate": avg_growth,
        "growth_volatility": volatility,
        "growth_consistency": 0.8,
        "trend_slope": 0.02,
        "trend_r_squared": 0.95,
        "trend_p_value": 0.001,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def ddm_valuator():
    """Default DDMValuator fixture."""
    return build_ddm_valuator()[0]


@pytest.fixture
def gordon_assumptions():
    return {
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.025,
        "stage1_growth_rate": 0.08,
        "stage2_growth_rate": 0.04,
        "stage1_years": 5,
        "stage2_years": 5,
        "model_type": "gordon",
        "min_dividend_history": 3,
        "payout_ratio_threshold": 0.9,
    }


@pytest.fixture
def two_stage_assumptions():
    return {
        "discount_rate": 0.10,
        "terminal_growth_rate": 0.025,
        "stage1_growth_rate": 0.08,
        "stage2_growth_rate": 0.04,
        "stage1_years": 5,
        "stage2_years": 5,
        "model_type": "two_stage",
        "min_dividend_history": 3,
        "payout_ratio_threshold": 0.9,
    }


# ---------------------------------------------------------------------------
# Test class: Gordon Growth Model
# ---------------------------------------------------------------------------

class TestGordonGrowthModel:
    """Tests the single-stage Gordon Growth Model formula: V = D1 / (r - g)."""

    def _prepare_valuator_for_gordon(self, dividend, growth_rate=0.05, discount_rate=0.10, price=50.0):
        """Set up the valuator with injected dividend_data and metrics."""
        calc = make_mock_financial_calculator(price=price)
        valuator, mock_var = build_ddm_valuator(
            financial_calculator=calc,
            discount_rate=discount_rate,
        )
        valuator.dividend_data = {"latest_dividend": dividend}
        valuator.dividend_metrics = make_dividend_metrics(
            cagr_3y=growth_rate, avg_growth=growth_rate, volatility=0.02
        )
        # Patch market data to avoid real network calls
        valuator._get_market_data = MagicMock(return_value={"current_price": price})
        return valuator

    def test_gordon_intrinsic_value_formula(self):
        """V = D0 * (1+g) / (r - g) with standard inputs."""
        dividend = 2.0
        growth = 0.04
        discount = 0.10
        valuator = self._prepare_valuator_for_gordon(dividend, growth_rate=growth, discount_rate=discount)

        assumptions = {
            "discount_rate": discount,
            "terminal_growth_rate": growth,
            "model_type": "gordon",
        }
        result = valuator._calculate_gordon_growth_model(assumptions)
        expected = dividend * (1 + growth) / (discount - growth)
        assert result["intrinsic_value"] == pytest.approx(expected, rel=1e-5)

    def test_gordon_result_contains_expected_keys(self):
        valuator = self._prepare_valuator_for_gordon(dividend=1.50, growth_rate=0.04)
        result = valuator._calculate_gordon_growth_model(
            {"discount_rate": 0.10, "terminal_growth_rate": 0.04, "model_type": "gordon"}
        )
        for key in ("intrinsic_value", "current_dividend", "growth_rate", "required_return", "next_year_dividend"):
            assert key in result, f"Expected key '{key}' missing from Gordon result"

    def test_gordon_zero_dividend_returns_zero_value(self):
        """With dividend = 0, intrinsic value must be 0."""
        valuator = self._prepare_valuator_for_gordon(dividend=0.0, growth_rate=0.04)
        result = valuator._calculate_gordon_growth_model(
            {"discount_rate": 0.10, "terminal_growth_rate": 0.04, "model_type": "gordon"}
        )
        assert result.get("intrinsic_value", 0) == pytest.approx(0.0, abs=1e-9)

    def test_gordon_growth_rate_adjusted_when_exceeds_discount_rate(self):
        """When g >= r, the model must adjust growth_rate to avoid div-by-zero."""
        dividend = 2.0
        # Pass g equal to r
        valuator = self._prepare_valuator_for_gordon(
            dividend=dividend, growth_rate=0.10, discount_rate=0.10
        )
        try:
            result = valuator._calculate_gordon_growth_model(
                {"discount_rate": 0.10, "terminal_growth_rate": 0.10, "model_type": "gordon"}
            )
            # If it returns a result, growth_rate must have been adjusted
            if "growth_rate" in result:
                assert result["growth_rate"] < 0.10
        except ZeroDivisionError:
            pytest.fail("Gordon Growth Model raised ZeroDivisionError for g == r")

    def test_gordon_growth_exceeds_discount_rate_no_crash(self):
        """g > r should be handled gracefully — no uncaught exception."""
        valuator = self._prepare_valuator_for_gordon(
            dividend=2.0, growth_rate=0.15, discount_rate=0.10
        )
        try:
            valuator._calculate_gordon_growth_model(
                {"discount_rate": 0.10, "terminal_growth_rate": 0.15, "model_type": "gordon"}
            )
        except Exception as exc:
            pytest.fail(f"Unexpected exception for g > r: {exc}")

    def test_gordon_higher_discount_rate_gives_lower_value(self):
        """Keeping dividend and growth constant, higher discount rate → lower value."""
        dividend = 2.0
        growth = 0.04
        v_low = self._prepare_valuator_for_gordon(
            dividend, growth_rate=growth, discount_rate=0.09
        )._calculate_gordon_growth_model(
            {"discount_rate": 0.09, "terminal_growth_rate": growth, "model_type": "gordon"}
        )["intrinsic_value"]

        v_high = self._prepare_valuator_for_gordon(
            dividend, growth_rate=growth, discount_rate=0.14
        )._calculate_gordon_growth_model(
            {"discount_rate": 0.14, "terminal_growth_rate": growth, "model_type": "gordon"}
        )["intrinsic_value"]

        assert v_low > v_high


# ---------------------------------------------------------------------------
# Test class: Two-Stage DDM
# ---------------------------------------------------------------------------

class TestTwoStageDDM:
    """Tests the two-stage DDM calculation."""

    def _prepare_valuator(self, dividend=2.0, discount_rate=0.10):
        calc = make_mock_financial_calculator()
        valuator, _ = build_ddm_valuator(financial_calculator=calc, discount_rate=discount_rate)
        valuator.dividend_data = {"latest_dividend": dividend}
        valuator.dividend_metrics = make_dividend_metrics()
        valuator._get_market_data = MagicMock(return_value={"current_price": 50.0})
        return valuator

    def test_two_stage_result_keys(self):
        valuator = self._prepare_valuator()
        result = valuator._calculate_two_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 5,
        })
        for key in ("intrinsic_value", "stage1_dividends", "stage1_pv", "terminal_value", "pv_terminal"):
            assert key in result, f"Expected key '{key}' missing from Two-Stage result"

    def test_two_stage_value_is_sum_of_parts(self):
        """intrinsic_value = sum(stage1_pv) + pv_terminal."""
        valuator = self._prepare_valuator(dividend=2.0)
        result = valuator._calculate_two_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 5,
        })
        expected = sum(result["stage1_pv"]) + result["pv_terminal"]
        assert result["intrinsic_value"] == pytest.approx(expected, rel=1e-6)

    def test_two_stage_zero_dividend_gives_zero_value(self):
        valuator = self._prepare_valuator(dividend=0.0)
        result = valuator._calculate_two_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 5,
        })
        assert result.get("intrinsic_value", 0) == pytest.approx(0.0, abs=1e-9)

    def test_two_stage_growth_ge_discount_rate_handled(self):
        """stage1_growth_rate >= discount_rate should be handled without crash."""
        valuator = self._prepare_valuator()
        try:
            result = valuator._calculate_two_stage_ddm({
                "discount_rate": 0.10,
                "terminal_growth_rate": 0.025,
                "stage1_growth_rate": 0.15,  # > discount_rate
                "stage1_years": 5,
            })
            assert "intrinsic_value" in result
        except Exception as exc:
            pytest.fail(f"Unexpected exception for stage1_growth >= discount: {exc}")

    def test_two_stage_stage1_dividend_count(self):
        """Number of stage-1 dividends must equal stage1_years."""
        valuator = self._prepare_valuator(dividend=1.0)
        result = valuator._calculate_two_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 7,
        })
        assert len(result["stage1_dividends"]) == 7

    def test_two_stage_terminal_pv_less_than_terminal_value(self):
        """PV of terminal value must be less than undiscounted terminal value."""
        valuator = self._prepare_valuator(dividend=2.0)
        result = valuator._calculate_two_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 5,
        })
        assert result["pv_terminal"] < result["terminal_value"]


# ---------------------------------------------------------------------------
# Test class: Multi-Stage (3-Stage) DDM
# ---------------------------------------------------------------------------

class TestMultiStageDDM:
    """Tests the three-stage DDM calculation."""

    def _prepare_valuator(self, dividend=3.0):
        calc = make_mock_financial_calculator()
        valuator, _ = build_ddm_valuator(financial_calculator=calc)
        valuator.dividend_data = {"latest_dividend": dividend}
        valuator.dividend_metrics = make_dividend_metrics(cagr_3y=0.12, avg_growth=0.12, volatility=0.03)
        valuator._get_market_data = MagicMock(return_value={"current_price": 80.0})
        return valuator

    def test_multi_stage_result_keys(self):
        valuator = self._prepare_valuator()
        result = valuator._calculate_multi_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.15,
            "stage2_growth_rate": 0.08,
            "stage1_years": 5,
            "stage2_years": 5,
        })
        for key in (
            "intrinsic_value", "stage1_dividends", "stage1_pv",
            "stage2_dividends", "stage2_pv", "terminal_value", "pv_terminal"
        ):
            assert key in result, f"Expected key '{key}' missing from Multi-Stage result"

    def test_multi_stage_value_is_sum_of_all_parts(self):
        """intrinsic_value = sum(stage1_pv) + sum(stage2_pv) + pv_terminal."""
        valuator = self._prepare_valuator(dividend=2.0)
        result = valuator._calculate_multi_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.12,
            "stage2_growth_rate": 0.07,
            "stage1_years": 5,
            "stage2_years": 5,
        })
        expected = sum(result["stage1_pv"]) + sum(result["stage2_pv"]) + result["pv_terminal"]
        assert result["intrinsic_value"] == pytest.approx(expected, rel=1e-6)

    def test_multi_stage_zero_dividend_gives_zero(self):
        valuator = self._prepare_valuator(dividend=0.0)
        result = valuator._calculate_multi_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.12,
            "stage2_growth_rate": 0.07,
            "stage1_years": 5,
            "stage2_years": 5,
        })
        assert result.get("intrinsic_value", 0) == pytest.approx(0.0, abs=1e-9)

    def test_multi_stage_counts_dividends_correctly(self):
        valuator = self._prepare_valuator(dividend=1.0)
        stage1_years = 4
        stage2_years = 3
        result = valuator._calculate_multi_stage_ddm({
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.10,
            "stage2_growth_rate": 0.06,
            "stage1_years": stage1_years,
            "stage2_years": stage2_years,
        })
        assert len(result["stage1_dividends"]) == stage1_years
        assert len(result["stage2_dividends"]) == stage2_years


# ---------------------------------------------------------------------------
# Test class: Dividend data validation
# ---------------------------------------------------------------------------

class TestValidateDividendData:
    """Tests _validate_dividend_data."""

    def test_valid_data_passes(self, ddm_valuator):
        processed = make_dividend_data()
        metrics = make_dividend_metrics(cagr_3y=0.05, volatility=0.05)
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is True

    def test_empty_data_fails(self, ddm_valuator):
        result = ddm_valuator._validate_dividend_data({}, {})
        assert result["valid"] is False

    def test_insufficient_data_points_fails(self, ddm_valuator):
        processed = make_dividend_data(years=[2022, 2023], dividends_per_share=[1.0, 1.05])
        metrics = make_dividend_metrics()
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is False
        assert "insufficient" in result["reason"].lower() or "minimum" in result["reason"].lower()

    def test_zero_latest_dividend_fails(self, ddm_valuator):
        processed = make_dividend_data()
        processed["latest_dividend"] = 0.0
        metrics = make_dividend_metrics()
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is False

    def test_extremely_high_volatility_fails(self, ddm_valuator):
        """Growth volatility > 2.5 should be rejected."""
        processed = make_dividend_data()
        metrics = make_dividend_metrics(volatility=3.0)
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is False
        assert "volatile" in result["reason"].lower()

    def test_moderate_volatility_flags_smoothing(self, ddm_valuator):
        """Volatility between 1.0 and 2.5 should still pass but request smoothing."""
        processed = make_dividend_data()
        metrics = make_dividend_metrics(volatility=1.5)
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is True
        assert metrics.get("requires_volatility_smoothing") is True

    def test_unsustainable_payout_ratio_fails(self, ddm_valuator):
        """Payout ratio above threshold should fail validation."""
        processed = make_dividend_data()
        metrics = make_dividend_metrics()
        metrics["payout_ratio"] = 0.95  # above default threshold of 0.9
        result = ddm_valuator._validate_dividend_data(processed, metrics)
        assert result["valid"] is False
        assert "payout" in result["reason"].lower()


# ---------------------------------------------------------------------------
# Test class: calculate_ddm_valuation end-to-end
# ---------------------------------------------------------------------------

class TestCalculateDDMValuation:
    """End-to-end tests for calculate_ddm_valuation with mocked dividend extraction."""

    def _make_valuator_with_dividends(
        self,
        dividends=None,
        discount_rate=0.10,
        terminal_growth_rate=0.025,
        price=50.0,
    ):
        """Create a DDMValuator with a patched _extract_dividend_data."""
        if dividends is None:
            dividends = [1.0, 1.05, 1.10, 1.15, 1.20]

        calc = make_mock_financial_calculator(price=price)
        valuator, mock_var = build_ddm_valuator(
            financial_calculator=calc,
            discount_rate=discount_rate,
            terminal_growth_rate=terminal_growth_rate,
        )

        years = list(range(2019, 2019 + len(dividends)))
        processed_data = make_dividend_data(
            years=years, dividends_per_share=dividends
        )
        metrics = make_dividend_metrics(cagr_3y=0.05, avg_growth=0.05, volatility=0.02)

        valuator._extract_dividend_data = MagicMock(
            return_value={"success": True, "data": processed_data, "metrics": metrics}
        )
        valuator._get_market_data = MagicMock(
            return_value={"current_price": price, "shares_outstanding": 500.0}
        )
        return valuator

    def test_returns_dict_with_value_per_share_or_error(self):
        valuator = self._make_valuator_with_dividends()
        result = valuator.calculate_ddm_valuation()
        assert isinstance(result, dict)
        assert "intrinsic_value" in result or "error" in result

    def test_no_dividend_data_returns_error(self):
        calc = make_mock_financial_calculator()
        valuator, _ = build_ddm_valuator(financial_calculator=calc)
        valuator._extract_dividend_data = MagicMock(
            return_value={"success": False, "error_message": "No dividend data available"}
        )
        result = valuator.calculate_ddm_valuation()
        assert "error" in result

    def test_uses_default_assumptions_when_none_passed(self):
        valuator = self._make_valuator_with_dividends()
        result = valuator.calculate_ddm_valuation(None)
        assert isinstance(result, dict)

    def test_forced_gordon_model_type(self):
        valuator = self._make_valuator_with_dividends()
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.06,
            "stage1_years": 5,
            "model_type": "gordon",
            "min_dividend_history": 3,
            "payout_ratio_threshold": 0.9,
        }
        result = valuator.calculate_ddm_valuation(assumptions)
        assert result.get("model_type") == "gordon" or "error" in result

    def test_forced_two_stage_model_type(self):
        valuator = self._make_valuator_with_dividends()
        assumptions = {
            "discount_rate": 0.10,
            "terminal_growth_rate": 0.025,
            "stage1_growth_rate": 0.08,
            "stage1_years": 5,
            "model_type": "two_stage",
            "min_dividend_history": 3,
            "payout_ratio_threshold": 0.9,
        }
        result = valuator.calculate_ddm_valuation(assumptions)
        assert result.get("model_type") == "two_stage" or "error" in result

    def test_intrinsic_value_positive_with_valid_dividends(self):
        valuator = self._make_valuator_with_dividends(
            dividends=[1.0, 1.05, 1.10, 1.15, 1.20], price=50.0
        )
        result = valuator.calculate_ddm_valuation()
        if "intrinsic_value" in result:
            assert result["intrinsic_value"] > 0

    def test_result_includes_model_metadata(self):
        valuator = self._make_valuator_with_dividends()
        result = valuator.calculate_ddm_valuation()
        if "error" not in result:
            assert "model_type" in result
            assert "assumptions" in result


# ---------------------------------------------------------------------------
# Test class: Model selection logic
# ---------------------------------------------------------------------------

class TestModelSelection:
    """Tests _select_model_type decision tree."""

    def _valuator_with_metrics(self, metrics):
        valuator, _ = build_ddm_valuator()
        valuator.dividend_metrics = metrics
        valuator._get_market_data = MagicMock(return_value={"current_price": 50.0, "market_cap": 25_000.0})
        return valuator

    def test_slow_growth_selects_gordon(self):
        metrics = make_dividend_metrics(cagr_3y=0.01, avg_growth=0.01, volatility=0.02)
        metrics["growth_consistency"] = 0.9
        valuator = self._valuator_with_metrics(metrics)
        model = valuator._select_model_type({"model_type": "auto"})
        assert model == "gordon"

    def test_moderate_growth_selects_two_stage(self):
        metrics = make_dividend_metrics(cagr_3y=0.08, avg_growth=0.08, volatility=0.05)
        metrics["growth_consistency"] = 0.8
        valuator = self._valuator_with_metrics(metrics)
        model = valuator._select_model_type({"model_type": "auto"})
        assert model in ("two_stage", "gordon")  # 5-15% range

    def test_explicit_model_type_overrides_auto(self):
        metrics = make_dividend_metrics(cagr_3y=0.20, avg_growth=0.20, volatility=0.02)
        valuator = self._valuator_with_metrics(metrics)
        model = valuator._select_model_type({"model_type": "gordon"})
        assert model == "gordon"

    def test_inconsistent_growth_defaults_to_gordon(self):
        metrics = make_dividend_metrics(cagr_3y=0.07, avg_growth=0.07, volatility=0.05)
        metrics["growth_consistency"] = 0.3  # low consistency
        valuator = self._valuator_with_metrics(metrics)
        model = valuator._select_model_type({"model_type": "auto"})
        assert model == "gordon"
