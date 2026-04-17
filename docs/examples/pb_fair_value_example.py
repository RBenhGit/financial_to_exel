"""
P/B Fair Value Calculator Usage Example
======================================

This example demonstrates how to use the P/B Fair Value Calculator with historical
P/B analysis to determine fair value estimates for stocks.

Example workflow:
1. Get historical data using data sources
2. Perform historical P/B analysis  
3. Calculate fair value using P/B patterns
4. Generate investment recommendations
"""

import logging
from datetime import datetime
from typing import Dict, Any

# Import required modules
from pb_fair_value_calculator import (
    PBFairValueCalculator, 
    create_fair_value_report, 
    validate_fair_value_inputs
)
from pb_historical_analysis import PBHistoricalAnalysisEngine
from data_sources import DataSourceResponse, FinancialDataRequest

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_fair_value_calculation():
    """
    Example of complete fair value calculation workflow.
    
    This example uses mock data to demonstrate the process. In practice,
    you would replace this with real data from your preferred data source.
    """
    
    print("="*60)
    print("P/B Fair Value Calculator - Example Usage")
    print("="*60)
    
    # Step 1: Create sample data response (in practice, this comes from your data source)
    sample_data = create_sample_data_response()
    
    # Step 2: Perform historical P/B analysis
    print("\n1. Performing Historical P/B Analysis...")
    historical_engine = PBHistoricalAnalysisEngine()
    historical_result = historical_engine.analyze_historical_performance(sample_data, years=5)
    
    if not historical_result.success:
        print(f"[ERROR] Historical analysis failed: {historical_result.error_message}")
        return
    
    print(f"[SUCCESS] Historical analysis completed:")
    print(f"   - Data points: {historical_result.data_points_count}")
    print(f"   - Quality score: {historical_result.quality_metrics.overall_score:.2f}")
    print(f"   - Mean P/B: {historical_result.statistics.mean_pb:.2f}")
    print(f"   - Median P/B: {historical_result.statistics.median_pb:.2f}")
    print(f"   - P/B Range: {historical_result.statistics.min_pb:.2f} - {historical_result.statistics.max_pb:.2f}")
    
    # Step 3: Validate inputs for fair value calculation
    current_book_value = 28.50  # Current book value per share
    current_price = 385.00      # Current market price
    
    print(f"\n2. Validating Inputs...")
    validation = validate_fair_value_inputs(current_book_value, current_price)
    
    if not validation['valid']:
        print(f"[ERROR] Input validation failed: {validation['issues']}")
        return
    
    print(f"[SUCCESS] Inputs validated successfully")
    if validation['recommendations']:
        for rec in validation['recommendations']:
            print(f"   - {rec}")
    
    # Step 4: Calculate fair value
    print(f"\n3. Calculating Fair Value...")
    calculator = PBFairValueCalculator(decay_factor=0.85)
    fair_value_result = calculator.calculate_fair_value(
        historical_result, 
        current_book_value, 
        current_price
    )
    
    if not fair_value_result.success:
        print(f"[ERROR] Fair value calculation failed: {fair_value_result.error_message}")
        return
    
    # Step 5: Display results
    print(f"\n4. Fair Value Results for {fair_value_result.ticker}:")
    print(f"   Current Price: ${current_price:.2f}")
    print(f"   Current Book Value: ${current_book_value:.2f}")
    print(f"   Current P/B Ratio: {current_price/current_book_value:.2f}")
    
    print(f"\n   [SCENARIOS] Fair Value Scenarios:")
    print(f"   Conservative: ${fair_value_result.conservative_scenario.target_price:.2f} (P/B: {fair_value_result.conservative_scenario.pb_multiple:.2f})")
    print(f"   Fair Value:   ${fair_value_result.fair_scenario.target_price:.2f} (P/B: {fair_value_result.fair_scenario.pb_multiple:.2f})")
    print(f"   Optimistic:   ${fair_value_result.optimistic_scenario.target_price:.2f} (P/B: {fair_value_result.optimistic_scenario.pb_multiple:.2f})")
    
    print(f"\n   [RECOMMENDATION] Investment Recommendation:")
    print(f"   Signal: {fair_value_result.investment_signal.upper()}")
    print(f"   Strength: {fair_value_result.signal_strength:.1%}")
    print(f"   Margin of Safety: {fair_value_result.margin_of_safety:.1%}")
    
    print(f"\n   [STATS] Statistical Validation:")
    print(f"   Significance: {fair_value_result.statistical_significance:.2f}")
    print(f"   Confidence Interval: ${fair_value_result.confidence_interval[0]:.2f} - ${fair_value_result.confidence_interval[1]:.2f}")
    print(f"   Overall Quality: {fair_value_result.overall_quality_score:.2f}")
    
    # Step 6: Show methodology and warnings
    if fair_value_result.methodology_notes:
        print(f"\n   [METHODOLOGY] Methodology Notes:")
        for note in fair_value_result.methodology_notes:
            print(f"   - {note}")
    
    if fair_value_result.calculation_warnings:
        print(f"\n   [WARNING] Warnings:")
        for warning in fair_value_result.calculation_warnings:
            print(f"   - {warning}")
    
    # Step 7: Generate comprehensive report
    print(f"\n5. Generating Comprehensive Report...")
    report = create_fair_value_report(fair_value_result)
    
    if report['success']:
        print(f"[SUCCESS] Report generated successfully")
        print(f"   Report includes: scenarios, methodology, statistical validation, and recommendations")
        
        # You could save this report to JSON, CSV, or display in a web interface
        # Example: save_report_to_file(report, f"{fair_value_result.ticker}_fair_value_report.json")
    else:
        print(f"[ERROR] Report generation failed: {report.get('error', 'Unknown error')}")
    
    print(f"\n6. Summary:")
    signal_text = {"buy": "[BUY]", "sell": "[SELL]", "hold": "[HOLD]", "neutral": "[NEUTRAL]"}.get(fair_value_result.investment_signal, "[NEUTRAL]")
    print(f"   {signal_text} {fair_value_result.investment_signal.upper()} signal with {fair_value_result.signal_strength:.0%} confidence")
    
    if fair_value_result.investment_signal == "buy":
        upside = (fair_value_result.fair_scenario.target_price - current_price) / current_price
        print(f"   Potential upside: {upside:.1%} to fair value")
    elif fair_value_result.investment_signal == "sell":
        downside = (current_price - fair_value_result.fair_scenario.target_price) / current_price
        print(f"   Current overvaluation: {downside:.1%} above fair value")
    
    print("="*60)


def create_sample_data_response() -> DataSourceResponse:
    """
    Create sample data response for demonstration.
    
    In practice, this data would come from your data source adapter
    (Alpha Vantage, Financial Modeling Prep, yfinance, etc.)
    """
    
    # Sample data structure matching DataSourceResponse format
    sample_data = {
        'ticker': 'MSFT',
        'historical_prices': [
            {'date': '2024-01-01', 'close': 376.04},
            {'date': '2023-10-01', 'close': 348.10},
            {'date': '2023-07-01', 'close': 366.78},
            {'date': '2023-04-01', 'close': 325.29},
            {'date': '2023-01-01', 'close': 289.86},
            {'date': '2022-10-01', 'close': 279.33},
            {'date': '2022-07-01', 'close': 256.83},
            {'date': '2022-04-01', 'close': 309.40},
            {'date': '2022-01-01', 'close': 328.79},
            {'date': '2021-10-01', 'close': 315.75},
            {'date': '2021-07-01', 'close': 284.91},
            {'date': '2021-04-01', 'close': 252.57},
            {'date': '2021-01-01', 'close': 231.96},
            {'date': '2020-10-01', 'close': 215.25},
            {'date': '2020-07-01', 'close': 202.47},
            {'date': '2020-04-01', 'close': 181.40},
            {'date': '2020-01-01', 'close': 170.23},
            {'date': '2019-10-01', 'close': 139.14},
            {'date': '2019-07-01', 'close': 136.27},
            {'date': '2019-04-01', 'close': 130.06},
        ],
        'quarterly_balance_sheet': [
            {'date': '2024-01-01', 'total_shareholders_equity': 244090000000, 'common_shares_outstanding': 7430000000},
            {'date': '2023-10-01', 'total_shareholders_equity': 238600000000, 'common_shares_outstanding': 7420000000},
            {'date': '2023-07-01', 'total_shareholders_equity': 235800000000, 'common_shares_outstanding': 7400000000},
            {'date': '2023-04-01', 'total_shareholders_equity': 228300000000, 'common_shares_outstanding': 7410000000},
            {'date': '2023-01-01', 'total_shareholders_equity': 225400000000, 'common_shares_outstanding': 7400000000},
            {'date': '2022-10-01', 'total_shareholders_equity': 216200000000, 'common_shares_outstanding': 7390000000},
            {'date': '2022-07-01', 'total_shareholders_equity': 206223000000, 'common_shares_outstanding': 7380000000},
            {'date': '2022-04-01', 'total_shareholders_equity': 201500000000, 'common_shares_outstanding': 7370000000},
            {'date': '2022-01-01', 'total_shareholders_equity': 197100000000, 'common_shares_outstanding': 7360000000},
            {'date': '2021-10-01', 'total_shareholders_equity': 192800000000, 'common_shares_outstanding': 7350000000},
            {'date': '2021-07-01', 'total_shareholders_equity': 186300000000, 'common_shares_outstanding': 7340000000},
            {'date': '2021-04-01', 'total_shareholders_equity': 181500000000, 'common_shares_outstanding': 7330000000},
            {'date': '2021-01-01', 'total_shareholders_equity': 178200000000, 'common_shares_outstanding': 7320000000},
            {'date': '2020-10-01', 'total_shareholders_equity': 175100000000, 'common_shares_outstanding': 7310000000},
            {'date': '2020-07-01', 'total_shareholders_equity': 172800000000, 'common_shares_outstanding': 7300000000},
            {'date': '2020-04-01', 'total_shareholders_equity': 169400000000, 'common_shares_outstanding': 7290000000},
            {'date': '2020-01-01', 'total_shareholders_equity': 166500000000, 'common_shares_outstanding': 7280000000},
            {'date': '2019-10-01', 'total_shareholders_equity': 162200000000, 'common_shares_outstanding': 7270000000},
            {'date': '2019-07-01', 'total_shareholders_equity': 159400000000, 'common_shares_outstanding': 7260000000},
            {'date': '2019-04-01', 'total_shareholders_equity': 156800000000, 'common_shares_outstanding': 7250000000},
        ]
    }
    
    # Create DataSourceResponse object
    from data_sources import DataSourceResponse, DataSourceType, DataQualityMetrics
    
    quality_metrics = DataQualityMetrics()
    quality_metrics.completeness = 0.90
    quality_metrics.accuracy = 0.88
    quality_metrics.timeliness = 0.85
    quality_metrics.consistency = 0.92
    quality_metrics.calculate_overall_score()
    
    return DataSourceResponse(
        success=True,
        data=sample_data,
        source_type=DataSourceType.FINANCIAL_MODELING_PREP,  # List format matches FMP/Polygon
        quality_metrics=quality_metrics
    )


def advanced_fair_value_example():
    """
    Advanced example showing parameter customization and scenario analysis.
    """
    
    print("\n" + "="*60)
    print("Advanced Fair Value Analysis Example")
    print("="*60)
    
    # Create sample data
    sample_data = create_sample_data_response()
    
    # Perform historical analysis
    historical_engine = PBHistoricalAnalysisEngine()
    historical_result = historical_engine.analyze_historical_performance(sample_data, years=7)
    
    if not historical_result.success:
        print(f"Historical analysis failed: {historical_result.error_message}")
        return
    
    # Test different decay factors
    decay_factors = [0.75, 0.85, 0.95]  # More aggressive, standard, conservative weighting
    current_book_value = 28.50
    current_price = 385.00
    
    print(f"\nComparing Different Time Weighting Approaches:")
    print(f"{'Decay Factor':<15}{'Fair Value':<15}{'Signal':<10}{'Confidence':<12}")
    print("-" * 55)
    
    for decay in decay_factors:
        calculator = PBFairValueCalculator(decay_factor=decay)
        result = calculator.calculate_fair_value(historical_result, current_book_value, current_price)
        
        if result.success:
            print(f"{decay:<15.2f}${result.fair_scenario.target_price:<14.2f}{result.investment_signal:<10}{result.signal_strength:<12.1%}")
    
    # Sensitivity analysis - how sensitive is fair value to book value assumptions?
    print(f"\nSensitivity Analysis - Book Value Impact:")
    book_values = [26.0, 28.5, 31.0]  # ±10% around base case
    
    calculator = PBFairValueCalculator()
    
    print(f"{'Book Value':<15}{'Fair Value':<15}{'P/B Multiple':<15}{'Margin of Safety':<18}")
    print("-" * 65)
    
    for bv in book_values:
        result = calculator.calculate_fair_value(historical_result, bv, current_price)
        if result.success:
            margin = result.margin_of_safety
            print(f"${bv:<14.2f}${result.fair_scenario.target_price:<14.2f}{result.fair_scenario.pb_multiple:<15.2f}{margin:<18.1%}")


if __name__ == "__main__":
    """
    Run the examples when script is executed directly.
    """
    try:
        # Run basic example
        example_fair_value_calculation()
        
        # Run advanced example
        advanced_fair_value_example()
        
        print(f"\n[SUCCESS] Examples completed successfully!")
        print(f"\nNext steps:")
        print(f"1. Replace sample data with real data from your preferred source")
        print(f"2. Integrate with your existing analysis workflow")
        print(f"3. Customize parameters (decay_factor, confidence_threshold) for your needs")
        print(f"4. Add the report output to your investment research process")
        
    except Exception as e:
        logger.error(f"Example execution failed: {e}")
        print(f"[ERROR] Example failed: {e}")
        print(f"\nPlease check that all required modules are properly installed and accessible.")