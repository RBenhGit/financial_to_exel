#!/usr/bin/env python3
"""
Test script to validate DCF units fix
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator
import logging

# Configure logging to see debug output
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def test_dcf_units_consistency():
    """Test that FCF and DCF calculations use consistent units"""

    print("=" * 60)
    print("TESTING DCF UNITS FIX")
    print("=" * 60)

    # Create a mock financial calculator with known FCF values
    calc = FinancialCalculator(None)

    # Set known FCF values in millions (e.g., Microsoft-like values)
    # These should be: [45000, 50000, 55000, 60000] representing millions
    test_fcf_millions = [45000, 50000, 55000, 60000]  # $45B, $50B, $55B, $60B
    calc.fcf_results = {'FCFE': test_fcf_millions}

    # Mock market data
    calc.ticker_symbol = 'TEST'
    calc.shares_outstanding = 7500  # 7.5B shares
    calc.current_stock_price = 400  # $400/share
    calc.market_cap = (
        calc.shares_outstanding * calc.current_stock_price * 1000000
    )  # Market cap in actual dollars

    def mock_fetch_market_data():
        return {
            'shares_outstanding': calc.shares_outstanding * 1000000,  # Convert to actual shares
            'current_price': calc.current_stock_price,
            'market_cap': calc.market_cap,
            'ticker_symbol': 'TEST',
            'currency': 'USD',
            'is_tase_stock': False,
        }

    calc.fetch_market_data = mock_fetch_market_data

    print(f"Input FCF values (millions): {test_fcf_millions}")
    print(f"Scale factor: {calc.financial_scale_factor}")
    print(
        f"Final FCF values after scaling: {[v * calc.financial_scale_factor for v in test_fcf_millions]}"
    )

    # Create DCF valuator
    dcf_valuator = DCFValuator(calc)

    # Test DCF calculation with standard assumptions
    test_assumptions = {
        'discount_rate': 0.10,  # 10%
        'terminal_growth_rate': 0.025,  # 2.5%
        'growth_rate_yr1_5': 0.08,  # 8%
        'growth_rate_yr5_10': 0.05,  # 5%
        'projection_years': 10,
        'terminal_method': 'perpetual_growth',
        'fcf_type': 'FCFE',
    }

    print(f"\nDCF Assumptions:")
    for key, value in test_assumptions.items():
        if 'rate' in key:
            print(f"  {key}: {value:.1%}")
        else:
            print(f"  {key}: {value}")

    # Calculate DCF
    print(f"\n" + "=" * 40)
    print("DCF CALCULATION RESULTS")
    print("=" * 40)

    dcf_result = dcf_valuator.calculate_dcf_projections(test_assumptions)

    if dcf_result:
        print(f"\nKey Results:")
        print(
            f"  Base FCF (latest): ${dcf_result.get('projections', {}).get('base_fcf', 0)/1000000:.1f}M"
        )
        print(f"  Terminal Value: ${dcf_result.get('terminal_value', 0)/1000000:.1f}M")
        print(f"  Equity Value: ${dcf_result.get('equity_value', 0)/1000000:.1f}M")
        print(f"  Value per Share: ${dcf_result.get('value_per_share', 0):.2f}")
        print(f"  Current Price: ${calc.current_stock_price:.2f}")

        # Calculate upside/downside
        value_per_share = dcf_result.get('value_per_share', 0)
        if value_per_share > 0:
            upside = (value_per_share - calc.current_stock_price) / calc.current_stock_price
            print(f"  Upside/Downside: {upside:.1%}")

        # Sanity checks
        print(f"\n" + "=" * 40)
        print("SANITY CHECKS")
        print("=" * 40)

        equity_value = dcf_result.get('equity_value', 0)
        base_fcf = dcf_result.get('projections', {}).get('base_fcf', 0)

        # Check if equity value is reasonable (should be 10-20x base FCF for growth companies)
        if base_fcf > 0:
            multiple = equity_value / base_fcf
            print(f"  Equity Value / Base FCF Multiple: {multiple:.1f}x")
            if 5 <= multiple <= 50:
                print(f"  OK Multiple is reasonable for a growth company")
            else:
                print(f"  ERROR Multiple seems too {'high' if multiple > 50 else 'low'}")

        # Check if value per share is reasonable
        if 50 <= value_per_share <= 2000:
            print(f"  OK Value per share ${value_per_share:.2f} is in reasonable range")
        else:
            print(
                f"  ERROR Value per share ${value_per_share:.2f} seems {'too high' if value_per_share > 2000 else 'too low'}"
            )

        # Check if equity value isn't ridiculously large
        if equity_value < 10_000_000:  # Less than $10 trillion
            print(f"  OK Equity value ${equity_value/1000000:.0f}M is not absurdly large")
        else:
            print(f"  ERROR Equity value ${equity_value/1000000:.0f}M is suspiciously large!")

        print(f"\n" + "=" * 40)
        print("CONCLUSION")
        print("=" * 40)

        if 5 <= multiple <= 50 and 50 <= value_per_share <= 2000 and equity_value < 10_000_000:
            print("OK DCF calculation appears to be working correctly!")
            print("OK Units fix was successful - no more 1,000,000x inflation")
        else:
            print("ERROR DCF calculation may still have issues")

    else:
        print("ERROR DCF calculation failed!")
        return False

    return True


if __name__ == "__main__":
    test_dcf_units_consistency()
