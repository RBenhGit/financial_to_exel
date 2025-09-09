"""
Streamlit Performance Integration for Large Watch Lists

This module provides Streamlit UI components optimized for large watch list performance,
including lazy loading, pagination, concurrent processing, and real-time progress indicators.

Features:
- Paginated watch list display with virtual scrolling
- Real-time progress tracking for concurrent operations
- Performance metrics dashboard
- Lazy loading controls and indicators
- Memory usage monitoring
"""

import streamlit as st
import pandas as pd
import time
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from concurrent.futures import ThreadPoolExecutor

# Import performance components
from .concurrent_watch_list_optimizer import ConcurrentWatchListOptimizer, create_optimized_watch_list_manager
from core.data_processing.managers.watch_list_manager import WatchListManager
from ui.visualization.watch_list_visualizer import WatchListVisualizer

class StreamlitPerformanceIntegration:
    """
    Streamlit integration for high-performance watch list operations
    """
    
    def __init__(self):
        """Initialize the performance integration"""
        self.optimizer = None
        self.visualizer = WatchListVisualizer()
    
    def display_optimized_watch_list_section(self, watch_list_manager: WatchListManager):
        """
        Display the performance-optimized watch list section
        
        Args:
            watch_list_manager: Watch list manager instance
        """
        st.header("🚀 High-Performance Watch Lists")
        st.markdown("""
        **Optimized for Large Watch Lists (50+ stocks)**
        - ⚡ Concurrent API calls for faster loading
        - 📄 Lazy loading with pagination
        - 🧠 Memory optimization
        - 📊 Real-time performance monitoring
        """)
        
        # Initialize optimizer if needed
        if 'performance_optimizer' not in st.session_state:
            with st.spinner("Initializing performance optimizer..."):
                st.session_state.performance_optimizer = create_optimized_watch_list_manager(watch_list_manager)
        
        optimizer = st.session_state.performance_optimizer
        
        # Performance controls
        self._display_performance_controls()
        
        # Watch list selection
        watch_lists = watch_list_manager.get_all_watch_lists()
        if not watch_lists:
            st.info("📝 No watch lists found. Create a watch list first.")
            return
        
        selected_list = st.selectbox(
            "Select Watch List:",
            options=list(watch_lists.keys()),
            help="Choose a watch list to view with performance optimization"
        )
        
        if selected_list:
            # Performance mode selection
            col1, col2 = st.columns(2)
            
            with col1:
                mode = st.radio(
                    "Loading Mode:",
                    options=["Concurrent (Recommended)", "Paginated (Large Lists)", "Standard"],
                    help="Choose loading strategy based on your watch list size"
                )
            
            with col2:
                force_refresh = st.checkbox(
                    "Force Refresh Prices",
                    help="Bypass cache and fetch fresh prices from APIs"
                )
            
            # Display based on selected mode
            if mode == "Concurrent (Recommended)":
                self._display_concurrent_watch_list(optimizer, selected_list, force_refresh)
            elif mode == "Paginated (Large Lists)":
                self._display_paginated_watch_list(optimizer, selected_list)
            else:
                self._display_standard_watch_list(watch_list_manager, selected_list, force_refresh)
    
    def _display_performance_controls(self):
        """Display performance monitoring and control panel"""
        with st.expander("⚙️ Performance Controls", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🧹 Optimize Memory"):
                    if 'performance_optimizer' in st.session_state:
                        st.session_state.performance_optimizer.optimize_memory()
                        st.success("Memory optimization completed!")
            
            with col2:
                if st.button("📊 View Metrics"):
                    self._display_performance_metrics()
            
            with col3:
                if st.button("🔄 Reset Optimizer"):
                    if 'performance_optimizer' in st.session_state:
                        st.session_state.performance_optimizer.shutdown()
                        del st.session_state.performance_optimizer
                    st.success("Optimizer reset!")
                    st.rerun()
    
    def _display_concurrent_watch_list(self, optimizer: ConcurrentWatchListOptimizer, 
                                     watch_list_name: str, force_refresh: bool):
        """Display watch list with concurrent processing"""
        
        # Progress tracking
        progress_placeholder = st.empty()
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def progress_callback(completed: int, total: int):
            """Update progress in real-time"""
            progress = completed / max(total, 1)
            progress_bar.progress(progress)
            status_text.text(f"Loading prices... {completed}/{total} completed")
        
        # Load with concurrent processing
        start_time = time.time()
        
        try:
            with st.spinner("🚀 Loading watch list with concurrent optimization..."):
                watch_list_data = optimizer.get_watch_list_with_concurrent_prices(
                    watch_list_name=watch_list_name,
                    force_refresh=force_refresh,
                    progress_callback=progress_callback
                )
            
            # Clear progress indicators
            progress_placeholder.empty()
            progress_bar.empty()
            status_text.empty()
            
            if watch_list_data:
                # Display performance summary
                if 'performance_metadata' in watch_list_data:
                    self._display_performance_summary(watch_list_data['performance_metadata'])
                
                # Display watch list content
                self._display_watch_list_content(watch_list_data)
                
                # Performance visualization
                self._display_performance_charts(watch_list_data)
                
            else:
                st.error("❌ Failed to load watch list data")
                
        except Exception as e:
            st.error(f"❌ Error during concurrent loading: {str(e)}")
            progress_placeholder.empty()
            progress_bar.empty()
            status_text.empty()
    
    def _display_paginated_watch_list(self, optimizer: ConcurrentWatchListOptimizer, 
                                    watch_list_name: str):
        """Display watch list with pagination for large datasets"""
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        
        # Initialize pagination state
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1
        if 'page_size' not in st.session_state:
            st.session_state.page_size = 25
        
        with col1:
            page_size = st.selectbox(
                "Items per page:",
                options=[10, 25, 50, 100],
                index=[10, 25, 50, 100].index(st.session_state.page_size)
            )
            if page_size != st.session_state.page_size:
                st.session_state.page_size = page_size
                st.session_state.current_page = 1
        
        # Load paginated data
        with st.spinner("📄 Loading paginated data..."):
            paginated_data = optimizer.get_paginated_watch_list(
                watch_list_name=watch_list_name,
                page=st.session_state.current_page,
                page_size=st.session_state.page_size
            )
        
        if paginated_data and paginated_data.get('stocks'):
            # Pagination info
            with col2:
                st.markdown(f"""
                **Page {paginated_data['page']} of {paginated_data['total_pages']}** 
                (Showing {len(paginated_data['stocks'])} of {paginated_data['total_items']} stocks)
                """)
            
            # Pagination buttons
            with col3:
                btn_col1, btn_col2 = st.columns(2)
                with btn_col1:
                    if st.button("◀ Previous", disabled=not paginated_data['has_previous']):
                        st.session_state.current_page = max(1, st.session_state.current_page - 1)
                        st.rerun()
                
                with btn_col2:
                    if st.button("Next ▶", disabled=not paginated_data['has_next']):
                        st.session_state.current_page = min(
                            paginated_data['total_pages'],
                            st.session_state.current_page + 1
                        )
                        st.rerun()
            
            # Prefetch next pages for better UX
            if paginated_data['has_next']:
                optimizer.prefetch_pages(
                    watch_list_name, 
                    st.session_state.current_page,
                    st.session_state.page_size
                )
            
            # Display paginated content
            self._display_watch_list_content(paginated_data)
            
        else:
            st.warning("No data found for the current page.")
    
    def _display_standard_watch_list(self, watch_list_manager: WatchListManager, 
                                   watch_list_name: str, force_refresh: bool):
        """Display watch list using standard processing"""
        
        with st.spinner("📊 Loading watch list (standard mode)..."):
            watch_list_data = watch_list_manager.get_watch_list_with_current_prices(
                watch_list_name, force_refresh
            )
        
        if watch_list_data:
            st.info("💡 Using standard loading. Switch to Concurrent mode for better performance with large lists.")
            self._display_watch_list_content(watch_list_data)
        else:
            st.error("❌ Failed to load watch list data")
    
    def _display_watch_list_content(self, watch_list_data: Dict):
        """Display the main watch list content"""
        stocks = watch_list_data.get('stocks', [])
        
        if not stocks:
            st.warning("📭 No stocks found in this watch list.")
            return
        
        # Summary metrics
        self._display_watch_list_summary(stocks)
        
        # Interactive data table
        self._display_interactive_table(stocks)
        
        # Visualizations
        if len(stocks) > 1:
            self._display_watch_list_visualizations(watch_list_data)
    
    def _display_watch_list_summary(self, stocks: List[Dict]):
        """Display summary metrics for the watch list"""
        # Calculate metrics
        total_stocks = len(stocks)
        stocks_with_prices = len([s for s in stocks if s.get('current_market_price')])
        
        upside_values = [
            s.get('updated_upside_downside_pct', s.get('upside_downside_pct', 0)) 
            for s in stocks if s.get('fair_value')
        ]
        
        if upside_values:
            avg_upside = sum(upside_values) / len(upside_values)
            undervalued_count = len([u for u in upside_values if u > 5])
            overvalued_count = len([u for u in upside_values if u < -5])
        else:
            avg_upside = 0
            undervalued_count = 0
            overvalued_count = 0
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("📊 Total Stocks", total_stocks)
        
        with col2:
            st.metric("💰 With Prices", stocks_with_prices, 
                     delta=f"{stocks_with_prices/max(total_stocks, 1)*100:.1f}%")
        
        with col3:
            st.metric("📈 Avg Upside", f"{avg_upside:.1f}%",
                     delta="Bullish" if avg_upside > 0 else "Bearish")
        
        with col4:
            st.metric("🟢 Undervalued", undervalued_count,
                     delta=f"{undervalued_count/max(len(upside_values), 1)*100:.0f}%")
        
        with col5:
            st.metric("🔴 Overvalued", overvalued_count,
                     delta=f"{overvalued_count/max(len(upside_values), 1)*100:.0f}%")
    
    def _display_interactive_table(self, stocks: List[Dict]):
        """Display interactive sortable table"""
        
        # Prepare dataframe
        table_data = []
        for stock in stocks:
            row = {
                'Ticker': stock.get('ticker', 'N/A'),
                'Company': stock.get('company_name', 'N/A'),
                'Current Price': stock.get('current_market_price', stock.get('current_price', 0)),
                'Fair Value': stock.get('fair_value', 0),
                'Current Upside %': stock.get('updated_upside_downside_pct', 
                                           stock.get('upside_downside_pct', 0)),
                'Volume': stock.get('current_volume', 0),
                'Market Cap': stock.get('current_market_cap', 0),
                'Source': stock.get('price_source', 'N/A'),
                'Last Updated': stock.get('price_last_updated', 'N/A')
            }
            table_data.append(row)
        
        if table_data:
            df = pd.DataFrame(table_data)
            
            # Format columns
            if 'Current Price' in df.columns:
                df['Current Price'] = df['Current Price'].apply(lambda x: f"${x:.2f}" if x > 0 else "N/A")
            if 'Fair Value' in df.columns:
                df['Fair Value'] = df['Fair Value'].apply(lambda x: f"${x:.2f}" if x > 0 else "N/A")
            if 'Current Upside %' in df.columns:
                df['Current Upside %'] = df['Current Upside %'].apply(lambda x: f"{x:.1f}%" if x != 0 else "N/A")
            if 'Volume' in df.columns:
                df['Volume'] = df['Volume'].apply(lambda x: f"{x:,}" if x > 0 else "N/A")
            if 'Market Cap' in df.columns:
                df['Market Cap'] = df['Market Cap'].apply(
                    lambda x: f"${x/1e9:.1f}B" if x > 1e9 else f"${x/1e6:.1f}M" if x > 1e6 else "N/A"
                )
            
            # Display table with sorting
            st.subheader("📋 Watch List Details")
            
            # Table controls
            col1, col2 = st.columns([3, 1])
            with col1:
                search_term = st.text_input("🔍 Search stocks:", placeholder="Enter ticker or company name...")
            with col2:
                show_all_columns = st.checkbox("Show All Columns", value=False)
            
            # Filter data
            if search_term:
                mask = (df['Ticker'].str.contains(search_term, case=False, na=False) |
                       df['Company'].str.contains(search_term, case=False, na=False))
                df = df[mask]
            
            # Column selection
            if show_all_columns:
                display_columns = df.columns.tolist()
            else:
                display_columns = ['Ticker', 'Company', 'Current Price', 'Fair Value', 'Current Upside %']
            
            # Display filtered/selected data
            if not df.empty:
                st.dataframe(
                    df[display_columns],
                    use_container_width=True,
                    height=min(400, len(df) * 35 + 50)
                )
            else:
                st.info("🔍 No stocks match your search criteria.")
    
    def _display_watch_list_visualizations(self, watch_list_data: Dict):
        """Display visualizations for the watch list"""
        st.subheader("📊 Performance Visualizations")
        
        # Create enhanced upside/downside chart
        fig = self.visualizer.create_enhanced_upside_downside_chart(
            watch_list_data, 
            title=f"Performance Analysis: {watch_list_data.get('name', 'Watch List')}",
            show_enhanced_features=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Additional charts for large datasets
        stocks = watch_list_data.get('stocks', [])
        if len(stocks) > 10:
            
            # Performance distribution
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribution histogram
                upside_values = [
                    s.get('updated_upside_downside_pct', s.get('upside_downside_pct', 0))
                    for s in stocks if s.get('fair_value')
                ]
                
                if upside_values:
                    fig_hist = px.histogram(
                        x=upside_values,
                        title="Upside/Downside Distribution",
                        labels={'x': 'Upside/Downside %', 'y': 'Count'},
                        nbins=20
                    )
                    fig_hist.add_vline(x=0, line_dash="dash", line_color="red", 
                                     annotation_text="Fair Value")
                    st.plotly_chart(fig_hist, use_container_width=True)
            
            with col2:
                # Price vs Fair Value scatter
                current_prices = []
                fair_values = []
                tickers = []
                
                for stock in stocks:
                    if (stock.get('current_market_price') and stock.get('fair_value') and 
                        stock.get('current_market_price') > 0 and stock.get('fair_value') > 0):
                        current_prices.append(stock['current_market_price'])
                        fair_values.append(stock['fair_value'])
                        tickers.append(stock['ticker'])
                
                if current_prices and fair_values:
                    fig_scatter = go.Figure()
                    fig_scatter.add_trace(go.Scatter(
                        x=current_prices,
                        y=fair_values,
                        mode='markers+text',
                        text=tickers,
                        textposition='top center',
                        marker=dict(size=10, color='blue', opacity=0.6),
                        name='Stocks'
                    ))
                    
                    # Add diagonal line (fair value line)
                    min_val = min(min(current_prices), min(fair_values))
                    max_val = max(max(current_prices), max(fair_values))
                    fig_scatter.add_trace(go.Scatter(
                        x=[min_val, max_val],
                        y=[min_val, max_val],
                        mode='lines',
                        line=dict(dash='dash', color='red'),
                        name='Fair Value Line'
                    ))
                    
                    fig_scatter.update_layout(
                        title="Current Price vs Fair Value",
                        xaxis_title="Current Price ($)",
                        yaxis_title="Fair Value ($)"
                    )
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)
    
    def _display_performance_summary(self, metadata: Dict):
        """Display performance summary from concurrent processing"""
        st.success("🚀 Concurrent Processing Completed!")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("⏱️ Processing Time", 
                     f"{metadata.get('processing_time_seconds', 0):.2f}s")
        
        with col2:
            st.metric("🎯 Success Rate", 
                     f"{(metadata.get('successful_price_fetches', 0) / max(metadata.get('total_tickers_processed', 1), 1) * 100):.1f}%")
        
        with col3:
            st.metric("⚡ Requests/sec", 
                     f"{metadata.get('requests_per_second', 0):.1f}")
        
        with col4:
            st.metric("🧠 Peak Memory", 
                     f"{metadata.get('peak_memory_mb', 0):.1f} MB")
    
    def _display_performance_metrics(self):
        """Display detailed performance metrics"""
        if 'performance_optimizer' not in st.session_state:
            st.warning("Performance optimizer not initialized.")
            return
        
        optimizer = st.session_state.performance_optimizer
        metrics = optimizer.get_performance_metrics()
        
        st.subheader("📊 Performance Metrics Dashboard")
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Requests", metrics.total_requests)
        
        with col2:
            st.metric("Success Rate", f"{(metrics.successful_requests / max(metrics.total_requests, 1) * 100):.1f}%")
        
        with col3:
            st.metric("Avg Response Time", f"{metrics.average_response_time:.3f}s")
        
        with col4:
            st.metric("Peak Memory", f"{metrics.peak_memory_mb:.1f} MB")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Success vs Failure pie chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=['Successful', 'Failed'],
                values=[metrics.successful_requests, metrics.failed_requests],
                hole=0.3
            )])
            fig_pie.update_layout(title="Request Success Rate")
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Performance timeline (placeholder)
            st.markdown("**Performance Timeline**")
            st.info("Real-time performance timeline will be displayed here during active operations.")


# Convenience function for integration
def display_performance_optimized_watch_lists(watch_list_manager: WatchListManager):
    """
    Display the performance-optimized watch lists section
    
    Args:
        watch_list_manager: Watch list manager instance
    """
    integration = StreamlitPerformanceIntegration()
    integration.display_optimized_watch_list_section(watch_list_manager)