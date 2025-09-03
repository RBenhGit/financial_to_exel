"""
Price Service Integration Module

This module provides integration utilities for the RealTimePriceService with
the existing financial analysis toolkit, particularly for Streamlit UI integration.

Features:
- Streamlit integration utilities
- Price data formatting for UI display
- Watch list integration
- Error handling for UI contexts
- Background refresh management
"""

import asyncio
import streamlit as st
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import pandas as pd
import logging

from .real_time_price_service import RealTimePriceService, PriceData, create_price_service

# Import enhanced logging
try:
    from utils.logging_config import get_api_logger
    logger = get_api_logger()
except ImportError:
    logger = logging.getLogger(__name__)


class StreamlitPriceIntegration:
    """Integration utilities for RealTimePriceService with Streamlit"""
    
    def __init__(self, cache_ttl_minutes: int = 15):
        self.cache_ttl_minutes = cache_ttl_minutes
        self._service = None
    
    @property
    def service(self) -> RealTimePriceService:
        """Lazy initialization of price service"""
        if self._service is None:
            self._service = create_price_service(cache_ttl_minutes=self.cache_ttl_minutes)
        return self._service
    
    def get_prices_sync(self, tickers: List[str], force_refresh: bool = False) -> Dict[str, Optional[PriceData]]:
        """
        Synchronous wrapper for getting multiple prices (Streamlit-friendly)
        
        Args:
            tickers: List of ticker symbols
            force_refresh: Force refresh from API
            
        Returns:
            Dictionary mapping tickers to PriceData objects
        """
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self.service.get_multiple_prices(tickers, force_refresh)
                )
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error fetching prices for {tickers}: {e}")
            # Return empty results for failed tickers
            return {ticker: None for ticker in tickers}
    
    def get_single_price_sync(self, ticker: str, force_refresh: bool = False) -> Optional[PriceData]:
        """
        Synchronous wrapper for getting single price (Streamlit-friendly)
        
        Args:
            ticker: Stock ticker symbol
            force_refresh: Force refresh from API
            
        Returns:
            PriceData object or None if failed
        """
        try:
            # Run async function in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                return loop.run_until_complete(
                    self.service.get_real_time_price(ticker, force_refresh)
                )
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None
    
    def display_price_table(self, tickers: List[str], show_refresh_button: bool = True) -> pd.DataFrame:
        """
        Display real-time prices in a Streamlit table format
        
        Args:
            tickers: List of ticker symbols
            show_refresh_button: Whether to show refresh button
            
        Returns:
            DataFrame with price data for display
        """
        # Create columns for layout
        if show_refresh_button:
            col1, col2 = st.columns([3, 1])
            with col2:
                refresh_clicked = st.button("🔄 Refresh Prices", key=f"refresh_{hash(tuple(tickers))}")
        else:
            refresh_clicked = False
        
        # Fetch prices
        with st.spinner("Fetching real-time prices..."):
            prices = self.get_prices_sync(tickers, force_refresh=refresh_clicked)
        
        # Create DataFrame for display
        price_data = []
        for ticker in tickers:
            price_info = prices.get(ticker)
            if price_info:
                # Format change percentage with color
                change_pct = price_info.change_percent
                change_color = "🟢" if change_pct >= 0 else "🔴"
                change_display = f"{change_color} {change_pct:+.2f}%"
                
                # Format price with currency
                price_display = f"${price_info.current_price:.2f}"
                
                # Format volume
                volume_display = self._format_volume(price_info.volume)
                
                # Format market cap
                market_cap_display = self._format_market_cap(price_info.market_cap)
                
                # Cache status with freshness indicators (with emoji for Streamlit)
                cache_status = self._get_freshness_indicator_with_emoji(price_info)
                
                price_data.append({
                    "Ticker": ticker,
                    "Price": price_display,
                    "Change": change_display,
                    "Volume": volume_display,
                    "Market Cap": market_cap_display,
                    "Source": price_info.source.replace("_", " ").title(),
                    "Status": cache_status,
                    "Updated": price_info.last_updated.strftime("%H:%M:%S")
                })
            else:
                price_data.append({
                    "Ticker": ticker,
                    "Price": "❌ Error",
                    "Change": "—",
                    "Volume": "—",
                    "Market Cap": "—",
                    "Source": "—",
                    "Status": "🔴 Failed",
                    "Updated": "—"
                })
        
        df = pd.DataFrame(price_data)
        
        # Display the table
        if show_refresh_button:
            with col1:
                st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        return df
    
    def display_price_metrics(self, ticker: str, show_refresh: bool = True) -> Optional[PriceData]:
        """
        Display price metrics in Streamlit metrics format
        
        Args:
            ticker: Stock ticker symbol
            show_refresh: Whether to show refresh button
            
        Returns:
            PriceData object or None if failed
        """
        # Refresh button
        if show_refresh:
            col1, col2 = st.columns([3, 1])
            with col2:
                refresh_clicked = st.button(f"🔄 Refresh {ticker}", key=f"refresh_metric_{ticker}")
        else:
            refresh_clicked = False
        
        # Fetch price data
        with st.spinner(f"Fetching {ticker} price..."):
            price_data = self.get_single_price_sync(ticker, force_refresh=refresh_clicked)
        
        if price_data:
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label="Current Price",
                    value=f"${price_data.current_price:.2f}",
                    delta=f"{price_data.change_percent:+.2f}%"
                )
            
            with col2:
                st.metric(
                    label="Volume",
                    value=self._format_volume(price_data.volume)
                )
            
            with col3:
                st.metric(
                    label="Market Cap",
                    value=self._format_market_cap(price_data.market_cap)
                )
            
            with col4:
                freshness_info = self._get_freshness_indicator_with_emoji(price_data)
                st.metric(
                    label="Data Status",
                    value=freshness_info
                )
            
            # Additional info
            st.caption(f"Source: {price_data.source.replace('_', ' ').title()} | "
                      f"Updated: {price_data.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            return price_data
        else:
            st.error(f"❌ Failed to fetch price data for {ticker}")
            return None
    
    def display_cache_status(self):
        """Display enhanced cache status information with freshness details"""
        cache_status = self.service.get_cache_status()
        
        st.subheader("💾 Price Cache Status")
        
        # Main metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Memory Entries", cache_status['memory_cache_entries'])
        
        with col2:
            st.metric("Persistent Entries", cache_status['persistent_cache_entries'])
        
        with col3:
            fresh_pct = (cache_status['fresh_entries'] / max(1, cache_status['memory_cache_entries']) * 100)
            st.metric("Fresh Entries", f"{cache_status['fresh_entries']} ({fresh_pct:.0f}%)")
        
        with col4:
            st.metric("API Providers", cache_status['providers_initialized'])
        
        # Freshness breakdown
        if cache_status['memory_cache_entries'] > 0:
            st.subheader("🕒 Cache Freshness Breakdown")
            freshness_stats = self._get_cache_freshness_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🟢 Fresh (0-5min)", freshness_stats['fresh'])
            with col2:
                st.metric("🟡 Recent (5-15min)", freshness_stats['recent'])  
            with col3:
                st.metric("🟠 Stale (15-30min)", freshness_stats['stale'])
            with col4:
                st.metric("🔴 Old (>30min)", freshness_stats['old'])
        
        # Cache management buttons
        st.subheader("🔧 Cache Management")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🗑️ Clear All Cache"):
                self.service.clear_cache()
                st.success("All cache cleared successfully!")
                st.rerun()
        
        with col2:
            if st.button("🧹 Clear Expired"):
                self._clear_expired_cache()
                st.success("Expired cache entries cleared!")
                st.rerun()
        
        with col3:
            if st.button("📊 Refresh Status"):
                st.rerun()
        
        with col4:
            st.info(f"TTL: {cache_status['cache_ttl_minutes']}min")
        
        # Memory usage warning
        if cache_status['memory_cache_entries'] > 50:
            st.warning(f"⚠️ High memory usage: {cache_status['memory_cache_entries']} cached entries. Consider clearing old cache.")
    
    def create_watch_list_widget(self, default_tickers: List[str] = None) -> List[str]:
        """
        Create a watch list widget for ticker selection
        
        Args:
            default_tickers: Default tickers to include
            
        Returns:
            List of selected tickers
        """
        if default_tickers is None:
            default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
        
        st.subheader("📊 Watch List")
        
        # Ticker input
        col1, col2 = st.columns([3, 1])
        
        with col1:
            ticker_input = st.text_input(
                "Add ticker(s) (comma-separated)",
                placeholder="e.g., AAPL, MSFT, GOOGL",
                key="ticker_input"
            )
        
        with col2:
            add_clicked = st.button("➕ Add", key="add_ticker")
        
        # Manage watch list in session state
        if "watch_list" not in st.session_state:
            st.session_state.watch_list = default_tickers.copy()
        
        # Add new tickers
        if add_clicked and ticker_input:
            new_tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
            for ticker in new_tickers:
                if ticker not in st.session_state.watch_list:
                    st.session_state.watch_list.append(ticker)
            # Clear input
            st.rerun()
        
        # Display current watch list with removal options
        if st.session_state.watch_list:
            st.write("**Current Watch List:**")
            
            # Create columns for ticker display
            num_cols = min(5, len(st.session_state.watch_list))
            cols = st.columns(num_cols)
            
            tickers_to_remove = []
            for i, ticker in enumerate(st.session_state.watch_list):
                with cols[i % num_cols]:
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.write(ticker)
                    with col2:
                        if st.button("❌", key=f"remove_{ticker}", help=f"Remove {ticker}"):
                            tickers_to_remove.append(ticker)
            
            # Remove tickers
            for ticker in tickers_to_remove:
                st.session_state.watch_list.remove(ticker)
                st.rerun()
        
        return st.session_state.watch_list
    
    def _get_freshness_indicator(self, price_data: PriceData) -> str:
        """
        Get visual freshness indicator based on data age
        
        Args:
            price_data: PriceData object with timestamp information
            
        Returns:
            String with status indicating data freshness
        """
        if not price_data.cache_hit:
            # Live data is always fresh
            return "LIVE"
        
        # Calculate data age in minutes
        age_minutes = (datetime.now() - price_data.last_updated).total_seconds() / 60
        
        if age_minutes <= 5:
            # Very fresh
            return "FRESH"
        elif age_minutes <= self.cache_ttl_minutes:
            # Fresh within cache TTL
            return "RECENT"
        elif age_minutes <= self.cache_ttl_minutes * 2:
            # Stale but usable
            return "STALE"
        else:
            # Very old
            return "OLD"
    
    def _get_freshness_indicator_with_emoji(self, price_data: PriceData) -> str:
        """
        Get visual freshness indicator with emoji for Streamlit display
        
        Args:
            price_data: PriceData object with timestamp information
            
        Returns:
            String with emoji and status indicating data freshness
        """
        if not price_data.cache_hit:
            return "🟢 Live"
        
        age_minutes = (datetime.now() - price_data.last_updated).total_seconds() / 60
        
        if age_minutes <= 5:
            return "🟢 Fresh"
        elif age_minutes <= self.cache_ttl_minutes:
            return "🟡 Recent"
        elif age_minutes <= self.cache_ttl_minutes * 2:
            return "🟠 Stale"
        else:
            return "🔴 Old"
    
    def _format_volume(self, volume: int) -> str:
        """Format volume for display"""
        if volume == 0:
            return "—"
        elif volume >= 1_000_000_000:
            return f"{volume/1_000_000_000:.1f}B"
        elif volume >= 1_000_000:
            return f"{volume/1_000_000:.1f}M"
        elif volume >= 1_000:
            return f"{volume/1_000:.1f}K"
        else:
            return f"{volume:,}"
    
    def _format_market_cap(self, market_cap: float) -> str:
        """Format market cap for display"""
        if market_cap == 0:
            return "—"
        elif market_cap >= 1_000_000_000_000:
            return f"${market_cap/1_000_000_000_000:.1f}T"
        elif market_cap >= 1_000_000_000:
            return f"${market_cap/1_000_000_000:.1f}B"
        elif market_cap >= 1_000_000:
            return f"${market_cap/1_000_000:.1f}M"
        else:
            return f"${market_cap:,.0f}"
    
    def _get_cache_freshness_stats(self) -> Dict[str, int]:
        """
        Get detailed cache freshness statistics
        
        Returns:
            Dictionary with counts for each freshness category
        """
        stats = {'fresh': 0, 'recent': 0, 'stale': 0, 'old': 0}
        
        # Access memory cache directly (this is a bit of a hack, but necessary)
        try:
            from datetime import datetime
            current_time = datetime.now()
            
            # Get cache entries through service
            cache_status = self.service.get_cache_status()
            
            # If we can't access internal cache, return empty stats
            if not hasattr(self.service, '_memory_cache'):
                return stats
            
            for entry in self.service._memory_cache.values():
                if hasattr(entry, 'price_data') and hasattr(entry.price_data, 'last_updated'):
                    age_minutes = (current_time - entry.price_data.last_updated).total_seconds() / 60
                    
                    if age_minutes <= 5:
                        stats['fresh'] += 1
                    elif age_minutes <= self.cache_ttl_minutes:
                        stats['recent'] += 1
                    elif age_minutes <= self.cache_ttl_minutes * 2:
                        stats['stale'] += 1
                    else:
                        stats['old'] += 1
                        
        except Exception as e:
            logger.warning(f"Failed to get cache freshness stats: {e}")
            
        return stats
    
    def _clear_expired_cache(self):
        """Clear only expired cache entries to optimize memory usage"""
        try:
            # Access memory cache and remove expired entries
            if hasattr(self.service, '_memory_cache'):
                expired_tickers = []
                current_time = datetime.now()
                
                for ticker, entry in self.service._memory_cache.items():
                    if hasattr(entry, 'is_expired') and entry.is_expired():
                        expired_tickers.append(ticker)
                
                # Remove expired entries
                for ticker in expired_tickers:
                    self.service.clear_cache(ticker)
                    
                logger.info(f"Cleared {len(expired_tickers)} expired cache entries")
                
        except Exception as e:
            logger.warning(f"Failed to clear expired cache: {e}")
            # Fallback to clearing all cache if specific clearing fails
            self.service.clear_cache()
    
    def cleanup(self):
        """Cleanup resources"""
        if self._service:
            self._service.__exit__(None, None, None)


# Streamlit session state management
@st.cache_resource
def get_price_integration() -> StreamlitPriceIntegration:
    """Get cached price integration instance"""
    return StreamlitPriceIntegration()


def display_real_time_prices_section(tickers: List[str] = None):
    """
    Complete real-time prices section for Streamlit apps
    
    Args:
        tickers: Optional list of tickers to display
    """
    st.header("📈 Real-Time Prices")
    
    price_integration = get_price_integration()
    
    # Watch list widget
    if tickers is None:
        tickers = price_integration.create_watch_list_widget()
    
    if tickers:
        # Display prices table
        st.subheader("Current Prices")
        df = price_integration.display_price_table(tickers)
        
        # Cache status in expander
        with st.expander("🔧 Cache & Settings"):
            price_integration.display_cache_status()
    else:
        st.info("Add some tickers to your watch list to see real-time prices.")


# Integration with existing watch list functionality
def integrate_with_watch_list_manager(watch_list_data: Dict[str, Any]) -> Dict[str, PriceData]:
    """
    Integrate price service with existing watch list manager
    
    Args:
        watch_list_data: Watch list data from existing manager
        
    Returns:
        Dictionary mapping tickers to current price data
    """
    price_integration = StreamlitPriceIntegration()
    
    # Extract tickers from watch list data
    tickers = []
    if isinstance(watch_list_data, dict):
        if 'tickers' in watch_list_data:
            tickers = watch_list_data['tickers']
        elif 'companies' in watch_list_data:
            tickers = list(watch_list_data['companies'].keys())
    elif isinstance(watch_list_data, list):
        tickers = watch_list_data
    
    # Fetch current prices
    if tickers:
        prices = price_integration.get_prices_sync(tickers)
        return {ticker: data for ticker, data in prices.items() if data is not None}
    
    return {}


# Utility functions for manual integration
def get_current_price_simple(ticker: str, use_cache: bool = True) -> Optional[float]:
    """
    Simple function to get current price (synchronous)
    
    Args:
        ticker: Stock ticker symbol
        use_cache: Whether to use cached data if available
        
    Returns:
        Current price as float or None if failed
    """
    integration = StreamlitPriceIntegration()
    price_data = integration.get_single_price_sync(ticker, force_refresh=not use_cache)
    return price_data.current_price if price_data else None


def get_current_prices_simple(tickers: List[str], use_cache: bool = True) -> Dict[str, Optional[float]]:
    """
    Simple function to get current prices for multiple tickers (synchronous)
    
    Args:
        tickers: List of stock ticker symbols
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary mapping tickers to prices (None if failed)
    """
    integration = StreamlitPriceIntegration()
    price_data_dict = integration.get_prices_sync(tickers, force_refresh=not use_cache)
    return {
        ticker: data.current_price if data else None 
        for ticker, data in price_data_dict.items()
    }


if __name__ == "__main__":
    # Example Streamlit app using the integration
    st.title("Real-Time Price Service Demo")
    
    # Display the complete real-time prices section
    display_real_time_prices_section()
    
    # Example of individual ticker display
    st.header("Individual Ticker Demo")
    selected_ticker = st.selectbox("Select ticker", ["AAPL", "MSFT", "GOOGL", "AMZN"])
    
    if selected_ticker:
        price_integration = get_price_integration()
        price_integration.display_price_metrics(selected_ticker)