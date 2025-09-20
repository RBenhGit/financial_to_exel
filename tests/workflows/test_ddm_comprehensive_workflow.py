"""
DDM (Dividend Discount Model) Comprehensive Workflow Test
=========================================================

This test module provides complete end-to-end testing of the Dividend Discount Model (DDM)
valuation workflow, covering all available options and configurations.

Test Coverage:
- Gordon Growth Model for stable dividend payers
- Two-Stage and Multi-Stage DDM for complex growth scenarios
- Automatic dividend data extraction and model selection
- Dividend sustainability analysis and quality assessment
- Sensitivity analysis and scenario modeling
- Integration with market data APIs and Excel sources
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# Import core modules
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.ddm.ddm_valuation import DDMValuator

# Import test utilities
from tests.utils.common_test_utilities import get_test_companies, create_mock_financial_data
from tests.fixtures.analysis_fixtures import sample_financial_statements, sample_market_data

logger = logging.getLogger(__name__)


class TestDDMComprehensiveWorkflow:
    """
    Comprehensive workflow tests for DDM valuation covering all functionality
    and integration points.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with sample data and configurations"""
        self.test_companies = get_test_companies()

        # Focus on dividend-paying companies for DDM testing
        self.dividend_companies = ['AAPL', 'MSFT', 'KO', 'JNJ', 'PG']  # Known dividend payers

        # DDM test configuration
        self.ddm_config = {
            'model_selection': {
                'auto_select': True,
                'stability_threshold': 0.15,  # 15% coefficient of variation
                'growth_change_threshold': 0.05  # 5% growth rate change
            },
            'gordon_growth': {
                'min_years_required': 5,
                'max_growth_rate': 0.12,
                'min_growth_rate': -0.05
            },
            'two_stage': {
                'stage1_years': 5,
                'transition_years': 2
            },
            'multi_stage': {
                'max_stages': 4,
                'stage_min_years': 2
            },
            'sensitivity_ranges': {
                'growth_rate': (-0.02, 0.02),
                'discount_rate': (-0.01, 0.01),
                'payout_ratio': (-0.10, 0.10)
            }
        }

    def test_complete_ddm_valuation_workflow(self):
        """
        Test complete DDM valuation workflow with automatic model selection.

        Workflow:
        1. Extract dividend history from multiple sources
        2. Analyze dividend payment patterns and stability
        3. Automatically select appropriate DDM model
        4. Calculate fair value using selected model
        5. Perform sensitivity analysis
        6. Generate comprehensive DDM report
        """
        for ticker in self.dividend_companies[:3]:  # Test with first 3 dividend companies
            logger.info(f"Testing DDM valuation workflow for {ticker}")

            # Step 1: Initialize DDM valuator
            calculator = FinancialCalculator(ticker)
            ddm_valuator = DDMValuator(calculator)

            # Step 2: Extract and analyze dividend data
            dividend_data = ddm_valuator.extract_dividend_history()
            self._validate_dividend_data(dividend_data, ticker)

            # Step 3: Analyze dividend patterns
            dividend_analysis = ddm_valuator.analyze_dividend_patterns(dividend_data)
            self._validate_dividend_analysis(dividend_analysis, ticker)

            # Step 4: Automatic model selection
            selected_model = ddm_valuator.select_optimal_ddm_model(dividend_analysis)
            self._validate_model_selection(selected_model, ticker)

            # Step 5: Calculate DDM valuation
            ddm_valuation = ddm_valuator.calculate_ddm_valuation(selected_model)

            if ddm_valuation:  # Only validate if dividends exist
                self._validate_ddm_valuation(ddm_valuation, ticker, selected_model['model_type'])

                # Step 6: Perform sensitivity analysis
                sensitivity_results = ddm_valuator.perform_ddm_sensitivity_analysis()
                self._validate_ddm_sensitivity_analysis(sensitivity_results, ticker)

                # Step 7: Generate comprehensive DDM report
                ddm_report = ddm_valuator.generate_comprehensive_ddm_report()
                self._validate_ddm_report(ddm_report, ticker)
            else:
                logger.info(f"No dividends found for {ticker}, skipping DDM valuation")

    def test_gordon_growth_model_workflow(self):
        """
        Test Gordon Growth Model for stable dividend-paying companies.

        Workflow:
        1. Identify stable dividend payers
        2. Calculate dividend growth rates
        3. Apply Gordon Growth Model
        4. Validate model assumptions
        5. Perform sensitivity analysis
        """
        logger.info("Testing Gordon Growth Model workflow")

        for ticker in self.dividend_companies[:2]:
            calculator = FinancialCalculator(ticker)
            ddm_valuator = DDMValuator(calculator)

            # Step 1: Extract dividend data
            dividend_data = ddm_valuator.extract_dividend_history()

            if not dividend_data or len(dividend_data) < self.ddm_config['gordon_growth']['min_years_required']:
                logger.info(f"Insufficient dividend data for {ticker}, skipping Gordon Growth test")
                continue

            # Step 2: Calculate growth rates
            growth_rates = ddm_valuator.calculate_dividend_growth_rates(dividend_data)
            self._validate_growth_rates(growth_rates, ticker)

            # Step 3: Check Gordon Growth Model applicability
            gg_applicable = ddm_valuator.is_gordon_growth_applicable(growth_rates)

            if gg_applicable:
                # Step 4: Apply Gordon Growth Model
                gg_config = {
                    'model_type': 'gordon_growth',
                    'growth_rate': np.mean(growth_rates),
                    'required_return': 0.10,  # Assumed required return
                    'current_dividend': dividend_data[-1]['dividend_amount']
                }

                gg_valuation = ddm_valuator.calculate_gordon_growth_valuation(gg_config)
                self._validate_gordon_growth_valuation(gg_valuation, ticker)

                # Step 5: Sensitivity analysis
                gg_sensitivity = ddm_valuator.gordon_growth_sensitivity_analysis(gg_config)
                self._validate_gordon_growth_sensitivity(gg_sensitivity, ticker)
            else:
                logger.info(f"Gordon Growth Model not applicable for {ticker}")

    def test_two_stage_ddm_workflow(self):
        """
        Test Two-Stage DDM for companies with distinct growth phases.

        Workflow:
        1. Identify companies with changing growth patterns
        2. Estimate high-growth and stable-growth phases
        3. Calculate two-stage DDM valuation
        4. Validate transition assumptions
        5. Perform scenario analysis
        """
        logger.info("Testing Two-Stage DDM workflow")

        ticker = self.dividend_companies[0]  # Use one company for detailed testing
        calculator = FinancialCalculator(ticker)
        ddm_valuator = DDMValuator(calculator)

        # Step 1: Extract dividend data
        dividend_data = ddm_valuator.extract_dividend_history()

        if not dividend_data:
            pytest.skip(f"No dividend data available for {ticker}")

        # Step 2: Analyze growth phases
        growth_phases = ddm_valuator.identify_growth_phases(dividend_data)
        self._validate_growth_phases(growth_phases, ticker)

        # Step 3: Configure Two-Stage DDM
        two_stage_config = {
            'model_type': 'two_stage',
            'stage1_growth': growth_phases.get('recent_growth', 0.08),
            'stage1_years': self.ddm_config['two_stage']['stage1_years'],
            'stage2_growth': growth_phases.get('mature_growth', 0.03),
            'required_return': 0.10,
            'current_dividend': dividend_data[-1]['dividend_amount']
        }

        # Step 4: Calculate Two-Stage DDM
        two_stage_valuation = ddm_valuator.calculate_two_stage_ddm(two_stage_config)
        self._validate_two_stage_valuation(two_stage_valuation, ticker)

        # Step 5: Scenario analysis
        scenarios = {
            'optimistic': {'stage1_growth': two_stage_config['stage1_growth'] * 1.5},
            'pessimistic': {'stage1_growth': two_stage_config['stage1_growth'] * 0.5},
            'extended_growth': {'stage1_years': two_stage_config['stage1_years'] + 3}
        }

        scenario_results = ddm_valuator.two_stage_scenario_analysis(two_stage_config, scenarios)
        self._validate_scenario_results(scenario_results, ticker)

    def test_multi_stage_ddm_workflow(self):
        """
        Test Multi-Stage DDM for complex growth scenarios.

        Workflow:
        1. Design multi-stage growth pattern
        2. Configure stage-specific parameters
        3. Calculate multi-stage DDM valuation
        4. Validate stage transitions
        5. Perform optimization of stage parameters
        """
        logger.info("Testing Multi-Stage DDM workflow")

        ticker = self.dividend_companies[0]
        calculator = FinancialCalculator(ticker)
        ddm_valuator = DDMValuator(calculator)

        # Step 1: Extract dividend data
        dividend_data = ddm_valuator.extract_dividend_history()

        if not dividend_data:
            pytest.skip(f"No dividend data available for {ticker}")

        # Step 2: Design multi-stage pattern
        multi_stage_config = {
            'model_type': 'multi_stage',
            'stages': [
                {'years': 3, 'growth_rate': 0.15, 'description': 'High growth'},
                {'years': 4, 'growth_rate': 0.08, 'description': 'Moderate growth'},
                {'years': 3, 'growth_rate': 0.05, 'description': 'Slowing growth'},
                {'years': float('inf'), 'growth_rate': 0.025, 'description': 'Terminal growth'}
            ],
            'required_return': 0.10,
            'current_dividend': dividend_data[-1]['dividend_amount']
        }

        # Step 3: Calculate Multi-Stage DDM
        multi_stage_valuation = ddm_valuator.calculate_multi_stage_ddm(multi_stage_config)
        self._validate_multi_stage_valuation(multi_stage_valuation, ticker)

        # Step 4: Validate stage contributions
        stage_contributions = ddm_valuator.analyze_stage_contributions(multi_stage_config)
        self._validate_stage_contributions(stage_contributions, ticker)

        # Step 5: Optimize stage parameters
        optimized_config = ddm_valuator.optimize_multi_stage_parameters(
            multi_stage_config, dividend_data
        )
        self._validate_optimized_config(optimized_config, ticker)

    def test_dividend_data_extraction_workflow(self):
        """
        Test comprehensive dividend data extraction from multiple sources.

        Workflow:
        1. Extract from yfinance API
        2. Extract from alternative APIs (Alpha Vantage, FMP)
        3. Extract from Excel files (if available)
        4. Validate data consistency across sources
        5. Handle missing or inconsistent data
        """
        logger.info("Testing dividend data extraction workflow")

        ticker = self.dividend_companies[0]
        calculator = FinancialCalculator(ticker)
        ddm_valuator = DDMValuator(calculator)

        extraction_results = {}

        # Step 1: Extract from yfinance
        try:
            yf_dividends = ddm_valuator.extract_dividends_yfinance()
            extraction_results['yfinance'] = yf_dividends
            self._validate_dividend_extraction(yf_dividends, ticker, 'yfinance')
        except Exception as e:
            logger.warning(f"yfinance extraction failed for {ticker}: {e}")

        # Step 2: Extract from alternative APIs
        alternative_sources = ['alpha_vantage', 'fmp']
        for source in alternative_sources:
            try:
                alt_dividends = ddm_valuator.extract_dividends_alternative_api(source)
                extraction_results[source] = alt_dividends
                self._validate_dividend_extraction(alt_dividends, ticker, source)
            except Exception as e:
                logger.warning(f"{source} extraction failed for {ticker}: {e}")

        # Step 3: Extract from Excel (if available)
        try:
            excel_dividends = ddm_valuator.extract_dividends_excel()
            extraction_results['excel'] = excel_dividends
            self._validate_dividend_extraction(excel_dividends, ticker, 'excel')
        except Exception as e:
            logger.info(f"Excel extraction not available for {ticker}: {e}")

        # Step 4: Compare and validate consistency
        if len(extraction_results) > 1:
            consistency_report = ddm_valuator.validate_dividend_data_consistency(extraction_results)
            self._validate_consistency_report(consistency_report, ticker)

        # Step 5: Handle data quality issues
        best_source_data = ddm_valuator.select_best_dividend_source(extraction_results)
        self._validate_best_source_selection(best_source_data, ticker)

    def test_dividend_sustainability_analysis_workflow(self):
        """
        Test dividend sustainability and quality analysis.

        Workflow:
        1. Calculate dividend coverage ratios
        2. Analyze payout ratio trends
        3. Assess free cash flow coverage
        4. Evaluate debt service coverage
        5. Generate sustainability score
        6. Provide dividend sustainability recommendations
        """
        logger.info("Testing dividend sustainability analysis workflow")

        for ticker in self.dividend_companies[:2]:
            calculator = FinancialCalculator(ticker)
            ddm_valuator = DDMValuator(calculator)

            # Check if dividend data exists
            dividend_data = ddm_valuator.extract_dividend_history()
            if not dividend_data:
                logger.info(f"No dividend data for {ticker}, skipping sustainability analysis")
                continue

            # Step 1: Calculate coverage ratios
            coverage_ratios = ddm_valuator.calculate_dividend_coverage_ratios()
            self._validate_coverage_ratios(coverage_ratios, ticker)

            # Step 2: Analyze payout ratio trends
            payout_analysis = ddm_valuator.analyze_payout_ratio_trends()
            self._validate_payout_analysis(payout_analysis, ticker)

            # Step 3: Assess FCF coverage
            fcf_coverage = ddm_valuator.assess_fcf_dividend_coverage()
            self._validate_fcf_coverage(fcf_coverage, ticker)

            # Step 4: Evaluate debt service coverage
            debt_coverage = ddm_valuator.evaluate_debt_service_coverage()
            self._validate_debt_coverage(debt_coverage, ticker)

            # Step 5: Generate sustainability score
            sustainability_score = ddm_valuator.calculate_dividend_sustainability_score()
            self._validate_sustainability_score(sustainability_score, ticker)

            # Step 6: Generate recommendations
            sustainability_recommendations = ddm_valuator.generate_sustainability_recommendations()
            self._validate_sustainability_recommendations(sustainability_recommendations, ticker)

    def test_ddm_sensitivity_and_scenario_analysis_workflow(self):
        """
        Test comprehensive sensitivity analysis and scenario modeling for DDM.

        Workflow:
        1. Single-variable sensitivity analysis
        2. Multi-variable sensitivity analysis
        3. Monte Carlo simulation for DDM
        4. Stress testing scenarios
        5. Interest rate sensitivity analysis
        """
        logger.info("Testing DDM sensitivity and scenario analysis workflow")

        ticker = self.dividend_companies[0]
        calculator = FinancialCalculator(ticker)
        ddm_valuator = DDMValuator(calculator)

        # Ensure dividend data exists
        dividend_data = ddm_valuator.extract_dividend_history()
        if not dividend_data:
            pytest.skip(f"No dividend data available for {ticker}")

        # Get base DDM valuation
        base_valuation = ddm_valuator.calculate_ddm_valuation()
        if not base_valuation:
            pytest.skip(f"DDM valuation not possible for {ticker}")

        # Step 1: Single-variable sensitivity
        variables = ['growth_rate', 'required_return', 'payout_ratio']
        for variable in variables:
            sensitivity_result = ddm_valuator.single_variable_ddm_sensitivity(
                variable=variable,
                range_percent=0.20,
                steps=21
            )
            self._validate_single_variable_ddm_sensitivity(sensitivity_result, ticker, variable)

        # Step 2: Multi-variable sensitivity
        multi_var_result = ddm_valuator.multi_variable_ddm_sensitivity(
            variables=['growth_rate', 'required_return'],
            ranges=[0.15, 0.10],
            steps=[11, 11]
        )
        self._validate_multi_variable_ddm_sensitivity(multi_var_result, ticker)

        # Step 3: Monte Carlo simulation
        mc_config = {
            'simulations': 10000,
            'distributions': {
                'growth_rate': {'type': 'normal', 'mean': 0.06, 'std': 0.02},
                'required_return': {'type': 'normal', 'mean': 0.10, 'std': 0.01},
                'payout_ratio': {'type': 'beta', 'alpha': 2, 'beta': 3}
            }
        }

        mc_results = ddm_valuator.ddm_monte_carlo_simulation(mc_config)
        self._validate_ddm_monte_carlo_results(mc_results, ticker)

        # Step 4: Stress testing scenarios
        stress_scenarios = {
            'recession': {'growth_rate': -0.05, 'required_return': 0.15},
            'inflation_spike': {'required_return': 0.12, 'payout_ratio': 0.8},
            'dividend_cut': {'payout_ratio': 0.3, 'growth_rate': 0.02}
        }

        stress_results = ddm_valuator.ddm_stress_testing(stress_scenarios)
        self._validate_ddm_stress_results(stress_results, ticker)

        # Step 5: Interest rate sensitivity
        interest_rate_sensitivity = ddm_valuator.analyze_interest_rate_sensitivity(
            rate_changes=[-0.02, -0.01, 0, 0.01, 0.02]
        )
        self._validate_interest_rate_sensitivity(interest_rate_sensitivity, ticker)

    def test_ddm_integration_and_comparison_workflow(self):
        """
        Test DDM integration with other valuation methods and comparison analysis.

        Workflow:
        1. Compare DDM with DCF valuation
        2. Compare DDM with P/E and P/B multiples
        3. Integrate DDM with portfolio analysis
        4. Validate DDM against historical performance
        5. Generate comparative valuation report
        """
        logger.info("Testing DDM integration and comparison workflow")

        ticker = self.dividend_companies[0]
        calculator = FinancialCalculator(ticker)
        ddm_valuator = DDMValuator(calculator)

        # Ensure DDM valuation is possible
        ddm_valuation = ddm_valuator.calculate_ddm_valuation()
        if not ddm_valuation:
            pytest.skip(f"DDM valuation not possible for {ticker}")

        # Step 1: Compare with DCF valuation
        try:
            from core.analysis.dcf.dcf_valuation import DCFValuator
            dcf_valuator = DCFValuator(calculator)
            dcf_valuation = dcf_valuator.calculate_dcf_valuation()

            dcf_ddm_comparison = ddm_valuator.compare_ddm_with_dcf(ddm_valuation, dcf_valuation)
            self._validate_dcf_ddm_comparison(dcf_ddm_comparison, ticker)
        except Exception as e:
            logger.warning(f"DCF comparison not available for {ticker}: {e}")

        # Step 2: Compare with multiples valuation
        try:
            multiples_comparison = ddm_valuator.compare_ddm_with_multiples()
            self._validate_multiples_comparison(multiples_comparison, ticker)
        except Exception as e:
            logger.warning(f"Multiples comparison not available for {ticker}: {e}")

        # Step 3: Portfolio integration
        try:
            portfolio_integration = ddm_valuator.integrate_with_portfolio_analysis()
            self._validate_portfolio_integration(portfolio_integration, ticker)
        except Exception as e:
            logger.warning(f"Portfolio integration not available for {ticker}: {e}")

        # Step 4: Historical validation
        try:
            historical_validation = ddm_valuator.validate_ddm_historical_performance()
            self._validate_historical_ddm_validation(historical_validation, ticker)
        except Exception as e:
            logger.info(f"Historical validation not available for {ticker}: {e}")

        # Step 5: Generate comparative report
        comparative_report = ddm_valuator.generate_comparative_valuation_report()
        self._validate_comparative_report(comparative_report, ticker)

    # Helper methods for validation

    def _validate_dividend_data(self, dividend_data: List[Dict], ticker: str):
        """Validate dividend data structure and quality"""
        assert dividend_data is not None, f"Dividend data is None for {ticker}"

        if len(dividend_data) == 0:
            logger.info(f"No dividend history found for {ticker}")
            return

        for dividend in dividend_data:
            required_fields = ['date', 'dividend_amount']
            for field in required_fields:
                assert field in dividend, f"Missing {field} in dividend data for {ticker}"

            assert dividend['dividend_amount'] > 0, \
                f"Invalid dividend amount for {ticker}: {dividend['dividend_amount']}"

    def _validate_dividend_analysis(self, analysis: Dict, ticker: str):
        """Validate dividend pattern analysis"""
        assert analysis is not None, f"Dividend analysis is None for {ticker}"

        expected_metrics = ['stability_score', 'growth_consistency', 'payment_frequency']
        for metric in expected_metrics:
            assert metric in analysis, f"Missing {metric} in dividend analysis for {ticker}"

    def _validate_model_selection(self, selection: Dict, ticker: str):
        """Validate DDM model selection results"""
        assert selection is not None, f"Model selection is None for {ticker}"
        assert 'model_type' in selection, f"Missing model type for {ticker}"
        assert 'confidence_score' in selection, f"Missing confidence score for {ticker}"

        valid_models = ['gordon_growth', 'two_stage', 'multi_stage', 'no_dividends']
        assert selection['model_type'] in valid_models, \
            f"Invalid model type for {ticker}: {selection['model_type']}"

    def _validate_ddm_valuation(self, valuation: Dict, ticker: str, model_type: str):
        """Validate DDM valuation results"""
        assert valuation is not None, f"DDM valuation is None for {ticker}"

        required_fields = ['intrinsic_value', 'dividend_yield', 'model_assumptions']
        for field in required_fields:
            assert field in valuation, f"Missing {field} in DDM valuation for {ticker}"

        intrinsic_value = valuation['intrinsic_value']
        assert isinstance(intrinsic_value, (int, float)), \
            f"Invalid intrinsic value type for {ticker}: {type(intrinsic_value)}"
        assert intrinsic_value > 0, f"Negative intrinsic value for {ticker}: {intrinsic_value}"

    def _validate_ddm_sensitivity_analysis(self, sensitivity: Dict, ticker: str):
        """Validate DDM sensitivity analysis results"""
        assert sensitivity is not None, f"DDM sensitivity is None for {ticker}"
        assert 'sensitivity_matrix' in sensitivity, f"Missing sensitivity matrix for {ticker}"

    def _validate_ddm_report(self, report: Dict, ticker: str):
        """Validate comprehensive DDM report"""
        assert report is not None, f"DDM report is None for {ticker}"

        required_sections = ['executive_summary', 'dividend_analysis', 'valuation_results']
        for section in required_sections:
            assert section in report, f"Missing {section} in DDM report for {ticker}"

    def _validate_growth_rates(self, growth_rates: List[float], ticker: str):
        """Validate dividend growth rate calculations"""
        assert growth_rates is not None, f"Growth rates is None for {ticker}"
        assert len(growth_rates) > 0, f"Empty growth rates for {ticker}"

        for rate in growth_rates:
            if rate is not None:
                assert -0.5 <= rate <= 2.0, \
                    f"Unreasonable growth rate for {ticker}: {rate:.2%}"

    def _validate_gordon_growth_valuation(self, valuation: Dict, ticker: str):
        """Validate Gordon Growth Model valuation"""
        assert valuation is not None, f"Gordon Growth valuation is None for {ticker}"
        assert 'intrinsic_value' in valuation, f"Missing intrinsic value for {ticker}"
        assert 'dividend_yield' in valuation, f"Missing dividend yield for {ticker}"

    def _validate_gordon_growth_sensitivity(self, sensitivity: Dict, ticker: str):
        """Validate Gordon Growth sensitivity analysis"""
        assert sensitivity is not None, f"Gordon Growth sensitivity is None for {ticker}"
        assert 'growth_sensitivity' in sensitivity, f"Missing growth sensitivity for {ticker}"
        assert 'return_sensitivity' in sensitivity, f"Missing return sensitivity for {ticker}"

    def _validate_growth_phases(self, phases: Dict, ticker: str):
        """Validate growth phase identification"""
        assert phases is not None, f"Growth phases is None for {ticker}"
        assert 'recent_growth' in phases, f"Missing recent growth for {ticker}"
        assert 'historical_growth' in phases, f"Missing historical growth for {ticker}"

    def _validate_two_stage_valuation(self, valuation: Dict, ticker: str):
        """Validate Two-Stage DDM valuation"""
        assert valuation is not None, f"Two-stage valuation is None for {ticker}"
        assert 'stage1_value' in valuation, f"Missing stage1 value for {ticker}"
        assert 'stage2_value' in valuation, f"Missing stage2 value for {ticker}"
        assert 'total_value' in valuation, f"Missing total value for {ticker}"

    def _validate_scenario_results(self, results: Dict, ticker: str):
        """Validate scenario analysis results"""
        assert results is not None, f"Scenario results is None for {ticker}"

        expected_scenarios = ['optimistic', 'pessimistic', 'extended_growth']
        for scenario in expected_scenarios:
            assert scenario in results, f"Missing {scenario} scenario for {ticker}"

    def _validate_multi_stage_valuation(self, valuation: Dict, ticker: str):
        """Validate Multi-Stage DDM valuation"""
        assert valuation is not None, f"Multi-stage valuation is None for {ticker}"
        assert 'stage_values' in valuation, f"Missing stage values for {ticker}"
        assert 'total_value' in valuation, f"Missing total value for {ticker}"

    def _validate_stage_contributions(self, contributions: Dict, ticker: str):
        """Validate stage contribution analysis"""
        assert contributions is not None, f"Stage contributions is None for {ticker}"
        assert 'percentage_contributions' in contributions, \
            f"Missing percentage contributions for {ticker}"

    def _validate_optimized_config(self, config: Dict, ticker: str):
        """Validate optimized configuration"""
        assert config is not None, f"Optimized config is None for {ticker}"
        assert 'optimized_stages' in config, f"Missing optimized stages for {ticker}"

    def _validate_dividend_extraction(self, dividends: List[Dict], ticker: str, source: str):
        """Validate dividend extraction from specific source"""
        assert dividends is not None, f"Dividends from {source} is None for {ticker}"

        if len(dividends) > 0:
            for dividend in dividends:
                assert 'date' in dividend, f"Missing date in {source} dividend for {ticker}"
                assert 'dividend_amount' in dividend, \
                    f"Missing amount in {source} dividend for {ticker}"

    def _validate_consistency_report(self, report: Dict, ticker: str):
        """Validate dividend data consistency report"""
        assert report is not None, f"Consistency report is None for {ticker}"
        assert 'consistency_score' in report, f"Missing consistency score for {ticker}"

    def _validate_best_source_selection(self, selection: Dict, ticker: str):
        """Validate best dividend source selection"""
        assert selection is not None, f"Best source selection is None for {ticker}"
        assert 'selected_source' in selection, f"Missing selected source for {ticker}"
        assert 'quality_score' in selection, f"Missing quality score for {ticker}"

    def _validate_coverage_ratios(self, ratios: Dict, ticker: str):
        """Validate dividend coverage ratios"""
        assert ratios is not None, f"Coverage ratios is None for {ticker}"

        expected_ratios = ['earnings_coverage', 'fcf_coverage', 'cash_coverage']
        for ratio in expected_ratios:
            if ratio in ratios:
                assert isinstance(ratios[ratio], (int, float)), \
                    f"Invalid {ratio} type for {ticker}: {type(ratios[ratio])}"

    def _validate_payout_analysis(self, analysis: Dict, ticker: str):
        """Validate payout ratio trend analysis"""
        assert analysis is not None, f"Payout analysis is None for {ticker}"
        assert 'current_payout_ratio' in analysis, f"Missing current payout ratio for {ticker}"
        assert 'payout_trend' in analysis, f"Missing payout trend for {ticker}"

    def _validate_fcf_coverage(self, coverage: Dict, ticker: str):
        """Validate FCF dividend coverage analysis"""
        assert coverage is not None, f"FCF coverage is None for {ticker}"
        assert 'coverage_ratio' in coverage, f"Missing FCF coverage ratio for {ticker}"

    def _validate_debt_coverage(self, coverage: Dict, ticker: str):
        """Validate debt service coverage analysis"""
        assert coverage is not None, f"Debt coverage is None for {ticker}"
        assert 'debt_service_coverage' in coverage, \
            f"Missing debt service coverage for {ticker}"

    def _validate_sustainability_score(self, score: Dict, ticker: str):
        """Validate dividend sustainability score"""
        assert score is not None, f"Sustainability score is None for {ticker}"
        assert 'overall_score' in score, f"Missing overall sustainability score for {ticker}"

        overall_score = score['overall_score']
        assert 0 <= overall_score <= 100, \
            f"Invalid sustainability score for {ticker}: {overall_score}"

    def _validate_sustainability_recommendations(self, recommendations: List, ticker: str):
        """Validate sustainability recommendations"""
        assert recommendations is not None, f"Sustainability recommendations is None for {ticker}"
        assert len(recommendations) > 0, f"Empty recommendations for {ticker}"

    def _validate_single_variable_ddm_sensitivity(self, result: Dict, ticker: str, variable: str):
        """Validate single-variable DDM sensitivity analysis"""
        assert result is not None, f"DDM sensitivity result is None for {ticker} ({variable})"
        assert 'values' in result, f"Missing values in DDM sensitivity for {ticker} ({variable})"

    def _validate_multi_variable_ddm_sensitivity(self, result: Dict, ticker: str):
        """Validate multi-variable DDM sensitivity analysis"""
        assert result is not None, f"Multi-var DDM sensitivity is None for {ticker}"
        assert 'sensitivity_matrix' in result, f"Missing sensitivity matrix for {ticker}"

    def _validate_ddm_monte_carlo_results(self, results: Dict, ticker: str):
        """Validate DDM Monte Carlo simulation results"""
        assert results is not None, f"DDM Monte Carlo results is None for {ticker}"
        assert 'simulated_values' in results, f"Missing simulated values for {ticker}"
        assert 'statistics' in results, f"Missing statistics for {ticker}"

    def _validate_ddm_stress_results(self, results: Dict, ticker: str):
        """Validate DDM stress testing results"""
        assert results is not None, f"DDM stress results is None for {ticker}"

        expected_scenarios = ['recession', 'inflation_spike', 'dividend_cut']
        for scenario in expected_scenarios:
            assert scenario in results, f"Missing {scenario} stress scenario for {ticker}"

    def _validate_interest_rate_sensitivity(self, sensitivity: Dict, ticker: str):
        """Validate interest rate sensitivity analysis"""
        assert sensitivity is not None, f"Interest rate sensitivity is None for {ticker}"
        assert 'rate_impacts' in sensitivity, f"Missing rate impacts for {ticker}"

    def _validate_dcf_ddm_comparison(self, comparison: Dict, ticker: str):
        """Validate DCF vs DDM comparison"""
        assert comparison is not None, f"DCF-DDM comparison is None for {ticker}"
        assert 'dcf_value' in comparison, f"Missing DCF value in comparison for {ticker}"
        assert 'ddm_value' in comparison, f"Missing DDM value in comparison for {ticker}"

    def _validate_multiples_comparison(self, comparison: Dict, ticker: str):
        """Validate multiples valuation comparison"""
        assert comparison is not None, f"Multiples comparison is None for {ticker}"

    def _validate_portfolio_integration(self, integration: Dict, ticker: str):
        """Validate portfolio integration results"""
        assert integration is not None, f"Portfolio integration is None for {ticker}"

    def _validate_historical_ddm_validation(self, validation: Dict, ticker: str):
        """Validate historical DDM performance validation"""
        assert validation is not None, f"Historical DDM validation is None for {ticker}"
        assert 'accuracy_metrics' in validation, f"Missing accuracy metrics for {ticker}"

    def _validate_comparative_report(self, report: Dict, ticker: str):
        """Validate comparative valuation report"""
        assert report is not None, f"Comparative report is None for {ticker}"
        assert 'valuation_summary' in report, f"Missing valuation summary for {ticker}"


if __name__ == "__main__":
    # Run comprehensive DDM workflow tests
    pytest.main([__file__, "-v", "--tb=short"])