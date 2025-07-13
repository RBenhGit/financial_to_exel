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

def render_sidebar():
    """Render the sidebar with file selection and settings"""
    st.sidebar.title("📊 FCF Analysis Tool")
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
        help="Path to folder containing FY/ and LTM/ subfolders",
        placeholder="e.g., C:/data/AAPL or /home/user/data/TSLA"
    )
    
    # Add a diagnostic option
    if company_path and os.path.exists(company_path):
        if st.sidebar.button("🔬 Diagnose Data Issues"):
            st.sidebar.info("Check the console/terminal for diagnostic output")
            # Run diagnosis in the background
            try:
                from diagnose_data import examine_folder_structure, examine_excel_file
                import io
                import contextlib
                
                # Capture output
                output_buffer = io.StringIO()
                with contextlib.redirect_stdout(output_buffer):
                    examine_folder_structure(company_path)
                    
                    # Quick check for files
                    for subfolder in ['FY', 'LTM']:
                        subfolder_path = os.path.join(company_path, subfolder)
                        if os.path.exists(subfolder_path):
                            for file_name in os.listdir(subfolder_path):
                                if file_name.endswith(('.xlsx', '.xls')):
                                    file_path = os.path.join(subfolder_path, file_name)
                                    examine_excel_file(file_path)
                
                # Display results in sidebar
                diagnosis_result = output_buffer.getvalue()
                st.sidebar.text_area("Diagnostic Results:", diagnosis_result, height=200)
                
            except Exception as e:
                st.sidebar.error(f"Diagnostic failed: {e}")
    
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
                    
                    # Show auto-extracted ticker
                    if st.session_state.financial_calculator.ticker_symbol:
                        st.sidebar.info(f"🎯 Auto-detected ticker: {st.session_state.financial_calculator.ticker_symbol}")
                
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
                st.sidebar.info(f"💰 **Current Price**: ${current_price:.2f}")
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
                    market_data = st.session_state.financial_calculator.fetch_market_data()
                    if market_data:
                        st.sidebar.success("✅ Market data updated!")
                        st.rerun()
                    else:
                        st.sidebar.error("❌ Failed to fetch market data")
        else:
            st.sidebar.warning("⚠️ No ticker auto-detected")
            
            # Manual ticker input as fallback
            manual_ticker = st.sidebar.text_input(
                "Manual Ticker Entry",
                placeholder="e.g., GOOGL, AAPL, MSFT",
                help="Enter ticker if auto-detection failed"
            )
            
            if manual_ticker and st.session_state.financial_calculator:
                if st.sidebar.button("📊 Fetch Market Data"):
                    with st.spinner(f"Fetching data for {manual_ticker.upper()}..."):
                        market_data = st.session_state.financial_calculator.fetch_market_data(manual_ticker.upper())
                        if market_data:
                            st.sidebar.success(f"✅ Fetched data for {manual_ticker.upper()}")
                            st.rerun()
                        else:
                            st.sidebar.error(f"❌ Could not fetch data for {manual_ticker.upper()}")
        
        # Quick stats
        if st.session_state.fcf_results:
            fcf_types = list(st.session_state.fcf_results.keys())
            st.sidebar.write(f"**FCF Types Calculated:** {len(fcf_types)}")
            for fcf_type in fcf_types:
                values = st.session_state.fcf_results[fcf_type]
                if values:
                    latest_fcf = values[-1]  # Values already in millions
                    st.sidebar.write(f"**{fcf_type} (Latest):** ${latest_fcf:.1f}M")

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
        - **Professional Visualizations**: Interactive charts and graphs
        - **Responsive Design**: Works on any screen size
        - **Export Capabilities**: Download results and charts
        
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
    
    # Example company demonstration
    st.markdown("---")
    st.subheader("🎯 Demo Mode")
    st.info("To see the tool in action, please load a company folder using the sidebar.")

def render_fcf_analysis():
    """Render FCF Analysis tab"""
    st.header("📈 Free Cash Flow Analysis")
    
    if not st.session_state.fcf_results:
        st.warning("⚠️ Please load company data first using the sidebar.")
        return
    
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
    
    with col1:
        if latest_values['FCFF'] is not None:
            st.metric("FCFF (Latest)", f"${latest_values['FCFF']:.1f}M")
        else:
            st.metric("FCFF (Latest)", "N/A")
    
    with col2:
        if latest_values['FCFE'] is not None:
            st.metric("FCFE (Latest)", f"${latest_values['FCFE']:.1f}M")
        else:
            st.metric("FCFE (Latest)", "N/A")
    
    with col3:
        if latest_values['LFCF'] is not None:
            st.metric("LFCF (Latest)", f"${latest_values['LFCF']:.1f}M")
        else:
            st.metric("LFCF (Latest)", "N/A")
    
    with col4:
        # Average of the 3 FCF types (latest values)
        if avg_latest_fcf is not None:
            st.metric("Average FCF (Latest)", f"${avg_latest_fcf:.1f}M")
        else:
            st.metric("Average FCF (Latest)", "N/A")
    
    with col5:
        # Show the range (max - min) of latest FCF values
        if len(available_latest) > 1:
            fcf_range = max(available_latest) - min(available_latest)
            st.metric("FCF Range", f"${fcf_range:.1f}M")
        else:
            st.metric("FCF Range", "N/A")
    
    # FCF Comparison Chart
    st.subheader("📊 FCF Trend Analysis")
    st.info("💡 This chart shows all FCF calculation methods plus their average (bright orange dashed line with diamond markers)")
    
    company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Company"
    
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
        for fcf_type, values in fcf_data['padded_fcf_data'].items():
            fcf_df_data[f'{fcf_type} ($M)'] = values
        
        # Add Average FCF column using pre-calculated averages
        fcf_df_data['Average FCF ($M)'] = fcf_data['average_fcf']
        
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
                "Average FCF ($M)": st.column_config.TextColumn(
                    "Average FCF ($M)",
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
        
        # Calculate growth rates for each FCF type
        growth_data = {'FCF Type': ['LFCF', 'FCFE', 'FCFF', 'Average']}
        
        for period in range(1, 10):  # 1yr to 9yr
            period_growth_rates = []
            
            for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
                values = fcf_results.get(fcf_type, [])
                if len(values) >= period + 1:
                    start_value = values[-(period + 1)]
                    end_value = values[-1]
                    
                    if start_value != 0 and start_value is not None and end_value is not None:
                        # Calculate annualized growth rate
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        # Handle negative cash flows
                        if end_value < 0 and start_value > 0:
                            growth_rate = -growth_rate
                        elif end_value > 0 and start_value < 0:
                            growth_rate = abs(growth_rate)
                        
                        period_growth_rates.append(growth_rate)
                    else:
                        period_growth_rates.append(None)
                else:
                    period_growth_rates.append(None)
            
            # Calculate average (excluding None values)
            valid_rates = [rate for rate in period_growth_rates if rate is not None]
            avg_rate = sum(valid_rates) / len(valid_rates) if valid_rates else None
            period_growth_rates.append(avg_rate)
            
            # Format as percentages
            formatted_rates = []
            for rate in period_growth_rates:
                if rate is not None:
                    formatted_rates.append(f"{rate:.1%}")
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
        styled_df = growth_df.style.applymap(
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
    
    # Display Company and Ticker Information
    company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Unknown"
    ticker = st.session_state.financial_calculator.ticker_symbol
    current_price = st.session_state.financial_calculator.current_stock_price
    
    # Company Header with Ticker Info
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader(f"📊 {company_name}")
    
    with col2:
        if ticker:
            st.metric("Ticker Symbol", ticker)
        else:
            st.metric("Ticker Symbol", "N/A", help="No ticker auto-detected")
    
    with col3:
        if current_price:
            st.metric("Market Price", f"${current_price:.2f}")
        else:
            st.metric("Market Price", "N/A", help="Price data unavailable")
    
    st.markdown("---")
    
    # Get FCF results for dropdown selection
    fcf_results = st.session_state.financial_calculator.fcf_results
    
    # FCF Growth Rate Analysis Table
    if fcf_results and any(fcf_results.values()):
        st.subheader("📈 FCF Growth Rate Analysis")
        
        # Calculate growth rates for each FCF type
        growth_data = {'FCF Type': ['LFCF', 'FCFE', 'FCFF', 'Average']}
        
        for period in range(1, 10):  # 1yr to 9yr
            period_growth_rates = []
            
            for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
                values = fcf_results.get(fcf_type, [])
                if len(values) >= period + 1:
                    start_value = values[-(period + 1)]
                    end_value = values[-1]
                    
                    if start_value != 0 and start_value is not None and end_value is not None:
                        # Calculate annualized growth rate
                        growth_rate = (abs(end_value) / abs(start_value)) ** (1 / period) - 1
                        
                        # Handle negative cash flows
                        if end_value < 0 and start_value > 0:
                            growth_rate = -growth_rate
                        elif end_value > 0 and start_value < 0:
                            growth_rate = abs(growth_rate)
                        
                        period_growth_rates.append(growth_rate)
                    else:
                        period_growth_rates.append(None)
                else:
                    period_growth_rates.append(None)
            
            # Calculate average (excluding None values)
            valid_rates = [rate for rate in period_growth_rates if rate is not None]
            avg_rate = sum(valid_rates) / len(valid_rates) if valid_rates else None
            period_growth_rates.append(avg_rate)
            
            # Format as percentages
            formatted_rates = []
            for rate in period_growth_rates:
                if rate is not None:
                    formatted_rates.append(f"{rate:.1%}")
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
        styled_df = growth_df.style.applymap(
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
        st.info(f"💡 Using {selected_fcf_type}: Latest FCF = ${latest_fcf:.1f}M")
    
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
                    st.write(f"- Current Price: ${market_data.get('current_price', 0):.2f}")
                    st.write(f"- Market Cap: ${market_data.get('market_cap', 0)/1000000:.1f}M")
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
        st.expander("🔍 Debug: DCF Calculation Details").write({
            'Enterprise Value': f"${dcf_results.get('enterprise_value', 0)/1000000:.1f}M",
            'Equity Value': f"${dcf_results.get('equity_value', 0)/1000000:.1f}M", 
            'Shares Outstanding': f"{dcf_results.get('market_data', {}).get('shares_outstanding', 0)/1000000:.1f}M",
            'Fair Value per Share': f"${fair_value:.2f}",
            'FCF Type Used': dcf_results.get('fcf_type', 'Unknown')
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
                st.metric("Equity Value (FCFE)", f"${equity_value:.0f}M")
            
            with col2:
                if current_price > 0:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, f"${current_price:.2f}")
                else:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, "N/A", help="Market price unavailable")
            
            with col3:
                st.metric("Fair Value (DCF)", f"${fair_value:.2f}")
            
            with col4:
                if current_price > 0 and fair_value > 0:
                    upside_text = f"{upside_downside:+.1%}"
                    st.metric("Upside/Downside", upside_text, delta=recommendation)
                else:
                    st.metric("Upside/Downside", "N/A", help="Requires both current price and DCF calculation")
        else:
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                enterprise_value = dcf_results.get('enterprise_value', 0)  # Already in millions
                st.metric("Enterprise Value", f"${enterprise_value:.0f}M")
            
            with col2:
                net_debt = dcf_results.get('net_debt', 0)  # Already in millions
                st.metric("Net Debt", f"${net_debt:.0f}M")
            
            with col3:
                equity_value = dcf_results.get('equity_value', 0)  # Already in millions
                st.metric("Equity Value", f"${equity_value:.0f}M")
            
            with col4:
                if current_price > 0:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, f"${current_price:.2f}")
                else:
                    label = f"Current Price ({ticker})" if ticker else "Current Price"
                    st.metric(label, "N/A", help="Market price unavailable")
            
            with col5:
                st.metric("Fair Value (DCF)", f"${fair_value:.2f}")
        
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
        st.metric("Terminal Value", f"${terminal_value:.0f}M")
        
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
            
            dcf_table_data = {
                'Year': years,
                'Projected FCF ($M)': projections.get('projected_fcf', []),  # Already in millions
                'Growth Rate': [f"{rate:.1%}" for rate in projections.get('growth_rates', [])],
                'Present Value ($M)': dcf_results.get('pv_fcf', [])  # Already in millions
            }
            
            dcf_df = pd.DataFrame(dcf_table_data)
            st.dataframe(dcf_df, use_container_width=False, width=700)
            
            # Download button for DCF data
            csv = dcf_df.to_csv(index=False)
            
            # Create filename with ticker if available
            if ticker:
                file_name = f"{ticker}_DCF_Analysis.csv"
                download_label = f"📥 Download {ticker} DCF Data (CSV)"
            else:
                company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Company"
                file_name = f"{company_name}_DCF_Analysis.csv"
                download_label = "📥 Download DCF Data (CSV)"
            
            st.download_button(
                label=download_label,
                data=csv,
                file_name=file_name,
                mime="text/csv"
            )

def render_report_generation():
    """Render the PDF report generation tab"""
    st.header("📄 Generate Comprehensive Report")
    
    if not st.session_state.financial_calculator.fcf_results:
        st.error("❌ No financial data available. Please load data first from the sidebar.")
        return
    
    # Auto-detect company information
    st.subheader("📋 Report Configuration")
    
    # Extract information from current analysis
    auto_company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Company Analysis"
    auto_ticker = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else ""
    
    # Get market data from DCF valuator
    auto_current_price = 0.0
    if hasattr(st.session_state, 'dcf_valuator') and st.session_state.dcf_valuator:
        try:
            market_data = st.session_state.dcf_valuator._get_market_data()
            auto_current_price = market_data.get('current_price', 0.0)
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
            st.metric("Current Price", f"${auto_current_price:.2f}")
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
            ticker = st.text_input("Stock Ticker", value=auto_ticker)
            
        with col2:
            current_price = st.number_input(
                "Current Share Price ($)", 
                value=float(auto_current_price) if auto_current_price > 0 else 0.0,
                step=0.01, 
                format="%.2f",
                help="Override auto-detected price if needed"
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
    if current_price > 0:
        st.success(f"✅ Investment analysis will compare DCF fair value vs ${current_price:.2f} market price")
    elif auto_current_price > 0:
        st.success(f"✅ Investment analysis will compare DCF fair value vs ${auto_current_price:.2f} auto-detected price")
    else:
        st.info("💡 No current price available - report will show fair value without market comparison")
    
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
                                    fcf_df_data[f'{fcf_type} ($M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in values]
                                else:
                                    # Pad or trim to match year count
                                    padded_values = (values + [None] * year_count)[:year_count]
                                    fcf_df_data[f'{fcf_type} ($M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in padded_values]
                            
                            # Handle average FCF
                            avg_fcf = fcf_data.get('average_fcf', [])
                            if len(avg_fcf) == year_count:
                                fcf_df_data['Average FCF ($M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in avg_fcf]
                            else:
                                padded_avg = (avg_fcf + [None] * year_count)[:year_count]
                                fcf_df_data['Average FCF ($M)'] = [f"{v:.1f}" if v is not None else "N/A" for v in padded_avg]
                            
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
                    # Get DCF assumptions
                    dcf_assumptions = {
                        'projection_years': 5,
                        'growth_rate_yr1_5': 0.05,
                        'growth_rate_yr5_10': 0.03,
                        'terminal_growth_rate': 0.025,
                        'discount_rate': 0.10,
                        'tax_rate': 0.25
                    }
                    
                    # Calculate DCF
                    dcf_results = st.session_state.dcf_valuator.calculate_dcf_projections(dcf_assumptions)
                    
                    # Prepare DCF plots
                    dcf_plots['waterfall'] = st.session_state.data_processor.create_dcf_waterfall_chart(dcf_results)
                    
                    if include_sensitivity:
                        discount_rates = np.linspace(0.08, 0.15, 5)
                        growth_rates = np.linspace(0.0, 0.05, 5)
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
                                'Projected FCF ($M)': [f"{fcf:.1f}" for fcf in projected_fcf[:min_length]],
                                'Growth Rate': [f"{rate:.1%}" for rate in growth_rates[:min_length]],
                                'Discount Factor': [f"{df:.3f}" for df in discount_factors[:min_length]],
                                'Present Value ($M)': [f"{pv:.1f}" for pv in pv_fcf[:min_length]]
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
                    ticker=ticker if ticker else None
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
                                    subprocess.run(f'explorer /select,"{saved_path}"', shell=True)
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

def main():
    """Main application function"""
    initialize_session_state()
    render_sidebar()
    
    # Main content area
    if not st.session_state.company_folder:
        render_welcome()
    else:
        # Create tabs for FCF and DCF analysis
        tab1, tab2, tab3 = st.tabs(["📈 FCF Analysis", "💰 DCF Valuation", "📄 Generate Report"])
        
        with tab1:
            render_fcf_analysis()
        
        with tab2:
            render_dcf_analysis()
        
        with tab3:
            render_report_generation()

if __name__ == "__main__":
    main()