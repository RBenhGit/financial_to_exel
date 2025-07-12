"""
Modern FCF Analysis Application using Streamlit

This replaces the matplotlib-based UI with a modern, responsive web interface.
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
            
            st.sidebar.success(f"📈 **Ticker**: {ticker}")
            if current_price:
                st.sidebar.info(f"💰 **Current Price**: ${current_price:.2f}")
            else:
                st.sidebar.warning("⚠️ Price fetch failed")
                
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
    
    # FCF Summary Metrics
    st.subheader("📊 FCF Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    fcf_results = st.session_state.fcf_results
    
    with col1:
        if 'FCFF' in fcf_results and fcf_results['FCFF']:
            latest_fcff = fcf_results['FCFF'][-1]  # Values already in millions
            st.metric("FCFF (Latest)", f"${latest_fcff:.1f}M")
        else:
            st.metric("FCFF (Latest)", "N/A")
    
    with col2:
        if 'FCFE' in fcf_results and fcf_results['FCFE']:
            latest_fcfe = fcf_results['FCFE'][-1]  # Values already in millions
            st.metric("FCFE (Latest)", f"${latest_fcfe:.1f}M")
        else:
            st.metric("FCFE (Latest)", "N/A")
    
    with col3:
        if 'LFCF' in fcf_results and fcf_results['LFCF']:
            latest_lfcf = fcf_results['LFCF'][-1]  # Values already in millions
            st.metric("LFCF (Latest)", f"${latest_lfcf:.1f}M")
        else:
            st.metric("LFCF (Latest)", "N/A")
    
    with col4:
        # Calculate average FCF
        all_fcf_values = []
        for fcf_type, values in fcf_results.items():
            if values:
                all_fcf_values.extend(values)
        if all_fcf_values:
            avg_fcf = np.mean(all_fcf_values)  # Values already in millions
            st.metric("Average FCF", f"${avg_fcf:.1f}M")
        else:
            st.metric("Average FCF", "N/A")
    
    # FCF Comparison Chart
    st.subheader("📊 FCF Trend Analysis")
    
    company_name = os.path.basename(st.session_state.company_folder) if st.session_state.company_folder else "Company"
    fcf_chart = st.session_state.data_processor.create_fcf_comparison_plot(fcf_results, company_name)
    st.plotly_chart(fcf_chart, use_container_width=True)
    
    # Growth Analysis
    st.subheader("📈 Growth Rate Analysis")
    slope_chart = st.session_state.data_processor.create_slope_analysis_plot(fcf_results, company_name)
    st.plotly_chart(slope_chart, use_container_width=True)
    
    # FCF Data Table
    st.subheader("📋 FCF Data Table")
    
    # Create comprehensive FCF table
    valid_fcf_data = [values for values in fcf_results.values() if values]
    max_years = max(len(values) for values in valid_fcf_data) if valid_fcf_data else 0
    if max_years > 0:
        years = list(range(2024 - max_years + 1, 2025))
        
        fcf_df_data = {'Year': years[-max_years:]}
        for fcf_type, values in fcf_results.items():
            if values:
                # Pad values to match the year range length
                values_length = len(values)
                if values_length < max_years:
                    # Pad with None values at the beginning for missing years
                    padded_values = [None] * (max_years - values_length) + values
                else:
                    # Take the last max_years values
                    padded_values = values[-max_years:]
                
                # Values already in millions, handle None values
                fcf_values_millions = [v if v is not None else None for v in padded_values]
                fcf_df_data[f'{fcf_type} ($M)'] = fcf_values_millions
        
        fcf_df = pd.DataFrame(fcf_df_data)
        st.dataframe(fcf_df, use_container_width=False, width=800)
        
        # Download button for FCF data
        csv = fcf_df.to_csv(index=False)
        st.download_button(
            label="📥 Download FCF Data (CSV)",
            data=csv,
            file_name=f"{company_name}_FCF_Analysis.csv",
            mime="text/csv"
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
    
    # Calculate intelligent defaults based on historical FCF data
    fcf_results = st.session_state.financial_calculator.fcf_results
    default_growth_1_5 = 5.0  # 5% fallback
    default_growth_6_10 = 2.5  # 2.5% fallback
    
    if fcf_results:
        # Calculate 5-year average growth rate across all FCF types
        five_year_growth_rates = []
        
        for fcf_type in ['LFCF', 'FCFE', 'FCFF']:
            values = fcf_results.get(fcf_type, [])
            if len(values) >= 6:  # Need at least 6 years for 5-year growth
                start_value = values[-6]
                end_value = values[-1]
                
                if start_value != 0 and start_value is not None and end_value is not None:
                    growth_rate = (abs(end_value) / abs(start_value)) ** (1 / 5) - 1
                    
                    # Handle negative cash flows
                    if end_value < 0 and start_value > 0:
                        growth_rate = -growth_rate
                    elif end_value > 0 and start_value < 0:
                        growth_rate = abs(growth_rate)
                    
                    # Cap extreme values
                    if -0.5 <= growth_rate <= 1.0:
                        five_year_growth_rates.append(growth_rate)
        
        if five_year_growth_rates:
            avg_5yr_growth = sum(five_year_growth_rates) / len(five_year_growth_rates)
            default_growth_1_5 = avg_5yr_growth * 100
            default_growth_6_10 = (avg_5yr_growth / 2) * 100  # Half of 5yr average
    
    # DCF Assumptions Panel
    st.subheader("⚙️ DCF Assumptions")
    
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
    
    # Update DCF assumptions
    dcf_assumptions = {
        'discount_rate': discount_rate / 100,
        'terminal_growth_rate': terminal_growth / 100,
        'growth_rate_yr1_5': growth_yr1_5 / 100,
        'growth_rate_yr5_10': growth_yr5_10 / 100,
        'projection_years': projection_years
    }
    
    # Calculate DCF
    if st.button("🔄 Calculate DCF Valuation", type="primary"):
        with st.spinner("Calculating DCF valuation..."):
            st.session_state.dcf_results = st.session_state.dcf_valuator.calculate_dcf_projections(dcf_assumptions)
        st.success("✅ DCF calculation completed!")
        st.rerun()
    
    # Display DCF Results
    if st.session_state.dcf_results:
        dcf_results = st.session_state.dcf_results
        
        # Key Valuation Metrics
        st.subheader("🎯 Valuation Results")
        
        # Get market data
        market_data = dcf_results.get('market_data', {})
        current_price = market_data.get('current_price', 0)
        fair_value = dcf_results.get('value_per_share', 0)
        
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
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            enterprise_value = dcf_results.get('enterprise_value', 0)  # Already in millions
            st.metric("Enterprise Value", f"${enterprise_value:.0f}M")
        
        with col2:
            equity_value = dcf_results.get('equity_value', 0)  # Already in millions
            st.metric("Equity Value", f"${equity_value:.0f}M")
        
        with col3:
            if current_price > 0:
                st.metric("Current Price", f"${current_price:.2f}")
            else:
                st.metric("Current Price", "Enter Ticker", help="Add ticker symbol in sidebar to fetch current price")
        
        with col4:
            st.metric("Fair Value (DCF)", f"${fair_value:.2f}")
        
        with col5:
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
                st.markdown("**Discount Rate Range**")
                dr_min = st.number_input("Min Discount Rate", value=0.08, step=0.01, format="%.2f")
                dr_max = st.number_input("Max Discount Rate", value=0.15, step=0.01, format="%.2f")
            
            with col2:
                st.markdown("**Terminal Growth Range**")
                tg_min = st.number_input("Min Terminal Growth", value=0.015, step=0.005, format="%.3f")
                tg_max = st.number_input("Max Terminal Growth", value=0.035, step=0.005, format="%.3f")
        
        if st.button("Generate Sensitivity Analysis"):
            with st.spinner("Generating sensitivity analysis..."):
                discount_rates = np.linspace(dr_min, dr_max, 5)
                terminal_growth_rates = np.linspace(tg_min, tg_max, 5)
                
                sensitivity_results = st.session_state.dcf_valuator.sensitivity_analysis(
                    discount_rates, terminal_growth_rates, dcf_assumptions
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

def main():
    """Main application function"""
    initialize_session_state()
    render_sidebar()
    
    # Main content area
    if not st.session_state.company_folder:
        render_welcome()
    else:
        # Create tabs for FCF and DCF analysis
        tab1, tab2 = st.tabs(["📈 FCF Analysis", "💰 DCF Valuation"])
        
        with tab1:
            render_fcf_analysis()
        
        with tab2:
            render_dcf_analysis()

if __name__ == "__main__":
    main()