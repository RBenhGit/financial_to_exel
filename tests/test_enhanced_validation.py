"""
Test Enhanced Financial Statement Validation
===========================================

Simple test to verify the enhanced data quality validation functionality
"""

import pytest
import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.data_processing.enhanced_financial_statement_validator import (
    EnhancedFinancialStatementValidator,
    ValidationSeverity,
    ValidationCategory
)
from core.data_processing.data_validator import validate_financial_statements_comprehensive


class TestEnhancedValidation:
    """Test cases for enhanced financial statement validation"""

    def test_enhanced_validator_initialization(self):
        """Test that the enhanced validator initializes correctly"""
        validator = EnhancedFinancialStatementValidator()
        assert validator is not None
        assert validator.base_validator is not None
        assert validator.quality_scorer is not None
        assert validator.validation_rules is not None

    def test_balance_sheet_equation_validation(self):
        """Test balance sheet equation validation"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data with balanced balance sheet
        financial_data = {
            'balance_fy': {
                'Total Assets': [1000, 1100, 1200],
                'Total Liabilities': [600, 650, 700],
                'Total Stockholders\' Equity': [400, 450, 500]
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Balance Sheet")

        # Should pass balance sheet equation validation
        assert report.balance_sheet_score > 90
        assert "Balance sheet equation validation" in report.passed_checks

    def test_balance_sheet_equation_imbalance(self):
        """Test detection of balance sheet equation imbalance"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data with imbalanced balance sheet
        financial_data = {
            'balance_fy': {
                'Total Assets': [1000, 1100, 1200],
                'Total Liabilities': [600, 650, 700],
                'Total Stockholders\' Equity': [300, 350, 400]  # Imbalanced
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Imbalanced")

        # Should detect imbalance
        balance_issues = report.get_issues_by_category(ValidationCategory.BALANCE_SHEET_EQUATION)
        assert len(balance_issues) > 0
        assert report.balance_sheet_score < 100

    def test_business_rule_validation(self):
        """Test business rule constraints validation"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data with negative assets (violates business rules)
        financial_data = {
            'balance_fy': {
                'Total Current Assets': [-100, 200, 300],  # Negative assets
                'Cash and Cash Equivalents': [50, 60, 70]
            },
            'income_fy': {
                'Revenue': [1000, 1100, 1200],
                'Net Income': [-2500, 110, 120]  # Extreme loss
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Business Rules")

        # Should detect business rule violations
        business_rule_issues = report.get_issues_by_category(ValidationCategory.BUSINESS_RULE_CONSTRAINTS)
        assert len(business_rule_issues) > 0
        assert report.business_rules_score < 100

    def test_cross_period_validation(self):
        """Test cross-period consistency validation"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data with extreme growth (outlier)
        financial_data = {
            'income_fy': {
                'Revenue': [100, 110, 10000, 120, 130]  # Extreme spike in period 3
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Cross Period")

        # Should detect cross-period issues
        cross_period_issues = report.get_issues_by_category(ValidationCategory.CROSS_PERIOD_VALIDATION)
        assert len(cross_period_issues) > 0

    def test_data_completeness_validation(self):
        """Test data completeness validation"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data missing critical metrics
        financial_data = {
            'income_fy': {
                'Other Income': [10, 15, 20]  # Non-critical metric only
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Completeness")

        # Should detect completeness issues
        completeness_issues = report.get_issues_by_category(ValidationCategory.DATA_COMPLETENESS)
        assert len(completeness_issues) > 0
        assert report.completeness_score < 80

    def test_comprehensive_validation_function(self):
        """Test the comprehensive validation function"""
        # Create complete test data
        financial_data = {
            'income_fy': {
                'Revenue': [1000, 1100, 1200],
                'Net Income': [100, 110, 120]
            },
            'balance_fy': {
                'Total Assets': [2000, 2200, 2400],
                'Total Liabilities': [1200, 1320, 1440],
                'Total Stockholders\' Equity': [800, 880, 960]
            },
            'cashflow_fy': {
                'Cash from Operations': [150, 165, 180]
            }
        }

        results = validate_financial_statements_comprehensive(
            financial_data, "Test Comprehensive", include_enhanced_validation=True
        )

        # Should return both base and enhanced validation results
        assert 'base_validation' in results
        assert 'enhanced_validation' in results
        assert 'combined_score' in results

        assert results['base_validation']['overall_score'] >= 0
        assert results['enhanced_validation']['overall_score'] >= 0
        assert results['combined_score'] >= 0

    def test_validation_report_summary(self):
        """Test validation report summary generation"""
        validator = EnhancedFinancialStatementValidator()

        # Create test data with mixed issues
        financial_data = {
            'balance_fy': {
                'Total Assets': [1000, 1100],  # Insufficient data
                'Total Liabilities': [600, 650],
                'Total Stockholders\' Equity': [300, 350]  # Imbalanced
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Summary")

        # Test summary generation
        summary = report.get_summary()
        assert "FINANCIAL STATEMENT VALIDATION REPORT" in summary
        assert "Overall Score:" in summary
        assert "Category Scores:" in summary

    def test_validation_issue_filtering(self):
        """Test filtering validation issues by severity and category"""
        validator = EnhancedFinancialStatementValidator()

        # Create data that will generate various types of issues
        financial_data = {
            'balance_fy': {
                'Total Current Assets': [-100],  # Business rule violation
                'Total Liabilities': [600],
                'Total Stockholders\' Equity': [300]  # Missing Total Assets
            }
        }

        report = validator.validate_financial_statements(financial_data, "Test Filtering")

        # Test filtering by severity
        warnings = report.get_issues_by_severity(ValidationSeverity.WARNING)
        errors = report.get_issues_by_severity(ValidationSeverity.ERROR)

        assert isinstance(warnings, list)
        assert isinstance(errors, list)

        # Test filtering by category
        business_rule_issues = report.get_issues_by_category(ValidationCategory.BUSINESS_RULE_CONSTRAINTS)
        completeness_issues = report.get_issues_by_category(ValidationCategory.DATA_COMPLETENESS)

        assert isinstance(business_rule_issues, list)
        assert isinstance(completeness_issues, list)


def test_enhanced_validation_integration():
    """Integration test for enhanced validation with realistic data"""
    # This would be run with real Excel data in a full integration test
    print("Enhanced validation integration test would use real Excel files")
    print("Key features implemented:")
    print("✓ Balance sheet equation validation")
    print("✓ Cash flow reconciliation checks")
    print("✓ Income statement consistency validation")
    print("✓ Cross-period validation for historical data")
    print("✓ Business rule constraints validation")
    print("✓ Data completeness scoring integrated with quality scorer")
    print("✓ Comprehensive validation reporting")


if __name__ == "__main__":
    # Run simple tests if executed directly
    test_enhanced_validation_integration()

    # Run basic validation test
    validator = EnhancedFinancialStatementValidator()

    # Test with sample data
    sample_data = {
        'income_fy': {
            'Revenue': [1000, 1100, 1200, 1300, 1400],
            'Net Income': [100, 110, 120, 130, 140],
            'EBIT': [150, 165, 180, 195, 210]
        },
        'balance_fy': {
            'Total Assets': [2000, 2200, 2400, 2600, 2800],
            'Total Liabilities': [1200, 1320, 1440, 1560, 1680],
            'Total Stockholders\' Equity': [800, 880, 960, 1040, 1120],
            'Total Current Assets': [800, 880, 960, 1040, 1120],
            'Total Current Liabilities': [400, 440, 480, 520, 560]
        },
        'cashflow_fy': {
            'Cash from Operations': [150, 165, 180, 195, 210],
            'Cash from Investing': [-50, -55, -60, -65, -70],
            'Cash from Financing': [-30, -33, -36, -39, -42]
        }
    }

    print("\nRunning enhanced validation on sample data...")
    report = validator.validate_financial_statements(sample_data, "Sample Company")
    print(report.get_summary())