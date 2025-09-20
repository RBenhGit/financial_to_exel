"""
Tests for Portfolio Optimization Algorithms
===========================================

Comprehensive tests for the portfolio optimization system including:
- Mean-Variance Optimization
- Risk Parity allocation
- Black-Litterman model
- Constraint handling
- Efficient frontier calculation
- Integration with portfolio models
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch
from datetime import datetime, date

from core.analysis.portfolio.portfolio_optimization import (
    PortfolioOptimizer,
    OptimizationObjective,
    OptimizationMethod,
    OptimizationConstraints,
    OptimizationResult,
    create_sample_optimization_data,
    create_optimization_constraints_from_portfolio,
    apply_optimization_to_portfolio
)

from core.analysis.portfolio.black_litterman import (
    BlackLittermanOptimizer,
    BlackLittermanInputs,
    InvestorView,
    ViewType,
    create_absolute_view,
    create_relative_view,
    create_sample_bl_optimization
)

from core.analysis.portfolio.portfolio_models import (
    Portfolio,
    PortfolioHolding,
    PortfolioType,
    PositionSizingMethod,
    create_sample_portfolio
)


class TestPortfolioOptimizer:
    """Test suite for PortfolioOptimizer class"""

    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample optimization data"""
        return create_sample_optimization_data()

    @pytest.fixture
    def optimizer(self):
        """Fixture providing PortfolioOptimizer instance"""
        return PortfolioOptimizer(risk_free_rate=0.02)

    def test_optimizer_initialization(self, optimizer):
        """Test optimizer initialization"""
        assert optimizer.risk_free_rate == 0.02
        assert optimizer.estimation_window == 252
        assert optimizer.confidence_level == 0.95

    def test_equal_weight_optimization(self, optimizer, sample_data):
        """Test equal weight allocation"""
        tickers, expected_returns, covariance_matrix = sample_data

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.EQUAL_WEIGHT
        )

        assert result.success
        assert result.objective == OptimizationObjective.EQUAL_WEIGHT
        assert len(result.weights) == len(tickers)

        # Check all weights are equal (approximately)
        expected_weight = 1.0 / len(tickers)
        for weight in result.weights.values():
            assert abs(weight - expected_weight) < 1e-6

        # Check weights sum to 1
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6

    def test_max_sharpe_optimization(self, optimizer, sample_data):
        """Test maximum Sharpe ratio optimization"""
        tickers, expected_returns, covariance_matrix = sample_data

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE
        )

        assert result.success
        assert result.objective == OptimizationObjective.MAX_SHARPE
        assert result.expected_return is not None
        assert result.expected_volatility is not None
        assert result.sharpe_ratio is not None
        assert result.sharpe_ratio > 0  # Should be positive with positive expected returns

        # Check weights sum to 1
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6

    def test_min_volatility_optimization(self, optimizer, sample_data):
        """Test minimum volatility optimization"""
        tickers, expected_returns, covariance_matrix = sample_data

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MIN_VOLATILITY
        )

        assert result.success
        assert result.objective == OptimizationObjective.MIN_VOLATILITY
        assert result.expected_volatility is not None
        assert result.expected_volatility > 0

        # Min volatility should have lower volatility than equal weight
        equal_weight_result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.EQUAL_WEIGHT
        )

        assert result.expected_volatility <= equal_weight_result.expected_volatility

    def test_risk_parity_optimization(self, optimizer, sample_data):
        """Test risk parity allocation"""
        tickers, expected_returns, covariance_matrix = sample_data

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.RISK_PARITY
        )

        assert result.success
        assert result.objective == OptimizationObjective.RISK_PARITY
        assert result.iterations > 0  # Should require iterations

        # Check weights sum to 1
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6

        # Risk contributions should be approximately equal
        if result.risk_contribution:
            risk_contribs = list(result.risk_contribution.values())
            # Check that risk contributions are reasonably similar
            max_contrib = max(risk_contribs)
            min_contrib = min(risk_contribs)
            ratio = max_contrib / min_contrib if min_contrib > 0 else float('inf')
            assert ratio < 3.0  # Allow some deviation but not too much

    def test_optimization_with_constraints(self, optimizer, sample_data):
        """Test optimization with position constraints"""
        tickers, expected_returns, covariance_matrix = sample_data

        constraints = OptimizationConstraints(
            min_weight=0.05,  # Minimum 5% per position
            max_weight=0.40,  # Maximum 40% per position
            max_concentration=0.35
        )

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE,
            constraints=constraints
        )

        assert result.success

        # Check constraint compliance
        for weight in result.weights.values():
            assert weight >= constraints.min_weight - 1e-6
            assert weight <= constraints.max_weight + 1e-6

        max_weight = max(result.weights.values())
        assert max_weight <= constraints.max_concentration + 1e-6

    def test_efficient_frontier_calculation(self, optimizer, sample_data):
        """Test efficient frontier calculation"""
        tickers, expected_returns, covariance_matrix = sample_data

        efficient_portfolios = optimizer.calculate_efficient_frontier(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            num_points=10
        )

        assert len(efficient_portfolios) > 0
        assert len(efficient_portfolios) <= 10

        # Check that portfolios are ordered by return
        returns = [p.expected_return for p in efficient_portfolios if p.expected_return is not None]
        assert returns == sorted(returns)

        # Check that all portfolios are valid
        for portfolio in efficient_portfolios:
            assert portfolio.success
            assert abs(sum(portfolio.weights.values()) - 1.0) < 1e-6
            assert portfolio.expected_return is not None
            assert portfolio.expected_volatility is not None

    def test_input_validation(self, optimizer):
        """Test input validation"""
        # Test with empty tickers
        result = optimizer.optimize_portfolio(
            tickers=[],
            expected_returns={},
            covariance_matrix=np.array([]),
            objective=OptimizationObjective.EQUAL_WEIGHT
        )
        assert not result.success

        # Test with mismatched dimensions
        result = optimizer.optimize_portfolio(
            tickers=['A', 'B'],
            expected_returns={'A': 0.1},  # Missing B
            covariance_matrix=np.array([[0.1, 0.05], [0.05, 0.1]]),
            objective=OptimizationObjective.EQUAL_WEIGHT
        )
        assert not result.success

    def test_portfolio_metrics_calculation(self, optimizer, sample_data):
        """Test calculation of portfolio metrics"""
        tickers, expected_returns, covariance_matrix = sample_data

        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE
        )

        assert result.success
        assert result.expected_return is not None
        assert result.expected_volatility is not None
        assert result.sharpe_ratio is not None

        # Check that Sharpe ratio calculation is correct
        expected_sharpe = (result.expected_return - optimizer.risk_free_rate) / result.expected_volatility
        assert abs(result.sharpe_ratio - expected_sharpe) < 1e-6

        # Check risk and return contributions
        assert result.risk_contribution is not None
        assert result.return_contribution is not None
        assert len(result.risk_contribution) == len(tickers)
        assert len(result.return_contribution) == len(tickers)


class TestBlackLittermanOptimizer:
    """Test suite for Black-Litterman optimization"""

    @pytest.fixture
    def sample_bl_data(self):
        """Fixture providing sample Black-Litterman data"""
        return create_sample_bl_optimization()

    @pytest.fixture
    def bl_optimizer(self):
        """Fixture providing BlackLittermanOptimizer instance"""
        return BlackLittermanOptimizer()

    def test_bl_optimizer_initialization(self, bl_optimizer):
        """Test Black-Litterman optimizer initialization"""
        assert bl_optimizer.tickers == []
        assert bl_optimizer.n_assets == 0

    def test_create_absolute_view(self):
        """Test creation of absolute views"""
        view = create_absolute_view('AAPL', 0.15, confidence=0.8)

        assert view.view_type == ViewType.ABSOLUTE
        assert view.assets == ['AAPL']
        assert view.expected_return == 0.15
        assert view.confidence == 0.8
        assert 'AAPL' in view.description

    def test_create_relative_view(self):
        """Test creation of relative views"""
        view = create_relative_view('AAPL', 'MSFT', 0.03, confidence=0.6)

        assert view.view_type == ViewType.RELATIVE
        assert view.assets == ['AAPL', 'MSFT']
        assert view.expected_return == 0.03
        assert view.confidence == 0.6
        assert 'AAPL' in view.description and 'MSFT' in view.description

    def test_bl_optimization_no_views(self, bl_optimizer, sample_bl_data):
        """Test Black-Litterman optimization without views"""
        tickers, bl_inputs = sample_bl_data

        # Remove all views
        bl_inputs.views = []

        result = bl_optimizer.optimize(tickers, bl_inputs)

        assert result.model_success
        assert len(result.implied_returns) == len(tickers)
        assert len(result.optimal_weights) == len(tickers)

        # Without views, should be close to market cap weights
        total_deviation = sum(abs(result.weight_deviations.get(ticker, 0.0)) for ticker in tickers)
        assert total_deviation < 0.1  # Small deviation allowed due to optimization

    def test_bl_optimization_with_views(self, bl_optimizer, sample_bl_data):
        """Test Black-Litterman optimization with views"""
        tickers, bl_inputs = sample_bl_data

        result = bl_optimizer.optimize(tickers, bl_inputs)

        assert result.model_success
        assert len(result.implied_returns) == len(tickers)
        assert len(result.adjusted_returns) == len(tickers)
        assert len(result.optimal_weights) == len(tickers)

        # Check that views have impact
        assert result.view_impacts is not None
        assert len(result.view_impacts) > 0

        # Adjusted returns should differ from implied returns when views are present
        total_adjustment = sum(
            abs(result.adjusted_returns.get(ticker, 0.0) - result.implied_returns.get(ticker, 0.0))
            for ticker in tickers
        )
        assert total_adjustment > 0.001  # Should have some impact

    def test_bl_portfolio_metrics(self, bl_optimizer, sample_bl_data):
        """Test Black-Litterman portfolio metrics calculation"""
        tickers, bl_inputs = sample_bl_data

        result = bl_optimizer.optimize(tickers, bl_inputs)

        assert result.model_success
        assert result.expected_return is not None
        assert result.expected_volatility is not None
        assert result.sharpe_ratio is not None
        assert result.expected_return > 0
        assert result.expected_volatility > 0

        # Check weight deviations from market cap
        assert result.market_cap_weights is not None
        assert result.weight_deviations is not None
        assert len(result.weight_deviations) == len(tickers)

    def test_view_setup_matrices(self, bl_optimizer):
        """Test setup of P, Q, Omega matrices for views"""
        tickers = ['AAPL', 'MSFT', 'GOOGL']
        views = [
            create_absolute_view('AAPL', 0.15, confidence=0.8),
            create_relative_view('MSFT', 'GOOGL', 0.02, confidence=0.6)
        ]

        P, Q, Omega = bl_optimizer._setup_views(views, tickers)

        # Check dimensions
        assert P.shape == (2, 3)  # 2 views, 3 assets
        assert Q.shape == (2,)    # 2 view returns
        assert Omega.shape == (2, 2)  # 2x2 uncertainty matrix

        # Check P matrix structure
        assert P[0, 0] == 1.0  # AAPL absolute view
        assert P[1, 1] == 1.0  # MSFT in relative view
        assert P[1, 2] == -1.0  # GOOGL in relative view

        # Check Q vector
        assert Q[0] == 0.15  # AAPL expected return
        assert Q[1] == 0.02  # Relative return

        # Check Omega diagonal (uncertainty decreases with confidence)
        assert Omega[0, 0] < Omega[1, 1]  # Higher confidence -> lower uncertainty


class TestOptimizationConstraints:
    """Test suite for optimization constraints"""

    def test_constraint_creation(self):
        """Test constraint object creation"""
        constraints = OptimizationConstraints(
            min_weight=0.05,
            max_weight=0.30,
            max_concentration=0.25,
            target_return=0.12
        )

        assert constraints.min_weight == 0.05
        assert constraints.max_weight == 0.30
        assert constraints.max_concentration == 0.25
        assert constraints.target_return == 0.12

    def test_constraint_from_portfolio(self):
        """Test creating constraints from portfolio object"""
        portfolio = create_sample_portfolio()
        constraints = create_optimization_constraints_from_portfolio(portfolio)

        assert constraints.min_weight == portfolio.min_position_weight
        assert constraints.max_weight == portfolio.max_position_weight
        assert constraints.max_concentration == portfolio.max_position_weight


class TestPortfolioIntegration:
    """Test suite for portfolio model integration"""

    def test_apply_optimization_to_portfolio(self):
        """Test applying optimization results to portfolio"""
        portfolio = create_sample_portfolio()

        # Create sample optimization result
        optimization_result = OptimizationResult(
            objective=OptimizationObjective.MAX_SHARPE,
            method=OptimizationMethod.QUADRATIC,
            success=True,
            weights={'AAPL': 0.4, 'MSFT': 0.3, 'GOOGL': 0.3},
            expected_return=0.12,
            expected_volatility=0.18,
            sharpe_ratio=0.56
        )

        updated_portfolio = apply_optimization_to_portfolio(portfolio, optimization_result)

        # Check that target weights were updated
        for holding in updated_portfolio.holdings:
            if holding.ticker in optimization_result.weights:
                expected_weight = optimization_result.weights[holding.ticker]
                assert abs(holding.target_weight - expected_weight) < 1e-6

    def test_portfolio_optimization_workflow(self):
        """Test complete portfolio optimization workflow"""
        # Create portfolio
        portfolio = create_sample_portfolio()

        # Get tickers and create simple data
        tickers = [h.ticker for h in portfolio.holdings]
        expected_returns = {ticker: 0.10 + i * 0.01 for i, ticker in enumerate(tickers)}

        # Simple covariance matrix
        n = len(tickers)
        volatilities = np.array([0.20] * n)
        correlation = 0.5
        corr_matrix = np.full((n, n), correlation)
        np.fill_diagonal(corr_matrix, 1.0)
        covariance_matrix = np.outer(volatilities, volatilities) * corr_matrix

        # Create constraints from portfolio
        constraints = create_optimization_constraints_from_portfolio(portfolio)

        # Optimize
        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE,
            constraints=constraints
        )

        assert result.success

        # Apply to portfolio
        updated_portfolio = apply_optimization_to_portfolio(portfolio, result)

        # Check portfolio was updated
        assert updated_portfolio.portfolio_metrics.deviation_from_targets >= 0


class TestOptimizationEdgeCases:
    """Test suite for edge cases and error handling"""

    def test_singular_covariance_matrix(self):
        """Test handling of singular covariance matrix"""
        tickers = ['A', 'B', 'C']
        expected_returns = {'A': 0.1, 'B': 0.1, 'C': 0.1}

        # Create singular matrix (rank deficient)
        covariance_matrix = np.array([
            [0.04, 0.02, 0.02],
            [0.02, 0.01, 0.01],  # This row is 0.5 * first row
            [0.02, 0.01, 0.01]   # This row is identical to second row
        ])

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE
        )

        # Should handle gracefully (using pseudo-inverse)
        assert result.success

    def test_negative_expected_returns(self):
        """Test optimization with negative expected returns"""
        tickers = ['A', 'B']
        expected_returns = {'A': -0.05, 'B': -0.02}
        covariance_matrix = np.array([[0.04, 0.01], [0.01, 0.02]])

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE
        )

        # Should complete but may have negative Sharpe ratio
        assert result.success
        assert result.sharpe_ratio is not None

    def test_extreme_constraints(self):
        """Test optimization with extreme constraints"""
        tickers = ['A', 'B', 'C']
        expected_returns = {'A': 0.1, 'B': 0.12, 'C': 0.08}
        covariance_matrix = np.eye(3) * 0.04

        # Impossible constraints
        constraints = OptimizationConstraints(
            min_weight=0.4,  # Minimum 40% each
            max_weight=0.5   # Maximum 50% each - impossible with 3 assets
        )

        optimizer = PortfolioOptimizer()
        result = optimizer.optimize_portfolio(
            tickers=tickers,
            expected_returns=expected_returns,
            covariance_matrix=covariance_matrix,
            objective=OptimizationObjective.MAX_SHARPE,
            constraints=constraints
        )

        # Should complete but may violate constraints
        assert result.success
        # Constraint violations should be detected
        assert not result.constraints_satisfied or result.constraint_violations


@pytest.mark.integration
class TestOptimizationIntegration:
    """Integration tests for optimization system"""

    def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline"""
        # Get sample data
        tickers, expected_returns, covariance_matrix = create_sample_optimization_data()

        # Test multiple optimization methods
        optimizer = PortfolioOptimizer()

        objectives_to_test = [
            OptimizationObjective.EQUAL_WEIGHT,
            OptimizationObjective.RISK_PARITY,
            OptimizationObjective.MIN_VOLATILITY,
            OptimizationObjective.MAX_SHARPE
        ]

        results = {}

        for objective in objectives_to_test:
            result = optimizer.optimize_portfolio(
                tickers=tickers,
                expected_returns=expected_returns,
                covariance_matrix=covariance_matrix,
                objective=objective
            )

            assert result.success, f"Optimization failed for {objective.value}: {result.message}"
            results[objective] = result

        # Compare results
        equal_weight = results[OptimizationObjective.EQUAL_WEIGHT]
        max_sharpe = results[OptimizationObjective.MAX_SHARPE]
        min_vol = results[OptimizationObjective.MIN_VOLATILITY]

        # Max Sharpe should have highest Sharpe ratio
        assert max_sharpe.sharpe_ratio >= equal_weight.sharpe_ratio
        assert max_sharpe.sharpe_ratio >= min_vol.sharpe_ratio

        # Min volatility should have lowest volatility
        assert min_vol.expected_volatility <= equal_weight.expected_volatility
        assert min_vol.expected_volatility <= max_sharpe.expected_volatility

    def test_black_litterman_integration(self):
        """Test Black-Litterman integration with standard optimization"""
        from core.analysis.portfolio.black_litterman import integrate_black_litterman_with_portfolio

        # Get sample data
        tickers, bl_inputs = create_sample_bl_optimization()

        # Standard optimizer
        standard_optimizer = PortfolioOptimizer()

        # Integrate Black-Litterman
        result = integrate_black_litterman_with_portfolio(
            standard_optimizer,
            tickers,
            bl_inputs
        )

        assert result.success
        assert result.weights is not None
        assert len(result.weights) == len(tickers)
        assert abs(sum(result.weights.values()) - 1.0) < 1e-6

if __name__ == "__main__":
    pytest.main([__file__, "-v"])