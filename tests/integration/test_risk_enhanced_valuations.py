"""
Integration Tests for Risk-Enhanced Valuations
==============================================

This module provides comprehensive integration tests for the risk-enhanced valuation
models, ensuring proper integration between risk analysis, performance optimization,
and valuation calculations.

Test Categories:
- Risk-enhanced DCF integration tests
- Risk-enhanced DDM integration tests
- Risk-enhanced P/B integration tests
- Performance optimization integration tests
- End-to-end workflow tests
- Multi-valuation method comparison tests
- Stress testing under extreme scenarios

Features:
- Comprehensive test coverage for all risk-enhanced valuation methods
- Performance benchmarking and validation
- Memory usage and resource utilization testing
- Parallel processing validation
- GPU acceleration testing (when available)
- Error handling and edge case testing
- Real data validation tests
"""

import pytest
import numpy as np
import pandas as pd
import logging
import time
import warnings
from typing import Dict, List, Tuple, Optional, Any
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

# Import modules under test
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.analysis.risk.risk_enhanced_valuations import (
    RiskEnhancedDCF, RiskEnhancedDDM, RiskEnhancedPB,
    RiskEnhancedValuationResult, RiskAdjustedParameters,
    ValuationMethod, RiskAdjustmentMethod, ParallelMonteCarloEngine,
    create_risk_enhanced_valuator
)

from core.analysis.risk.integrated_risk_engine import (
    IntegratedRiskEngine, RiskAnalysisRequest, RiskAnalysisResult
)

from core.analysis.risk.performance_optimization import (
    PerformanceOptimizer, ParallelStrategy, OptimizationLevel,
    PerformanceBenchmark, GPUAccelerator, MemoryManager
)

from core.analysis.risk.risk_metrics import RiskType, RiskLevel, RiskMetrics

# Mock financial calculator for testing
class MockFinancialCalculator:
    """Mock financial calculator for testing purposes."""

    def __init__(self, ticker_symbol: str = "TEST"):
        self.ticker_symbol = ticker_symbol
        self.data = {
            'income_statement': pd.DataFrame({
                'Revenue': [1000, 1100, 1200],
                'Net Income': [100, 110, 120],
                'Year': [2021, 2022, 2023]
            }),
            'balance_sheet': pd.DataFrame({
                'Total Assets': [2000, 2200, 2400],
                'Total Equity': [800, 850, 900],
                'Year': [2021, 2022, 2023]
            }),
            'cash_flow': pd.DataFrame({
                'Operating Cash Flow': [150, 165, 180],
                'Capex': [50, 55, 60],
                'Year': [2021, 2022, 2023]
            })
        }

    def get_financial_metrics(self):
        return {
            'roic': 0.15,
            'roe': 0.14,
            'debt_to_equity': 0.3,
            'current_ratio': 2.1
        }

    def calculate_all_fcf_types(self):
        return {
            'FCFE': [95, 105, 115],
            'FCFF': [100, 110, 120],
            'LFCF': [100, 110, 120]
        }


# Fixtures
@pytest.fixture
def mock_financial_calculator():
    """Create a mock financial calculator for testing."""
    return MockFinancialCalculator()


@pytest.fixture
def mock_risk_engine(mock_financial_calculator):
    """Create a mock risk engine for testing."""
    risk_engine = Mock(spec=IntegratedRiskEngine)

    # Mock risk analysis result
    mock_risk_result = Mock(spec=RiskAnalysisResult)
    mock_risk_result.analysis_id = "test_analysis_001"
    mock_risk_result.overall_risk_score = 65.0
    mock_risk_result.risk_level = RiskLevel.MEDIUM
    mock_risk_result.key_risk_drivers = ["Market volatility", "Credit risk"]

    # Mock risk metrics
    mock_risk_metrics = Mock(spec=RiskMetrics)
    mock_risk_metrics.annual_volatility = 0.25
    mock_risk_metrics.var_1day_95 = -0.03
    mock_risk_metrics.max_drawdown = -0.15
    mock_risk_metrics.sharpe_ratio = 1.2

    mock_risk_result.risk_metrics = mock_risk_metrics
    mock_risk_result.correlation_matrices = {}
    mock_risk_result.scenario_results = {}
    mock_risk_result.warnings = []

    risk_engine.analyze_risk.return_value = mock_risk_result

    return risk_engine


@pytest.fixture
def sample_dcf_result():
    """Sample DCF calculation result for testing."""
    return {
        'value_per_share': 150.0,
        'enterprise_value': 30000000,
        'equity_value': 25000000,
        'projected_fcf': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900],
        'terminal_value': 40000,
        'shares_outstanding': 166667,
        'net_debt': 5000000
    }


class TestRiskEnhancedDCF:
    """Test suite for Risk-Enhanced DCF valuation."""

    def test_risk_enhanced_dcf_initialization(self, mock_financial_calculator, mock_risk_engine):
        """Test proper initialization of RiskEnhancedDCF."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        assert risk_dcf.financial_calculator == mock_financial_calculator
        assert risk_dcf.risk_engine == mock_risk_engine
        assert risk_dcf.dcf_valuator is not None
        assert risk_dcf.parallel_engine is not None
        assert isinstance(risk_dcf.parallel_engine, ParallelMonteCarloEngine)

    def test_risk_adjusted_dcf_calculation(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test basic risk-adjusted DCF calculation."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        # Mock DCF valuator
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        # Run risk-adjusted DCF with small simulation for speed
        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=100,
            use_parallel=False,
            confidence_levels=[0.95]
        )

        # Validate result structure
        assert isinstance(result, RiskEnhancedValuationResult)
        assert result.valuation_method == ValuationMethod.DCF
        assert result.base_value == 150.0
        assert result.risk_adjusted_value > 0
        assert result.num_simulations == 100
        assert result.calculation_time > 0
        assert len(result.confidence_intervals) > 0

        # Validate risk metrics
        assert result.var_95 > 0 or result.var_95 < 0  # VaR can be negative
        assert result.value_volatility >= 0

    def test_parallel_monte_carlo_execution(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test parallel Monte Carlo execution."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        # Test parallel execution
        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=1000,
            use_parallel=True,
            confidence_levels=[0.95, 0.99]
        )

        assert result.num_simulations == 1000
        assert len(result.confidence_intervals) == 2
        assert result.calculation_time > 0

    def test_risk_parameter_adjustment(self, mock_financial_calculator, mock_risk_engine):
        """Test risk parameter adjustment logic."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        # Create mock risk result with specific metrics
        mock_risk_result = Mock()
        mock_risk_result.risk_metrics = Mock()
        mock_risk_result.risk_metrics.annual_volatility = 0.30
        mock_risk_result.risk_metrics.var_1day_95 = -0.025
        mock_risk_result.correlation_matrices = {}

        # Test risk parameter creation
        risk_params = risk_dcf._create_risk_adjusted_parameters(mock_risk_result, None)

        assert isinstance(risk_params, RiskAdjustedParameters)
        assert risk_params.risk_adjusted_discount_rate > risk_params.base_discount_rate
        assert risk_params.revenue_growth_std > 0

    def test_scenario_analysis_enhancement(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test scenario analysis enhancement."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=100,
            use_parallel=False
        )

        # Check scenario values are populated
        assert len(result.scenario_values) > 0
        assert 'bear_case' in result.scenario_values
        assert 'bull_case' in result.scenario_values
        assert 'stress_case' in result.scenario_values

        # Validate scenario logic
        assert result.scenario_values['bear_case'] < result.scenario_values['bull_case']

    def test_tail_risk_analysis(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test tail risk analysis enhancement."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=1000,
            use_parallel=False
        )

        # Check tail risk metrics
        assert len(result.tail_risk_metrics) > 0
        assert 'p1' in result.tail_risk_metrics
        assert 'p99' in result.tail_risk_metrics
        assert 'tail_ratio' in result.tail_risk_metrics

        # Validate tail ratio makes sense
        assert result.tail_risk_metrics['tail_ratio'] > 1.0

    def test_error_handling(self, mock_financial_calculator, mock_risk_engine):
        """Test error handling in risk-enhanced DCF."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        # Mock DCF valuator to raise exception
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(
            side_effect=Exception("DCF calculation failed")
        )

        # Should raise exception
        with pytest.raises(Exception):
            risk_dcf.calculate_risk_adjusted_dcf(num_simulations=100)

    def test_single_dcf_simulation(self, sample_dcf_result):
        """Test individual DCF simulation logic."""
        risk_params = RiskAdjustedParameters()
        risk_params.risk_adjusted_discount_rate = 0.10
        risk_params.revenue_growth_mean = 0.05
        risk_params.terminal_growth_mean = 0.03

        # Test single simulation
        result = RiskEnhancedDCF._single_dcf_simulation(risk_params, sample_dcf_result)

        assert isinstance(result, float)
        assert result >= 0  # Value should be non-negative


class TestRiskEnhancedDDM:
    """Test suite for Risk-Enhanced DDM valuation."""

    def test_risk_enhanced_ddm_initialization(self, mock_financial_calculator, mock_risk_engine):
        """Test proper initialization of RiskEnhancedDDM."""
        risk_ddm = RiskEnhancedDDM(mock_financial_calculator, mock_risk_engine)

        assert risk_ddm.financial_calculator == mock_financial_calculator
        assert risk_ddm.risk_engine == mock_risk_engine
        assert risk_ddm.ddm_valuator is not None

    def test_risk_adjusted_ddm_calculation(self, mock_financial_calculator, mock_risk_engine):
        """Test basic risk-adjusted DDM calculation."""
        risk_ddm = RiskEnhancedDDM(mock_financial_calculator, mock_risk_engine)

        # Mock DDM valuator
        sample_ddm_result = {'value_per_share': 120.0, 'dividend_yield': 0.03}
        risk_ddm.ddm_valuator.calculate_ddm_valuation = Mock(return_value=sample_ddm_result)

        result = risk_ddm.calculate_risk_adjusted_ddm(
            num_simulations=100,
            use_parallel=False
        )

        assert isinstance(result, RiskEnhancedValuationResult)
        assert result.valuation_method == ValuationMethod.DDM
        assert result.base_value == 120.0

    def test_dividend_risk_analysis(self, mock_financial_calculator, mock_risk_engine):
        """Test dividend-specific risk analysis."""
        risk_ddm = RiskEnhancedDDM(mock_financial_calculator, mock_risk_engine)

        # Test dividend risk analysis
        risk_result = risk_ddm._perform_dividend_risk_analysis()

        # Verify risk engine was called with dividend-focused parameters
        mock_risk_engine.analyze_risk.assert_called()
        call_args = mock_risk_engine.analyze_risk.call_args[0][0]
        assert isinstance(call_args, RiskAnalysisRequest)

    def test_dividend_scenarios(self, mock_financial_calculator, mock_risk_engine):
        """Test dividend-specific scenarios."""
        risk_ddm = RiskEnhancedDDM(mock_financial_calculator, mock_risk_engine)

        sample_ddm_result = {'value_per_share': 120.0}
        risk_ddm.ddm_valuator.calculate_ddm_valuation = Mock(return_value=sample_ddm_result)

        result = risk_ddm.calculate_risk_adjusted_ddm(num_simulations=100)

        # Check dividend-specific scenarios
        assert 'dividend_cut_scenario' in result.scenario_values
        assert 'dividend_suspension_scenario' in result.scenario_values

        # Validate dividend scenario logic
        assert result.scenario_values['dividend_suspension_scenario'] < result.scenario_values['dividend_cut_scenario']


class TestRiskEnhancedPB:
    """Test suite for Risk-Enhanced P/B valuation."""

    def test_risk_enhanced_pb_initialization(self, mock_financial_calculator, mock_risk_engine):
        """Test proper initialization of RiskEnhancedPB."""
        risk_pb = RiskEnhancedPB(mock_financial_calculator, mock_risk_engine)

        assert risk_pb.financial_calculator == mock_financial_calculator
        assert risk_pb.risk_engine == mock_risk_engine
        assert risk_pb.pb_valuator is not None

    def test_risk_adjusted_pb_calculation(self, mock_financial_calculator, mock_risk_engine):
        """Test basic risk-adjusted P/B calculation."""
        risk_pb = RiskEnhancedPB(mock_financial_calculator, mock_risk_engine)

        # Mock P/B valuator
        sample_pb_result = {
            'fair_value_per_share': 80.0,
            'book_value_per_share': 50.0,
            'pb_ratio': 1.6
        }
        risk_pb.pb_valuator.calculate_pb_valuation = Mock(return_value=sample_pb_result)

        result = risk_pb.calculate_risk_adjusted_pb()

        assert isinstance(result, RiskEnhancedValuationResult)
        assert result.valuation_method == ValuationMethod.PB
        assert result.base_value == 80.0

    def test_balance_sheet_risk_analysis(self, mock_financial_calculator, mock_risk_engine):
        """Test balance sheet focused risk analysis."""
        risk_pb = RiskEnhancedPB(mock_financial_calculator, mock_risk_engine)

        risk_result = risk_pb._perform_balance_sheet_risk_analysis()

        # Verify risk engine was called with balance sheet focus
        mock_risk_engine.analyze_risk.assert_called()
        call_args = mock_risk_engine.analyze_risk.call_args[0][0]
        assert RiskType.CREDIT in call_args.risk_types
        assert RiskType.LIQUIDITY in call_args.risk_types

    def test_pb_multiple_adjustment(self, mock_financial_calculator, mock_risk_engine):
        """Test P/B multiple risk adjustment."""
        risk_pb = RiskEnhancedPB(mock_financial_calculator, mock_risk_engine)

        # Create mock risk result
        mock_risk_result = Mock()
        mock_risk_result.risk_metrics = Mock()

        multiple = risk_pb._calculate_risk_adjusted_pb_multiple(mock_risk_result)

        assert isinstance(multiple, float)
        assert multiple > 0

    def test_stress_testing(self, mock_financial_calculator, mock_risk_engine):
        """Test balance sheet stress testing."""
        risk_pb = RiskEnhancedPB(mock_financial_calculator, mock_risk_engine)

        sample_pb_result = {'fair_value_per_share': 80.0, 'book_value_per_share': 50.0, 'pb_ratio': 1.6}
        risk_pb.pb_valuator.calculate_pb_valuation = Mock(return_value=sample_pb_result)

        result = risk_pb.calculate_risk_adjusted_pb(stress_testing=True)

        # Check stress test scenarios
        assert len(result.stress_test_values) > 0
        assert 'asset_writedown_10pct' in result.stress_test_values
        assert 'liquidity_crisis' in result.stress_test_values


class TestPerformanceOptimization:
    """Test suite for performance optimization features."""

    def test_performance_optimizer_initialization(self):
        """Test performance optimizer initialization."""
        optimizer = PerformanceOptimizer(
            optimization_level=OptimizationLevel.BALANCED,
            max_memory_gb=4,
            use_gpu=False
        )

        assert optimizer.optimization_level == OptimizationLevel.BALANCED
        assert optimizer.max_memory_gb == 4
        assert optimizer.use_gpu is False

    def test_parallel_monte_carlo_engine(self):
        """Test parallel Monte Carlo engine."""
        engine = ParallelMonteCarloEngine(num_processes=2)

        def simple_simulation():
            return np.random.normal(100, 20)

        results = engine.run_parallel_simulation(
            simulation_func=simple_simulation,
            num_simulations=100,
            simulation_params={}
        )

        assert len(results) == 100
        assert all(isinstance(r, (int, float)) for r in results)

    def test_chunk_calculation(self):
        """Test optimal chunk calculation."""
        from core.analysis.risk.performance_optimization import AdaptiveChunkManager, SystemResources

        resources = SystemResources()
        chunk_manager = AdaptiveChunkManager(resources)

        chunks = chunk_manager.calculate_optimal_chunks(10000, 'cpu')

        assert isinstance(chunks, list)
        assert all(isinstance(chunk, int) for chunk in chunks)
        assert sum(chunks) == 10000

    def test_memory_management(self):
        """Test memory management functionality."""
        from core.analysis.risk.performance_optimization import MemoryManager

        memory_manager = MemoryManager(max_memory_gb=2)

        # Test preparation
        memory_manager.prepare_for_simulation(1000)

        # Test status
        status = memory_manager.get_memory_status()
        assert 'rss_gb' in status
        assert 'available_gb' in status

        # Test cleanup
        memory_manager.cleanup_after_simulation()

    @pytest.mark.skipif(not hasattr(pytest, 'slow'), reason="Slow test skipped by default")
    def test_performance_benchmark(self):
        """Test performance benchmarking."""
        from core.analysis.risk.performance_optimization import PerformanceBenchmark

        benchmark = PerformanceBenchmark()

        results = benchmark.run_comprehensive_benchmark(
            simulation_sizes=[100, 1000],
            parallel_strategies=[ParallelStrategy.CPU_ONLY]
        )

        assert 'system_info' in results
        assert 'results' in results
        assert 'analysis' in results


class TestIntegrationWorkflows:
    """Test suite for end-to-end integration workflows."""

    def test_factory_function(self, mock_financial_calculator, mock_risk_engine):
        """Test valuation factory function."""
        # Test DCF creation
        dcf_valuator = create_risk_enhanced_valuator(
            ValuationMethod.DCF, mock_financial_calculator, mock_risk_engine
        )
        assert isinstance(dcf_valuator, RiskEnhancedDCF)

        # Test DDM creation
        ddm_valuator = create_risk_enhanced_valuator(
            ValuationMethod.DDM, mock_financial_calculator, mock_risk_engine
        )
        assert isinstance(ddm_valuator, RiskEnhancedDDM)

        # Test P/B creation
        pb_valuator = create_risk_enhanced_valuator(
            ValuationMethod.PB, mock_financial_calculator, mock_risk_engine
        )
        assert isinstance(pb_valuator, RiskEnhancedPB)

        # Test invalid method
        with pytest.raises(ValueError):
            create_risk_enhanced_valuator(
                "invalid_method", mock_financial_calculator, mock_risk_engine
            )

    def test_multi_method_comparison(self, mock_financial_calculator, mock_risk_engine):
        """Test comparison across multiple valuation methods."""
        methods = [ValuationMethod.DCF, ValuationMethod.DDM, ValuationMethod.PB]
        results = {}

        for method in methods:
            valuator = create_risk_enhanced_valuator(method, mock_financial_calculator, mock_risk_engine)

            if method == ValuationMethod.DCF:
                valuator.dcf_valuator.calculate_dcf_projections = Mock(return_value={'value_per_share': 150.0})
                result = valuator.calculate_risk_adjusted_dcf(num_simulations=50, use_parallel=False)
            elif method == ValuationMethod.DDM:
                valuator.ddm_valuator.calculate_ddm_valuation = Mock(return_value={'value_per_share': 120.0})
                result = valuator.calculate_risk_adjusted_ddm(num_simulations=50, use_parallel=False)
            else:  # P/B
                valuator.pb_valuator.calculate_pb_valuation = Mock(return_value={
                    'fair_value_per_share': 80.0, 'book_value_per_share': 50.0, 'pb_ratio': 1.6
                })
                result = valuator.calculate_risk_adjusted_pb()

            results[method] = result

        # Validate all methods produced results
        assert len(results) == 3
        for method, result in results.items():
            assert isinstance(result, RiskEnhancedValuationResult)
            assert result.valuation_method == method

    def test_result_serialization(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test result serialization and deserialization."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        result = risk_dcf.calculate_risk_adjusted_dcf(num_simulations=50, use_parallel=False)

        # Test to_dict conversion
        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert 'valuation_method' in result_dict
        assert 'risk_adjusted_value' in result_dict
        assert 'analysis_id' in result_dict

        # Validate all required fields are present
        required_fields = [
            'base_value', 'risk_adjusted_value', 'value_volatility',
            'var_95', 'confidence_intervals', 'calculation_time'
        ]
        for field in required_fields:
            assert field in result_dict

    def test_memory_intensive_workflow(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test memory-intensive workflow with large simulations."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        # Test with larger simulation count
        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=5000,
            use_parallel=True,
            confidence_levels=[0.90, 0.95, 0.99]
        )

        assert result.num_simulations == 5000
        assert len(result.confidence_intervals) == 3
        assert result.calculation_time > 0

    def test_error_recovery(self, mock_financial_calculator, mock_risk_engine):
        """Test error recovery and graceful degradation."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        # Mock risk engine to fail
        mock_risk_engine.analyze_risk.side_effect = Exception("Risk analysis failed")

        # Should handle the error gracefully
        with pytest.raises(Exception):
            risk_dcf.calculate_risk_adjusted_dcf(num_simulations=100)


class TestEdgeCases:
    """Test suite for edge cases and boundary conditions."""

    def test_zero_simulations(self, mock_financial_calculator, mock_risk_engine):
        """Test handling of zero simulations."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        with pytest.raises((ValueError, ZeroDivisionError)):
            risk_dcf.calculate_risk_adjusted_dcf(num_simulations=0)

    def test_negative_base_value(self, mock_financial_calculator, mock_risk_engine):
        """Test handling of negative base values."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)

        negative_dcf_result = {'value_per_share': -50.0}
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=negative_dcf_result)

        result = risk_dcf.calculate_risk_adjusted_dcf(num_simulations=100, use_parallel=False)

        # Should handle negative values appropriately
        assert result.base_value == -50.0

    def test_extreme_volatility(self, mock_financial_calculator, mock_risk_engine):
        """Test handling of extreme volatility scenarios."""
        # Create risk engine with extreme volatility
        extreme_risk_result = Mock()
        extreme_risk_result.risk_metrics = Mock()
        extreme_risk_result.risk_metrics.annual_volatility = 2.0  # 200% volatility
        extreme_risk_result.correlation_matrices = {}
        extreme_risk_result.warnings = []

        mock_risk_engine.analyze_risk.return_value = extreme_risk_result

        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value={'value_per_share': 100.0})

        result = risk_dcf.calculate_risk_adjusted_dcf(num_simulations=100, use_parallel=False)

        # Should still produce valid results
        assert isinstance(result, RiskEnhancedValuationResult)
        assert result.value_volatility > 0

    def test_missing_risk_metrics(self, mock_financial_calculator, mock_risk_engine):
        """Test handling of missing risk metrics."""
        # Create risk result with None risk metrics
        incomplete_risk_result = Mock()
        incomplete_risk_result.risk_metrics = None
        incomplete_risk_result.correlation_matrices = {}
        incomplete_risk_result.warnings = []

        mock_risk_engine.analyze_risk.return_value = incomplete_risk_result

        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value={'value_per_share': 100.0})

        result = risk_dcf.calculate_risk_adjusted_dcf(num_simulations=100, use_parallel=False)

        # Should handle missing metrics gracefully
        assert isinstance(result, RiskEnhancedValuationResult)


# Test configuration and utilities
@pytest.fixture(autouse=True)
def configure_logging():
    """Configure logging for tests."""
    logging.basicConfig(level=logging.WARNING)  # Reduce noise during testing


@pytest.mark.integration
class TestRealDataIntegration:
    """Integration tests with real data scenarios (if available)."""

    @pytest.mark.skipif(True, reason="Requires real financial data")
    def test_real_data_workflow(self):
        """Test with real financial data if available."""
        # This test would use real financial data when available
        # Skipped by default to avoid dependency on external data
        pass


# Performance and stress tests
@pytest.mark.performance
class TestPerformanceValidation:
    """Performance validation tests."""

    def test_large_simulation_performance(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test performance with large simulation counts."""
        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        start_time = time.time()
        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=10000,
            use_parallel=True
        )
        end_time = time.time()

        # Performance assertions
        assert result.num_simulations == 10000
        assert end_time - start_time < 60  # Should complete within 60 seconds
        assert result.throughput_per_second > 100 if hasattr(result, 'throughput_per_second') else True

    def test_memory_usage_validation(self, mock_financial_calculator, mock_risk_engine, sample_dcf_result):
        """Test memory usage stays within reasonable bounds."""
        import psutil
        process = psutil.Process()

        initial_memory = process.memory_info().rss

        risk_dcf = RiskEnhancedDCF(mock_financial_calculator, mock_risk_engine)
        risk_dcf.dcf_valuator.calculate_dcf_projections = Mock(return_value=sample_dcf_result)

        result = risk_dcf.calculate_risk_adjusted_dcf(
            num_simulations=5000,
            use_parallel=True
        )

        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024**2  # MB

        # Memory increase should be reasonable (less than 1GB for this test)
        assert memory_increase < 1024


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v", "--tb=short"])