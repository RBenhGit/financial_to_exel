"""
Modern FCF Analysis Application using Streamlit

Modern, responsive web interface for comprehensive FCF and DCF analysis.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from pathlib import Path
import logging

try:
    import tkinter as tk
    from tkinter.filedialog import askdirectory

    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Import our custom modules
from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator
from ddm_valuation import DDMValuator
from pb_valuation import PBValuator
from pb_visualizer import display_pb_analysis
from data_processing import DataProcessor
from report_generator import FCFReportGenerator
from fcf_consolidated import FCFCalculator, calculate_fcf_growth_rates
from config import (
    get_default_company_name,
    get_unknown_company_name,
    get_unknown_fcf_type,
    get_unknown_ticker,
    get_export_directory,
    set_user_export_directory,
    get_export_config,
    ensure_export_directory,
)
from watch_list_manager import WatchListManager
from analysis_capture import analysis_capture
from watch_list_visualizer import watch_list_visualizer
from enhanced_data_manager import create_enhanced_data_manager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="FCF Analysis Tool", page_icon="📊", layout="wide", initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 1.2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-card {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .warning-card {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""",
    unsafe_allow_html=True,
)


def _apply_market_selection_to_ticker(ticker, market_selection):
    """
    Apply market selection logic to ticker symbol processing.

    Args:
        ticker (str): Original ticker symbol
        market_selection (str): Selected market ("US Market" or "TASE (Tel Aviv)")

    Returns:
        str: Processed ticker symbol with appropriate suffix
    """
    if not ticker:
        return ticker

    if market_selection == "TASE (Tel Aviv)":
        # For TASE selection, ensure .TA suffix
        if not ticker.endswith('.TA'):
            return f"{ticker}.TA"
        return ticker
    else:
        # For US Market selection, remove .TA suffix if present
        if ticker.endswith('.TA'):
            return ticker[:-3]  # Remove .TA suffix
        return ticker


def create_ticker_mode_calculator(ticker_symbol, market_selection, preferred_source=None):
    """
    Create a FinancialCalculator instance using API data only (no Excel files).

    Args:
        ticker_symbol (str): Stock ticker symbol
        market_selection (str): Selected market ("US Market" or "TASE (Tel Aviv)")
        preferred_source (str, optional): Preferred data source ('yfinance', 'alpha_vantage', 'fmp', 'polygon')

    Returns:
        FinancialCalculator or None: Calculator instance with API data
    """
    try:
        import yfinance as yf
        import pandas as pd

        # Apply market selection to ticker
        processed_ticker = _apply_market_selection_to_ticker(ticker_symbol, market_selection)

        # Create enhanced data manager for API access
        data_manager = create_enhanced_data_manager()

        # Configure preferred source if specified
        actual_source_used = "Auto"
        if preferred_source:
            try:
                # If user specified a preferred source, try to use it specifically
                if preferred_source != "yfinance":
                    # For non-yfinance sources, try to use the unified adapter with specific source
                    from data_sources import DataSourceType, FinancialDataRequest

                    source_type_mapping = {
                        'alpha_vantage': DataSourceType.ALPHA_VANTAGE,
                        'fmp': DataSourceType.FINANCIAL_MODELING_PREP,
                        'polygon': DataSourceType.POLYGON,
                    }

                    if preferred_source in source_type_mapping:
                        request = FinancialDataRequest(
                            ticker=processed_ticker,
                            data_types=['price', 'fundamentals'],
                            force_refresh=True,
                        )

                        # Try the preferred source first
                        preferred_source_type = source_type_mapping[preferred_source]
                        if preferred_source_type in data_manager.unified_adapter.providers:
                            provider = data_manager.unified_adapter.providers[preferred_source_type]
                            response = provider.fetch_data(request)
                            if response.success and response.data:
                                market_data = {
                                    'current_price': response.data.get('current_price'),
                                    'market_cap': response.data.get('market_cap'),
                                    'shares_outstanding': response.data.get('shares_outstanding'),
                                    'company_name': response.data.get(
                                        'company_name', processed_ticker
                                    ),
                                }
                                # Use proper display names
                                source_display_names = {
                                    'alpha_vantage': 'Alpha Vantage',
                                    'fmp': 'Financial Modeling Prep',
                                    'polygon': 'Polygon.io',
                                }
                                actual_source_used = source_display_names.get(
                                    preferred_source, preferred_source.replace('_', ' ').title()
                                )
                            else:
                                market_data = None
                        else:
                            market_data = None
                    else:
                        market_data = None
                else:
                    # For yfinance preference, use it directly
                    market_data = data_manager.fetch_market_data(processed_ticker)
                    actual_source_used = "Yahoo Finance"

            except Exception as e:
                logger.warning(f"Failed to use preferred source {preferred_source}: {e}")
                market_data = None
        else:
            market_data = None

        # Fallback to automatic source selection if preferred source failed or not specified
        if not market_data:
            market_data = data_manager.fetch_market_data(processed_ticker)
            if market_data:
                # Try to determine which source was actually used
                if hasattr(data_manager, '_data_source_used'):
                    actual_source_used = data_manager._data_source_used
                else:
                    actual_source_used = "Auto (Multiple Sources)"

        if not market_data:
            return None, f"Could not fetch market data for ticker: {processed_ticker}"

        # Fetch financial statements via yfinance
        yf_ticker = yf.Ticker(processed_ticker)

        # Get financial statements
        income_stmt = yf_ticker.financials
        balance_sheet = yf_ticker.balance_sheet
        cash_flow = yf_ticker.cashflow

        if income_stmt.empty or cash_flow.empty:
            return None, f"Could not fetch financial statements for ticker: {processed_ticker}"

        # Create a minimal FinancialCalculator instance
        # We'll use a temporary folder approach to satisfy the constructor
        temp_folder = f"temp_{processed_ticker}"
        calculator = FinancialCalculator(temp_folder)

        # Attach enhanced data manager for multi-source data access
        try:
            enhanced_data_manager = create_enhanced_data_manager()
            calculator.enhanced_data_manager = enhanced_data_manager
            logger.info(
                f"Enhanced data manager attached to ticker mode calculator for {processed_ticker}"
            )
        except Exception as e:
            logger.warning(f"Could not attach enhanced data manager to ticker mode calculator: {e}")

        # Override the ticker and market data
        calculator.ticker_symbol = processed_ticker
        calculator.current_stock_price = market_data.get('current_price')
        calculator.market_cap = market_data.get('market_cap')
        calculator.shares_outstanding = market_data.get('shares_outstanding', 0)
        calculator.company_name = market_data.get('company_name', processed_ticker)

        # Set currency and market info based on selection
        if market_selection == "TASE (Tel Aviv)":
            calculator.is_tase_stock = True
            calculator.currency = 'ILS'
            calculator.financial_currency = 'ILS'
        else:
            calculator.is_tase_stock = False
            calculator.currency = 'USD'
            calculator.financial_currency = 'USD'

        # Convert yfinance data to calculator format
        calculator.financial_data = _convert_yfinance_to_calculator_format(
            income_stmt, balance_sheet, cash_flow, processed_ticker
        )

        # Override the load_financial_statements method to use API data
        def load_financial_statements_api():
            """Override method to use API data instead of Excel files"""
            # Data is already loaded in calculator.financial_data
            logger.info("Using API financial data for FCF calculations")
            # Clear cached metrics when new data is loaded
            calculator.metrics = {}
            calculator.metrics_calculated = False

        # Replace the method
        calculator.load_financial_statements = load_financial_statements_api

        # Store the data manager reference for future use
        calculator._data_manager = data_manager
        calculator._data_source_used = actual_source_used
        calculator._has_api_financial_data = True

        return calculator, None

    except Exception as e:
        logger.error(f"Error creating ticker mode calculator for {ticker_symbol}: {e}")
        return None, str(e)


def _convert_yfinance_to_calculator_format(income_stmt, balance_sheet, cash_flow, ticker):
    """
    Convert yfinance financial statement data to FinancialCalculator expected format.

    Args:
        income_stmt (pd.DataFrame): YFinance income statement
        balance_sheet (pd.DataFrame): YFinance balance sheet
        cash_flow (pd.DataFrame): YFinance cash flow statement
        ticker (str): Stock ticker symbol

    Returns:
        dict: Financial data in calculator format
    """
    try:
        import pandas as pd
        import numpy as np

        # Field mappings from yfinance names to expected names
        FIELD_MAPPINGS = {
            # Income Statement
            'Net Income Common Stockholders': 'Net Income',
            'Net Income': 'Net Income',
            'EBIT': 'EBIT',
            'Pretax Income': 'EBT',
            'Tax Provision': 'Income Tax Expense',
            # Balance Sheet
            'Current Assets': 'Total Current Assets',
            'Current Liabilities': 'Total Current Liabilities',
            # Cash Flow
            'Depreciation And Amortization': 'Depreciation & Amortization',
            'Operating Cash Flow': 'Cash from Operations',
            'Capital Expenditure': 'Capital Expenditure',
            'Long Term Debt Issuance': 'Long-Term Debt Issued',
            'Long Term Debt Payments': 'Long-Term Debt Repaid',
        }

        def _rename_columns(df):
            """Rename DataFrame columns using field mappings"""
            if df.empty:
                return df

            # Create a copy to avoid modifying original
            df_renamed = df.copy()

            # Rename columns using exact matches
            rename_dict = {}
            for old_name, new_name in FIELD_MAPPINGS.items():
                if old_name in df_renamed.columns:
                    rename_dict[old_name] = new_name

            if rename_dict:
                df_renamed = df_renamed.rename(columns=rename_dict)
                logger.debug(f"Renamed fields: {rename_dict}")

            return df_renamed

        # Initialize financial data structure
        financial_data = {}

        # Convert income statement (use most recent 4 years as "FY" data)
        if not income_stmt.empty:
            # Transpose to have years as rows and metrics as columns
            income_transposed = income_stmt.T
            income_transposed.index = pd.to_datetime(income_transposed.index)
            income_transposed = income_transposed.sort_index()  # Sort by year

            # Rename columns to match expected field names
            income_transposed = _rename_columns(income_transposed)

            # Use the most recent data as current
            financial_data['income_fy'] = income_transposed
            financial_data['income_ltm'] = (
                income_transposed.iloc[-1:] if len(income_transposed) > 0 else income_transposed
            )

        # Convert balance sheet
        if not balance_sheet.empty:
            balance_transposed = balance_sheet.T
            balance_transposed.index = pd.to_datetime(balance_transposed.index)
            balance_transposed = balance_transposed.sort_index()

            # Rename columns to match expected field names
            balance_transposed = _rename_columns(balance_transposed)

            financial_data['balance_fy'] = balance_transposed
            financial_data['balance_ltm'] = (
                balance_transposed.iloc[-1:] if len(balance_transposed) > 0 else balance_transposed
            )

        # Convert cash flow statement
        if not cash_flow.empty:
            cash_transposed = cash_flow.T
            cash_transposed.index = pd.to_datetime(cash_transposed.index)
            cash_transposed = cash_transposed.sort_index()

            # Rename columns to match expected field names
            cash_transposed = _rename_columns(cash_transposed)

            financial_data['cashflow_fy'] = cash_transposed
            financial_data['cashflow_ltm'] = (
                cash_transposed.iloc[-1:] if len(cash_transposed) > 0 else cash_transposed
            )

        logger.info(f"Successfully converted yfinance data for {ticker}")
        return financial_data

    except Exception as e:
        logger.error(f"Error converting yfinance data for {ticker}: {e}")
        return {}


def render_centralized_data_settings():
    """Render centralized data input settings that apply to all tabs"""
    st.sidebar.subheader("⚙️ Data Input Settings")

    # Data source preference for all tabs
    data_source_options = {
        'auto': 'Auto (Smart Selection)',
        'api_first': 'API First (Excel Fallback)',
        'excel_first': 'Excel First (API Fallback)',
        'api_only': 'API Only',
        'excel_only': 'Excel Files Only',
    }

    selected_source = st.sidebar.selectbox(
        "Data Source Priority:",
        options=list(data_source_options.keys()),
        format_func=lambda x: data_source_options[x],
        index=0,
        help="This setting applies to ALL analysis tabs (FCF, DCF, DDM, P/B)",
    )

    # Update session state
    st.session_state.data_input_settings['preferred_source'] = selected_source
    st.session_state.centralized_data_source = selected_source

    # API Priority order (only show if API is enabled)
    if selected_source not in ['excel_only']:
        with st.sidebar.expander("🔧 API Priority Order", expanded=False):
            api_sources = ['yfinance', 'alpha_vantage', 'fmp', 'polygon']
            st.markdown("**API Source Priority Order:**")

            # Simple reorderable list display
            for i, source in enumerate(st.session_state.data_input_settings['api_priority']):
                st.markdown(f"{i+1}. {source.title()}")

            # Reset to default option
            if st.button("🔄 Reset to Default Order", key="reset_api_order"):
                st.session_state.data_input_settings['api_priority'] = [
                    'yfinance',
                    'alpha_vantage',
                    'fmp',
                    'polygon',
                ]
                st.rerun()

    # Show current effective settings
    with st.sidebar.expander("📊 Current Settings", expanded=False):
        st.json(st.session_state.data_input_settings)

    # Global data source indicator
    if selected_source == 'auto':
        st.sidebar.info("🤖 Auto mode: Intelligent source selection based on data availability")
    elif selected_source == 'api_first':
        st.sidebar.info("🌐 API Priority: All tabs will prefer API data with Excel backup")
    elif selected_source == 'excel_first':
        st.sidebar.info("📁 Excel Priority: All tabs will prefer Excel files with API backup")
    elif selected_source == 'api_only':
        st.sidebar.warning("🌐 API Only: Excel files will be ignored in all tabs")
    elif selected_source == 'excel_only':
        st.sidebar.warning("📁 Excel Only: API data will be ignored in all tabs")


def centralized_data_loader(ticker_symbol=None, company_path=None):
    """
    Centralized data loading function that respects user's data source preferences.
    This function is used by all tabs to ensure consistent data loading behavior.

    Args:
        ticker_symbol (str): Stock ticker symbol for API loading
        company_path (str): Path to company folder for Excel loading

    Returns:
        tuple: (success, financial_calculator, error_message)
    """
    settings = st.session_state.data_input_settings
    preferred_source = settings['preferred_source']

    financial_calculator = None
    error_message = None

    try:
        if preferred_source == 'excel_only':
            # Force Excel loading only
            if company_path and Path(company_path).exists():
                financial_calculator = FinancialCalculator(company_path)
                return True, financial_calculator, None
            else:
                return False, None, "Excel files required but company folder not found or invalid"

        elif preferred_source == 'api_only':
            # Force API loading only
            if ticker_symbol:
                financial_calculator, error_message = create_ticker_mode_calculator(
                    ticker_symbol,
                    st.session_state.get('selected_market', 'US Market'),
                    st.session_state.get('preferred_data_source'),
                )
                return financial_calculator is not None, financial_calculator, error_message
            else:
                return False, None, "API data required but no ticker symbol provided"

        elif preferred_source == 'excel_first':
            # Try Excel first, fallback to API
            if company_path and Path(company_path).exists():
                try:
                    financial_calculator = FinancialCalculator(company_path)
                    return True, financial_calculator, None
                except Exception as e:
                    logger.warning(f"Excel loading failed, trying API: {e}")

            # Fallback to API
            if ticker_symbol:
                financial_calculator, error_message = create_ticker_mode_calculator(
                    ticker_symbol,
                    st.session_state.get('selected_market', 'US Market'),
                    st.session_state.get('preferred_data_source'),
                )
                return financial_calculator is not None, financial_calculator, error_message
            else:
                return False, None, "Both Excel and API loading failed"

        elif preferred_source == 'api_first':
            # Try API first, fallback to Excel
            if ticker_symbol:
                try:
                    financial_calculator, error_message = create_ticker_mode_calculator(
                        ticker_symbol,
                        st.session_state.get('selected_market', 'US Market'),
                        st.session_state.get('preferred_data_source'),
                    )
                    if financial_calculator is not None:
                        return True, financial_calculator, None
                except Exception as e:
                    logger.warning(f"API loading failed, trying Excel: {e}")

            # Fallback to Excel
            if company_path and Path(company_path).exists():
                financial_calculator = FinancialCalculator(company_path)
                return True, financial_calculator, None
            else:
                return False, None, "Both API and Excel loading failed"

        else:  # 'auto' mode
            # Intelligent selection based on data availability
            success_excel = company_path and Path(company_path).exists()
            success_api = ticker_symbol is not None

            # Prefer the source with better data availability
            if success_excel and success_api:
                # Both available, try API first (faster)
                try:
                    financial_calculator, error_message = create_ticker_mode_calculator(
                        ticker_symbol,
                        st.session_state.get('selected_market', 'US Market'),
                        st.session_state.get('preferred_data_source'),
                    )
                    if financial_calculator is not None:
                        return True, financial_calculator, None
                except Exception:
                    pass

                # Fallback to Excel
                financial_calculator = FinancialCalculator(company_path)
                return True, financial_calculator, None

            elif success_api:
                financial_calculator, error_message = create_ticker_mode_calculator(
                    ticker_symbol,
                    st.session_state.get('selected_market', 'US Market'),
                    st.session_state.get('preferred_data_source'),
                )
                return financial_calculator is not None, financial_calculator, error_message

            elif success_excel:
                financial_calculator = FinancialCalculator(company_path)
                return True, financial_calculator, None
            else:
                return False, None, "No valid data source available"

    except Exception as e:
        logger.error(f"Error in centralized data loader: {e}")
        return False, None, f"Data loading error: {str(e)}"


def render_centralized_data_source_info():
    """Display current data source information consistently across all tabs"""
    if not st.session_state.financial_calculator:
        return

    # Get current settings
    settings = st.session_state.data_input_settings
    preferred_source = settings['preferred_source']

    # Get actual data source used
    actual_source = getattr(st.session_state.financial_calculator, '_data_source_used', 'Unknown')
    has_api_data = getattr(st.session_state.financial_calculator, '_has_api_financial_data', False)

    # Create info box
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        if preferred_source == 'auto':
            st.info("🤖 **Data Mode:** Auto Selection")
        elif preferred_source == 'api_first':
            st.info("🌐 **Data Mode:** API Priority")
        elif preferred_source == 'excel_first':
            st.info("📁 **Data Mode:** Excel Priority")
        elif preferred_source == 'api_only':
            st.info("🌐 **Data Mode:** API Only")
        elif preferred_source == 'excel_only':
            st.info("📁 **Data Mode:** Excel Only")

    with col2:
        if has_api_data:
            st.success(f"✅ **Source Used:** {actual_source}")
        else:
            st.success("✅ **Source Used:** Excel Files")

    with col3:
        # Show data quality indicator
        if st.session_state.fcf_results:
            try:
                calculated_types = [
                    k
                    for k, v in st.session_state.fcf_results.items()
                    if v is not None and hasattr(v, 'empty') and not v.empty
                ]
                if calculated_types:
                    st.metric("📊 FCF Types", len(calculated_types))
                else:
                    st.metric("📊 FCF Types", "0", delta="No data")
            except Exception:
                st.metric("📊 FCF Types", "Error")
        else:
            st.metric("📊 FCF Types", "Not calculated")


def initialize_session_state():
    """Initialize session state variables"""
    if 'financial_calculator' not in st.session_state:
        st.session_state.financial_calculator = None
    if 'dcf_valuator' not in st.session_state:
        st.session_state.dcf_valuator = None
    if 'data_processor' not in st.session_state:
        st.session_state.data_processor = DataProcessor()

    # Reinitialize DataProcessor if it doesn't have the new method (for compatibility)
    if not hasattr(st.session_state.data_processor, 'create_average_fcf_plot'):
        st.session_state.data_processor = DataProcessor()
    if 'company_folder' not in st.session_state:
        st.session_state.company_folder = None
    if 'ticker_symbol' not in st.session_state:
        st.session_state.ticker_symbol = ""
    if 'fcf_results' not in st.session_state:
        st.session_state.fcf_results = {}
    if 'dcf_results' not in st.session_state:
        st.session_state.dcf_results = {}
    if 'watch_list_manager' not in st.session_state:
        st.session_state.watch_list_manager = WatchListManager()
    if 'current_watch_list' not in st.session_state:
        st.session_state.current_watch_list = None
    if 'centralized_data_source' not in st.session_state:
        st.session_state.centralized_data_source = 'auto'
    if 'data_input_settings' not in st.session_state:
        st.session_state.data_input_settings = {
            'preferred_source': 'auto',
            'fallback_enabled': True,
            'api_priority': ['yfinance', 'alpha_vantage', 'fmp', 'polygon'],
            'force_excel': False,
        }


def render_sidebar():
    """Render the sidebar with file selection and settings"""
    st.sidebar.title("📊 FCF Analysis Tool")
    st.sidebar.markdown("---")

    # Market selection
    st.sidebar.subheader("🌍 Market Selection")

    # Market selection radio buttons
    market_selection = st.sidebar.radio(
        "Select Stock Market:",
        options=["US Market", "TASE (Tel Aviv)"],
        index=0,  # Default to US Market
        help="Choose the stock exchange for ticker symbol processing",
    )

    # Store market selection in session state
    st.session_state.selected_market = market_selection

    # Show market-specific ticker format examples
    if market_selection == "US Market":
        st.sidebar.info("💡 **US Market examples:** AAPL, MSFT, GOOGL")
    else:
        st.sidebar.info("💡 **TASE examples:** TEVA.TA, ICL.TA, ELBIT.TA")

    st.sidebar.markdown("---")

    # Company folder selection
    st.sidebar.subheader("📁 Data Source")

    # Add mode selection
    data_mode = st.sidebar.radio(
        "Choose data input method:",
        ["📁 Folder Mode (Excel Files)", "🌐 Ticker Mode (API Data)"],
        index=1,  # Default to Ticker Mode for better user experience
        help="Folder Mode: Use local Excel files | Ticker Mode: Fetch data via APIs",
    )

    # Initialize variables
    company_path = ""
    ticker_symbol = ""

    if data_mode == "📁 Folder Mode (Excel Files)":
        # Show folder structure help
        st.sidebar.markdown("**Expected folder structure:**")
        st.sidebar.code(
            """
<COMPANY>/
├── FY/
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx  
│   └── Cash Flow Statement.xlsx
└── LTM/
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx
        """
        )

        # Folder path input
        st.sidebar.markdown("**Enter Company Folder Path:**")
        company_path = st.sidebar.text_input(
            "Company Folder Path",
            value=st.session_state.get('company_folder', ''),
            help="Path to folder containing FY and LTM subfolders",
            placeholder="e.g., C:\\data\\COMPANY or .\\SYMBOL",
        )

    else:  # Ticker Mode
        # Show API mode help
        st.sidebar.markdown("**API Data Sources:**")

        # Get available data sources information
        try:
            data_manager = create_enhanced_data_manager()
            sources_info = data_manager.get_available_data_sources()

            # Show available sources with their status
            available_sources = []
            source_display_names = {
                'alpha_vantage': 'Alpha Vantage',
                'fmp': 'Financial Modeling Prep',
                'polygon': 'Polygon.io',
            }

            for source_name, source_info in sources_info.get('enhanced_sources', {}).items():
                if source_info.get('enabled', False) and source_info.get('has_credentials', False):
                    display_name = source_display_names.get(
                        source_name, source_name.replace('_', ' ').title()
                    )
                    available_sources.append(display_name)

            # Always add YFinance as it's always available
            available_sources.insert(0, "Yahoo Finance")

            if available_sources:
                sources_text = ", ".join(available_sources)
                st.sidebar.info(f"🌐 Available sources: {sources_text}")

                # Add manual source selection option
                st.sidebar.markdown("**Source Selection:**")
                source_selection_mode = st.sidebar.radio(
                    "Data source mode:",
                    ["Auto (use best available)", "Manual selection"],
                    help="Auto mode tries sources in priority order. Manual lets you choose specific source.",
                )

                preferred_source = None
                if source_selection_mode == "Manual selection":
                    # Create mapping of display names to actual source types
                    source_mapping = {
                        "Yahoo Finance": "yfinance",
                        "Alpha Vantage": "alpha_vantage",
                        "Financial Modeling Prep": "fmp",
                        "Polygon": "polygon",
                    }

                    display_sources = [
                        name
                        for name in source_mapping.keys()
                        if name in available_sources or name == "Yahoo Finance"
                    ]

                    selected_display = st.sidebar.selectbox(
                        "Choose preferred source:",
                        display_sources,
                        help="Select your preferred data source",
                    )
                    preferred_source = source_mapping.get(selected_display, "yfinance")

                    # Store the preference in session state
                    st.session_state.preferred_data_source = preferred_source
                else:
                    # Clear any manual preference
                    if 'preferred_data_source' in st.session_state:
                        del st.session_state.preferred_data_source

            else:
                st.sidebar.warning("⚠️ Only Yahoo Finance available (no API keys configured)")

        except Exception as e:
            logger.warning(f"Could not get data sources info: {e}")
            st.sidebar.info(
                "🌐 Automatically fetches data from Yahoo Finance, Alpha Vantage, and other sources"
            )

        # Ticker input
        st.sidebar.markdown("**Enter Stock Ticker:**")
        ticker_symbol = (
            st.sidebar.text_input(
                "Stock Ticker",
                value=st.session_state.get('ticker_symbol', ''),
                help=f"Enter ticker symbol for {market_selection}",
                placeholder=(
                    "e.g., AAPL, MSFT, GOOGL"
                    if market_selection == "US Market"
                    else "e.g., TEVA, ICL, ELBIT (without .TA)"
                ),
            )
            .upper()
            .strip()
        )

    # Data loading section

    if st.sidebar.button("Load Company Data", type="primary"):

        if data_mode == "📁 Folder Mode (Excel Files)":
            # Traditional folder-based loading
            if company_path and Path(company_path).exists():
                st.sidebar.info(f"🔍 Validating folder: {company_path}")
                validation = st.session_state.data_processor.validate_company_folder(company_path)

                if validation['is_valid']:
                    st.sidebar.success("✅ Folder structure valid")
                    st.session_state.company_folder = company_path
                    st.session_state.ticker_symbol = ""  # Clear ticker mode data

                    # Use centralized data loader
                    with st.spinner("🔍 Analyzing company data..."):
                        success, calculator, error_msg = centralized_data_loader(
                            company_path=company_path,
                            ticker_symbol=getattr(st.session_state, 'ticker_symbol', None),
                        )

                        if success:
                            st.session_state.financial_calculator = calculator
                        else:
                            st.sidebar.error(f"❌ Data loading failed: {error_msg}")
                            st.session_state.financial_calculator = None
                            return

                        # Attach enhanced data manager for multi-source data access
                        try:
                            enhanced_data_manager = create_enhanced_data_manager()
                            st.session_state.financial_calculator.enhanced_data_manager = (
                                enhanced_data_manager
                            )
                            logger.info("Enhanced data manager attached to financial calculator")
                        except Exception as e:
                            logger.warning(f"Could not attach enhanced data manager: {e}")

                        st.session_state.dcf_valuator = DCFValuator(
                            st.session_state.financial_calculator
                        )

                        # Apply market selection to ticker processing
                        if st.session_state.financial_calculator.ticker_symbol:
                            original_ticker = st.session_state.financial_calculator.ticker_symbol
                            processed_ticker = _apply_market_selection_to_ticker(
                                original_ticker, market_selection
                            )

                            if processed_ticker != original_ticker:
                                st.session_state.financial_calculator.ticker_symbol = (
                                    processed_ticker
                                )
                                st.sidebar.info(
                                    f"🎯 Auto-detected ticker: {original_ticker} → {processed_ticker} ({market_selection})"
                                )
                            else:
                                st.sidebar.info(f"🎯 Auto-detected ticker: {processed_ticker}")

                            # Set market detection override based on user selection
                            if market_selection == "TASE (Tel Aviv)":
                                st.session_state.financial_calculator.is_tase_stock = True
                                st.session_state.financial_calculator.currency = 'ILS'
                                st.session_state.financial_calculator.financial_currency = 'ILS'
                            else:
                                st.session_state.financial_calculator.is_tase_stock = False
                                st.session_state.financial_calculator.currency = 'USD'
                                st.session_state.financial_calculator.financial_currency = 'USD'

                    # Load data with detailed progress
                    with st.spinner("📊 Calculating FCF and fetching market data..."):
                        try:
                            st.session_state.fcf_results = (
                                st.session_state.financial_calculator.calculate_all_fcf_types()
                            )

                            # Show what was loaded
                            if st.session_state.fcf_results:
                                loaded_types = [
                                    fcf_type
                                    for fcf_type, values in st.session_state.fcf_results.items()
                                    if values
                                ]
                                empty_types = [
                                    fcf_type
                                    for fcf_type, values in st.session_state.fcf_results.items()
                                    if not values
                                ]

                                if loaded_types:
                                    st.sidebar.success(
                                        f"✅ Loaded FCF types: {', '.join(loaded_types)}"
                                    )

                                    # Show market data status
                                    if st.session_state.financial_calculator.current_stock_price:
                                        st.sidebar.success(
                                            f"✅ Market data: ${st.session_state.financial_calculator.current_stock_price:.2f}"
                                        )
                                    elif st.session_state.financial_calculator.ticker_symbol:
                                        st.sidebar.warning(
                                            f"⚠️ Ticker detected ({st.session_state.financial_calculator.ticker_symbol}) but price fetch failed"
                                        )

                                # Show visual notifications for empty FCF types
                                if empty_types:
                                    company_folder = (
                                        st.session_state.company_folder.lower()
                                        if st.session_state.company_folder
                                        else ""
                                    )

                                    if 'vici' in company_folder:
                                        st.sidebar.warning(
                                            "⚠️ VICI Properties: FCF calculation not possible"
                                        )
                                        st.sidebar.info(
                                            "💡 **Reason:** Zero CapEx (typical for REITs)"
                                        )
                                        st.sidebar.info(
                                            "🔧 **Alternative:** Use Operating Cash Flow or AFFO analysis"
                                        )
                                    elif 'main' in company_folder:
                                        st.sidebar.warning(
                                            "⚠️ Main Street Capital: FCF calculation not possible"
                                        )
                                        st.sidebar.info(
                                            "💡 **Reason:** Financial company - missing standard fields"
                                        )
                                        st.sidebar.info(
                                            "🔧 **Alternative:** Use Net Investment Income analysis"
                                        )
                                    else:
                                        st.sidebar.warning(
                                            "⚠️ No FCF data calculated - check financial statements"
                                        )
                                        st.sidebar.info(
                                            f"📊 Failed calculations: {', '.join(empty_types)}"
                                        )

                                        # Show specific missing data guidance
                                        if hasattr(
                                            st.session_state.financial_calculator, 'data_validator'
                                        ):
                                            report = (
                                                st.session_state.financial_calculator.data_validator.report
                                            )
                                            critical_missing = []
                                            for error in report.errors:
                                                if 'missing critical data' in error.lower():
                                                    if 'capex' in error.lower():
                                                        critical_missing.append(
                                                            "Capital Expenditure"
                                                        )
                                                    if 'depreciation' in error.lower():
                                                        critical_missing.append(
                                                            "Depreciation & Amortization"
                                                        )

                                            if critical_missing:
                                                st.sidebar.info(
                                                    f"📋 **Missing:** {', '.join(critical_missing)}"
                                                )
                                else:
                                    st.sidebar.warning(
                                        "⚠️ No FCF data calculated - check financial statements"
                                    )
                            else:
                                st.sidebar.warning("⚠️ No FCF results returned")

                        except Exception as e:
                            st.sidebar.error(f"❌ Error loading data: {str(e)}")
                            logger.error(f"Data loading error: {e}")
                            return

                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid folder structure")
                    if validation['missing_folders']:
                        st.sidebar.write("Missing folders:", validation['missing_folders'])
                    if validation['missing_files']:
                        st.sidebar.write("Missing files:", validation['missing_files'])
                    if validation['warnings']:
                        for warning in validation['warnings']:
                            st.sidebar.warning(warning)
            else:
                st.sidebar.error("❌ Folder not found")

        else:  # Ticker Mode (API Data)
            if ticker_symbol:
                st.sidebar.info(f"🌐 Fetching data for ticker: {ticker_symbol}")

                # Use centralized data loader
                with st.spinner("🌐 Fetching market data and financial information..."):
                    success, calculator, error_msg = centralized_data_loader(
                        ticker_symbol=ticker_symbol, company_path=None
                    )

                    if success and calculator:
                        st.session_state.financial_calculator = calculator
                        st.session_state.dcf_valuator = DCFValuator(calculator)
                        st.session_state.ticker_symbol = ticker_symbol
                        st.session_state.company_folder = ""  # Clear folder mode data

                        # Show successful loading
                        st.sidebar.success(
                            f"✅ Successfully loaded data for {calculator.ticker_symbol}"
                        )
                        st.sidebar.success(
                            f"📈 Current Price: ${calculator.current_stock_price:.2f}"
                        )
                        st.sidebar.info(f"🏢 Company: {calculator.company_name}")

                        # Highlight which data source was actually used
                        data_source_used = getattr(calculator, '_data_source_used', 'API')
                        if preferred_source and data_source_used != "Auto":
                            if preferred_source in data_source_used.lower().replace(' ', '_'):
                                st.sidebar.success(
                                    f"✅ Data Source: {data_source_used} (as requested)"
                                )
                            else:
                                st.sidebar.warning(
                                    f"⚠️ Data Source: {data_source_used} (fallback - {preferred_source.replace('_', ' ').title()} failed)"
                                )
                        else:
                            st.sidebar.info(f"📊 Data Source: {data_source_used}")

                        # Calculate FCF using API financial data
                        with st.spinner("📊 Calculating FCF using API financial data..."):
                            try:
                                st.session_state.fcf_results = calculator.calculate_all_fcf_types()

                                # Show what was loaded
                                if st.session_state.fcf_results:
                                    loaded_types = [
                                        fcf_type
                                        for fcf_type, values in st.session_state.fcf_results.items()
                                        if values
                                    ]
                                    empty_types = [
                                        fcf_type
                                        for fcf_type, values in st.session_state.fcf_results.items()
                                        if not values
                                    ]

                                    if loaded_types:
                                        st.sidebar.success(
                                            f"✅ Loaded FCF types: {', '.join(loaded_types)}"
                                        )
                                        st.sidebar.success(
                                            "🎯 FCF Analysis ready! Check the analysis tabs."
                                        )
                                    else:
                                        # Check for known special cases even in API mode
                                        ticker_upper = ticker_symbol.upper()

                                        if ticker_upper == 'VICI':
                                            st.sidebar.warning(
                                                "⚠️ VICI Properties: FCF calculation challenges"
                                            )
                                            st.sidebar.info(
                                                "💡 **Note:** REIT with minimal CapEx - FCF may not be meaningful"
                                            )
                                            st.sidebar.info(
                                                "🔧 **Better metrics:** AFFO, Operating Cash Flow, or FFO"
                                            )
                                        elif ticker_upper == 'MAIN':
                                            st.sidebar.warning(
                                                "⚠️ Main Street Capital: FCF calculation challenges"
                                            )
                                            st.sidebar.info(
                                                "💡 **Note:** Business Development Company - different structure"
                                            )
                                            st.sidebar.info(
                                                "🔧 **Better metrics:** Net Investment Income or NII coverage"
                                            )
                                        else:
                                            st.sidebar.warning(
                                                "⚠️ No FCF data calculated - API data may be incomplete"
                                            )
                                            if empty_types:
                                                st.sidebar.info(
                                                    f"📊 Failed calculations: {', '.join(empty_types)}"
                                                )
                                else:
                                    st.sidebar.warning("⚠️ No FCF results returned from API data")

                            except Exception as fcf_error:
                                st.sidebar.error(f"❌ Error calculating FCF: {str(fcf_error)}")
                                logger.error(f"FCF calculation error: {fcf_error}")
                                # Set empty results as fallback
                                st.session_state.fcf_results = {}

                        st.rerun()
                    else:
                        st.sidebar.error(f"❌ Failed to load data for {ticker_symbol}")
                        if error_msg:
                            st.sidebar.error(f"Error: {error_msg}")
                        st.session_state.financial_calculator = None
                        st.session_state.fcf_results = {}
            else:
                st.sidebar.error("❌ Please enter a ticker symbol")

    # Display current company info
    if st.session_state.company_folder or st.session_state.ticker_symbol:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📈 Current Company")

        # Display company name based on current mode
        if st.session_state.company_folder:
            company_name = os.path.basename(st.session_state.company_folder)
            st.sidebar.info(f"**Company:** {company_name} (Folder Mode)")
        elif st.session_state.ticker_symbol:
            if (
                st.session_state.financial_calculator
                and st.session_state.financial_calculator.company_name
            ):
                company_name = st.session_state.financial_calculator.company_name
                st.sidebar.info(f"**Company:** {company_name} (Ticker Mode)")
            else:
                st.sidebar.info(f"**Ticker:** {st.session_state.ticker_symbol} (Ticker Mode)")

        # Display Auto-Extracted Market Data
        st.sidebar.markdown("**Market Data:**")
        if (
            st.session_state.financial_calculator
            and st.session_state.financial_calculator.ticker_symbol
        ):
            ticker = st.session_state.financial_calculator.ticker_symbol
            current_price = st.session_state.financial_calculator.current_stock_price
            shares_outstanding = getattr(
                st.session_state.financial_calculator, 'shares_outstanding', 0
            )

            st.sidebar.success(f"📈 **Ticker**: {ticker}")
            if current_price:
                # Display current price with appropriate currency
                calculator = st.session_state.financial_calculator
                is_tase_stock = getattr(calculator, 'is_tase_stock', False)
                currency = getattr(calculator, 'currency', 'USD')

                if is_tase_stock:
                    price_agorot = calculator.get_price_in_agorot()
                    price_shekels = calculator.get_price_in_shekels()
                    currency_symbol = "₪" if currency == "ILS" else currency
                    st.sidebar.info(
                        f"💰 **Current Price**: {price_agorot:.0f} ILA (≈ {price_shekels:.2f} {currency_symbol})"
                    )
                else:
                    currency_symbol = "$" if currency == "USD" else currency
                    st.sidebar.info(f"💰 **Current Price**: {currency_symbol}{current_price:.2f}")
            else:
                st.sidebar.warning("⚠️ Price fetch failed")

            # Show shares outstanding status
            if shares_outstanding and shares_outstanding > 0:
                st.sidebar.info(f"📊 **Shares Outstanding**: {shares_outstanding/1000000:.1f}M")
            else:
                st.sidebar.error("❌ **Shares Outstanding**: Not available")
                st.sidebar.warning("DCF calculation will fail without shares outstanding data")

            # Option to manually refresh market data
            if st.sidebar.button("🔄 Refresh Market Data"):
                with st.spinner("Fetching latest market data..."):
                    # Ensure market properties are set according to user selection
                    selected_market = st.session_state.get('selected_market', 'US Market')
                    if selected_market == "TASE (Tel Aviv)":
                        st.session_state.financial_calculator.is_tase_stock = True
                        st.session_state.financial_calculator.currency = 'ILS'
                        st.session_state.financial_calculator.financial_currency = 'ILS'
                    else:
                        st.session_state.financial_calculator.is_tase_stock = False
                        st.session_state.financial_calculator.currency = 'USD'
                        st.session_state.financial_calculator.financial_currency = 'USD'

                    market_data = st.session_state.financial_calculator.fetch_market_data()
                    if market_data:
                        st.sidebar.success("✅ Market data updated!")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Failed to fetch market data")
        else:
            st.sidebar.warning("⚠️ No ticker auto-detected")

            # Manual ticker input as fallback
            selected_market = st.session_state.get('selected_market', 'US Market')
            if selected_market == "US Market":
                placeholder = "e.g., AAPL, MSFT, GOOGL"
            else:
                placeholder = "e.g., TEVA, ICL, ELBIT (without .TA)"

            manual_ticker = st.sidebar.text_input(
                "Manual Ticker Entry",
                placeholder=placeholder,
                help=f"Enter ticker for {selected_market} (format will be auto-adjusted)",
            )

            if manual_ticker and st.session_state.financial_calculator:
                if st.sidebar.button("📊 Fetch Market Data"):
                    # Apply market selection to manual ticker
                    processed_ticker = _apply_market_selection_to_ticker(
                        manual_ticker.upper(), selected_market
                    )

                    with st.spinner(f"Fetching data for {processed_ticker}..."):
                        # Set market properties before fetching
                        if selected_market == "TASE (Tel Aviv)":
                            st.session_state.financial_calculator.is_tase_stock = True
                            st.session_state.financial_calculator.currency = 'ILS'
                            st.session_state.financial_calculator.financial_currency = 'ILS'
                        else:
                            st.session_state.financial_calculator.is_tase_stock = False
                            st.session_state.financial_calculator.currency = 'USD'
                            st.session_state.financial_calculator.financial_currency = 'USD'

                        market_data = st.session_state.financial_calculator.fetch_market_data(
                            processed_ticker
                        )
                        if market_data:
                            st.sidebar.success(f"✅ Fetched data for {processed_ticker}")
                            if processed_ticker != manual_ticker.upper():
                                st.sidebar.info(
                                    f"Applied {selected_market} format: {manual_ticker.upper()} → {processed_ticker}"
                                )
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ Could not fetch data for {processed_ticker}")

        # Quick stats
        if st.session_state.fcf_results:
            fcf_types = list(st.session_state.fcf_results.keys())
            st.sidebar.write(f"**FCF Types Calculated:** {len(fcf_types)}")
            for fcf_type in fcf_types:
                values = st.session_state.fcf_results[fcf_type]
                if values:
                    latest_fcf = values[-1]  # Values already in millions
                    currency_symbol = get_currency_symbol_financial(
                        st.session_state.financial_calculator
                    )
                    st.sidebar.write(f"**{fcf_type} (Latest):** {currency_symbol}{latest_fcf:.1f}M")


def render_welcome():
    """Render welcome page when no data is loaded"""
    st.title("📊 Modern FCF Analysis Tool")
    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            """
        ### Welcome to the Financial Analysis Dashboard
        
        This modern tool provides comprehensive **Free Cash Flow (FCF)** and **DCF (Discounted Cash Flow)** analysis 
        with an intuitive, responsive interface.
        
        #### 🔍 Key Features:
        - **Multiple FCF Calculations**: FCFF, FCFE, and Levered FCF
        - **Interactive DCF Valuation**: Real-time sensitivity analysis
        - **📊 Watch Lists**: Track multiple companies with automatic capture
        - **Professional Visualizations**: Interactive charts and graphs
        - **Multi-Market Support**: US Market and TASE (Tel Aviv) stocks
        - **Responsive Design**: Works on any screen size
        - **Export Capabilities**: Download results, charts, and watch list data
        
        #### 📁 Getting Started:
        1. Use the sidebar to select your company folder
        2. Ensure your folder contains `FY/` and `LTM/` subfolders
        3. Each subfolder should have Income Statement, Balance Sheet, and Cash Flow Statement files
        """
        )

    with col2:
        st.markdown(
            """
        ### 📋 Required Folder Structure
        ```
        <COMPANY>/
        ├── FY/
        │   ├── Income Statement.xlsx
        │   ├── Balance Sheet.xlsx
        │   └── Cash Flow Statement.xlsx
        └── LTM/
            ├── Income Statement.xlsx
            ├── Balance Sheet.xlsx
            └── Cash Flow Statement.xlsx
        ```
        """
        )

    # Watch Lists feature highlight
    st.markdown("---")
    st.subheader("🆕 NEW: Watch Lists Feature")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        #### 📋 **Portfolio Tracking**
        - Create multiple watch lists
        - Organize by strategy or sector
        - Automatic analysis capture
        """
        )

    with col2:
        st.markdown(
            """
        #### 📊 **Performance Analysis**
        - Visual upside/downside charts
        - Investment category breakdowns
        - Historical trend analysis
        """
        )

    with col3:
        st.markdown(
            """
        #### 📥 **Export Options**
        - Current view CSV export
        - Complete historical data
        - Individual stock timelines
        """
        )

    st.info(
        "💡 **Get Started**: Create your first watch list in the **📊 Watch Lists** tab after loading company data!"
    )

    # Example company demonstration
    st.markdown("---")
    st.subheader("🎯 Demo Mode")
    st.info("To see the tool in action, please load a company folder using the sidebar.")


def is_tase_stock(financial_calculator):
    """
    Check if the stock is a TASE (Tel Aviv Stock Exchange) stock

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        bool: True if TASE stock, False otherwise
    """
    # Check explicit TASE flag first
    if hasattr(financial_calculator, 'is_tase_stock') and financial_calculator.is_tase_stock:
        return True

    # Check for TASE detection indicators
    ticker = getattr(financial_calculator, 'ticker_symbol', '')
    currency = getattr(financial_calculator, 'currency', '')

    # Auto-detect TASE stocks
    if ticker and ticker.endswith('.TA'):
        return True
    if currency in ['ILS', 'ILA']:
        return True

    return False


def get_currency_symbol_per_share(financial_calculator):
    """
    Get currency symbol for per-share values (stock prices, fair values)

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        str: Currency symbol with unit - ₪ (ILA) for TASE stocks, $ for others
    """
    if is_tase_stock(financial_calculator):
        return "₪ (ILA)"  # Agorot for TASE per-share values
    else:
        return "$"  # Dollar for other stocks


def get_currency_symbol_financial(financial_calculator):
    """
    Get currency symbol for financial values (FCF, enterprise values in millions)

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        str: Currency symbol - ₪ for TASE stocks, $ for others
    """
    if is_tase_stock(financial_calculator):
        return "₪"  # Millions of Shekels for TASE financial values
    else:
        return "$"  # Dollar for other stocks


def get_currency_symbol(financial_calculator):
    """
    Get the basic currency symbol (for backward compatibility)

    Args:
        financial_calculator: FinancialCalculator instance

    Returns:
        str: Currency symbol (₪ for TASE stocks, $ for others)
    """
    return get_currency_symbol_financial(financial_calculator)


def render_fcf_analysis():
    """Render FCF Analysis tab"""
    st.header("📈 Free Cash Flow Analysis")

    if not st.session_state.fcf_results:
        st.warning("⚠️ Please load company data first using the sidebar.")
        return

    # Show centralized data source information
    render_centralized_data_source_info()
    st.markdown("---")

    # Display Company Information below header
    folder_name = (
        os.path.basename(st.session_state.company_folder)
        if st.session_state.company_folder
        else get_unknown_company_name()
    )
    ticker = (
        st.session_state.financial_calculator.ticker_symbol
        if st.session_state.financial_calculator
        else None
    )
    current_price = (
        st.session_state.financial_calculator.current_stock_price
        if st.session_state.financial_calculator
        else None
    )

    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = (
        getattr(st.session_state.financial_calculator, 'company_name', None)
        or ticker
        or folder_name
    )

    # Company info row (including data source)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.subheader(f"🏢 {company_name}")

    with col2:
        if ticker:
            st.metric("📊 Ticker Symbol", ticker)
        else:
            st.metric("📊 Ticker Symbol", "N/A")

    with col3:
        if current_price:
            currency_symbol = get_currency_symbol_per_share(st.session_state.financial_calculator)
            st.metric("💰 Market Price", f"{current_price:.2f} {currency_symbol}")
        else:
            st.metric("💰 Market Price", "N/A")

    with col4:
        # Show data source used for this analysis
        data_source = getattr(
            st.session_state.financial_calculator, '_data_source_used', 'Excel/Manual'
        )
        if data_source == 'Excel/Manual' or not hasattr(
            st.session_state.financial_calculator, '_has_api_financial_data'
        ):
            st.metric("📊 Data Source", "Excel Files")
        else:
            st.metric("🌐 API Source", data_source)

    st.markdown("---")

    # FCF Type Definitions
    st.subheader("📚 FCF Definitions")
    st.markdown(
        """
    - **Free Cash Flow to Firm (FCFF)** = EBIT(1-Tax Rate) + Depreciation & Amortization - Working Capital Change - Capital Expenditures
    - **Free Cash Flow to Equity (FCFE)** = Net Income + Depreciation & Amortization - Working Capital Change - Capital Expenditures + Net Borrowing
    - **Levered Free Cash Flow (LFCF)** = Operating Cash Flow - Capital Expenditures
    """
    )

    # FCF Summary Metrics
    st.subheader("📊 FCF Summary")
    col1, col2, col3, col4, col5 = st.columns(5)

    fcf_results = st.session_state.fcf_results

    # Calculate latest values for each FCF type
    latest_values = {}
    for fcf_type in ['FCFF', 'FCFE', 'LFCF']:
        if fcf_type in fcf_results and fcf_results[fcf_type]:
            latest_values[fcf_type] = fcf_results[fcf_type][-1]
        else:
            latest_values[fcf_type] = None

    # Calculate average of the 3 FCF types (latest values)
    available_latest = [v for v in latest_values.values() if v is not None]
    avg_latest_fcf = np.mean(available_latest) if available_latest else None

    # Get appropriate currency symbol for financial values
    currency_symbol = get_currency_symbol_financial(st.session_state.financial_calculator)

    with col1:
        if latest_values['FCFF'] is not None:
            st.metric("FCFF (Latest)", f"{currency_symbol}{latest_values['FCFF']:.1f}M")
        else:
            st.metric("FCFF (Latest)", "N/A")

    with col2:
        if latest_values['FCFE'] is not None:
            st.metric("FCFE (Latest)", f"{currency_symbol}{latest_values['FCFE']:.1f}M")
        else:
            st.metric("FCFE (Latest)", "N/A")

    with col3:
        if latest_values['LFCF'] is not None:
            st.metric("LFCF (Latest)", f"{currency_symbol}{latest_values['LFCF']:.1f}M")
        else:
            st.metric("LFCF (Latest)", "N/A")

    with col4:
        # Average of the 3 FCF types (latest values)
        if avg_latest_fcf is not None:
            st.metric("Average FCF (Latest)", f"{currency_symbol}{avg_latest_fcf:.1f}M")
        else:
            st.metric("Average FCF (Latest)", "N/A")

    with col5:
        # Show the range (max - min) of latest FCF values
        if len(available_latest) > 1:
            fcf_range = max(available_latest) - min(available_latest)
            st.metric("FCF Range", f"{currency_symbol}{fcf_range:.1f}M")
        else:
            st.metric("FCF Range", "N/A")

    # FCF Comparison Chart
    st.subheader("📊 FCF Trend Analysis")
    st.info(
        "💡 This chart shows all FCF calculation methods plus their average (bright orange dashed line with diamond markers)"
    )

    company_name = (
        os.path.basename(st.session_state.company_folder)
        if st.session_state.company_folder
        else get_default_company_name()
    )

    # Force refresh for plots to ensure they use latest data
    st.session_state.data_processor._cached_fcf_data = None

    fcf_chart = st.session_state.data_processor.create_fcf_comparison_plot(
        fcf_results, company_name
    )
    st.plotly_chart(fcf_chart, use_container_width=True)

    # Dedicated Average FCF Plot
    st.subheader("📊 Average FCF Trend")
    st.info("💡 This chart focuses specifically on the average FCF across all calculation methods")

    avg_fcf_chart = st.session_state.data_processor.create_average_fcf_plot(
        fcf_results, company_name
    )
    st.plotly_chart(avg_fcf_chart, use_container_width=True)

    # Growth Analysis
    st.subheader("📈 Growth Rate Analysis")
    slope_chart = st.session_state.data_processor.create_slope_analysis_plot(
        fcf_results, company_name
    )
    st.plotly_chart(slope_chart, use_container_width=True)

    # FCF Data Table
    st.subheader("📋 FCF Data Table")
    st.info(
        "💡 The table includes an Average FCF column that shows the mean of all FCF calculation methods for each year"
    )

    # Use centralized data preparation for FCF table (force refresh for new data)
    fcf_data = st.session_state.data_processor.prepare_fcf_data(fcf_results, force_refresh=True)
    if fcf_data:
        # Build table data using pre-calculated values
        fcf_df_data = {'Year': fcf_data['years']}

        # Add individual FCF type columns using padded data
        currency_symbol = get_currency_symbol(st.session_state.financial_calculator)
        for fcf_type, values in fcf_data['padded_fcf_data'].items():
            fcf_df_data[f'{fcf_type} ({currency_symbol}M)'] = values

        # Add Average FCF column using pre-calculated averages
        fcf_df_data[f'Average FCF ({currency_symbol}M)'] = fcf_data['average_fcf']

        fcf_df = pd.DataFrame(fcf_df_data)

        # Format the dataframe for better display
        def format_fcf_value(val):
            """Format FCF values for display"""
            if pd.isna(val) or val is None:
                return "N/A"
            return f"${val:.1f}M"

        # Apply vectorized formatting to FCF columns
        formatted_df = fcf_df.copy()
        for col in formatted_df.columns:
            if col != 'Year':
                # Vectorized formatting instead of apply()
                formatted_df[col] = pd.Series(
                    np.where(
                        pd.isna(formatted_df[col]), "N/A", formatted_df[col].map("${:.1f}M".format)
                    )
                )

        # Display the table
        st.dataframe(
            formatted_df,
            use_container_width=False,
            width=1000,
            column_config={
                f"Average FCF ({currency_symbol}M)": st.column_config.TextColumn(
                    f"Average FCF ({currency_symbol}M)",
                    help="Average of all FCF calculation methods for each year",
                    default="N/A",
                )
            },
        )

        # Download and save buttons for FCF data
        csv = fcf_df.to_csv(index=False)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="📥 Download FCF Data (CSV)",
                data=csv,
                file_name=f"{company_name}_FCF_Analysis.csv",
                mime="text/csv",
                help="Downloads raw numerical data including Average FCF column",
            )

        with col2:
            if st.button(
                "💾 Save to Directory", help="Save FCF data to configured export directory"
            ):
                # Get ticker if available
                ticker = None
                try:
                    ticker = st.session_state.financial_calculator.ticker_symbol
                except:
                    pass

                saved_path = save_fcf_analysis_to_file(fcf_df, company_name, ticker)
                if saved_path:
                    st.success(f"✅ FCF data saved to: {saved_path}")
                else:
                    st.error("❌ Failed to save FCF data")

        # FCF Growth Rates Table
        st.subheader("📈 FCF Growth Rate Analysis")

        # Calculate growth rates using consolidated function
        growth_rates = calculate_fcf_growth_rates(fcf_results, periods=list(range(1, 10)))

        # Format for display
        growth_data = {'FCF Type': ['LFCF', 'FCFE', 'FCFF', 'Average']}

        for period in range(1, 10):  # 1yr to 9yr
            period_key = f'{period}yr'
            formatted_rates = []

            for fcf_type in ['LFCF', 'FCFE', 'FCFF', 'Average']:
                if fcf_type in growth_rates and period_key in growth_rates[fcf_type]:
                    rate = growth_rates[fcf_type][period_key]
                    if rate is not None:
                        formatted_rates.append(f"{rate:.1%}")
                    else:
                        formatted_rates.append("N/A")
                else:
                    formatted_rates.append("N/A")

            growth_data[f'{period}yr'] = formatted_rates

        growth_df = pd.DataFrame(growth_data)

        # Define color coding function for growth rates
        def color_growth_rates(val):
            """Color code growth rates based on performance"""
            if val == "N/A":
                return 'background-color: #f0f0f0'  # Light gray for N/A
            try:
                # Extract percentage value
                rate = float(val.strip('%')) / 100
                if rate >= 0.15:  # >= 15%
                    return 'background-color: #d4edda; color: #155724'  # Dark green
                elif rate >= 0.05:  # 5% to 15%
                    return 'background-color: #d1ecf1; color: #0c5460'  # Light blue
                elif rate >= 0:  # 0% to 5%
                    return 'background-color: #fff3cd; color: #856404'  # Light yellow
                elif rate >= -0.05:  # 0% to -5%
                    return 'background-color: #f8d7da; color: #721c24'  # Light red
                else:  # < -5%
                    return 'background-color: #f5c6cb; color: #721c24'  # Dark red
            except:
                return 'background-color: #f0f0f0'  # Light gray for parsing errors

        # Apply styling to all columns except the first (FCF Type)
        styled_df = growth_df.style.map(
            color_growth_rates, subset=[col for col in growth_df.columns if col != 'FCF Type']
        )

        st.dataframe(styled_df, use_container_width=False, width=900, hide_index=True)

    else:
        st.info(
            "📋 No FCF data available to display. Please ensure your financial statements contain the required metrics."
        )


def render_dcf_analysis():
    """Render DCF Analysis tab"""
    st.header("💰 DCF Valuation Analysis")

    # FCF type descriptions (used in multiple places)
    fcf_type_descriptions = {
        'FCFE': 'Free Cash Flow to Equity - Net Income + D&A - Working Capital Change - CapEx + Net Borrowing (Recommended for equity valuation)',
        'FCFF': 'Free Cash Flow to Firm - EBIT(1-Tax) + D&A - Working Capital Change - CapEx (Requires debt adjustment)',
        'LFCF': 'Levered Free Cash Flow - Operating Cash Flow - CapEx (Simplified approach)',
    }

    if not st.session_state.financial_calculator:
        st.warning("⚠️ Please load company data first using the sidebar.")
        return

    # Show centralized data source information
    render_centralized_data_source_info()
    st.markdown("---")

    # Display Company Information below header
    folder_name = (
        os.path.basename(st.session_state.company_folder)
        if st.session_state.company_folder
        else get_unknown_company_name()
    )
    ticker = st.session_state.financial_calculator.ticker_symbol
    current_price = st.session_state.financial_calculator.current_stock_price

    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = (
        getattr(st.session_state.financial_calculator, 'company_name', None)
        or ticker
        or folder_name
    )

    # Company info row
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader(f"🏢 {company_name}")

    with col2:
        if ticker:
            st.metric("📊 Ticker Symbol", ticker)
        else:
            st.metric("📊 Ticker Symbol", "N/A")

    with col3:
        if current_price:
            currency_symbol = get_currency_symbol_per_share(st.session_state.financial_calculator)
            st.metric("💰 Market Price", f"{current_price:.2f} {currency_symbol}")
        else:
            st.metric("💰 Market Price", "N/A")

    st.markdown("---")

    # Get FCF results for dropdown selection
    fcf_results = st.session_state.financial_calculator.fcf_results

    # FCF Growth Rate Analysis Table
    if fcf_results and any(fcf_results.values()):
        st.subheader("📈 FCF Growth Rate Analysis")

        # Calculate growth rates using consolidated function
        growth_rates = calculate_fcf_growth_rates(fcf_results, periods=list(range(1, 10)))

        # Format for display
        growth_data = {'FCF Type': ['LFCF', 'FCFE', 'FCFF', 'Average']}

        for period in range(1, 10):  # 1yr to 9yr
            period_key = f'{period}yr'
            formatted_rates = []

            for fcf_type in ['LFCF', 'FCFE', 'FCFF', 'Average']:
                if fcf_type in growth_rates and period_key in growth_rates[fcf_type]:
                    rate = growth_rates[fcf_type][period_key]
                    if rate is not None:
                        formatted_rates.append(f"{rate:.1%}")
                    else:
                        formatted_rates.append("N/A")
                else:
                    formatted_rates.append("N/A")

            growth_data[f'{period}yr'] = formatted_rates

        growth_df = pd.DataFrame(growth_data)

        # Define color coding function for growth rates
        def color_growth_rates(val):
            """Color code growth rates based on performance"""
            if val == "N/A":
                return 'background-color: #f0f0f0'  # Light gray for N/A
            try:
                # Extract percentage value
                rate = float(val.strip('%')) / 100
                if rate >= 0.15:  # >= 15%
                    return 'background-color: #d4edda; color: #155724'  # Dark green
                elif rate >= 0.05:  # 5% to 15%
                    return 'background-color: #d1ecf1; color: #0c5460'  # Light blue
                elif rate >= 0:  # 0% to 5%
                    return 'background-color: #fff3cd; color: #856404'  # Light yellow
                elif rate >= -0.05:  # 0% to -5%
                    return 'background-color: #f8d7da; color: #721c24'  # Light red
                else:  # < -5%
                    return 'background-color: #f5c6cb; color: #721c24'  # Dark red
            except:
                return 'background-color: #f0f0f0'  # Light gray for parsing errors

        # Apply styling to all columns except the first (FCF Type)
        styled_df = growth_df.style.map(
            color_growth_rates, subset=[col for col in growth_df.columns if col != 'FCF Type']
        )

        st.dataframe(styled_df, use_container_width=False, width=900, hide_index=True)
        st.markdown("---")

    # DCF Assumptions Panel
    st.subheader("⚙️ DCF Assumptions")

    # FCF Type Selection
    st.markdown("**FCF Selection**")
    fcf_type_options = []

    # Only show available FCF types (prioritize FCFE first)
    for fcf_type in ['FCFE', 'FCFF', 'LFCF']:
        if fcf_type in fcf_results and fcf_results[fcf_type]:
            fcf_type_options.append(fcf_type)

    if not fcf_type_options:
        st.error("❌ No FCF data available for DCF calculation")
        return

    # Default to first available type (FCFE prioritized in ordering)
    default_fcf_idx = 0

    selected_fcf_type = st.selectbox(
        "FCF Type for DCF Calculation",
        options=fcf_type_options,
        index=default_fcf_idx,
        format_func=lambda x: f"{x} - {fcf_type_descriptions[x]}",
        help="Select which Free Cash Flow calculation to use for DCF valuation",
    )

    # Update default growth rates based on selected FCF type
    selected_fcf_values = fcf_results[selected_fcf_type]
    default_growth_1_5 = 5.0  # 5% fallback
    default_growth_6_10 = 2.5  # 2.5% fallback

    if selected_fcf_values and len(selected_fcf_values) >= 6:
        # Calculate 5-year growth rate for selected FCF type
        start_value = selected_fcf_values[-6]
        end_value = selected_fcf_values[-1]

        if start_value != 0 and start_value is not None and end_value is not None:
            growth_rate = (abs(end_value) / abs(start_value)) ** (1 / 5) - 1

            # Handle negative cash flows
            if end_value < 0 and start_value > 0:
                growth_rate = -growth_rate
            elif end_value > 0 and start_value < 0:
                growth_rate = abs(growth_rate)

            # Cap extreme values
            if -0.5 <= growth_rate <= 1.0:
                default_growth_1_5 = growth_rate * 100
                default_growth_6_10 = (growth_rate / 2) * 100  # Half of 5yr average

    # Display selected FCF type summary
    if selected_fcf_values:
        latest_fcf = selected_fcf_values[-1]
        currency_symbol = get_currency_symbol_financial(st.session_state.financial_calculator)
        st.info(f"💡 Using {selected_fcf_type}: Latest FCF = {currency_symbol}{latest_fcf:.1f}M")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Growth Assumptions**")
        growth_yr1_5 = st.number_input(
            "Growth Rate (Years 1-5) (%)",
            min_value=-50.0,
            max_value=100.0,
            value=default_growth_1_5,
            step=1.0,
            format="%.1f",
            help="Annual growth rate for years 1-5 (based on 5yr historical average)",
        )

        growth_yr5_10 = st.number_input(
            "Growth Rate (Years 6-10) (%)",
            min_value=-50.0,
            max_value=50.0,
            value=default_growth_6_10,
            step=0.5,
            format="%.1f",
            help="Annual growth rate for years 6-10 (conservative estimate)",
        )

        terminal_growth = st.number_input(
            "Terminal Growth Rate (%)",
            min_value=0.0,
            max_value=10.0,
            value=3.0,
            step=0.1,
            format="%.1f",
            help="Long-term growth rate (typically 2-3%)",
        )

    with col2:
        st.markdown("**Valuation Assumptions**")
        discount_rate = st.number_input(
            "Discount Rate (WACC) (%)",
            min_value=5.0,
            max_value=30.0,
            value=10.0,
            step=0.5,
            format="%.1f",
            help="Weighted Average Cost of Capital",
        )

        projection_years = st.selectbox(
            "Projection Period (Years)",
            options=[5, 7, 10],
            index=0,
            help="Number of years to project FCF",
        )

    # Update DCF assumptions with selected FCF type
    dcf_assumptions = {
        'discount_rate': discount_rate / 100,
        'terminal_growth_rate': terminal_growth / 100,
        'growth_rate_yr1_5': growth_yr1_5 / 100,
        'growth_rate_yr5_10': growth_yr5_10 / 100,
        'projection_years': projection_years,
        'fcf_type': selected_fcf_type,
    }

    # Check if shares outstanding is available before allowing DCF calculation
    shares_outstanding = getattr(st.session_state.financial_calculator, 'shares_outstanding', 0)
    can_calculate_dcf = shares_outstanding and shares_outstanding > 0

    if not can_calculate_dcf:
        st.error(
            "❌ **Cannot Calculate DCF**: Shares outstanding data is required but not available."
        )
        st.info(
            "💡 Please ensure the ticker symbol is correct and try refreshing market data in the sidebar."
        )

    # Calculate DCF
    dcf_button_disabled = not can_calculate_dcf
    if st.button("🔄 Calculate DCF Valuation", type="primary", disabled=dcf_button_disabled):
        with st.spinner("Calculating DCF valuation..."):
            # Store user DCF assumptions in session state for report generation
            st.session_state.user_dcf_assumptions = dcf_assumptions.copy()

            dcf_results = st.session_state.dcf_valuator.calculate_dcf_projections(dcf_assumptions)

            # Check for errors in DCF calculation
            if 'error' in dcf_results:
                st.error(f"❌ DCF Calculation Failed: {dcf_results['error_message']}")

                # Show helpful debug information
                if dcf_results['error'] == 'shares_outstanding_unavailable':
                    st.warning("💡 **Possible Solutions:**")
                    st.markdown(
                        """
                    - Verify the ticker symbol is correct
                    - Check if the company is publicly traded
                    - Try refreshing market data using the sidebar button
                    - Ensure internet connection for market data fetch
                    """
                    )

                    # Show market data status
                    market_data = dcf_results.get('market_data', {})
                    st.info(f"**Market Data Status:**")
                    st.write(f"- Ticker: {market_data.get('ticker_symbol', 'Not detected')}")
                    per_share_currency = get_currency_symbol_per_share(
                        st.session_state.financial_calculator
                    )
                    financial_currency = get_currency_symbol_financial(
                        st.session_state.financial_calculator
                    )
                    st.write(
                        f"- Current Price: {market_data.get('current_price', 0):.2f} {per_share_currency}"
                    )
                    st.write(
                        f"- Market Cap: {financial_currency}{market_data.get('market_cap', 0)/1000000:.1f}M"
                    )
                    st.write(f"- Shares Outstanding: {market_data.get('shares_outstanding', 0):,}")

                return
            else:
                st.session_state.dcf_results = dcf_results
                st.success("✅ DCF calculation completed!")
                st.rerun()

    # Display DCF Results
    if st.session_state.dcf_results:
        dcf_results = st.session_state.dcf_results

        # Key Valuation Metrics
        st.subheader("🎯 Valuation Results")

        # Display which FCF type was used
        used_fcf_type = dcf_results.get('fcf_type', 'FCFF')
        st.info(
            f"💼 DCF calculated using **{used_fcf_type}** - {fcf_type_descriptions.get(used_fcf_type, 'Free Cash Flow')}"
        )

        # Get market data (use same source as DCF header for consistency)
        current_price = st.session_state.financial_calculator.current_stock_price or 0
        ticker = st.session_state.financial_calculator.ticker_symbol
        fair_value = dcf_results.get('value_per_share', 0)

        # Debug: Show DCF calculation values
        financial_currency = get_currency_symbol_financial(st.session_state.financial_calculator)
        per_share_currency = get_currency_symbol_per_share(st.session_state.financial_calculator)
        st.expander("🔍 Debug: DCF Calculation Details").write(
            {
                'Enterprise Value': f"{financial_currency}{dcf_results.get('enterprise_value', 0)/1000000:.1f}M",
                'Equity Value': f"{financial_currency}{dcf_results.get('equity_value', 0)/1000000:.1f}M",
                'Shares Outstanding': f"{dcf_results.get('market_data', {}).get('shares_outstanding', 0)/1000000:.1f}M",
                'Fair Value per Share': f"{fair_value:.2f} {per_share_currency}",
                'FCF Type Used': dcf_results.get('fcf_type', get_unknown_fcf_type()),
            }
        )

        # Calculate upside/downside
        upside_downside = 0
        recommendation = "N/A"
        recommendation_color = "gray"

        if current_price > 0 and fair_value > 0:
            upside_downside = (fair_value - current_price) / current_price

            if upside_downside > 0.20:  # >20% upside
                recommendation = "🟢 BUY"
                recommendation_color = "green"
            elif upside_downside < -0.20:  # >20% overvalued
                recommendation = "🔴 SELL"
                recommendation_color = "red"
            else:  # Within ±20%
                recommendation = "🟡 HOLD"
                recommendation_color = "orange"

        # Show different metrics based on FCF type
        if used_fcf_type == 'FCFE':
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                equity_value = dcf_results.get('equity_value', 0)  # Already in millions
                currency_symbol = get_currency_symbol(st.session_state.financial_calculator)
                st.metric("Equity Value (FCFE)", f"{currency_symbol}{equity_value:.0f}M")

            with col2:
                if current_price > 0:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"

                    # Display current price with appropriate currency
                    calculator = st.session_state.financial_calculator
                    is_tase_stock = getattr(calculator, 'is_tase_stock', False)
                    currency = getattr(calculator, 'currency', 'USD')

                    if is_tase_stock:
                        price_agorot = calculator.get_price_in_agorot()
                        price_shekels = calculator.get_price_in_shekels()
                        currency_symbol = "₪" if currency == "ILS" else currency
                        st.metric(
                            label,
                            f"{price_agorot:.0f} ILA",
                            help=f"≈ {price_shekels:.2f} {currency_symbol}",
                        )
                    else:
                        currency_symbol = "$" if currency == "USD" else currency
                        st.metric(label, f"{currency_symbol}{current_price:.2f}")
                else:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, "N/A", help="Market price unavailable")

            with col3:
                # Display fair value with appropriate currency
                is_tase_stock = dcf_results.get('is_tase_stock', False)
                currency = dcf_results.get('currency', 'USD')

                if is_tase_stock:
                    fair_value_agorot = dcf_results.get('value_per_share_agorot', fair_value)
                    fair_value_shekels = dcf_results.get(
                        'value_per_share_shekels', fair_value / 100.0
                    )
                    currency_symbol = "₪" if currency == "ILS" else currency
                    st.metric(
                        "Fair Value (DCF)",
                        f"{fair_value_agorot:.0f} ILA",
                        help=f"≈ {fair_value_shekels:.2f} {currency_symbol}",
                    )
                else:
                    currency_symbol = "$" if currency == "USD" else currency
                    st.metric("Fair Value (DCF)", f"{currency_symbol}{fair_value:.2f}")

            with col4:
                if current_price > 0 and fair_value > 0:
                    upside_text = f"{upside_downside:+.1%}"
                    st.metric("Upside/Downside", upside_text, delta=recommendation)
                else:
                    st.metric(
                        "Upside/Downside",
                        "N/A",
                        help="Requires both current price and DCF calculation",
                    )
        else:
            col1, col2, col3, col4, col5 = st.columns(5)

            # Get currency symbol once for this section
            currency_symbol = get_currency_symbol(st.session_state.financial_calculator)

            with col1:
                enterprise_value = dcf_results.get('enterprise_value', 0)  # Already in millions
                st.metric("Enterprise Value", f"{currency_symbol}{enterprise_value:.0f}M")

            with col2:
                net_debt = dcf_results.get('net_debt', 0)  # Already in millions
                st.metric("Net Debt", f"{currency_symbol}{net_debt:.0f}M")

            with col3:
                equity_value = dcf_results.get('equity_value', 0)  # Already in millions
                st.metric("Equity Value", f"{currency_symbol}{equity_value:.0f}M")

            with col4:
                if current_price > 0:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"

                    # Display current price with appropriate currency
                    calculator = st.session_state.financial_calculator
                    is_tase_stock = getattr(calculator, 'is_tase_stock', False)
                    currency = getattr(calculator, 'currency', 'USD')

                    if is_tase_stock:
                        price_agorot = calculator.get_price_in_agorot()
                        price_shekels = calculator.get_price_in_shekels()
                        currency_symbol = "₪" if currency == "ILS" else currency
                        st.metric(
                            label,
                            f"{price_agorot:.0f} ILA",
                            help=f"≈ {price_shekels:.2f} {currency_symbol}",
                        )
                    else:
                        currency_symbol = "$" if currency == "USD" else currency
                        st.metric(label, f"{currency_symbol}{current_price:.2f}")
                else:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, "N/A", help="Market price unavailable")

            with col5:
                # Display fair value with appropriate currency
                is_tase_stock = dcf_results.get('is_tase_stock', False)
                currency = dcf_results.get('currency', 'USD')

                if is_tase_stock:
                    fair_value_agorot = dcf_results.get('value_per_share_agorot', fair_value)
                    fair_value_shekels = dcf_results.get(
                        'value_per_share_shekels', fair_value / 100.0
                    )
                    currency_symbol = "₪" if currency == "ILS" else currency
                    st.metric(
                        "Fair Value (DCF)",
                        f"{fair_value_agorot:.0f} ILA",
                        help=f"≈ {fair_value_shekels:.2f} {currency_symbol}",
                    )
                else:
                    currency_symbol = "$" if currency == "USD" else currency
                    st.metric("Fair Value (DCF)", f"{currency_symbol}{fair_value:.2f}")

        # Second row for upside/downside when using FCFF/LFCF
        if used_fcf_type != 'FCFE':
            st.markdown("---")
            col_upside = st.columns([2, 1, 2])[1]  # Center the upside/downside metric
            with col_upside:
                if current_price > 0 and fair_value > 0:
                    upside_text = f"{upside_downside:+.1%}"
                    st.metric("Upside/Downside", upside_text, delta=recommendation)
                else:
                    st.metric(
                        "Upside/Downside",
                        "N/A",
                        help="Requires both current price and DCF calculation",
                    )

        # Investment Recommendation
        if recommendation != "N/A":
            st.markdown("---")
            st.subheader("📋 Investment Recommendation")

            rec_col1, rec_col2 = st.columns([1, 3])
            with rec_col1:
                st.markdown(f"**{recommendation}**")

            with rec_col2:
                if upside_downside > 0.20:
                    st.success(
                        f"Stock appears undervalued by {upside_downside:.1%}. Consider buying."
                    )
                elif upside_downside < -0.20:
                    st.error(
                        f"Stock appears overvalued by {abs(upside_downside):.1%}. Consider selling."
                    )
                else:
                    st.warning(f"Stock is fairly valued (within ±20%). Hold position.")

        # Terminal Value Display
        st.markdown("---")
        terminal_value = dcf_results.get('terminal_value', 0)  # Already in millions
        currency_symbol = get_currency_symbol_financial(st.session_state.financial_calculator)
        st.metric("Terminal Value", f"{currency_symbol}{terminal_value:.0f}M")

        # DCF Waterfall Chart
        st.subheader("📊 DCF Valuation Breakdown")
        waterfall_chart = st.session_state.data_processor.create_dcf_waterfall_chart(dcf_results)
        st.plotly_chart(waterfall_chart, use_container_width=True)

        # Sensitivity Analysis
        sensitivity_title = f"🎛️ Sensitivity Analysis"
        if ticker and current_price:
            sensitivity_title += f" - {ticker} (${current_price:.2f})"
        elif ticker:
            sensitivity_title += f" - {ticker}"

        st.subheader(sensitivity_title)

        with st.expander("Configure Sensitivity Analysis"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Discount Rate Range (%)**")
                dr_min_pct = st.number_input(
                    "Min Discount Rate (%)", value=8.0, step=0.5, format="%.1f"
                )
                dr_max_pct = st.number_input(
                    "Max Discount Rate (%)", value=15.0, step=0.5, format="%.1f"
                )

            with col2:
                st.markdown("**Growth Rate Range (%)**")
                gr_min_pct = st.number_input(
                    "Min Growth Rate (%)", value=0.0, step=0.5, format="%.1f"
                )
                gr_max_pct = st.number_input(
                    "Max Growth Rate (%)", value=5.0, step=0.5, format="%.1f"
                )

        if st.button("Generate Sensitivity Analysis"):
            with st.spinner("Generating sensitivity analysis..."):
                # Convert percentage inputs to decimal format for calculations
                dr_min = dr_min_pct / 100
                dr_max = dr_max_pct / 100
                gr_min = gr_min_pct / 100
                gr_max = gr_max_pct / 100

                # Store user sensitivity parameters in session state for report generation
                st.session_state.user_sensitivity_params = {
                    'discount_rate_min': dr_min,
                    'discount_rate_max': dr_max,
                    'growth_rate_min': gr_min,
                    'growth_rate_max': gr_max,
                    'discount_rate_min_pct': dr_min_pct,
                    'discount_rate_max_pct': dr_max_pct,
                    'growth_rate_min_pct': gr_min_pct,
                    'growth_rate_max_pct': gr_max_pct,
                }

                discount_rates = np.linspace(dr_min, dr_max, 5)
                growth_rates = np.linspace(gr_min, gr_max, 5)

                sensitivity_results = st.session_state.dcf_valuator.sensitivity_analysis(
                    discount_rates, growth_rates, dcf_assumptions
                )

                sensitivity_chart = st.session_state.data_processor.create_sensitivity_heatmap(
                    sensitivity_results
                )
                st.plotly_chart(sensitivity_chart, use_container_width=True)

        # DCF Data Table
        projections_title = "📋 DCF Projections Table"
        if ticker:
            projections_title += f" - {ticker}"

        st.subheader(projections_title)

        if 'projections' in dcf_results:
            projections = dcf_results['projections']
            years = dcf_results.get('years', [])

            currency_symbol = get_currency_symbol(st.session_state.financial_calculator)
            dcf_table_data = {
                'Year': years,
                f'Projected FCF ({currency_symbol}M)': projections.get(
                    'projected_fcf', []
                ),  # Already in millions
                'Growth Rate': [f"{rate:.1%}" for rate in projections.get('growth_rates', [])],
                f'Present Value ({currency_symbol}M)': dcf_results.get(
                    'pv_fcf', []
                ),  # Already in millions
            }

            dcf_df = pd.DataFrame(dcf_table_data)
            st.dataframe(dcf_df, use_container_width=False, width=700)

            # Enhanced CSV export with comprehensive metadata
            csv_data = create_enhanced_dcf_csv_export(
                dcf_df, dcf_results, dcf_assumptions, ticker, current_price
            )

            # Create filename with ticker if available
            if ticker:
                file_name = f"{ticker}_DCF_Analysis_Enhanced.csv"
                download_label = f"📥 Download {ticker} Enhanced DCF Data (CSV)"
            else:
                company_name = (
                    os.path.basename(st.session_state.company_folder)
                    if st.session_state.company_folder
                    else get_default_company_name()
                )
                file_name = f"{company_name}_DCF_Analysis_Enhanced.csv"
                download_label = "📥 Download Enhanced DCF Data (CSV)"

            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label=download_label,
                    data=csv_data,
                    file_name=file_name,
                    mime="text/csv",
                    help="Download comprehensive DCF analysis with metadata for database import",
                )

            with col2:
                save_label = (
                    f"💾 Save {ticker} to Directory" if ticker else "💾 Save DCF to Directory"
                )
                if st.button(
                    save_label, help="Save enhanced DCF data to configured export directory"
                ):
                    saved_path = save_enhanced_dcf_to_file(
                        dcf_df, dcf_results, dcf_assumptions, ticker, current_price
                    )
                    if saved_path:
                        st.success(f"✅ Enhanced DCF data saved to: {saved_path}")
                    else:
                        st.error("❌ Failed to save enhanced DCF data")


def get_financial_scale_and_unit(value, already_in_millions=True):
    """
    Determine appropriate scale and unit for financial values based on magnitude

    Args:
        value (float): Financial value to scale
        already_in_millions (bool): Whether the input value is already scaled to millions

    Returns:
        tuple: (scaled_value, unit_name, unit_abbreviation)
    """
    # If value is already in millions, convert back to raw currency for proper scaling
    if already_in_millions:
        raw_value = value * 1e6
    else:
        raw_value = value

    abs_value = abs(raw_value)

    if abs_value >= 1e12:  # Trillions
        return raw_value / 1e12, "Trillions USD", "T"
    elif abs_value >= 1e9:  # Billions
        return raw_value / 1e9, "Billions USD", "B"
    elif abs_value >= 1e6:  # Millions
        return raw_value / 1e6, "Millions USD", "M"
    elif abs_value >= 1e3:  # Thousands
        return raw_value / 1e3, "Thousands USD", "K"
    else:
        return raw_value, "USD", ""


def save_fcf_analysis_to_file(fcf_df, company_name, ticker=None, output_dir=None):
    """
    Save FCF analysis data to configured export directory

    Args:
        fcf_df (pd.DataFrame): FCF analysis DataFrame
        company_name (str): Company name
        ticker (str): Ticker symbol (optional)
        output_dir (str): Output directory (optional, uses configured if None)

    Returns:
        str: Path to saved file or None if failed
    """
    try:
        # Use configured export directory if none specified
        if output_dir is None:
            output_dir = ensure_export_directory()
            if output_dir is None:
                logger.error("No usable export directory available")
                return None

        # Create output directory
        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create export directory '{output_dir}': {e}")
                return None

        # Generate filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if ticker:
            filename = f"{ticker}_FCF_Analysis_{timestamp}.csv"
        else:
            safe_company_name = company_name.replace(' ', '_').replace('/', '_')
            filename = f"{safe_company_name}_FCF_Analysis_{timestamp}.csv"

        filepath = output_path / filename

        # Save to CSV
        fcf_df.to_csv(filepath, index=False)

        logger.info(f"Saved FCF analysis to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Error saving FCF analysis: {e}")
        return None


def save_enhanced_dcf_to_file(
    dcf_df, dcf_results, dcf_assumptions, ticker=None, current_price=None, output_dir=None
):
    """
    Save enhanced DCF analysis data to configured export directory

    Args:
        dcf_df (pd.DataFrame): DCF projections DataFrame
        dcf_results (dict): DCF results
        dcf_assumptions (dict): DCF assumptions
        ticker (str): Ticker symbol (optional)
        current_price (float): Current stock price (optional)
        output_dir (str): Output directory (optional, uses configured if None)

    Returns:
        str: Path to saved file or None if failed
    """
    try:
        # Use configured export directory if none specified
        if output_dir is None:
            output_dir = ensure_export_directory()
            if output_dir is None:
                logger.error("No usable export directory available")
                return None

        # Create output directory
        output_path = Path(output_dir)
        if not output_path.exists():
            try:
                output_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.error(f"Failed to create export directory '{output_dir}': {e}")
                return None

        # Generate filename with timestamp
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if ticker:
            filename = f"{ticker}_DCF_Analysis_Enhanced_{timestamp}.csv"
        else:
            filename = f"DCF_Analysis_Enhanced_{timestamp}.csv"

        filepath = output_path / filename

        # Create the enhanced CSV data
        csv_data = create_enhanced_dcf_csv_export(
            dcf_df, dcf_results, dcf_assumptions, ticker, current_price
        )

        # Save to file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(csv_data)

        logger.info(f"Saved enhanced DCF analysis to {filepath}")
        return str(filepath)

    except Exception as e:
        logger.error(f"Error saving enhanced DCF analysis: {e}")
        return None


def create_enhanced_dcf_csv_export(
    dcf_df, dcf_results, dcf_assumptions, ticker=None, current_price=None
):
    """
    Create enhanced CSV export with comprehensive analysis metadata for database compatibility

    Args:
        dcf_df (pd.DataFrame): Basic DCF projections DataFrame
        dcf_results (dict): Complete DCF calculation results
        dcf_assumptions (dict): DCF assumptions used in analysis
        ticker (str, optional): Company ticker symbol
        current_price (float, optional): Current market price

    Returns:
        str: CSV data as string
    """
    import io
    from datetime import datetime

    # Create StringIO buffer for CSV output
    output = io.StringIO()

    # Current timestamp for analysis date
    analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Get company information
    company_name = (
        getattr(st.session_state.financial_calculator, 'company_name', None)
        if hasattr(st.session_state, 'financial_calculator')
        else None
    )
    if not company_name and ticker:
        company_name = ticker
    elif not company_name:
        company_name = (
            os.path.basename(st.session_state.company_folder)
            if st.session_state.company_folder
            else get_default_company_name()
        )

    # Get market data from dcf_results
    market_data = dcf_results.get('market_data', {})

    # Fetch current market price if not provided
    if not current_price and ticker:
        try:
            if hasattr(st.session_state, 'dcf_valuator') and st.session_state.dcf_valuator:
                market_data_fresh = st.session_state.dcf_valuator._get_market_data()
                current_price = market_data_fresh.get('current_price', 0)
        except Exception as e:
            current_price = 0

    current_price = current_price or 0

    # Format assumptions as text
    assumptions_text = "; ".join(
        [
            f"Discount Rate: {dcf_assumptions.get('discount_rate', 0)*100:.1f}%",
            f"Terminal Growth Rate: {dcf_assumptions.get('terminal_growth_rate', 0)*100:.1f}%",
            f"Projection Years: {dcf_assumptions.get('projection_years', 5)}",
            f"Growth Rate Yr1-5: {dcf_assumptions.get('growth_rate_yr1_5', 0)*100:.1f}%",
        ]
    )

    # Extract key results
    calculated_ev = dcf_results.get('enterprise_value', 0) or dcf_results.get(
        'equity_value', 0
    )  # Fallback to equity for FCFE
    calculated_fair_value = dcf_results.get('value_per_share', 0)
    fcf_type = dcf_results.get('fcf_type', get_unknown_fcf_type())

    # Get appropriate scales for financial values
    # CRITICAL BUG FIX: DCF results are in actual currency units, need proper scaling
    # The dcf_valuation.py produces values like 3,487,000,000,000 for $3.487T
    ev_scaled, ev_unit, ev_abbrev = get_financial_scale_and_unit(
        calculated_ev, already_in_millions=False
    )
    equity_value = dcf_results.get('equity_value', 0)
    equity_scaled, equity_unit, equity_abbrev = get_financial_scale_and_unit(
        equity_value, already_in_millions=False
    )
    terminal_value = dcf_results.get('terminal_value', 0)
    terminal_scaled, terminal_unit, terminal_abbrev = get_financial_scale_and_unit(
        terminal_value, already_in_millions=False
    )
    net_debt = dcf_results.get('net_debt', 0)
    debt_scaled, debt_unit, debt_abbrev = get_financial_scale_and_unit(
        net_debt, already_in_millions=False
    )

    # === SECTION 1: ANALYSIS METADATA ===
    output.write("# DCF ANALYSIS METADATA\n")
    output.write(
        f"analysis_date,ticker_symbol,company_name,fcf_type_used,calculated_enterprise_value_{ev_unit.lower().replace(' ', '_')},calculated_fair_value_per_share,current_market_price,assumptions\n"
    )
    output.write(
        f'"{analysis_date}","{ticker or ""}","{company_name}","{fcf_type}",{ev_scaled:.3f},{calculated_fair_value:.2f},{current_price:.2f},"{assumptions_text}"\n'
    )
    output.write("\n")

    # === SECTION 2: KEY RESULTS SUMMARY ===
    output.write("# KEY RESULTS SUMMARY\n")
    output.write("metric,value,unit\n")
    output.write(f'"Enterprise Value",{ev_scaled:.3f},"{ev_unit}"\n')
    output.write(f'"Equity Value",{equity_scaled:.3f},"{equity_unit}"\n')
    # Get appropriate currency for per-share values
    per_share_currency = (
        get_currency_symbol_per_share(st.session_state.financial_calculator)
        if hasattr(st.session_state, 'financial_calculator')
        else "$"
    )
    output.write(f'"Fair Value Per Share",{calculated_fair_value:.2f},"{per_share_currency}"\n')
    output.write(f'"Current Market Price",{current_price:.2f},"{per_share_currency}"\n')

    # Calculate upside/downside if both prices available
    if current_price > 0 and calculated_fair_value > 0:
        upside_downside = (calculated_fair_value - current_price) / current_price
        output.write(f'"Upside/Downside Potential",{upside_downside*100:.1f},"Percent"\n')

    output.write(f'"Terminal Value",{terminal_scaled:.3f},"{terminal_unit}"\n')
    output.write(f'"Net Debt",{debt_scaled:.3f},"{debt_unit}"\n')

    # Market data
    shares_outstanding = market_data.get('shares_outstanding', 0)
    shares_scaled, shares_unit, shares_abbrev = get_financial_scale_and_unit(shares_outstanding)
    # For shares, we want to show the count unit, not USD
    if shares_outstanding >= 1e9:
        shares_unit = "Billions"
    elif shares_outstanding >= 1e6:
        shares_unit = "Millions"
    elif shares_outstanding >= 1e3:
        shares_unit = "Thousands"
    else:
        shares_unit = "Count"

    output.write(f'"Shares Outstanding",{shares_scaled:.2f},"{shares_unit}"\n')
    output.write("\n")

    # === SECTION 3: DETAILED ASSUMPTIONS ===
    output.write("# ANALYSIS ASSUMPTIONS\n")
    output.write("assumption_type,value,unit\n")
    for key, value in dcf_assumptions.items():
        if isinstance(value, (int, float)):
            if 'rate' in key.lower() or 'growth' in key.lower():
                output.write(f'"{key}",{value*100:.2f},"Percent"\n')
            else:
                output.write(f'"{key}",{value},"Count"\n')
        else:
            output.write(f'"{key}","{value}","Text"\n')
    output.write("\n")

    # === SECTION 4: HISTORICAL DATA (if available) ===
    if 'historical_growth' in dcf_results:
        output.write("# HISTORICAL GROWTH RATES\n")
        output.write("period,growth_rate,unit\n")
        hist_growth = dcf_results['historical_growth']
        for period, rate in hist_growth.items():
            if isinstance(rate, (int, float)):
                output.write(f'"{period}",{rate*100:.2f},"Percent"\n')
    output.write("\n")

    # === SECTION 5: PROJECTIONS TABLE (Enhanced version of original dcf_df) ===
    output.write("# DCF PROJECTIONS\n")

    # Enhanced projections with additional metadata columns
    enhanced_df = dcf_df.copy()
    enhanced_df.insert(0, 'analysis_date', analysis_date)
    enhanced_df.insert(1, 'ticker_symbol', ticker or '')
    enhanced_df.insert(2, 'company_name', company_name)
    enhanced_df.insert(3, 'fcf_type', fcf_type)

    # Add discount factors for transparency
    if 'projections' in dcf_results:
        discount_rate = dcf_assumptions.get('discount_rate', 0)
        discount_factors = [1 / ((1 + discount_rate) ** year) for year in enhanced_df['Year']]
        enhanced_df['Discount_Factor'] = [f"{factor:.4f}" for factor in discount_factors]

    # Write enhanced DataFrame
    enhanced_df.to_csv(output, index=False)
    output.write("\n")

    # === SECTION 6: DATABASE IMPORT NOTES ===
    output.write("# DATABASE IMPORT GUIDELINES\n")
    output.write("# This CSV is structured for database import with the following sections:\n")
    output.write("# 1. ANALYSIS METADATA - Primary analysis record (one row per analysis)\n")
    output.write("# 2. KEY RESULTS SUMMARY - Key metrics in name-value pairs\n")
    output.write("# 3. ANALYSIS ASSUMPTIONS - Assumption parameters used\n")
    output.write("# 4. HISTORICAL GROWTH RATES - Historical performance data\n")
    output.write("# 5. DCF PROJECTIONS - Year-by-year projections with full context\n")
    output.write("#\n")
    output.write("# Recommended database tables:\n")
    output.write("# - dcf_analyses (metadata section)\n")
    output.write("# - dcf_results (key results)\n")
    output.write("# - dcf_assumptions (assumptions)\n")
    output.write("# - dcf_projections (projections)\n")
    output.write("# - historical_data (historical growth rates)\n")

    # Get the CSV string
    csv_string = output.getvalue()
    output.close()

    return csv_string


def render_dividend_history_chart(ddm_valuator, financial_calculator=None):
    """
    Render dividend history chart for DDM analysis

    Args:
        ddm_valuator: DDM valuator instance
        financial_calculator: Financial calculator instance (optional)
    """
    try:
        # Extract dividend data directly from DDM valuator
        dividend_result = ddm_valuator._extract_dividend_data()

        if not dividend_result.get('success') or not dividend_result.get('data'):
            st.info("📊 **Dividend History**: No dividend data available for this company")
            with st.expander("Why might dividend data be missing?", expanded=False):
                st.markdown(
                    """
                **Possible reasons:**
                - Company doesn't pay dividends (growth stock)
                - Very young company with no dividend history
                - Insufficient historical data available
                - Data source limitations
                
                **What you can do:**
                - Use DCF analysis instead for non-dividend paying stocks
                - Check if company has started paying dividends recently
                - Verify ticker symbol is correct
                """
                )
            return

        dividend_data = dividend_result['data']

        if not dividend_data.get('years') or not dividend_data.get('dividends_per_share'):
            st.info("📊 **Dividend History**: No sufficient dividend data to display chart")
            return

        st.subheader("📈 Dividend History & Trends")
        st.markdown("**Review historical dividend patterns to inform your growth assumptions**")

        # Import chart libraries
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        # Get data (last 10 years for better readability)
        years = dividend_data['years'][-10:]
        dividends = dividend_data['dividends_per_share'][-10:]

        # Create subplot chart
        fig = make_subplots(
            rows=2,
            cols=1,
            subplot_titles=('Annual Dividend Per Share', 'Year-over-Year Growth Rate'),
            vertical_spacing=0.12,
        )

        # Dividend trend line
        fig.add_trace(
            go.Scatter(
                x=years,
                y=dividends,
                mode='lines+markers',
                name='Dividend/Share',
                line=dict(color='green', width=3),
                marker=dict(size=8),
                hovertemplate='Year: %{x}<br>Dividend: $%{y:.2f}<extra></extra>',
            ),
            row=1,
            col=1,
        )

        # Growth rates if available
        if len(dividend_data.get('growth_rates', [])) > 0:
            growth_rates = [
                r * 100 for r in dividend_data['growth_rates'][-9:]
            ]  # One less than dividends
            colors = ['green' if r > 0 else 'red' for r in growth_rates]

            fig.add_trace(
                go.Bar(
                    x=years[1 : len(growth_rates) + 1],
                    y=growth_rates,
                    name='Growth Rate (%)',
                    marker_color=colors,
                    hovertemplate='Year: %{x}<br>Growth: %{y:.1f}%<extra></extra>',
                ),
                row=2,
                col=1,
            )

        # Get ticker for title
        ticker = (
            getattr(financial_calculator, 'ticker_symbol', 'Company')
            if financial_calculator
            else 'Company'
        )

        # Update layout
        fig.update_layout(
            title=f"Historical Dividend Analysis - {ticker}",
            height=600,
            showlegend=True,
            hovermode='x unified',
        )

        # Update axes
        fig.update_xaxes(title_text="Year", row=2, col=1)
        fig.update_yaxes(title_text="Dividend ($)", row=1, col=1)
        fig.update_yaxes(title_text="Growth Rate (%)", row=2, col=1)

        # Add zero line for growth rates
        if len(dividend_data.get('growth_rates', [])) > 0:
            fig.add_hline(y=0, row=2, col=1, line_dash="dash", line_color="gray", opacity=0.5)

        st.plotly_chart(fig, use_container_width=True)

        # Show key dividend metrics
        dividend_metrics = dividend_result.get('metrics', {})
        if dividend_metrics:
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                latest_dividend = dividend_data.get('latest_dividend', 0)
                st.metric("Latest Dividend", f"${latest_dividend:.2f}")

            with col2:
                if 'dividend_cagr_3y' in dividend_metrics:
                    cagr_3y = dividend_metrics['dividend_cagr_3y'] * 100
                    st.metric("3Y Growth (CAGR)", f"{cagr_3y:.1f}%")

            with col3:
                if 'growth_consistency' in dividend_metrics:
                    consistency = dividend_metrics['growth_consistency'] * 100
                    st.metric("Growth Consistency", f"{consistency:.0f}%")

            with col4:
                if 'payout_ratio' in dividend_metrics:
                    payout = dividend_metrics['payout_ratio'] * 100
                    st.metric("Payout Ratio", f"{payout:.1f}%")

        # Add helpful context
        with st.expander("💡 How to use this data for DDM assumptions", expanded=False):
            st.markdown(
                """
            **Using dividend history for growth assumptions:**
            
            🔹 **Recent Trends**: Look at the last 3-5 years for current growth patterns
            
            🔹 **Growth Consistency**: Consistent positive growth suggests sustainable dividend policy
            
            🔹 **Payout Ratio**: Lower ratios (< 60%) suggest room for future dividend growth
            
            🔹 **Growth Volatility**: High volatility may require conservative assumptions
            
            **Recommended approach:**
            - Use 3-5 year CAGR as baseline for Stage 1 growth
            - Consider economic cycles and company maturity
            - Be conservative with high-growth assumptions
            - Factor in payout ratio sustainability
            """
            )

    except Exception as e:
        st.error(f"❌ Error displaying dividend history: {e}")
        st.info("Unable to load dividend history chart. Please try again or contact support.")


def render_ddm_analysis():
    """Render DDM Analysis tab"""
    st.header("🏆 Dividend Discount Model (DDM) Valuation")
    st.markdown("**Dividend-based equity valuation using multiple DDM variants**")

    # Show centralized data source information
    if st.session_state.financial_calculator:
        render_centralized_data_source_info()
        st.markdown("---")

    # Simple explanation for DDM
    with st.expander("📖 What is DDM Valuation?", expanded=False):
        st.markdown(
            """
        **DDM values stocks based on expected future dividends.**
        
        **How it works**: Calculates what you should pay today for all future dividend payments.
        
        **Three Models Implemented:**
        
        🔹 **Gordon Growth Model** - Single constant growth rate forever
        - Best for: Mature dividend payers with steady growth
        - Formula: Value = Next Dividend ÷ (Required Return - Growth Rate)
        
        🔹 **Two-Stage DDM** - High growth period, then stable growth
        - Phase 1: Higher growth for set years (e.g., 8% for 5 years)
        - Phase 2: Lower stable growth forever (e.g., 3% perpetual)
        - Best for: Growing companies transitioning to maturity
        
        🔹 **Multi-Stage DDM** - Three growth phases
        - Stage 1: High growth period
        - Stage 2: Moderate growth period  
        - Stage 3: Stable long-term growth
        - Best for: Complex growth transitions
        
        **Auto-Selection**: The system automatically picks the best model based on your company's dividend history and growth patterns.
        """
        )

    # Get financial calculator
    financial_calculator = st.session_state.get('financial_calculator')
    if not financial_calculator:
        st.error("❌ No financial data loaded. Please load company data first.")
        return

    # Initialize DDM valuator
    try:
        ddm_valuator = DDMValuator(financial_calculator)
    except Exception as e:
        st.error(f"❌ Error initializing DDM valuator: {e}")
        return

    # Display dividend history chart immediately (before configuration)
    render_dividend_history_chart(ddm_valuator, financial_calculator)

    # Add separator
    st.divider()

    # DDM Configuration Panel
    st.subheader("⚙️ DDM Configuration")

    with st.expander("Configure DDM Parameters", expanded=True):
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("**Required Rate of Return**")
            discount_rate = (
                st.number_input(
                    "Discount Rate (%)",
                    min_value=1.0,
                    max_value=30.0,
                    value=10.0,
                    step=0.5,
                    help="Cost of equity / required rate of return",
                )
                / 100
            )

            model_type = st.selectbox(
                "Model Type",
                options=['auto', 'gordon', 'two_stage', 'multi_stage'],
                index=0,
                help="Auto selects best model based on company characteristics",
            )

        with col2:
            st.markdown("**Growth Rates**")
            stage1_growth = (
                st.number_input(
                    "Stage 1 Growth (%)",
                    min_value=-10.0,
                    max_value=50.0,
                    value=8.0,
                    step=0.5,
                    help="High growth period (Years 1-5)",
                )
                / 100
            )

            stage2_growth = (
                st.number_input(
                    "Stage 2 Growth (%)",
                    min_value=-5.0,
                    max_value=20.0,
                    value=4.0,
                    step=0.5,
                    help="Moderate growth period (Years 6-10)",
                )
                / 100
            )

            terminal_growth = (
                st.number_input(
                    "Terminal Growth (%)",
                    min_value=0.0,
                    max_value=8.0,
                    value=3.0,
                    step=0.1,
                    help="Long-term sustainable growth rate",
                )
                / 100
            )

        with col3:
            st.markdown("**Time Periods**")
            stage1_years = st.number_input(
                "Stage 1 Years",
                min_value=1,
                max_value=15,
                value=5,
                help="Length of high growth period",
            )

            stage2_years = st.number_input(
                "Stage 2 Years",
                min_value=1,
                max_value=15,
                value=5,
                help="Length of moderate growth period",
            )

    # DDM Calculation
    if st.button("🚀 Calculate DDM Valuation", type="primary"):
        with st.spinner("Calculating DDM valuation..."):
            # Prepare assumptions
            ddm_assumptions = {
                'discount_rate': discount_rate,
                'terminal_growth_rate': terminal_growth,
                'stage1_growth_rate': stage1_growth,
                'stage2_growth_rate': stage2_growth,
                'stage1_years': stage1_years,
                'stage2_years': stage2_years,
                'model_type': model_type,
            }

            # Calculate DDM with progress indicator
            with st.spinner("📈 Calculating DDM valuation..."):
                ddm_results = ddm_valuator.calculate_ddm_valuation(ddm_assumptions)

            # Store in session state
            st.session_state.ddm_results = ddm_results
            st.session_state.ddm_assumptions = ddm_assumptions

    # Display Results
    if 'ddm_results' in st.session_state and st.session_state.ddm_results:
        ddm_results = st.session_state.ddm_results

        # Check for errors
        if 'error' in ddm_results:
            st.error(
                f"❌ DDM Calculation Error: {ddm_results.get('error_message', 'Unknown error')}"
            )
            return

        # Key Metrics Summary
        st.subheader("📊 DDM Valuation Summary")

        # Get key values
        intrinsic_value = ddm_results.get('intrinsic_value', 0)
        current_price = ddm_results.get('current_price', 0)
        model_variant = ddm_results.get('model_variant', 'DDM')
        upside_downside = ddm_results.get('upside_downside', 0) * 100
        dividend_yield = ddm_results.get('dividend_yield', 0) * 100
        current_dividend = ddm_results.get('current_dividend', 0)

        # Key metrics display
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Intrinsic Value", f"${intrinsic_value:.2f}", help=f"Based on {model_variant}"
            )

        with col2:
            if current_price > 0:
                st.metric(
                    "Current Price",
                    f"${current_price:.2f}",
                    delta=f"{upside_downside:+.1f}%",
                    delta_color="normal" if upside_downside > 0 else "inverse",
                )
            else:
                st.metric("Current Price", "N/A")

        with col3:
            st.metric(
                "Dividend Yield",
                f"{dividend_yield:.2f}%",
                help="Based on current dividend and price",
            )

        with col4:
            st.metric(
                "Current Dividend",
                f"${current_dividend:.2f}",
                help="Latest annual dividend per share",
            )

        # Model Details
        st.subheader("🔍 Model Details")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Model Information**")
            # Show if auto-selection was used
            if model_type == 'auto':
                st.success(f"🤖 **Auto-Selected Model:** {model_variant}")
                st.caption(
                    "The system automatically chose the best model based on dividend history and growth patterns"
                )
            else:
                st.write(f"**Model Used:** {model_variant}")
            st.write(
                f"**Discount Rate:** {ddm_results.get('required_return', discount_rate)*100:.1f}%"
            )

            if 'growth_rate' in ddm_results:
                st.write(f"**Growth Rate:** {ddm_results['growth_rate']*100:.1f}%")

            # Display dividend data quality
            dividend_metrics = ddm_results.get('dividend_metrics', {})
            if dividend_metrics:
                st.markdown("**Dividend Metrics**")
                if 'dividend_cagr_3y' in dividend_metrics:
                    st.write(
                        f"**3Y Dividend CAGR:** {dividend_metrics['dividend_cagr_3y']*100:.1f}%"
                    )
                if 'growth_consistency' in dividend_metrics:
                    st.write(
                        f"**Growth Consistency:** {dividend_metrics['growth_consistency']*100:.0f}%"
                    )
                if 'payout_ratio' in dividend_metrics:
                    st.write(f"**Payout Ratio:** {dividend_metrics['payout_ratio']*100:.1f}%")

        with col2:
            st.markdown("**Valuation Summary**")
            ticker = getattr(financial_calculator, 'ticker_symbol', 'N/A')
            currency = ddm_results.get('currency', 'USD')

            if current_price > 0:
                if upside_downside > 10:
                    verdict = "🟢 **UNDERVALUED**"
                elif upside_downside > -10:
                    verdict = "🟡 **FAIRLY VALUED**"
                else:
                    verdict = "🔴 **OVERVALUED**"

                st.markdown(f"**Ticker:** {ticker}")
                st.markdown(f"**Currency:** {currency}")
                st.markdown(f"**Investment Verdict:** {verdict}")
                st.markdown(f"**Upside/Downside:** {upside_downside:+.1f}%")
            else:
                st.write("**Market price unavailable for comparison**")

        # Sensitivity Analysis
        st.subheader("🎛️ DDM Sensitivity Analysis")

        with st.expander("Configure Sensitivity Analysis"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Discount Rate Range (%)**")
                dr_min_pct = st.number_input(
                    "Min Discount Rate (%)", value=8.0, step=0.5, format="%.1f", key="ddm_dr_min"
                )
                dr_max_pct = st.number_input(
                    "Max Discount Rate (%)", value=15.0, step=0.5, format="%.1f", key="ddm_dr_max"
                )

            with col2:
                st.markdown("**Growth Rate Range (%)**")
                gr_min_pct = st.number_input(
                    "Min Growth Rate (%)", value=0.0, step=0.5, format="%.1f", key="ddm_gr_min"
                )
                gr_max_pct = st.number_input(
                    "Max Growth Rate (%)", value=8.0, step=0.5, format="%.1f", key="ddm_gr_max"
                )

        if st.button("Generate DDM Sensitivity Analysis"):
            with st.spinner("Generating sensitivity analysis..."):
                # Convert to decimal
                dr_min = dr_min_pct / 100
                dr_max = dr_max_pct / 100
                gr_min = gr_min_pct / 100
                gr_max = gr_max_pct / 100

                discount_rates = np.linspace(dr_min, dr_max, 5)
                growth_rates = np.linspace(gr_min, gr_max, 5)

                # Calculate sensitivity
                sensitivity_results = ddm_valuator.sensitivity_analysis(
                    growth_rates, discount_rates, st.session_state.ddm_assumptions
                )

                # Create heatmap
                import plotly.graph_objects as go

                with np.errstate(invalid='ignore', over='ignore'):
                    valuations = np.array(sensitivity_results['valuations'], dtype=float)
                    upside_matrix = (
                        np.array(sensitivity_results['upside_downside'], dtype=float) * 100
                    )

                    # Validate arrays for finite values
                    if not np.all(np.isfinite(valuations)):
                        st.warning(
                            "Some valuation results contain non-finite values and will be filtered"
                        )
                        valuations = np.where(np.isfinite(valuations), valuations, 0)

                    if not np.all(np.isfinite(upside_matrix)):
                        st.warning(
                            "Some upside/downside results contain non-finite values and will be filtered"
                        )
                        upside_matrix = np.where(np.isfinite(upside_matrix), upside_matrix, 0)

                fig = go.Figure(
                    data=go.Heatmap(
                        z=upside_matrix,
                        x=[f"{rate*100:.1f}%" for rate in growth_rates],
                        y=[f"{rate*100:.1f}%" for rate in discount_rates],
                        colorscale=[
                            [0, 'red'],
                            [0.3, 'orange'],
                            [0.5, 'yellow'],
                            [0.7, 'lightgreen'],
                            [1, 'green'],
                        ],
                        text=[
                            [f"${val:.1f}<br>{up:+.1f}%" for val, up in zip(val_row, up_row)]
                            for val_row, up_row in zip(valuations, upside_matrix)
                        ],
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        hovertemplate="Growth: %{x}<br>Discount: %{y}<br>Upside: %{z:.1f}%<extra></extra>",
                    )
                )

                fig.update_layout(
                    title=f"DDM Sensitivity Analysis - {ticker}",
                    xaxis_title="Growth Rate",
                    yaxis_title="Discount Rate",
                    height=500,
                )

                st.plotly_chart(fig, use_container_width=True)

                # Store sensitivity results
                st.session_state.ddm_sensitivity = sensitivity_results

        # Export DDM Results
        st.subheader("📁 Export DDM Analysis")

        if st.button("Export DDM Results to CSV"):
            # Prepare export data
            export_data = {
                'Metric': [
                    'Intrinsic Value',
                    'Current Price',
                    'Upside/Downside (%)',
                    'Model Used',
                    'Discount Rate (%)',
                    'Current Dividend',
                    'Dividend Yield (%)',
                ],
                'Value': [
                    f"${intrinsic_value:.2f}",
                    f"${current_price:.2f}" if current_price > 0 else "N/A",
                    f"{upside_downside:+.1f}%",
                    model_variant,
                    f"{discount_rate*100:.1f}%",
                    f"${current_dividend:.2f}",
                    f"{dividend_yield:.2f}%",
                ],
            }

            df = pd.DataFrame(export_data)
            csv = df.to_csv(index=False)

            st.download_button(
                label="📥 Download DDM Analysis",
                data=csv,
                file_name=f"ddm_analysis_{ticker}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )


def render_pb_analysis():
    """Render P/B Analysis tab"""
    st.header("📊 Price-to-Book (P/B) Ratio Analysis")

    if not st.session_state.financial_calculator:
        st.error("❌ No financial data available. Please load data first from the sidebar.")
        return

    # Show centralized data source information
    render_centralized_data_source_info()
    st.markdown("---")

    # Check data availability for P/B calculation
    has_enhanced_data_manager = (
        hasattr(st.session_state.financial_calculator, 'enhanced_data_manager')
        and st.session_state.financial_calculator.enhanced_data_manager is not None
    )

    # Check if we have balance sheet data for P/B calculation
    balance_sheet_data = st.session_state.financial_calculator.financial_data.get(
        'Balance Sheet', {}
    )

    # Check if we have valid balance sheet data (handle both dict and DataFrame)
    def has_valid_data(data):
        if data is None:
            return False
        if isinstance(data, dict):
            return bool(data)
        if hasattr(data, 'empty'):  # pandas DataFrame
            return not data.empty
        return bool(data)

    if not has_valid_data(balance_sheet_data):
        # Try alternative key names
        for key in ['balance_fy', 'balance_ltm', 'balance_sheet']:
            balance_sheet_data = st.session_state.financial_calculator.financial_data.get(key, {})
            if has_valid_data(balance_sheet_data):
                break

    # If no local balance sheet data and no enhanced data manager, show warning
    if not has_valid_data(balance_sheet_data) and not has_enhanced_data_manager:
        st.warning(
            "⚠️ No balance sheet data available. P/B analysis requires balance sheet data for book value calculation."
        )
        st.info(
            "💡 To perform P/B analysis, please ensure you have balance sheet data loaded either from Excel files or API sources."
        )
        return

    # If no local data but enhanced data manager is available, show info that API will be used
    if not has_valid_data(balance_sheet_data) and has_enhanced_data_manager:
        st.info(
            "📡 No local balance sheet data found. Will attempt to fetch data from API sources for P/B analysis."
        )

    # Check for ticker symbol
    ticker_symbol = st.session_state.financial_calculator.ticker_symbol
    if not ticker_symbol:
        st.warning(
            "⚠️ No ticker symbol available. P/B analysis requires a ticker symbol for market data."
        )
        st.info("💡 Please ensure a valid ticker symbol is provided for market price comparison.")
        return

    try:
        # Create P/B valuator
        pb_valuator = PBValuator(st.session_state.financial_calculator)

        # Show loading message
        with st.spinner("🔄 Calculating P/B analysis..."):
            # Perform P/B analysis
            pb_analysis = pb_valuator.calculate_pb_analysis(ticker_symbol)

        # Check for errors
        if 'error' in pb_analysis:
            st.error(
                f"❌ P/B Analysis Error: {pb_analysis.get('error_message', 'Unknown error occurred')}"
            )

            # Provide specific guidance based on error type
            error_type = pb_analysis.get('error')
            if error_type == 'book_value_unavailable':
                st.info(
                    "💡 **Troubleshooting:** Book value calculation failed. This may be due to:"
                )
                st.write("• Missing shareholders' equity data in balance sheet")
                st.write("• Invalid or zero shares outstanding")
                st.write("• Data formatting issues")
            elif error_type == 'market_data_unavailable':
                st.info("💡 **Troubleshooting:** Market data unavailable. This may be due to:")
                st.write("• Invalid ticker symbol")
                st.write("• Network connectivity issues")
                st.write("• Market data provider limitations")

            return

        # Display P/B analysis results using the visualizer
        display_pb_analysis(pb_analysis)

        # Add capture to watch list functionality
        st.markdown("---")
        st.subheader("📋 Capture to Watch List")

        # Watch list capture section
        try:
            watch_list_manager = WatchListManager()
            watch_lists = watch_list_manager.get_all_watch_lists()

            if watch_lists:
                col1, col2 = st.columns([2, 1])

                with col1:
                    selected_watch_list = st.selectbox(
                        "Select Watch List:",
                        options=list(watch_lists.keys()),
                        help="Choose a watch list to save this P/B analysis",
                    )

                with col2:
                    if st.button("📊 Capture P/B Analysis", type="primary"):
                        # Prepare combined analysis data for watch list
                        analysis_data = {
                            'ticker': ticker_symbol,
                            'company_name': getattr(
                                st.session_state.financial_calculator, 'company_name', ticker_symbol
                            ),
                            'current_price': pb_analysis.get('current_data', {}).get(
                                'current_price', 0
                            ),
                            'fair_value': pb_analysis.get('valuation_analysis', {})
                            .get('valuation_ranges', {})
                            .get('fair_value', 0),
                            'pb_analysis': pb_analysis,
                            'metadata': {
                                'analysis_type': 'P/B Analysis',
                                'data_source': getattr(
                                    st.session_state.financial_calculator,
                                    '_data_source_used',
                                    'Unknown',
                                ),
                                'currency': pb_analysis.get('currency', 'USD'),
                                'is_tase_stock': pb_analysis.get('is_tase_stock', False),
                            },
                        }

                        if watch_list_manager.add_analysis_to_watch_list(
                            selected_watch_list, analysis_data
                        ):
                            st.success(
                                f"✅ P/B analysis for {ticker_symbol} captured to '{selected_watch_list}' watch list!"
                            )
                        else:
                            st.error("❌ Failed to capture analysis to watch list")
            else:
                st.info(
                    "💡 No watch lists available. Create a watch list in the Watch Lists tab to capture P/B analysis."
                )

        except Exception as e:
            st.warning(f"Watch list functionality unavailable: {str(e)}")

        # Add export functionality
        st.markdown("---")
        st.subheader("📤 Export P/B Analysis")

        col1, col2 = st.columns(2)

        with col1:
            # Create summary report
            summary_report = pb_valuator.create_pb_summary_report(pb_analysis)

            st.download_button(
                label="📄 Download P/B Summary Report",
                data=summary_report,
                file_name=f"{ticker_symbol}_pb_analysis_summary.txt",
                mime="text/plain",
                help="Download a text summary of the P/B analysis",
            )

        with col2:
            # Create detailed JSON export
            import json

            pb_json = json.dumps(pb_analysis, indent=2, default=str)

            st.download_button(
                label="📊 Download Detailed P/B Data (JSON)",
                data=pb_json,
                file_name=f"{ticker_symbol}_pb_analysis_detailed.json",
                mime="application/json",
                help="Download detailed P/B analysis data in JSON format",
            )

        # Add integration notes
        st.markdown("---")
        st.info(
            """
        **📋 P/B Analysis Notes:**
        • P/B ratio compares market price to book value per share
        • Values below 1.0 may indicate undervaluation or financial distress
        • Industry comparisons help contextualize P/B ratios
        • Historical trends show valuation patterns over time
        • Consider P/B alongside other valuation metrics for comprehensive analysis
        """
        )

        # Success message
        st.success(f"✅ P/B analysis completed successfully for {ticker_symbol}")

    except Exception as e:
        st.error(f"❌ Error during P/B analysis: {str(e)}")
        logger.error(f"Error in render_pb_analysis: {e}", exc_info=True)

        st.info("💡 **Troubleshooting:** Please check that:")
        st.write("• Balance sheet data is properly loaded")
        st.write("• Ticker symbol is valid and accessible")
        st.write("• Internet connection is available for market data")
        st.write("• All required dependencies are installed")


def render_report_generation():
    """Render the PDF report generation tab"""
    st.header("📄 Generate Comprehensive Report")

    if not st.session_state.financial_calculator.fcf_results:
        st.error("❌ No financial data available. Please load data first from the sidebar.")
        return

    # Display Company Information below header
    folder_name = (
        os.path.basename(st.session_state.company_folder)
        if st.session_state.company_folder
        else get_unknown_company_name()
    )
    ticker = (
        st.session_state.financial_calculator.ticker_symbol
        if st.session_state.financial_calculator
        else None
    )
    current_price = (
        st.session_state.financial_calculator.current_stock_price
        if st.session_state.financial_calculator
        else None
    )

    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = (
        getattr(st.session_state.financial_calculator, 'company_name', None)
        or ticker
        or folder_name
    )

    # Company info row
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.subheader(f"🏢 {company_name}")

    with col2:
        if ticker:
            st.metric("📊 Ticker Symbol", ticker)
        else:
            st.metric("📊 Ticker Symbol", "N/A")

    with col3:
        if current_price:
            currency_symbol = get_currency_symbol_per_share(st.session_state.financial_calculator)
            st.metric("💰 Market Price", f"{current_price:.2f} {currency_symbol}")
        else:
            st.metric("💰 Market Price", "N/A")

    st.markdown("---")

    # Auto-detect company information
    st.subheader("📋 Report Configuration")

    # Extract information from current analysis
    folder_name = (
        os.path.basename(st.session_state.company_folder)
        if st.session_state.company_folder
        else "Company Analysis"
    )
    auto_ticker = (
        st.session_state.financial_calculator.ticker_symbol
        if st.session_state.financial_calculator
        else ""
    )

    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    auto_company_name = (
        getattr(st.session_state.financial_calculator, 'company_name', None)
        or auto_ticker
        or folder_name
    )

    # Get market data from DCF valuator
    auto_current_price = 0.0
    if hasattr(st.session_state, 'dcf_valuator') and st.session_state.dcf_valuator:
        try:
            market_data = st.session_state.dcf_valuator._get_market_data()
            auto_current_price = market_data.get('current_price') or 0.0
            if market_data.get('ticker_symbol'):
                auto_ticker = market_data.get('ticker_symbol')
        except Exception as e:
            logger.warning(f"Could not fetch market data: {e}")

    # Show auto-detected information
    st.markdown("**🔍 Auto-Detected Information**")
    col1, col2, col3 = st.columns(3)

    with col1:
        if auto_ticker:
            st.metric("Ticker Symbol", auto_ticker)
        else:
            st.metric("Ticker Symbol", "Not detected")

    with col2:
        if auto_current_price > 0:
            currency_symbol = get_currency_symbol_per_share(st.session_state.financial_calculator)
            st.metric("Current Price", f"{auto_current_price:.2f} {currency_symbol}")
        else:
            st.metric("Current Price", "Not available")

    with col3:
        download_path = (
            st.session_state.company_folder if st.session_state.company_folder else os.getcwd()
        )
        st.metric(
            "Download Path",
            f"...{download_path[-30:]}" if len(download_path) > 30 else download_path,
        )

    # Allow manual override if needed
    with st.expander("🛠️ Override Auto-Detected Values (Optional)"):
        col1, col2 = st.columns(2)

        with col1:
            company_name = st.text_input("Company Name", value=auto_company_name)

            # Show market-aware ticker input
            selected_market = st.session_state.get('selected_market', 'US Market')
            ticker_help = f"Ticker format for {selected_market}"
            if selected_market == "TASE (Tel Aviv)":
                ticker_help += " (include .TA suffix for TASE stocks)"

            ticker = st.text_input("Stock Ticker", value=auto_ticker, help=ticker_help)

        with col2:
            # Market-aware price label
            selected_market = st.session_state.get('selected_market', 'US Market')
            if selected_market == "TASE (Tel Aviv)":
                price_label = "Current Share Price (₪ ILA)"
                price_help = "Enter price in Agorot (ILA) for TASE stocks"
            else:
                price_label = "Current Share Price ($)"
                price_help = "Enter price in USD for US stocks"

            current_price = st.number_input(
                price_label,
                value=float(auto_current_price) if auto_current_price > 0 else 0.0,
                step=0.01,
                format="%.2f",
                help=price_help,
            )

            custom_download_path = st.text_input(
                "Download Path", value=download_path, help="Path where the PDF report will be saved"
            )

    # Use auto-detected values if not overridden
    if 'custom_download_path' not in locals():
        custom_download_path = download_path

    # Report options
    st.markdown("**📊 Report Sections**")
    col1, col2, col3 = st.columns(3)

    with col1:
        include_fcf = st.checkbox("Include FCF Analysis", value=True)
    with col2:
        include_dcf = st.checkbox("Include DCF Valuation", value=True)
    with col3:
        include_sensitivity = st.checkbox("Include Sensitivity Analysis", value=True)

    # Show what will be included in analysis
    per_share_currency = get_currency_symbol_per_share(st.session_state.financial_calculator)
    if current_price > 0:
        st.success(
            f"✅ Investment analysis will compare DCF fair value vs {current_price:.2f} {per_share_currency} market price"
        )
    elif auto_current_price > 0:
        st.success(
            f"✅ Investment analysis will compare DCF fair value vs {auto_current_price:.2f} {per_share_currency} auto-detected price"
        )
    else:
        st.info(
            "💡 No current price available - report will show fair value without market comparison"
        )

    st.markdown("---")

    # Analysis Status Check
    st.subheader("📋 Analysis Status")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**DCF Analysis Status:**")
        if (
            hasattr(st.session_state, 'user_dcf_assumptions')
            and st.session_state.user_dcf_assumptions
        ):
            st.success("✅ DCF Analysis Completed")
            dcf_type = st.session_state.user_dcf_assumptions.get('fcf_type', get_unknown_fcf_type())
            growth_1_5 = st.session_state.user_dcf_assumptions.get('growth_rate_yr1_5', 0) * 100
            discount_rate = st.session_state.user_dcf_assumptions.get('discount_rate', 0) * 100
            st.info(
                f"📈 **Method:** {dcf_type}  \n💰 **Growth (1-5yr):** {growth_1_5:.1f}%  \n🎯 **Discount Rate:** {discount_rate:.1f}%"
            )
        else:
            st.warning("⚠️ DCF Analysis Not Performed")
            st.info(
                "Go to 'DCF Analysis' tab and click 'Calculate DCF Valuation' to include your custom assumptions in the report."
            )

    with col2:
        st.markdown("**Sensitivity Analysis Status:**")
        if (
            hasattr(st.session_state, 'user_sensitivity_params')
            and st.session_state.user_sensitivity_params
        ):
            st.success("✅ Sensitivity Analysis Completed")
            dr_range = f"{st.session_state.user_sensitivity_params.get('discount_rate_min_pct', 8):.1f}%-{st.session_state.user_sensitivity_params.get('discount_rate_max_pct', 15):.1f}%"
            gr_range = f"{st.session_state.user_sensitivity_params.get('growth_rate_min_pct', 0):.1f}%-{st.session_state.user_sensitivity_params.get('growth_rate_max_pct', 5):.1f}%"
            st.info(
                f"📊 **Discount Rate Range:** {dr_range}  \n📈 **Growth Rate Range:** {gr_range}"
            )
        else:
            st.warning("⚠️ Custom Sensitivity Analysis Not Performed")
            st.info(
                "Go to 'DCF Analysis' tab and click 'Generate Sensitivity Analysis' to include your custom ranges in the report."
            )

    st.markdown("---")

    # Report preview section
    st.subheader("📊 Report Preview")

    # Show what will be included
    preview_items = []
    if include_fcf:
        preview_items.extend(
            [
                "✅ FCF Analysis Charts",
                "✅ Growth Rate Analysis Table",
                "✅ Historical FCF Data Table",
            ]
        )

    if include_dcf:
        preview_items.extend(
            ["✅ DCF Valuation Summary", "✅ DCF Projections Table", "✅ Waterfall Chart"]
        )

        # Check if we have current price (manual or auto-detected)
        final_preview_price = current_price if current_price > 0 else auto_current_price
        if final_preview_price > 0:
            preview_items.extend(
                ["🎯 Investment Recommendation", "📈 Fair Value vs Market Price Comparison"]
            )

        if include_sensitivity:
            preview_items.append("✅ Sensitivity Analysis Heatmap")

    if preview_items:
        for item in preview_items:
            st.write(item)
    else:
        st.warning("⚠️ Please select at least one analysis type to include in the report.")

    st.markdown("---")

    # Generate report button
    if st.button(
        "🚀 Generate PDF Report", type="primary", disabled=not (include_fcf or include_dcf)
    ):
        if not (include_fcf or include_dcf):
            st.error("❌ Please select at least one analysis type to include in the report.")
            return

        try:
            with st.spinner("📝 Generating comprehensive PDF report..."):
                # Prepare data for report
                fcf_results = st.session_state.financial_calculator.fcf_results

                # Prepare FCF plots
                fcf_plots = {}
                if include_fcf:
                    fcf_plots['fcf_comparison'] = (
                        st.session_state.data_processor.create_fcf_comparison_plot(
                            fcf_results, company_name
                        )
                    )
                    fcf_plots['slope_analysis'] = (
                        st.session_state.data_processor.create_slope_analysis_plot(
                            fcf_results, company_name
                        )
                    )

                # Prepare FCF data tables
                growth_analysis_df = None
                fcf_data_df = None

                if include_fcf:
                    # Prepare growth analysis table
                    fcf_data = st.session_state.data_processor.prepare_fcf_data(fcf_results)
                    if fcf_data and 'growth_rates' in fcf_data:
                        # Define consistent FCF types
                        fcf_types = ['LFCF', 'FCFE', 'FCFF', 'Average']
                        growth_data = {'FCF Type': fcf_types}

                        for period in range(1, 10):
                            period_rates = []

                            # Process each FCF type in order
                            for fcf_type in fcf_types:
                                if fcf_type in fcf_data['growth_rates']:
                                    rate = fcf_data['growth_rates'][fcf_type].get(f'{period}yr')
                                    if rate is not None:
                                        period_rates.append(f"{rate:.1%}")
                                    else:
                                        period_rates.append("N/A")
                                else:
                                    period_rates.append("N/A")

                            # Ensure we have exactly 4 items
                            while len(period_rates) < len(fcf_types):
                                period_rates.append("N/A")
                            period_rates = period_rates[: len(fcf_types)]  # Trim if too many

                            growth_data[f'{period}yr'] = period_rates

                        growth_analysis_df = pd.DataFrame(growth_data)

                    # Prepare FCF data table
                    if fcf_data and 'years' in fcf_data and 'padded_fcf_data' in fcf_data:
                        try:
                            years = fcf_data['years']
                            year_count = len(years)

                            fcf_df_data = {'Year': years}

                            # Ensure all FCF data arrays match year count
                            for fcf_type, values in fcf_data['padded_fcf_data'].items():
                                if len(values) == year_count:
                                    fcf_df_data[f'{fcf_type} ({currency_symbol}M)'] = [
                                        f"{v:.1f}" if v is not None else "N/A" for v in values
                                    ]
                                else:
                                    # Pad or trim to match year count
                                    padded_values = (values + [None] * year_count)[:year_count]
                                    fcf_df_data[f'{fcf_type} ({currency_symbol}M)'] = [
                                        f"{v:.1f}" if v is not None else "N/A"
                                        for v in padded_values
                                    ]

                            # Handle average FCF
                            currency_symbol = get_currency_symbol(
                                st.session_state.financial_calculator
                            )
                            avg_fcf = fcf_data.get('average_fcf', [])
                            if len(avg_fcf) == year_count:
                                fcf_df_data[f'Average FCF ({currency_symbol}M)'] = [
                                    f"{v:.1f}" if v is not None else "N/A" for v in avg_fcf
                                ]
                            else:
                                padded_avg = (avg_fcf + [None] * year_count)[:year_count]
                                fcf_df_data[f'Average FCF ({currency_symbol}M)'] = [
                                    f"{v:.1f}" if v is not None else "N/A" for v in padded_avg
                                ]

                            fcf_data_df = pd.DataFrame(fcf_df_data)
                        except Exception as e:
                            logger.warning(f"Error creating FCF data table: {e}")
                            fcf_data_df = None

                # Prepare DCF data
                dcf_results = None
                dcf_assumptions = None
                dcf_plots = {}
                dcf_projections_df = None

                if include_dcf:
                    # Get user DCF assumptions from session state (if available)
                    if (
                        hasattr(st.session_state, 'user_dcf_assumptions')
                        and st.session_state.user_dcf_assumptions
                    ):
                        dcf_assumptions = st.session_state.user_dcf_assumptions
                    else:
                        # Fallback to defaults if user hasn't run DCF analysis yet
                        dcf_assumptions = {
                            'projection_years': 5,
                            'growth_rate_yr1_5': 0.05,
                            'growth_rate_yr5_10': 0.03,
                            'terminal_growth_rate': 0.025,
                            'discount_rate': 0.10,
                            'fcf_type': 'LFCF',
                        }

                    # Calculate DCF with progress indicator
                    with st.spinner("🧮 Generating DCF for report..."):
                        dcf_results = st.session_state.dcf_valuator.calculate_dcf_projections(
                            dcf_assumptions
                        )

                    # Prepare DCF plots
                    dcf_plots['waterfall'] = (
                        st.session_state.data_processor.create_dcf_waterfall_chart(dcf_results)
                    )

                    if include_sensitivity:
                        # Use user's sensitivity parameters if available, otherwise use defaults
                        if (
                            hasattr(st.session_state, 'user_sensitivity_params')
                            and st.session_state.user_sensitivity_params
                        ):
                            dr_min = st.session_state.user_sensitivity_params.get(
                                'discount_rate_min', 0.08
                            )
                            dr_max = st.session_state.user_sensitivity_params.get(
                                'discount_rate_max', 0.15
                            )
                            gr_min = st.session_state.user_sensitivity_params.get(
                                'growth_rate_min', 0.0
                            )
                            gr_max = st.session_state.user_sensitivity_params.get(
                                'growth_rate_max', 0.05
                            )
                        else:
                            # Default ranges
                            dr_min, dr_max = 0.08, 0.15
                            gr_min, gr_max = 0.0, 0.05

                        discount_rates = np.linspace(dr_min, dr_max, 5)
                        growth_rates = np.linspace(gr_min, gr_max, 5)
                        sensitivity_results = st.session_state.dcf_valuator.sensitivity_analysis(
                            discount_rates, growth_rates, dcf_assumptions
                        )
                        if current_price > 0:
                            sensitivity_results['current_price'] = current_price
                        dcf_plots['sensitivity'] = (
                            st.session_state.data_processor.create_sensitivity_heatmap(
                                sensitivity_results
                            )
                        )

                    # Prepare DCF projections table
                    if 'projections' in dcf_results:
                        projections = dcf_results['projections']
                        years = dcf_results.get('years', [])
                        projected_fcf = projections.get('projected_fcf', [])
                        growth_rates = projections.get('growth_rates', [])
                        discount_factors = dcf_results.get('discount_factors', [])
                        pv_fcf = dcf_results.get('pv_fcf', [])

                        # Find the minimum length to ensure all arrays are same size
                        min_length = min(
                            len(years),
                            len(projected_fcf),
                            len(growth_rates),
                            len(discount_factors),
                            len(pv_fcf),
                        )

                        if min_length > 0:
                            dcf_table_data = {
                                'Year': years[:min_length],
                                f'Projected FCF ({currency_symbol}M)': [
                                    f"{fcf:.1f}" for fcf in projected_fcf[:min_length]
                                ],
                                'Growth Rate': [
                                    f"{rate:.1%}" for rate in growth_rates[:min_length]
                                ],
                                'Discount Factor': [
                                    f"{df:.3f}" for df in discount_factors[:min_length]
                                ],
                                f'Present Value ({currency_symbol}M)': [
                                    f"{pv:.1f}" for pv in pv_fcf[:min_length]
                                ],
                            }
                            dcf_projections_df = pd.DataFrame(dcf_table_data)

                # Validate data before report generation
                logger.info("Validating data for report generation...")

                # Debug information
                if growth_analysis_df is not None:
                    logger.info(f"Growth analysis DF shape: {growth_analysis_df.shape}")
                if fcf_data_df is not None:
                    logger.info(f"FCF data DF shape: {fcf_data_df.shape}")
                if dcf_projections_df is not None:
                    logger.info(f"DCF projections DF shape: {dcf_projections_df.shape}")

                # Generate the report
                report_generator = FCFReportGenerator()

                # Use current_price if provided, otherwise use auto-detected price
                final_current_price = (
                    current_price
                    if current_price > 0
                    else (auto_current_price if auto_current_price > 0 else None)
                )

                # Collect actual user sensitivity parameters from session state
                if (
                    hasattr(st.session_state, 'user_sensitivity_params')
                    and st.session_state.user_sensitivity_params
                ):
                    sensitivity_params = st.session_state.user_sensitivity_params
                else:
                    # Fallback to defaults if user hasn't run sensitivity analysis yet
                    sensitivity_params = {
                        'discount_rate_min': 0.08,  # 8%
                        'discount_rate_max': 0.15,  # 15%
                        'growth_rate_min': 0.00,  # 0%
                        'growth_rate_max': 0.05,  # 5%
                        'discount_rate_min_pct': 8.0,
                        'discount_rate_max_pct': 15.0,
                        'growth_rate_min_pct': 0.0,
                        'growth_rate_max_pct': 5.0,
                    }

                # Collect user decisions and rationale based on actual selections
                growth_1_5_pct = dcf_assumptions.get('growth_rate_yr1_5', 0.05) * 100
                growth_6_10_pct = dcf_assumptions.get('growth_rate_yr5_10', 0.03) * 100
                terminal_pct = dcf_assumptions.get('terminal_growth_rate', 0.025) * 100
                discount_pct = dcf_assumptions.get('discount_rate', 0.10) * 100
                fcf_type = dcf_assumptions.get('fcf_type', 'LFCF')
                proj_years = dcf_assumptions.get('projection_years', 5)

                # Build detailed assumptions rationale
                assumptions_detail = f"""
                Selected {fcf_type} methodology for {proj_years}-year projection period.
                Growth assumptions: Years 1-5 at {growth_1_5_pct:.1f}%, Years 6-10 at {growth_6_10_pct:.1f}%, Terminal at {terminal_pct:.1f}%.
                Discount rate (WACC) set at {discount_pct:.1f}% reflecting cost of capital assumptions.
                """

                # Build sensitivity analysis summary
                sens_summary = "Default sensitivity ranges used."
                if (
                    hasattr(st.session_state, 'user_sensitivity_params')
                    and st.session_state.user_sensitivity_params
                ):
                    dr_min_pct = sensitivity_params.get('discount_rate_min_pct', 8.0)
                    dr_max_pct = sensitivity_params.get('discount_rate_max_pct', 15.0)
                    gr_min_pct = sensitivity_params.get('growth_rate_min_pct', 0.0)
                    gr_max_pct = sensitivity_params.get('growth_rate_max_pct', 5.0)
                    sens_summary = f"Custom sensitivity ranges: Discount rate {dr_min_pct:.1f}%-{dr_max_pct:.1f}%, Growth rate {gr_min_pct:.1f}%-{gr_max_pct:.1f}%."

                user_decisions = {
                    'assumptions_rationale': assumptions_detail.strip(),
                    'risk_factors': f"Market volatility, competitive dynamics, economic conditions, and company-specific operational risks. {sens_summary}",
                    'investment_thesis': (
                        f"DCF valuation using {fcf_type} with {proj_years}-year horizon. Growth rates based on historical analysis and forward-looking assumptions. Fair value comparison vs current market price of ${final_current_price:.2f}."
                        if final_current_price
                        else f"DCF valuation using {fcf_type} methodology with {proj_years}-year projection horizon based on selected growth and discount rate assumptions."
                    ),
                }

                pdf_bytes = report_generator.generate_report(
                    company_name=company_name,
                    fcf_results=fcf_results if include_fcf else {},
                    dcf_results=dcf_results if include_dcf else {},
                    dcf_assumptions=dcf_assumptions if include_dcf else {},
                    fcf_plots=fcf_plots,
                    dcf_plots=dcf_plots,
                    growth_analysis_df=growth_analysis_df,
                    fcf_data_df=fcf_data_df,
                    dcf_projections_df=dcf_projections_df,
                    current_price=final_current_price,
                    ticker=ticker if ticker else None,
                    sensitivity_params=sensitivity_params,
                    user_decisions=user_decisions,
                )

                # Generate filename with ticker and date
                from datetime import datetime

                current_date = datetime.now().strftime("%Y%m%d")

                if ticker:
                    # Format: TICKER_FCF_DCF_Report_YYYYMMDD.pdf
                    filename = f"{ticker}_FCF_DCF_Report_{current_date}.pdf"
                else:
                    # Fallback format if no ticker
                    safe_company_name = "".join(
                        c for c in company_name if c.isalnum() or c in (' ', '-', '_')
                    ).rstrip()
                    filename = (
                        f"FCF_DCF_Report_{safe_company_name.replace(' ', '_')}_{current_date}.pdf"
                    )

                # Save to custom download path
                file_saved = False
                try:
                    if custom_download_path and os.path.exists(custom_download_path):
                        full_file_path = os.path.join(custom_download_path, filename)
                        with open(full_file_path, "wb") as f:
                            f.write(pdf_bytes)
                        file_saved = True
                        saved_path = full_file_path
                except Exception as e:
                    logger.warning(f"Could not save file to {custom_download_path}: {e}")

                # Show success message
                st.success("✅ Report generated successfully!")

                # File save status
                if file_saved:
                    st.success(f"💾 Report saved to: `{saved_path}`")
                else:
                    st.warning("⚠️ Could not save to specified path. Use download button below.")

                # Download button
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=filename,
                        mime="application/pdf",
                        type="primary",
                    )

                with col2:
                    if file_saved:
                        if st.button(
                            "📂 Open Folder", help="Open the folder containing the saved report"
                        ):
                            try:
                                # Open the folder in file explorer (cross-platform)
                                import subprocess
                                import platform

                                if platform.system() == "Windows":
                                    subprocess.run(['explorer', '/select,', saved_path], shell=True)
                                elif platform.system() == "Darwin":  # macOS
                                    subprocess.run(["open", "-R", saved_path])
                                else:  # Linux
                                    subprocess.run(["xdg-open", os.path.dirname(saved_path)])
                            except Exception as e:
                                st.error(f"Could not open folder: {e}")

                # Show report stats
                st.info(
                    f"📊 Report includes {len(preview_items)} sections and generated {len(pdf_bytes):,} bytes"
                )

                # Show analysis details used
                if final_current_price:
                    st.info(
                        f"📈 Investment analysis included using ${final_current_price:.2f} share price"
                    )
                if ticker:
                    st.info(f"🏷️ Report generated for {ticker} - {company_name}")

        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
            logger.error(f"Report generation error: {e}")

    # Help section
    with st.expander("ℹ️ About PDF Reports"):
        st.markdown(
            """
        **Report Contents:**
        - **Executive Summary**: Key metrics and valuation overview
        - **FCF Analysis**: Historical trends, growth rates, and comparison charts
        - **DCF Valuation**: Fair value calculation, projections, and sensitivity analysis
        - **Appendix**: Methodology and assumptions used
        
        **Professional Features:**
        - High-quality charts and tables
        - Comprehensive data analysis
        - Professional formatting
        - Detailed methodology explanation
        
        **Use Cases:**
        - Investment analysis documentation
        - Client presentations
        - Internal research reports
        - Academic research
        """
        )


def render_watch_lists():
    """Render the watch lists management interface"""
    st.header("📊 Watch Lists Management")

    # Create sub-tabs for different watch list functions
    watch_tab1, watch_tab2, watch_tab3 = st.tabs(
        ["📋 Manage Lists", "📈 View Analysis", "⚙️ Capture Settings"]
    )

    with watch_tab1:
        render_watch_list_management()

    with watch_tab2:
        render_watch_list_analysis()

    with watch_tab3:
        render_capture_settings()


def render_watch_list_management():
    """Render watch list creation and management"""
    st.subheader("📋 Watch List Management")

    # Create new watch list section
    st.markdown("### Create New Watch List")
    col1, col2 = st.columns([3, 1])

    with col1:
        new_watch_list_name = st.text_input(
            "Watch List Name", placeholder="e.g., Tech Stocks, Value Plays, High Growth"
        )
        new_watch_list_desc = st.text_area(
            "Description (Optional)", placeholder="Brief description of the watch list purpose"
        )

    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("Create Watch List", type="primary"):
            if new_watch_list_name.strip():
                success = st.session_state.watch_list_manager.create_watch_list(
                    new_watch_list_name.strip(), new_watch_list_desc.strip()
                )
                if success:
                    st.success(f"✅ Created watch list: {new_watch_list_name}")
                    st.rerun()
                else:
                    st.error("❌ Watch list with this name already exists")
            else:
                st.error("❌ Please enter a watch list name")

    st.markdown("---")

    # List existing watch lists
    st.markdown("### Existing Watch Lists")
    watch_lists = st.session_state.watch_list_manager.list_watch_lists()

    if not watch_lists:
        st.info("📝 No watch lists created yet. Create your first watch list above!")
    else:
        for watch_list in watch_lists:
            with st.expander(f"📊 {watch_list['name']} ({watch_list['stock_count']} stocks)"):
                st.write(f"**Description:** {watch_list['description'] or 'No description'}")
                st.write(f"**Created:** {watch_list['created_date'][:10]}")
                st.write(f"**Last Updated:** {watch_list['updated_date'][:10]}")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    if st.button(f"📈 View", key=f"view_{watch_list['name']}"):
                        st.session_state.selected_watch_list_for_view = watch_list['name']

                with col2:
                    if st.button(f"📥 Export", key=f"export_{watch_list['name']}"):
                        export_path = st.session_state.watch_list_manager.export_watch_list_to_csv(
                            watch_list['name']
                        )
                        if export_path:
                            st.success(f"✅ Exported to: {export_path}")
                        else:
                            st.error("❌ Export failed")

                with col3:
                    if st.button(f"🎯 Set Active", key=f"active_{watch_list['name']}"):
                        st.session_state.current_watch_list = watch_list['name']
                        analysis_capture.set_current_watch_list(watch_list['name'])
                        st.success(f"✅ Set '{watch_list['name']}' as active for capture")

                with col4:
                    if st.button(f"🗑️ Delete", key=f"delete_{watch_list['name']}", type="secondary"):
                        if st.session_state.get(f"confirm_delete_{watch_list['name']}", False):
                            success = st.session_state.watch_list_manager.delete_watch_list(
                                watch_list['name']
                            )
                            if success:
                                st.success(f"✅ Deleted watch list: {watch_list['name']}")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete watch list")
                        else:
                            st.session_state[f"confirm_delete_{watch_list['name']}"] = True
                            st.warning("⚠️ Click again to confirm deletion")


def render_watch_list_analysis():
    """Render watch list analysis and visualization"""
    st.subheader("📈 Watch List Analysis")

    # Select watch list for analysis
    watch_lists = st.session_state.watch_list_manager.list_watch_lists()

    if not watch_lists:
        st.info("📝 No watch lists available. Create a watch list first!")
        return

    watch_list_names = [wl['name'] for wl in watch_lists]
    selected_watch_list_name = st.selectbox(
        "Select Watch List for Analysis",
        options=watch_list_names,
        index=0 if watch_list_names else None,
    )

    if selected_watch_list_name:
        # Add view options
        col1, col2 = st.columns([3, 1])
        with col1:
            view_mode = st.radio(
                "View Mode:",
                options=["Latest Analysis Only", "All Historical Data"],
                index=0,
                horizontal=True,
                help="Latest Analysis Only shows current valuation per stock. All Historical Data shows every analysis.",
            )

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            show_latest_only = view_mode == "Latest Analysis Only"

        # Get watch list data based on view mode
        watch_list_data = st.session_state.watch_list_manager.get_watch_list(
            selected_watch_list_name, latest_only=show_latest_only
        )

        if not watch_list_data or not watch_list_data['stocks']:
            st.info(
                f"📝 Watch list '{selected_watch_list_name}' is empty. Add some analysis results first!"
            )
            return

        # Performance summary metrics
        st.markdown("### 📊 Performance Summary")
        summary_metrics = watch_list_visualizer.create_performance_summary_metrics(watch_list_data)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Stocks", summary_metrics.get('total_stocks', 0))
        with col2:
            avg_upside = summary_metrics.get('avg_upside', 0)
            st.metric("Avg Upside/Downside", f"{avg_upside:.1f}%")
        with col3:
            undervalued = summary_metrics.get('undervalued_count', 0)
            st.metric(
                "Undervalued",
                undervalued,
                delta=f"{undervalued}/{summary_metrics.get('total_stocks', 1)}",
            )
        with col4:
            overvalued = summary_metrics.get('overvalued_count', 0)
            st.metric(
                "Overvalued",
                overvalued,
                delta=f"{overvalued}/{summary_metrics.get('total_stocks', 1)}",
            )

        # Performance categories
        st.markdown("### 🎯 Investment Categories")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Strong Buy", summary_metrics.get('strong_buy_count', 0), help=">20% upside")
        with col2:
            st.metric("Buy", summary_metrics.get('buy_count', 0), help="10-20% upside")
        with col3:
            st.metric("Hold", summary_metrics.get('hold_count', 0), help="-10% to 10%")
        with col4:
            st.metric("Sell", summary_metrics.get('sell_count', 0), help="-20% to -10%")
        with col5:
            st.metric("Strong Sell", summary_metrics.get('strong_sell_count', 0), help="<-20%")

        # Main upside/downside chart
        st.markdown("### 📊 Upside/Downside Analysis")
        upside_chart = watch_list_visualizer.create_upside_downside_chart(
            watch_list_data, title=f"Watch List: {selected_watch_list_name}"
        )
        st.plotly_chart(upside_chart, use_container_width=True)

        # Performance distribution
        st.markdown("### 📈 Performance Distribution")
        distribution_chart = watch_list_visualizer.create_performance_distribution_chart(
            watch_list_data
        )
        st.plotly_chart(distribution_chart, use_container_width=True)

        # Historical analysis trend (only show if we're not in latest-only mode and have historical data)
        if not show_latest_only and watch_list_data['stocks']:
            st.markdown("### 📊 Historical Analysis Trends")

            # Get unique tickers for selection
            all_tickers = list(set([stock['ticker'] for stock in watch_list_data['stocks']]))

            if len(all_tickers) == 1:
                # If only one ticker, show its trend automatically
                selected_ticker_trend = all_tickers[0]
            else:
                # Let user select ticker for trend analysis
                selected_ticker_trend = st.selectbox(
                    "Select stock for trend analysis:",
                    options=["All Stocks"] + all_tickers,
                    key="trend_ticker_select",
                )

            if selected_ticker_trend == "All Stocks":
                # Show trends for all stocks
                trend_chart = watch_list_visualizer.create_time_series_chart(watch_list_data)
            else:
                # Show trend for selected stock
                trend_chart = watch_list_visualizer.create_time_series_chart(
                    watch_list_data, selected_ticker_trend
                )

            st.plotly_chart(trend_chart, use_container_width=True)

        # Stock Management Section
        st.markdown("### 🔧 Stock Management")

        if watch_list_data['stocks']:
            # Get unique tickers for management operations
            tickers = list(set([stock['ticker'] for stock in watch_list_data['stocks']]))

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("#### 🗑️ Remove Stock")
                selected_ticker_remove = st.selectbox(
                    "Select stock to remove:",
                    options=["Select ticker..."] + tickers,
                    key="remove_ticker_select",
                )

                if selected_ticker_remove and selected_ticker_remove != "Select ticker...":
                    if st.button(f"🗑️ Remove {selected_ticker_remove}", key="remove_stock_btn"):
                        success = st.session_state.watch_list_manager.remove_stock_from_watch_list(
                            selected_watch_list_name, selected_ticker_remove
                        )
                        if success:
                            st.success(f"✅ Removed {selected_ticker_remove} from watch list")
                            st.rerun()
                        else:
                            st.error(f"❌ Failed to remove {selected_ticker_remove}")

            with col2:
                st.markdown("#### 📋 Copy to List")
                selected_ticker_copy = st.selectbox(
                    "Select stock to copy:",
                    options=["Select ticker..."] + tickers,
                    key="copy_ticker_select",
                )

                if selected_ticker_copy and selected_ticker_copy != "Select ticker...":
                    # Get other watch lists
                    all_lists = [
                        wl['name'] for wl in st.session_state.watch_list_manager.list_watch_lists()
                    ]
                    other_lists = [name for name in all_lists if name != selected_watch_list_name]

                    if other_lists:
                        target_list = st.selectbox(
                            "Copy to:",
                            options=["Select target..."] + other_lists,
                            key="copy_target_select",
                        )

                        copy_latest_only = st.checkbox(
                            "Copy latest analysis only",
                            value=True,
                            key="copy_latest_only",
                            help="If unchecked, copies complete history",
                        )

                        if target_list and target_list != "Select target...":
                            if st.button(f"📋 Copy to {target_list}", key="copy_stock_btn"):
                                success = (
                                    st.session_state.watch_list_manager.copy_stock_to_watch_list(
                                        selected_watch_list_name,
                                        target_list,
                                        selected_ticker_copy,
                                        copy_latest_only,
                                    )
                                )
                                if success:
                                    st.success(
                                        f"✅ Copied {selected_ticker_copy} to '{target_list}'"
                                    )
                                else:
                                    st.error(f"❌ Failed to copy {selected_ticker_copy}")
                    else:
                        st.info("No other watch lists available")

            with col3:
                st.markdown("#### 🔄 Move to List")
                selected_ticker_move = st.selectbox(
                    "Select stock to move:",
                    options=["Select ticker..."] + tickers,
                    key="move_ticker_select",
                )

                if selected_ticker_move and selected_ticker_move != "Select ticker...":
                    # Get other watch lists
                    all_lists = [
                        wl['name'] for wl in st.session_state.watch_list_manager.list_watch_lists()
                    ]
                    other_lists = [name for name in all_lists if name != selected_watch_list_name]

                    if other_lists:
                        target_list_move = st.selectbox(
                            "Move to:",
                            options=["Select target..."] + other_lists,
                            key="move_target_select",
                        )

                        move_all_history = st.checkbox(
                            "Move complete history",
                            value=True,
                            key="move_all_history",
                            help="If unchecked, moves only latest analysis",
                        )

                        if target_list_move and target_list_move != "Select target...":
                            if st.button(f"🔄 Move to {target_list_move}", key="move_stock_btn"):
                                success = (
                                    st.session_state.watch_list_manager.move_stock_between_lists(
                                        selected_watch_list_name,
                                        target_list_move,
                                        selected_ticker_move,
                                        move_all_history,
                                    )
                                )
                                if success:
                                    st.success(
                                        f"✅ Moved {selected_ticker_move} to '{target_list_move}'"
                                    )
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to move {selected_ticker_move}")
                    else:
                        st.info("No other watch lists available")

        st.markdown("---")

        # Detailed stock table
        st.markdown("### 📋 Detailed Stock Information")

        # Prepare data for table
        table_data = []
        for stock in watch_list_data['stocks']:
            ticker = stock.get('ticker', 'N/A')

            # If showing latest only, get count of historical analyses
            history_count = ""
            if show_latest_only:
                history_data = st.session_state.watch_list_manager.get_stock_analysis_history(
                    selected_watch_list_name, ticker
                )
                if history_data and history_data['total_records'] > 1:
                    history_count = f" ({history_data['total_records']} analyses)"

            # Get membership info (which lists contain this stock)
            membership = st.session_state.watch_list_manager.get_stock_membership_summary(ticker)
            list_membership = ""
            if membership and membership['total_lists'] > 1:
                list_membership = f" [In {membership['total_lists']} lists]"

            table_data.append(
                {
                    'Ticker': ticker + history_count + list_membership,
                    'Company': stock.get('company_name', 'N/A'),
                    'Current Price': f"${stock.get('current_price', 0):.2f}",
                    'Fair Value': f"${stock.get('fair_value', 0):.2f}",
                    'Upside/Downside': f"{stock.get('upside_downside_pct', 0):.1f}%",
                    'Discount Rate': f"{stock.get('discount_rate', 0):.1f}%",
                    'FCF Type': stock.get('fcf_type', 'N/A'),
                    'Analysis Date': (
                        stock.get('analysis_date', '')[:10] if stock.get('analysis_date') else 'N/A'
                    ),
                }
            )

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)

        # Stock membership details
        if watch_list_data['stocks']:
            with st.expander("🔍 View Stock Membership Details"):
                tickers = list(set([stock['ticker'] for stock in watch_list_data['stocks']]))
                for ticker in tickers:
                    membership = st.session_state.watch_list_manager.get_stock_membership_summary(
                        ticker
                    )
                    if membership and membership['total_lists'] > 0:
                        st.write(f"**{ticker}** is in {membership['total_lists']} watch list(s):")
                        for wl in membership['watch_lists']:
                            st.write(f"  • {wl['name']} ({wl['analysis_count']} analyses)")
                    else:
                        st.write(f"**{ticker}** is only in this watch list")

        # Enhanced download options
        st.markdown("### 📥 Export Options")

        col1, col2, col3 = st.columns(3)

        with col1:
            # Current view download
            csv = df.to_csv(index=False)
            st.download_button(
                label=f"📥 Download Current View",
                data=csv,
                file_name=f"{selected_watch_list_name.replace(' ', '_')}_current.csv",
                mime="text/csv",
                help=f"Downloads {view_mode.lower()} data",
            )

        with col2:
            # Historical data export
            if st.button("📊 Export Full History"):
                export_path = st.session_state.watch_list_manager.export_stock_history_to_csv(
                    selected_watch_list_name
                )
                if export_path:
                    st.success(f"✅ Full history exported to: {export_path}")
                else:
                    st.error("❌ Failed to export history")

        with col3:
            # Individual stock history
            if watch_list_data['stocks']:
                tickers = list(set([stock['ticker'] for stock in watch_list_data['stocks']]))
                selected_ticker = st.selectbox(
                    "Export Single Stock History:",
                    options=["Select ticker..."] + tickers,
                    key="ticker_history_export",
                )

                if selected_ticker and selected_ticker != "Select ticker...":
                    if st.button(f"📈 Export {selected_ticker} History"):
                        export_path = (
                            st.session_state.watch_list_manager.export_stock_history_to_csv(
                                selected_watch_list_name, selected_ticker
                            )
                        )
                        if export_path:
                            st.success(f"✅ {selected_ticker} history exported to: {export_path}")
                        else:
                            st.error(f"❌ Failed to export {selected_ticker} history")


def render_capture_settings():
    """Render analysis capture settings and controls"""
    st.subheader("⚙️ Analysis Capture Settings")

    # Current capture status
    capture_status = analysis_capture.get_capture_status()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Capture Status")

        # Show current status
        if capture_status['capture_enabled']:
            st.success("✅ Analysis capture is ENABLED")
        else:
            st.error("❌ Analysis capture is DISABLED")

        # Show current watch list
        current_wl = capture_status.get('current_watch_list')
        if current_wl:
            st.info(f"📊 Active watch list: **{current_wl}**")
        else:
            st.warning("⚠️ No active watch list set")

        # Enable/Disable controls
        col1a, col1b = st.columns(2)
        with col1a:
            if st.button("✅ Enable Capture"):
                analysis_capture.enable_capture()
                st.rerun()
        with col1b:
            if st.button("❌ Disable Capture"):
                analysis_capture.disable_capture()
                st.rerun()

    with col2:
        st.markdown("### 📋 Watch List Selection")

        available_lists = capture_status.get('available_watch_lists', [])

        if available_lists:
            # Single list selection (primary)
            selected_list = st.selectbox(
                "Select Primary Watch List",
                options=available_lists,
                index=available_lists.index(current_wl) if current_wl in available_lists else 0,
            )

            # Multiple list selection (advanced feature)
            with st.expander("🔄 Advanced: Capture to Multiple Lists"):
                selected_multiple = st.multiselect(
                    "Select multiple watch lists for automatic capture:",
                    options=available_lists,
                    default=[current_wl] if current_wl in available_lists else [],
                    help="New analyses will be captured to all selected lists",
                )

                if selected_multiple:
                    if st.button("🎯 Set Multiple Lists as Active"):
                        analysis_capture.set_multiple_watch_lists(selected_multiple)
                        st.session_state.current_watch_list = selected_multiple[0]  # Primary
                        st.success(
                            f"✅ Set {len(selected_multiple)} watch lists as active: {', '.join(selected_multiple)}"
                        )
                        st.rerun()

            if st.button("🎯 Set as Primary Active"):
                st.session_state.current_watch_list = selected_list
                analysis_capture.set_current_watch_list(selected_list)
                st.success(f"✅ Set '{selected_list}' as primary active watch list")
                st.rerun()
        else:
            st.info("📝 No watch lists available. Create a watch list first!")

    st.markdown("---")

    # Export Directory Configuration Section
    st.markdown("### 📁 Export Directory Settings")

    # Get current export directory
    export_config = get_export_config()
    current_export_dir = get_export_directory()

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Current Export Directory:**")
        if export_config.user_export_directory:
            st.info(f"📁 **User Directory:** {current_export_dir}")
        else:
            st.info(f"📁 **Default Directory:** {current_export_dir}")

        # Directory validation
        export_path = Path(current_export_dir)
        if export_path.exists():
            if export_path.is_dir():
                try:
                    # Test write permissions
                    test_file = export_path / ".write_test"
                    test_file.touch()
                    test_file.unlink()
                    st.success("✅ Directory is writable")
                except:
                    st.error("❌ Directory exists but is not writable")
            else:
                st.error("❌ Path exists but is not a directory")
        else:
            st.warning("⚠️ Directory does not exist (will be created on export)")

    with col2:
        st.markdown("**Actions:**")

        # Directory selection button
        if TKINTER_AVAILABLE:
            if st.button("📂 Choose Directory", help="Select a custom export directory"):
                # Use a callback to handle directory selection
                if 'show_directory_dialog' not in st.session_state:
                    st.session_state.show_directory_dialog = True
                    st.rerun()
        else:
            st.warning("⚠️ Directory selection not available")

        # Reset to default button
        if export_config.user_export_directory:
            if st.button("🔄 Reset to Default", help="Reset to default exports directory"):
                set_user_export_directory(None)
                st.success("✅ Reset to default directory")
                st.rerun()

    # Handle directory selection dialog
    if st.session_state.get('show_directory_dialog', False):
        try:
            # Hide the main window
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            # Show directory dialog
            selected_dir = askdirectory(
                title="Select Export Directory", initialdir=current_export_dir
            )

            if selected_dir:
                set_user_export_directory(selected_dir)
                st.success(f"✅ Export directory updated to: {selected_dir}")

            root.destroy()
        except Exception as e:
            st.error(f"❌ Error selecting directory: {e}")
        finally:
            st.session_state.show_directory_dialog = False
            st.rerun()

    # Manual text input as alternative
    with st.expander("✏️ Manual Directory Input"):
        manual_dir = st.text_input(
            "Enter directory path:",
            value=current_export_dir,
            help="Enter the full path to your desired export directory",
        )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("💾 Save Manual Path"):
                if manual_dir and manual_dir.strip():
                    path_obj = Path(manual_dir.strip())
                    try:
                        # Validate the path
                        if path_obj.is_absolute():
                            set_user_export_directory(str(path_obj))
                            st.success(f"✅ Export directory set to: {path_obj}")
                            st.rerun()
                        else:
                            st.error("❌ Please provide an absolute path")
                    except Exception as e:
                        st.error(f"❌ Invalid path: {e}")
                else:
                    st.error("❌ Please enter a directory path")

        with col_b:
            if st.button("📁 Create Directory", help="Create directory if it doesn't exist"):
                if manual_dir and manual_dir.strip():
                    path_obj = Path(manual_dir.strip())
                    try:
                        path_obj.mkdir(parents=True, exist_ok=True)
                        set_user_export_directory(str(path_obj))
                        st.success(f"✅ Directory created and set: {path_obj}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to create directory: {e}")

    st.markdown("---")

    # Manual capture section
    st.markdown("### 📥 Manual Analysis Capture")
    st.info(
        "💡 **Tip:** When you run any analysis (DCF, DDM, or P/B) with capture enabled, results will be automatically saved to the active watch list."
    )

    # Check for available analysis results
    available_analyses = []
    if hasattr(st.session_state, 'dcf_results') and st.session_state.dcf_results:
        available_analyses.append(('DCF', 'dcf_results', '💰'))
    if hasattr(st.session_state, 'ddm_results') and st.session_state.ddm_results:
        available_analyses.append(('DDM', 'ddm_results', '🏆'))
    if hasattr(st.session_state, 'pb_analysis') and st.session_state.pb_analysis:
        available_analyses.append(('P/B', 'pb_analysis', '📊'))

    if available_analyses and current_wl:
        st.markdown("**📊 Available Analysis Results:**")

        # Get ticker and company info
        ticker = "UNKNOWN"
        company_name = ""

        if (
            hasattr(st.session_state, 'financial_calculator')
            and st.session_state.financial_calculator
        ):
            ticker = st.session_state.financial_calculator.ticker_symbol or "UNKNOWN"
            company_name = st.session_state.financial_calculator.company_name or ""

        st.write(f"**Ticker:** {ticker}")
        st.write(f"**Company:** {company_name}")
        st.write(f"**Target Watch List:** {current_wl}")

        # Show available analyses
        st.markdown("**Analysis Types Ready for Capture:**")
        for analysis_type, session_key, emoji in available_analyses:
            st.write(f"{emoji} {analysis_type} Analysis")

        # Create capture buttons for each available analysis
        cols = st.columns(len(available_analyses))

        for idx, (analysis_type, session_key, emoji) in enumerate(available_analyses):
            with cols[idx]:
                if st.button(f"💾 Capture {analysis_type}", key=f"capture_{analysis_type.lower()}"):
                    analysis_results = getattr(st.session_state, session_key)

                    if analysis_type == "DCF":
                        success = analysis_capture.capture_dcf_analysis(
                            ticker=ticker, company_name=company_name, dcf_results=analysis_results
                        )
                    elif analysis_type == "DDM":
                        success = analysis_capture.capture_ddm_analysis(
                            ticker=ticker, company_name=company_name, ddm_results=analysis_results
                        )
                    elif analysis_type == "P/B":
                        success = analysis_capture.capture_pb_analysis(
                            ticker=ticker, company_name=company_name, pb_results=analysis_results
                        )

                    if success:
                        st.success(
                            f"✅ Successfully captured {analysis_type} analysis for {ticker}"
                        )
                    else:
                        st.error(f"❌ Failed to capture {analysis_type} analysis")

        # Capture all button
        if len(available_analyses) > 1:
            st.markdown("---")
            if st.button("💾 Capture All Available Analyses", key="capture_all"):
                success_count = 0
                total_count = len(available_analyses)

                for analysis_type, session_key, emoji in available_analyses:
                    analysis_results = getattr(st.session_state, session_key)

                    if analysis_type == "DCF":
                        success = analysis_capture.capture_dcf_analysis(
                            ticker=ticker, company_name=company_name, dcf_results=analysis_results
                        )
                    elif analysis_type == "DDM":
                        success = analysis_capture.capture_ddm_analysis(
                            ticker=ticker, company_name=company_name, ddm_results=analysis_results
                        )
                    elif analysis_type == "P/B":
                        success = analysis_capture.capture_pb_analysis(
                            ticker=ticker, company_name=company_name, pb_results=analysis_results
                        )

                    if success:
                        success_count += 1

                if success_count == total_count:
                    st.success(f"✅ Successfully captured all {total_count} analyses for {ticker}")
                elif success_count > 0:
                    st.warning(f"⚠️ Captured {success_count}/{total_count} analyses for {ticker}")
                else:
                    st.error(f"❌ Failed to capture any analyses for {ticker}")

    else:
        if not current_wl:
            st.warning("⚠️ Set an active watch list first")
        else:
            st.info("📊 Run a valuation analysis (DCF, DDM, or P/B) to see capture options")


def main():
    """
    Main application function with centralized data input system.

    The application now uses a centralized data input approach where:
    1. User sets global data source preferences in the sidebar
    2. All tabs (FCF, DCF, DDM, P/B) use the same data loading logic
    3. Data source selection is consistent across all analysis types
    4. Users can choose between Excel-first, API-first, or auto modes
    """
    initialize_session_state()
    render_sidebar()

    # Main content area - show tabs if we have data from either folder mode OR ticker mode
    if not st.session_state.company_folder and not st.session_state.financial_calculator:
        render_welcome()
    else:
        # Create tabs for FCF and DCF analysis
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
            [
                "📈 FCF Analysis",
                "💰 DCF Valuation",
                "🏆 DDM Valuation",
                "📊 P/B Analysis",
                "📄 Generate Report",
                "📊 Watch Lists",
                "📚 Help & Guide",
            ]
        )

        with tab1:
            render_fcf_analysis()

        with tab2:
            render_dcf_analysis()

        with tab3:
            render_ddm_analysis()

        with tab4:
            render_pb_analysis()

        with tab5:
            render_report_generation()

        with tab6:
            render_watch_lists()

        with tab7:
            render_help_guide()


def render_help_guide():
    """Render the comprehensive help guide and user documentation"""
    st.header("📚 Comprehensive User Guide")

    # Create a sidebar navigation for the guide sections
    guide_sections = [
        "🚀 Quick Start",
        "🌍 Multi-Market Support",
        "📊 FCF Analysis",
        "💰 DCF Valuation",
        "🏆 DDM Valuation",
        "📊 P/B Analysis",
        "📊 Watch Lists",
        "📁 Data Structure",
        "🔧 LTM Integration",
        "🏗️ System Architecture",
        "📈 Mathematical Formulas",
        "⚙️ Configuration",
        "🐛 Troubleshooting",
    ]

    selected_section = st.selectbox("Select Help Section:", guide_sections)

    if selected_section == "🚀 Quick Start":
        render_quick_start_guide()
    elif selected_section == "🌍 Multi-Market Support":
        render_multi_market_support_guide()
    elif selected_section == "📊 FCF Analysis":
        render_fcf_analysis_guide()
    elif selected_section == "💰 DCF Valuation":
        render_dcf_valuation_guide()
    elif selected_section == "🏆 DDM Valuation":
        render_ddm_valuation_guide()
    elif selected_section == "📊 P/B Analysis":
        render_pb_analysis_guide()
    elif selected_section == "📊 Watch Lists":
        render_watch_lists_guide()
    elif selected_section == "📁 Data Structure":
        render_data_structure_guide()
    elif selected_section == "🔧 LTM Integration":
        render_ltm_integration_guide()
    elif selected_section == "🏗️ System Architecture":
        render_system_architecture_guide()
    elif selected_section == "📈 Mathematical Formulas":
        render_mathematical_formulas_guide()
    elif selected_section == "⚙️ Configuration":
        render_configuration_guide()
    elif selected_section == "🐛 Troubleshooting":
        render_troubleshooting_guide()


def render_quick_start_guide():
    """Render the quick start guide"""
    st.subheader("🚀 Quick Start Guide")

    st.markdown(
        """
    ### Welcome to the FCF Analysis Tool!
    
    This application provides comprehensive **Free Cash Flow (FCF) analysis**, **Discounted Cash Flow (DCF) valuation**, 
    **Dividend Discount Model (DDM)**, and **Price-to-Book (P/B) analysis** capabilities 
    for both **US Market** and **TASE (Tel Aviv Stock Exchange)** stocks.
    
    #### Getting Started in 4 Steps:
    
    1. **🌍 Select Market**
       - Choose **US Market** for American stocks (NASDAQ, NYSE, etc.)
       - Choose **TASE (Tel Aviv)** for Israeli stocks
       - The app automatically handles ticker formatting and currency
    
    2. **📁 Prepare Your Data**
       - Create a company folder (e.g., `AAPL` for Apple or `TEVA` for Teva)
       - Add `FY/` subfolder with 10-year historical financial statements
       - Add `LTM/` subfolder with latest 12-month data
    
    3. **🔍 Select Company Folder**
       - Use the sidebar to select your company folder
       - The app will automatically detect and validate your data
       - Ticker will be auto-processed based on your market selection
    
    4. **📊 Analyze & Track Results**
       - Navigate to FCF Analysis tab for historical trends
       - Use DCF Valuation tab for fair value calculations
       - Try DDM Valuation for dividend-paying stocks
       - Analyze P/B ratios for industry comparisons
       - Create Watch Lists to track multiple companies over time
       - Generate professional reports in the Reports tab
    
    #### Key Features:
    - ✅ **Multi-Market Support**: US stocks and TASE stocks with automatic currency handling
    - ✅ **Smart Ticker Processing**: Automatic .TA suffix handling for TASE stocks
    - ✅ **Three FCF Methods**: FCFF, FCFE, LFCF calculations
    - ✅ **Interactive Charts**: Plotly-powered visualizations
    - ✅ **DCF Modeling**: Complete valuation with sensitivity analysis
    - ✅ **DDM Valuation**: Dividend Discount Model for dividend-paying stocks
    - ✅ **P/B Analysis**: Price-to-Book ratio analysis with industry benchmarks
    - ✅ **Watch Lists**: Track portfolio performance with automatic capture
    - ✅ **Currency Awareness**: USD for US stocks, ILS/Agorot for TASE stocks
    - ✅ **Data Validation**: Quality checks and error reporting
    - ✅ **PDF Reports**: Professional analysis outputs
    
    #### Market-Specific Examples:
    
    **US Market Examples:**
    - `AAPL` (Apple Inc.) → Ticker: `AAPL`, Currency: USD
    - `MSFT` (Microsoft) → Ticker: `MSFT`, Currency: USD
    - `GOOGL` (Alphabet) → Ticker: `GOOGL`, Currency: USD
    
    **TASE Market Examples:**
    - `TEVA` (Teva Pharmaceutical) → Ticker: `TEVA.TA`, Currency: ILS/Agorot
    - `ICL` (ICL Group) → Ticker: `ICL.TA`, Currency: ILS/Agorot
    - `ELBIT` (Elbit Systems) → Ticker: `ELBIT.TA`, Currency: ILS/Agorot
    """
    )

    st.info(
        "💡 **Pro Tip**: The market selection automatically handles ticker formatting - just enter the base ticker (e.g., 'TEVA') and the app will add '.TA' for TASE stocks!"
    )

    st.success(
        """
    🆕 **NEW: Watch Lists Feature**
    
    Track multiple companies and analyze portfolio performance over time:
    - **Automatic Capture**: DCF results saved to watch lists automatically
    - **Performance Charts**: Visual upside/downside analysis with reference lines
    - **Historical Tracking**: Complete audit trail of all valuations
    - **Export Options**: CSV exports for current view and historical data
    
    Get started: Go to the **📊 Watch Lists** tab to create your first list!
    """
    )


def render_multi_market_support_guide():
    """Render the multi-market support guide"""
    st.subheader("🌍 Multi-Market Support Guide")

    st.markdown(
        """
    ### Overview
    
    The FCF Analysis Tool supports comprehensive analysis for stocks from multiple exchanges:
    - **🇺🇸 US Market**: NASDAQ, NYSE, and other American stock exchanges
    - **🇮🇱 TASE (Tel Aviv)**: Tel Aviv Stock Exchange for Israeli companies
    
    ### Market Selection Interface
    
    #### Location
    The **Market Selection** feature is located at the top of the left sidebar, above the data source section.
    
    #### Options
    - **US Market**: Select for American companies (Apple, Microsoft, Google, etc.)
    - **TASE (Tel Aviv)**: Select for Israeli companies (Teva, ICL, Elbit, etc.)
    
    ### Ticker Symbol Processing
    
    #### US Market Behavior
    ```
    User Input → System Processing → Final Ticker
    "AAPL"     → No change        → "AAPL"
    "MSFT"     → No change        → "MSFT" 
    "TEVA.TA"  → Remove .TA       → "TEVA"
    ```
    
    #### TASE Market Behavior  
    ```
    User Input → System Processing → Final Ticker
    "TEVA"     → Add .TA suffix   → "TEVA.TA"
    "ICL"      → Add .TA suffix   → "ICL.TA"
    "ELBIT.TA" → Keep as-is       → "ELBIT.TA"
    ```
    
    ### Currency Handling
    
    #### US Market Currencies
    - **Stock Prices**: Displayed in US Dollars ($)
    - **Financial Data**: Expected in millions USD ($M)
    - **DCF Results**: Enterprise/Equity values in $M
    - **Reports**: All values formatted in USD
    
    #### TASE Market Currencies
    - **Stock Prices**: Displayed in Agorot (ILA) with Shekel (₪) equivalent
    - **Financial Data**: Expected in millions ILS (₪M)  
    - **DCF Results**: Enterprise/Equity values in ₪M
    - **Reports**: Mixed format - prices in ILA, financials in ₪M
    - **Conversion**: 1 Shekel (₪) = 100 Agorot (ILA)
    
    ### Market-Specific Examples
    
    #### US Market Analysis Example
    
    **Company**: Apple Inc. (AAPL)
    ```
    1. Select "US Market" from radio buttons
    2. Load AAPL company folder with FY/LTM data
    3. System detects ticker as "AAPL" 
    4. Market data fetched from yfinance as "AAPL"
    5. Current price: $150.25 USD
    6. Financial data: Revenue $365,000M USD
    7. DCF Fair Value: $145.50 USD per share
    ```
    
    #### TASE Market Analysis Example
    
    **Company**: Teva Pharmaceutical (TEVA)
    ```
    1. Select "TASE (Tel Aviv)" from radio buttons  
    2. Load TEVA company folder with FY/LTM data
    3. System processes ticker: "TEVA" → "TEVA.TA"
    4. Market data fetched from yfinance as "TEVA.TA"
    5. Current price: 4,250 ILA (≈ 42.50 ₪)
    6. Financial data: Revenue ₪58,000M ILS 
    7. DCF Fair Value: 4,100 ILA (≈ 41.00 ₪) per share
    ```
    
    ### Multi-Market Workflow
    
    #### Step-by-Step Process
    
    1. **🌍 Market Selection**
       - Choose appropriate market before loading data
       - Market selection affects all subsequent processing
    
    2. **📁 Data Preparation**
       - Ensure financial data uses consistent currency
       - US: Financial statements in USD millions
       - TASE: Financial statements in ILS millions
    
    3. **🎯 Ticker Processing**
       - System automatically formats ticker for selected market
       - Visual feedback shows ticker transformation if applicable
    
    4. **📊 Analysis**
       - All calculations respect market-specific currency conventions
       - Charts and metrics display appropriate currency symbols
    
    5. **📄 Reporting**
       - Reports generated with market-appropriate formatting
       - Currency labels adjust based on market selection
    
    ### Advanced Features
    
    #### Automatic Market Detection
    Even with market selection, the system includes intelligent fallback:
    - Auto-detects TASE stocks if ticker ends with .TA
    - Recognizes currency metadata from yfinance
    - Provides manual override capabilities
    
    #### Mixed Analysis Support
    - Analyze different companies by changing market selection
    - System maintains separate configurations per analysis
    - Clear visual indicators for current market setting
    
    ### Best Practices
    
    #### For US Market Analysis
    - ✅ Use standard US ticker symbols (no .TA suffix)
    - ✅ Ensure financial data is in USD millions
    - ✅ Verify market data connections to US exchanges
    - ✅ Use standard US DCF assumptions and growth rates
    
    #### For TASE Market Analysis  
    - ✅ Select TASE market before loading company data
    - ✅ Use base ticker without .TA (system adds automatically)
    - ✅ Ensure financial data is in ILS millions
    - ✅ Consider Israeli market-specific growth assumptions
    - ✅ Account for currency volatility in projections
    
    ### Troubleshooting Multi-Market Issues
    
    #### Common Problems
    1. **Wrong Currency Display**: Check market selection setting
    2. **Ticker Not Found**: Verify correct market is selected  
    3. **Mixed Currency Data**: Ensure consistent market selection throughout
    4. **Price Format Issues**: Use refresh market data button
    
    #### Quick Solutions
    - Always select market before loading company data
    - Use manual ticker entry if auto-detection fails
    - Check yfinance availability for specific tickers
    - Validate financial data currency consistency
    """
    )


def render_fcf_analysis_guide():
    """Render the FCF analysis guide"""
    st.subheader("📊 Free Cash Flow Analysis Guide")

    st.markdown(
        """
    ### Understanding the Three FCF Methods
    
    #### 1. 🏢 Free Cash Flow to Firm (FCFF)
    **What it measures:** Cash available to ALL capital providers (equity and debt holders)
    
    **Formula:**
    ```
    FCFF = EBIT × (1 - Tax Rate) + Depreciation - Working Capital Change - CapEx
    ```
    
    **Key Characteristics:**
    - ✅ **Pre-financing**: Ignores capital structure decisions
    - ✅ **Enterprise Focus**: Values the entire business operations
    - ✅ **M&A Analysis**: Perfect for acquisition scenarios
    
    #### 2. 👥 Free Cash Flow to Equity (FCFE)
    **What it measures:** Cash available specifically to EQUITY HOLDERS
    
    **Formula:**
    ```
    FCFE = Net Income + Depreciation - Working Capital Change - CapEx + Net Borrowing
    ```
    
    **Key Characteristics:**
    - ✅ **Post-financing**: Accounts for debt payments and borrowings
    - ✅ **Equity Focus**: Values only the equity portion
    - ✅ **Dividend Capacity**: Shows potential for distributions
    
    #### 3. ⚡ Levered Free Cash Flow (LFCF)
    **What it measures:** Simplified cash flow after capital investments
    
    **Formula:**
    ```
    LFCF = Operating Cash Flow - Capital Expenditures
    ```
    
    **Key Characteristics:**
    - ✅ **Simplicity**: Easy to calculate and understand
    - ✅ **Operational Focus**: Direct from cash flow statement
    - ✅ **Quick Assessment**: Rapid liquidity evaluation
    
    ### Interpreting Results
    
    #### Strong Business Pattern:
    ```
    FCFF: $1,000M → $1,200M → $1,400M
    FCFE: $800M → $900M → $1,000M  
    LFCF: $600M → $700M → $800M
    ```
    **Interpretation:** Excellent business generating increasing cash across all measures
    
    #### Multi-Method Analysis Framework:
    1. **Start with LFCF**: Quick operational assessment
    2. **Analyze FCFF**: Understand business fundamentals  
    3. **Examine FCFE**: Evaluate equity investor returns
    4. **Compare All Three**: Identify financing impact
    """
    )


def render_dcf_valuation_guide():
    """Render the DCF valuation guide"""
    st.subheader("💰 DCF Valuation Guide")

    st.markdown(
        """
    ### Complete DCF Valuation Process
    
    #### Step-by-Step DCF Calculation:
    
    **Step 1: Base FCF Determination**
    - Uses the most recent Free Cash Flow to Firm (FCFF) value
    - Falls back to $100M if no historical data available
    
    **Step 2: Growth Rate Assumptions**
    - **Years 1-5**: 3-year historical growth rate (or user input)
    - **Years 5-10**: 5-year historical growth rate (or user input)  
    - **Terminal Growth**: Default 3% perpetual growth rate
    
    **Step 3: 10-Year FCF Projections**
    ```
    FCF(year) = Previous FCF × (1 + Growth Rate)
    ```
    
    **Step 4: Terminal Value (Gordon Growth Model)**
    ```
    Terminal Value = FCF₁₁ / (Discount Rate - Terminal Growth Rate)
    ```
    
    **Step 5: Present Value Calculations**
    ```
    PV of FCF = FCF(t) / (1 + Discount Rate)^t
    PV of Terminal Value = Terminal Value / (1 + Discount Rate)^10
    ```
    
    **Step 6: Enterprise Value**
    ```
    Enterprise Value = Sum of all PV of FCF + PV of Terminal Value
    ```
    
    **Step 7: Equity Value**
    ```
    Equity Value = Enterprise Value - Net Debt
    ```
    
    **Step 8: Fair Value Per Share**
    ```
    Fair Value Per Share = Equity Value × 1,000,000 / Shares Outstanding
    ```
    
    ### Default Assumptions
    - **Discount Rate**: 10% (required rate of return)
    - **Terminal Growth Rate**: 2.5% (perpetual growth)
    - **Projection Years**: 5-10 years explicit forecast
    
    ### Sensitivity Analysis
    Test different scenarios across:
    - **Discount rates** (typically 8% to 14%)
    - **Terminal growth rates** (typically 1% to 4%)
    
    Results show upside/downside percentages relative to current market price.
    """
    )


def render_ddm_valuation_guide():
    """Render the DDM (Dividend Discount Model) valuation guide"""
    st.subheader("🏆 DDM Valuation Guide")

    st.markdown(
        """
    ### Dividend Discount Model (DDM) Analysis
    
    The DDM valuation model is specifically designed for **dividend-paying stocks**, using dividend payments 
    to determine intrinsic value based on the present value of expected future dividends.
    
    #### When to Use DDM:
    - ✅ **Dividend-Paying Stocks**: Companies with consistent dividend payment history
    - ✅ **Mature Companies**: Stable businesses with predictable dividend policies
    - ✅ **Utility Stocks**: REITs, utilities, and other income-focused companies
    - ✅ **Blue-Chip Stocks**: Large-cap companies with established dividend track records
    
    #### DDM Model Variants:
    
    **🔵 Gordon Growth Model (Single-Stage)**
    - **Best for**: Mature companies with stable dividend growth
    - **Formula**: `Value = D₁ / (r - g)`
    - **Where**: D₁ = Next year's dividend, r = Required return, g = Growth rate
    - **Auto-Selected**: When dividend growth is stable (CV < 0.3)
    
    **🟡 Two-Stage DDM**
    - **Best for**: Companies transitioning from high to stable growth
    - **Calculation**: High growth period + Stable growth period
    - **Auto-Selected**: When moderate growth volatility is detected
    
    **🔴 Multi-Stage DDM**
    - **Best for**: Complex growth scenarios with multiple phases
    - **Calculation**: Multiple distinct growth periods + Terminal value
    - **Auto-Selected**: When high growth volatility or complex patterns exist
    
    #### Step-by-Step DDM Process:
    
    **Step 1: Dividend Data Extraction**
    - Fetches historical dividend data from multiple sources
    - Aggregates quarterly dividends to annual figures
    - Validates data quality and consistency
    
    **Step 2: Dividend Analysis**
    - Calculates historical dividend growth rates (1Y, 3Y, 5Y CAGR)
    - Estimates dividend payout ratio from earnings data
    - Assesses dividend payment consistency and sustainability
    
    **Step 3: Model Selection**
    - Analyzes dividend growth pattern volatility
    - Selects optimal DDM variant based on historical data
    - Can be manually overridden if desired
    
    **Step 4: Growth Assumptions**
    - **Stage 1 Growth**: High growth period (default: 8% for 5 years)
    - **Stage 2 Growth**: Transitional growth (default: 4% for 5 years)
    - **Terminal Growth**: Long-term sustainable rate (default: 2.5%)
    
    **Step 5: Dividend Projections**
    ```
    Projected Dividend = Current Dividend × (1 + Growth Rate)^Year
    ```
    
    **Step 6: Present Value Calculation**
    ```
    PV of Dividend = Dividend(t) / (1 + Discount Rate)^t
    ```
    
    **Step 7: Terminal Value (if applicable)**
    ```
    Terminal Value = Final Dividend × (1 + Terminal Growth) / (Discount Rate - Terminal Growth)
    ```
    
    **Step 8: Intrinsic Value**
    ```
    DDM Value = Sum of PV of All Projected Dividends + PV of Terminal Value
    ```
    
    ### Default Assumptions:
    - **Discount Rate**: 10% (cost of equity)
    - **Stage 1 Growth**: 8% (first 5 years)
    - **Stage 2 Growth**: 4% (years 5-10)
    - **Terminal Growth**: 2.5% (perpetual)
    - **Model Type**: Auto-selection based on data
    
    ### DDM Results Include:
    - **Intrinsic Value**: Calculated fair value per share
    - **Current Dividend**: Most recent annual dividend
    - **Dividend Yield**: Current yield vs market price
    - **Payout Ratio**: Estimated dividend payout ratio
    - **Growth Metrics**: Historical and projected growth rates
    - **Model Validation**: Data quality and model selection rationale
    
    ### Important Limitations:
    - ⚠️ **Dividend Dependency**: Only works for dividend-paying companies
    - ⚠️ **Growth Sensitivity**: Highly sensitive to growth rate assumptions
    - ⚠️ **Model Selection**: Automatic selection may not always be optimal
    - ⚠️ **Market Conditions**: May not capture short-term market dynamics
    
    ### Best Practices:
    - 💡 Compare with other valuation methods (DCF, P/B)
    - 💡 Analyze dividend sustainability and coverage ratios
    - 💡 Consider industry and economic cycles
    - 💡 Use sensitivity analysis to test different scenarios
    """
    )


def render_pb_analysis_guide():
    """Render the P/B (Price-to-Book) analysis guide"""
    st.subheader("📊 P/B Analysis Guide")

    st.markdown(
        """
    ### Price-to-Book (P/B) Ratio Analysis
    
    P/B analysis evaluates whether a stock is **undervalued or overvalued** relative to its book value,
    providing insights into market perception versus fundamental asset value.
    
    #### When P/B Analysis is Most Useful:
    - ✅ **Asset-Heavy Companies**: Banks, real estate, manufacturing, utilities
    - ✅ **Value Investing**: Screening for potentially undervalued stocks
    - ✅ **Financial Institutions**: Banks and insurance companies with significant assets
    - ✅ **Distressed Analysis**: Companies trading below book value
    - ✅ **Industry Comparison**: Relative valuation within sectors
    
    #### P/B Ratio Fundamentals:
    
    **Basic Formula:**
    ```
    P/B Ratio = Market Price per Share / Book Value per Share
    ```
    
    **Book Value per Share Calculation:**
    ```
    BVPS = Shareholders' Equity / Shares Outstanding
    ```
    
    **Where Shareholders' Equity =**
    ```
    Total Assets - Total Liabilities - Preferred Equity
    ```
    
    #### P/B Analysis Components:
    
    **📊 Current P/B Assessment**
    - Real-time P/B ratio calculation
    - Book value per share from latest financial statements
    - Market capitalization validation
    
    **🏭 Industry Benchmarking**
    - Sector-specific P/B ratio comparisons
    - Percentile ranking within industry
    - Position assessment (undervalued/fair/overvalued)
    
    **📈 Historical Analysis**
    - 5-year P/B ratio trend analysis
    - Historical percentile ranking
    - Trend direction and volatility assessment
    
    **💰 Valuation Assessment**
    - Fair value estimates using industry medians
    - Upside/downside potential calculation
    - Conservative and optimistic scenarios
    
    #### Industry P/B Benchmarks:
    
    **Technology Sector**
    - Median P/B: 3.5 (Range: 1.5 - 8.0)
    - High P/B due to intellectual property and growth expectations
    
    **Financial Services**
    - Median P/B: 1.2 (Range: 0.8 - 2.0)
    - Lower P/B reflecting asset-heavy business models
    
    **Healthcare**
    - Median P/B: 2.8 (Range: 1.2 - 6.0)
    - Moderate P/B with premium for R&D and patents
    
    **Utilities**
    - Median P/B: 1.8 (Range: 1.0 - 2.5)
    - Stable P/B ratios, regulated asset-intensive operations
    
    **Energy**
    - Median P/B: 1.5 (Range: 0.5 - 3.0)
    - Cyclical P/B ratios influenced by commodity prices
    
    #### P/B Ratio Interpretation:
    
    **P/B < 1.0: Trading Below Book Value**
    - Potentially undervalued OR distressed company
    - May indicate market skepticism about asset values
    - Could signal value opportunity or fundamental problems
    
    **P/B 1.0 - 3.0: Typical Range**
    - Normal valuation for most industries
    - Market confidence in business fundamentals
    - Industry context crucial for interpretation
    
    **P/B > 3.0: Premium Valuation**
    - High growth expectations or significant intangible assets
    - Strong brand value, patents, or market position
    - Technology and growth companies often trade here
    
    #### Step-by-Step P/B Analysis:
    
    **Step 1: Data Collection**
    - Extract shareholders' equity from balance sheet
    - Obtain current market price and shares outstanding
    - Validate data consistency across sources
    
    **Step 2: Book Value Calculation**
    - Calculate book value per share (BVPS)
    - Quality assessment of book value components
    - Adjust for preferred equity if applicable
    
    **Step 3: P/B Ratio Calculation**
    - Current P/B = Market Price / BVPS
    - Validate against multiple data sources
    
    **Step 4: Industry Analysis**
    - Determine appropriate industry classification
    - Compare against sector benchmarks
    - Calculate percentile ranking
    
    **Step 5: Historical Context**
    - Analyze 5-year P/B trend
    - Calculate historical statistics
    - Assess current position vs history
    
    **Step 6: Valuation Assessment**
    - Estimate fair value using industry metrics
    - Calculate upside/downside potential
    - Generate investment thesis
    
    ### P/B Analysis Results Include:
    - **Current P/B Ratio**: Real-time valuation metric
    - **Book Value per Share**: Fundamental asset value
    - **Industry Comparison**: Sector benchmarking and ranking
    - **Historical Trends**: 5-year P/B analysis with statistics
    - **Fair Value Estimates**: Multiple valuation scenarios
    - **Risk Assessment**: Book value quality and market factors
    
    ### Important Considerations:
    - ⚠️ **Asset Quality**: Book value may not reflect fair market value
    - ⚠️ **Intangible Assets**: Often undervalued in book value calculations
    - ⚠️ **Industry Context**: P/B norms vary significantly by sector
    - ⚠️ **Accounting Policies**: Different standards affect book value
    - ⚠️ **Market Cycles**: P/B ratios can be cyclical within industries
    
    ### Best Practices:
    - 💡 Use alongside other valuation methods (DCF, DDM)
    - 💡 Consider asset turnover and ROE relationships
    - 💡 Analyze trends rather than point-in-time ratios
    - 💡 Understand company's asset composition and quality
    - 💡 Account for industry and economic cycles
    """
    )


def render_data_structure_guide():
    """Render the data structure guide"""
    st.subheader("📁 Data Structure Requirements")

    st.markdown(
        """
    ### Expected File Structure
    
    ```
    <TICKER>/
    ├── FY/                           # 10-year historical data
    │   ├── <Company> - Income Statement.xlsx
    │   ├── <Company> - Balance Sheet.xlsx
    │   └── <Company> - Cash Flow Statement.xlsx
    └── LTM/                          # Latest 12 months data
        ├── <Company> - Income Statement.xlsx
        ├── <Company> - Balance Sheet.xlsx
        └── <Company> - Cash Flow Statement.xlsx
    ```
    
    ### File Naming Conventions
    Files must contain specific keywords for automatic categorization:
    - Files with **"Balance"** → Balance Sheet
    - Files with **"Cash"** → Cash Flow Statement  
    - Files with **"Income"** → Income Statement
    
    ### Excel Format Requirements
    - **Investing.com Export Format**: Native support for Investing.com Excel exports
    - **Fiscal Year Columns**: Must contain header row with FY-9, FY-8, etc.
    - **Metric Names**: Standard financial statement metric names in column 2
    - **Data Format**: Numeric values in millions, supports comma formatting
    
    ### Sample Companies Available
    - **GOOG/** - Alphabet Inc Class C
    - **COMPANY1/** - Example Corporation A
    - **COMPANY2/** - Example Corporation B
    - **COMPANY3/** - Example Corporation C
    - **V/** - Visa Inc Class A
    
    ### Data Coverage Requirements
    - **Minimum Coverage**: At least 3 years for meaningful trend analysis
    - **Optimal Coverage**: 10 years for comprehensive historical analysis
    - **LTM Integration**: Latest twelve months data for current performance
    - **Missing Data Handling**: System gracefully handles incomplete datasets
    """
    )


def render_ltm_integration_guide():
    """Render the LTM integration guide"""
    st.subheader("🔧 LTM (Latest Twelve Months) Integration")

    st.markdown(
        """
    ### LTM Role in Financial Analysis
    
    **Purpose**: LTM provides the most recent 12-month financial performance data to complement historical FY data, ensuring DCF valuations reflect current reality rather than outdated annual reports.
    
    **Integration Strategy**: The system uses an **"FY Historical + LTM Latest"** approach where historical trends from FY data are combined with the most recent LTM data point.
    
    ### How LTM Works
    
    #### Data Combination Logic:
    ```python
    # Integration process
    combined_values = fy_values[:-1] + [ltm_values[-1]]
    ```
    
    This replaces the most recent FY data point with the latest LTM value, creating a seamless blend of historical context and current performance.
    
    ### Business Value
    
    - **⏰ Timeliness**: Reduces lag between analysis and actual company performance
    - **🎯 Accuracy**: FCF projections based on recent performance rather than outdated annual data
    - **📈 Market Relevance**: Valuations align with current company performance trends
    
    ### Implementation Details
    
    #### Data Processing:
    1. **FY Data**: Provides 10-year historical context
    2. **LTM Data**: Provides 3-year recent quarterly/annual data
    3. **Integration**: Latest LTM value replaces most recent FY value
    4. **Fallback**: If LTM unavailable, system uses FY-only data
    
    #### Example Timeline:
    ```
    FY Dates:  YYYY-12-31, YYYY-12-31, ..., YYYY-12-31 (10-year range)
    LTM Dates: YYYY-MM-DD, YYYY-MM-DD, ..., YYYY-MM-DD (recent quarters)
    Combined:  YYYY-12-31, YYYY-12-31, ..., YYYY-MM-DD (most recent)
    ```
    
    ### Key Benefits
    - **Current Performance**: Uses most recent 12-month data
    - **Historical Context**: Maintains long-term trend analysis
    - **Seamless Integration**: Automatic blending of FY and LTM data
    - **Quality Assurance**: Comprehensive validation and error handling
    """
    )


def render_system_architecture_guide():
    """Render the system architecture guide"""
    st.subheader("🏗️ System Architecture")

    st.markdown(
        """
    ### Application Hierarchy Tree Map
    
    ```
    Financial Analysis Application
    │
    ├── 🚀 APPLICATION LAYER (Entry Points)
    │   ├── CopyDataNew.py .......................... Excel data extraction & DCF template population
    │   ├── fcf_analysis_streamlit.py ............... Modern web-based FCF analysis interface
    │   ├── run_streamlit_app.py .................... Application launcher with requirements checking
    │   └── run_fcf_streamlit.bat ................... Windows batch launcher
    │
    ├── 🧮 CORE ANALYSIS LAYER (Financial Engines)
    │   ├── financial_calculations.py .............. Financial calculations engine (FCF, growth rates)
    │   ├── dcf_valuation.py ....................... DCF valuation engine (projections, terminal value)
    │   ├── fcf_consolidated.py .................... Consolidated FCF calculations
    │   └── data_validator.py ...................... Comprehensive data validation framework
    │
    ├── 🔧 DATA PROCESSING LAYER (Data Operations)
    │   ├── data_processing.py ..................... Data processing & Plotly visualization functions
    │   ├── centralized_data_manager.py ............ Centralized data management
    │   ├── centralized_data_processor.py .......... Centralized data processing
    │   ├── centralized_integration.py ............. Integration utilities
    │   └── excel_utils.py ......................... Dynamic Excel data extraction utilities
    │
    ├── ⚙️ UTILITY LAYER (Support & Configuration)
    │   ├── config.py .............................. Centralized configuration system
    │   ├── error_handler.py ....................... Enhanced error handling and logging
    │   ├── report_generator.py .................... PDF report generation using ReportLab
    │   └── requirements.txt ....................... Python dependencies
    │
    ├── 📊 DATA LAYER (Company Analysis Structure)
    │   ├── <TICKER>/ .............................. Company-specific data folders
    │   │   ├── FY/ ................................ 10-year historical financial data
    │   │   └── LTM/ ............................... Latest 12 months financial data
    │   ├── GOOG/ .................................. Alphabet Inc Class C sample data
    │   ├── COMPANY1/ ............................. Example Corporation A sample data
    │   ├── COMPANY2/ ............................. Example Corporation B sample data
    │   ├── COMPANY3/ ............................. Example Corporation C sample data
    │   └── V/ ..................................... Visa Inc Class A sample data
    │
    └── 🧪 TESTING LAYER (Quality Assurance)
        ├── test_comprehensive.py .................. Comprehensive system testing
        ├── test_centralized_system.py ............. Centralized system testing
        ├── test_integration.py .................... Integration testing
        └── test_*.py .............................. Additional specialized tests
    ```
    
    ### Data Flow Architecture
    
    ```
    📂 Excel Files → 🔄 Data Loading → 📊 Metric Extraction → 🧮 FCF Calculation → 💰 DCF Valuation → 📈 Visualization
          ↓               ↓                 ↓                    ↓                 ↓                ↓
       FY + LTM    →   config.py    →   excel_utils.py  →  financial_calc.py →  dcf_valuation.py → data_processing.py
       Structure   →   Configuration →   Dynamic Extract →   FCFF/FCFE/LFCF  →   Fair Value    →   Plotly Charts
    ```
    
    ### Key Technical Features
    - **Modular Design**: Clean separation of concerns for maintainability
    - **Vectorized Operations**: NumPy arrays for performance
    - **Comprehensive Caching**: Intelligent result storage
    - **Error Recovery**: Graceful degradation with partial results
    - **Multi-format Support**: Excel, CSV, Parquet compatibility
    """
    )


def render_mathematical_formulas_guide():
    """Render the mathematical formulas guide"""
    st.subheader("📈 Mathematical Formulas")

    st.markdown(
        """
    ### Core FCF Formulas
    
    #### Free Cash Flow to Firm (FCFF)
    ```
    FCFF = EBIT × (1 - Tax Rate) + Depreciation & Amortization - ΔWorking Capital - Capital Expenditures
    ```
    
    **Component Calculations:**
    - **After-Tax EBIT**: `EBIT × (1 - Tax Rate)`
    - **Working Capital Change**: `(Current Assets - Current Liabilities)ᵢ - (Current Assets - Current Liabilities)ᵢ₋₁`
    - **Tax Rate**: `min(|Income Tax Expense| / |Earnings Before Tax|, 0.35)`
    
    #### Free Cash Flow to Equity (FCFE)
    ```
    FCFE = Net Income + Depreciation & Amortization - ΔWorking Capital - Capital Expenditures + Net Borrowing
    ```
    
    #### Levered Free Cash Flow (LFCF)
    ```
    LFCF = Cash from Operations - Capital Expenditures
    ```
    
    ### DCF Valuation Mathematics
    
    #### Present Value of FCF Projections
    ```
    PV(FCFᵢ) = FCFᵢ / (1 + r)ᵢ
    ```
    
    #### Terminal Value (Gordon Growth Model)
    ```
    Terminal Value = FCF₁₀ × (1 + g) / (r - g)
    ```
    
    #### Enterprise and Equity Value
    ```
    Enterprise Value = Σ PV(FCFᵢ) + PV(Terminal Value)
    Equity Value = Enterprise Value - Net Debt
    Value per Share = Equity Value / Shares Outstanding
    ```
    
    ### DDM (Dividend Discount Model) Mathematics
    
    #### Gordon Growth Model (Single-Stage)
    ```
    Value = D₁ / (r - g)
    ```
    **Where:**
    - `D₁` = Next year's expected dividend
    - `r` = Required rate of return (discount rate)
    - `g` = Constant dividend growth rate
    
    #### Two-Stage DDM
    ```
    Value = Σ[Dᵢ / (1 + r)ᵢ] + [D₍ₙ₊₁₎ / (r - g₂)] / (1 + r)ⁿ
    ```
    **Where:**
    - `Stage 1`: High growth period (years 1 to n)
    - `Stage 2`: Stable growth period (beyond year n)
    - `g₂` = Terminal growth rate
    
    #### Dividend Growth Rate
    ```
    Dividend Growth Rate = (Dividend_current / Dividend_past)^(1/years) - 1
    ```
    
    #### Payout Ratio Estimation
    ```
    Payout Ratio = Total Dividends / Net Income
    ```
    
    ### P/B (Price-to-Book) Analysis Mathematics
    
    #### Basic P/B Ratio
    ```
    P/B Ratio = Market Price per Share / Book Value per Share
    ```
    
    #### Book Value per Share
    ```
    BVPS = (Total Shareholders' Equity - Preferred Equity) / Shares Outstanding
    ```
    
    #### Industry Percentile Ranking
    ```
    Percentile = (Number of companies with lower P/B / Total companies) × 100
    ```
    
    #### Fair Value Estimation (P/B Method)
    ```
    Fair Value = Book Value per Share × Industry Median P/B
    ```
    
    #### Upside/Downside Calculation
    ```
    Upside/Downside = (Fair Value - Current Price) / Current Price × 100%
    ```
    
    ### Growth Rate Calculations
    
    #### Annualized Growth Rate
    ```
    Growth Rate = (|End Value| / |Start Value|)^(1/n) - 1
    ```
    
    #### Multi-Period Analysis
    - **1-Year Growth**: `(FCF₂₀₂₄ / FCF₂₀₂₃) - 1`
    - **3-Year Growth**: `(FCF₂₀₂₄ / FCF₂₀₂₁)^(1/3) - 1`
    - **5-Year Growth**: `(FCF₂₀₂₄ / FCF₂₀₁₉)^(1/5) - 1`
    - **10-Year Growth**: `(FCF₂₀₂₄ / FCF₂₀₁₄)^(1/10) - 1`
    
    ### Validation Rules
    
    #### Calculation Bounds
    ```python
    MIN_TAX_RATE = 0.0
    MAX_TAX_RATE = 0.35
    DEFAULT_TAX_RATE = 0.25
    
    MIN_GROWTH_RATE = -0.99  # -99%
    MAX_GROWTH_RATE = 5.0    # 500%
    
    MIN_DISCOUNT_RATE = 0.01     # 1%
    MAX_DISCOUNT_RATE = 0.50     # 50%
    ```
    """
    )


def render_configuration_guide():
    """Render the configuration guide"""
    st.subheader("⚙️ Configuration & Settings")

    st.markdown(
        """
    ### Market Selection Configuration
    
    #### Market Selection Interface
    The application provides a **Market Selection** radio button interface in the left sidebar:
    
    - **US Market**: For American stocks (NASDAQ, NYSE, etc.)
    - **TASE (Tel Aviv)**: For Israeli stocks on Tel Aviv Stock Exchange
    
    #### Ticker Processing Rules
    
    **US Market Selected:**
    ```python
    # Ticker processing for US Market
    "AAPL" → "AAPL"           # No change for US tickers  
    "TEVA.TA" → "TEVA"        # Removes .TA suffix if present
    "MSFT" → "MSFT"           # Standard US ticker format
    ```
    
    **TASE Market Selected:**
    ```python
    # Ticker processing for TASE Market
    "TEVA" → "TEVA.TA"        # Adds .TA suffix for TASE
    "ICL.TA" → "ICL.TA"       # Keeps .TA suffix if already present
    "ELBIT" → "ELBIT.TA"      # Auto-formats for TASE
    ```
    
    #### Currency Handling Configuration
    
    **US Market Configuration:**
    ```python
    us_market_config = {
        'currency': 'USD',                    # US Dollars
        'financial_currency': 'USD',          # Financial statements in USD
        'is_tase_stock': False,              # Not a TASE stock
        'price_display': '$XX.XX',           # Dollar format
        'financial_display': '$XXXm'         # Millions USD format
    }
    ```
    
    **TASE Market Configuration:**
    ```python
    tase_market_config = {
        'currency': 'ILS',                    # Israeli Shekels
        'financial_currency': 'ILS',          # Financial statements in ILS
        'is_tase_stock': True,               # TASE stock flag
        'price_display': 'XXX ILA (≈ X.XX ₪)', # Agorot with Shekel equivalent
        'financial_display': '₪XXXm'         # Millions ILS format
    }
    ```
    
    ### System Configuration
    
    #### Default DCF Assumptions
    ```python
    default_assumptions = {
        'discount_rate': 0.10,           # 10% required rate of return
        'terminal_growth_rate': 0.025,   # 2.5% perpetual growth
        'growth_rate_yr1_5': 0.05,       # 5% early years growth
        'growth_rate_yr5_10': 0.03,      # 3% later years growth
        'projection_years': 5,           # 5-year explicit forecast period
        'terminal_method': 'perpetual_growth'
    }
    ```
    
    #### Excel Configuration
    ```python
    excel_config = {
        'data_start_column': 4,     # Column D for FY data
        'ltm_column': 15,           # Column O for LTM data
        'max_scan_rows': 59,        # Maximum rows to scan
        'company_name_locations': [(2, 3), (1, 3), (3, 3)]  # Multiple search locations
    }
    ```
    
    ### Core Dependencies
    ```
    openpyxl>=3.0.0      # Excel file manipulation
    pandas>=1.3.0        # Data analysis and manipulation  
    numpy>=1.20.0        # Numerical computing
    scipy>=1.7.0         # Scientific computing
    yfinance>=0.2.0      # Yahoo Finance API
    streamlit>=1.28.0    # Web-based UI framework
    plotly>=5.15.0       # Interactive visualizations
    reportlab>=4.0.0     # PDF report generation
    ```
    
    ### Environment Configuration
    
    #### Performance Settings
    - **Chart DPI**: 300 for high-quality exports
    - **Memory Management**: Automatic cleanup of large datasets
    - **Caching**: Intelligent result storage for faster repeated calculations
    
    #### File Handling
    - **Excel Engine**: openpyxl for .xlsx files
    - **CSV Support**: pandas for alternative data formats
    - **Error Recovery**: Graceful handling of corrupted files
    
    ### Customization Options
    
    #### DCF Assumptions
    - Modify discount rates via the DCF Valuation tab
    - Adjust growth rate assumptions in real-time
    - Customize projection periods (5-10 years)
    
    #### Visualization Settings
    - Chart themes and colors
    - Export formats (PNG, SVG, PDF)
    - Interactive features (zoom, hover, download)
    
    #### Data Processing
    - Custom metric extraction patterns
    - Alternative file naming conventions
    - Flexible data validation rules
    """
    )


def render_troubleshooting_guide():
    """Render the troubleshooting guide"""
    st.subheader("🐛 Troubleshooting Guide")

    st.markdown(
        """
    ### Common Issues and Solutions
    
    #### 📁 Data Loading Problems
    
    **Issue**: "Excel file not found" or "Invalid file format"
    
    **Solutions**:
    - ✅ Verify file paths are correct
    - ✅ Ensure files are in .xlsx format
    - ✅ Check folder structure matches requirements
    - ✅ Verify FY/ and LTM/ subfolders exist
    
    **Issue**: "Metric not found in financial data"
    
    **Solutions**:
    - ✅ Verify Excel files contain standard metric names
    - ✅ Check for typos in financial statement headers
    - ✅ Ensure data is in expected columns (D for FY, O for LTM)
    - ✅ Use Investing.com export format
    
    #### 🧮 Calculation Errors
    
    **Issue**: "FCF values seem incorrect"
    
    **Solutions**:
    - ✅ Verify input data quality in source Excel files
    - ✅ Check for missing balance sheet data
    - ✅ Review working capital calculation methodology
    - ✅ Compare with manual calculations for validation
    
    **Issue**: "Negative or unrealistic FCF values"
    
    **Solutions**:
    - ✅ Check for data entry errors in source files
    - ✅ Verify correct sign conventions in financial statements
    - ✅ Review one-time items affecting cash flow
    - ✅ Consider industry-specific adjustments
    
    #### 🌍 Market Selection Issues
    
    **Issue**: "Ticker not found" or "Invalid ticker symbol"
    
    **Solutions**:
    - ✅ **Check Market Selection**: Ensure correct market is selected (US vs TASE)
    - ✅ **Verify Ticker Format**: 
      - US Market: Use base ticker without .TA (e.g., "AAPL", "MSFT")  
      - TASE Market: Use base ticker without .TA (e.g., "TEVA", "ICL") - app adds .TA automatically
    - ✅ **Try Manual Entry**: Use the manual ticker input if auto-detection fails
    - ✅ **Check Ticker Availability**: Verify ticker exists on yfinance for the selected market
    
    **Issue**: "Wrong currency display" or "Incorrect price format"
    
    **Solutions**:
    - ✅ **Verify Market Selection**: US Market should show USD ($), TASE should show ILS/Agorot (₪)
    - ✅ **Refresh Market Data**: Use the "🔄 Refresh Market Data" button in sidebar
    - ✅ **Check Data Source**: Ensure yfinance has correct currency metadata for the stock
    - ✅ **Manual Correction**: Override values in report generation if needed
    
    **Issue**: "Market data fetch failed" for TASE stocks
    
    **Solutions**:
    - ✅ **Use Correct TASE Format**: Ensure ticker ends with .TA (auto-handled by market selection)
    - ✅ **Check Connection**: Verify internet connection to Yahoo Finance
    - ✅ **Try Alternative Tickers**: Some TASE stocks may have different ticker formats
    - ✅ **Manual Price Entry**: Use override function in report generation
    
    **Issue**: "DCF calculation errors" with mixed currencies
    
    **Solutions**:
    - ✅ **Consistent Market Selection**: Ensure same market selected throughout analysis
    - ✅ **Check Financial Data Currency**: Verify Excel files use consistent currency
    - ✅ **Review Currency Assumptions**: TASE stocks expect financial data in millions ILS
    - ✅ **Validate Conversion Factors**: Check Agorot/Shekel conversions (1 ILS = 100 ILA)
    
    #### 🚀 Application Performance
    
    **Issue**: "Slow loading or processing"
    
    **Solutions**:
    - ✅ Check available system memory
    - ✅ Reduce dataset size if needed
    - ✅ Close other resource-intensive applications
    - ✅ Clear browser cache for Streamlit apps
    
    **Issue**: "Charts not displaying correctly"
    
    **Solutions**:
    - ✅ Clear browser cache and cookies
    - ✅ Update web browser to latest version
    - ✅ Check internet connection for web fonts
    - ✅ Try different chart export formats
    
    ### Error Codes Reference
    
    #### Data Validation Errors
    - **DV001**: Missing required folder structure
    - **DV002**: Invalid file format or corruption
    - **DV003**: Insufficient historical data
    - **DV004**: Metric extraction failure
    
    #### Calculation Errors
    - **CE001**: Division by zero in growth rate calculation
    - **CE002**: Invalid tax rate calculation
    - **CE003**: Array length mismatch
    - **CE004**: DCF assumption validation failure
    
    ### Getting Help
    
    #### Diagnostic Steps
    1. **Check Data Quality**: Use the data validation features
    2. **Review Logs**: Check application logs for specific errors
    3. **Test with Sample Data**: Use included sample company folders
    4. **Verify File Structure**: Ensure proper FY/LTM organization
    
    #### Best Practices
    - Always backup original Excel files before processing
    - Use consistent file naming conventions
    - Validate data quality before analysis
    - Keep historical data for trend analysis
    - Regular system updates and maintenance
    
    ### Support Resources
    - **Sample Data**: Use included company folders for testing
    - **Documentation**: Reference this comprehensive guide
    - **Validation Reports**: Use built-in data quality checks
    - **Logs**: Check application logs for detailed error information
    """
    )


def render_watch_lists_guide():
    """Render comprehensive watch lists documentation"""
    st.markdown(
        """
    ## 📊 Watch Lists - Complete Guide
    
    Watch Lists provide a powerful way to track and analyze DCF valuations across multiple companies over time. 
    This feature automatically captures analysis results and provides comprehensive visualization and export capabilities.
    
    ---
    
    ### 🎯 **Key Features Overview**
    
    #### 📋 **Multi-List Management**
    - Create unlimited watch lists for different investment themes
    - Organize stocks by sector, strategy, or any custom criteria
    - Track description and creation dates for each list
    
    #### 🔄 **Automatic Analysis Capture**
    - DCF results automatically saved when analysis capture is enabled
    - Complete audit trail of all valuations over time
    - No manual data entry required
    
    #### 📈 **Advanced Visualization**
    - Interactive upside/downside bar charts with performance indicators
    - Performance distribution histograms
    - Historical trend analysis for individual stocks
    - Color-coded performance categories
    
    #### 📥 **Flexible Export Options**
    - Current view export (latest analysis per stock)
    - Complete historical data export (all analyses)
    - Individual stock history export
    - Multiple CSV format options
    
    ---
    
    ### 🚀 **Getting Started**
    
    #### Step 1: Create Your First Watch List
    1. Navigate to the **📊 Watch Lists** tab
    2. Go to **📋 Manage Lists** sub-tab
    3. Enter a descriptive name (e.g., "Tech Growth Stocks", "Value Plays", "High Dividend")
    4. Add an optional description
    5. Click **Create Watch List**
    
    #### Step 2: Enable Analysis Capture
    1. Go to **⚙️ Capture Settings** sub-tab
    2. Select your newly created watch list as active
    3. Click **✅ Enable Capture**
    4. Your watch list is now ready to automatically capture DCF analyses
    
    #### Step 3: Run DCF Analyses
    1. Perform DCF analyses as usual in the **💰 DCF Valuation** tab
    2. Results are automatically captured to your active watch list
    3. Each new analysis for the same stock updates the current valuation
    4. Historical data is preserved in the database
    
    ---
    
    ### 📊 **Understanding View Modes**
    
    #### 🎯 **Latest Analysis Only** (Default)
    - Shows the most recent valuation for each stock
    - Perfect for current portfolio decision-making
    - Eliminates duplicate entries in charts and tables
    - **Best for**: Daily monitoring, quick performance overview
    
    #### 📚 **All Historical Data**
    - Shows every analysis ever captured for all stocks
    - Reveals valuation changes over time
    - Enables trend analysis and historical comparison
    - **Best for**: Research, tracking valuation evolution
    
    ---
    
    ### 📈 **Visualization Features**
    
    #### 🎨 **Performance Bar Chart**
    - **Green bars**: Undervalued stocks (positive upside)
    - **Red bars**: Overvalued stocks (negative upside)
    - **Reference lines**: -20%, -10%, 0%, +10%, +20% thresholds
    - **Hover details**: Complete stock information on mouseover
    
    #### 📊 **Investment Categories**
    - **Strong Buy**: >20% upside potential
    - **Buy**: 10-20% upside potential  
    - **Hold**: -10% to +10% (fairly valued)
    - **Sell**: -10% to -20% downside
    - **Strong Sell**: >20% overvalued
    
    #### 📈 **Historical Trends** (Historical View Only)
    - Time series charts showing valuation changes
    - Individual stock trend analysis
    - Multi-stock comparison capabilities
    - Trend identification for timing decisions
    
    ---
    
    ### 💾 **Export Capabilities**
    
    #### 📥 **Current View Export**
    ```
    Exports: Latest analysis for each stock
    Format: CSV with current valuations
    Use case: Share current portfolio positions
    ```
    
    #### 📊 **Full History Export**  
    ```
    Exports: Complete analysis history for all stocks
    Format: CSV with timestamps and evolution
    Use case: Research, backtesting, audit trails
    ```
    
    #### 📈 **Individual Stock History**
    ```
    Exports: Complete timeline for selected stock
    Format: CSV with all historical analyses
    Use case: Deep dive into specific stock valuation changes
    ```
    
    ---
    
    ### ⚙️ **Advanced Features**
    
    #### 🔄 **Analysis Replacement Logic**
    - New DCF analysis for existing stock **replaces** it in graphical view
    - Original analysis **preserved** in database for historical reference
    - Ticker column shows analysis count: "AAPL (3 analyses)" 
    - Switch to "All Historical Data" to see complete timeline
    
    #### 📊 **Performance Metrics**
    - **Total Stocks**: Number of unique stocks in watch list
    - **Average Upside/Downside**: Mean performance across portfolio
    - **Undervalued/Overvalued Counts**: Distribution of opportunities
    - **Category Breakdown**: Strong Buy/Buy/Hold/Sell/Strong Sell counts
    
    #### 🎯 **Multi-List Strategy**
    ```
    Example Organization:
    • "High Growth Tech" - Growth stocks with >15% revenue growth
    • "Dividend Aristocrats" - Stable dividend payers
    • "Value Opportunities" - Low P/E with strong fundamentals  
    • "International Exposure" - Non-US market stocks
    • "Watchlist - Research" - Stocks under investigation
    ```
    
    ---
    
    ### 🛠️ **Best Practices**
    
    #### 📋 **List Organization**
    - Use descriptive, specific names for watch lists
    - Create separate lists for different investment strategies
    - Regularly review and update list descriptions
    - Delete unused lists to maintain organization
    
    #### 🔄 **Analysis Workflow**
    1. Set active watch list before starting analysis sessions
    2. Enable capture to automatically save results
    3. Review captured data in "Latest Analysis Only" mode
    4. Use "All Historical Data" for research and trends
    5. Export data regularly for backup and sharing
    
    #### 📊 **Performance Review**
    - Weekly: Check performance summary metrics
    - Monthly: Review category distributions and rebalance
    - Quarterly: Analyze historical trends for timing patterns
    - Annually: Export full history for tax and reporting purposes
    
    ---
    
    ### 🚨 **Important Notes**
    
    #### 💾 **Data Persistence**
    - All data stored in local SQLite database (`data/watch_lists.db`)
    - JSON backup maintained (`data/watch_lists.json`)
    - Data survives application restarts and updates
    - Regular backups recommended for important data
    
    #### 🔒 **Data Privacy**
    - All data stored locally on your machine
    - No cloud synchronization or external sharing
    - Complete control over your analysis data
    - Export functionality for manual backup/sharing
    
    #### ⚡ **Performance Considerations**
    - Optimized SQL queries for fast data retrieval
    - Efficient storage of large historical datasets
    - Responsive interface even with 100+ stocks per list
    - Automatic indexing for ticker and date searches
    
    ---
    
    ### 🆘 **Troubleshooting**
    
    #### ❌ **Analysis Not Capturing**
    1. Verify watch list is set as active in Capture Settings
    2. Ensure analysis capture is enabled (green status)
    3. Complete DCF analysis fully before expecting capture
    4. Check that company folder is properly loaded
    
    #### 📊 **Charts Not Displaying**
    1. Verify watch list contains analysis data
    2. Try switching between Latest/Historical view modes
    3. Refresh browser if using web interface
    4. Check for JavaScript errors in browser console
    
    #### 📥 **Export Issues**
    1. Ensure `exports/` directory has write permissions
    2. Check available disk space for CSV files
    3. Try individual stock export if full export fails
    4. Verify watch list contains data before exporting
    
    ---
    
    ### 💡 **Pro Tips**
    
    #### 🎯 **Efficient Workflow**
    - Create watch lists **before** starting analysis sessions
    - Use keyboard shortcuts for faster navigation between tabs
    - Keep capture enabled for consistent data collection
    - Review performance metrics regularly for portfolio insights
    
    #### 📊 **Advanced Analysis**
    - Compare multiple watch lists for sector analysis
    - Use historical view to identify seasonal patterns
    - Export data to Excel for additional calculations
    - Track changes in discount rates and assumptions over time
    
    #### 🔄 **Maintenance**
    - Periodically clean up test or experimental watch lists
    - Update watch list descriptions as strategies evolve
    - Export historical data before major application updates
    - Monitor database size and export old data if needed
    
    ---
    
    *The Watch Lists feature transforms the FCF Analysis Tool from a single-company calculator into a comprehensive portfolio management and analysis platform. Start with one watch list and expand your system as your investment process grows!*
    """
    )


if __name__ == "__main__":
    main()
