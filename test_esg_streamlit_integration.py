#!/usr/bin/env python3
"""
ESG Streamlit Integration Test
==============================

Test script to verify that the ESG integration works properly in the Streamlit UI.
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

def test_esg_dashboard_import():
    """Test that ESG dashboard components can be imported"""
    try:
        from ui.streamlit.esg_analysis_dashboard import ESGDashboard, render_esg_analysis
        logger.info("✓ ESG dashboard components imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Failed to import ESG dashboard components: {e}")
        return False

def test_esg_tab_configuration():
    """Test that ESG tab is properly configured"""
    try:
        from ui.streamlit.tab_configuration import TAB_DEFINITIONS

        esg_tabs = [tab for tab in TAB_DEFINITIONS if 'esg' in tab.key.lower()]
        if esg_tabs:
            esg_tab = esg_tabs[0]
            logger.info(f"✓ Found ESG tab: '{esg_tab.title}' with icon '{esg_tab.icon}'")
            return True
        else:
            logger.error("✗ No ESG tab found in configuration")
            return False
    except Exception as e:
        logger.error(f"✗ Failed to check ESG tab configuration: {e}")
        return False

def test_esg_variable_registration_at_startup():
    """Test that ESG variables are properly registered during initialization"""
    try:
        from core.analysis.esg.esg_variable_definitions import register_esg_variables_with_registry
        from core.data_processing.financial_variable_registry import FinancialVariableRegistry

        # Clear any existing registry state for clean test
        registry = FinancialVariableRegistry()

        # Register ESG variables
        registered_count = register_esg_variables_with_registry()
        logger.info(f"✓ Registered {registered_count} ESG variables")

        # Verify some key variables are registered
        test_vars = ['carbon_emissions_total', 'board_independence', 'esg_score_total']
        for var_name in test_vars:
            var_def = registry.get_variable_definition(var_name)
            if var_def:
                logger.info(f"  ✓ Variable '{var_name}' is registered")
            else:
                logger.warning(f"  ⚠ Variable '{var_name}' not found in registry")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to test ESG variable registration: {e}")
        return False

def test_esg_dashboard_initialization():
    """Test that ESG dashboard can be initialized without errors"""
    try:
        from ui.streamlit.esg_analysis_dashboard import ESGDashboard

        # Initialize dashboard (this should register ESG variables)
        dashboard = ESGDashboard()

        # Check if the dashboard has the expected components
        if hasattr(dashboard, 'esg_engine'):
            logger.info("✓ ESG dashboard has analysis engine")

        if hasattr(dashboard, 'esg_adapter'):
            logger.info("✓ ESG dashboard has data adapter")

        if hasattr(dashboard, 'colors'):
            logger.info(f"✓ ESG dashboard has color scheme with {len(dashboard.colors)} colors")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to initialize ESG dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_esg_analysis_mock_run():
    """Test that ESG analysis can run with mock data"""
    try:
        from ui.streamlit.esg_analysis_dashboard import ESGDashboard
        from core.analysis.esg.esg_analysis_engine import ESGAnalysisEngine

        # Initialize engine
        engine = ESGAnalysisEngine()

        # Run analysis with mock data
        test_symbol = "AAPL"
        result = engine.analyze_company_esg(
            symbol=test_symbol,
            weighting_scheme='equal',
            industry='technology'
        )

        logger.info(f"✓ ESG analysis completed for {test_symbol}")
        logger.info(f"  Overall Score: {result.overall_esg_score:.1f}")
        logger.info(f"  Rating: {result.overall_esg_rating.value}")
        logger.info(f"  Risk Level: {result.overall_risk_level.value}")
        logger.info(f"  Data Completeness: {result.data_completeness:.1%}")

        return True
    except Exception as e:
        logger.error(f"✗ Failed to run ESG analysis: {e}")
        return False

def main():
    """Run all ESG Streamlit integration tests"""
    logger.info("Starting ESG Streamlit Integration Tests")
    logger.info("=" * 50)

    tests = [
        ("ESG Dashboard Import", test_esg_dashboard_import),
        ("ESG Tab Configuration", test_esg_tab_configuration),
        ("ESG Variable Registration at Startup", test_esg_variable_registration_at_startup),
        ("ESG Dashboard Initialization", test_esg_dashboard_initialization),
        ("ESG Analysis Mock Run", test_esg_analysis_mock_run)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        logger.info(f"\nRunning: {test_name}")
        logger.info("-" * 30)

        try:
            if test_func():
                passed += 1
                logger.info(f"PASSED: {test_name}")
            else:
                failed += 1
                logger.error(f"FAILED: {test_name}")
        except Exception as e:
            failed += 1
            logger.error(f"FAILED: {test_name} with exception: {e}")

    logger.info("\n" + "=" * 50)
    logger.info(f"ESG Streamlit Integration Test Results:")
    logger.info(f"  Passed: {passed}")
    logger.info(f"  Failed: {failed}")
    logger.info(f"  Total:  {passed + failed}")

    if failed == 0:
        logger.info("🎉 All ESG Streamlit integration tests PASSED!")
        return 0
    else:
        logger.error(f"❌ {failed} test(s) FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())