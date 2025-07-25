#!/usr/bin/env python3
"""
Test script to verify field mapping fix
"""

import yfinance as yf
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_field_mapping_fix():
    """Test the field mapping fix"""
    
    print("Testing field mapping fix for AAPL...")
    
    # Get AAPL data
    ticker = yf.Ticker("AAPL")
    income_stmt = ticker.financials
    balance_sheet = ticker.balance_sheet
    cash_flow = ticker.cashflow
    
    # Import the conversion function
    from fcf_analysis_streamlit import _convert_yfinance_to_calculator_format
    
    # Convert the data
    financial_data = _convert_yfinance_to_calculator_format(
        income_stmt, balance_sheet, cash_flow, "AAPL"
    )
    
    # Check what fields we have now
    print("\n=== Converted Financial Data Structure ===")
    for data_type, df in financial_data.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            print(f"\n{data_type.upper()}:")
            print(f"  Shape: {df.shape}")
            print(f"  Columns: {list(df.columns)}")
            
            # Check for required fields
            required_by_type = {
                'income_fy': ['Net Income', 'EBIT', 'EBT', 'Income Tax Expense'],
                'balance_fy': ['Total Current Assets', 'Total Current Liabilities'],
                'cashflow_fy': ['Depreciation & Amortization', 'Cash from Operations', 'Capital Expenditure']
            }
            
            if data_type in required_by_type:
                found_fields = []
                missing_fields = []
                for req_field in required_by_type[data_type]:
                    if req_field in df.columns:
                        found_fields.append(req_field)
                    else:
                        missing_fields.append(req_field)
                
                print(f"  ✅ Found required fields: {found_fields}")
                if missing_fields:
                    print(f"  ❌ Missing required fields: {missing_fields}")
    
    # Test with centralized data processor
    print("\n=== Testing with Centralized Data Processor ===")
    try:
        from centralized_data_manager import CentralizedDataManager
        from centralized_data_processor import CentralizedDataProcessor
        
        # Create data manager and save the converted data
        data_manager = CentralizedDataManager(".")
        
        # Mock the data as if it was loaded from Excel
        data_manager._memory_cache["test_excel_data"] = financial_data
        
        # Create processor and test metrics extraction
        processor = CentralizedDataProcessor(data_manager)
        
        # We'll need to mock the company folder for testing
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create mock company structure
            company_folder = os.path.join(temp_dir, "AAPL")
            os.makedirs(company_folder)
            
            # Save the converted data to temporary Excel files
            fy_dir = os.path.join(company_folder, "FY")
            os.makedirs(fy_dir)
            
            if 'income_fy' in financial_data:
                financial_data['income_fy'].to_excel(os.path.join(fy_dir, "Income Statement.xlsx"))
            if 'balance_fy' in financial_data:
                financial_data['balance_fy'].to_excel(os.path.join(fy_dir, "Balance Sheet.xlsx"))
            if 'cashflow_fy' in financial_data:
                financial_data['cashflow_fy'].to_excel(os.path.join(fy_dir, "Cash Flow Statement.xlsx"))
            
            # Test the processor
            data_manager_test = CentralizedDataManager(temp_dir)
            processor_test = CentralizedDataProcessor(data_manager_test)
            
            result = processor_test.extract_financial_metrics("AAPL")
            
            if result.success:
                print("✅ SUCCESS: Centralized data processor can now extract metrics!")
                print(f"  Errors: {len(result.errors)}")
                print(f"  Warnings: {len(result.warnings)}")
                
                # Show extracted metrics
                if result.data:
                    metrics = result.data
                    print(f"  Net Income: {len(metrics.net_income)} years")
                    print(f"  EBIT: {len(metrics.ebit)} years") 
                    print(f"  Current Assets: {len(metrics.current_assets)} years")
            else:
                print("❌ FAILED: Still have issues with data extraction")
                print(f"  Errors: {result.errors}")
                
    except Exception as e:
        print(f"❌ Error testing with centralized processor: {e}")

if __name__ == "__main__":
    test_field_mapping_fix()