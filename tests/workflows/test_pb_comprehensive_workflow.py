"""
P/B (Price-to-Book) Analysis Comprehensive Workflow Test
=======================================================

This test module provides complete end-to-end testing of the Price-to-Book ratio
analysis workflow, covering all available options and configurations.

Test Coverage:
- Current P/B ratio calculation from multiple data sources
- Industry-specific benchmarking and sector comparisons
- Historical P/B trend analysis and percentile ranking
- Book value quality assessment and fair value estimation
- Statistical analysis and risk assessment
- Integration with enhanced multi-source data management
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
from core.analysis.pb.pb_valuation import PBValuator
from core.analysis.pb.pb_statistical_analysis import PBStatisticalAnalysisEngine
from core.analysis.pb.pb_fair_value_calculator import PBFairValueCalculator

# Import test utilities
from tests.utils.common_test_utilities import get_test_companies, create_mock_financial_data
from tests.fixtures.analysis_fixtures import sample_financial_statements, sample_market_data

logger = logging.getLogger(__name__)


class TestPBComprehensiveWorkflow:
    """
    Comprehensive workflow tests for P/B analysis covering all functionality
    and integration points.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with sample data and configurations"""
        self.test_companies = get_test_companies()

        # P/B test configuration
        self.pb_config = {
            'industry_benchmarking': {
                'sector_classifications': ['Technology', 'Healthcare', 'Finance', 'Consumer'],
                'peer_count_min': 5,
                'peer_count_max': 20
            },
            'historical_analysis': {
                'min_years': 5,
                'max_years': 10,
                'percentile_levels': [5, 10, 25, 50, 75, 90, 95]
            },
            'statistical_analysis': {
                'confidence_levels': [0.90, 0.95, 0.99],
                'distribution_tests': ['normal', 'lognormal', 'beta'],
                'outlier_threshold': 2.5  # Standard deviations
            },
            'fair_value_estimation': {
                'methods': ['industry_multiple', 'historical_average', 'regression_based'],
                'adjustment_factors': ['growth', 'profitability', 'risk']
            },
            'quality_assessment': {
                'book_value_adjustments': True,
                'intangible_treatment': 'conservative',
                'debt_adjustments': True
            }
        }

    def test_complete_pb_analysis_workflow(self):
        """
        Test complete P/B analysis workflow with all components.

        Workflow:
        1. Calculate current P/B ratio from multiple sources
        2. Perform industry benchmarking and sector comparisons
        3. Conduct historical P/B trend analysis
        4. Assess book value quality and adjustments
        5. Estimate fair value using industry multiples
        6. Perform statistical analysis and risk assessment
        7. Generate comprehensive P/B analysis report
        """
        for ticker in self.test_companies[:3]:  # Test with first 3 companies
            logger.info(f"Testing P/B analysis workflow for {ticker}")

            # Step 1: Initialize P/B valuator
            calculator = FinancialCalculator(ticker)
            pb_valuator = PBValuator(calculator)

            # Step 2: Calculate current P/B ratio
            current_pb = pb_valuator.calculate_current_pb_ratio()
            self._validate_current_pb_calculation(current_pb, ticker)

            # Step 3: Industry benchmarking
            industry_analysis = pb_valuator.perform_industry_benchmarking()
            self._validate_industry_benchmarking(industry_analysis, ticker)

            # Step 4: Historical trend analysis
            historical_analysis = pb_valuator.analyze_historical_pb_trends()
            self._validate_historical_analysis(historical_analysis, ticker)

            # Step 5: Book value quality assessment
            quality_assessment = pb_valuator.assess_book_value_quality()
            self._validate_quality_assessment(quality_assessment, ticker)

            # Step 6: Fair value estimation
            fair_value_analysis = pb_valuator.estimate_fair_value_pb_multiple()
            self._validate_fair_value_analysis(fair_value_analysis, ticker)

            # Step 7: Statistical analysis
            statistical_analysis = pb_valuator.perform_statistical_analysis()
            self._validate_statistical_analysis(statistical_analysis, ticker)

            # Step 8: Generate comprehensive report
            pb_report = pb_valuator.generate_comprehensive_pb_report()
            self._validate_pb_report(pb_report, ticker)

    def test_pb_calculation_multi_source_workflow(self):
        """
        Test P/B calculation using multiple data sources with validation.

        Workflow:
        1. Calculate P/B using market data APIs
        2. Calculate P/B using Excel financial statements
        3. Calculate P/B using alternative data sources
        4. Validate consistency across sources
        5. Handle data quality issues and discrepancies
        """
        logger.info("Testing P/B multi-source calculation workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        pb_calculations = {}

        # Step 1: Calculate using market data APIs
        try:
            api_pb = pb_valuator.calculate_pb_from_market_data()
            pb_calculations['market_api'] = api_pb
            self._validate_pb_calculation(api_pb, ticker, 'market_api')
        except Exception as e:
            logger.warning(f"Market API P/B calculation failed for {ticker}: {e}")

        # Step 2: Calculate using Excel financial statements
        try:
            excel_pb = pb_valuator.calculate_pb_from_excel_data()
            pb_calculations['excel'] = excel_pb
            self._validate_pb_calculation(excel_pb, ticker, 'excel')
        except Exception as e:
            logger.warning(f"Excel P/B calculation failed for {ticker}: {e}")

        # Step 3: Calculate using alternative sources
        alternative_sources = ['yfinance', 'alpha_vantage', 'fmp']
        for source in alternative_sources:
            try:
                alt_pb = pb_valuator.calculate_pb_from_alternative_source(source)
                pb_calculations[source] = alt_pb
                self._validate_pb_calculation(alt_pb, ticker, source)
            except Exception as e:
                logger.warning(f"{source} P/B calculation failed for {ticker}: {e}")

        # Step 4: Validate consistency across sources
        if len(pb_calculations) > 1:
            consistency_analysis = pb_valuator.analyze_pb_source_consistency(pb_calculations)
            self._validate_source_consistency(consistency_analysis, ticker)

        # Step 5: Select best P/B calculation
        best_pb = pb_valuator.select_best_pb_calculation(pb_calculations)
        self._validate_best_pb_selection(best_pb, ticker)

    def test_industry_benchmarking_comprehensive_workflow(self):
        """
        Test comprehensive industry benchmarking and peer comparison.

        Workflow:
        1. Identify industry classification and peer companies
        2. Collect peer P/B ratios and financial metrics
        3. Calculate industry statistics and percentiles
        4. Perform sector-specific analysis
        5. Generate relative positioning assessment
        6. Create industry comparison visualizations
        """
        logger.info("Testing industry benchmarking workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        # Step 1: Industry classification
        industry_classification = pb_valuator.identify_industry_classification()
        self._validate_industry_classification(industry_classification, ticker)

        # Step 2: Identify peer companies
        peer_companies = pb_valuator.identify_peer_companies(
            min_count=self.pb_config['industry_benchmarking']['peer_count_min'],
            max_count=self.pb_config['industry_benchmarking']['peer_count_max']
        )
        self._validate_peer_identification(peer_companies, ticker)

        # Step 3: Collect peer P/B data
        peer_pb_data = pb_valuator.collect_peer_pb_ratios(peer_companies)
        self._validate_peer_pb_data(peer_pb_data, ticker)

        # Step 4: Calculate industry statistics
        industry_statistics = pb_valuator.calculate_industry_pb_statistics(peer_pb_data)
        self._validate_industry_statistics(industry_statistics, ticker)

        # Step 5: Perform relative positioning
        relative_position = pb_valuator.assess_relative_pb_position(
            current_pb=pb_valuator.calculate_current_pb_ratio(),
            industry_stats=industry_statistics
        )
        self._validate_relative_position(relative_position, ticker)

        # Step 6: Sector-specific analysis
        sector_analysis = pb_valuator.perform_sector_specific_analysis()
        self._validate_sector_analysis(sector_analysis, ticker)

        # Step 7: Generate benchmarking report
        benchmarking_report = pb_valuator.generate_industry_benchmarking_report()
        self._validate_benchmarking_report(benchmarking_report, ticker)

    def test_historical_pb_trend_analysis_workflow(self):
        """
        Test comprehensive historical P/B trend analysis and pattern recognition.

        Workflow:
        1. Extract historical P/B ratios over multiple years
        2. Identify trends, cycles, and patterns
        3. Calculate percentile rankings over time
        4. Analyze P/B volatility and stability
        5. Identify mean reversion opportunities
        6. Perform seasonality analysis
        """
        logger.info("Testing historical P/B trend analysis workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        # Step 1: Extract historical P/B data
        historical_pb = pb_valuator.extract_historical_pb_ratios(
            years=self.pb_config['historical_analysis']['max_years']
        )
        self._validate_historical_pb_data(historical_pb, ticker)

        if len(historical_pb) < self.pb_config['historical_analysis']['min_years']:
            pytest.skip(f"Insufficient historical data for {ticker}")

        # Step 2: Trend analysis
        trend_analysis = pb_valuator.analyze_pb_trends(historical_pb)
        self._validate_trend_analysis(trend_analysis, ticker)

        # Step 3: Percentile ranking analysis
        percentile_analysis = pb_valuator.calculate_historical_percentiles(
            historical_pb,
            percentiles=self.pb_config['historical_analysis']['percentile_levels']
        )
        self._validate_percentile_analysis(percentile_analysis, ticker)

        # Step 4: Volatility and stability analysis
        volatility_analysis = pb_valuator.analyze_pb_volatility(historical_pb)
        self._validate_volatility_analysis(volatility_analysis, ticker)

        # Step 5: Mean reversion analysis
        mean_reversion = pb_valuator.analyze_pb_mean_reversion(historical_pb)
        self._validate_mean_reversion_analysis(mean_reversion, ticker)

        # Step 6: Seasonality analysis
        seasonality_analysis = pb_valuator.analyze_pb_seasonality(historical_pb)
        self._validate_seasonality_analysis(seasonality_analysis, ticker)

        # Step 7: Generate historical analysis report
        historical_report = pb_valuator.generate_historical_analysis_report()
        self._validate_historical_report(historical_report, ticker)

    def test_book_value_quality_assessment_workflow(self):
        """
        Test comprehensive book value quality assessment and adjustments.

        Workflow:
        1. Analyze balance sheet composition and quality
        2. Assess intangible asset valuations
        3. Evaluate debt and liability adjustments
        4. Calculate adjusted book value per share
        5. Assess accounting quality and conservatism
        6. Generate quality-adjusted P/B ratios
        """
        logger.info("Testing book value quality assessment workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        # Step 1: Balance sheet composition analysis
        balance_sheet_analysis = pb_valuator.analyze_balance_sheet_composition()
        self._validate_balance_sheet_analysis(balance_sheet_analysis, ticker)

        # Step 2: Intangible asset assessment
        intangible_analysis = pb_valuator.assess_intangible_assets()
        self._validate_intangible_analysis(intangible_analysis, ticker)

        # Step 3: Debt and liability adjustments
        liability_adjustments = pb_valuator.calculate_liability_adjustments()
        self._validate_liability_adjustments(liability_adjustments, ticker)

        # Step 4: Calculate adjusted book value
        adjusted_book_value = pb_valuator.calculate_adjusted_book_value(
            intangible_adjustments=intangible_analysis,
            liability_adjustments=liability_adjustments
        )
        self._validate_adjusted_book_value(adjusted_book_value, ticker)

        # Step 5: Accounting quality assessment
        accounting_quality = pb_valuator.assess_accounting_quality()
        self._validate_accounting_quality(accounting_quality, ticker)

        # Step 6: Quality-adjusted P/B calculation
        quality_adjusted_pb = pb_valuator.calculate_quality_adjusted_pb(adjusted_book_value)
        self._validate_quality_adjusted_pb(quality_adjusted_pb, ticker)

        # Step 7: Generate quality assessment report
        quality_report = pb_valuator.generate_book_value_quality_report()
        self._validate_quality_report(quality_report, ticker)

    def test_pb_fair_value_estimation_workflow(self):
        """
        Test fair value estimation using P/B multiples and various methodologies.

        Workflow:
        1. Industry multiple-based fair value estimation
        2. Historical average-based fair value estimation
        3. Regression-based fair value modeling
        4. Growth-adjusted P/B fair value calculation
        5. Risk-adjusted fair value estimation
        6. Consensus fair value calculation
        """
        logger.info("Testing P/B fair value estimation workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)
        fair_value_calculator = PBFairValueCalculator(pb_valuator)

        fair_value_estimates = {}

        # Step 1: Industry multiple-based estimation
        industry_fair_value = fair_value_calculator.calculate_industry_multiple_fair_value()
        fair_value_estimates['industry_multiple'] = industry_fair_value
        self._validate_fair_value_estimate(industry_fair_value, ticker, 'industry_multiple')

        # Step 2: Historical average-based estimation
        historical_fair_value = fair_value_calculator.calculate_historical_average_fair_value()
        fair_value_estimates['historical_average'] = historical_fair_value
        self._validate_fair_value_estimate(historical_fair_value, ticker, 'historical_average')

        # Step 3: Regression-based modeling
        regression_fair_value = fair_value_calculator.calculate_regression_based_fair_value()
        fair_value_estimates['regression'] = regression_fair_value
        self._validate_fair_value_estimate(regression_fair_value, ticker, 'regression')

        # Step 4: Growth-adjusted estimation
        growth_adjusted_fair_value = fair_value_calculator.calculate_growth_adjusted_fair_value()
        fair_value_estimates['growth_adjusted'] = growth_adjusted_fair_value
        self._validate_fair_value_estimate(growth_adjusted_fair_value, ticker, 'growth_adjusted')

        # Step 5: Risk-adjusted estimation
        risk_adjusted_fair_value = fair_value_calculator.calculate_risk_adjusted_fair_value()
        fair_value_estimates['risk_adjusted'] = risk_adjusted_fair_value
        self._validate_fair_value_estimate(risk_adjusted_fair_value, ticker, 'risk_adjusted')

        # Step 6: Consensus fair value
        consensus_fair_value = fair_value_calculator.calculate_consensus_fair_value(fair_value_estimates)
        self._validate_consensus_fair_value(consensus_fair_value, ticker)

        # Step 7: Fair value sensitivity analysis
        sensitivity_analysis = fair_value_calculator.perform_fair_value_sensitivity_analysis()
        self._validate_fair_value_sensitivity(sensitivity_analysis, ticker)

    def test_pb_statistical_analysis_workflow(self):
        """
        Test comprehensive statistical analysis of P/B ratios.

        Workflow:
        1. Distribution analysis and normality testing
        2. Outlier detection and treatment
        3. Confidence interval calculations
        4. Monte Carlo simulation for P/B forecasting
        5. Statistical significance testing
        6. Correlation analysis with other metrics
        """
        logger.info("Testing P/B statistical analysis workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)
        statistical_analyzer = PBStatisticalAnalyzer(pb_valuator)

        # Step 1: Distribution analysis
        distribution_analysis = statistical_analyzer.analyze_pb_distribution()
        self._validate_distribution_analysis(distribution_analysis, ticker)

        # Step 2: Normality testing
        normality_tests = statistical_analyzer.perform_normality_tests()
        self._validate_normality_tests(normality_tests, ticker)

        # Step 3: Outlier detection
        outlier_analysis = statistical_analyzer.detect_pb_outliers(
            threshold=self.pb_config['statistical_analysis']['outlier_threshold']
        )
        self._validate_outlier_analysis(outlier_analysis, ticker)

        # Step 4: Confidence intervals
        confidence_intervals = statistical_analyzer.calculate_pb_confidence_intervals(
            confidence_levels=self.pb_config['statistical_analysis']['confidence_levels']
        )
        self._validate_confidence_intervals(confidence_intervals, ticker)

        # Step 5: Monte Carlo simulation
        mc_simulation = statistical_analyzer.perform_pb_monte_carlo_simulation(
            simulations=10000
        )
        self._validate_monte_carlo_simulation(mc_simulation, ticker)

        # Step 6: Correlation analysis
        correlation_analysis = statistical_analyzer.analyze_pb_correlations()
        self._validate_correlation_analysis(correlation_analysis, ticker)

        # Step 7: Statistical significance testing
        significance_tests = statistical_analyzer.perform_statistical_significance_tests()
        self._validate_significance_tests(significance_tests, ticker)

    def test_pb_risk_assessment_workflow(self):
        """
        Test comprehensive risk assessment based on P/B analysis.

        Workflow:
        1. P/B-based downside risk assessment
        2. Volatility analysis and risk metrics
        3. Value trap identification
        4. Market timing risk analysis
        5. Sector-specific risk factors
        6. Generate risk-adjusted recommendations
        """
        logger.info("Testing P/B risk assessment workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        # Step 1: Downside risk assessment
        downside_risk = pb_valuator.assess_pb_downside_risk()
        self._validate_downside_risk_assessment(downside_risk, ticker)

        # Step 2: Volatility analysis
        volatility_metrics = pb_valuator.calculate_pb_volatility_metrics()
        self._validate_volatility_metrics(volatility_metrics, ticker)

        # Step 3: Value trap identification
        value_trap_analysis = pb_valuator.assess_value_trap_risk()
        self._validate_value_trap_analysis(value_trap_analysis, ticker)

        # Step 4: Market timing risk
        timing_risk = pb_valuator.assess_market_timing_risk()
        self._validate_timing_risk_assessment(timing_risk, ticker)

        # Step 5: Sector-specific risks
        sector_risks = pb_valuator.identify_sector_specific_risks()
        self._validate_sector_risk_assessment(sector_risks, ticker)

        # Step 6: Generate risk-adjusted recommendations
        risk_recommendations = pb_valuator.generate_risk_adjusted_recommendations()
        self._validate_risk_recommendations(risk_recommendations, ticker)

    def test_pb_integration_workflow(self):
        """
        Test P/B analysis integration with other valuation methods.

        Workflow:
        1. Integration with DCF valuation
        2. Integration with DDM analysis
        3. Integration with other multiple-based valuations
        4. Portfolio-level P/B analysis
        5. Cross-validation with other metrics
        """
        logger.info("Testing P/B integration workflow")

        ticker = self.test_companies[0]
        calculator = FinancialCalculator(ticker)
        pb_valuator = PBValuator(calculator)

        # Step 1: DCF integration
        try:
            from core.analysis.dcf.dcf_valuation import DCFValuator
            dcf_valuator = DCFValuator(calculator)
            dcf_pb_integration = pb_valuator.integrate_with_dcf_analysis(dcf_valuator)
            self._validate_dcf_integration(dcf_pb_integration, ticker)
        except Exception as e:
            logger.warning(f"DCF integration failed for {ticker}: {e}")

        # Step 2: DDM integration
        try:
            from core.analysis.ddm.ddm_valuation import DDMValuator
            ddm_valuator = DDMValuator(calculator)
            ddm_pb_integration = pb_valuator.integrate_with_ddm_analysis(ddm_valuator)
            self._validate_ddm_integration(ddm_pb_integration, ticker)
        except Exception as e:
            logger.warning(f"DDM integration failed for {ticker}: {e}")

        # Step 3: Multiple-based valuation integration
        multiples_integration = pb_valuator.integrate_with_other_multiples()
        self._validate_multiples_integration(multiples_integration, ticker)

        # Step 4: Portfolio-level analysis
        try:
            portfolio_pb_analysis = pb_valuator.perform_portfolio_level_pb_analysis()
            self._validate_portfolio_pb_analysis(portfolio_pb_analysis, ticker)
        except Exception as e:
            logger.warning(f"Portfolio P/B analysis failed for {ticker}: {e}")

    # Helper methods for validation

    def _validate_current_pb_calculation(self, pb_result: Dict, ticker: str):
        """Validate current P/B ratio calculation"""
        assert pb_result is not None, f"P/B calculation is None for {ticker}"

        required_fields = ['pb_ratio', 'book_value_per_share', 'market_price', 'calculation_date']
        for field in required_fields:
            assert field in pb_result, f"Missing {field} in P/B calculation for {ticker}"

        pb_ratio = pb_result['pb_ratio']
        assert isinstance(pb_ratio, (int, float)), \
            f"Invalid P/B ratio type for {ticker}: {type(pb_ratio)}"
        assert pb_ratio > 0, f"Negative P/B ratio for {ticker}: {pb_ratio}"

    def _validate_industry_benchmarking(self, analysis: Dict, ticker: str):
        """Validate industry benchmarking analysis"""
        assert analysis is not None, f"Industry benchmarking is None for {ticker}"

        required_fields = ['industry_stats', 'peer_comparison', 'relative_position']
        for field in required_fields:
            assert field in analysis, f"Missing {field} in industry analysis for {ticker}"

    def _validate_historical_analysis(self, analysis: Dict, ticker: str):
        """Validate historical trend analysis"""
        assert analysis is not None, f"Historical analysis is None for {ticker}"

        required_fields = ['trend_direction', 'volatility_metrics', 'percentile_rankings']
        for field in required_fields:
            assert field in analysis, f"Missing {field} in historical analysis for {ticker}"

    def _validate_quality_assessment(self, assessment: Dict, ticker: str):
        """Validate book value quality assessment"""
        assert assessment is not None, f"Quality assessment is None for {ticker}"

        required_fields = ['quality_score', 'adjustments', 'risk_factors']
        for field in required_fields:
            assert field in assessment, f"Missing {field} in quality assessment for {ticker}"

    def _validate_fair_value_analysis(self, analysis: Dict, ticker: str):
        """Validate fair value analysis"""
        assert analysis is not None, f"Fair value analysis is None for {ticker}"

        required_fields = ['fair_value_estimate', 'upside_downside', 'confidence_level']
        for field in required_fields:
            assert field in analysis, f"Missing {field} in fair value analysis for {ticker}"

    def _validate_statistical_analysis(self, analysis: Dict, ticker: str):
        """Validate statistical analysis"""
        assert analysis is not None, f"Statistical analysis is None for {ticker}"

        required_fields = ['distribution_stats', 'confidence_intervals', 'significance_tests']
        for field in required_fields:
            assert field in analysis, f"Missing {field} in statistical analysis for {ticker}"

    def _validate_pb_report(self, report: Dict, ticker: str):
        """Validate comprehensive P/B report"""
        assert report is not None, f"P/B report is None for {ticker}"

        required_sections = [
            'executive_summary', 'current_analysis', 'industry_comparison',
            'historical_trends', 'fair_value_estimate', 'risk_assessment'
        ]
        for section in required_sections:
            assert section in report, f"Missing {section} in P/B report for {ticker}"

    def _validate_pb_calculation(self, calculation: Dict, ticker: str, source: str):
        """Validate P/B calculation from specific source"""
        assert calculation is not None, f"P/B calculation from {source} is None for {ticker}"
        assert 'pb_ratio' in calculation, f"Missing P/B ratio from {source} for {ticker}"

        pb_ratio = calculation['pb_ratio']
        assert isinstance(pb_ratio, (int, float)), \
            f"Invalid P/B ratio type from {source} for {ticker}: {type(pb_ratio)}"
        assert pb_ratio > 0, f"Negative P/B ratio from {source} for {ticker}: {pb_ratio}"

    def _validate_source_consistency(self, consistency: Dict, ticker: str):
        """Validate source consistency analysis"""
        assert consistency is not None, f"Source consistency is None for {ticker}"
        assert 'consistency_score' in consistency, f"Missing consistency score for {ticker}"

    def _validate_best_pb_selection(self, selection: Dict, ticker: str):
        """Validate best P/B calculation selection"""
        assert selection is not None, f"Best P/B selection is None for {ticker}"
        assert 'selected_pb' in selection, f"Missing selected P/B for {ticker}"
        assert 'selection_rationale' in selection, f"Missing selection rationale for {ticker}"

    def _validate_industry_classification(self, classification: Dict, ticker: str):
        """Validate industry classification"""
        assert classification is not None, f"Industry classification is None for {ticker}"
        assert 'primary_industry' in classification, f"Missing primary industry for {ticker}"

    def _validate_peer_identification(self, peers: List[str], ticker: str):
        """Validate peer company identification"""
        assert peers is not None, f"Peer companies is None for {ticker}"
        assert len(peers) >= self.pb_config['industry_benchmarking']['peer_count_min'], \
            f"Insufficient peer companies for {ticker}: {len(peers)}"

    def _validate_peer_pb_data(self, peer_data: Dict, ticker: str):
        """Validate peer P/B data collection"""
        assert peer_data is not None, f"Peer P/B data is None for {ticker}"
        assert len(peer_data) > 0, f"Empty peer P/B data for {ticker}"

    def _validate_industry_statistics(self, stats: Dict, ticker: str):
        """Validate industry P/B statistics"""
        assert stats is not None, f"Industry statistics is None for {ticker}"

        required_stats = ['mean', 'median', 'std', 'percentiles']
        for stat in required_stats:
            assert stat in stats, f"Missing {stat} in industry statistics for {ticker}"

    def _validate_relative_position(self, position: Dict, ticker: str):
        """Validate relative position assessment"""
        assert position is not None, f"Relative position is None for {ticker}"
        assert 'percentile_rank' in position, f"Missing percentile rank for {ticker}"

    def _validate_sector_analysis(self, analysis: Dict, ticker: str):
        """Validate sector-specific analysis"""
        assert analysis is not None, f"Sector analysis is None for {ticker}"

    def _validate_benchmarking_report(self, report: Dict, ticker: str):
        """Validate industry benchmarking report"""
        assert report is not None, f"Benchmarking report is None for {ticker}"

    def _validate_historical_pb_data(self, historical_data: List[Dict], ticker: str):
        """Validate historical P/B data"""
        assert historical_data is not None, f"Historical P/B data is None for {ticker}"
        assert len(historical_data) >= self.pb_config['historical_analysis']['min_years'], \
            f"Insufficient historical data for {ticker}: {len(historical_data)} years"

    def _validate_trend_analysis(self, analysis: Dict, ticker: str):
        """Validate trend analysis"""
        assert analysis is not None, f"Trend analysis is None for {ticker}"
        assert 'trend_direction' in analysis, f"Missing trend direction for {ticker}"

    def _validate_percentile_analysis(self, analysis: Dict, ticker: str):
        """Validate percentile analysis"""
        assert analysis is not None, f"Percentile analysis is None for {ticker}"
        assert 'current_percentile' in analysis, f"Missing current percentile for {ticker}"

    def _validate_volatility_analysis(self, analysis: Dict, ticker: str):
        """Validate volatility analysis"""
        assert analysis is not None, f"Volatility analysis is None for {ticker}"
        assert 'volatility_score' in analysis, f"Missing volatility score for {ticker}"

    def _validate_mean_reversion_analysis(self, analysis: Dict, ticker: str):
        """Validate mean reversion analysis"""
        assert analysis is not None, f"Mean reversion analysis is None for {ticker}"

    def _validate_seasonality_analysis(self, analysis: Dict, ticker: str):
        """Validate seasonality analysis"""
        assert analysis is not None, f"Seasonality analysis is None for {ticker}"

    def _validate_historical_report(self, report: Dict, ticker: str):
        """Validate historical analysis report"""
        assert report is not None, f"Historical report is None for {ticker}"

    def _validate_balance_sheet_analysis(self, analysis: Dict, ticker: str):
        """Validate balance sheet composition analysis"""
        assert analysis is not None, f"Balance sheet analysis is None for {ticker}"

    def _validate_intangible_analysis(self, analysis: Dict, ticker: str):
        """Validate intangible asset analysis"""
        assert analysis is not None, f"Intangible analysis is None for {ticker}"

    def _validate_liability_adjustments(self, adjustments: Dict, ticker: str):
        """Validate liability adjustments"""
        assert adjustments is not None, f"Liability adjustments is None for {ticker}"

    def _validate_adjusted_book_value(self, adjusted_bv: Dict, ticker: str):
        """Validate adjusted book value calculation"""
        assert adjusted_bv is not None, f"Adjusted book value is None for {ticker}"
        assert 'adjusted_book_value_per_share' in adjusted_bv, \
            f"Missing adjusted BVPS for {ticker}"

    def _validate_accounting_quality(self, quality: Dict, ticker: str):
        """Validate accounting quality assessment"""
        assert quality is not None, f"Accounting quality is None for {ticker}"

    def _validate_quality_adjusted_pb(self, pb: Dict, ticker: str):
        """Validate quality-adjusted P/B calculation"""
        assert pb is not None, f"Quality-adjusted P/B is None for {ticker}"

    def _validate_quality_report(self, report: Dict, ticker: str):
        """Validate book value quality report"""
        assert report is not None, f"Quality report is None for {ticker}"

    def _validate_fair_value_estimate(self, estimate: Dict, ticker: str, method: str):
        """Validate fair value estimate"""
        assert estimate is not None, f"Fair value estimate ({method}) is None for {ticker}"
        assert 'fair_value' in estimate, f"Missing fair value ({method}) for {ticker}"

    def _validate_consensus_fair_value(self, consensus: Dict, ticker: str):
        """Validate consensus fair value"""
        assert consensus is not None, f"Consensus fair value is None for {ticker}"

    def _validate_fair_value_sensitivity(self, sensitivity: Dict, ticker: str):
        """Validate fair value sensitivity analysis"""
        assert sensitivity is not None, f"Fair value sensitivity is None for {ticker}"

    def _validate_distribution_analysis(self, analysis: Dict, ticker: str):
        """Validate distribution analysis"""
        assert analysis is not None, f"Distribution analysis is None for {ticker}"

    def _validate_normality_tests(self, tests: Dict, ticker: str):
        """Validate normality tests"""
        assert tests is not None, f"Normality tests is None for {ticker}"

    def _validate_outlier_analysis(self, analysis: Dict, ticker: str):
        """Validate outlier analysis"""
        assert analysis is not None, f"Outlier analysis is None for {ticker}"

    def _validate_confidence_intervals(self, intervals: Dict, ticker: str):
        """Validate confidence intervals"""
        assert intervals is not None, f"Confidence intervals is None for {ticker}"

    def _validate_monte_carlo_simulation(self, simulation: Dict, ticker: str):
        """Validate Monte Carlo simulation"""
        assert simulation is not None, f"Monte Carlo simulation is None for {ticker}"

    def _validate_correlation_analysis(self, analysis: Dict, ticker: str):
        """Validate correlation analysis"""
        assert analysis is not None, f"Correlation analysis is None for {ticker}"

    def _validate_significance_tests(self, tests: Dict, ticker: str):
        """Validate statistical significance tests"""
        assert tests is not None, f"Significance tests is None for {ticker}"

    def _validate_downside_risk_assessment(self, assessment: Dict, ticker: str):
        """Validate downside risk assessment"""
        assert assessment is not None, f"Downside risk assessment is None for {ticker}"

    def _validate_volatility_metrics(self, metrics: Dict, ticker: str):
        """Validate volatility metrics"""
        assert metrics is not None, f"Volatility metrics is None for {ticker}"

    def _validate_value_trap_analysis(self, analysis: Dict, ticker: str):
        """Validate value trap analysis"""
        assert analysis is not None, f"Value trap analysis is None for {ticker}"

    def _validate_timing_risk_assessment(self, assessment: Dict, ticker: str):
        """Validate market timing risk assessment"""
        assert assessment is not None, f"Timing risk assessment is None for {ticker}"

    def _validate_sector_risk_assessment(self, assessment: Dict, ticker: str):
        """Validate sector-specific risk assessment"""
        assert assessment is not None, f"Sector risk assessment is None for {ticker}"

    def _validate_risk_recommendations(self, recommendations: Dict, ticker: str):
        """Validate risk-adjusted recommendations"""
        assert recommendations is not None, f"Risk recommendations is None for {ticker}"

    def _validate_dcf_integration(self, integration: Dict, ticker: str):
        """Validate DCF integration"""
        assert integration is not None, f"DCF integration is None for {ticker}"

    def _validate_ddm_integration(self, integration: Dict, ticker: str):
        """Validate DDM integration"""
        assert integration is not None, f"DDM integration is None for {ticker}"

    def _validate_multiples_integration(self, integration: Dict, ticker: str):
        """Validate multiples integration"""
        assert integration is not None, f"Multiples integration is None for {ticker}"

    def _validate_portfolio_pb_analysis(self, analysis: Dict, ticker: str):
        """Validate portfolio-level P/B analysis"""
        assert analysis is not None, f"Portfolio P/B analysis is None for {ticker}"


if __name__ == "__main__":
    # Run comprehensive P/B workflow tests
    pytest.main([__file__, "-v", "--tb=short"])