"""
Streamlit Utility Functions
===========================

Common utility functions used across Streamlit components for financial analysis.
Extracted from fcf_analysis_streamlit.py to improve code organization and reusability.
"""

# Standard library imports
import os
from datetime import datetime
from typing import Optional, Any

# Third-party imports
import pandas as pd
import streamlit as st


def get_currency_symbol_per_share(financial_calculator) -> str:
    """
    Get currency symbol for per-share values display.
    
    Args:
        financial_calculator: FinancialCalculator instance
        
    Returns:
        str: Currency symbol for per-share values
    """
    if hasattr(financial_calculator, 'currency') and financial_calculator.currency:
        currency = financial_calculator.currency.upper()
        return f"{currency}/share"
    return "USD/share"  # Default fallback


def get_currency_symbol_financial(financial_calculator) -> str:
    """
    Get currency symbol for financial statement values display.
    
    Args:
        financial_calculator: FinancialCalculator instance
        
    Returns:
        str: Currency symbol for financial values
    """
    if hasattr(financial_calculator, 'currency') and financial_calculator.currency:
        currency = financial_calculator.currency.upper()
        return f"{currency} (Millions)"
    return "USD (Millions)"  # Default fallback


def get_currency_symbol(financial_calculator) -> str:
    """
    Get base currency symbol from financial calculator.
    
    Args:
        financial_calculator: FinancialCalculator instance
        
    Returns:
        str: Currency symbol
    """
    if hasattr(financial_calculator, 'currency') and financial_calculator.currency:
        return financial_calculator.currency.upper()
    return "USD"  # Default fallback


def get_financial_scale_and_unit(value: float, already_in_millions: bool = True) -> tuple[str, str]:
    """
    Determine appropriate scale and unit for displaying financial values.
    
    Args:
        value: Financial value to scale
        already_in_millions: Whether value is already in millions
        
    Returns:
        tuple: (scaled_value_str, unit_description)
    """
    if already_in_millions:
        # Value is already in millions
        if abs(value) >= 1000:
            return f"{value/1000:.2f}", "Billions"
        else:
            return f"{value:.2f}", "Millions"
    else:
        # Value is in actual units
        if abs(value) >= 1_000_000_000:
            return f"{value/1_000_000_000:.2f}", "Billions"
        elif abs(value) >= 1_000_000:
            return f"{value/1_000_000:.2f}", "Millions"
        elif abs(value) >= 1_000:
            return f"{value/1_000:.2f}", "Thousands"
        else:
            return f"{value:.2f}", "Units"


def save_fcf_analysis_to_file(fcf_df: pd.DataFrame, company_name: str, 
                             ticker: Optional[str] = None, output_dir: Optional[str] = None) -> str:
    """
    Save FCF analysis DataFrame to CSV file.
    
    Args:
        fcf_df: FCF analysis DataFrame
        company_name: Company name for filename
        ticker: Stock ticker (optional)
        output_dir: Output directory (optional)
        
    Returns:
        str: Path to saved file
    """
    try:
        # Create default output directory if not specified
        if output_dir is None:
            output_dir = "exports"
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ticker_part = f"_{ticker}" if ticker else ""
        filename = f"{company_name.replace(' ', '_')}{ticker_part}_FCF_Analysis_{timestamp}.csv"
        filepath = os.path.join(output_dir, filename)
        
        # Save to CSV
        fcf_df.to_csv(filepath, index=False)
        
        return filepath
        
    except Exception as e:
        st.error(f"Error saving FCF analysis: {str(e)}")
        raise


def is_tase_stock(financial_calculator) -> bool:
    """
    Check if the stock is from Tel Aviv Stock Exchange (TASE).
    
    Args:
        financial_calculator: FinancialCalculator instance
        
    Returns:
        bool: True if TASE stock, False otherwise
    """
    if not financial_calculator or not hasattr(financial_calculator, 'ticker_symbol'):
        return False
        
    ticker = getattr(financial_calculator, 'ticker_symbol', '')
    if not ticker:
        return False
        
    # TASE stocks typically end with .TA
    return ticker.upper().endswith('.TA')


def apply_market_selection_to_ticker(ticker: str, market_selection: str) -> str:
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


def format_financial_value(value: Any, currency_symbol: str = "USD", 
                          scale: str = "Millions") -> str:
    """
    Format financial value for display in Streamlit.
    
    Args:
        value: Value to format
        currency_symbol: Currency symbol
        scale: Scale description (Millions, Billions, etc.)
        
    Returns:
        str: Formatted value string
    """
    if pd.isna(value) or value is None:
        return "N/A"
        
    try:
        if isinstance(value, (int, float)):
            return f"{value:,.2f} {currency_symbol} ({scale})"
        else:
            return str(value)
    except (ValueError, TypeError):
        return "N/A"


def initialize_session_state_defaults():
    """Initialize default values for Streamlit session state."""
    defaults = {
        'fcf_results': None,
        'financial_calculator': None,
        'dcf_results': None,
        'ddm_results': None,
        'pb_results': None,
        'report_data': None,
        'selected_company_path': None,
        'selected_ticker': None,
        'data_source': 'Excel',
        'preferred_api_source': 'yfinance',
        'market_selection': 'US Markets'
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value