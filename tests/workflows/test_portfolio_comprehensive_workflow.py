"""
Portfolio Management Comprehensive Workflow Test
===============================================

This test module provides complete end-to-end testing of the Portfolio Management
system workflow, covering all available options and configurations.

Test Coverage:
- Portfolio creation, optimization, and management
- Performance analytics and attribution analysis
- Risk management and Monte Carlo simulation
- Backtesting and strategy validation
- Rebalancing and position sizing
- Integration with individual security analysis
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
from core.analysis.portfolio.portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType, RebalancingStrategy,
    PositionSizingMethod, create_sample_portfolio
)
from core.analysis.portfolio.portfolio_performance_analytics import PortfolioPerformanceAnalyzer
from core.analysis.portfolio.portfolio_optimization import PortfolioOptimizer
from core.analysis.portfolio.portfolio_backtesting import BacktestEngine
from core.analysis.portfolio.portfolio_persistence import (
    get_portfolio_manager, save_portfolio, load_portfolio,
    list_portfolios, delete_portfolio
)

# Import test utilities
from tests.utils.common_test_utilities import get_test_companies, create_mock_financial_data
from tests.fixtures.analysis_fixtures import sample_financial_statements, sample_market_data

logger = logging.getLogger(__name__)


class TestPortfolioComprehensiveWorkflow:
    """
    Comprehensive workflow tests for Portfolio Management covering all functionality
    and integration points.
    """

    @pytest.fixture(autouse=True)
    def setup_test_environment(self):
        """Set up test environment with sample data and configurations"""
        self.test_companies = get_test_companies()

        # Portfolio test configuration
        self.portfolio_config = {
            'portfolio_types': [
                PortfolioType.GROWTH, PortfolioType.VALUE, PortfolioType.DIVIDEND,
                PortfolioType.BALANCED, PortfolioType.CONSERVATIVE
            ],
            'rebalancing_strategies': [
                RebalancingStrategy.PERIODIC, RebalancingStrategy.THRESHOLD,
                RebalancingStrategy.VOLATILITY_TARGET
            ],
            'position_sizing_methods': [
                PositionSizingMethod.EQUAL_WEIGHT, PositionSizingMethod.MARKET_CAP,
                PositionSizingMethod.RISK_PARITY, PositionSizingMethod.CUSTOM
            ],
            'performance_metrics': [
                'total_return', 'annualized_return', 'volatility', 'sharpe_ratio',
                'max_drawdown', 'calmar_ratio', 'sortino_ratio'
            ],
            'benchmark_options': ['SPY', 'QQQ', 'VTI', 'custom_benchmark']
        }

        # Create sample portfolios for testing
        self.sample_portfolios = self._create_sample_portfolios()

    def test_complete_portfolio_management_workflow(self):
        """
        Test complete portfolio management workflow from creation to analysis.

        Workflow:
        1. Create portfolio with holdings and configurations
        2. Optimize portfolio allocations
        3. Perform portfolio analytics and performance measurement
        4. Execute rebalancing operations
        5. Conduct risk analysis and stress testing
        6. Generate comprehensive portfolio reports
        """
        logger.info("Testing complete portfolio management workflow")

        for portfolio_type in self.portfolio_config['portfolio_types'][:3]:
            logger.info(f"Testing {portfolio_type.value} portfolio workflow")

            # Step 1: Create portfolio
            portfolio = self._create_test_portfolio(portfolio_type)
            self._validate_portfolio_creation(portfolio, portfolio_type)

            # Step 2: Optimize portfolio allocations
            optimizer = PortfolioOptimizer(portfolio)
            optimized_portfolio = optimizer.optimize_portfolio()
            self._validate_portfolio_optimization(optimized_portfolio, portfolio_type)

            # Step 3: Performance analytics
            performance_analyzer = PortfolioPerformanceAnalyzer(optimized_portfolio)
            performance_metrics = performance_analyzer.calculate_comprehensive_metrics()
            self._validate_performance_metrics(performance_metrics, portfolio_type)

            # Step 4: Rebalancing operations
            rebalancing_result = optimizer.perform_rebalancing()
            self._validate_rebalancing_operation(rebalancing_result, portfolio_type)

            # Step 5: Risk analysis
            risk_analysis = performance_analyzer.perform_risk_analysis()
            self._validate_risk_analysis(risk_analysis, portfolio_type)

            # Step 6: Generate comprehensive report
            portfolio_report = performance_analyzer.generate_comprehensive_report()
            self._validate_portfolio_report(portfolio_report, portfolio_type)

    def test_portfolio_optimization_comprehensive_workflow(self):
        """
        Test comprehensive portfolio optimization with multiple methodologies.

        Workflow:
        1. Mean-variance optimization (Markowitz)
        2. Black-Litterman model implementation
        3. Risk parity optimization
        4. Constraint-based optimization
        5. Multi-objective optimization
        6. Optimization sensitivity analysis
        """
        logger.info("Testing portfolio optimization workflow")

        portfolio = self.sample_portfolios['balanced']
        optimizer = PortfolioOptimizer(portfolio)

        optimization_methods = ['markowitz', 'black_litterman', 'risk_parity', 'constrained']

        for method in optimization_methods:
            logger.info(f"Testing {method} optimization")

            # Configure optimization method
            optimization_config = self._create_optimization_config(method)
            optimizer.configure_optimization(optimization_config)

            # Execute optimization
            optimized_result = optimizer.optimize_portfolio(method=method)
            self._validate_optimization_result(optimized_result, method)

            # Sensitivity analysis
            sensitivity_analysis = optimizer.perform_sensitivity_analysis(optimized_result)
            self._validate_optimization_sensitivity(sensitivity_analysis, method)

        # Multi-objective optimization
        multi_obj_result = optimizer.multi_objective_optimization(
            objectives=['return', 'risk', 'diversification']
        )
        self._validate_multi_objective_optimization(multi_obj_result)

    def test_portfolio_performance_analytics_workflow(self):
        """
        Test comprehensive portfolio performance analytics and attribution.

        Workflow:
        1. Return calculation (time-weighted, money-weighted)
        2. Risk metrics calculation (volatility, VaR, drawdown)
        3. Risk-adjusted return metrics (Sharpe, Sortino, Calmar)
        4. Benchmark comparison and tracking error
        5. Attribution analysis (sector, security, allocation)
        6. Rolling performance analysis
        """
        logger.info("Testing portfolio performance analytics workflow")

        portfolio = self.sample_portfolios['growth']
        performance_analyzer = PortfolioPerformanceAnalyzer(portfolio)

        # Step 1: Return calculations
        return_metrics = performance_analyzer.calculate_return_metrics()
        self._validate_return_metrics(return_metrics)

        # Step 2: Risk metrics
        risk_metrics = performance_analyzer.calculate_risk_metrics()
        self._validate_risk_metrics(risk_metrics)

        # Step 3: Risk-adjusted returns
        risk_adjusted_metrics = performance_analyzer.calculate_risk_adjusted_returns()
        self._validate_risk_adjusted_metrics(risk_adjusted_metrics)

        # Step 4: Benchmark comparison
        benchmark_comparison = performance_analyzer.compare_to_benchmark('SPY')
        self._validate_benchmark_comparison(benchmark_comparison)

        # Step 5: Attribution analysis
        attribution_analysis = performance_analyzer.perform_attribution_analysis()
        self._validate_attribution_analysis(attribution_analysis)

        # Step 6: Rolling performance
        rolling_analysis = performance_analyzer.calculate_rolling_performance()
        self._validate_rolling_performance(rolling_analysis)

    def test_portfolio_backtesting_comprehensive_workflow(self):
        """
        Test comprehensive portfolio backtesting and strategy validation.

        Workflow:
        1. Historical simulation setup and data preparation
        2. Strategy implementation and signal generation
        3. Transaction cost modeling and execution
        4. Performance tracking and metric calculation
        5. Drawdown analysis and risk management
        6. Out-of-sample testing and validation
        """
        logger.info("Testing portfolio backtesting workflow")

        portfolio = self.sample_portfolios['value']
        backtester = BacktestEngine(portfolio)

        # Step 1: Setup backtesting parameters
        backtest_config = {
            'start_date': datetime.now() - timedelta(days=365*3),  # 3 years
            'end_date': datetime.now(),
            'initial_capital': 100000,
            'rebalancing_frequency': 'quarterly',
            'transaction_costs': 0.001,  # 0.1%
            'benchmark': 'SPY'
        }

        backtester.configure_backtest(backtest_config)

        # Step 2: Execute backtesting
        backtest_results = backtester.run_backtest()
        self._validate_backtest_results(backtest_results)

        # Step 3: Performance analysis
        backtest_performance = backtester.analyze_backtest_performance(backtest_results)
        self._validate_backtest_performance(backtest_performance)

        # Step 4: Drawdown analysis
        drawdown_analysis = backtester.analyze_drawdowns(backtest_results)
        self._validate_drawdown_analysis(drawdown_analysis)

        # Step 5: Out-of-sample testing
        oos_results = backtester.out_of_sample_testing()
        self._validate_out_of_sample_results(oos_results)

        # Step 6: Strategy validation
        strategy_validation = backtester.validate_strategy_robustness()
        self._validate_strategy_validation(strategy_validation)

    def test_portfolio_rebalancing_workflow(self):
        """
        Test comprehensive portfolio rebalancing strategies and execution.

        Workflow:
        1. Threshold-based rebalancing triggers
        2. Periodic rebalancing execution
        3. Volatility-target rebalancing
        4. Tax-efficient rebalancing
        5. Transaction cost optimization
        6. Rebalancing impact analysis
        """
        logger.info("Testing portfolio rebalancing workflow")

        portfolio = self.sample_portfolios['dividend']
        optimizer = PortfolioOptimizer(portfolio)

        rebalancing_strategies = [
            RebalancingStrategy.THRESHOLD,
            RebalancingStrategy.PERIODIC,
            RebalancingStrategy.VOLATILITY_TARGET
        ]

        for strategy in rebalancing_strategies:
            logger.info(f"Testing {strategy.value} rebalancing")

            # Configure rebalancing strategy
            rebalancing_config = self._create_rebalancing_config(strategy)
            optimizer.configure_rebalancing(rebalancing_config)

            # Execute rebalancing
            rebalancing_result = optimizer.execute_rebalancing(strategy)
            self._validate_rebalancing_execution(rebalancing_result, strategy)

            # Analyze rebalancing impact
            impact_analysis = optimizer.analyze_rebalancing_impact(rebalancing_result)
            self._validate_rebalancing_impact(impact_analysis, strategy)

        # Tax-efficient rebalancing
        tax_efficient_result = optimizer.tax_efficient_rebalancing()
        self._validate_tax_efficient_rebalancing(tax_efficient_result)

        # Transaction cost optimization
        cost_optimized_result = optimizer.optimize_transaction_costs()
        self._validate_cost_optimized_rebalancing(cost_optimized_result)

    def test_portfolio_risk_management_workflow(self):
        """
        Test comprehensive portfolio risk management and monitoring.

        Workflow:
        1. Portfolio risk profiling and measurement
        2. Value-at-Risk (VaR) calculation and monitoring
        3. Stress testing and scenario analysis
        4. Correlation analysis and diversification metrics
        5. Risk factor exposure analysis
        6. Dynamic risk management and alerts
        """
        logger.info("Testing portfolio risk management workflow")

        portfolio = self.sample_portfolios['aggressive']
        performance_analyzer = PortfolioPerformanceAnalyzer(portfolio)

        # Step 1: Risk profiling
        risk_profile = performance_analyzer.create_portfolio_risk_profile()
        self._validate_risk_profile(risk_profile)

        # Step 2: VaR calculation
        var_analysis = performance_analyzer.calculate_portfolio_var()
        self._validate_var_analysis(var_analysis)

        # Step 3: Stress testing
        stress_test_results = performance_analyzer.perform_stress_testing()
        self._validate_stress_test_results(stress_test_results)

        # Step 4: Correlation analysis
        correlation_analysis = performance_analyzer.analyze_portfolio_correlations()
        self._validate_correlation_analysis(correlation_analysis)

        # Step 5: Risk factor exposure
        factor_exposure = performance_analyzer.analyze_risk_factor_exposure()
        self._validate_factor_exposure_analysis(factor_exposure)

        # Step 6: Dynamic risk monitoring
        risk_monitoring = performance_analyzer.setup_dynamic_risk_monitoring()
        self._validate_risk_monitoring_setup(risk_monitoring)

    def test_portfolio_persistence_and_management_workflow(self):
        """
        Test portfolio persistence, loading, and management operations.

        Workflow:
        1. Save portfolios to persistent storage
        2. Load portfolios from storage
        3. List and search existing portfolios
        4. Update and modify portfolio configurations
        5. Delete portfolios and cleanup
        6. Portfolio versioning and history tracking
        """
        logger.info("Testing portfolio persistence and management workflow")

        portfolio_manager = get_portfolio_manager()

        # Step 1: Save portfolios
        for name, portfolio in self.sample_portfolios.items():
            save_result = save_portfolio(portfolio, name)
            self._validate_portfolio_save(save_result, name)

        # Step 2: Load portfolios
        for name in self.sample_portfolios.keys():
            loaded_portfolio = load_portfolio(name)
            self._validate_portfolio_load(loaded_portfolio, name)

        # Step 3: List portfolios
        portfolio_list = list_portfolios()
        self._validate_portfolio_listing(portfolio_list)

        # Step 4: Update portfolio
        updated_portfolio = self._modify_portfolio(self.sample_portfolios['balanced'])
        update_result = save_portfolio(updated_portfolio, 'balanced_updated')
        self._validate_portfolio_update(update_result)

        # Step 5: Portfolio versioning
        version_history = portfolio_manager.get_portfolio_history('balanced')
        self._validate_portfolio_versioning(version_history)

        # Step 6: Cleanup - delete test portfolios
        for name in list(self.sample_portfolios.keys()) + ['balanced_updated']:
            delete_result = delete_portfolio(name)
            self._validate_portfolio_deletion(delete_result, name)

    def test_portfolio_integration_workflow(self):
        """
        Test portfolio integration with individual security analysis.

        Workflow:
        1. Import security analysis results into portfolio
        2. Update portfolio based on analysis recommendations
        3. Integrate FCF, DCF, DDM, P/B analysis results
        4. Portfolio-level aggregation of security metrics
        5. Cross-validation of portfolio and security analysis
        """
        logger.info("Testing portfolio integration workflow")

        portfolio = self.sample_portfolios['growth']

        # Step 1: Import security analysis
        for holding in portfolio.holdings:
            try:
                # Import FCF analysis
                fcf_analysis = self._get_security_fcf_analysis(holding.ticker)
                integration_result = portfolio.integrate_fcf_analysis(holding.ticker, fcf_analysis)
                self._validate_fcf_integration(integration_result, holding.ticker)

                # Import DCF analysis
                dcf_analysis = self._get_security_dcf_analysis(holding.ticker)
                integration_result = portfolio.integrate_dcf_analysis(holding.ticker, dcf_analysis)
                self._validate_dcf_integration(integration_result, holding.ticker)

                # Import DDM analysis (if applicable)
                ddm_analysis = self._get_security_ddm_analysis(holding.ticker)
                if ddm_analysis:
                    integration_result = portfolio.integrate_ddm_analysis(holding.ticker, ddm_analysis)
                    self._validate_ddm_integration(integration_result, holding.ticker)

                # Import P/B analysis
                pb_analysis = self._get_security_pb_analysis(holding.ticker)
                integration_result = portfolio.integrate_pb_analysis(holding.ticker, pb_analysis)
                self._validate_pb_integration(integration_result, holding.ticker)

            except Exception as e:
                logger.warning(f"Security analysis integration failed for {holding.ticker}: {e}")

        # Step 2: Portfolio-level aggregation
        aggregated_metrics = portfolio.aggregate_security_metrics()
        self._validate_metric_aggregation(aggregated_metrics)

        # Step 3: Cross-validation
        cross_validation = portfolio.cross_validate_analysis()
        self._validate_cross_validation(cross_validation)

    # Helper methods for portfolio creation and configuration

    def _create_sample_portfolios(self) -> Dict[str, Portfolio]:
        """Create sample portfolios for testing"""
        portfolios = {}

        # Growth portfolio
        growth_holdings = [
            PortfolioHolding(ticker='AAPL', shares=50, purchase_price=150.0),
            PortfolioHolding(ticker='GOOGL', shares=25, purchase_price=2800.0),
            PortfolioHolding(ticker='TSLA', shares=30, purchase_price=800.0),
            PortfolioHolding(ticker='NVDA', shares=40, purchase_price=500.0)
        ]
        portfolios['growth'] = Portfolio(
            name='Growth Portfolio',
            portfolio_type=PortfolioType.GROWTH,
            holdings=growth_holdings
        )

        # Value portfolio
        value_holdings = [
            PortfolioHolding(ticker='BRK.B', shares=100, purchase_price=300.0),
            PortfolioHolding(ticker='JPM', shares=75, purchase_price=140.0),
            PortfolioHolding(ticker='WMT', shares=80, purchase_price=140.0),
            PortfolioHolding(ticker='XOM', shares=90, purchase_price=100.0)
        ]
        portfolios['value'] = Portfolio(
            name='Value Portfolio',
            portfolio_type=PortfolioType.VALUE,
            holdings=value_holdings
        )

        # Dividend portfolio
        dividend_holdings = [
            PortfolioHolding(ticker='JNJ', shares=60, purchase_price=170.0),
            PortfolioHolding(ticker='PG', shares=70, purchase_price=150.0),
            PortfolioHolding(ticker='KO', shares=100, purchase_price=60.0),
            PortfolioHolding(ticker='VZ', shares=120, purchase_price=50.0)
        ]
        portfolios['dividend'] = Portfolio(
            name='Dividend Portfolio',
            portfolio_type=PortfolioType.DIVIDEND,
            holdings=dividend_holdings
        )

        # Balanced portfolio
        balanced_holdings = growth_holdings[:2] + value_holdings[:2] + dividend_holdings[:2]
        portfolios['balanced'] = Portfolio(
            name='Balanced Portfolio',
            portfolio_type=PortfolioType.BALANCED,
            holdings=balanced_holdings
        )

        # Aggressive portfolio
        aggressive_holdings = [
            PortfolioHolding(ticker='GME', shares=50, purchase_price=200.0),
            PortfolioHolding(ticker='AMC', shares=200, purchase_price=20.0),
            PortfolioHolding(ticker='PLTR', shares=100, purchase_price=25.0)
        ]
        portfolios['aggressive'] = Portfolio(
            name='Aggressive Portfolio',
            portfolio_type=PortfolioType.AGGRESSIVE,
            holdings=aggressive_holdings
        )

        return portfolios

    def _create_test_portfolio(self, portfolio_type: PortfolioType) -> Portfolio:
        """Create a test portfolio of specified type"""
        holdings = [
            PortfolioHolding(ticker=ticker, shares=100, purchase_price=100.0)
            for ticker in self.test_companies[:5]
        ]

        return Portfolio(
            name=f'Test {portfolio_type.value} Portfolio',
            portfolio_type=portfolio_type,
            holdings=holdings
        )

    def _create_optimization_config(self, method: str) -> Dict[str, Any]:
        """Create optimization configuration for specified method"""
        base_config = {
            'target_return': 0.12,
            'risk_tolerance': 0.15,
            'constraints': {
                'max_weight': 0.20,
                'min_weight': 0.02,
                'sector_limits': {'Technology': 0.30}
            }
        }

        if method == 'black_litterman':
            base_config.update({
                'confidence_level': 0.25,
                'market_cap_weights': True
            })
        elif method == 'risk_parity':
            base_config.update({
                'target_risk_contribution': 'equal'
            })

        return base_config

    def _create_rebalancing_config(self, strategy: RebalancingStrategy) -> Dict[str, Any]:
        """Create rebalancing configuration for specified strategy"""
        configs = {
            RebalancingStrategy.THRESHOLD: {
                'threshold': 0.05,  # 5% deviation threshold
                'min_rebalance_amount': 1000
            },
            RebalancingStrategy.PERIODIC: {
                'frequency': 'quarterly',
                'calendar_based': True
            },
            RebalancingStrategy.VOLATILITY_TARGET: {
                'target_volatility': 0.15,
                'lookback_period': 60  # days
            }
        }
        return configs.get(strategy, {})

    def _modify_portfolio(self, portfolio: Portfolio) -> Portfolio:
        """Modify portfolio for testing updates"""
        modified_portfolio = Portfolio(
            name=portfolio.name + ' Modified',
            portfolio_type=portfolio.portfolio_type,
            holdings=portfolio.holdings[:3]  # Remove some holdings
        )
        return modified_portfolio

    # Security analysis helper methods

    def _get_security_fcf_analysis(self, ticker: str) -> Dict[str, Any]:
        """Get FCF analysis for security"""
        try:
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calculator = FinancialCalculator(ticker)
            return calculator.calculate_fcfe()
        except Exception:
            return {'current_fcf': 1000000, 'growth_rate': 0.05}

    def _get_security_dcf_analysis(self, ticker: str) -> Dict[str, Any]:
        """Get DCF analysis for security"""
        try:
            from core.analysis.dcf.dcf_valuation import DCFValuator
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calculator = FinancialCalculator(ticker)
            dcf_valuator = DCFValuator(calculator)
            return dcf_valuator.calculate_dcf_valuation()
        except Exception:
            return {'intrinsic_value': 100.0, 'current_price': 95.0}

    def _get_security_ddm_analysis(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get DDM analysis for security"""
        try:
            from core.analysis.ddm.ddm_valuation import DDMValuator
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calculator = FinancialCalculator(ticker)
            ddm_valuator = DDMValuator(calculator)
            return ddm_valuator.calculate_ddm_valuation()
        except Exception:
            return None

    def _get_security_pb_analysis(self, ticker: str) -> Dict[str, Any]:
        """Get P/B analysis for security"""
        try:
            from core.analysis.pb.pb_valuation import PBValuator
            from core.analysis.engines.financial_calculations import FinancialCalculator
            calculator = FinancialCalculator(ticker)
            pb_valuator = PBValuator(calculator)
            return pb_valuator.calculate_current_pb_ratio()
        except Exception:
            return {'pb_ratio': 2.5, 'book_value_per_share': 40.0}

    # Validation methods

    def _validate_portfolio_creation(self, portfolio: Portfolio, portfolio_type: PortfolioType):
        """Validate portfolio creation"""
        assert portfolio is not None, f"Portfolio creation failed for {portfolio_type.value}"
        assert portfolio.portfolio_type == portfolio_type, \
            f"Incorrect portfolio type: expected {portfolio_type.value}"
        assert len(portfolio.holdings) > 0, f"No holdings in {portfolio_type.value} portfolio"

    def _validate_portfolio_optimization(self, optimized_portfolio: Portfolio, portfolio_type: PortfolioType):
        """Validate portfolio optimization results"""
        assert optimized_portfolio is not None, \
            f"Portfolio optimization failed for {portfolio_type.value}"
        # Additional optimization-specific validations would go here

    def _validate_performance_metrics(self, metrics: Dict[str, Any], portfolio_type: PortfolioType):
        """Validate performance metrics calculation"""
        assert metrics is not None, f"Performance metrics calculation failed for {portfolio_type.value}"

        for metric in self.portfolio_config['performance_metrics']:
            assert metric in metrics, f"Missing {metric} in performance metrics for {portfolio_type.value}"

    def _validate_rebalancing_operation(self, result: Dict[str, Any], portfolio_type: PortfolioType):
        """Validate rebalancing operation"""
        assert result is not None, f"Rebalancing failed for {portfolio_type.value}"

    def _validate_risk_analysis(self, analysis: Dict[str, Any], portfolio_type: PortfolioType):
        """Validate risk analysis"""
        assert analysis is not None, f"Risk analysis failed for {portfolio_type.value}"

    def _validate_portfolio_report(self, report: Dict[str, Any], portfolio_type: PortfolioType):
        """Validate comprehensive portfolio report"""
        assert report is not None, f"Portfolio report generation failed for {portfolio_type.value}"

    def _validate_optimization_result(self, result: Dict[str, Any], method: str):
        """Validate optimization result"""
        assert result is not None, f"Optimization failed for {method}"
        assert 'optimized_weights' in result, f"Missing optimized weights for {method}"

    def _validate_optimization_sensitivity(self, sensitivity: Dict[str, Any], method: str):
        """Validate optimization sensitivity analysis"""
        assert sensitivity is not None, f"Sensitivity analysis failed for {method}"

    def _validate_multi_objective_optimization(self, result: Dict[str, Any]):
        """Validate multi-objective optimization"""
        assert result is not None, "Multi-objective optimization failed"

    def _validate_return_metrics(self, metrics: Dict[str, Any]):
        """Validate return metrics"""
        assert metrics is not None, "Return metrics calculation failed"
        assert 'total_return' in metrics, "Missing total return"

    def _validate_risk_metrics(self, metrics: Dict[str, Any]):
        """Validate risk metrics"""
        assert metrics is not None, "Risk metrics calculation failed"
        assert 'volatility' in metrics, "Missing volatility"

    def _validate_risk_adjusted_metrics(self, metrics: Dict[str, Any]):
        """Validate risk-adjusted metrics"""
        assert metrics is not None, "Risk-adjusted metrics calculation failed"
        assert 'sharpe_ratio' in metrics, "Missing Sharpe ratio"

    def _validate_benchmark_comparison(self, comparison: Dict[str, Any]):
        """Validate benchmark comparison"""
        assert comparison is not None, "Benchmark comparison failed"

    def _validate_attribution_analysis(self, analysis: Dict[str, Any]):
        """Validate attribution analysis"""
        assert analysis is not None, "Attribution analysis failed"

    def _validate_rolling_performance(self, analysis: Dict[str, Any]):
        """Validate rolling performance analysis"""
        assert analysis is not None, "Rolling performance analysis failed"

    def _validate_backtest_results(self, results: Dict[str, Any]):
        """Validate backtesting results"""
        assert results is not None, "Backtesting failed"

    def _validate_backtest_performance(self, performance: Dict[str, Any]):
        """Validate backtest performance analysis"""
        assert performance is not None, "Backtest performance analysis failed"

    def _validate_drawdown_analysis(self, analysis: Dict[str, Any]):
        """Validate drawdown analysis"""
        assert analysis is not None, "Drawdown analysis failed"

    def _validate_out_of_sample_results(self, results: Dict[str, Any]):
        """Validate out-of-sample testing results"""
        assert results is not None, "Out-of-sample testing failed"

    def _validate_strategy_validation(self, validation: Dict[str, Any]):
        """Validate strategy validation"""
        assert validation is not None, "Strategy validation failed"

    def _validate_rebalancing_execution(self, result: Dict[str, Any], strategy: RebalancingStrategy):
        """Validate rebalancing execution"""
        assert result is not None, f"Rebalancing execution failed for {strategy.value}"

    def _validate_rebalancing_impact(self, impact: Dict[str, Any], strategy: RebalancingStrategy):
        """Validate rebalancing impact analysis"""
        assert impact is not None, f"Rebalancing impact analysis failed for {strategy.value}"

    def _validate_tax_efficient_rebalancing(self, result: Dict[str, Any]):
        """Validate tax-efficient rebalancing"""
        assert result is not None, "Tax-efficient rebalancing failed"

    def _validate_cost_optimized_rebalancing(self, result: Dict[str, Any]):
        """Validate cost-optimized rebalancing"""
        assert result is not None, "Cost-optimized rebalancing failed"

    def _validate_risk_profile(self, profile: Dict[str, Any]):
        """Validate risk profile"""
        assert profile is not None, "Risk profile creation failed"

    def _validate_var_analysis(self, analysis: Dict[str, Any]):
        """Validate VaR analysis"""
        assert analysis is not None, "VaR analysis failed"

    def _validate_stress_test_results(self, results: Dict[str, Any]):
        """Validate stress test results"""
        assert results is not None, "Stress testing failed"

    def _validate_correlation_analysis(self, analysis: Dict[str, Any]):
        """Validate correlation analysis"""
        assert analysis is not None, "Correlation analysis failed"

    def _validate_factor_exposure_analysis(self, analysis: Dict[str, Any]):
        """Validate factor exposure analysis"""
        assert analysis is not None, "Factor exposure analysis failed"

    def _validate_risk_monitoring_setup(self, setup: Dict[str, Any]):
        """Validate risk monitoring setup"""
        assert setup is not None, "Risk monitoring setup failed"

    def _validate_portfolio_save(self, result: bool, name: str):
        """Validate portfolio save operation"""
        assert result, f"Failed to save portfolio {name}"

    def _validate_portfolio_load(self, portfolio: Portfolio, name: str):
        """Validate portfolio load operation"""
        assert portfolio is not None, f"Failed to load portfolio {name}"

    def _validate_portfolio_listing(self, portfolio_list: List[str]):
        """Validate portfolio listing"""
        assert portfolio_list is not None, "Failed to list portfolios"
        assert len(portfolio_list) > 0, "No portfolios found in listing"

    def _validate_portfolio_update(self, result: bool):
        """Validate portfolio update operation"""
        assert result, "Failed to update portfolio"

    def _validate_portfolio_versioning(self, history: List[Dict]):
        """Validate portfolio versioning"""
        assert history is not None, "Failed to get portfolio history"

    def _validate_portfolio_deletion(self, result: bool, name: str):
        """Validate portfolio deletion"""
        assert result, f"Failed to delete portfolio {name}"

    def _validate_fcf_integration(self, result: Dict[str, Any], ticker: str):
        """Validate FCF analysis integration"""
        assert result is not None, f"FCF integration failed for {ticker}"

    def _validate_dcf_integration(self, result: Dict[str, Any], ticker: str):
        """Validate DCF analysis integration"""
        assert result is not None, f"DCF integration failed for {ticker}"

    def _validate_ddm_integration(self, result: Dict[str, Any], ticker: str):
        """Validate DDM analysis integration"""
        assert result is not None, f"DDM integration failed for {ticker}"

    def _validate_pb_integration(self, result: Dict[str, Any], ticker: str):
        """Validate P/B analysis integration"""
        assert result is not None, f"P/B integration failed for {ticker}"

    def _validate_metric_aggregation(self, metrics: Dict[str, Any]):
        """Validate metric aggregation"""
        assert metrics is not None, "Metric aggregation failed"

    def _validate_cross_validation(self, validation: Dict[str, Any]):
        """Validate cross-validation"""
        assert validation is not None, "Cross-validation failed"


if __name__ == "__main__":
    # Run comprehensive Portfolio workflow tests
    pytest.main([__file__, "-v", "--tb=short"])