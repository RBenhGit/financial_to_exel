#!/usr/bin/env python3
"""
ESG Integration Test Script
===========================

Test script to verify that the ESG analysis engine is working correctly
and can be integrated with the existing financial analysis system.
"""

import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def test_esg_engine_imports():
    """Test that all ESG modules can be imported successfully"""
    try:
        from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine, ESGAnalysisResult
        from core.analysis.esg.esg_variable_definitions import get_esg_variable_definitions, register_esg_variables_with_registry
        logger.info("✓ ESG modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import ESG modules: {e}")
        return False

def test_esg_variable_definitions():
    """Test ESG variable definitions"""
    try:
        from core.analysis.esg.esg_variable_definitions import get_esg_variable_definitions

        esg_vars = get_esg_variable_definitions()
        logger.info(f"✓ Found {len(esg_vars)} ESG variable definitions")

        # Check some key variables exist
        key_vars = [
            'carbon_emissions_total', 'carbon_intensity', 'renewable_energy_percentage',
            'employee_count_total', 'gender_diversity_board', 'board_independence',
            'esg_score_total', 'environmental_score', 'social_score', 'governance_score'
        ]

        missing_vars = [var for var in key_vars if var not in esg_vars]
        if missing_vars:
            logger.warning(f"⚠ Missing key ESG variables: {missing_vars}")
        else:
            logger.info("✓ All key ESG variables are defined")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to get ESG variable definitions: {e}")
        return False

def test_esg_variable_registration():
    """Test registering ESG variables with the system"""
    try:
        from core.analysis.esg.esg_variable_definitions import register_esg_variables_with_registry

        registered_count = register_esg_variables_with_registry()
        logger.info(f"✓ Registered {registered_count} ESG variables with the system")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to register ESG variables: {e}")
        return False

def test_esg_analysis_engine_initialization():
    """Test ESG analysis engine initialization"""
    try:
        from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine

        engine = ESGAnalysisEngine()
        logger.info("✓ ESG Analysis Engine initialized successfully")

        # Check engine attributes
        if hasattr(engine, 'weighting_schemes') and engine.weighting_schemes:
            logger.info(f"✓ Found {len(engine.weighting_schemes)} weighting schemes")

        if hasattr(engine, 'industry_materiality') and engine.industry_materiality:
            logger.info(f"✓ Found {len(engine.industry_materiality)} industry materiality profiles")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize ESG Analysis Engine: {e}")
        return False

def test_mock_esg_analysis():
    """Test ESG analysis with mock data"""
    try:
        from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine

        engine = ESGAnalysisEngine()

        # Test with a common ticker
        test_symbol = "MSFT"
        logger.info(f"Testing ESG analysis for {test_symbol}")

        # This will likely use placeholder data since we don't have real ESG data sources configured
        result = engine.analyze_company_esg(
            symbol=test_symbol,
            weighting_scheme='equal',
            industry='technology'
        )

        logger.info(f"✓ ESG analysis completed for {test_symbol}")
        logger.info(f"  Overall ESG Score: {result.overall_esg_score:.1f}")
        logger.info(f"  ESG Rating: {result.overall_esg_rating.value}")
        logger.info(f"  Risk Level: {result.overall_risk_level.value}")
        logger.info(f"  Environmental Score: {result.environmental_score.score:.1f}")
        logger.info(f"  Social Score: {result.social_score.score:.1f}")
        logger.info(f"  Governance Score: {result.governance_score.score:.1f}")
        logger.info(f"  Data Completeness: {result.data_completeness:.1%}")
        logger.info(f"  Confidence Level: {result.confidence_level}")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to perform ESG analysis: {e}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_esg_report_generation():
    """Test ESG report generation"""
    try:
        from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine

        engine = ESGAnalysisEngine()
        test_symbol = "MSFT"

        # Run analysis
        result = engine.analyze_company_esg(
            symbol=test_symbol,
            weighting_scheme='equal',
            industry='technology'
        )

        # Generate report
        report = engine.generate_esg_report(result)

        logger.info("✓ ESG report generated successfully")
        logger.info(f"Report length: {len(report)} characters")

        # Save report to file for review
        report_filename = f"esg_report_{test_symbol}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_filename, 'w') as f:
            f.write(report)

        logger.info(f"✓ ESG report saved to {report_filename}")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to generate ESG report: {e}")
        return False

def main():
    """Run all ESG integration tests"""
    logger.info("Starting ESG Integration Tests")
    logger.info("=" * 50)

    tests = [
        ("ESG Module Imports", test_esg_engine_imports),
        ("ESG Variable Definitions", test_esg_variable_definitions),
        ("ESG Variable Registration", test_esg_variable_registration),
        ("ESG Engine Initialization", test_esg_analysis_engine_initialization),
        ("Mock ESG Analysis", test_mock_esg_analysis),
        ("ESG Report Generation", test_esg_report_generation)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 30)

        try:
            if test_func():
                passed += 1
                logger.info(f"✓ {test_name} PASSED")
            else:
                failed += 1
                logger.error(f"✗ {test_name} FAILED")
        except Exception as e:
            failed += 1
            logger.error(f"✗ {test_name} FAILED with exception: {e}")

    logger.info("\n" + "=" * 50)
    logger.info(f"ESG Integration Test Results:")
    logger.info(f"  Passed: {passed}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total:  {passed + failed}")

    if failed == 0:
        logger.info("🎉 All ESG integration tests PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed} test(s) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())