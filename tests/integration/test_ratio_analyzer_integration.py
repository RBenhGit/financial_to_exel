"""
Integration test for AdvancedRatioAnalyzer with FinancialCalculationEngine
"""

import pytest
from datetime import datetime
from core.analysis.ratios.ratio_analyzer import AdvancedRatioAnalyzer


class TestRatioAnalyzerIntegration:
    """Test integration of AdvancedRatioAnalyzer with FinancialCalculationEngine"""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return AdvancedRatioAnalyzer()

    @pytest.fixture
    def sample_financial_statements(self):
        """Sample financial statements for testing"""
        return {
            'revenue': 1000000,
            'cost_of_revenue': 600000,
            'gross_profit': 400000,
            'operating_income': 250000,
            'net_income': 150000,
            'total_assets': 2000000,
            'current_assets': 800000,
            'cash_and_equivalents': 200000,
            'inventory': 150000,
            'current_liabilities': 400000,
            'total_liabilities': 800000,
            'shareholders_equity': 1200000,
            'interest_expense': 50000
        }

    def test_calculation_engine_initialized(self, analyzer):
        """Test that FinancialCalculationEngine is properly initialized"""
        assert hasattr(analyzer, 'calculation_engine')
        assert analyzer.calculation_engine is not None

    def test_analyze_company_from_statements(self, analyzer, sample_financial_statements):
        """Test analyzing company from financial statements"""
        report = analyzer.analyze_company_from_statements(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            financial_statements=sample_financial_statements
        )

        # Check report structure
        assert report is not None
        assert report.company_ticker == 'TEST'
        assert report.company_name == 'Test Company'
        assert report.industry == 'Technology'
        assert isinstance(report.analysis_date, datetime)

        # Check that ratios were calculated
        assert len(report.enhanced_ratios) > 0

        # Check specific ratios are present
        expected_ratios = [
            'current_ratio', 'quick_ratio', 'cash_ratio',  # Liquidity
            'gross_profit_margin', 'operating_profit_margin', 'net_profit_margin',  # Profitability
            'return_on_assets', 'return_on_equity',  # Profitability
            'debt_to_assets', 'debt_to_equity', 'interest_coverage'  # Leverage
        ]

        for ratio in expected_ratios:
            assert ratio in report.enhanced_ratios, f"Expected ratio {ratio} not found in report"

    def test_analyze_company_from_statements_with_historical(self, analyzer, sample_financial_statements):
        """Test analyzing company with historical data"""
        # Create historical statements with slight variations (need at least 3 for trend analysis)
        historical_statements = [
            {**sample_financial_statements, 'revenue': 850000, 'net_income': 120000},
            {**sample_financial_statements, 'revenue': 900000, 'net_income': 130000},
            {**sample_financial_statements, 'revenue': 950000, 'net_income': 140000},
        ]

        periods = [
            datetime(2021, 12, 31),
            datetime(2022, 12, 31),
            datetime(2023, 12, 31)
        ]

        report = analyzer.analyze_company_from_statements(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            financial_statements=sample_financial_statements,
            historical_statements=historical_statements,
            periods=periods
        )

        # Check that historical analysis was performed
        assert report is not None
        assert len(report.enhanced_ratios) > 0

        # Check that trend analysis is present for some ratios
        ratios_with_trends = [
            ratio for ratio in report.enhanced_ratios.values()
            if ratio.trend_analysis is not None
        ]
        assert len(ratios_with_trends) > 0

    def test_overall_health_includes_all_categories(self, analyzer, sample_financial_statements):
        """Test that overall health calculation includes all ratio categories"""
        report = analyzer.analyze_company_from_statements(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            financial_statements=sample_financial_statements
        )

        health = report.overall_financial_health

        # Check health metrics
        assert 'score' in health
        assert 'grade' in health
        assert 'category_scores' in health

        # Check that multiple categories are analyzed
        assert len(health['category_scores']) > 0

        # Check expected categories present in results
        expected_categories = {'profitability', 'liquidity', 'leverage'}
        found_categories = set(health['category_scores'].keys())
        assert expected_categories.issubset(found_categories)

    def test_backward_compatibility_with_analyze_company(self, analyzer):
        """Test that old analyze_company method still works"""
        current_ratios = {
            'current_ratio': 2.0,
            'quick_ratio': 1.5,
            'roe': 0.15,
            'roa': 0.10,
            'debt_to_equity': 0.5,
            'gross_margin': 0.40,
            'operating_margin': 0.25,
            'net_margin': 0.15
        }

        report = analyzer.analyze_company(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            current_ratios=current_ratios
        )

        assert report is not None
        assert len(report.enhanced_ratios) == len(current_ratios)

    def test_field_mappings_support(self, analyzer):
        """Test that custom field mappings work"""
        # Use non-standard field names
        custom_statements = {
            'total_revenue': 1000000,  # Instead of 'revenue'
            'earnings': 150000,  # Instead of 'net_income'
            'assets': 2000000,  # Instead of 'total_assets'
            'equity': 1200000  # Instead of 'shareholders_equity'
        }

        field_mappings = {
            'revenue': 'total_revenue',
            'net_income': 'earnings',
            'total_assets': 'assets',
            'shareholders_equity': 'equity'
        }

        report = analyzer.analyze_company_from_statements(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            financial_statements=custom_statements,
            field_mappings=field_mappings
        )

        # Check that some ratios were calculated despite custom field names
        assert report is not None
        assert len(report.enhanced_ratios) > 0

    def test_handles_missing_fields_gracefully(self, analyzer):
        """Test that analyzer handles missing fields gracefully"""
        incomplete_statements = {
            'revenue': 1000000,
            'net_income': 150000,
            # Missing many other fields
        }

        report = analyzer.analyze_company_from_statements(
            company_ticker='TEST',
            company_name='Test Company',
            industry='Technology',
            financial_statements=incomplete_statements
        )

        # Should still produce a report, even with limited data
        assert report is not None
        # Some ratios should be calculated from available data
        # (return_on_equity won't work, but we should get what we can)
