"""
Portfolio Management UI Components
=================================

This module provides comprehensive portfolio management interface components
for the Streamlit application, integrating with the portfolio persistence system
and providing full CRUD operations for portfolios.

Key Features:
- Complete portfolio creation interface with data validation
- Portfolio listing and management with search/filter
- Portfolio editing and update functionality
- Holdings management with real-time data integration
- Import/export capabilities
- Integration with existing portfolio analytics and visualization
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
import logging
import uuid

# Import portfolio models and persistence
from core.analysis.portfolio.portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType, RebalancingStrategy,
    PositionSizingMethod, create_sample_portfolio, validate_portfolio
)
from core.analysis.portfolio.portfolio_persistence import (
    get_portfolio_manager, save_portfolio, load_portfolio,
    list_portfolios, delete_portfolio
)
from core.data_processing.data_contracts import CurrencyCode, MetadataInfo

logger = logging.getLogger(__name__)


def render_comprehensive_portfolio_creation_interface():
    """
    Render comprehensive portfolio creation interface with full functionality
    """
    st.markdown("#### 🆕 Create New Portfolio")

    # Initialize session state for holdings if not exists
    if 'new_portfolio_holdings' not in st.session_state:
        st.session_state.new_portfolio_holdings = []

    # Portfolio basic information section
    st.markdown("##### 📋 Portfolio Information")

    col1, col2 = st.columns(2)

    with col1:
        portfolio_name = st.text_input(
            "Portfolio Name*:",
            placeholder="e.g., My Growth Portfolio",
            help="Enter a descriptive name for your portfolio",
            key="portfolio_name_input"
        )

        portfolio_description = st.text_area(
            "Description:",
            placeholder="Optional description of your investment strategy and goals",
            help="Describe your portfolio strategy, goals, and any relevant notes",
            key="portfolio_description_input"
        )

        portfolio_type = st.selectbox(
            "Portfolio Strategy*:",
            options=[ptype.value for ptype in PortfolioType],
            format_func=lambda x: x.replace('_', ' ').title(),
            help="Select the investment strategy for your portfolio",
            key="portfolio_type_input"
        )

    with col2:
        initial_capital = st.number_input(
            "Initial Capital ($)*:",
            min_value=1000.0,
            max_value=100000000.0,
            value=100000.0,
            step=1000.0,
            help="Enter the initial capital amount",
            key="initial_capital_input"
        )

        base_currency = st.selectbox(
            "Base Currency*:",
            options=[currency.value for currency in CurrencyCode],
            index=0,  # USD by default
            help="Select the portfolio base currency",
            key="base_currency_input"
        )

        # Portfolio strategy settings
        rebalancing_strategy = st.selectbox(
            "Rebalancing Strategy:",
            options=[strategy.value for strategy in RebalancingStrategy],
            format_func=lambda x: x.replace('_', ' ').title(),
            help="Choose how you want to rebalance the portfolio",
            key="rebalancing_strategy_input"
        )

    # Portfolio constraints section
    st.markdown("##### ⚙️ Portfolio Constraints")

    col1, col2, col3 = st.columns(3)

    with col1:
        max_position_weight = st.slider(
            "Max Position Weight (%):",
            min_value=5.0,
            max_value=50.0,
            value=20.0,
            step=1.0,
            help="Maximum weight for any single position",
            key="max_position_weight_input"
        ) / 100

    with col2:
        min_position_weight = st.slider(
            "Min Position Weight (%):",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="Minimum weight for any position",
            key="min_position_weight_input"
        ) / 100

    with col3:
        target_cash_allocation = st.slider(
            "Target Cash Allocation (%):",
            min_value=0.0,
            max_value=20.0,
            value=5.0,
            step=0.5,
            help="Target percentage to hold in cash",
            key="target_cash_allocation_input"
        ) / 100

    # Holdings management section
    st.markdown("##### 📈 Portfolio Holdings")

    # Method selection for adding holdings
    input_method = st.radio(
        "How would you like to add holdings?",
        options=["Manual Entry", "Import from Watch List", "Upload CSV"],
        horizontal=True,
        key="holdings_input_method"
    )

    if input_method == "Manual Entry":
        render_enhanced_manual_holdings_input()
    elif input_method == "Import from Watch List":
        render_enhanced_watchlist_import()
    else:  # Upload CSV
        render_enhanced_csv_upload_interface()

    # Display current holdings with validation
    if st.session_state.new_portfolio_holdings:
        st.markdown("##### 📊 Current Holdings Preview")

        # Calculate current allocations
        total_value = sum(h.get('market_value', 0) for h in st.session_state.new_portfolio_holdings)

        holdings_data = []
        for holding in st.session_state.new_portfolio_holdings:
            current_weight = (holding.get('market_value', 0) / total_value * 100) if total_value > 0 else 0
            holdings_data.append({
                'Ticker': holding['ticker'],
                'Company': holding.get('company_name', 'N/A'),
                'Shares': holding['shares'],
                'Price': f"${holding.get('current_price', 0):.2f}",
                'Market Value': f"${holding.get('market_value', 0):,.0f}",
                'Target Weight': f"{holding['target_weight']*100:.1f}%",
                'Current Weight': f"{current_weight:.1f}%"
            })

        holdings_df = pd.DataFrame(holdings_data)
        st.dataframe(holdings_df, use_container_width=True)

        # Validation warnings
        total_target_weight = sum(h['target_weight'] for h in st.session_state.new_portfolio_holdings)
        available_weight = 1.0 - target_cash_allocation

        if abs(total_target_weight - available_weight) > 0.01:
            st.warning(f"⚠️ Target weights sum to {total_target_weight:.1%}, should sum to {available_weight:.1%}")

        if len(st.session_state.new_portfolio_holdings) < 3:
            st.info("💡 Consider adding more holdings for better diversification")

    # Portfolio creation section
    st.markdown("##### 🚀 Create Portfolio")

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if st.button("🚀 Create Portfolio", type="primary", key="create_portfolio_btn"):
            create_portfolio_result = _create_portfolio_from_inputs(
                portfolio_name, portfolio_description, portfolio_type,
                initial_capital, base_currency, rebalancing_strategy,
                max_position_weight, min_position_weight, target_cash_allocation
            )

            if create_portfolio_result:
                st.success("✅ Portfolio created successfully!")
                st.balloons()

                # Clear session state
                st.session_state.new_portfolio_holdings = []

                # Suggest next steps
                st.info("💡 You can now view and analyze your portfolio in the 'View Existing' and 'Analyze Portfolio' tabs.")

                # Auto-refresh the page to show the new portfolio
                st.rerun()
            else:
                st.error("❌ Failed to create portfolio. Please check your inputs.")

    with col2:
        if st.button("🔄 Reset Form", key="reset_portfolio_form"):
            st.session_state.new_portfolio_holdings = []
            st.rerun()

    with col3:
        if st.session_state.new_portfolio_holdings:
            # Export holdings as template
            holdings_template = pd.DataFrame([{
                'ticker': h['ticker'],
                'shares': h['shares'],
                'target_weight': h['target_weight']
            } for h in st.session_state.new_portfolio_holdings])

            csv_template = holdings_template.to_csv(index=False)
            st.download_button(
                "📥 Export Template",
                data=csv_template,
                file_name="portfolio_holdings_template.csv",
                mime="text/csv",
                help="Download current holdings as CSV template"
            )


def render_enhanced_manual_holdings_input():
    """Enhanced manual holdings input with real-time price fetching"""
    st.markdown("##### ✏️ Manual Holdings Entry")

    # Holdings input form
    with st.form("add_holding_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            ticker = st.text_input(
                "Ticker Symbol*",
                placeholder="AAPL",
                help="Enter the stock ticker symbol"
            ).upper().strip()

        with col2:
            shares = st.number_input(
                "Shares*",
                min_value=0.001,
                value=100.0,
                step=1.0,
                help="Number of shares to hold"
            )

        with col3:
            target_weight = st.number_input(
                "Target Weight (%)*",
                min_value=0.1,
                max_value=100.0,
                value=10.0,
                step=0.1,
                help="Target allocation percentage"
            )

        with col4:
            add_holding = st.form_submit_button("➕ Add Holding", type="primary")

        # Optional fields
        company_name = st.text_input(
            "Company Name (Optional)",
            placeholder="Apple Inc.",
            help="Company name for display purposes"
        )

        manual_price = st.number_input(
            "Manual Price (Optional, $)",
            min_value=0.01,
            value=0.0,
            step=0.01,
            help="Enter manual price or leave 0 to fetch automatically"
        )

        if add_holding and ticker and shares > 0 and target_weight > 0:
            success = _add_holding_to_session(
                ticker, shares, target_weight/100, company_name, manual_price
            )
            if success:
                st.success(f"✅ Added {ticker} to portfolio")
                st.rerun()
            else:
                st.error(f"❌ Failed to add {ticker}. It may already exist in the portfolio.")


def render_enhanced_watchlist_import():
    """Enhanced watch list import interface with integration"""
    st.markdown("##### 📊 Import from Watch List")

    try:
        # Try to import watch list functionality
        from core.data_sources.watch_list_manager import WatchListManager

        watch_manager = WatchListManager()
        available_lists = watch_manager.list_watch_lists()

        if available_lists:
            selected_list = st.selectbox(
                "Select Watch List:",
                options=available_lists,
                help="Choose a watch list to import holdings from"
            )

            if selected_list:
                watch_list_data = watch_manager.get_watch_list(selected_list)

                if watch_list_data and 'companies' in watch_list_data:
                    st.markdown(f"**{selected_list}** contains {len(watch_list_data['companies'])} companies:")

                    # Show preview
                    preview_data = []
                    for company in watch_list_data['companies'][:10]:  # Show first 10
                        preview_data.append({
                            'Ticker': company.get('ticker', 'N/A'),
                            'Company': company.get('company_name', 'N/A')
                        })

                    if preview_data:
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True)

                        if len(watch_list_data['companies']) > 10:
                            st.info(f"... and {len(watch_list_data['companies']) - 10} more companies")

                    # Import options
                    col1, col2 = st.columns(2)

                    with col1:
                        equal_weight = st.checkbox(
                            "Equal Weight All Holdings",
                            value=True,
                            help="Assign equal weight to all imported holdings"
                        )

                    with col2:
                        default_shares = st.number_input(
                            "Default Shares per Holding:",
                            min_value=1,
                            value=100,
                            step=1,
                            help="Default number of shares for each holding"
                        )

                    if st.button("📥 Import from Watch List", type="primary"):
                        imported_count = _import_from_watchlist(
                            watch_list_data['companies'], equal_weight, default_shares
                        )

                        if imported_count > 0:
                            st.success(f"✅ Imported {imported_count} holdings from {selected_list}")
                            st.rerun()
                        else:
                            st.warning("⚠️ No new holdings were imported")
                else:
                    st.warning("⚠️ Selected watch list is empty")
        else:
            st.info("💡 No watch lists found. Create a watch list first to import holdings.")

    except ImportError:
        st.warning("⚠️ Watch list functionality not available. Use manual entry or CSV upload instead.")
    except Exception as e:
        logger.error(f"Error accessing watch lists: {e}")
        st.error("❌ Error accessing watch lists")


def render_enhanced_csv_upload_interface():
    """Enhanced CSV upload interface with validation and preview"""
    st.markdown("##### 📁 Upload Holdings CSV")

    # Show expected format with detailed explanation
    with st.expander("📖 CSV Format Requirements", expanded=True):
        st.markdown("""
        **Required Columns:**
        - `ticker`: Stock ticker symbol (e.g., AAPL, MSFT)
        - `shares`: Number of shares (decimal allowed)
        - `target_weight`: Target allocation as decimal (0.15 = 15%)

        **Optional Columns:**
        - `company_name`: Company display name
        - `current_price`: Manual price override
        - `sector`: Company sector classification
        """)

        # Show sample data
        sample_data = pd.DataFrame({
            'ticker': ['AAPL', 'MSFT', 'GOOGL', 'AMZN'],
            'shares': [100, 50, 25, 30],
            'target_weight': [0.25, 0.25, 0.25, 0.25],
            'company_name': ['Apple Inc.', 'Microsoft Corp.', 'Alphabet Inc.', 'Amazon.com Inc.'],
            'sector': ['Technology', 'Technology', 'Technology', 'Consumer Discretionary']
        })
        st.dataframe(sample_data, use_container_width=True)

        # Download template
        csv_template = sample_data.to_csv(index=False)
        st.download_button(
            "📥 Download Template",
            data=csv_template,
            file_name="portfolio_holdings_template.csv",
            mime="text/csv",
            help="Download CSV template with sample data"
        )

    # File upload
    uploaded_file = st.file_uploader(
        "Choose CSV file",
        type=['csv'],
        help="Upload a CSV file with holdings data",
        key="portfolio_csv_upload"
    )

    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file)

            # Validate required columns
            required_columns = ['ticker', 'shares', 'target_weight']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                return

            # Validate data types and ranges
            validation_errors = []

            # Check for empty tickers
            if df['ticker'].isna().any() or (df['ticker'] == '').any():
                validation_errors.append("Some ticker symbols are empty")

            # Check shares are positive
            if (df['shares'] <= 0).any():
                validation_errors.append("All shares must be positive numbers")

            # Check target weights are valid
            if (df['target_weight'] <= 0).any() or (df['target_weight'] > 1).any():
                validation_errors.append("Target weights must be between 0 and 1")

            # Check total target weight
            total_weight = df['target_weight'].sum()
            if total_weight > 1.0:
                validation_errors.append(f"Total target weight ({total_weight:.2f}) exceeds 100%")

            if validation_errors:
                st.error("❌ Validation Errors:")
                for error in validation_errors:
                    st.error(f"  • {error}")
                return

            # Show preview
            st.success("✅ CSV format is valid")
            st.markdown("**Preview:**")

            # Add calculated columns for preview
            preview_df = df.copy()
            preview_df['Target Weight (%)'] = preview_df['target_weight'] * 100

            # Show relevant columns
            display_columns = ['ticker', 'shares', 'Target Weight (%)']
            if 'company_name' in df.columns:
                display_columns.insert(1, 'company_name')
            if 'sector' in df.columns:
                display_columns.append('sector')

            st.dataframe(preview_df[display_columns], use_container_width=True)

            # Import button
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📥 Import Holdings", type="primary", key="import_csv_holdings"):
                    imported_count = _import_from_csv(df)

                    if imported_count > 0:
                        st.success(f"✅ Imported {imported_count} holdings from CSV")
                        st.rerun()
                    else:
                        st.warning("⚠️ No new holdings were imported")

            with col2:
                replace_existing = st.checkbox(
                    "Replace Existing Holdings",
                    help="Clear current holdings before importing CSV data"
                )

                if replace_existing and st.button("🔄 Replace & Import", key="replace_import_csv"):
                    st.session_state.new_portfolio_holdings = []
                    imported_count = _import_from_csv(df)

                    if imported_count > 0:
                        st.success(f"✅ Replaced with {imported_count} holdings from CSV")
                        st.rerun()
                    else:
                        st.error("❌ Failed to import holdings")

        except Exception as e:
            st.error(f"❌ Error reading CSV: {str(e)}")
            logger.error(f"CSV upload error: {e}")


def render_comprehensive_existing_portfolios_interface():
    """
    Render comprehensive interface for viewing and managing existing portfolios
    """
    st.markdown("#### 📋 Portfolio Manager")

    try:
        # Get all portfolios
        portfolio_list = list_portfolios()

        if not portfolio_list:
            st.info("💡 No portfolios found. Create your first portfolio in the 'Create Portfolio' tab.")

            # Show sample portfolio option
            if st.button("🎯 Create Sample Portfolio", type="primary"):
                sample_portfolio = create_sample_portfolio()
                if save_portfolio(sample_portfolio):
                    st.success("✅ Sample portfolio created successfully!")
                    st.rerun()
                else:
                    st.error("❌ Failed to create sample portfolio")
            return

        # Portfolio search and filter
        st.markdown("##### 🔍 Search & Filter")

        col1, col2, col3 = st.columns(3)

        with col1:
            search_term = st.text_input(
                "Search Portfolios:",
                placeholder="Enter portfolio name...",
                key="portfolio_search"
            )

        with col2:
            type_filter = st.selectbox(
                "Filter by Type:",
                options=["All"] + [ptype.value for ptype in PortfolioType],
                format_func=lambda x: x.replace('_', ' ').title() if x != "All" else x,
                key="portfolio_type_filter"
            )

        with col3:
            sort_by = st.selectbox(
                "Sort by:",
                options=["Last Updated", "Name", "Total Value", "Creation Date"],
                key="portfolio_sort"
            )

        # Apply filters
        filtered_portfolios = _filter_portfolios(portfolio_list, search_term, type_filter, sort_by)

        # Portfolio list display
        st.markdown(f"##### 📊 Portfolio List ({len(filtered_portfolios)} found)")

        for i, portfolio_summary in enumerate(filtered_portfolios):
            with st.container():
                # Portfolio card
                col1, col2, col3, col4 = st.columns([3, 2, 2, 3])

                with col1:
                    st.markdown(f"**{portfolio_summary['name']}**")
                    st.caption(portfolio_summary.get('description', 'No description'))

                with col2:
                    st.metric(
                        "Total Value",
                        f"${portfolio_summary.get('total_value', 0):,.0f}"
                    )

                with col3:
                    st.metric(
                        "Holdings",
                        portfolio_summary.get('holdings_count', 0)
                    )

                with col4:
                    # Action buttons
                    button_col1, button_col2, button_col3 = st.columns(3)

                    with button_col1:
                        if st.button("👁️ View", key=f"view_{portfolio_summary['portfolio_id']}_{i}"):
                            _show_portfolio_details(portfolio_summary['portfolio_id'])

                    with button_col2:
                        if st.button("📊 Analyze", key=f"analyze_{portfolio_summary['portfolio_id']}_{i}"):
                            portfolio = load_portfolio(portfolio_summary['portfolio_id'])
                            if portfolio:
                                st.session_state.selected_portfolio_for_analysis = portfolio
                                st.success(f"✅ Selected '{portfolio.name}' for analysis")
                                st.info("💡 Go to the 'Analyze Portfolio' tab to view detailed analysis")

                    with button_col3:
                        if st.button("🗑️ Delete", key=f"delete_{portfolio_summary['portfolio_id']}_{i}"):
                            if st.session_state.get(f"confirm_delete_{portfolio_summary['portfolio_id']}", False):
                                if delete_portfolio(portfolio_summary['portfolio_id']):
                                    st.success(f"✅ Deleted '{portfolio_summary['name']}'")
                                    st.rerun()
                                else:
                                    st.error("❌ Failed to delete portfolio")
                            else:
                                st.session_state[f"confirm_delete_{portfolio_summary['portfolio_id']}"] = True
                                st.warning("⚠️ Click delete again to confirm")

                st.markdown("---")

        # Bulk operations
        if len(filtered_portfolios) > 1:
            st.markdown("##### ⚙️ Bulk Operations")

            col1, col2, col3 = st.columns(3)

            with col1:
                if st.button("📥 Export All", key="export_all_portfolios"):
                    _export_all_portfolios(filtered_portfolios)

            with col2:
                if st.button("📊 Compare Selected", key="compare_portfolios"):
                    st.info("💡 Portfolio comparison feature coming soon")

            with col3:
                if st.button("🔄 Refresh List", key="refresh_portfolio_list"):
                    st.rerun()

        # Storage statistics
        _show_storage_statistics()

    except Exception as e:
        logger.error(f"Error rendering existing portfolios interface: {e}")
        st.error("❌ Error loading portfolios")


def render_comprehensive_portfolio_analysis_interface():
    """
    Render comprehensive portfolio analysis interface with full visualization integration
    """
    st.markdown("#### 📈 Portfolio Analysis Dashboard")

    # Portfolio selection
    if 'selected_portfolio_for_analysis' not in st.session_state:
        st.session_state.selected_portfolio_for_analysis = None

    # Portfolio selector
    try:
        portfolio_list = list_portfolios()

        if not portfolio_list:
            st.info("💡 No portfolios found. Create a portfolio first to analyze.")
            return

        # Portfolio selection dropdown
        col1, col2 = st.columns([3, 1])

        with col1:
            portfolio_options = {p['portfolio_id']: f"{p['name']} (${p.get('total_value', 0):,.0f})"
                               for p in portfolio_list}

            selected_portfolio_id = st.selectbox(
                "Select Portfolio to Analyze:",
                options=list(portfolio_options.keys()),
                format_func=lambda x: portfolio_options[x],
                key="analysis_portfolio_selector"
            )

        with col2:
            if st.button("🔄 Load Portfolio", type="primary"):
                portfolio = load_portfolio(selected_portfolio_id)
                if portfolio:
                    st.session_state.selected_portfolio_for_analysis = portfolio
                    st.success(f"✅ Loaded '{portfolio.name}'")
                    st.rerun()
                else:
                    st.error("❌ Failed to load portfolio")

        # Load portfolio if not in session state
        if (st.session_state.selected_portfolio_for_analysis is None and
            selected_portfolio_id):
            portfolio = load_portfolio(selected_portfolio_id)
            if portfolio:
                st.session_state.selected_portfolio_for_analysis = portfolio

        # Analysis interface
        if st.session_state.selected_portfolio_for_analysis:
            portfolio = st.session_state.selected_portfolio_for_analysis

            # Portfolio overview
            st.markdown("##### 📊 Portfolio Overview")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                total_value = sum(h.market_value or 0 for h in portfolio.holdings)
                st.metric("Total Value", f"${total_value:,.0f}")

            with col2:
                st.metric("Holdings", len(portfolio.holdings))

            with col3:
                portfolio_type = portfolio.portfolio_type.value.replace('_', ' ').title()
                st.metric("Strategy", portfolio_type)

            with col4:
                if portfolio.inception_date:
                    days_old = (date.today() - portfolio.inception_date).days
                    st.metric("Age (Days)", days_old)
                else:
                    st.metric("Age", "N/A")

            # Analysis options
            st.markdown("##### 🔧 Analysis Options")

            analysis_type = st.radio(
                "Select Analysis Type:",
                options=[
                    "Complete Dashboard",
                    "Allocation Analysis",
                    "Performance Metrics",
                    "Risk Analysis",
                    "Holdings Detail"
                ],
                horizontal=True,
                key="analysis_type_selector"
            )

            # Render analysis based on selection
            if analysis_type == "Complete Dashboard":
                # Use the existing comprehensive portfolio visualization
                from ui.streamlit.portfolio_visualization import render_portfolio_visualization_dashboard
                render_portfolio_visualization_dashboard(portfolio)

            elif analysis_type == "Allocation Analysis":
                _render_allocation_analysis(portfolio)

            elif analysis_type == "Performance Metrics":
                _render_performance_analysis(portfolio)

            elif analysis_type == "Risk Analysis":
                _render_risk_analysis(portfolio)

            elif analysis_type == "Holdings Detail":
                _render_holdings_detail(portfolio)

            # Portfolio management actions
            st.markdown("##### ⚙️ Portfolio Actions")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("📝 Edit Portfolio", key="edit_portfolio_btn"):
                    st.info("💡 Portfolio editing feature coming soon")

            with col2:
                if st.button("🔄 Rebalance", key="rebalance_portfolio_btn"):
                    _show_rebalancing_recommendations(portfolio)

            with col3:
                if st.button("📥 Export Data", key="export_portfolio_btn"):
                    _export_portfolio_data(portfolio)

            with col4:
                if st.button("📊 Generate Report", key="generate_report_btn"):
                    st.info("💡 Report generation feature coming soon")

        else:
            st.info("💡 Select a portfolio to begin analysis")

    except Exception as e:
        logger.error(f"Error rendering portfolio analysis interface: {e}")
        st.error("❌ Error loading portfolio analysis")


# Helper functions for the UI components

def _create_portfolio_from_inputs(
    name: str, description: str, portfolio_type: str,
    initial_capital: float, base_currency: str, rebalancing_strategy: str,
    max_position_weight: float, min_position_weight: float, target_cash_allocation: float
) -> bool:
    """Create portfolio from UI inputs"""
    try:
        if not name or not name.strip():
            st.error("❌ Portfolio name is required")
            return False

        if not st.session_state.new_portfolio_holdings:
            st.error("❌ Please add at least one holding")
            return False

        # Generate unique ID
        portfolio_id = f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        # Create holdings
        holdings = []
        for holding_data in st.session_state.new_portfolio_holdings:
            holding = PortfolioHolding(
                ticker=holding_data['ticker'],
                company_name=holding_data.get('company_name'),
                shares=holding_data['shares'],
                current_price=holding_data.get('current_price'),
                market_value=holding_data.get('market_value'),
                target_weight=holding_data['target_weight']
            )
            holdings.append(holding)

        # Create portfolio
        portfolio = Portfolio(
            portfolio_id=portfolio_id,
            name=name.strip(),
            description=description.strip() if description else None,
            portfolio_type=PortfolioType(portfolio_type),
            base_currency=CurrencyCode(base_currency),
            rebalancing_strategy=RebalancingStrategy(rebalancing_strategy),
            holdings=holdings,
            cash_position=initial_capital * target_cash_allocation,
            target_cash_allocation=target_cash_allocation,
            max_position_weight=max_position_weight,
            min_position_weight=min_position_weight,
            inception_date=date.today()
        )

        # Validate portfolio
        validation_errors = validate_portfolio(portfolio)
        if validation_errors:
            st.error("❌ Portfolio validation failed:")
            for error in validation_errors:
                st.error(f"  • {error}")
            return False

        # Save portfolio
        return save_portfolio(portfolio)

    except Exception as e:
        logger.error(f"Error creating portfolio: {e}")
        st.error(f"❌ Error creating portfolio: {str(e)}")
        return False


def _add_holding_to_session(
    ticker: str, shares: float, target_weight: float,
    company_name: str = None, manual_price: float = 0.0
) -> bool:
    """Add holding to session state with validation"""
    try:
        # Check for duplicates
        existing_tickers = [h['ticker'] for h in st.session_state.new_portfolio_holdings]
        if ticker in existing_tickers:
            return False

        # Try to fetch current price if not provided
        current_price = manual_price if manual_price > 0 else _fetch_current_price(ticker)
        market_value = shares * current_price if current_price > 0 else 0

        holding_data = {
            'ticker': ticker,
            'company_name': company_name or ticker,
            'shares': shares,
            'target_weight': target_weight,
            'current_price': current_price,
            'market_value': market_value
        }

        st.session_state.new_portfolio_holdings.append(holding_data)
        return True

    except Exception as e:
        logger.error(f"Error adding holding {ticker}: {e}")
        return False


def _fetch_current_price(ticker: str) -> float:
    """Fetch current price for a ticker (placeholder implementation)"""
    try:
        # This would integrate with the existing price service
        # For now, return a placeholder price
        import random
        return random.uniform(50, 300)  # Mock price
    except Exception:
        return 0.0


def _import_from_watchlist(companies: List[Dict], equal_weight: bool, default_shares: int) -> int:
    """Import holdings from watch list"""
    try:
        imported_count = 0
        existing_tickers = [h['ticker'] for h in st.session_state.new_portfolio_holdings]

        weight_per_holding = (1.0 / len(companies)) if equal_weight else 0.1

        for company in companies:
            ticker = company.get('ticker', '').upper().strip()
            if not ticker or ticker in existing_tickers:
                continue

            current_price = _fetch_current_price(ticker)
            market_value = default_shares * current_price if current_price > 0 else 0

            holding_data = {
                'ticker': ticker,
                'company_name': company.get('company_name', ticker),
                'shares': default_shares,
                'target_weight': weight_per_holding,
                'current_price': current_price,
                'market_value': market_value
            }

            st.session_state.new_portfolio_holdings.append(holding_data)
            imported_count += 1

        return imported_count

    except Exception as e:
        logger.error(f"Error importing from watchlist: {e}")
        return 0


def _import_from_csv(df: pd.DataFrame) -> int:
    """Import holdings from CSV DataFrame"""
    try:
        imported_count = 0
        existing_tickers = [h['ticker'] for h in st.session_state.new_portfolio_holdings]

        for _, row in df.iterrows():
            ticker = str(row['ticker']).upper().strip()
            if not ticker or ticker in existing_tickers:
                continue

            shares = float(row['shares'])
            target_weight = float(row['target_weight'])
            company_name = row.get('company_name', ticker)
            manual_price = float(row.get('current_price', 0))

            current_price = manual_price if manual_price > 0 else _fetch_current_price(ticker)
            market_value = shares * current_price if current_price > 0 else 0

            holding_data = {
                'ticker': ticker,
                'company_name': company_name,
                'shares': shares,
                'target_weight': target_weight,
                'current_price': current_price,
                'market_value': market_value
            }

            st.session_state.new_portfolio_holdings.append(holding_data)
            imported_count += 1

        return imported_count

    except Exception as e:
        logger.error(f"Error importing from CSV: {e}")
        return 0


def _filter_portfolios(
    portfolio_list: List[Dict], search_term: str, type_filter: str, sort_by: str
) -> List[Dict]:
    """Filter and sort portfolio list"""
    try:
        filtered = portfolio_list.copy()

        # Apply search filter
        if search_term:
            filtered = [p for p in filtered
                       if search_term.lower() in p['name'].lower()]

        # Apply type filter
        if type_filter != "All":
            filtered = [p for p in filtered
                       if p.get('portfolio_type') == type_filter]

        # Apply sorting
        if sort_by == "Name":
            filtered.sort(key=lambda x: x['name'])
        elif sort_by == "Total Value":
            filtered.sort(key=lambda x: x.get('total_value', 0), reverse=True)
        elif sort_by == "Creation Date":
            filtered.sort(key=lambda x: x.get('inception_date', ''), reverse=True)
        else:  # Last Updated
            filtered.sort(key=lambda x: x.get('last_update', ''), reverse=True)

        return filtered

    except Exception as e:
        logger.error(f"Error filtering portfolios: {e}")
        return portfolio_list


def _show_portfolio_details(portfolio_id: str):
    """Show detailed portfolio information"""
    try:
        portfolio = load_portfolio(portfolio_id)
        if not portfolio:
            st.error("❌ Failed to load portfolio details")
            return

        st.markdown(f"##### 📊 Portfolio Details: {portfolio.name}")

        # Basic information
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Portfolio Information:**")
            st.write(f"• **ID:** {portfolio.portfolio_id}")
            st.write(f"• **Type:** {portfolio.portfolio_type.value.replace('_', ' ').title()}")
            st.write(f"• **Currency:** {portfolio.base_currency.value}")
            st.write(f"• **Created:** {portfolio.inception_date}")

        with col2:
            st.markdown("**Portfolio Metrics:**")
            total_value = sum(h.market_value or 0 for h in portfolio.holdings)
            st.write(f"• **Total Value:** ${total_value:,.0f}")
            st.write(f"• **Holdings:** {len(portfolio.holdings)}")
            st.write(f"• **Cash:** ${portfolio.cash_position:,.0f}")
            st.write(f"• **Strategy:** {portfolio.rebalancing_strategy.value.replace('_', ' ').title()}")

        # Holdings summary
        if portfolio.holdings:
            st.markdown("**Holdings Summary:**")
            holdings_data = []
            for holding in portfolio.holdings:
                holdings_data.append({
                    'Ticker': holding.ticker,
                    'Company': holding.company_name or 'N/A',
                    'Shares': f"{holding.shares:,.1f}",
                    'Current Price': f"${holding.current_price or 0:.2f}",
                    'Market Value': f"${holding.market_value or 0:,.0f}",
                    'Target Weight': f"{holding.target_weight*100:.1f}%",
                    'Current Weight': f"{holding.current_weight*100:.1f}%"
                })

            st.dataframe(pd.DataFrame(holdings_data), use_container_width=True)

    except Exception as e:
        logger.error(f"Error showing portfolio details: {e}")
        st.error("❌ Error loading portfolio details")


def _show_storage_statistics():
    """Show portfolio storage statistics"""
    try:
        manager = get_portfolio_manager()
        stats = manager.get_storage_stats()

        st.markdown("##### 📊 Storage Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Portfolios", stats.get('total_portfolios', 0))

        with col2:
            size_mb = stats.get('storage_file_size', 0) / (1024 * 1024)
            st.metric("Storage Size", f"{size_mb:.2f} MB")

        with col3:
            st.metric("Backups", stats.get('backup_count', 0))

        with col4:
            st.metric("Cache Status", stats.get('cache_status', 'unknown').title())

    except Exception as e:
        logger.error(f"Error showing storage statistics: {e}")


def _render_allocation_analysis(portfolio: Portfolio):
    """Render allocation analysis section"""
    st.markdown("##### 📊 Allocation Analysis")

    # Holdings allocation table
    if portfolio.holdings:
        holdings_data = []
        total_value = sum(h.market_value or 0 for h in portfolio.holdings)

        for holding in portfolio.holdings:
            current_weight = (holding.market_value / total_value * 100) if total_value > 0 else 0
            weight_deviation = current_weight - (holding.target_weight * 100)

            holdings_data.append({
                'Ticker': holding.ticker,
                'Company': holding.company_name or 'N/A',
                'Market Value': holding.market_value or 0,
                'Target Weight (%)': holding.target_weight * 100,
                'Current Weight (%)': current_weight,
                'Deviation (%)': weight_deviation
            })

        df = pd.DataFrame(holdings_data)

        # Color code deviations
        def highlight_deviation(val):
            if abs(val) > 5:  # More than 5% deviation
                return 'background-color: #ffcccb'  # Light red
            elif abs(val) > 2:  # More than 2% deviation
                return 'background-color: #fff2cc'  # Light yellow
            else:
                return 'background-color: #d4edda'  # Light green

        styled_df = df.style.applymap(highlight_deviation, subset=['Deviation (%)'])
        st.dataframe(styled_df, use_container_width=True)

        # Summary metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            max_deviation = df['Deviation (%)'].abs().max()
            st.metric("Max Deviation", f"{max_deviation:.1f}%")

        with col2:
            avg_deviation = df['Deviation (%)'].abs().mean()
            st.metric("Avg Deviation", f"{avg_deviation:.1f}%")

        with col3:
            rebalance_needed = (df['Deviation (%)'].abs() > 5).any()
            st.metric("Rebalance Needed", "Yes" if rebalance_needed else "No")


def _render_performance_analysis(portfolio: Portfolio):
    """Render performance analysis section"""
    st.markdown("##### 📈 Performance Analysis")
    st.info("💡 Performance analysis requires historical data integration")


def _render_risk_analysis(portfolio: Portfolio):
    """Render risk analysis section"""
    st.markdown("##### ⚠️ Risk Analysis")
    st.info("💡 Risk analysis requires volatility and correlation data integration")


def _render_holdings_detail(portfolio: Portfolio):
    """Render detailed holdings information"""
    st.markdown("##### 📋 Holdings Detail")

    if not portfolio.holdings:
        st.warning("⚠️ No holdings found in this portfolio")
        return

    for i, holding in enumerate(portfolio.holdings):
        with st.expander(f"{holding.ticker} - {holding.company_name or 'N/A'}", expanded=i < 3):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Position Details:**")
                st.write(f"• **Shares:** {holding.shares:,.2f}")
                st.write(f"• **Current Price:** ${holding.current_price or 0:.2f}")
                st.write(f"• **Market Value:** ${holding.market_value or 0:,.0f}")
                st.write(f"• **Target Weight:** {holding.target_weight*100:.1f}%")
                st.write(f"• **Current Weight:** {holding.current_weight*100:.1f}%")

            with col2:
                st.markdown("**Performance:**")
                if holding.unrealized_gain_loss_pct:
                    color = "green" if holding.unrealized_gain_loss_pct > 0 else "red"
                    st.markdown(f"• **Unrealized P&L:** <span style='color:{color}'>{holding.unrealized_gain_loss_pct:+.1f}%</span>", unsafe_allow_html=True)

                if holding.total_cost:
                    st.write(f"• **Cost Basis:** ${holding.cost_basis or 0:.2f}")
                    st.write(f"• **Total Cost:** ${holding.total_cost:,.0f}")


def _show_rebalancing_recommendations(portfolio: Portfolio):
    """Show rebalancing recommendations"""
    st.markdown("##### 🔄 Rebalancing Recommendations")
    st.info("💡 Rebalancing recommendations require portfolio optimization engine integration")


def _export_portfolio_data(portfolio: Portfolio):
    """Export portfolio data"""
    try:
        manager = get_portfolio_manager()
        export_path = manager.export_portfolio(portfolio.portfolio_id, 'json')

        if export_path:
            st.success(f"✅ Portfolio exported to: {export_path}")
        else:
            st.error("❌ Failed to export portfolio")

    except Exception as e:
        logger.error(f"Error exporting portfolio: {e}")
        st.error("❌ Error exporting portfolio")


def _export_all_portfolios(portfolio_list: List[Dict]):
    """Export all portfolios"""
    st.info("💡 Bulk export feature coming soon")