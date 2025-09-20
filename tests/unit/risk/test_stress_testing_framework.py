"""
Comprehensive Tests for Stress Testing Framework
===============================================

Tests for the stress testing framework including historical scenarios,
hypothetical stress tests, regime-switching models, and extreme value analysis.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import warnings

# Import the stress testing framework
from core.analysis.risk.stress_testing_framework import (
    StressTestingFramework,
    HistoricalStressScenarios,
    HypotheticalStressScenarios,
    ExtreemeValueAnalyzer,
    RegimeSwitchingAnalyzer,
    StressScenarioType,
    MarketRegime,
    ScenarioSeverity,
    run_quick_stress_test
)
from core.analysis.risk.scenario_modeling import ScenarioType


class TestHistoricalStressScenarios:
    """Test historical stress scenarios definitions."""

    def test_financial_crisis_2008_scenario(self):
        """Test 2008 financial crisis scenario definition."""
        scenario = HistoricalStressScenarios.financial_crisis_2008()

        assert scenario.name == "Financial Crisis 2008"
        assert scenario.scenario_type == StressScenarioType.HISTORICAL_CRISIS
        assert scenario.severity == ScenarioSeverity.EXTREME
        assert scenario.equity_shock == -0.37
        assert scenario.bond_shock == 0.20
        assert scenario.volatility_multiplier == 2.5
        assert scenario.duration_months == 18
        assert scenario.recovery_months == 36
        assert scenario.historical_precedent == "Sep 2008 - Mar 2009"

    def test_covid19_pandemic_scenario(self):
        """Test COVID-19 pandemic scenario definition."""
        scenario = HistoricalStressScenarios.covid19_pandemic()

        assert scenario.name == "COVID-19 Pandemic"
        assert scenario.scenario_type == StressScenarioType.HISTORICAL_CRISIS
        assert scenario.severity == ScenarioSeverity.SEVERE
        assert scenario.equity_shock == -0.34
        assert scenario.volatility_multiplier == 3.0
        assert scenario.correlation_shift == 0.4
        assert scenario.duration_months == 3
        assert scenario.recovery_months == 18

    def test_dotcom_crash_scenario(self):
        """Test dot-com crash scenario definition."""
        scenario = HistoricalStressScenarios.dotcom_crash()

        assert scenario.name == "Dot-com Crash"
        assert scenario.equity_shock == -0.49  # NASDAQ decline
        assert scenario.duration_months == 30
        assert scenario.recovery_months == 60

    def test_black_monday_1987_scenario(self):
        """Test Black Monday 1987 scenario definition."""
        scenario = HistoricalStressScenarios.black_monday_1987()

        assert scenario.name == "Black Monday 1987"
        assert scenario.equity_shock == -0.22
        assert scenario.volatility_multiplier == 5.0
        assert scenario.duration_months == 1
        assert scenario.liquidity_shock == -0.6


class TestHypotheticalStressScenarios:
    """Test hypothetical stress scenarios definitions."""

    def test_extreme_inflation_scenario(self):
        """Test extreme inflation scenario definition."""
        scenario = HypotheticalStressScenarios.extreme_inflation()

        assert scenario.name == "Extreme Inflation Shock"
        assert scenario.scenario_type == StressScenarioType.HYPOTHETICAL_EXTREME
        assert scenario.equity_shock == -0.25
        assert scenario.bond_shock == -0.40  # Bonds hurt by inflation
        assert scenario.inflation_shock == 0.08
        assert scenario.interest_rate_shock == 0.06

    def test_geopolitical_crisis_scenario(self):
        """Test geopolitical crisis scenario definition."""
        scenario = HypotheticalStressScenarios.geopolitical_crisis()

        assert scenario.name == "Geopolitical Crisis"
        assert scenario.equity_shock == -0.30
        assert scenario.commodity_shock == 0.50
        assert scenario.fx_shock == -0.15
        assert scenario.duration_months == 6

    def test_cyber_attack_scenario(self):
        """Test cyber attack scenario definition."""
        scenario = HypotheticalStressScenarios.cyber_attack()

        assert scenario.name == "Systemic Cyber Attack"
        assert scenario.liquidity_shock == -0.8
        assert scenario.volatility_multiplier == 4.0
        assert scenario.correlation_shift == 0.6


class TestExtreemeValueAnalyzer:
    """Test extreme value analysis functionality."""

    @pytest.fixture
    def sample_returns(self):
        """Generate sample returns data for testing."""
        np.random.seed(42)

        # Generate returns with some extreme values
        normal_returns = np.random.normal(0.001, 0.02, 1000)  # Daily returns

        # Add some extreme events
        extreme_indices = np.random.choice(1000, 20, replace=False)
        for idx in extreme_indices:
            if np.random.rand() > 0.5:
                normal_returns[idx] = -0.08  # -8% extreme loss
            else:
                normal_returns[idx] = 0.06   # 6% extreme gain

        dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
        return pd.Series(normal_returns, index=dates, name='returns')

    @pytest.fixture
    def evt_analyzer(self):
        """Create EVT analyzer instance."""
        return ExtreemeValueAnalyzer(confidence_levels=[0.95, 0.99, 0.995])

    def test_evt_analyzer_initialization(self, evt_analyzer):
        """Test EVT analyzer initialization."""
        assert len(evt_analyzer.confidence_levels) == 3
        assert 0.99 in evt_analyzer.confidence_levels

    def test_tail_risk_analysis_basic(self, evt_analyzer, sample_returns):
        """Test basic tail risk analysis."""
        result = evt_analyzer.analyze_tail_risk(sample_returns)

        # Check that we get meaningful results
        assert result.threshold > 0
        assert result.extreme_event_probability > 0
        assert result.extreme_event_probability < 1
        assert result.tail_index > 0
        assert len(result.tail_var_estimates) > 0
        assert len(result.tail_cvar_estimates) > 0

        # Check that VaR estimates make sense
        assert 'VaR_0.99' in result.tail_var_estimates
        assert result.tail_var_estimates['VaR_0.99'] > 0

    def test_tail_risk_analysis_insufficient_data(self, evt_analyzer):
        """Test tail risk analysis with insufficient data."""
        short_returns = pd.Series(np.random.normal(0, 0.01, 50))

        with pytest.raises(ValueError, match="Insufficient data"):
            evt_analyzer.analyze_tail_risk(short_returns)

    def test_gpd_fitting(self, evt_analyzer):
        """Test Generalized Pareto Distribution fitting."""
        # Generate sample excess values
        np.random.seed(42)
        excess_values = np.random.exponential(0.02, 100)  # Exponential distribution

        params = evt_analyzer._fit_gpd(excess_values)

        assert 'shape' in params
        assert 'scale' in params
        assert 'method' in params
        assert params['scale'] > 0

    def test_gumbel_fitting(self, evt_analyzer, sample_returns):
        """Test Gumbel distribution fitting to block maxima."""
        loc, scale = evt_analyzer._fit_gumbel_block_maxima(sample_returns)

        assert isinstance(loc, float)
        assert isinstance(scale, float)
        assert scale > 0

    def test_hill_estimator(self, evt_analyzer, sample_returns):
        """Test Hill estimator calculation."""
        tail_index = evt_analyzer._calculate_hill_estimator(sample_returns, 50)

        assert isinstance(tail_index, float)
        assert 0.1 <= tail_index <= 5.0  # Reasonable bounds


class TestRegimeSwitchingAnalyzer:
    """Test regime-switching analysis functionality."""

    @pytest.fixture
    def sample_returns_with_regimes(self):
        """Generate returns data with different regimes."""
        np.random.seed(42)

        # Bull market regime (low vol, positive returns)
        bull_returns = np.random.normal(0.0008, 0.01, 300)

        # Bear market regime (high vol, negative returns)
        bear_returns = np.random.normal(-0.002, 0.03, 200)

        # High volatility regime (neutral returns, high vol)
        high_vol_returns = np.random.normal(0.0001, 0.04, 200)

        all_returns = np.concatenate([bull_returns, bear_returns, high_vol_returns])
        dates = pd.date_range(start='2020-01-01', periods=700, freq='D')

        return pd.Series(all_returns, index=dates, name='returns')

    @pytest.fixture
    def regime_analyzer(self):
        """Create regime-switching analyzer instance."""
        return RegimeSwitchingAnalyzer(n_regimes=3)

    def test_regime_analyzer_initialization(self, regime_analyzer):
        """Test regime analyzer initialization."""
        assert regime_analyzer.n_regimes == 3

    def test_regime_model_fitting(self, regime_analyzer, sample_returns_with_regimes):
        """Test regime-switching model fitting."""
        model = regime_analyzer.fit_regime_model(sample_returns_with_regimes)

        # Check model structure
        assert len(model.regimes) == 3
        assert model.transition_matrix.shape == (3, 3)
        assert len(model.regime_parameters) == 3
        assert model.current_regime in model.regimes

        # Check transition matrix properties
        # Each row should sum to 1 (probabilities)
        for i in range(3):
            assert abs(model.transition_matrix[i, :].sum() - 1.0) < 1e-6

        # Check regime parameters
        for regime, params in model.regime_parameters.items():
            assert 'mean' in params
            assert 'std' in params
            assert 'duration' in params
            assert params['std'] > 0

    def test_transition_matrix_calculation(self, regime_analyzer):
        """Test transition matrix calculation."""
        # Simple test with known regime sequence
        regimes = [
            MarketRegime.BULL_MARKET, MarketRegime.BULL_MARKET,
            MarketRegime.BEAR_MARKET, MarketRegime.BEAR_MARKET,
            MarketRegime.BULL_MARKET
        ]

        transition_matrix = regime_analyzer._calculate_transition_matrix(regimes)

        # Check dimensions
        assert transition_matrix.shape[0] == transition_matrix.shape[1]

        # Check that rows sum to 1
        for i in range(transition_matrix.shape[0]):
            assert abs(transition_matrix[i, :].sum() - 1.0) < 1e-6

    def test_regime_parameters_calculation(self, regime_analyzer, sample_returns_with_regimes):
        """Test regime parameters calculation."""
        # Create simple regime classification
        n_obs = len(sample_returns_with_regimes)
        regimes = [MarketRegime.BULL_MARKET] * (n_obs // 2) + [MarketRegime.BEAR_MARKET] * (n_obs - n_obs // 2)

        params = regime_analyzer._calculate_regime_parameters(sample_returns_with_regimes, regimes)

        assert MarketRegime.BULL_MARKET in params
        assert MarketRegime.BEAR_MARKET in params

        for regime_params in params.values():
            assert 'mean' in regime_params
            assert 'std' in regime_params
            assert regime_params['std'] > 0


class TestStressTestingFramework:
    """Test the main stress testing framework."""

    @pytest.fixture
    def sample_portfolio_data(self):
        """Sample portfolio data for testing."""
        return {
            'equity_weight': 0.6,
            'bond_weight': 0.3,
            'cash_weight': 0.1,
            'base_volatility': 0.15,
            'holdings': [
                {'asset_id': 'AAPL', 'weight': 0.2, 'asset_type': 'equity'},
                {'asset_id': 'MSFT', 'weight': 0.2, 'asset_type': 'equity'},
                {'asset_id': 'BND', 'weight': 0.3, 'asset_type': 'bond'},
                {'asset_id': 'CASH', 'weight': 0.3, 'asset_type': 'cash'}
            ]
        }

    @pytest.fixture
    def sample_returns(self):
        """Generate sample returns for testing."""
        np.random.seed(42)
        returns = np.random.normal(0.0005, 0.015, 500)  # Daily returns
        dates = pd.date_range(start='2022-01-01', periods=500, freq='D')
        return pd.Series(returns, index=dates, name='returns')

    @pytest.fixture
    def mock_financial_calculator(self):
        """Mock financial calculator for testing."""
        calc = Mock()
        calc.get_financial_data = Mock(return_value={'price': 100})
        return calc

    @pytest.fixture
    def stress_framework(self, mock_financial_calculator):
        """Create stress testing framework instance."""
        return StressTestingFramework(financial_calculator=mock_financial_calculator)

    def test_framework_initialization(self, stress_framework):
        """Test stress testing framework initialization."""
        assert stress_framework.financial_calculator is not None
        assert stress_framework.monte_carlo_engine is not None
        assert stress_framework.evt_analyzer is not None
        assert stress_framework.regime_analyzer is not None
        assert len(stress_framework.historical_scenarios) > 0
        assert len(stress_framework.hypothetical_scenarios) > 0

    def test_scenario_loading(self, stress_framework):
        """Test that scenarios are loaded correctly."""
        # Check historical scenarios
        assert "financial_crisis_2008" in stress_framework.historical_scenarios
        assert "covid19_pandemic" in stress_framework.historical_scenarios
        assert "dotcom_crash" in stress_framework.historical_scenarios
        assert "black_monday_1987" in stress_framework.historical_scenarios

        # Check hypothetical scenarios
        assert "extreme_inflation" in stress_framework.hypothetical_scenarios
        assert "geopolitical_crisis" in stress_framework.hypothetical_scenarios
        assert "cyber_attack" in stress_framework.hypothetical_scenarios

    def test_single_stress_test(self, stress_framework, sample_portfolio_data, sample_returns):
        """Test running a single stress test."""
        scenario = stress_framework.historical_scenarios["financial_crisis_2008"]

        result = stress_framework._run_single_stress_test(
            scenario, sample_portfolio_data, sample_returns
        )

        # Check result structure
        assert result.scenario_name == "Financial Crisis 2008"
        assert result.scenario_definition == scenario
        assert result.portfolio_value_impact != 0  # Should have some impact
        assert result.max_drawdown > 0
        assert result.time_to_recovery is not None
        assert len(result.var_change) > 0
        assert result.calculation_time is not None

    def test_portfolio_impact_calculation(self, stress_framework, sample_portfolio_data):
        """Test portfolio impact calculation."""
        scenario = stress_framework.historical_scenarios["financial_crisis_2008"]

        impact = stress_framework._calculate_portfolio_impact(scenario, sample_portfolio_data)

        assert 'value_change' in impact
        assert 'asset_impacts' in impact
        assert 'sector_impacts' in impact

        # Impact should be negative for crisis scenario
        assert impact['value_change'] < 0

        # Check asset-level impacts
        assert 'AAPL' in impact['asset_impacts']
        assert 'MSFT' in impact['asset_impacts']

    def test_risk_metric_changes(self, stress_framework, sample_returns):
        """Test risk metric changes calculation."""
        scenario = stress_framework.historical_scenarios["covid19_pandemic"]

        changes = stress_framework._calculate_risk_metric_changes(scenario, sample_returns)

        assert 'var_change' in changes
        assert 'cvar_change' in changes
        assert 'volatility_change' in changes
        assert 'correlation_change' in changes

        # Volatility should increase in stress scenario
        assert changes['volatility_change'] > 0

    def test_comprehensive_stress_test(self, stress_framework, sample_portfolio_data, sample_returns):
        """Test comprehensive stress testing."""
        # Test with limited scenarios for speed
        scenarios = ["financial_crisis_2008", "covid19_pandemic"]

        results = stress_framework.run_comprehensive_stress_test(
            portfolio_data=sample_portfolio_data,
            asset_returns=sample_returns,
            scenarios=scenarios,
            include_tail_analysis=True,
            include_regime_analysis=True
        )

        # Check that we got results for all requested scenarios
        assert len(results) >= len(scenarios)  # May include tail and regime analysis

        for scenario_name in scenarios:
            assert scenario_name in results
            result = results[scenario_name]
            assert result.scenario_name is not None
            assert result.portfolio_value_impact is not None

        # Check tail analysis if included
        if "tail_risk_analysis" in results:
            tail_result = results["tail_risk_analysis"]
            assert "Tail Risk" in tail_result.scenario_name

    def test_scenario_summary(self, stress_framework):
        """Test scenario summary generation."""
        summary_df = stress_framework.get_scenario_summary()

        assert isinstance(summary_df, pd.DataFrame)
        assert len(summary_df) > 0
        assert 'Scenario' in summary_df.columns
        assert 'Type' in summary_df.columns
        assert 'Severity' in summary_df.columns
        assert 'Equity Shock' in summary_df.columns

    def test_stress_test_report_generation(self, stress_framework):
        """Test stress test report generation."""
        # Create mock results
        from core.analysis.risk.stress_testing_framework import StressTestResult, StressScenarioDefinition

        scenario_def = stress_framework.historical_scenarios["financial_crisis_2008"]
        mock_result = StressTestResult(
            scenario_name="Test Scenario",
            scenario_definition=scenario_def,
            portfolio_value_impact=-0.25,
            max_drawdown=0.30,
            time_to_recovery=18
        )

        results = {"test_scenario": mock_result}

        report = stress_framework.generate_stress_test_report(results)

        assert 'executive_summary' in report
        assert 'scenario_results' in report
        assert 'risk_ranking' in report
        assert 'recommendations' in report

        # Check executive summary
        exec_summary = report['executive_summary']
        assert exec_summary['total_scenarios'] == 1
        assert exec_summary['worst_case_scenario'] == "test_scenario"
        assert exec_summary['maximum_loss'] == 0.25

    def test_confidence_interval_calculation(self, stress_framework, sample_returns):
        """Test confidence interval calculation."""
        scenario = stress_framework.historical_scenarios["financial_crisis_2008"]

        ci = stress_framework._calculate_confidence_interval(scenario, sample_returns)

        assert isinstance(ci, tuple)
        assert len(ci) == 2
        assert ci[0] <= ci[1]  # Lower bound <= Upper bound

    def test_max_drawdown_estimation(self, stress_framework):
        """Test maximum drawdown estimation."""
        scenario = stress_framework.historical_scenarios["financial_crisis_2008"]

        max_dd = stress_framework._estimate_max_drawdown(scenario)

        assert isinstance(max_dd, float)
        assert 0 <= max_dd <= 0.8  # Should be between 0 and 80%

    def test_recovery_time_estimation(self, stress_framework):
        """Test recovery time estimation."""
        scenario = stress_framework.historical_scenarios["covid19_pandemic"]

        recovery_time = stress_framework._estimate_recovery_time(scenario)

        assert isinstance(recovery_time, int)
        assert recovery_time > 0


class TestStressTestIntegration:
    """Integration tests for stress testing framework."""

    @pytest.fixture
    def real_market_data(self):
        """Generate realistic market data for integration testing."""
        np.random.seed(42)

        # Generate more realistic return patterns
        n_days = 1000
        base_return = 0.0008  # 0.08% daily return (20% annual)
        base_vol = 0.015      # 1.5% daily volatility (24% annual)

        # Add regime changes
        returns = []
        for i in range(n_days):
            if 200 <= i < 250:  # Crisis period
                daily_return = np.random.normal(-0.003, 0.035)  # High vol, negative returns
            elif 600 <= i < 650:  # Another stress period
                daily_return = np.random.normal(-0.002, 0.025)
            else:  # Normal periods
                daily_return = np.random.normal(base_return, base_vol)
            returns.append(daily_return)

        dates = pd.date_range(start='2021-01-01', periods=n_days, freq='D')
        return pd.Series(returns, index=dates, name='market_returns')

    @pytest.fixture
    def complex_portfolio(self):
        """Create a more complex portfolio for testing."""
        return {
            'equity_weight': 0.7,
            'bond_weight': 0.2,
            'cash_weight': 0.05,
            'alternatives_weight': 0.05,
            'holdings': [
                {'asset_id': 'AAPL', 'weight': 0.15, 'asset_type': 'equity', 'sector': 'technology'},
                {'asset_id': 'MSFT', 'weight': 0.15, 'asset_type': 'equity', 'sector': 'technology'},
                {'asset_id': 'JPM', 'weight': 0.10, 'asset_type': 'equity', 'sector': 'financial'},
                {'asset_id': 'JNJ', 'weight': 0.10, 'asset_type': 'equity', 'sector': 'healthcare'},
                {'asset_id': 'XOM', 'weight': 0.10, 'asset_type': 'equity', 'sector': 'energy'},
                {'asset_id': 'PG', 'weight': 0.10, 'asset_type': 'equity', 'sector': 'consumer_staples'},
                {'asset_id': 'BND', 'weight': 0.20, 'asset_type': 'bond'},
                {'asset_id': 'CASH', 'weight': 0.05, 'asset_type': 'cash'},
                {'asset_id': 'REIT', 'weight': 0.05, 'asset_type': 'alternatives'}
            ]
        }

    def test_full_stress_testing_workflow(self, complex_portfolio, real_market_data):
        """Test complete stress testing workflow with realistic data."""
        framework = StressTestingFramework()

        # Run comprehensive stress test
        results = framework.run_comprehensive_stress_test(
            portfolio_data=complex_portfolio,
            asset_returns=real_market_data,
            scenarios=None,  # Test all scenarios
            include_tail_analysis=True,
            include_regime_analysis=True
        )

        # Verify we got comprehensive results
        assert len(results) > 5  # Should have multiple scenarios + tail + regime analysis

        # Check that all scenario types are represented
        scenario_types = set()
        for result in results.values():
            scenario_types.add(result.scenario_definition.scenario_type)

        # Should have at least historical and hypothetical scenarios
        assert any('HISTORICAL' in str(st) for st in scenario_types)
        assert any('HYPOTHETICAL' in str(st) for st in scenario_types)

    def test_scenario_comparison_analysis(self, complex_portfolio, real_market_data):
        """Test comparing different scenarios."""
        framework = StressTestingFramework()

        # Test specific scenarios for comparison
        comparison_scenarios = [
            "financial_crisis_2008",
            "covid19_pandemic",
            "extreme_inflation"
        ]

        results = framework.run_comprehensive_stress_test(
            portfolio_data=complex_portfolio,
            asset_returns=real_market_data,
            scenarios=comparison_scenarios,
            include_tail_analysis=False,
            include_regime_analysis=False
        )

        # Compare scenario impacts
        impacts = {name: result.portfolio_value_impact for name, result in results.items()}

        # 2008 crisis should generally be severe
        crisis_2008_impact = impacts["financial_crisis_2008"]
        assert crisis_2008_impact < -0.2  # At least 20% loss

        # All impacts should be negative (crisis scenarios)
        for impact in impacts.values():
            assert impact < 0

    def test_export_functionality(self, complex_portfolio, real_market_data, tmp_path):
        """Test stress test results export functionality."""
        framework = StressTestingFramework()

        # Run limited stress test
        results = framework.run_comprehensive_stress_test(
            portfolio_data=complex_portfolio,
            asset_returns=real_market_data,
            scenarios=["financial_crisis_2008", "covid19_pandemic"],
            include_tail_analysis=False,
            include_regime_analysis=False
        )

        # Test JSON export
        json_file = tmp_path / "stress_results.json"
        framework.export_stress_results(results, str(json_file), format='json')
        assert json_file.exists()

        # Test CSV export
        csv_file = tmp_path / "stress_results.csv"
        framework.export_stress_results(results, str(csv_file), format='csv')
        assert csv_file.exists()

        # Verify CSV content
        import pandas as pd
        csv_data = pd.read_csv(csv_file)
        assert len(csv_data) == len(results)
        assert 'Scenario' in csv_data.columns
        assert 'Portfolio_Impact' in csv_data.columns


class TestQuickStressTest:
    """Test the quick stress test convenience function."""

    def test_quick_stress_test_function(self):
        """Test the quick stress test convenience function."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.015, 300))

        results = run_quick_stress_test(returns)

        # Should return default scenarios
        assert len(results) >= 3  # At least the default scenarios
        assert any("financial_crisis_2008" in name for name in results.keys())
        assert any("covid19_pandemic" in name for name in results.keys())

        # Check result structure
        for result in results.values():
            assert hasattr(result, 'scenario_name')
            assert hasattr(result, 'portfolio_value_impact')

    def test_quick_stress_test_custom_scenarios(self):
        """Test quick stress test with custom scenarios."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.015, 300))

        custom_scenarios = ["covid19_pandemic", "extreme_inflation"]
        results = run_quick_stress_test(returns, scenarios=custom_scenarios)

        assert len(results) >= len(custom_scenarios)

        for scenario_name in custom_scenarios:
            # Should either be directly present or as part of comprehensive results
            scenario_found = any(scenario_name in name for name in results.keys())
            assert scenario_found, f"Scenario {scenario_name} not found in results"


@pytest.mark.slow
class TestStressTestPerformance:
    """Performance tests for stress testing framework."""

    def test_large_dataset_performance(self):
        """Test stress testing performance with large dataset."""
        np.random.seed(42)

        # Large dataset (5 years of daily data)
        large_returns = pd.Series(np.random.normal(0.0005, 0.015, 1825))

        framework = StressTestingFramework()

        import time
        start_time = time.time()

        results = framework.run_comprehensive_stress_test(
            asset_returns=large_returns,
            scenarios=["financial_crisis_2008"],  # Single scenario for performance test
            include_tail_analysis=True,
            include_regime_analysis=True
        )

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in reasonable time (less than 30 seconds)
        assert execution_time < 30, f"Stress test took too long: {execution_time:.2f} seconds"
        assert len(results) > 0

    def test_memory_efficiency(self):
        """Test memory efficiency of stress testing framework."""
        # This test would typically use memory profiling tools
        # For now, we'll just ensure no obvious memory leaks

        framework = StressTestingFramework()

        # Run multiple stress tests to check for memory accumulation
        for i in range(5):
            np.random.seed(i)
            returns = pd.Series(np.random.normal(0.0005, 0.015, 500))

            results = framework.run_comprehensive_stress_test(
                asset_returns=returns,
                scenarios=["covid19_pandemic"],
                include_tail_analysis=False,
                include_regime_analysis=False
            )

            # Clear cache periodically to test cleanup
            if i % 2 == 0:
                framework.stress_test_cache.clear()

        # Framework should still be functional
        assert framework is not None
        assert len(framework.historical_scenarios) > 0


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])