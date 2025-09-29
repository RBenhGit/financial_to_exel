"""
Modern FCF Analysis Application - Refactored Architecture
========================================================

Restructured Streamlit application with improved separation of concerns:
- UI rendering separated from business logic
- Utility functions extracted to dedicated modules  
- Help documentation isolated for maintainability
- Data processing logic centralized
"""

# Standard library imports
import logging
from pathlib import Path

# Third-party imports
import streamlit as st

# Local imports - Core business logic
from core.analysis.engines.financial_calculations import FinancialCalculator
from core.analysis.dcf.dcf_valuation import DCFValuator
from core.analysis.ddm.ddm_valuation import DDMValuator
from core.analysis.pb.pb_valuation import PBValuator
from core.data_processing.processors.data_processing import DataProcessor
from report_generator import FCFReportGenerator

# Local imports - Streamlit-specific modules
from streamlit_utils import (
    initialize_session_state_defaults,
    get_currency_symbol,
    get_currency_symbol_per_share,
    get_currency_symbol_financial,
    format_financial_value,
    is_tase_stock
)
from streamlit_data_processing import (
    centralized_data_loader,
    create_ticker_mode_calculator,
    validate_financial_data,
    get_data_quality_metrics
)
from streamlit_help import render_help_guide
from fcf_analysis_streamlit import render_dcf_analysis

# Configure Streamlit page
st.set_page_config(
    page_title="FCF Financial Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/financial-analysis',
        'Report a bug': 'https://github.com/your-repo/financial-analysis/issues',
        'About': 'Modern Financial Analysis Tool with FCF, DCF, DDM, and P/B Analysis'
    }
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state with default values."""
    initialize_session_state_defaults()
    
    # App-specific session state
    session_defaults = {
        'company_folder': None,
        'show_advanced_settings': False,
        'analysis_cache': {},
        'last_data_refresh': None
    }
    
    for key, default_value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def render_sidebar():
    """Render sidebar with data source selection and configuration."""
    st.sidebar.header("🔧 Data Configuration")
    
    # Data source selection
    data_source = st.sidebar.selectbox(
        "📊 Data Source",
        ["Excel Files", "API (Ticker)", "Auto-Detect"],
        index=0,
        help="Choose how to load financial data"
    )
    st.session_state.data_source = data_source
    
    if data_source == "Excel Files":
        render_excel_data_source()
    elif data_source == "API (Ticker)":
        render_api_data_source()
    else:  # Auto-Detect
        render_auto_detect_source()
    
    # Advanced settings
    render_advanced_settings()
    
    # Data quality indicators
    if st.session_state.financial_calculator:
        render_data_quality_panel()


def render_excel_data_source():
    """Render Excel file data source configuration."""
    st.sidebar.subheader("📁 Excel Data Source")
    
    # File selection
    if st.sidebar.button("📂 Select Company Folder", type="primary"):
        # This would open a folder dialog in a real implementation
        # For now, use text input as fallback
        st.sidebar.info("💡 Enter the path to your company's financial data folder")
    
    company_path = st.sidebar.text_input(
        "Company Data Path",
        value=st.session_state.get('selected_company_path', ''),
        placeholder="C:/path/to/company/financial/data"
    )
    
    if company_path and company_path != st.session_state.get('selected_company_path'):
        st.session_state.selected_company_path = company_path
        load_excel_data(company_path)


def render_api_data_source():
    """Render API data source configuration."""
    st.sidebar.subheader("🌐 API Data Source")
    
    # Market selection
    market = st.sidebar.selectbox(
        "🌍 Market",
        ["US Markets", "TASE (Tel Aviv)", "Auto-Detect"],
        help="Select the stock market for ticker lookup"
    )
    st.session_state.market_selection = market
    
    # Ticker input
    ticker = st.sidebar.text_input(
        "📈 Ticker Symbol",
        value=st.session_state.get('selected_ticker', ''),
        placeholder="AAPL, MSFT, GOOGL...",
        help="Enter stock ticker symbol"
    ).upper().strip()
    
    # API source preference
    api_source = st.sidebar.selectbox(
        "🔌 API Source",
        ["yfinance", "fmp", "alpha_vantage", "polygon"],
        help="Choose preferred data provider"
    )
    st.session_state.preferred_api_source = api_source
    
    # Load data button
    if st.sidebar.button("📊 Load Data", type="primary", disabled=not ticker):
        if ticker != st.session_state.get('selected_ticker'):
            st.session_state.selected_ticker = ticker
            load_api_data(ticker, market, api_source)


def render_auto_detect_source():
    """Render auto-detect data source configuration."""
    st.sidebar.subheader("🔍 Auto-Detect Mode")
    st.sidebar.info("""
    **Auto-Detection Logic:**
    1. Check for ticker symbol format
    2. Search for Excel files in current directory
    3. Use best available data source
    """)
    
    search_input = st.sidebar.text_input(
        "🔍 Company Name or Ticker",
        placeholder="Apple Inc. or AAPL",
        help="Enter company name or ticker for automatic detection"
    )
    
    if st.sidebar.button("🚀 Auto-Load", type="primary", disabled=not search_input):
        auto_load_data(search_input)


def render_advanced_settings():
    """Render advanced configuration settings."""
    if st.sidebar.button("⚙️ Advanced Settings"):
        st.session_state.show_advanced_settings = not st.session_state.show_advanced_settings
    
    if st.session_state.show_advanced_settings:
        st.sidebar.subheader("⚙️ Advanced Configuration")
        
        # Calculation preferences
        st.sidebar.selectbox(
            "FCF Type Preference", 
            ["FCFE", "FCFF", "Levered FCF"],
            help="Default free cash flow calculation method"
        )
        
        # Data refresh options
        st.sidebar.checkbox(
            "Auto-refresh data",
            help="Automatically refresh API data on app load"
        )
        
        # Export preferences
        st.sidebar.text_input(
            "Export Directory",
            value="exports",
            help="Default directory for exported reports"
        )


def render_data_quality_panel():
    """Render data quality and status information."""
    st.sidebar.subheader("📊 Data Quality")
    
    if st.session_state.financial_calculator:
        metrics = get_data_quality_metrics(st.session_state.financial_calculator)
        
        # Quality score
        quality_score = metrics.get('quality_score', 0)
        if quality_score >= 80:
            st.sidebar.success(f"✅ Quality Score: {quality_score:.1f}%")
        elif quality_score >= 60:
            st.sidebar.warning(f"⚠️ Quality Score: {quality_score:.1f}%")
        else:
            st.sidebar.error(f"❌ Quality Score: {quality_score:.1f}%")
        
        # Coverage information
        coverage_years = metrics.get('coverage_years', 0)
        st.sidebar.info(f"📅 Data Coverage: {coverage_years} years")
        
        # Data source
        data_source = metrics.get('data_source', 'Unknown')
        st.sidebar.info(f"🔌 Source: {data_source}")


def load_excel_data(company_path: str):
    """Load data from Excel files."""
    try:
        with st.sidebar.status("Loading Excel data...") as status:
            calculator, message = centralized_data_loader(company_path=company_path)
            
            if calculator:
                st.session_state.financial_calculator = calculator
                st.session_state.company_folder = company_path
                status.update(label="✅ Excel data loaded successfully!")
                st.sidebar.success(message)
            else:
                status.update(label="❌ Failed to load Excel data")
                st.sidebar.error(message)
                
    except Exception as e:
        st.sidebar.error(f"Error loading Excel data: {str(e)}")


def load_api_data(ticker: str, market: str, api_source: str):
    """Load data from API sources."""
    try:
        with st.sidebar.status(f"Loading data for {ticker}...") as status:
            calculator, message = centralized_data_loader(
                ticker_symbol=ticker,
            )
            
            if calculator:
                st.session_state.financial_calculator = calculator
                st.session_state.selected_ticker = ticker
                status.update(label=f"✅ Data loaded for {ticker}")
                st.sidebar.success(message)
            else:
                status.update(label=f"❌ Failed to load data for {ticker}")
                st.sidebar.error(message)
                
    except Exception as e:
        st.sidebar.error(f"Error loading API data: {str(e)}")


def auto_load_data(search_input: str):
    """Auto-detect and load data from best available source."""
    try:
        with st.sidebar.status("Auto-detecting data source...") as status:
            # Simple heuristic: if it looks like a ticker, try API first
            if len(search_input) <= 5 and search_input.replace('.', '').isalpha():
                calculator, message = centralized_data_loader(ticker_symbol=search_input)
            else:
                # Try as company name / path
                calculator, message = centralized_data_loader(company_path=search_input)
            
            if calculator:
                st.session_state.financial_calculator = calculator
                status.update(label="✅ Data loaded successfully!")
                st.sidebar.success(message)
            else:
                status.update(label="❌ Auto-detection failed")
                st.sidebar.error(message)
                
    except Exception as e:
        st.sidebar.error(f"Auto-detection error: {str(e)}")


def render_welcome():
    """Render welcome screen when no data is loaded."""
    st.header("👋 Welcome to Financial Analysis Tool")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        ### 🚀 Get Started
        
        **Choose your data source from the sidebar:**
        
        📁 **Excel Files** - Upload financial statements  
        🌐 **API Data** - Enter a ticker symbol  
        🔍 **Auto-Detect** - Let us find your data  
        
        ### 📊 Available Analysis
        
        ✅ **FCF Analysis** - Free Cash Flow trends  
        ✅ **DCF Valuation** - Company valuation model  
        ✅ **DDM Analysis** - Dividend discount model  
        ✅ **P/B Analysis** - Price-to-book analysis  
        ✅ **Reports** - Export comprehensive analysis  
        ✅ **Watch Lists** - Monitor multiple companies  
        
        ---
        
        💡 **Pro Tip**: Start with a familiar ticker like AAPL or MSFT to explore the features!
        """)


def main():
    """Main application entry point with improved architecture."""
    # Initialize application state
    initialize_session_state()
    
    # Render sidebar for data configuration
    render_sidebar()
    
    # Main content area
    if not st.session_state.get('financial_calculator'):
        render_welcome()
    else:
        # Create analysis tabs
        tabs = st.tabs([
            "📈 FCF Analysis",
            "💰 DCF Valuation", 
            "🏆 DDM Analysis",
            "📊 P/B Analysis",
            "📄 Generate Report",
            "📊 Watch Lists",
            "📚 Help & Guide"
        ])
        
        with tabs[0]:
            render_fcf_analysis_placeholder()
        
        with tabs[1]:
            render_dcf_analysis()
        
        with tabs[2]:
            render_ddm_analysis_placeholder()
        
        with tabs[3]:
            render_pb_analysis_placeholder()
        
        with tabs[4]:
            render_report_generation_placeholder()
        
        with tabs[5]:
            render_watch_lists_placeholder()
        
        with tabs[6]:
            render_help_guide()


def render_fcf_analysis_placeholder():
    """Placeholder for FCF analysis tab."""
    st.header("📈 Free Cash Flow Analysis")
    st.info("🚧 FCF Analysis implementation would be moved here from the original file")
    
    if st.session_state.financial_calculator:
        st.success("✅ Financial data loaded - Ready for FCF analysis")
        # Here would be the actual FCF analysis implementation


# DCF analysis implemented in fcf_analysis_streamlit.py


def render_ddm_analysis_placeholder():
    """Placeholder for DDM analysis tab."""
    st.header("🏆 DDM Analysis") 
    st.info("🚧 DDM Analysis implementation would be moved here from the original file")


def render_pb_analysis_placeholder():
    """Placeholder for P/B analysis tab."""
    st.header("📊 P/B Analysis")
    st.info("🚧 P/B Analysis implementation would be moved here from the original file")


def render_report_generation_placeholder():
    """Placeholder for report generation tab."""
    st.header("📄 Generate Report")
    st.info("🚧 Report generation implementation would be moved here from the original file")


def render_watch_lists_placeholder():
    """Placeholder for watch lists tab."""
    st.header("📊 Watch Lists")
    st.info("🚧 Watch Lists implementation would be moved here from the original file")


if __name__ == "__main__":
    main()