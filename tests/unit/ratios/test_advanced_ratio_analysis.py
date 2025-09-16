"""
Test Suite for Advanced Ratio Analysis Module
=============================================

Comprehensive tests for the advanced ratio analysis components including
industry benchmarks, statistical analysis, peer comparison, and main analyzer.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile
import shutil

# Import the components to test
from core.analysis.ratios import (
    IndustryBenchmarkManager,
    RatioStatisticalAnalysis,
    PeerComparisonEngine,
    AdvancedRatioAnalyzer
)
from core.analysis.ratios.industry_benchmarks import IndustryBenchmark, IndustryProfile
from core.analysis.ratios.statistical_analysis import TrendAnalysis, VolatilityMetrics
from core.analysis.ratios.peer_comparison import PeerMetrics, ComparisonResult


class TestIndustryBenchmarkManager:
    """Test industry benchmark management functionality"""

    @pytest.fixture
    def temp_data_path(self):
        """Create temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def benchmark_manager(self, temp_data_path):
        """Create benchmark manager with temp data path"""
        return IndustryBenchmarkManager(temp_data_path)

    def test_initialization(self, benchmark_manager):
        """Test benchmark manager initialization"""
        assert benchmark_manager is not None
        assert len(benchmark_manager.get_available_industries()) > 0

        # Should have default industries
        industries = benchmark_manager.get_available_industries()
        assert 'Technology' in industries
        assert 'Manufacturing' in industries

    def test_get_industry_benchmark(self, benchmark_manager):
        """Test getting specific industry benchmark"""
        benchmark = benchmark_manager.get_industry_benchmark('Technology', 'roe')

        assert benchmark is not None
        assert isinstance(benchmark, IndustryBenchmark)
        assert benchmark.ratio_name == 'roe'
        assert benchmark.industry == 'Technology'
        assert benchmark.percentile_25 < benchmark.median < benchmark.percentile_75

    def test_classify_performance(self, benchmark_manager):
        """Test performance classification"""
        # Test excellent performance
        performance, percentile = benchmark_manager.classify_performance('Technology', 'roe', 25.0)
        assert performance == "excellent"
        assert percentile > 75

        # Test poor performance
        performance, percentile = benchmark_manager.classify_performance('Technology', 'roe', 5.0)
        assert performance == "poor"
        assert percentile < 25

    def test_get_peer_companies(self, benchmark_manager):
        """Test getting peer companies"""
        peers = benchmark_manager.get_peer_companies('Technology')
        assert isinstance(peers, list)
        assert len(peers) > 0
        assert 'MSFT' in peers

    def test_add_custom_benchmark(self, benchmark_manager):
        """Test adding custom benchmark"""
        custom_data = {
            'sector': 'Custom',
            'percentile_25': 10.0,
            'median': 15.0,
            'percentile_75': 20.0,
            'mean': 15.5,
            'std_deviation': 5.0,
            'sample_size': 50
        }

        benchmark_manager.add_custom_benchmark('CustomIndustry', 'custom_ratio', custom_data)

        # Verify custom benchmark was added
        benchmark = benchmark_manager.get_industry_benchmark('CustomIndustry', 'custom_ratio')
        assert benchmark is not None
        assert benchmark.median == 15.0


class TestRatioStatisticalAnalysis:
    """Test statistical analysis functionality"""

    @pytest.fixture
    def statistical_analyzer(self):
        """Create statistical analyzer"""
        return RatioStatisticalAnalysis()

    @pytest.fixture
    def sample_ratio_data(self):
        """Create sample ratio data for testing"""
        return {
            'roe': [0.12, 0.15, 0.18, 0.20, 0.22, 0.25],
            'current_ratio': [1.8, 2.0, 2.2, 2.1, 2.3, 2.4],
            'debt_to_equity': [0.6, 0.5, 0.4, 0.3, 0.35, 0.3]
        }

    @pytest.fixture
    def sample_periods(self):
        """Create sample time periods"""
        base_date = datetime(2020, 1, 1)
        return [base_date + timedelta(days=365*i) for i in range(6)]

    def test_analyze_trend_improving(self, statistical_analyzer):
        """Test trend analysis for improving trend"""
        values = [10, 12, 14, 16, 18, 20]  # Clear upward trend

        trend = statistical_analyzer.analyze_trend(values, ratio_name='test_ratio')

        assert isinstance(trend, TrendAnalysis)
        assert trend.trend_direction == "improving"
        assert trend.slope > 0
        assert trend.is_significant
        assert trend.r_squared > 0.8  # Should have high correlation

    def test_analyze_trend_declining(self, statistical_analyzer):
        """Test trend analysis for declining trend"""
        values = [20, 18, 16, 14, 12, 10]  # Clear downward trend

        trend = statistical_analyzer.analyze_trend(values, ratio_name='test_ratio')

        assert trend.trend_direction == "declining"
        assert trend.slope < 0
        assert trend.is_significant

    def test_analyze_trend_stable(self, statistical_analyzer):
        """Test trend analysis for stable values"""
        values = [15, 14.8, 15.2, 14.9, 15.1, 15.0]  # Stable around 15

        trend = statistical_analyzer.analyze_trend(values, ratio_name='test_ratio')

        assert trend.trend_direction == "stable"
        assert not trend.is_significant

    def test_analyze_volatility(self, statistical_analyzer):
        """Test volatility analysis"""
        values = [10, 15, 8, 12, 18, 9]  # High volatility

        volatility = statistical_analyzer.analyze_volatility(values, 'test_ratio')

        assert isinstance(volatility, VolatilityMetrics)
        assert volatility.standard_deviation > 0
        assert volatility.coefficient_of_variation > 0
        assert volatility.maximum_drawdown >= 0

    def test_analyze_correlation(self, statistical_analyzer, sample_ratio_data):
        """Test correlation analysis"""
        correlation_result = statistical_analyzer.analyze_correlation(sample_ratio_data)

        assert len(correlation_result.ratio_names) == 3
        assert correlation_result.correlation_matrix.shape == (3, 3)

        # Check diagonal elements are 1 (perfect self-correlation)
        np.testing.assert_array_almost_equal(
            np.diag(correlation_result.correlation_matrix),
            [1.0, 1.0, 1.0]
        )

    def test_generate_comprehensive_report(self, statistical_analyzer, sample_ratio_data, sample_periods):
        """Test comprehensive report generation"""
        report = statistical_analyzer.generate_comprehensive_report(
            sample_ratio_data, sample_periods
        )

        assert 'summary' in report
        assert 'trend_analysis' in report
        assert 'volatility_analysis' in report
        assert 'correlation_analysis' in report

        # Check summary statistics
        summary = report['summary']
        assert summary['total_ratios'] == 3
        assert 'improving_ratios' in summary
        assert 'declining_ratios' in summary

    def test_insufficient_data_handling(self, statistical_analyzer):
        """Test handling of insufficient data"""
        # Test with too little data
        values = [10, 12]  # Only 2 points

        trend = statistical_analyzer.analyze_trend(values, ratio_name='test_ratio')
        assert trend.trend_direction == "insufficient_data"
        assert not trend.is_significant

    def test_data_cleaning(self, statistical_analyzer):
        """Test data cleaning functionality"""
        # Include NaN, infinite, and extreme outliers
        values = [10, 12, float('nan'), 14, float('inf'), 100, 16, 18]

        trend = statistical_analyzer.analyze_trend(values, ratio_name='test_ratio')

        # Should still work with cleaned data
        assert trend.periods_analyzed > 0
        assert trend.periods_analyzed < len(values)  # Some data should be filtered


class TestPeerComparisonEngine:
    """Test peer comparison functionality"""

    @pytest.fixture
    def peer_engine(self):
        """Create peer comparison engine"""
        from core.analysis.ratios.industry_benchmarks import IndustryBenchmarkManager
        benchmark_manager = IndustryBenchmarkManager()
        return PeerComparisonEngine(benchmark_manager)

    @pytest.fixture
    def sample_peer_data(self):
        """Create sample peer data"""
        return {
            'PEER1': {
                'company_name': 'Peer Company 1',
                'industry': 'Technology',
                'ratios': {
                    'roe': 0.18,
                    'current_ratio': 2.2,
                    'debt_to_equity': 0.4
                }
            },
            'PEER2': {
                'company_name': 'Peer Company 2',
                'industry': 'Technology',
                'ratios': {
                    'roe': 0.22,
                    'current_ratio': 2.8,
                    'debt_to_equity': 0.3
                }
            },
            'PEER3': {
                'company_name': 'Peer Company 3',
                'industry': 'Technology',
                'ratios': {
                    'roe': 0.15,
                    'current_ratio': 1.8,
                    'debt_to_equity': 0.6
                }
            }
        }

    def test_add_peer_data(self, peer_engine, sample_peer_data):
        """Test adding peer data"""
        for ticker, data in sample_peer_data.items():
            peer_engine.add_peer_data(
                ticker=ticker,
                company_name=data['company_name'],
                industry=data['industry'],
                ratios=data['ratios']
            )

        # Verify data was added
        assert len(peer_engine._peer_data) == 3

    def test_compare_ratio(self, peer_engine, sample_peer_data):
        """Test ratio comparison"""
        peer_engine.load_peer_data_from_dict(sample_peer_data)

        # Test company with middle performance
        comparison = peer_engine.compare_ratio(
            company_ticker='TEST',
            ratio_name='roe',
            company_value=0.20,
            peer_group=['PEER1', 'PEER2', 'PEER3'],
            higher_is_better=True
        )

        assert isinstance(comparison, ComparisonResult)
        assert comparison.ratio_name == 'roe'
        assert comparison.company_value == 0.20
        assert len(comparison.peer_values) == 3
        assert 1 <= comparison.ranking <= 4  # Should be ranked somewhere
        assert 0 <= comparison.percentile_rank <= 100

    def test_comprehensive_analysis(self, peer_engine, sample_peer_data):
        """Test comprehensive peer analysis"""
        peer_engine.load_peer_data_from_dict(sample_peer_data)

        company_ratios = {
            'roe': 0.20,
            'current_ratio': 2.4,
            'debt_to_equity': 0.35
        }

        report = peer_engine.generate_comprehensive_analysis(
            company_ticker='TEST',
            company_ratios=company_ratios,
            peer_group=['PEER1', 'PEER2', 'PEER3']
        )

        assert report.company_ticker == 'TEST'
        assert len(report.ratio_comparisons) == 3
        assert report.overall_ranking is not None
        assert isinstance(report.strength_areas, list)
        assert isinstance(report.weakness_areas, list)
        assert len(report.competitive_summary) > 0

    def test_get_industry_leaders(self, peer_engine, sample_peer_data):
        """Test getting industry leaders"""
        peer_engine.load_peer_data_from_dict(sample_peer_data)

        leaders = peer_engine.get_industry_leaders('Technology', 'roe', top_n=2)

        assert len(leaders) <= 2
        assert all(isinstance(item, tuple) and len(item) == 2 for item in leaders)

        # Should be sorted by performance (higher is better for ROE)
        if len(leaders) > 1:
            assert leaders[0][1] >= leaders[1][1]

    def test_calculate_competitive_moat_score(self, peer_engine):
        """Test competitive moat score calculation"""
        company_ratios = {
            'roe': 0.25,  # Excellent
            'gross_margin': 0.50,  # Excellent
            'operating_margin': 0.25,  # Excellent
            'current_ratio': 2.0,  # Good
            'debt_to_equity': 0.3,  # Good
        }

        moat_analysis = peer_engine.calculate_competitive_moat_score('TEST', company_ratios)

        assert 'moat_score' in moat_analysis
        assert 'moat_strength' in moat_analysis
        assert 'contributing_factors' in moat_analysis
        assert 'weakness_factors' in moat_analysis

        # Should have high score with these good ratios
        assert moat_analysis['moat_score'] > 60
        assert moat_analysis['moat_strength'] in ['Moderate', 'Strong', 'Very Strong']


class TestAdvancedRatioAnalyzer:
    """Test the main advanced ratio analyzer"""

    @pytest.fixture
    def temp_data_path(self):
        """Create temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def ratio_analyzer(self, temp_data_path):
        """Create advanced ratio analyzer"""
        return AdvancedRatioAnalyzer(temp_data_path)

    @pytest.fixture
    def sample_company_data(self):
        """Create sample company data"""
        return {
            'current_ratios': {
                'roe': 0.20,
                'current_ratio': 2.2,
                'debt_to_equity': 0.4,
                'gross_margin': 0.45
            },
            'historical_ratios': {
                'roe': [0.15, 0.17, 0.18, 0.19, 0.20],
                'current_ratio': [1.8, 2.0, 2.1, 2.2, 2.2],
                'debt_to_equity': [0.6, 0.5, 0.45, 0.42, 0.4],
                'gross_margin': [0.40, 0.42, 0.43, 0.44, 0.45]
            },
            'periods': [
                datetime(2020, 1, 1),
                datetime(2021, 1, 1),
                datetime(2022, 1, 1),
                datetime(2023, 1, 1),
                datetime(2024, 1, 1)
            ]
        }

    def test_analyze_company_comprehensive(self, ratio_analyzer, sample_company_data):
        """Test comprehensive company analysis"""
        report = ratio_analyzer.analyze_company(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            current_ratios=sample_company_data['current_ratios'],
            historical_ratios=sample_company_data['historical_ratios'],
            periods=sample_company_data['periods']
        )

        # Verify report structure
        assert report.company_ticker == 'TEST'
        assert report.company_name == 'Test Company'
        assert report.industry == 'Technology'
        assert len(report.enhanced_ratios) == 4

        # Check overall health calculation
        assert 'score' in report.overall_financial_health
        assert 'grade' in report.overall_financial_health
        assert 0 <= report.overall_financial_health['score'] <= 100

        # Check strategic insights
        assert isinstance(report.strategic_insights, list)

        # Check risk assessment
        assert 'risk_level' in report.risk_assessment
        assert 'risk_factors' in report.risk_assessment

    def test_enhanced_ratio_analysis(self, ratio_analyzer, sample_company_data):
        """Test individual enhanced ratio analysis"""
        report = ratio_analyzer.analyze_company(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            current_ratios=sample_company_data['current_ratios'],
            historical_ratios=sample_company_data['historical_ratios'],
            periods=sample_company_data['periods']
        )

        # Check ROE analysis
        roe_ratio = report.enhanced_ratios.get('roe')
        assert roe_ratio is not None
        assert roe_ratio.current_value == 0.20
        assert roe_ratio.industry_benchmark is not None
        assert roe_ratio.trend_analysis is not None
        assert roe_ratio.volatility_metrics is not None
        assert 0 <= roe_ratio.performance_score <= 100
        assert roe_ratio.industry_position in ['leader', 'above_average', 'below_average', 'laggard']

    def test_overall_health_calculation(self, ratio_analyzer, sample_company_data):
        """Test overall financial health calculation"""
        report = ratio_analyzer.analyze_company(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            current_ratios=sample_company_data['current_ratios']
        )

        health = report.overall_financial_health

        # Should have all required fields
        assert 'score' in health
        assert 'grade' in health
        assert 'category_scores' in health
        assert 'summary' in health

        # Score should be reasonable
        assert 0 <= health['score'] <= 100

        # Grade should be valid
        valid_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D+', 'D', 'F']
        assert health['grade'] in valid_grades

    def test_risk_assessment(self, ratio_analyzer):
        """Test risk assessment functionality"""
        # High-risk scenario
        high_risk_ratios = {
            'current_ratio': 0.8,  # Low liquidity
            'debt_to_equity': 2.0,  # High leverage
            'interest_coverage': 2.0,  # Low coverage
            'roe': 0.05  # Low profitability
        }

        report = ratio_analyzer.analyze_company(
            company_ticker='RISKY',
            company_name='Risky Company',
            industry='Technology',
            current_ratios=high_risk_ratios
        )

        risk_assessment = report.risk_assessment

        assert risk_assessment['risk_level'] in ['Low', 'Moderate', 'High', 'Very High']
        assert risk_assessment['risk_score'] > 0
        assert isinstance(risk_assessment['risk_factors'], list)

        # High-risk company should have multiple risk factors
        assert len(risk_assessment['risk_factors']) > 0

    def test_strategic_insights_generation(self, ratio_analyzer, sample_company_data):
        """Test strategic insights generation"""
        report = ratio_analyzer.analyze_company(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            current_ratios=sample_company_data['current_ratios'],
            historical_ratios=sample_company_data['historical_ratios'],
            periods=sample_company_data['periods']
        )

        insights = report.strategic_insights

        assert isinstance(insights, list)
        assert len(insights) <= 5  # Should be limited to top 5

        # Each insight should be a meaningful string
        for insight in insights:
            assert isinstance(insight, str)
            assert len(insight) > 50  # Should be substantial insights


@pytest.fixture
def mock_financial_calculator():
    """Create mock financial calculator for integration tests"""
    class MockCalculator:
        def get_financial_metrics(self):
            return {
                'profitability': {
                    'roe': [0.15, 0.18, 0.20],
                    'roa': [0.08, 0.10, 0.12],
                    'gross_margin': [0.40, 0.42, 0.45],
                    'operating_margin': [0.18, 0.20, 0.22],
                    'net_margin': [0.12, 0.14, 0.16]
                },
                'liquidity': {
                    'current_ratio': [1.8, 2.0, 2.2],
                    'quick_ratio': [1.2, 1.4, 1.6]
                },
                'leverage': {
                    'debt_to_equity': [0.6, 0.5, 0.4],
                    'interest_coverage': [8.0, 9.0, 10.0]
                },
                'efficiency': {
                    'asset_turnover': [0.8, 0.9, 1.0]
                },
                'growth': {
                    'revenue_growth': [0.08, 0.12, 0.15],
                    'fcf_growth': [0.05, 0.10, 0.15]
                },
                'company_info': {
                    'name': 'Test Corporation',
                    'ticker': 'TEST'
                }
            }

    return MockCalculator()


class TestIntegration:
    """Integration tests for the complete system"""

    def test_end_to_end_analysis(self, mock_financial_calculator):
        """Test complete end-to-end analysis"""
        from ui.streamlit.advanced_ratio_dashboard import AdvancedRatioDashboard

        dashboard = AdvancedRatioDashboard()

        # Test that dashboard can be created and initialized
        assert dashboard is not None
        assert dashboard.ratio_analyzer is not None
        assert dashboard.benchmark_manager is not None

        # Test ratio extraction
        metrics = mock_financial_calculator.get_financial_metrics()
        current_ratios = dashboard._extract_current_ratios(metrics)

        assert len(current_ratios) > 0
        assert 'roe' in current_ratios
        assert current_ratios['roe'] == 0.20  # Latest value

    def test_data_flow_consistency(self):
        """Test data flow consistency between components"""
        # Create analyzer with temp path
        temp_dir = tempfile.mkdtemp()
        try:
            analyzer = AdvancedRatioAnalyzer(Path(temp_dir))

            # Test data consistency
            industries = analyzer.benchmark_manager.get_available_industries()
            assert len(industries) > 0

            # Test that all components use same benchmark data
            for industry in industries:
                profile = analyzer.benchmark_manager.get_industry_profile(industry)
                if profile:
                    peers = analyzer.benchmark_manager.get_peer_companies(industry)
                    assert isinstance(peers, list)

        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])