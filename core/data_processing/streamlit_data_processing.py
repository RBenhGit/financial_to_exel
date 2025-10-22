"""
Streamlit Data Processing Module
===============================

Data processing and business logic functions extracted from fcf_analysis_streamlit.py.
Handles data transformation, validation, and integration between different data sources.
"""

# Standard library imports
import logging
from typing import Dict, Any, Optional, Tuple

# Third-party imports
import pandas as pd
import streamlit as st

# Local imports
from ..analysis.engines.financial_calculations import FinancialCalculator
from .managers.enhanced_data_manager import EnhancedDataManager
from error_handler import EnhancedLogger

# Set up logging
logger = EnhancedLogger(__name__)


def convert_yfinance_to_calculator_format(income_stmt: pd.DataFrame, 
                                        balance_sheet: pd.DataFrame,
                                        cash_flow: pd.DataFrame, 
                                        ticker: str) -> Dict[str, Any]:
    """
    Convert yfinance financial statement data to FinancialCalculator expected format.

    Args:
        income_stmt: YFinance income statement DataFrame
        balance_sheet: YFinance balance sheet DataFrame  
        cash_flow: YFinance cash flow statement DataFrame
        ticker: Stock ticker symbol

    Returns:
        dict: Financial data in calculator format
    """
    try:
        logger.info(f"Converting yfinance data for ticker: {ticker}")
        
        # Initialize result dictionary
        financial_data = {
            'ticker': ticker,
            'currency': 'USD',  # YFinance typically returns USD
            'periods': [],
            'income_statement': {},
            'balance_sheet': {},
            'cash_flow': {}
        }
        
        # Get periods from data (typically years)
        if not income_stmt.empty:
            periods = income_stmt.columns.tolist()
            financial_data['periods'] = [str(period.year) if hasattr(period, 'year') else str(period) 
                                       for period in periods]
        
        # Convert income statement
        if not income_stmt.empty:
            financial_data['income_statement'] = _convert_dataframe_to_dict(income_stmt)
            
        # Convert balance sheet
        if not balance_sheet.empty:
            financial_data['balance_sheet'] = _convert_dataframe_to_dict(balance_sheet)
            
        # Convert cash flow statement
        if not cash_flow.empty:
            financial_data['cash_flow'] = _convert_dataframe_to_dict(cash_flow)
        
        logger.info(f"Successfully converted yfinance data for {ticker}")
        return financial_data
        
    except Exception as e:
        logger.error(f"Error converting yfinance data for {ticker}: {str(e)}")
        raise


def _convert_dataframe_to_dict(df: pd.DataFrame) -> Dict[str, Dict]:
    """
    Convert pandas DataFrame to nested dictionary format.
    
    Args:
        df: DataFrame to convert
        
    Returns:
        dict: Nested dictionary with period and metric data
    """
    result = {}
    
    for column in df.columns:
        period_key = str(column.year) if hasattr(column, 'year') else str(column)
        result[period_key] = {}
        
        for index in df.index:
            value = df.loc[index, column]
            if pd.notna(value):
                result[period_key][str(index)] = float(value)
                
    return result


def create_ticker_mode_calculator(ticker_symbol: str, 
                                market_selection: str,
                                preferred_source: Optional[str] = None) -> Tuple[Optional[FinancialCalculator], str]:
    """
    Create FinancialCalculator instance using ticker symbol and API data sources.
    
    Args:
        ticker_symbol: Stock ticker symbol
        market_selection: Selected market (US, TASE, etc.)
        preferred_source: Preferred API source
        
    Returns:
        tuple: (FinancialCalculator instance or None, status message)
    """
    try:
        logger.info(f"Creating calculator for ticker: {ticker_symbol}, market: {market_selection}")
        
        # Apply market selection to ticker
        formatted_ticker = _apply_market_selection_to_ticker(ticker_symbol, market_selection)
        
        # Initialize enhanced data manager with correct base path for Excel files
        data_manager = EnhancedDataManager(base_path="./data/companies")
        
        # Attempt to fetch data using available method
        financial_data = data_manager.fetch_market_data(formatted_ticker)
        
        if not financial_data:
            return None, f"❌ Unable to fetch financial data for {formatted_ticker}"
        
        # Create calculator instance
        calculator = FinancialCalculator()
        calculator.load_from_dict(financial_data)
        calculator.ticker_symbol = formatted_ticker
        
        return calculator, f"✅ Successfully loaded data for {formatted_ticker}"
        
    except Exception as e:
        error_msg = f"Error creating calculator for {ticker_symbol}: {str(e)}"
        logger.error(error_msg)
        return None, f"❌ {error_msg}"


def _apply_market_selection_to_ticker(ticker: str, market_selection: str) -> str:
    """
    Apply market suffix to ticker based on market selection.
    
    Args:
        ticker: Base ticker symbol
        market_selection: Selected market
        
    Returns:
        str: Ticker with appropriate market suffix
    """
    if not ticker:
        return ticker
        
    # Remove existing suffixes
    base_ticker = ticker.split('.')[0]
    
    # Apply market suffix based on selection
    if market_selection == "TASE (Tel Aviv)":
        return f"{base_ticker}.TA"
    elif market_selection == "US Markets":
        return base_ticker  # US markets typically don't need suffix
    else:
        return ticker  # Return original if unknown market


def centralized_data_loader(ticker_symbol: Optional[str] = None, 
                          company_path: Optional[str] = None) -> Tuple[Optional[FinancialCalculator], str]:
    """
    Centralized data loading function supporting both Excel files and API sources.
    
    Args:
        ticker_symbol: Stock ticker for API data loading
        company_path: Path to Excel files for file-based loading
        
    Returns:
        tuple: (FinancialCalculator instance or None, status message)
    """
    try:
        if ticker_symbol:
            # API-based loading
            market_selection = st.session_state.get('market_selection', 'US Markets')
            preferred_source = st.session_state.get('preferred_api_source', 'yfinance')
            
            return create_ticker_mode_calculator(ticker_symbol, market_selection, preferred_source)
            
        elif company_path:
            # Excel-based loading
            calculator = FinancialCalculator()
            calculator.load_from_excel(company_path)
            
            return calculator, f"✅ Successfully loaded Excel data from {company_path}"
            
        else:
            return None, "❌ No ticker symbol or company path provided"
            
    except Exception as e:
        error_msg = f"Error in centralized data loader: {str(e)}"
        logger.error(error_msg)
        return None, f"❌ {error_msg}"


def validate_financial_data(financial_calculator: FinancialCalculator) -> Tuple[bool, list]:
    """
    Validate loaded financial data for completeness and consistency.
    
    Args:
        financial_calculator: FinancialCalculator instance to validate
        
    Returns:
        tuple: (is_valid, list_of_validation_issues)
    """
    validation_issues = []
    
    try:
        # Check if calculator has basic data
        if not financial_calculator:
            validation_issues.append("No financial calculator provided")
            return False, validation_issues
        
        # Check for required financial statements
        if not hasattr(financial_calculator, 'financial_data') or not financial_calculator.financial_data:
            validation_issues.append("No financial data loaded")
            return False, validation_issues
        
        # Check for income statement data
        income_data = getattr(financial_calculator, 'income_statement_data', None)
        if not income_data or income_data.empty:
            validation_issues.append("Income statement data missing or empty")
        
        # Check for balance sheet data
        balance_data = getattr(financial_calculator, 'balance_sheet_data', None)
        if not balance_data or balance_data.empty:
            validation_issues.append("Balance sheet data missing or empty")
        
        # Check for cash flow data
        cashflow_data = getattr(financial_calculator, 'cash_flow_data', None)
        if not cashflow_data or cashflow_data.empty:
            validation_issues.append("Cash flow statement data missing or empty")
        
        # Check for minimum required periods (at least 2 years for analysis)
        if hasattr(financial_calculator, 'periods') and len(financial_calculator.periods) < 2:
            validation_issues.append("Insufficient historical periods (minimum 2 years required)")
        
        is_valid = len(validation_issues) == 0
        return is_valid, validation_issues
        
    except Exception as e:
        validation_issues.append(f"Validation error: {str(e)}")
        return False, validation_issues


def get_data_quality_metrics(financial_calculator: FinancialCalculator) -> Dict[str, Any]:
    """
    Calculate data quality metrics for loaded financial data.
    
    Args:
        financial_calculator: FinancialCalculator instance
        
    Returns:
        dict: Data quality metrics
    """
    try:
        metrics = {
            'completeness': 0.0,
            'consistency': 0.0,
            'coverage_years': 0,
            'data_source': 'Unknown',
            'missing_fields': [],
            'quality_score': 0.0
        }
        
        if not financial_calculator:
            return metrics
        
        # Calculate completeness
        total_fields = 0
        populated_fields = 0
        
        for statement_type in ['income_statement_data', 'balance_sheet_data', 'cash_flow_data']:
            if hasattr(financial_calculator, statement_type):
                data = getattr(financial_calculator, statement_type)
                if data is not None and not data.empty:
                    total_fields += data.size
                    populated_fields += data.count().sum()
        
        if total_fields > 0:
            metrics['completeness'] = (populated_fields / total_fields) * 100
        
        # Calculate coverage years
        if hasattr(financial_calculator, 'periods'):
            metrics['coverage_years'] = len(financial_calculator.periods)
        
        # Determine data source
        if hasattr(financial_calculator, 'data_source'):
            metrics['data_source'] = financial_calculator.data_source
        
        # Calculate overall quality score
        metrics['quality_score'] = (metrics['completeness'] + 
                                  (metrics['coverage_years'] * 10)) / 2
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error calculating data quality metrics: {str(e)}")
        return metrics