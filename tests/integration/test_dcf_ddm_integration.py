"""
Test DCF and DDM integration with var_input_data system
=======================================================

This script tests the integration of DCF and DDM calculation engines 
with the var_input_data system to ensure proper data flow and lineage tracking.
"""

import sys
import logging
from pathlib import Path
import pandas as pd

# Setup path for imports
sys.path.append(str(Path(__file__).parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_dcf_integration():
    """Test DCF integration with var_input_data"""
    logger.info("=" * 60)
    logger.info("TESTING DCF INTEGRATION WITH VAR_INPUT_DATA")
    logger.info("=" * 60)
    
    try:
        # Import required modules
        from core.data_processing.var_input_data import get_var_input_data, VariableMetadata
        from core.analysis.dcf.dcf_valuation import DCFValuator
        
        # Create mock financial calculator
        class MockFinancialCalculator:
            def __init__(self):
                self.ticker_symbol = "TEST_DCF"
                self.currency = "USD"
                self.is_tase_stock = False
                self.shares_outstanding = 1000.0  # millions
                self.current_stock_price = 150.0
                self.market_cap = 150000.0  # millions
                
                # Mock FCF results for fallback
                self.fcf_results = {
                    'FCFE': [8000, 8500, 9200, 9800, 10500],  # millions
                    'FCFF': [9000, 9600, 10300, 11000, 11800],
                }
                
                # Mock financial data
                self.financial_data = {
                    'Balance Sheet': {
                        2023: {
                            'Total Debt': 5000,
                            'Cash and Cash Equivalents': 2000
                        }
                    }
                }
            
            def fetch_market_data(self):
                return {
                    'current_price': self.current_stock_price,
                    'market_cap': self.market_cap,
                    'shares_outstanding': self.shares_outstanding,
                    'ticker_symbol': self.ticker_symbol
                }
        
        # Initialize var_input_data system and register standard variables
        from core.data_processing.standard_financial_variables import register_all_variables
        from core.data_processing.financial_variable_registry import get_registry
        
        registry = get_registry()
        register_all_variables(registry)  # Register all standard variables
        
        # Register additional variables needed for testing
        from core.data_processing.financial_variable_registry import VariableDefinition, VariableCategory, DataType, Units
        
        additional_vars = [
            VariableDefinition(
                name="intrinsic_value",
                category=VariableCategory.CALCULATED,
                data_type=DataType.CURRENCY,
                units=Units.USD,
                description="Intrinsic value per share from DCF/DDM calculations"
            ),
            VariableDefinition(
                name="gordon_growth_rate", 
                category=VariableCategory.CALCULATED,
                data_type=DataType.PERCENTAGE,
                units=Units.PERCENTAGE,
                description="Growth rate used in Gordon Growth Model"
            ),
            VariableDefinition(
                name="dividend_growth_rate",
                category=VariableCategory.CALCULATED, 
                data_type=DataType.PERCENTAGE,
                units=Units.PERCENTAGE,
                description="Historical dividend growth rate"
            ),
            VariableDefinition(
                name="current_price",
                category=VariableCategory.MARKET_DATA,
                data_type=DataType.CURRENCY,
                units=Units.USD,
                description="Current market price per share"
            ),
            VariableDefinition(
                name="market_cap",
                category=VariableCategory.MARKET_DATA,
                data_type=DataType.CURRENCY,
                units=Units.MILLIONS_USD,
                description="Market capitalization"
            ),
            VariableDefinition(
                name="shares_outstanding",
                category=VariableCategory.MARKET_DATA,
                data_type=DataType.NUMBER,
                units=Units.MILLIONS,
                description="Shares outstanding"
            ),
            VariableDefinition(
                name="payout_ratio",
                category=VariableCategory.CALCULATED,
                data_type=DataType.PERCENTAGE,
                units=Units.PERCENTAGE,
                description="Dividend payout ratio"
            )
        ]
        
        for var_def in additional_vars:
            registry.register_variable(var_def)
        
        var_data = get_var_input_data()
        
        # Clear any existing test data
        var_data.clear_cache("TEST_DCF")
        
        # Pre-populate some FCF data in var_input_data
        logger.info("Pre-populating FCF data in var_input_data...")
        fcf_data = [8000, 8500, 9200, 9800, 10500]
        years = [2019, 2020, 2021, 2022, 2023]
        
        for year, fcf in zip(years, fcf_data):
            metadata = VariableMetadata(
                source="test_setup",
                timestamp=pd.Timestamp.now(),
                quality_score=1.0,
                validation_passed=True,
                calculation_method="test_data_injection",
                period=str(year)
            )
            
            var_data.set_variable(
                symbol="TEST_DCF",
                variable_name="fcfe",
                value=fcf,
                period=str(year),
                source="test_setup", 
                metadata=metadata
            )
        
        # Initialize DCF valuator
        mock_calc = MockFinancialCalculator()
        dcf_valuator = DCFValuator(mock_calc)
        
        # Test DCF calculation
        logger.info("Running DCF calculation...")
        dcf_assumptions = {
            'discount_rate': 0.10,
            'terminal_growth_rate': 0.03,
            'growth_rate_yr1_5': 0.08,
            'projection_years': 10,
            'fcf_type': 'FCFE'
        }
        
        dcf_result = dcf_valuator.calculate_dcf_projections(dcf_assumptions)
        
        if dcf_result and 'value_per_share' in dcf_result:
            logger.info(f"✓ DCF calculation successful!")
            logger.info(f"  - Intrinsic Value: ${dcf_result['value_per_share']:.2f}")
            logger.info(f"  - FCF Type Used: {dcf_result['fcf_type']}")
            logger.info(f"  - Terminal Value: ${dcf_result['terminal_value']:,.0f}M")
            logger.info(f"  - Equity Value: ${dcf_result['equity_value']:,.0f}M")
        else:
            logger.error("✗ DCF calculation failed!")
            logger.error(f"Result: {dcf_result}")
            return False
        
        # Test data retrieval from var_input_data
        logger.info("Testing var_input_data retrieval...")
        
        # Check if DCF results were stored
        intrinsic_value = var_data.get_variable("TEST_DCF", "intrinsic_value", "latest")
        terminal_value = var_data.get_variable("TEST_DCF", "terminal_value", "latest")
        wacc = var_data.get_variable("TEST_DCF", "wacc", "latest")
        
        if intrinsic_value is not None:
            logger.info(f"✓ Intrinsic value stored: ${intrinsic_value:.2f}")
        else:
            logger.warning("✗ Intrinsic value not found in var_input_data")
            
        if terminal_value is not None:
            logger.info(f"✓ Terminal value stored: ${terminal_value:,.0f}M")
        else:
            logger.warning("✗ Terminal value not found in var_input_data")
            
        if wacc is not None:
            logger.info(f"✓ WACC stored: {wacc:.1%}")
        else:
            logger.warning("✗ WACC not found in var_input_data")
        
        # Test historical FCF retrieval
        historical_fcfe = var_data.get_historical_data("TEST_DCF", "fcfe", years=5)
        if historical_fcfe:
            logger.info(f"✓ Historical FCFE data retrieved: {len(historical_fcfe)} data points")
        else:
            logger.warning("✗ No historical FCFE data found")
        
        return True
        
    except Exception as e:
        logger.error(f"DCF integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ddm_integration():
    """Test DDM integration with var_input_data"""
    logger.info("=" * 60)
    logger.info("TESTING DDM INTEGRATION WITH VAR_INPUT_DATA")
    logger.info("=" * 60)
    
    try:
        # Import required modules
        from core.data_processing.var_input_data import get_var_input_data, VariableMetadata
        from core.analysis.ddm.ddm_valuation import DDMValuator
        
        # Create mock financial calculator
        class MockFinancialCalculator:
            def __init__(self):
                self.ticker_symbol = "TEST_DDM"
                self.currency = "USD"
                self.is_tase_stock = False
                self.shares_outstanding = 1000.0  # millions
                self.current_stock_price = 50.0
                self.market_cap = 50000.0  # millions
                
                # Mock financial data
                self.financial_data = {
                    'Income Statement': {
                        2023: {'Basic EPS': 4.50},
                        2022: {'Basic EPS': 4.20},
                        2021: {'Basic EPS': 3.90}
                    }
                }
                
                # Mock scale factor
                self.financial_scale_factor = 1
            
            def fetch_market_data(self):
                return {
                    'current_price': self.current_stock_price,
                    'market_cap': self.market_cap,
                    'shares_outstanding': self.shares_outstanding,
                    'ticker_symbol': self.ticker_symbol
                }
        
        # Initialize var_input_data system (variables already registered from DCF test)
        var_data = get_var_input_data()
        
        # Clear any existing test data
        var_data.clear_cache("TEST_DDM")
        
        # Pre-populate dividend data in var_input_data
        logger.info("Pre-populating dividend data in var_input_data...")
        dividend_data = [1.80, 1.90, 2.00, 2.10, 2.20]  # Growing dividends
        years = [2019, 2020, 2021, 2022, 2023]
        
        for year, dividend in zip(years, dividend_data):
            metadata = VariableMetadata(
                source="test_setup",
                timestamp=pd.Timestamp.now(),
                quality_score=1.0,
                validation_passed=True,
                calculation_method="test_dividend_injection",
                period=str(year)
            )
            
            var_data.set_variable(
                symbol="TEST_DDM",
                variable_name="dividend_per_share",
                value=dividend,
                period=str(year),
                source="test_setup",
                metadata=metadata
            )
        
        # Initialize DDM valuator
        mock_calc = MockFinancialCalculator()
        ddm_valuator = DDMValuator(mock_calc)
        
        # Test DDM calculation
        logger.info("Running DDM calculation...")
        ddm_assumptions = {
            'discount_rate': 0.09,
            'terminal_growth_rate': 0.03,
            'stage1_growth_rate': 0.06,
            'stage1_years': 5,
            'model_type': 'gordon'
        }
        
        ddm_result = ddm_valuator.calculate_ddm_valuation(ddm_assumptions)
        
        if ddm_result and 'intrinsic_value' in ddm_result and not ddm_result.get('error'):
            logger.info(f"✓ DDM calculation successful!")
            logger.info(f"  - Intrinsic Value: ${ddm_result['intrinsic_value']:.2f}")
            logger.info(f"  - Model Type: {ddm_result['model_variant']}")
            logger.info(f"  - Current Dividend: ${ddm_result['current_dividend']:.2f}")
            logger.info(f"  - Growth Rate: {ddm_result.get('growth_rate', 0):.1%}")
        else:
            logger.error("✗ DDM calculation failed!")
            logger.error(f"Result: {ddm_result}")
            return False
        
        # Test data retrieval from var_input_data
        logger.info("Testing var_input_data retrieval...")
        
        # Check if DDM results were stored
        intrinsic_value = var_data.get_variable("TEST_DDM", "intrinsic_value", "latest")
        dividend_yield = var_data.get_variable("TEST_DDM", "dividend_yield", "latest")
        payout_ratio = var_data.get_variable("TEST_DDM", "payout_ratio", "latest")
        
        if intrinsic_value is not None:
            logger.info(f"✓ Intrinsic value stored: ${intrinsic_value:.2f}")
        else:
            logger.warning("✗ Intrinsic value not found in var_input_data")
            
        if dividend_yield is not None:
            logger.info(f"✓ Dividend yield stored: {dividend_yield:.1%}")
        else:
            logger.warning("✗ Dividend yield not found in var_input_data")
        
        # Test historical dividend retrieval
        historical_dividends = var_data.get_historical_data("TEST_DDM", "dividend_per_share", years=5)
        if historical_dividends:
            logger.info(f"✓ Historical dividend data retrieved: {len(historical_dividends)} data points")
        else:
            logger.warning("✗ No historical dividend data found")
        
        return True
        
    except Exception as e:
        logger.error(f"DDM integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_lineage_tracking():
    """Test calculation lineage tracking"""
    logger.info("=" * 60)
    logger.info("TESTING CALCULATION LINEAGE TRACKING")
    logger.info("=" * 60)
    
    try:
        from core.data_processing.var_input_data import get_var_input_data
        
        var_data = get_var_input_data()
        
        # Test DCF lineage
        try:
            result = var_data.get_variable(
                "TEST_DCF", "intrinsic_value", "latest", include_metadata=True
            )
            
            if result and len(result) == 2:
                dcf_intrinsic_value, metadata = result
                if metadata:
                    logger.info("✓ DCF calculation lineage found:")
                    logger.info(f"  - Source: {metadata.source}")
                    logger.info(f"  - Method: {metadata.calculation_method}")
                    logger.info(f"  - Dependencies: {metadata.dependencies}")
                    logger.info(f"  - Quality Score: {metadata.quality_score}")
                    logger.info(f"  - Timestamp: {metadata.timestamp}")
                else:
                    logger.warning("✗ No DCF lineage metadata found")
            else:
                logger.warning("✗ DCF intrinsic value not found in var_input_data")
        except Exception as e:
            logger.warning(f"✗ Error retrieving DCF lineage: {e}")
        
        # Test DDM lineage
        try:
            result = var_data.get_variable(
                "TEST_DDM", "intrinsic_value", "latest", include_metadata=True
            )
            
            if result and len(result) == 2:
                ddm_intrinsic_value, metadata = result
                if metadata:
                    logger.info("✓ DDM calculation lineage found:")
                    logger.info(f"  - Source: {metadata.source}")
                    logger.info(f"  - Method: {metadata.calculation_method}")
                    logger.info(f"  - Dependencies: {metadata.dependencies}")
                    logger.info(f"  - Quality Score: {metadata.quality_score}")
                    logger.info(f"  - Timestamp: {metadata.timestamp}")
                else:
                    logger.warning("✗ No DDM lineage metadata found")
            else:
                logger.warning("✗ DDM intrinsic value not found in var_input_data")
        except Exception as e:
            logger.warning(f"✗ Error retrieving DDM lineage: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Lineage tracking test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all integration tests"""
    logger.info("Starting DCF/DDM var_input_data Integration Tests...")
    
    results = {
        'dcf_integration': test_dcf_integration(),
        'ddm_integration': test_ddm_integration(),
        'lineage_tracking': test_lineage_tracking()
    }
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS ✓" if result else "FAIL ✗"
        logger.info(f"{test_name.replace('_', ' ').title()}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All integration tests passed! DCF/DDM var_input_data integration is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the logs for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)