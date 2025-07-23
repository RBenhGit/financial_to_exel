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

# Import our custom modules
from financial_calculations import FinancialCalculator
from dcf_valuation import DCFValuator
from data_processing import DataProcessor
from report_generator import FCFReportGenerator
from fcf_consolidated import FCFCalculator, calculate_fcf_growth_rates
from config import (get_default_company_name, get_unknown_company_name, 
                   get_unknown_fcf_type, get_unknown_ticker)
from watch_list_manager import WatchListManager
from analysis_capture import analysis_capture
from watch_list_visualizer import watch_list_visualizer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="FCF Analysis Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
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
""", unsafe_allow_html=True)

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
    if 'fcf_results' not in st.session_state:
        st.session_state.fcf_results = {}
    if 'dcf_results' not in st.session_state:
        st.session_state.dcf_results = {}
    if 'watch_list_manager' not in st.session_state:
        st.session_state.watch_list_manager = WatchListManager()
    if 'current_watch_list' not in st.session_state:
        st.session_state.current_watch_list = None

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
        help="Choose the stock exchange for ticker symbol processing"
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
    
    # Show some examples to help users
    st.sidebar.markdown("**Expected folder structure:**")
    st.sidebar.code("""
<COMPANY>/
├── FY/
│   ├── Income Statement.xlsx
│   ├── Balance Sheet.xlsx  
│   └── Cash Flow Statement.xlsx
└── LTM/
    ├── Income Statement.xlsx
    ├── Balance Sheet.xlsx
    └── Cash Flow Statement.xlsx
    """)
    
    # Option 1: Enter path manually
    st.sidebar.markdown("**Enter Company Folder Path:**")
    company_path = st.sidebar.text_input(
        "Company Folder Path",
        value=st.session_state.get('company_folder', ''),
        help="Path to folder containing FY and LTM subfolders",
        placeholder="e.g., C:\\data\\COMPANY or .\\SYMBOL"
    )
    
    # Data loading section
    
    if st.sidebar.button("Load Company Data", type="primary"):
        if company_path and os.path.exists(company_path):
            st.sidebar.info(f"🔍 Validating folder: {company_path}")
            validation = st.session_state.data_processor.validate_company_folder(company_path)
            
            if validation['is_valid']:
                st.sidebar.success("✅ Folder structure valid")
                st.session_state.company_folder = company_path
                
                # Use improved calculator for better Excel parsing
                with st.spinner("🔍 Analyzing company data..."):
                    st.session_state.financial_calculator = FinancialCalculator(company_path)
                    st.session_state.dcf_valuator = DCFValuator(st.session_state.financial_calculator)
                    
                    # Apply market selection to ticker processing
                    if st.session_state.financial_calculator.ticker_symbol:
                        original_ticker = st.session_state.financial_calculator.ticker_symbol
                        processed_ticker = _apply_market_selection_to_ticker(original_ticker, market_selection)
                        
                        if processed_ticker != original_ticker:
                            st.session_state.financial_calculator.ticker_symbol = processed_ticker
                            st.sidebar.info(f"🎯 Auto-detected ticker: {original_ticker} → {processed_ticker} ({market_selection})")
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
                        st.session_state.fcf_results = st.session_state.financial_calculator.calculate_all_fcf_types()
                        
                        # Show what was loaded
                        if st.session_state.fcf_results:
                            loaded_types = [fcf_type for fcf_type, values in st.session_state.fcf_results.items() if values]
                            if loaded_types:
                                st.sidebar.success(f"✅ Loaded FCF types: {', '.join(loaded_types)}")
                                
                                # Show market data status
                                if st.session_state.financial_calculator.current_stock_price:
                                    st.sidebar.success(f"✅ Market data: ${st.session_state.financial_calculator.current_stock_price:.2f}")
                                elif st.session_state.financial_calculator.ticker_symbol:
                                    st.sidebar.warning(f"⚠️ Ticker detected ({st.session_state.financial_calculator.ticker_symbol}) but price fetch failed")
                            else:
                                st.sidebar.warning("⚠️ No FCF data calculated - check financial statements")
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
    
    # Display current company info
    if st.session_state.company_folder:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📈 Current Company")
        company_name = os.path.basename(st.session_state.company_folder)
        st.sidebar.info(f"**Company:** {company_name}")
        
        # Display Auto-Extracted Market Data
        st.sidebar.markdown("**Market Data:**")
        if st.session_state.financial_calculator and st.session_state.financial_calculator.ticker_symbol:
            ticker = st.session_state.financial_calculator.ticker_symbol
            current_price = st.session_state.financial_calculator.current_stock_price
            shares_outstanding = getattr(st.session_state.financial_calculator, 'shares_outstanding', 0)
            
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
                    st.sidebar.info(f"💰 **Current Price**: {price_agorot:.0f} ILA (≈ {price_shekels:.2f} {currency_symbol})")
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
                help=f"Enter ticker for {selected_market} (format will be auto-adjusted)"
            )
            
            if manual_ticker and st.session_state.financial_calculator:
                if st.sidebar.button("📊 Fetch Market Data"):
                    # Apply market selection to manual ticker
                    processed_ticker = _apply_market_selection_to_ticker(manual_ticker.upper(), selected_market)
                    
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
                        
                        market_data = st.session_state.financial_calculator.fetch_market_data(processed_ticker)
                        if market_data:
                            st.sidebar.success(f"✅ Fetched data for {processed_ticker}")
                            if processed_ticker != manual_ticker.upper():
                                st.sidebar.info(f"Applied {selected_market} format: {manual_ticker.upper()} → {processed_ticker}")
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
                    currency_symbol = get_currency_symbol_financial(st.session_state.financial_calculator)
                    st.sidebar.write(f"**{fcf_type} (Latest):** {currency_symbol}{latest_fcf:.1f}M")

def render_welcome():
    """Render welcome page when no data is loaded"""
    st.title("📊 Modern FCF Analysis Tool")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
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
        """)
    
    with col2:
        st.markdown("""
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
        """)
    
    # Watch Lists feature highlight
    st.markdown("---")
    st.subheader("🆕 NEW: Watch Lists Feature")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 📋 **Portfolio Tracking**
        - Create multiple watch lists
        - Organize by strategy or sector
        - Automatic analysis capture
        """)
    
    with col2:
        st.markdown("""
        #### 📊 **Performance Analysis**
        - Visual upside/downside charts
        - Investment category breakdowns
        - Historical trend analysis
        """)
    
    with col3:
        st.markdown("""
        #### 📥 **Export Options**
        - Current view CSV export
        - Complete historical data
        - Individual stock timelines
        """)
    
    st.info("💡 **Get Started**: Create your first watch list in the **📊 Watch Lists** tab after loading company data!")
    
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
    
    # Display Company Information below header
    folder_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_unknown_company_name()
    ticker = st.session_state.financial_calculator.ticker_symbol if st.session_state.financial_calculator else None
    current_price = st.session_state.financial_calculator.current_stock_price if st.session_state.financial_calculator else None
    
    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = getattr(st.session_state.financial_calculator, 'company_name', None) or ticker or folder_name
    
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
    
    # FCF Type Definitions
    st.subheader("📚 FCF Definitions")
    st.markdown("""
    - **Free Cash Flow to Firm (FCFF)** = EBIT(1-Tax Rate) + Depreciation & Amortization - Working Capital Change - Capital Expenditures
    - **Free Cash Flow to Equity (FCFE)** = Net Income + Depreciation & Amortization - Working Capital Change - Capital Expenditures + Net Borrowing
    - **Levered Free Cash Flow (LFCF)** = Operating Cash Flow - Capital Expenditures
    """)
    
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
    st.info("💡 This chart shows all FCF calculation methods plus their average (bright orange dashed line with diamond markers)")
    
    company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_default_company_name()
    
    # Force refresh for plots to ensure they use latest data
    st.session_state.data_processor._cached_fcf_data = None
    
    fcf_chart = st.session_state.data_processor.create_fcf_comparison_plot(fcf_results, company_name)
    st.plotly_chart(fcf_chart, use_container_width=True)
    
    # Dedicated Average FCF Plot
    st.subheader("📊 Average FCF Trend")
    st.info("💡 This chart focuses specifically on the average FCF across all calculation methods")
    
    avg_fcf_chart = st.session_state.data_processor.create_average_fcf_plot(fcf_results, company_name)
    st.plotly_chart(avg_fcf_chart, use_container_width=True)
    
    
    # Growth Analysis
    st.subheader("📈 Growth Rate Analysis")
    slope_chart = st.session_state.data_processor.create_slope_analysis_plot(fcf_results, company_name)
    st.plotly_chart(slope_chart, use_container_width=True)
    
    # FCF Data Table
    st.subheader("📋 FCF Data Table")
    st.info("💡 The table includes an Average FCF column that shows the mean of all FCF calculation methods for each year")
    
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
        
        # Apply formatting to FCF columns
        formatted_df = fcf_df.copy()
        for col in formatted_df.columns:
            if col != 'Year':
                formatted_df[col] = formatted_df[col].apply(format_fcf_value)
        
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
            }
        )
        
        # Download button for FCF data (use original unformatted data)
        csv = fcf_df.to_csv(index=False)
        st.download_button(
            label="📥 Download FCF Data (CSV)",
            data=csv,
            file_name=f"{company_name}_FCF_Analysis.csv",
            mime="text/csv",
            help="Downloads raw numerical data including Average FCF column"
        )
        
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
            color_growth_rates, 
            subset=[col for col in growth_df.columns if col != 'FCF Type']
        )
        
        st.dataframe(styled_df, use_container_width=False, width=900, hide_index=True)
        
    else:
        st.info("📋 No FCF data available to display. Please ensure your financial statements contain the required metrics.")

def render_dcf_analysis():
    """Render DCF Analysis tab"""
    st.header("💰 DCF Valuation Analysis")
    
    # FCF type descriptions (used in multiple places)
    fcf_type_descriptions = {
        'FCFE': 'Free Cash Flow to Equity - Net Income + D&A - Working Capital Change - CapEx + Net Borrowing (Recommended for equity valuation)',
        'FCFF': 'Free Cash Flow to Firm - EBIT(1-Tax) + D&A - Working Capital Change - CapEx (Requires debt adjustment)',
        'LFCF': 'Levered Free Cash Flow - Operating Cash Flow - CapEx (Simplified approach)'
    }
    
    if not st.session_state.financial_calculator:
        st.warning("⚠️ Please load company data first using the sidebar.")
        return
    
    # Display Company Information below header
    folder_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_unknown_company_name()
    ticker = st.session_state.financial_calculator.ticker_symbol
    current_price = st.session_state.financial_calculator.current_stock_price
    
    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = getattr(st.session_state.financial_calculator, 'company_name', None) or ticker or folder_name
    
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
            color_growth_rates, 
            subset=[col for col in growth_df.columns if col != 'FCF Type']
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
        help="Select which Free Cash Flow calculation to use for DCF valuation"
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
            min_value=-50.0, max_value=100.0, value=default_growth_1_5, step=1.0,
            format="%.1f", help="Annual growth rate for years 1-5 (based on 5yr historical average)"
        )
        
        growth_yr5_10 = st.number_input(
            "Growth Rate (Years 6-10) (%)",
            min_value=-50.0, max_value=50.0, value=default_growth_6_10, step=0.5,
            format="%.1f", help="Annual growth rate for years 6-10 (conservative estimate)"
        )
        
        terminal_growth = st.number_input(
            "Terminal Growth Rate (%)",
            min_value=0.0, max_value=10.0, value=3.0, step=0.1,
            format="%.1f", help="Long-term growth rate (typically 2-3%)"
        )
    
    with col2:
        st.markdown("**Valuation Assumptions**")
        discount_rate = st.number_input(
            "Discount Rate (WACC) (%)",
            min_value=5.0, max_value=30.0, value=10.0, step=0.5,
            format="%.1f", help="Weighted Average Cost of Capital"
        )
        
        projection_years = st.selectbox(
            "Projection Period (Years)",
            options=[5, 7, 10],
            index=0,
            help="Number of years to project FCF"
        )
    
    # Update DCF assumptions with selected FCF type
    dcf_assumptions = {
        'discount_rate': discount_rate / 100,
        'terminal_growth_rate': terminal_growth / 100,
        'growth_rate_yr1_5': growth_yr1_5 / 100,
        'growth_rate_yr5_10': growth_yr5_10 / 100,
        'projection_years': projection_years,
        'fcf_type': selected_fcf_type
    }
    
    # Check if shares outstanding is available before allowing DCF calculation
    shares_outstanding = getattr(st.session_state.financial_calculator, 'shares_outstanding', 0)
    can_calculate_dcf = shares_outstanding and shares_outstanding > 0
    
    if not can_calculate_dcf:
        st.error("❌ **Cannot Calculate DCF**: Shares outstanding data is required but not available.")
        st.info("💡 Please ensure the ticker symbol is correct and try refreshing market data in the sidebar.")
    
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
                    st.markdown("""
                    - Verify the ticker symbol is correct
                    - Check if the company is publicly traded
                    - Try refreshing market data using the sidebar button
                    - Ensure internet connection for market data fetch
                    """)
                    
                    # Show market data status
                    market_data = dcf_results.get('market_data', {})
                    st.info(f"**Market Data Status:**")
                    st.write(f"- Ticker: {market_data.get('ticker_symbol', 'Not detected')}")
                    per_share_currency = get_currency_symbol_per_share(st.session_state.financial_calculator)
                    financial_currency = get_currency_symbol_financial(st.session_state.financial_calculator)
                    st.write(f"- Current Price: {market_data.get('current_price', 0):.2f} {per_share_currency}")
                    st.write(f"- Market Cap: {financial_currency}{market_data.get('market_cap', 0)/1000000:.1f}M")
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
        st.info(f"💼 DCF calculated using **{used_fcf_type}** - {fcf_type_descriptions.get(used_fcf_type, 'Free Cash Flow')}")
        
        # Get market data (use same source as DCF header for consistency)
        current_price = st.session_state.financial_calculator.current_stock_price or 0
        ticker = st.session_state.financial_calculator.ticker_symbol
        fair_value = dcf_results.get('value_per_share', 0)
        
        # Debug: Show DCF calculation values
        financial_currency = get_currency_symbol_financial(st.session_state.financial_calculator)
        per_share_currency = get_currency_symbol_per_share(st.session_state.financial_calculator)
        st.expander("🔍 Debug: DCF Calculation Details").write({
            'Enterprise Value': f"{financial_currency}{dcf_results.get('enterprise_value', 0)/1000000:.1f}M",
            'Equity Value': f"{financial_currency}{dcf_results.get('equity_value', 0)/1000000:.1f}M", 
            'Shares Outstanding': f"{dcf_results.get('market_data', {}).get('shares_outstanding', 0)/1000000:.1f}M",
            'Fair Value per Share': f"{fair_value:.2f} {per_share_currency}",
            'FCF Type Used': dcf_results.get('fcf_type', get_unknown_fcf_type())
        })
        
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
                        st.metric(label, f"{price_agorot:.0f} ILA", help=f"≈ {price_shekels:.2f} {currency_symbol}")
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
                    fair_value_shekels = dcf_results.get('value_per_share_shekels', fair_value / 100.0)
                    currency_symbol = "₪" if currency == "ILS" else currency
                    st.metric("Fair Value (DCF)", f"{fair_value_agorot:.0f} ILA", help=f"≈ {fair_value_shekels:.2f} {currency_symbol}")
                else:
                    currency_symbol = "$" if currency == "USD" else currency
                    st.metric("Fair Value (DCF)", f"{currency_symbol}{fair_value:.2f}")
            
            with col4:
                if current_price > 0 and fair_value > 0:
                    upside_text = f"{upside_downside:+.1%}"
                    st.metric("Upside/Downside", upside_text, delta=recommendation)
                else:
                    st.metric("Upside/Downside", "N/A", help="Requires both current price and DCF calculation")
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
                        st.metric(label, f"{price_agorot:.0f} ILA", help=f"≈ {price_shekels:.2f} {currency_symbol}")
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
                    fair_value_shekels = dcf_results.get('value_per_share_shekels', fair_value / 100.0)
                    currency_symbol = "₪" if currency == "ILS" else currency
                    st.metric("Fair Value (DCF)", f"{fair_value_agorot:.0f} ILA", help=f"≈ {fair_value_shekels:.2f} {currency_symbol}")
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
                    st.metric("Upside/Downside", "N/A", help="Requires both current price and DCF calculation")
        
        # Investment Recommendation
        if recommendation != "N/A":
            st.markdown("---")
            st.subheader("📋 Investment Recommendation")
            
            rec_col1, rec_col2 = st.columns([1, 3])
            with rec_col1:
                st.markdown(f"**{recommendation}**")
            
            with rec_col2:
                if upside_downside > 0.20:
                    st.success(f"Stock appears undervalued by {upside_downside:.1%}. Consider buying.")
                elif upside_downside < -0.20:
                    st.error(f"Stock appears overvalued by {abs(upside_downside):.1%}. Consider selling.")
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
                dr_min_pct = st.number_input("Min Discount Rate (%)", value=8.0, step=0.5, format="%.1f")
                dr_max_pct = st.number_input("Max Discount Rate (%)", value=15.0, step=0.5, format="%.1f")
            
            with col2:
                st.markdown("**Growth Rate Range (%)**")
                gr_min_pct = st.number_input("Min Growth Rate (%)", value=0.0, step=0.5, format="%.1f")
                gr_max_pct = st.number_input("Max Growth Rate (%)", value=5.0, step=0.5, format="%.1f")
        
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
                    'growth_rate_max_pct': gr_max_pct
                }
                
                discount_rates = np.linspace(dr_min, dr_max, 5)
                growth_rates = np.linspace(gr_min, gr_max, 5)
                
                sensitivity_results = st.session_state.dcf_valuator.sensitivity_analysis(
                    discount_rates, growth_rates, dcf_assumptions
                )
                
                sensitivity_chart = st.session_state.data_processor.create_sensitivity_heatmap(sensitivity_results)
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
                f'Projected FCF ({currency_symbol}M)': projections.get('projected_fcf', []),  # Already in millions
                'Growth Rate': [f"{rate:.1%}" for rate in projections.get('growth_rates', [])],
                f'Present Value ({currency_symbol}M)': dcf_results.get('pv_fcf', [])  # Already in millions
            }
            
            dcf_df = pd.DataFrame(dcf_table_data)
            st.dataframe(dcf_df, use_container_width=False, width=700)
            
            # Enhanced CSV export with comprehensive metadata
            csv_data = create_enhanced_dcf_csv_export(dcf_df, dcf_results, dcf_assumptions, ticker, current_price)
            
            # Create filename with ticker if available
            if ticker:
                file_name = f"{ticker}_DCF_Analysis_Enhanced.csv"
                download_label = f"📥 Download {ticker} Enhanced DCF Data (CSV)"
            else:
                company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_default_company_name()
                file_name = f"{company_name}_DCF_Analysis_Enhanced.csv"
                download_label = "📥 Download Enhanced DCF Data (CSV)"
            
            st.download_button(
                label=download_label,
                data=csv_data,
                file_name=file_name,
                mime="text/csv",
                help="Download comprehensive DCF analysis with metadata for database import"
            )

def get_financial_scale_and_unit(value):
    """
    Determine appropriate scale and unit for financial values based on magnitude
    
    Args:
        value (float): Financial value to scale
    
    Returns:
        tuple: (scaled_value, unit_name, unit_abbreviation)
    """
    abs_value = abs(value)
    
    if abs_value >= 1e12:  # Trillions
        return value / 1e12, "Trillions USD", "T"
    elif abs_value >= 1e9:  # Billions
        return value / 1e9, "Billions USD", "B" 
    elif abs_value >= 1e6:  # Millions
        return value / 1e6, "Millions USD", "M"
    elif abs_value >= 1e3:  # Thousands
        return value / 1e3, "Thousands USD", "K"
    else:
        return value, "USD", ""

def create_enhanced_dcf_csv_export(dcf_df, dcf_results, dcf_assumptions, ticker=None, current_price=None):
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
    company_name = getattr(st.session_state.financial_calculator, 'company_name', None) if hasattr(st.session_state, 'financial_calculator') else None
    if not company_name and ticker:
        company_name = ticker
    elif not company_name:
        company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_default_company_name()
    
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
    assumptions_text = "; ".join([
        f"Discount Rate: {dcf_assumptions.get('discount_rate', 0)*100:.1f}%",
        f"Terminal Growth Rate: {dcf_assumptions.get('terminal_growth_rate', 0)*100:.1f}%",
        f"Projection Years: {dcf_assumptions.get('projection_years', 5)}",
        f"Growth Rate Yr1-5: {dcf_assumptions.get('growth_rate_yr1_5', 0)*100:.1f}%"
    ])
    
    # Extract key results
    calculated_ev = dcf_results.get('enterprise_value', 0) or dcf_results.get('equity_value', 0)  # Fallback to equity for FCFE
    calculated_fair_value = dcf_results.get('value_per_share', 0)
    fcf_type = dcf_results.get('fcf_type', get_unknown_fcf_type())
    
    # Get appropriate scales for financial values
    ev_scaled, ev_unit, ev_abbrev = get_financial_scale_and_unit(calculated_ev)
    equity_value = dcf_results.get('equity_value', 0)
    equity_scaled, equity_unit, equity_abbrev = get_financial_scale_and_unit(equity_value)
    terminal_value = dcf_results.get('terminal_value', 0)
    terminal_scaled, terminal_unit, terminal_abbrev = get_financial_scale_and_unit(terminal_value)
    net_debt = dcf_results.get('net_debt', 0)
    debt_scaled, debt_unit, debt_abbrev = get_financial_scale_and_unit(net_debt)
    
    # === SECTION 1: ANALYSIS METADATA ===
    output.write("# DCF ANALYSIS METADATA\n")
    output.write(f"analysis_date,ticker_symbol,company_name,fcf_type_used,calculated_enterprise_value_{ev_unit.lower().replace(' ', '_')},calculated_fair_value_per_share,current_market_price,assumptions\n")
    output.write(f'"{analysis_date}","{ticker or ""}","{company_name}","{fcf_type}",{ev_scaled:.3f},{calculated_fair_value:.2f},{current_price:.2f},"{assumptions_text}"\n')
    output.write("\n")
    
    # === SECTION 2: KEY RESULTS SUMMARY ===
    output.write("# KEY RESULTS SUMMARY\n")
    output.write("metric,value,unit\n")
    output.write(f'"Enterprise Value",{ev_scaled:.3f},"{ev_unit}"\n')
    output.write(f'"Equity Value",{equity_scaled:.3f},"{equity_unit}"\n')
    # Get appropriate currency for per-share values
    per_share_currency = get_currency_symbol_per_share(st.session_state.financial_calculator) if hasattr(st.session_state, 'financial_calculator') else "$"
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

def render_report_generation():
    """Render the PDF report generation tab"""
    st.header("📄 Generate Comprehensive Report")
    
    if not st.session_state.financial_calculator.fcf_results:
        st.error("❌ No financial data available. Please load data first from the sidebar.")
        return
    
    # Display Company Information below header
    folder_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else get_unknown_company_name()
    ticker = st.session_state.financial_calculator.ticker_symbol if st.session_state.financial_calculator else None
    current_price = st.session_state.financial_calculator.current_stock_price if st.session_state.financial_calculator else None
    
    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    company_name = getattr(st.session_state.financial_calculator, 'company_name', None) or ticker or folder_name
    
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
    folder_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Company Analysis"
    auto_ticker = st.session_state.financial_calculator.ticker_symbol if st.session_state.financial_calculator else ""
    
    # Use company name from yfinance if available, otherwise use ticker, otherwise use folder name
    auto_company_name = getattr(st.session_state.financial_calculator, 'company_name', None) or auto_ticker or folder_name
    
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
        download_path = st.session_state.company_folder if st.session_state.company_folder else os.getcwd()
        st.metric("Download Path", f"...{download_path[-30:]}" if len(download_path) > 30 else download_path)
    
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
                help=price_help
            )
            
            custom_download_path = st.text_input(
                "Download Path",
                value=download_path,
                help="Path where the PDF report will be saved"
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
        st.success(f"✅ Investment analysis will compare DCF fair value vs {current_price:.2f} {per_share_currency} market price")
    elif auto_current_price > 0:
        st.success(f"✅ Investment analysis will compare DCF fair value vs {auto_current_price:.2f} {per_share_currency} auto-detected price")
    else:
        st.info("💡 No current price available - report will show fair value without market comparison")
    
    st.markdown("---")
    
    # Analysis Status Check
    st.subheader("📋 Analysis Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**DCF Analysis Status:**")
        if hasattr(st.session_state, 'user_dcf_assumptions') and st.session_state.user_dcf_assumptions:
            st.success("✅ DCF Analysis Completed")
            dcf_type = st.session_state.user_dcf_assumptions.get('fcf_type', get_unknown_fcf_type())
            growth_1_5 = st.session_state.user_dcf_assumptions.get('growth_rate_yr1_5', 0) * 100
            discount_rate = st.session_state.user_dcf_assumptions.get('discount_rate', 0) * 100
            st.info(f"📈 **Method:** {dcf_type}  \n💰 **Growth (1-5yr):** {growth_1_5:.1f}%  \n🎯 **Discount Rate:** {discount_rate:.1f}%")
        else:
            st.warning("⚠️ DCF Analysis Not Performed")
            st.info("Go to 'DCF Analysis' tab and click 'Calculate DCF Valuation' to include your custom assumptions in the report.")
    
    with col2:
        st.markdown("**Sensitivity Analysis Status:**")
        if hasattr(st.session_state, 'user_sensitivity_params') and st.session_state.user_sensitivity_params:
            st.success("✅ Sensitivity Analysis Completed")
            dr_range = f"{st.session_state.user_sensitivity_params.get('discount_rate_min_pct', 8):.1f}%-{st.session_state.user_sensitivity_params.get('discount_rate_max_pct', 15):.1f}%"
            gr_range = f"{st.session_state.user_sensitivity_params.get('growth_rate_min_pct', 0):.1f}%-{st.session_state.user_sensitivity_params.get('growth_rate_max_pct', 5):.1f}%"
            st.info(f"📊 **Discount Rate Range:** {dr_range}  \n📈 **Growth Rate Range:** {gr_range}")
        else:
            st.warning("⚠️ Custom Sensitivity Analysis Not Performed")
            st.info("Go to 'DCF Analysis' tab and click 'Generate Sensitivity Analysis' to include your custom ranges in the report.")
    
    st.markdown("---")
    
    # Report preview section
    st.subheader("📊 Report Preview")
    
    # Show what will be included
    preview_items = []
    if include_fcf:
        preview_items.extend([
            "✅ FCF Analysis Charts",
            "✅ Growth Rate Analysis Table", 
            "✅ Historical FCF Data Table"
        ])
    
    if include_dcf:
        preview_items.extend([
            "✅ DCF Valuation Summary",
            "✅ DCF Projections Table",
            "✅ Waterfall Chart"
        ])
        
        # Check if we have current price (manual or auto-detected)
        final_preview_price = current_price if current_price > 0 else auto_current_price
        if final_preview_price > 0:
            preview_items.extend([
                "🎯 Investment Recommendation",
                "📈 Fair Value vs Market Price Comparison"
            ])
        
        if include_sensitivity:
            preview_items.append("✅ Sensitivity Analysis Heatmap")
    
    if preview_items:
        for item in preview_items:
            st.write(item)
    else:
        st.warning("⚠️ Please select at least one analysis type to include in the report.")
    
    st.markdown("---")
    
    # Generate report button
    if st.button("🚀 Generate PDF Report", type="primary", disabled=not (include_fcf or include_dcf)):
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
                    fcf_plots['fcf_comparison'] = st.session_state.data_processor.create_fcf_comparison_plot(
                        fcf_results, company_name
                    )
                    fcf_plots['slope_analysis'] = st.session_state.data_processor.create_slope_analysis_plot(
                        fcf_results, company_name
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
                            period_rates = period_rates[:len(fcf_types)]  # Trim if too many
                            
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
                                    fcf_df_data[f'{fcf_type} ({currency_symbol}M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in values]
                                else:
                                    # Pad or trim to match year count
                                    padded_values = (values + [None] * year_count)[:year_count]
                                    fcf_df_data[f'{fcf_type} ({currency_symbol}M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in padded_values]
                            
                            # Handle average FCF
                            currency_symbol = get_currency_symbol(st.session_state.financial_calculator)
                            avg_fcf = fcf_data.get('average_fcf', [])
                            if len(avg_fcf) == year_count:
                                fcf_df_data[f'Average FCF ({currency_symbol}M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in avg_fcf]
                            else:
                                padded_avg = (avg_fcf + [None] * year_count)[:year_count]
                                fcf_df_data[f'Average FCF ({currency_symbol}M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in padded_avg]
                            
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
                    if hasattr(st.session_state, 'user_dcf_assumptions') and st.session_state.user_dcf_assumptions:
                        dcf_assumptions = st.session_state.user_dcf_assumptions
                    else:
                        # Fallback to defaults if user hasn't run DCF analysis yet
                        dcf_assumptions = {
                            'projection_years': 5,
                            'growth_rate_yr1_5': 0.05,
                            'growth_rate_yr5_10': 0.03,
                            'terminal_growth_rate': 0.025,
                            'discount_rate': 0.10,
                            'fcf_type': 'LFCF'
                        }
                    
                    # Calculate DCF
                    dcf_results = st.session_state.dcf_valuator.calculate_dcf_projections(dcf_assumptions)
                    
                    # Prepare DCF plots
                    dcf_plots['waterfall'] = st.session_state.data_processor.create_dcf_waterfall_chart(dcf_results)
                    
                    if include_sensitivity:
                        # Use user's sensitivity parameters if available, otherwise use defaults
                        if hasattr(st.session_state, 'user_sensitivity_params') and st.session_state.user_sensitivity_params:
                            dr_min = st.session_state.user_sensitivity_params.get('discount_rate_min', 0.08)
                            dr_max = st.session_state.user_sensitivity_params.get('discount_rate_max', 0.15)
                            gr_min = st.session_state.user_sensitivity_params.get('growth_rate_min', 0.0)
                            gr_max = st.session_state.user_sensitivity_params.get('growth_rate_max', 0.05)
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
                        dcf_plots['sensitivity'] = st.session_state.data_processor.create_sensitivity_heatmap(sensitivity_results)
                    
                    # Prepare DCF projections table
                    if 'projections' in dcf_results:
                        projections = dcf_results['projections']
                        years = dcf_results.get('years', [])
                        projected_fcf = projections.get('projected_fcf', [])
                        growth_rates = projections.get('growth_rates', [])
                        discount_factors = dcf_results.get('discount_factors', [])
                        pv_fcf = dcf_results.get('pv_fcf', [])
                        
                        # Find the minimum length to ensure all arrays are same size
                        min_length = min(len(years), len(projected_fcf), len(growth_rates), 
                                       len(discount_factors), len(pv_fcf))
                        
                        if min_length > 0:
                            dcf_table_data = {
                                'Year': years[:min_length],
                                f'Projected FCF ({currency_symbol}M)': [f"{fcf:.1f}" for fcf in projected_fcf[:min_length]],
                                'Growth Rate': [f"{rate:.1%}" for rate in growth_rates[:min_length]],
                                'Discount Factor': [f"{df:.3f}" for df in discount_factors[:min_length]],
                                f'Present Value ({currency_symbol}M)': [f"{pv:.1f}" for pv in pv_fcf[:min_length]]
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
                final_current_price = current_price if current_price > 0 else (auto_current_price if auto_current_price > 0 else None)
                
                # Collect actual user sensitivity parameters from session state
                if hasattr(st.session_state, 'user_sensitivity_params') and st.session_state.user_sensitivity_params:
                    sensitivity_params = st.session_state.user_sensitivity_params
                else:
                    # Fallback to defaults if user hasn't run sensitivity analysis yet
                    sensitivity_params = {
                        'discount_rate_min': 0.08,  # 8%
                        'discount_rate_max': 0.15,  # 15%
                        'growth_rate_min': 0.00,    # 0%
                        'growth_rate_max': 0.05,     # 5%
                        'discount_rate_min_pct': 8.0,
                        'discount_rate_max_pct': 15.0,
                        'growth_rate_min_pct': 0.0,
                        'growth_rate_max_pct': 5.0
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
                if hasattr(st.session_state, 'user_sensitivity_params') and st.session_state.user_sensitivity_params:
                    dr_min_pct = sensitivity_params.get('discount_rate_min_pct', 8.0)
                    dr_max_pct = sensitivity_params.get('discount_rate_max_pct', 15.0)
                    gr_min_pct = sensitivity_params.get('growth_rate_min_pct', 0.0)
                    gr_max_pct = sensitivity_params.get('growth_rate_max_pct', 5.0)
                    sens_summary = f"Custom sensitivity ranges: Discount rate {dr_min_pct:.1f}%-{dr_max_pct:.1f}%, Growth rate {gr_min_pct:.1f}%-{gr_max_pct:.1f}%."
                
                user_decisions = {
                    'assumptions_rationale': assumptions_detail.strip(),
                    'risk_factors': f"Market volatility, competitive dynamics, economic conditions, and company-specific operational risks. {sens_summary}",
                    'investment_thesis': f"DCF valuation using {fcf_type} with {proj_years}-year horizon. Growth rates based on historical analysis and forward-looking assumptions. Fair value comparison vs current market price of ${final_current_price:.2f}." if final_current_price else f"DCF valuation using {fcf_type} methodology with {proj_years}-year projection horizon based on selected growth and discount rate assumptions."
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
                    user_decisions=user_decisions
                )
                
                # Generate filename with ticker and date
                from datetime import datetime
                current_date = datetime.now().strftime("%Y%m%d")
                
                if ticker:
                    # Format: TICKER_FCF_DCF_Report_YYYYMMDD.pdf
                    filename = f"{ticker}_FCF_DCF_Report_{current_date}.pdf"
                else:
                    # Fallback format if no ticker
                    safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"FCF_DCF_Report_{safe_company_name.replace(' ', '_')}_{current_date}.pdf"
                
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
                        type="primary"
                    )
                
                with col2:
                    if file_saved:
                        if st.button("📂 Open Folder", help="Open the folder containing the saved report"):
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
                st.info(f"📊 Report includes {len(preview_items)} sections and generated {len(pdf_bytes):,} bytes")
                
                # Show analysis details used
                if final_current_price:
                    st.info(f"📈 Investment analysis included using ${final_current_price:.2f} share price")
                if ticker:
                    st.info(f"🏷️ Report generated for {ticker} - {company_name}")
                
        except Exception as e:
            st.error(f"❌ Error generating report: {str(e)}")
            logger.error(f"Report generation error: {e}")
    
    # Help section
    with st.expander("ℹ️ About PDF Reports"):
        st.markdown("""
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
        """)

def render_watch_lists():
    """Render the watch lists management interface"""
    st.header("📊 Watch Lists Management")
    
    # Create sub-tabs for different watch list functions
    watch_tab1, watch_tab2, watch_tab3 = st.tabs(["📋 Manage Lists", "📈 View Analysis", "⚙️ Capture Settings"])
    
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
            "Watch List Name",
            placeholder="e.g., Tech Stocks, Value Plays, High Growth"
        )
        new_watch_list_desc = st.text_area(
            "Description (Optional)",
            placeholder="Brief description of the watch list purpose"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # Spacing
        if st.button("Create Watch List", type="primary"):
            if new_watch_list_name.strip():
                success = st.session_state.watch_list_manager.create_watch_list(
                    new_watch_list_name.strip(), 
                    new_watch_list_desc.strip()
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
                            success = st.session_state.watch_list_manager.delete_watch_list(watch_list['name'])
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
        index=0 if watch_list_names else None
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
                help="Latest Analysis Only shows current valuation per stock. All Historical Data shows every analysis."
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            show_latest_only = view_mode == "Latest Analysis Only"
        
        # Get watch list data based on view mode
        watch_list_data = st.session_state.watch_list_manager.get_watch_list(
            selected_watch_list_name, latest_only=show_latest_only
        )
        
        if not watch_list_data or not watch_list_data['stocks']:
            st.info(f"📝 Watch list '{selected_watch_list_name}' is empty. Add some analysis results first!")
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
            st.metric("Undervalued", undervalued, delta=f"{undervalued}/{summary_metrics.get('total_stocks', 1)}")
        with col4:
            overvalued = summary_metrics.get('overvalued_count', 0)
            st.metric("Overvalued", overvalued, delta=f"{overvalued}/{summary_metrics.get('total_stocks', 1)}")
        
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
            watch_list_data, 
            title=f"Watch List: {selected_watch_list_name}"
        )
        st.plotly_chart(upside_chart, use_container_width=True)
        
        # Performance distribution
        st.markdown("### 📈 Performance Distribution")
        distribution_chart = watch_list_visualizer.create_performance_distribution_chart(watch_list_data)
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
                    key="trend_ticker_select"
                )
            
            if selected_ticker_trend == "All Stocks":
                # Show trends for all stocks
                trend_chart = watch_list_visualizer.create_time_series_chart(watch_list_data)
            else:
                # Show trend for selected stock
                trend_chart = watch_list_visualizer.create_time_series_chart(watch_list_data, selected_ticker_trend)
            
            st.plotly_chart(trend_chart, use_container_width=True)
        
        # Detailed stock table
        st.markdown("### 📋 Detailed Stock Information")
        
        # Prepare data for table
        table_data = []
        for stock in watch_list_data['stocks']:
            # If showing latest only, get count of historical analyses
            history_count = ""
            if show_latest_only:
                ticker = stock.get('ticker', 'N/A')
                history_data = st.session_state.watch_list_manager.get_stock_analysis_history(
                    selected_watch_list_name, ticker
                )
                if history_data and history_data['total_records'] > 1:
                    history_count = f" ({history_data['total_records']} analyses)"
            
            table_data.append({
                'Ticker': stock.get('ticker', 'N/A') + history_count,
                'Company': stock.get('company_name', 'N/A'),
                'Current Price': f"${stock.get('current_price', 0):.2f}",
                'Fair Value': f"${stock.get('fair_value', 0):.2f}",
                'Upside/Downside': f"{stock.get('upside_downside_pct', 0):.1f}%",
                'Discount Rate': f"{stock.get('discount_rate', 0):.1f}%",
                'FCF Type': stock.get('fcf_type', 'N/A'),
                'Analysis Date': stock.get('analysis_date', '')[:10] if stock.get('analysis_date') else 'N/A'
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True)
        
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
                help=f"Downloads {view_mode.lower()} data"
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
                    key="ticker_history_export"
                )
                
                if selected_ticker and selected_ticker != "Select ticker...":
                    if st.button(f"📈 Export {selected_ticker} History"):
                        export_path = st.session_state.watch_list_manager.export_stock_history_to_csv(
                            selected_watch_list_name, selected_ticker
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
            selected_list = st.selectbox(
                "Select Active Watch List",
                options=available_lists,
                index=available_lists.index(current_wl) if current_wl in available_lists else 0
            )
            
            if st.button("🎯 Set as Active"):
                st.session_state.current_watch_list = selected_list
                analysis_capture.set_current_watch_list(selected_list)
                st.success(f"✅ Set '{selected_list}' as active watch list")
                st.rerun()
        else:
            st.info("📝 No watch lists available. Create a watch list first!")
    
    st.markdown("---")
    
    # Manual capture section
    st.markdown("### 📥 Manual Analysis Capture")
    st.info("💡 **Tip:** When you run a DCF analysis with capture enabled, results will be automatically saved to the active watch list.")
    
    # Show current DCF results if available
    if st.session_state.dcf_results and current_wl:
        st.markdown("**Current DCF Results Available:**")
        
        # Get ticker and company info
        ticker = "UNKNOWN"
        company_name = ""
        
        if hasattr(st.session_state, 'financial_calculator') and st.session_state.financial_calculator:
            ticker = st.session_state.financial_calculator.ticker_symbol or "UNKNOWN"
            company_name = st.session_state.financial_calculator.company_name or ""
        
        st.write(f"**Ticker:** {ticker}")
        st.write(f"**Company:** {company_name}")
        st.write(f"**Target Watch List:** {current_wl}")
        
        if st.button("💾 Capture Current Analysis"):
            success = analysis_capture.capture_dcf_analysis(
                ticker=ticker,
                company_name=company_name,
                dcf_results=st.session_state.dcf_results
            )
            
            if success:
                st.success(f"✅ Successfully captured analysis for {ticker}")
            else:
                st.error("❌ Failed to capture analysis")
    
    else:
        if not current_wl:
            st.warning("⚠️ Set an active watch list first")
        else:
            st.info("📊 Run a DCF analysis to see capture options")

def main():
    """Main application function"""
    initialize_session_state()
    render_sidebar()
    
    # Main content area
    if not st.session_state.company_folder:
        render_welcome()
    else:
        # Create tabs for FCF and DCF analysis
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 FCF Analysis", "💰 DCF Valuation", "📄 Generate Report", "📊 Watch Lists", "📚 Help & Guide"])
        
        with tab1:
            render_fcf_analysis()
        
        with tab2:
            render_dcf_analysis()
        
        with tab3:
            render_report_generation()
        
        with tab4:
            render_watch_lists()
        
        with tab5:
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
        "📊 Watch Lists",
        "📁 Data Structure",
        "🔧 LTM Integration",
        "🏗️ System Architecture",
        "📈 Mathematical Formulas",
        "⚙️ Configuration",
        "🐛 Troubleshooting"
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
    
    st.markdown("""
    ### Welcome to the FCF Analysis Tool!
    
    This application provides comprehensive **Free Cash Flow (FCF) analysis** and **Discounted Cash Flow (DCF) valuation** capabilities 
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
       - Create Watch Lists to track multiple companies over time
       - Generate professional reports in the Reports tab
    
    #### Key Features:
    - ✅ **Multi-Market Support**: US stocks and TASE stocks with automatic currency handling
    - ✅ **Smart Ticker Processing**: Automatic .TA suffix handling for TASE stocks
    - ✅ **Three FCF Methods**: FCFF, FCFE, LFCF calculations
    - ✅ **Interactive Charts**: Plotly-powered visualizations
    - ✅ **DCF Modeling**: Complete valuation with sensitivity analysis
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
    """)
    
    st.info("💡 **Pro Tip**: The market selection automatically handles ticker formatting - just enter the base ticker (e.g., 'TEVA') and the app will add '.TA' for TASE stocks!")
    
    st.success("""
    🆕 **NEW: Watch Lists Feature**
    
    Track multiple companies and analyze portfolio performance over time:
    - **Automatic Capture**: DCF results saved to watch lists automatically
    - **Performance Charts**: Visual upside/downside analysis with reference lines
    - **Historical Tracking**: Complete audit trail of all valuations
    - **Export Options**: CSV exports for current view and historical data
    
    Get started: Go to the **📊 Watch Lists** tab to create your first list!
    """)

def render_multi_market_support_guide():
    """Render the multi-market support guide"""
    st.subheader("🌍 Multi-Market Support Guide")
    
    st.markdown("""
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
    """)

def render_fcf_analysis_guide():
    """Render the FCF analysis guide"""
    st.subheader("📊 Free Cash Flow Analysis Guide")
    
    st.markdown("""
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
    """)

def render_dcf_valuation_guide():
    """Render the DCF valuation guide"""
    st.subheader("💰 DCF Valuation Guide")
    
    st.markdown("""
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
    """)

def render_data_structure_guide():
    """Render the data structure guide"""
    st.subheader("📁 Data Structure Requirements")
    
    st.markdown("""
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
    """)

def render_ltm_integration_guide():
    """Render the LTM integration guide"""
    st.subheader("🔧 LTM (Latest Twelve Months) Integration")
    
    st.markdown("""
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
    """)

def render_system_architecture_guide():
    """Render the system architecture guide"""
    st.subheader("🏗️ System Architecture")
    
    st.markdown("""
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
    """)

def render_mathematical_formulas_guide():
    """Render the mathematical formulas guide"""
    st.subheader("📈 Mathematical Formulas")
    
    st.markdown("""
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
    """)

def render_configuration_guide():
    """Render the configuration guide"""
    st.subheader("⚙️ Configuration & Settings")
    
    st.markdown("""
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
    """)

def render_troubleshooting_guide():
    """Render the troubleshooting guide"""
    st.subheader("🐛 Troubleshooting Guide")
    
    st.markdown("""
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
    """)

def render_watch_lists_guide():
    """Render comprehensive watch lists documentation"""
    st.markdown("""
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
    """)

if __name__ == "__main__":
    main()