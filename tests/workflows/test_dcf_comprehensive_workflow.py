"""
DCF Valuation Comprehensive Workflow Test
=========================================

This test module provides complete end-to-end testing of the Discounted Cash Flow (DCF)
valuation workflow, covering all available options and configurations.

Test Coverage:
- Multi-stage growth projections and terminal value calculations
- WACC and discount rate calculations
- Sensitivity analysis and scenario modeling
- Monte Carlo simulation integration
- Multiple FCF types integration (FCFE, FCFF, LFCF)
- Valuation result comparison with market prices
- Export functionality and report generation
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
from unittest.mock import Mock, patch

# Import core modules
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.statistics.monte_carlo_engine import MonteCarloEngine

# Import test utilities
from tests.utils.common_test_utilities import get_test_companies, create_mock_financial_data
from tests.fixtures.analysis_fixtures import sample_financial_statements, sample_market_data

logger = logging.getLogger(__name__)


class TestDCFComprehensiveWorkflow:
    """
    Comprehensive workflow tests for DCF valuation covering all functionality
    and integration points.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with sample data and configurations"""
        self.test_companies = get_test_companies()

        # DCF test configuration
        self.dcf_config = {
            'growth_stages': {
                'stage1_years': 5,
                'stage2_years': 5,
                'terminal_growth': 0.025
            },
            'discount_rates': {
                'risk_free_rate': 0.03,
                'market_risk_premium': 0.06,
                'beta_adjustment': True
            },
            'sensitivity_ranges': {
                'growth_rate': (-0.02, 0.02),
                'discount_rate': (-0.01, 0.01),
                'terminal_multiple': (0.8, 1.2)
            },
            'monte_carlo': {
                'simulations': 10000,
                'confidence_levels': [0.05, 0.25, 0.5, 0.75, 0.95]
            }
        }

    def test_complete_dcf_valuation_workflow(self):
        """
        Test complete DCF valuation workflow with all components.

        Workflow:
        1. Initialize DCF valuator with financial data
        2. Configure growth assumptions and discount rates
        3. Calculate multi-stage DCF valuation
        4. Perform sensitivity analysis
        5. Run Monte Carlo simulation
        6. Compare with market valuation
        7. Generate comprehensive report
        """
        for ticker in self.test_companies[:3]:  # Test with first 3 companies
            logger.info(f"Testing DCF valuation workflow for {ticker}")

            # Step 1: Initialize DCF valuator
            calculator = FinancialCalculator(ticker)
            dcf_valuator = DCFValuator(calculator)

            # Verify initialization
            assert dcf_valuator.financial_calculator is not None
            assert dcf_valuator.ticker == ticker

            # Step 2: Configure DCF assumptions
            dcf_assumptions = self._create_dcf_assumptions(ticker, calculator)
            dcf_valuator.configure_assumptions(dcf_assumptions)

            # Step 3: Calculate base DCF valuation
            base_valuation = dcf_valuator.calculate_dcf_valuation()
            self._validate_dcf_valuation(base_valuation, ticker, 'base')

            # Step 4: Perform sensitivity analysis
            sensitivity_results = dcf_valuator.perform_sensitivity_analysis(
                growth_range=self.dcf_config['sensitivity_ranges']['growth_rate'],
                discount_range=self.dcf_config['sensitivity_ranges']['discount_rate']
            )
            self._validate_sensitivity_analysis(sensitivity_results, ticker)

            # Step 5: Run Monte Carlo simulation
            mc_results = dcf_valuator.run_monte_carlo_simulation(
                num_simulations=self.dcf_config['monte_carlo']['simulations']
            )
            self._validate_monte_carlo_results(mc_results, ticker)

            # Step 6: Compare with market valuation
            market_comparison = dcf_valuator.compare_with_market_price()
            self._validate_market_comparison(market_comparison, ticker)

            # Step 7: Generate comprehensive DCF report
            dcf_report = dcf_valuator.generate_comprehensive_report()
            self._validate_dcf_report(dcf_report, ticker)

    def test_multi_stage_growth_modeling_workflow(self):
        """
        Test multi-stage growth modeling with different scenarios.

        Workflow:
        1. Test two-stage growth model
        2. Test three-stage growth model
        3. Test custom growth patterns
        4. Validate terminal value calculations
        5. Test growth rate optimization
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing multi-stage growth modeling for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Test 1: Two-stage growth model
        two_stage_config = {
            'stage1_growth': 0.15,
            'stage1_years': 5,
            'terminal_growth': 0.025
        }

        two_stage_result = dcf_valuator.calculate_two_stage_dcf(two_stage_config)
        self._validate_multi_stage_result(two_stage_result, ticker, 'two_stage')

        # Test 2: Three-stage growth model
        three_stage_config = {
            'stage1_growth': 0.20,
            'stage1_years': 3,
            'stage2_growth': 0.10,
            'stage2_years': 4,
            'terminal_growth': 0.025
        }

        three_stage_result = dcf_valuator.calculate_three_stage_dcf(three_stage_config)
        self._validate_multi_stage_result(three_stage_result, ticker, 'three_stage')

        # Test 3: Custom growth pattern
        custom_growth_rates = [0.25, 0.20, 0.15, 0.10, 0.08, 0.05, 0.03, 0.025]
        custom_result = dcf_valuator.calculate_custom_growth_dcf(custom_growth_rates)
        self._validate_multi_stage_result(custom_result, ticker, 'custom')

        # Test 4: Terminal value calculation methods
        terminal_methods = ['gordon_growth', 'exit_multiple', 'perpetual_cash_flow']
        for method in terminal_methods:
            terminal_value = dcf_valuator.calculate_terminal_value(method=method)
            self._validate_terminal_value(terminal_value, ticker, method)

    def test_discount_rate_calculation_workflow(self):
        """
        Test comprehensive discount rate calculation methodologies.

        Workflow:
        1. Test WACC calculation with market data
        2. Test cost of equity using CAPM
        3. Test cost of debt calculation
        4. Test beta estimation and adjustment
        5. Test alternative discount rate methods
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing discount rate calculations for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Test 1: WACC calculation
        wacc_components = dcf_valuator.calculate_wacc_components()
        wacc_result = dcf_valuator.calculate_wacc(wacc_components)

        self._validate_wacc_calculation(wacc_result, ticker)

        # Test 2: Cost of equity using CAPM
        capm_inputs = {
            'risk_free_rate': 0.03,
            'market_risk_premium': 0.06,
            'beta': wacc_components.get('beta', 1.0)
        }

        cost_of_equity = dcf_valuator.calculate_cost_of_equity_capm(capm_inputs)
        self._validate_cost_of_equity(cost_of_equity, ticker)

        # Test 3: Cost of debt calculation
        cost_of_debt = dcf_valuator.calculate_cost_of_debt()
        self._validate_cost_of_debt(cost_of_debt, ticker)

        # Test 4: Beta estimation
        beta_estimates = dcf_valuator.estimate_beta_multiple_methods()
        self._validate_beta_estimates(beta_estimates, ticker)

        # Test 5: Alternative discount rate methods
        alternative_methods = ['build_up_method', 'dividend_growth_model', 'earnings_yield']
        for method in alternative_methods:
            try:
                alt_rate = dcf_valuator.calculate_alternative_discount_rate(method)
                self._validate_alternative_discount_rate(alt_rate, ticker, method)
            except NotImplementedError:
                logger.info(f"Alternative method {method} not implemented yet")

    def test_sensitivity_analysis_comprehensive_workflow(self):
        """
        Test comprehensive sensitivity analysis with multiple variables.

        Workflow:
        1. Single-variable sensitivity analysis
        2. Two-variable sensitivity analysis
        3. Multi-variable sensitivity analysis
        4. Scenario-based sensitivity testing
        5. Stress testing extreme scenarios
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing comprehensive sensitivity analysis for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Test 1: Single-variable sensitivity
        variables = ['growth_rate', 'discount_rate', 'terminal_multiple', 'tax_rate']
        for variable in variables:
            sensitivity_result = dcf_valuator.single_variable_sensitivity(
                variable=variable,
                range_percent=0.20,
                steps=21
            )
            self._validate_single_variable_sensitivity(sensitivity_result, ticker, variable)

        # Test 2: Two-variable sensitivity
        variable_pairs = [
            ('growth_rate', 'discount_rate'),
            ('terminal_multiple', 'tax_rate'),
            ('stage1_growth', 'stage2_growth')
        ]

        for var1, var2 in variable_pairs:
            two_var_result = dcf_valuator.two_variable_sensitivity(
                variable1=var1,
                variable2=var2,
                range1=0.15,
                range2=0.15,
                steps=11
            )
            self._validate_two_variable_sensitivity(two_var_result, ticker, var1, var2)

        # Test 3: Scenario-based sensitivity
        scenarios = {
            'optimistic': {'growth_adjustment': 1.5, 'discount_adjustment': 0.9},
            'pessimistic': {'growth_adjustment': 0.7, 'discount_adjustment': 1.2},
            'recession': {'growth_adjustment': 0.5, 'discount_adjustment': 1.4}
        }

        scenario_results = dcf_valuator.scenario_sensitivity_analysis(scenarios)
        self._validate_scenario_sensitivity(scenario_results, ticker)

    def test_monte_carlo_dcf_simulation_workflow(self):
        """
        Test Monte Carlo simulation for DCF valuation with uncertainty modeling.

        Workflow:
        1. Configure probability distributions for key variables
        2. Run Monte Carlo simulation
        3. Analyze simulation results and statistics
        4. Calculate confidence intervals
        5. Perform convergence testing
        6. Generate probability distributions
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing Monte Carlo DCF simulation for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Step 1: Configure probability distributions
        mc_config = {
            'growth_rate': {'distribution': 'normal', 'mean': 0.10, 'std': 0.03},
            'discount_rate': {'distribution': 'normal', 'mean': 0.08, 'std': 0.01},
            'terminal_growth': {'distribution': 'normal', 'mean': 0.025, 'std': 0.005},
            'tax_rate': {'distribution': 'uniform', 'low': 0.20, 'high': 0.30}
        }

        dcf_valuator.configure_monte_carlo_distributions(mc_config)

        # Step 2: Run Monte Carlo simulation
        num_simulations = self.dcf_config['monte_carlo']['simulations']
        mc_results = dcf_valuator.run_monte_carlo_simulation(
            num_simulations=num_simulations,
            random_seed=42  # For reproducible results
        )

        # Step 3: Analyze simulation results
        mc_statistics = dcf_valuator.analyze_monte_carlo_results(mc_results)
        self._validate_monte_carlo_statistics(mc_statistics, ticker)

        # Step 4: Calculate confidence intervals
        confidence_levels = self.dcf_config['monte_carlo']['confidence_levels']
        confidence_intervals = dcf_valuator.calculate_confidence_intervals(
            mc_results, confidence_levels
        )
        self._validate_confidence_intervals(confidence_intervals, ticker)

        # Step 5: Test convergence
        convergence_test = dcf_valuator.test_monte_carlo_convergence(mc_results)
        self._validate_convergence_test(convergence_test, ticker)

        # Step 6: Generate probability distributions
        distribution_analysis = dcf_valuator.analyze_value_distribution(mc_results)
        self._validate_distribution_analysis(distribution_analysis, ticker)

    def test_fcf_type_integration_workflow(self):
        """
        Test DCF valuation with different FCF types (FCFE, FCFF, LFCF).

        Workflow:
        1. Calculate DCF using FCFE (equity valuation)
        2. Calculate DCF using FCFF (firm valuation)
        3. Calculate DCF using Levered FCF
        4. Compare valuation results
        5. Test consistency between methods
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing FCF type integration for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        fcf_types = ['FCFE', 'FCFF', 'LFCF']
        valuation_results = {}

        for fcf_type in fcf_types:
            # Configure DCF for specific FCF type
            dcf_valuator.set_fcf_type(fcf_type)

            # Calculate valuation
            valuation = dcf_valuator.calculate_dcf_valuation()
            valuation_results[fcf_type] = valuation

            # Validate specific FCF type requirements
            self._validate_fcf_type_valuation(valuation, ticker, fcf_type)

        # Compare results between FCF types
        self._compare_fcf_type_valuations(valuation_results, ticker)

    def test_market_comparison_and_validation_workflow(self):
        """
        Test market price comparison and valuation validation.

        Workflow:
        1. Fetch current market price
        2. Calculate intrinsic value using DCF
        3. Perform relative valuation comparison
        4. Calculate margin of safety
        5. Generate investment recommendation
        6. Test historical validation
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing market comparison workflow for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Step 1: Get current market data
        market_data = dcf_valuator.get_current_market_data()
        self._validate_market_data(market_data, ticker)

        # Step 2: Calculate intrinsic value
        intrinsic_value = dcf_valuator.calculate_intrinsic_value()
        self._validate_intrinsic_value(intrinsic_value, ticker)

        # Step 3: Perform relative valuation
        relative_metrics = dcf_valuator.calculate_relative_valuation_metrics()
        self._validate_relative_metrics(relative_metrics, ticker)

        # Step 4: Calculate margin of safety
        margin_of_safety = dcf_valuator.calculate_margin_of_safety(
            intrinsic_value, market_data['current_price']
        )
        self._validate_margin_of_safety(margin_of_safety, ticker)

        # Step 5: Generate investment recommendation
        recommendation = dcf_valuator.generate_investment_recommendation(
            intrinsic_value, market_data, margin_of_safety
        )
        self._validate_investment_recommendation(recommendation, ticker)

        # Step 6: Historical validation (if available)
        try:
            historical_validation = dcf_valuator.validate_historical_predictions()
            self._validate_historical_validation(historical_validation, ticker)
        except Exception as e:
            logger.info(f"Historical validation not available for {ticker}: {e}")

    def test_dcf_export_and_reporting_workflow(self):
        """
        Test comprehensive DCF export and reporting capabilities.

        Workflow:
        1. Generate detailed DCF model export
        2. Create summary report with key metrics
        3. Export to multiple formats (Excel, PDF, CSV)
        4. Test report customization options
        5. Validate report accuracy and completeness
        """
        ticker = self.test_companies[0]
        logger.info(f"Testing DCF export and reporting for {ticker}")

        calculator = FinancialCalculator(ticker)
        dcf_valuator = DCFValuator(calculator)

        # Calculate complete DCF valuation
        dcf_result = dcf_valuator.calculate_dcf_valuation()

        # Step 1: Generate detailed DCF model
        detailed_model = dcf_valuator.export_detailed_dcf_model()
        self._validate_detailed_model_export(detailed_model, ticker)

        # Step 2: Create summary report
        summary_report = dcf_valuator.create_summary_report()
        self._validate_summary_report(summary_report, ticker)

        # Step 3: Test export formats
        export_formats = ['excel', 'csv', 'json']
        for format_type in export_formats:
            try:
                export_result = dcf_valuator.export_to_format(format_type)
                self._validate_export_format(export_result, ticker, format_type)
            except NotImplementedError:
                logger.info(f"Export format {format_type} not implemented yet")

        # Step 4: Test report customization
        custom_options = {
            'include_sensitivity': True,
            'include_monte_carlo': True,
            'include_market_comparison': True,
            'include_assumptions': True
        }

        custom_report = dcf_valuator.create_custom_report(custom_options)
        self._validate_custom_report(custom_report, ticker, custom_options)

    # Helper methods for validation

    def _create_dcf_assumptions(self, ticker: str, calculator: FinancialCalculator) -> Dict[str, Any]:
        """Create DCF assumptions based on company data"""
        # Calculate historical growth rates
        historical_fcf = calculator.get_historical_fcf()
        avg_growth = np.mean([r for r in historical_fcf.get('growth_rates', []) if r is not None])

        return {
            'stage1_growth': max(0.05, min(0.30, avg_growth or 0.10)),
            'stage1_years': self.dcf_config['growth_stages']['stage1_years'],
            'stage2_growth': self.dcf_config['growth_stages']['terminal_growth'] * 2,
            'stage2_years': self.dcf_config['growth_stages']['stage2_years'],
            'terminal_growth': self.dcf_config['growth_stages']['terminal_growth'],
            'risk_free_rate': self.dcf_config['discount_rates']['risk_free_rate'],
            'market_risk_premium': self.dcf_config['discount_rates']['market_risk_premium']
        }

    def _validate_dcf_valuation(self, valuation: Dict[str, Any], ticker: str, scenario: str):
        """Validate DCF valuation result structure and values"""
        assert valuation is not None, f"DCF valuation is None for {ticker} ({scenario})"

        required_fields = [
            'intrinsic_value', 'current_price', 'upside_downside',
            'assumptions', 'calculation_details'
        ]

        for field in required_fields:
            assert field in valuation, f"Missing {field} in DCF valuation for {ticker}"

        # Validate numerical values
        intrinsic_value = valuation['intrinsic_value']
        assert isinstance(intrinsic_value, (int, float)), \
            f"Invalid intrinsic value type for {ticker}: {type(intrinsic_value)}"
        assert intrinsic_value > 0, f"Negative intrinsic value for {ticker}: {intrinsic_value}"

    def _validate_sensitivity_analysis(self, sensitivity_results: Dict, ticker: str):
        """Validate sensitivity analysis results"""
        assert sensitivity_results is not None, f"Sensitivity results is None for {ticker}"
        assert 'sensitivity_matrix' in sensitivity_results, \
            f"Missing sensitivity matrix for {ticker}"
        assert 'tornado_chart_data' in sensitivity_results, \
            f"Missing tornado chart data for {ticker}"

    def _validate_monte_carlo_results(self, mc_results: Dict, ticker: str):
        """Validate Monte Carlo simulation results"""
        assert mc_results is not None, f"Monte Carlo results is None for {ticker}"
        assert 'simulated_values' in mc_results, f"Missing simulated values for {ticker}"
        assert 'statistics' in mc_results, f"Missing statistics for {ticker}"

        simulated_values = mc_results['simulated_values']
        assert len(simulated_values) == self.dcf_config['monte_carlo']['simulations'], \
            f"Incorrect number of simulations for {ticker}"

    def _validate_market_comparison(self, comparison: Dict, ticker: str):
        """Validate market price comparison"""
        assert comparison is not None, f"Market comparison is None for {ticker}"
        assert 'current_price' in comparison, f"Missing current price for {ticker}"
        assert 'intrinsic_value' in comparison, f"Missing intrinsic value for {ticker}"
        assert 'margin_of_safety' in comparison, f"Missing margin of safety for {ticker}"

    def _validate_dcf_report(self, report: Dict, ticker: str):
        """Validate comprehensive DCF report"""
        assert report is not None, f"DCF report is None for {ticker}"

        required_sections = [
            'executive_summary', 'assumptions', 'calculations',
            'sensitivity_analysis', 'recommendations'
        ]

        for section in required_sections:
            assert section in report, f"Missing {section} in DCF report for {ticker}"

    def _validate_multi_stage_result(self, result: Dict, ticker: str, stage_type: str):
        """Validate multi-stage growth model results"""
        assert result is not None, f"{stage_type} result is None for {ticker}"
        assert 'present_value' in result, f"Missing present value in {stage_type} for {ticker}"
        assert 'terminal_value' in result, f"Missing terminal value in {stage_type} for {ticker}"

    def _validate_terminal_value(self, terminal_value: float, ticker: str, method: str):
        """Validate terminal value calculation"""
        assert isinstance(terminal_value, (int, float)), \
            f"Invalid terminal value type for {ticker} ({method}): {type(terminal_value)}"
        assert terminal_value > 0, \
            f"Negative terminal value for {ticker} ({method}): {terminal_value}"

    def _validate_wacc_calculation(self, wacc_result: Dict, ticker: str):
        """Validate WACC calculation components"""
        assert wacc_result is not None, f"WACC result is None for {ticker}"
        assert 'wacc' in wacc_result, f"Missing WACC value for {ticker}"
        assert 'cost_of_equity' in wacc_result, f"Missing cost of equity for {ticker}"
        assert 'cost_of_debt' in wacc_result, f"Missing cost of debt for {ticker}"

        wacc = wacc_result['wacc']
        assert 0.01 <= wacc <= 0.50, f"Unreasonable WACC for {ticker}: {wacc:.2%}"

    def _validate_cost_of_equity(self, cost_of_equity: float, ticker: str):
        """Validate cost of equity calculation"""
        assert isinstance(cost_of_equity, (int, float)), \
            f"Invalid cost of equity type for {ticker}: {type(cost_of_equity)}"
        assert 0.02 <= cost_of_equity <= 0.40, \
            f"Unreasonable cost of equity for {ticker}: {cost_of_equity:.2%}"

    def _validate_cost_of_debt(self, cost_of_debt: float, ticker: str):
        """Validate cost of debt calculation"""
        assert isinstance(cost_of_debt, (int, float)), \
            f"Invalid cost of debt type for {ticker}: {type(cost_of_debt)}"
        assert 0.01 <= cost_of_debt <= 0.25, \
            f"Unreasonable cost of debt for {ticker}: {cost_of_debt:.2%}"

    def _validate_beta_estimates(self, beta_estimates: Dict, ticker: str):
        """Validate beta estimation results"""
        assert beta_estimates is not None, f"Beta estimates is None for {ticker}"
        assert 'raw_beta' in beta_estimates, f"Missing raw beta for {ticker}"
        assert 'adjusted_beta' in beta_estimates, f"Missing adjusted beta for {ticker}"

    def _validate_alternative_discount_rate(self, alt_rate: float, ticker: str, method: str):
        """Validate alternative discount rate calculation"""
        assert isinstance(alt_rate, (int, float)), \
            f"Invalid alt rate type for {ticker} ({method}): {type(alt_rate)}"
        assert 0.02 <= alt_rate <= 0.50, \
            f"Unreasonable alt rate for {ticker} ({method}): {alt_rate:.2%}"

    def _validate_single_variable_sensitivity(self, result: Dict, ticker: str, variable: str):
        """Validate single-variable sensitivity analysis"""
        assert result is not None, f"Sensitivity result is None for {ticker} ({variable})"
        assert 'values' in result, f"Missing values in sensitivity for {ticker} ({variable})"
        assert 'range' in result, f"Missing range in sensitivity for {ticker} ({variable})"

    def _validate_two_variable_sensitivity(self, result: Dict, ticker: str, var1: str, var2: str):
        """Validate two-variable sensitivity analysis"""
        assert result is not None, f"Two-var sensitivity is None for {ticker} ({var1}, {var2})"
        assert 'matrix' in result, f"Missing matrix in two-var sensitivity for {ticker}"

    def _validate_scenario_sensitivity(self, results: Dict, ticker: str):
        """Validate scenario-based sensitivity analysis"""
        assert results is not None, f"Scenario results is None for {ticker}"
        required_scenarios = ['optimistic', 'pessimistic', 'recession']
        for scenario in required_scenarios:
            assert scenario in results, f"Missing {scenario} scenario for {ticker}"

    def _validate_monte_carlo_statistics(self, statistics: Dict, ticker: str):
        """Validate Monte Carlo simulation statistics"""
        assert statistics is not None, f"MC statistics is None for {ticker}"
        required_stats = ['mean', 'median', 'std', 'percentiles']
        for stat in required_stats:
            assert stat in statistics, f"Missing {stat} in MC statistics for {ticker}"

    def _validate_confidence_intervals(self, intervals: Dict, ticker: str):
        """Validate confidence interval calculations"""
        assert intervals is not None, f"Confidence intervals is None for {ticker}"
        for level in self.dcf_config['monte_carlo']['confidence_levels']:
            assert level in intervals, f"Missing {level} confidence level for {ticker}"

    def _validate_convergence_test(self, convergence: Dict, ticker: str):
        """Validate Monte Carlo convergence test"""
        assert convergence is not None, f"Convergence test is None for {ticker}"
        assert 'converged' in convergence, f"Missing convergence status for {ticker}"
        assert 'iterations_needed' in convergence, f"Missing iterations for {ticker}"

    def _validate_distribution_analysis(self, analysis: Dict, ticker: str):
        """Validate value distribution analysis"""
        assert analysis is not None, f"Distribution analysis is None for {ticker}"
        assert 'histogram_data' in analysis, f"Missing histogram data for {ticker}"
        assert 'distribution_fit' in analysis, f"Missing distribution fit for {ticker}"

    def _validate_fcf_type_valuation(self, valuation: Dict, ticker: str, fcf_type: str):
        """Validate FCF type-specific valuation requirements"""
        assert valuation is not None, f"{fcf_type} valuation is None for {ticker}"

        if fcf_type == 'FCFE':
            assert 'equity_value' in valuation, f"Missing equity value for {ticker} FCFE"
        elif fcf_type == 'FCFF':
            assert 'enterprise_value' in valuation, f"Missing enterprise value for {ticker} FCFF"

    def _compare_fcf_type_valuations(self, valuations: Dict, ticker: str):
        """Compare valuations between different FCF types"""
        # Basic validation that all valuations produced reasonable results
        for fcf_type, valuation in valuations.items():
            assert valuation.get('intrinsic_value', 0) > 0, \
                f"Invalid intrinsic value for {ticker} {fcf_type}"

    def _validate_market_data(self, market_data: Dict, ticker: str):
        """Validate market data retrieval"""
        assert market_data is not None, f"Market data is None for {ticker}"
        assert 'current_price' in market_data, f"Missing current price for {ticker}"
        assert market_data['current_price'] > 0, f"Invalid current price for {ticker}"

    def _validate_intrinsic_value(self, intrinsic_value: float, ticker: str):
        """Validate intrinsic value calculation"""
        assert isinstance(intrinsic_value, (int, float)), \
            f"Invalid intrinsic value type for {ticker}: {type(intrinsic_value)}"
        assert intrinsic_value > 0, f"Negative intrinsic value for {ticker}: {intrinsic_value}"

    def _validate_relative_metrics(self, metrics: Dict, ticker: str):
        """Validate relative valuation metrics"""
        assert metrics is not None, f"Relative metrics is None for {ticker}"
        expected_metrics = ['P/E', 'P/B', 'EV/EBITDA']
        for metric in expected_metrics:
            if metric in metrics:
                assert isinstance(metrics[metric], (int, float)), \
                    f"Invalid {metric} type for {ticker}: {type(metrics[metric])}"

    def _validate_margin_of_safety(self, margin: float, ticker: str):
        """Validate margin of safety calculation"""
        assert isinstance(margin, (int, float)), \
            f"Invalid margin of safety type for {ticker}: {type(margin)}"
        assert -1.0 <= margin <= 2.0, \
            f"Unreasonable margin of safety for {ticker}: {margin:.2%}"

    def _validate_investment_recommendation(self, recommendation: Dict, ticker: str):
        """Validate investment recommendation"""
        assert recommendation is not None, f"Recommendation is None for {ticker}"
        assert 'action' in recommendation, f"Missing action in recommendation for {ticker}"
        assert 'confidence' in recommendation, f"Missing confidence for {ticker}"

        valid_actions = ['Strong Buy', 'Buy', 'Hold', 'Sell', 'Strong Sell']
        assert recommendation['action'] in valid_actions, \
            f"Invalid recommendation action for {ticker}: {recommendation['action']}"

    def _validate_historical_validation(self, validation: Dict, ticker: str):
        """Validate historical prediction validation"""
        assert validation is not None, f"Historical validation is None for {ticker}"
        assert 'accuracy_score' in validation, f"Missing accuracy score for {ticker}"

    def _validate_detailed_model_export(self, model_export: Dict, ticker: str):
        """Validate detailed DCF model export"""
        assert model_export is not None, f"Model export is None for {ticker}"
        assert 'cash_flows' in model_export, f"Missing cash flows in export for {ticker}"
        assert 'assumptions' in model_export, f"Missing assumptions in export for {ticker}"

    def _validate_summary_report(self, report: Dict, ticker: str):
        """Validate summary report structure"""
        assert report is not None, f"Summary report is None for {ticker}"
        assert 'key_metrics' in report, f"Missing key metrics in summary for {ticker}"

    def _validate_export_format(self, export_result: Any, ticker: str, format_type: str):
        """Validate export format results"""
        assert export_result is not None, \
            f"Export result is None for {ticker} ({format_type})"

    def _validate_custom_report(self, report: Dict, ticker: str, options: Dict):
        """Validate custom report with specified options"""
        assert report is not None, f"Custom report is None for {ticker}"

        for option, enabled in options.items():
            if enabled:
                section_name = option.replace('include_', '')
                assert section_name in report or f"{section_name}_data" in report, \
                    f"Missing {section_name} in custom report for {ticker}"


if __name__ == "__main__":
    # Run comprehensive DCF workflow tests
    pytest.main([__file__, "-v", "--tb=short"])