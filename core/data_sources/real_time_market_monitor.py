"""
Real-Time Market Monitor with Auto-Refresh and Market Status

This module extends the existing RealTimePriceService with:
- Market status detection (open/closed/pre-market/after-hours)
- Auto-refresh during trading hours
- Streamlit integration with live updates
- Market holidays and timezone handling
"""

import asyncio
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging
import streamlit as st
import pandas as pd

try:
    import pytz
    from pytz import timezone as pytz_timezone
    TIMEZONE_SUPPORT = True
except ImportError:
    TIMEZONE_SUPPORT = False

from .real_time_price_service import RealTimePriceService, PriceData, create_price_service

# Enhanced logging
try:
    from utils.logging_config import get_api_logger
    logger = get_api_logger()
except ImportError:
    logger = logging.getLogger(__name__)


class MarketStatus(Enum):
    """Market status enumeration"""
    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    OPEN = "open"
    AFTER_HOURS = "after_hours"
    WEEKEND = "weekend"
    HOLIDAY = "holiday"


@dataclass
class MarketInfo:
    """Market status and timing information"""
    status: MarketStatus
    is_trading_day: bool
    next_open: Optional[datetime] = None
    next_close: Optional[datetime] = None
    current_time: datetime = None
    timezone_name: str = "UTC"
    market_name: str = "US Markets"

    def __post_init__(self):
        if self.current_time is None:
            self.current_time = datetime.now(timezone.utc)


class RealTimeMarketMonitor:
    """
    Enhanced real-time market monitor with auto-refresh and market status tracking
    """

    def __init__(self, cache_ttl_minutes: int = 15, auto_refresh_interval: int = 30):
        """
        Initialize the Real-Time Market Monitor

        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
            auto_refresh_interval: Auto-refresh interval in seconds during market hours
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self.auto_refresh_interval = auto_refresh_interval
        self._price_service = create_price_service(cache_ttl_minutes=cache_ttl_minutes)

        # Auto-refresh control
        self._auto_refresh_enabled = False
        self._auto_refresh_thread = None
        self._stop_auto_refresh = threading.Event()
        self._refresh_callbacks: List[Callable] = []

        # Market timezone (US Eastern)
        if TIMEZONE_SUPPORT:
            self.market_timezone = pytz_timezone('US/Eastern')
        else:
            self.market_timezone = None
            logger.warning("pytz not available - market hours detection will be limited")

        logger.info(f"RealTimeMarketMonitor initialized with {auto_refresh_interval}s refresh interval")

    def get_market_status(self) -> MarketInfo:
        """
        Get current market status with detailed timing information

        Returns:
            MarketInfo object with current market status and timing
        """
        if not TIMEZONE_SUPPORT:
            # Fallback to basic status without timezone support
            return MarketInfo(
                status=MarketStatus.OPEN,  # Assume open as fallback
                is_trading_day=True,
                current_time=datetime.now(timezone.utc),
                timezone_name="UTC",
                market_name="US Markets (Limited)"
            )

        # Get current time in market timezone
        market_time = datetime.now(self.market_timezone)

        # Check if it's a weekend
        if market_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return MarketInfo(
                status=MarketStatus.WEEKEND,
                is_trading_day=False,
                current_time=market_time,
                timezone_name=self.market_timezone.zone,
                next_open=self._get_next_market_open(market_time)
            )

        # Market hours (9:30 AM - 4:00 PM ET)
        market_open = market_time.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = market_time.replace(hour=16, minute=0, second=0, microsecond=0)
        pre_market_start = market_time.replace(hour=4, minute=0, second=0, microsecond=0)
        after_hours_end = market_time.replace(hour=20, minute=0, second=0, microsecond=0)

        # Determine status
        if market_time < pre_market_start:
            status = MarketStatus.CLOSED
            next_open = pre_market_start
            next_close = market_close
        elif market_time < market_open:
            status = MarketStatus.PRE_MARKET
            next_open = market_open
            next_close = market_close
        elif market_time < market_close:
            status = MarketStatus.OPEN
            next_open = self._get_next_market_open(market_time)
            next_close = market_close
        elif market_time < after_hours_end:
            status = MarketStatus.AFTER_HOURS
            next_open = self._get_next_market_open(market_time)
            next_close = None
        else:
            status = MarketStatus.CLOSED
            next_open = self._get_next_market_open(market_time)
            next_close = None

        return MarketInfo(
            status=status,
            is_trading_day=True,
            current_time=market_time,
            timezone_name=self.market_timezone.zone,
            next_open=next_open,
            next_close=next_close
        )

    def _get_next_market_open(self, current_time: datetime) -> datetime:
        """Calculate next market open time"""
        if not TIMEZONE_SUPPORT:
            return current_time + timedelta(days=1)

        # If it's Friday after market close, next open is Monday
        if current_time.weekday() == 4 and current_time.hour >= 16:
            days_to_add = 3  # Friday -> Monday
        elif current_time.weekday() >= 5:  # Weekend
            days_to_add = 7 - current_time.weekday()  # To Monday
        elif current_time.hour >= 16:  # After market close
            days_to_add = 1
        else:
            days_to_add = 0

        next_day = current_time + timedelta(days=days_to_add)
        return next_day.replace(hour=9, minute=30, second=0, microsecond=0)

    async def get_real_time_price_with_status(self, ticker: str, force_refresh: bool = False) -> tuple[Optional[PriceData], MarketInfo]:
        """
        Get real-time price along with market status

        Args:
            ticker: Stock ticker symbol
            force_refresh: Force refresh from API

        Returns:
            Tuple of (PriceData, MarketInfo)
        """
        market_info = self.get_market_status()
        price_data = await self._price_service.get_real_time_price(ticker, force_refresh)
        return price_data, market_info

    async def get_multiple_prices_with_status(self, tickers: List[str], force_refresh: bool = False) -> tuple[Dict[str, Optional[PriceData]], MarketInfo]:
        """
        Get multiple real-time prices along with market status

        Args:
            tickers: List of ticker symbols
            force_refresh: Force refresh from API

        Returns:
            Tuple of (price_dict, MarketInfo)
        """
        market_info = self.get_market_status()
        price_data = await self._price_service.get_multiple_prices(tickers, force_refresh)
        return price_data, market_info

    def start_auto_refresh(self, tickers: List[str], callback: Optional[Callable] = None):
        """
        Start auto-refresh for given tickers during market hours

        Args:
            tickers: List of tickers to monitor
            callback: Optional callback function to call on refresh
        """
        if self._auto_refresh_enabled:
            logger.warning("Auto-refresh already enabled")
            return

        self._auto_refresh_enabled = True
        self._stop_auto_refresh.clear()

        if callback:
            self._refresh_callbacks.append(callback)

        self._auto_refresh_thread = threading.Thread(
            target=self._auto_refresh_worker,
            args=(tickers,),
            daemon=True
        )
        self._auto_refresh_thread.start()

        logger.info(f"Started auto-refresh for {len(tickers)} tickers")

    def stop_auto_refresh(self):
        """Stop auto-refresh functionality"""
        if not self._auto_refresh_enabled:
            return

        self._auto_refresh_enabled = False
        self._stop_auto_refresh.set()

        if self._auto_refresh_thread and self._auto_refresh_thread.is_alive():
            self._auto_refresh_thread.join(timeout=5)

        self._refresh_callbacks.clear()
        logger.info("Stopped auto-refresh")

    def _auto_refresh_worker(self, tickers: List[str]):
        """Background worker for auto-refresh functionality"""
        logger.info("Auto-refresh worker started")

        while not self._stop_auto_refresh.is_set():
            try:
                market_info = self.get_market_status()

                # Only refresh during market hours or pre-market
                if market_info.status in [MarketStatus.OPEN, MarketStatus.PRE_MARKET]:
                    logger.debug(f"Auto-refreshing {len(tickers)} tickers (market {market_info.status.value})")

                    # Refresh prices
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        updated_prices = loop.run_until_complete(
                            self._price_service.get_multiple_prices(tickers, force_refresh=True)
                        )

                        # Call callbacks
                        for callback in self._refresh_callbacks:
                            try:
                                callback(updated_prices, market_info)
                            except Exception as e:
                                logger.error(f"Callback error during auto-refresh: {e}")

                    finally:
                        loop.close()
                else:
                    logger.debug(f"Skipping auto-refresh - market {market_info.status.value}")

                # Wait for next refresh or stop signal
                if self._stop_auto_refresh.wait(timeout=self.auto_refresh_interval):
                    break

            except Exception as e:
                logger.error(f"Auto-refresh worker error: {e}")
                time.sleep(10)  # Wait before retrying on error

        logger.info("Auto-refresh worker stopped")

    def add_refresh_callback(self, callback: Callable):
        """Add callback function for auto-refresh events"""
        self._refresh_callbacks.append(callback)

    def remove_refresh_callback(self, callback: Callable):
        """Remove callback function from auto-refresh events"""
        if callback in self._refresh_callbacks:
            self._refresh_callbacks.remove(callback)

    def get_market_status_display(self) -> Dict[str, str]:
        """
        Get market status formatted for display

        Returns:
            Dictionary with display-ready market status information
        """
        market_info = self.get_market_status()

        # Status icon and color
        status_display = {
            MarketStatus.OPEN: "🟢 Market Open",
            MarketStatus.PRE_MARKET: "🟡 Pre-Market",
            MarketStatus.AFTER_HOURS: "🟠 After Hours",
            MarketStatus.CLOSED: "🔴 Market Closed",
            MarketStatus.WEEKEND: "🔵 Weekend",
            MarketStatus.HOLIDAY: "🟣 Holiday"
        }

        result = {
            'status': status_display.get(market_info.status, "❓ Unknown"),
            'current_time': market_info.current_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'timezone': market_info.timezone_name,
            'is_trading_day': "Yes" if market_info.is_trading_day else "No"
        }

        # Add timing information
        if market_info.next_open:
            result['next_open'] = market_info.next_open.strftime('%Y-%m-%d %H:%M:%S %Z')

        if market_info.next_close:
            result['next_close'] = market_info.next_close.strftime('%H:%M:%S %Z')

        return result

    def should_auto_refresh(self) -> bool:
        """Check if auto-refresh should be active based on market status"""
        market_info = self.get_market_status()
        return market_info.status in [MarketStatus.OPEN, MarketStatus.PRE_MARKET]

    def cleanup(self):
        """Cleanup resources"""
        self.stop_auto_refresh()
        if hasattr(self._price_service, '__exit__'):
            self._price_service.__exit__(None, None, None)


# Streamlit integration functions
def display_market_status_widget():
    """Display market status widget in Streamlit"""
    monitor = get_market_monitor()
    status_info = monitor.get_market_status_display()

    st.subheader("🏛️ Market Status")

    # Main status display
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Status", status_info['status'])

    with col2:
        st.metric("Trading Day", status_info['is_trading_day'])

    with col3:
        if 'next_close' in status_info:
            st.metric("Next Close", status_info['next_close'])
        else:
            st.metric("Next Close", "—")

    with col4:
        if 'next_open' in status_info:
            st.metric("Next Open", status_info['next_open'])
        else:
            st.metric("Next Open", "—")

    # Current time
    st.caption(f"Current Time: {status_info['current_time']} ({status_info['timezone']})")

    return monitor.get_market_status()


def create_auto_refresh_dashboard(default_tickers: List[str] = None):
    """
    Create a complete auto-refresh dashboard with market status

    Args:
        default_tickers: Default tickers to monitor
    """
    if default_tickers is None:
        default_tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    st.header("📈 Live Market Dashboard")

    # Market status
    market_info = display_market_status_widget()

    st.divider()

    # Auto-refresh controls
    st.subheader("🔄 Auto-Refresh Settings")

    col1, col2, col3 = st.columns(3)

    with col1:
        auto_refresh_enabled = st.checkbox(
            "Enable Auto-Refresh",
            value=st.session_state.get('auto_refresh_enabled', False),
            help="Automatically refresh prices during market hours"
        )
        st.session_state.auto_refresh_enabled = auto_refresh_enabled

    with col2:
        refresh_interval = st.selectbox(
            "Refresh Interval",
            [15, 30, 60, 120],
            index=1,
            format_func=lambda x: f"{x} seconds",
            help="How often to refresh during market hours"
        )

    with col3:
        only_market_hours = st.checkbox(
            "Only During Market Hours",
            value=True,
            help="Only auto-refresh when market is open"
        )

    # Get or create monitor
    monitor = get_market_monitor()

    # Ticker selection
    st.subheader("📊 Watch List")

    # Manage tickers in session state
    if "dashboard_tickers" not in st.session_state:
        st.session_state.dashboard_tickers = default_tickers.copy()

    # Ticker input
    col1, col2 = st.columns([3, 1])
    with col1:
        new_ticker = st.text_input("Add ticker", placeholder="e.g., NVDA")
    with col2:
        if st.button("➕ Add") and new_ticker:
            ticker = new_ticker.upper().strip()
            if ticker not in st.session_state.dashboard_tickers:
                st.session_state.dashboard_tickers.append(ticker)
                st.rerun()

    # Display current tickers with remove buttons
    if st.session_state.dashboard_tickers:
        ticker_cols = st.columns(min(5, len(st.session_state.dashboard_tickers)))
        tickers_to_remove = []

        for i, ticker in enumerate(st.session_state.dashboard_tickers):
            with ticker_cols[i % len(ticker_cols)]:
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(ticker)
                with col2:
                    if st.button("❌", key=f"remove_ticker_{ticker}"):
                        tickers_to_remove.append(ticker)

        # Remove tickers
        for ticker in tickers_to_remove:
            st.session_state.dashboard_tickers.remove(ticker)
            st.rerun()

    st.divider()

    # Live prices display
    if st.session_state.dashboard_tickers:
        st.subheader("💰 Live Prices")

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()

        # Display prices with market status
        display_enhanced_price_table(st.session_state.dashboard_tickers, monitor)

        # Auto-refresh status
        if auto_refresh_enabled:
            should_refresh = monitor.should_auto_refresh() if only_market_hours else True

            if should_refresh:
                st.success("🟢 Auto-refresh active")
                # Use Streamlit's auto-refresh feature
                time.sleep(refresh_interval)
                st.rerun()
            else:
                st.info("🟡 Auto-refresh paused (market closed)")
        else:
            st.info("🔴 Auto-refresh disabled")
    else:
        st.info("Add some tickers to start monitoring prices")


def display_enhanced_price_table(tickers: List[str], monitor: RealTimeMarketMonitor):
    """Display enhanced price table with market status integration"""

    # Get prices and market status
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        prices, market_info = loop.run_until_complete(
            monitor.get_multiple_prices_with_status(tickers)
        )
    finally:
        loop.close()

    # Create enhanced display data
    display_data = []
    for ticker in tickers:
        price_data = prices.get(ticker)
        if price_data:
            # Enhanced formatting with market status context
            change_pct = price_data.change_percent
            change_color = "🟢" if change_pct >= 0 else "🔴"
            change_display = f"{change_color} {change_pct:+.2f}%"

            # Price with market context
            price_display = f"${price_data.current_price:.2f}"

            # Add real-time indicator
            if market_info.status == MarketStatus.OPEN and not price_data.cache_hit:
                price_display += " 🔴"  # Live indicator
            elif price_data.cache_hit:
                age_minutes = (datetime.now() - price_data.last_updated).total_seconds() / 60
                if age_minutes <= 5:
                    price_display += " 🟢"  # Fresh
                elif age_minutes <= 15:
                    price_display += " 🟡"  # Recent
                else:
                    price_display += " 🟠"  # Stale

            display_data.append({
                "Ticker": ticker,
                "Price": price_display,
                "Change": change_display,
                "Volume": format_volume(price_data.volume),
                "Source": price_data.source.replace("_", " ").title(),
                "Updated": price_data.last_updated.strftime("%H:%M:%S")
            })
        else:
            display_data.append({
                "Ticker": ticker,
                "Price": "❌ Error",
                "Change": "—",
                "Volume": "—",
                "Source": "—",
                "Updated": "—"
            })

    # Display table
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Legend
    st.caption("🔴 Live • 🟢 Fresh (<5min) • 🟡 Recent (<15min) • 🟠 Stale (>15min)")


def format_volume(volume: int) -> str:
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


# Session state management
@st.cache_resource
def get_market_monitor() -> RealTimeMarketMonitor:
    """Get cached market monitor instance"""
    return RealTimeMarketMonitor()


if __name__ == "__main__":
    # Example Streamlit app
    st.title("Real-Time Market Monitor Demo")
    create_auto_refresh_dashboard()