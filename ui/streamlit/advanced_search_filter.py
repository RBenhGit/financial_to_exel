"""
Advanced Search and Filtering System for Financial Dashboard

This module provides comprehensive search, filtering, and bookmarking capabilities
for navigating financial data across multiple companies and metrics.

Features:
- Smart company search with autocomplete
- Advanced filtering by sector, market cap, geography, and financial metrics
- Bookmarks/favorites system with persistent storage
- Advanced query builder with logical operators
- Real-time filtering with performance optimization
"""

import streamlit as st
import pandas as pd
import yfinance as yf
import json
import os
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from pathlib import Path
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
import pickle

logger = logging.getLogger(__name__)


@dataclass
class CompanyInfo:
    """Company information for search and filtering"""
    symbol: str
    name: str
    sector: str = "Unknown"
    industry: str = "Unknown"
    market_cap: float = 0.0
    country: str = "Unknown"
    exchange: str = "Unknown"
    currency: str = "USD"
    employees: int = 0
    website: str = ""
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompanyInfo':
        return cls(**data)


@dataclass
class FilterCriteria:
    """Filtering criteria for company search"""
    sectors: List[str] = None
    market_cap_min: float = None
    market_cap_max: float = None
    countries: List[str] = None
    exchanges: List[str] = None
    pe_ratio_min: float = None
    pe_ratio_max: float = None
    dividend_yield_min: float = None
    dividend_yield_max: float = None
    revenue_growth_min: float = None
    revenue_growth_max: float = None
    debt_to_equity_max: float = None
    roe_min: float = None
    search_text: str = ""

    def __post_init__(self):
        if self.sectors is None:
            self.sectors = []
        if self.countries is None:
            self.countries = []
        if self.exchanges is None:
            self.exchanges = []


class CompanyDataCache:
    """Cached company data for fast filtering and search"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "company_info_cache.pkl"
        self.companies: Dict[str, CompanyInfo] = {}
        self.last_updated = None
        self.load_cache()

    def load_cache(self) -> None:
        """Load cached company data"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                    self.companies = cache_data.get('companies', {})
                    self.last_updated = cache_data.get('last_updated')
                logger.info(f"Loaded {len(self.companies)} companies from cache")
        except Exception as e:
            logger.warning(f"Failed to load company cache: {e}")
            self.companies = {}

    def save_cache(self) -> None:
        """Save company data to cache"""
        try:
            cache_data = {
                'companies': self.companies,
                'last_updated': datetime.now()
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            logger.info(f"Saved {len(self.companies)} companies to cache")
        except Exception as e:
            logger.error(f"Failed to save company cache: {e}")

    def is_cache_stale(self, hours: int = 24) -> bool:
        """Check if cache is stale"""
        if self.last_updated is None:
            return True
        return datetime.now() - self.last_updated > timedelta(hours=hours)

    def add_company(self, symbol: str, company_info: CompanyInfo) -> None:
        """Add company to cache"""
        self.companies[symbol.upper()] = company_info

    def get_company(self, symbol: str) -> Optional[CompanyInfo]:
        """Get company from cache"""
        return self.companies.get(symbol.upper())

    def get_all_companies(self) -> Dict[str, CompanyInfo]:
        """Get all cached companies"""
        return self.companies.copy()

    def search_companies(self, query: str, limit: int = 50) -> List[CompanyInfo]:
        """Search companies by name or symbol"""
        query = query.lower()
        results = []

        for company in self.companies.values():
            if (query in company.symbol.lower() or
                query in company.name.lower() or
                query in company.sector.lower() or
                query in company.industry.lower()):
                results.append(company)
                if len(results) >= limit:
                    break

        return results


class BookmarkManager:
    """Manage user bookmarks and favorites"""

    def __init__(self, user_id: str = "default", cache_dir: str = "data/cache"):
        self.user_id = user_id
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.bookmarks_file = self.cache_dir / f"bookmarks_{user_id}.json"
        self.bookmarks: Dict[str, Dict[str, Any]] = {}
        self.load_bookmarks()

    def load_bookmarks(self) -> None:
        """Load user bookmarks"""
        try:
            if self.bookmarks_file.exists():
                with open(self.bookmarks_file, 'r') as f:
                    self.bookmarks = json.load(f)
                logger.info(f"Loaded {len(self.bookmarks)} bookmarks for user {self.user_id}")
        except Exception as e:
            logger.warning(f"Failed to load bookmarks: {e}")
            self.bookmarks = {}

    def save_bookmarks(self) -> None:
        """Save user bookmarks"""
        try:
            with open(self.bookmarks_file, 'w') as f:
                json.dump(self.bookmarks, f, indent=2)
            logger.info(f"Saved {len(self.bookmarks)} bookmarks for user {self.user_id}")
        except Exception as e:
            logger.error(f"Failed to save bookmarks: {e}")

    def add_bookmark(self, symbol: str, name: str = "", tags: List[str] = None) -> None:
        """Add company to bookmarks"""
        if tags is None:
            tags = []

        self.bookmarks[symbol.upper()] = {
            "symbol": symbol.upper(),
            "name": name,
            "tags": tags,
            "added_date": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat()
        }
        self.save_bookmarks()

    def remove_bookmark(self, symbol: str) -> None:
        """Remove company from bookmarks"""
        symbol = symbol.upper()
        if symbol in self.bookmarks:
            del self.bookmarks[symbol]
            self.save_bookmarks()

    def is_bookmarked(self, symbol: str) -> bool:
        """Check if company is bookmarked"""
        return symbol.upper() in self.bookmarks

    def get_bookmarks(self) -> List[Dict[str, Any]]:
        """Get all bookmarks"""
        return list(self.bookmarks.values())

    def update_access_time(self, symbol: str) -> None:
        """Update last accessed time for bookmark"""
        symbol = symbol.upper()
        if symbol in self.bookmarks:
            self.bookmarks[symbol]["last_accessed"] = datetime.now().isoformat()
            self.save_bookmarks()


class AdvancedSearchFilter:
    """Main class for advanced search and filtering functionality"""

    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = cache_dir
        self.company_cache = CompanyDataCache(cache_dir)
        self.bookmark_manager = BookmarkManager(cache_dir=cache_dir)
        self.executor = ThreadPoolExecutor(max_workers=4)

        # Popular exchanges and sectors for filtering
        self.popular_exchanges = [
            "NASDAQ", "NYSE", "AMEX", "LSE", "TSX", "ASX", "JPX", "HKSE", "SSE", "BSE"
        ]

        self.popular_sectors = [
            "Technology", "Healthcare", "Financial Services", "Consumer Cyclical",
            "Communication Services", "Industrials", "Consumer Defensive", "Energy",
            "Utilities", "Real Estate", "Basic Materials"
        ]

        self.market_cap_ranges = {
            "Micro Cap (< $300M)": (0, 300_000_000),
            "Small Cap ($300M - $2B)": (300_000_000, 2_000_000_000),
            "Mid Cap ($2B - $10B)": (2_000_000_000, 10_000_000_000),
            "Large Cap ($10B - $200B)": (10_000_000_000, 200_000_000_000),
            "Mega Cap (> $200B)": (200_000_000_000, float('inf'))
        }

    def fetch_company_info(self, symbol: str, force_refresh: bool = False) -> Optional[CompanyInfo]:
        """Fetch company information from yfinance"""
        symbol = symbol.upper()

        # Check cache first
        if not force_refresh:
            cached_info = self.company_cache.get_company(symbol)
            if cached_info:
                return cached_info

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            company_info = CompanyInfo(
                symbol=symbol,
                name=info.get('longName', info.get('shortName', symbol)),
                sector=info.get('sector', 'Unknown'),
                industry=info.get('industry', 'Unknown'),
                market_cap=info.get('marketCap', 0),
                country=info.get('country', 'Unknown'),
                exchange=info.get('exchange', 'Unknown'),
                currency=info.get('currency', 'USD'),
                employees=info.get('fullTimeEmployees', 0),
                website=info.get('website', ''),
                description=info.get('longBusinessSummary', '')[:500] + '...' if info.get('longBusinessSummary') else ''
            )

            # Cache the information
            self.company_cache.add_company(symbol, company_info)
            self.company_cache.save_cache()

            return company_info

        except Exception as e:
            logger.error(f"Failed to fetch info for {symbol}: {e}")
            return None

    def batch_fetch_companies(self, symbols: List[str]) -> Dict[str, CompanyInfo]:
        """Fetch multiple company information in parallel"""
        results = {}

        # Use ThreadPoolExecutor for parallel fetching
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_to_symbol = {
                executor.submit(self.fetch_company_info, symbol): symbol
                for symbol in symbols
            }

            for future in future_to_symbol:
                symbol = future_to_symbol[future]
                try:
                    company_info = future.result(timeout=10)
                    if company_info:
                        results[symbol] = company_info
                except Exception as e:
                    logger.error(f"Failed to fetch {symbol}: {e}")

        return results

    def filter_companies(self, criteria: FilterCriteria) -> List[CompanyInfo]:
        """Filter companies based on criteria"""
        companies = self.company_cache.get_all_companies()
        results = []

        for company in companies.values():
            # Text search
            if criteria.search_text:
                search_text = criteria.search_text.lower()
                if not any(search_text in field.lower() for field in [
                    company.symbol, company.name, company.sector, company.industry
                ]):
                    continue

            # Sector filter
            if criteria.sectors and company.sector not in criteria.sectors:
                continue

            # Market cap filter
            if criteria.market_cap_min is not None and company.market_cap < criteria.market_cap_min:
                continue
            if criteria.market_cap_max is not None and company.market_cap > criteria.market_cap_max:
                continue

            # Country filter
            if criteria.countries and company.country not in criteria.countries:
                continue

            # Exchange filter
            if criteria.exchanges and company.exchange not in criteria.exchanges:
                continue

            results.append(company)

        return results

    def get_autocomplete_suggestions(self, query: str, limit: int = 20) -> List[Tuple[str, str]]:
        """Get autocomplete suggestions for search query"""
        if len(query) < 2:
            return []

        companies = self.company_cache.search_companies(query, limit)
        suggestions = []

        for company in companies:
            display_text = f"{company.symbol} - {company.name}"
            if company.sector != "Unknown":
                display_text += f" ({company.sector})"
            suggestions.append((company.symbol, display_text))

        return suggestions


def render_advanced_search_sidebar() -> Tuple[Optional[str], FilterCriteria]:
    """Render the advanced search sidebar"""
    if 'search_filter' not in st.session_state:
        st.session_state.search_filter = AdvancedSearchFilter()

    search_filter = st.session_state.search_filter

    st.sidebar.markdown("## 🔍 Advanced Search & Filter")

    # Quick search with autocomplete
    search_query = st.sidebar.text_input(
        "Search Companies",
        placeholder="Enter symbol, name, or sector...",
        help="Type to search by company symbol, name, or sector"
    )

    selected_symbol = None
    if search_query and len(search_query) >= 2:
        suggestions = search_filter.get_autocomplete_suggestions(search_query)
        if suggestions:
            suggestion_options = [""] + [display for symbol, display in suggestions]
            selected_suggestion = st.sidebar.selectbox(
                "Suggestions",
                suggestion_options,
                key="search_suggestions"
            )

            if selected_suggestion:
                # Extract symbol from suggestion
                selected_symbol = selected_suggestion.split(" - ")[0]

    # Bookmarks section
    st.sidebar.markdown("### ⭐ Bookmarks")
    bookmarks = search_filter.bookmark_manager.get_bookmarks()

    if bookmarks:
        bookmark_options = [""] + [f"{b['symbol']} - {b['name']}" for b in bookmarks]
        selected_bookmark = st.sidebar.selectbox(
            "Quick Access",
            bookmark_options,
            key="bookmark_selection"
        )

        if selected_bookmark:
            selected_symbol = selected_bookmark.split(" - ")[0]
    else:
        st.sidebar.info("No bookmarks yet. Add companies to your favorites!")

    # Advanced filters
    with st.sidebar.expander("🎛️ Advanced Filters", expanded=False):
        criteria = FilterCriteria()

        # Sector filter
        criteria.sectors = st.multiselect(
            "Sectors",
            search_filter.popular_sectors,
            help="Filter by business sector"
        )

        # Market cap filter
        market_cap_range = st.select_slider(
            "Market Cap Range",
            options=list(search_filter.market_cap_ranges.keys()),
            help="Filter by company size"
        )

        if market_cap_range:
            min_cap, max_cap = search_filter.market_cap_ranges[market_cap_range]
            criteria.market_cap_min = min_cap if min_cap > 0 else None
            criteria.market_cap_max = max_cap if max_cap != float('inf') else None

        # Exchange filter
        criteria.exchanges = st.multiselect(
            "Exchanges",
            search_filter.popular_exchanges,
            help="Filter by stock exchange"
        )

        # Financial metrics filters
        st.markdown("**Financial Metrics**")

        col1, col2 = st.columns(2)
        with col1:
            criteria.pe_ratio_min = st.number_input("Min P/E", min_value=0.0, step=1.0, value=None)
            criteria.dividend_yield_min = st.number_input("Min Div Yield %", min_value=0.0, step=0.1, value=None)
            criteria.roe_min = st.number_input("Min ROE %", min_value=0.0, step=1.0, value=None)

        with col2:
            criteria.pe_ratio_max = st.number_input("Max P/E", min_value=0.0, step=1.0, value=None)
            criteria.dividend_yield_max = st.number_input("Max Div Yield %", min_value=0.0, step=0.1, value=None)
            criteria.debt_to_equity_max = st.number_input("Max D/E", min_value=0.0, step=0.1, value=None)

        criteria.search_text = search_query

        # Apply filters button
        if st.button("🔎 Apply Filters", use_container_width=True):
            st.session_state.filter_results = search_filter.filter_companies(criteria)
            st.rerun()

    # Query builder
    with st.sidebar.expander("🔧 Query Builder", expanded=False):
        st.markdown("**Build Complex Queries**")

        # Saved queries
        if 'saved_queries' not in st.session_state:
            st.session_state.saved_queries = {}

        query_name = st.text_input("Query Name", placeholder="e.g., Tech Giants")

        if st.button("💾 Save Current Filter"):
            if query_name:
                st.session_state.saved_queries[query_name] = criteria
                st.success(f"Saved query: {query_name}")

        # Load saved queries
        if st.session_state.saved_queries:
            saved_query = st.selectbox(
                "Load Saved Query",
                [""] + list(st.session_state.saved_queries.keys())
            )

            if saved_query and st.button("📥 Load Query"):
                criteria = st.session_state.saved_queries[saved_query]
                st.success(f"Loaded query: {saved_query}")
                st.rerun()

    return selected_symbol, criteria


def render_search_results(filter_results: List[CompanyInfo] = None):
    """Render search and filter results"""
    if filter_results is None:
        filter_results = getattr(st.session_state, 'filter_results', [])

    if not filter_results:
        return

    st.markdown("## 🎯 Search Results")

    # Results summary
    st.info(f"Found {len(filter_results)} companies matching your criteria")

    # Results display options
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        view_mode = st.radio(
            "View Mode",
            ["Table", "Cards", "Chart"],
            horizontal=True
        )

    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Symbol", "Name", "Market Cap", "Sector"]
        )

    with col3:
        sort_order = st.selectbox("Order", ["Ascending", "Descending"])

    # Sort results
    reverse = sort_order == "Descending"
    if sort_by == "Symbol":
        filter_results.sort(key=lambda x: x.symbol, reverse=reverse)
    elif sort_by == "Name":
        filter_results.sort(key=lambda x: x.name, reverse=reverse)
    elif sort_by == "Market Cap":
        filter_results.sort(key=lambda x: x.market_cap, reverse=reverse)
    elif sort_by == "Sector":
        filter_results.sort(key=lambda x: x.sector, reverse=reverse)

    # Display results
    if view_mode == "Table":
        render_results_table(filter_results)
    elif view_mode == "Cards":
        render_results_cards(filter_results)
    elif view_mode == "Chart":
        render_results_chart(filter_results)


def render_results_table(companies: List[CompanyInfo]):
    """Render results as a table"""
    df_data = []
    search_filter = st.session_state.search_filter

    for company in companies:
        market_cap_billions = company.market_cap / 1_000_000_000 if company.market_cap > 0 else 0

        df_data.append({
            "Symbol": company.symbol,
            "Name": company.name,
            "Sector": company.sector,
            "Market Cap (B)": f"${market_cap_billions:.1f}",
            "Country": company.country,
            "Exchange": company.exchange,
            "Bookmarked": "⭐" if search_filter.bookmark_manager.is_bookmarked(company.symbol) else ""
        })

    df = pd.DataFrame(df_data)

    # Interactive table with selection
    event = st.dataframe(
        df,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )

    # Handle row selection
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        selected_company = companies[selected_idx]

        # Add bookmark button
        col1, col2 = st.columns([1, 4])
        with col1:
            if search_filter.bookmark_manager.is_bookmarked(selected_company.symbol):
                if st.button("🗑️ Remove Bookmark"):
                    search_filter.bookmark_manager.remove_bookmark(selected_company.symbol)
                    st.rerun()
            else:
                if st.button("⭐ Add Bookmark"):
                    search_filter.bookmark_manager.add_bookmark(
                        selected_company.symbol,
                        selected_company.name
                    )
                    st.rerun()

        with col2:
            if st.button(f"📊 Analyze {selected_company.symbol}", use_container_width=True):
                st.session_state.selected_ticker = selected_company.symbol
                st.rerun()


def render_results_cards(companies: List[CompanyInfo]):
    """Render results as cards"""
    search_filter = st.session_state.search_filter

    # Pagination
    items_per_page = 12
    total_pages = (len(companies) + items_per_page - 1) // items_per_page

    if total_pages > 1:
        page = st.selectbox("Page", range(1, total_pages + 1)) - 1
    else:
        page = 0

    start_idx = page * items_per_page
    end_idx = min(start_idx + items_per_page, len(companies))
    page_companies = companies[start_idx:end_idx]

    # Display cards in grid
    cols = st.columns(3)

    for i, company in enumerate(page_companies):
        col = cols[i % 3]

        with col:
            with st.container():
                # Company header
                market_cap_billions = company.market_cap / 1_000_000_000 if company.market_cap > 0 else 0

                bookmark_status = "⭐" if search_filter.bookmark_manager.is_bookmarked(company.symbol) else "☆"

                st.markdown(f"""
                <div style="border: 1px solid #ddd; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <h4>{bookmark_status} {company.symbol}</h4>
                    <p><strong>{company.name}</strong></p>
                    <p>🏢 {company.sector}</p>
                    <p>💰 ${market_cap_billions:.1f}B</p>
                    <p>🌍 {company.country} ({company.exchange})</p>
                </div>
                """, unsafe_allow_html=True)

                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📊", key=f"analyze_{company.symbol}_{i}", help="Analyze"):
                        st.session_state.selected_ticker = company.symbol
                        st.rerun()

                with col2:
                    if search_filter.bookmark_manager.is_bookmarked(company.symbol):
                        if st.button("🗑️", key=f"remove_{company.symbol}_{i}", help="Remove bookmark"):
                            search_filter.bookmark_manager.remove_bookmark(company.symbol)
                            st.rerun()
                    else:
                        if st.button("⭐", key=f"bookmark_{company.symbol}_{i}", help="Add bookmark"):
                            search_filter.bookmark_manager.add_bookmark(company.symbol, company.name)
                            st.rerun()


def render_results_chart(companies: List[CompanyInfo]):
    """Render results as charts"""
    import plotly.express as px
    import plotly.graph_objects as go

    # Prepare data for visualization
    df_data = []
    for company in companies:
        df_data.append({
            "Symbol": company.symbol,
            "Name": company.name,
            "Sector": company.sector,
            "Market_Cap": company.market_cap / 1_000_000_000,  # In billions
            "Country": company.country,
            "Exchange": company.exchange
        })

    df = pd.DataFrame(df_data)

    if df.empty:
        st.warning("No data to display")
        return

    # Chart type selection
    chart_type = st.selectbox(
        "Chart Type",
        ["Market Cap by Sector", "Geographic Distribution", "Exchange Distribution", "Market Cap Scatter"]
    )

    if chart_type == "Market Cap by Sector":
        # Market cap by sector
        sector_data = df.groupby('Sector')['Market_Cap'].sum().reset_index()
        sector_data = sector_data.sort_values('Market_Cap', ascending=False)

        fig = px.bar(
            sector_data,
            x='Sector',
            y='Market_Cap',
            title="Total Market Cap by Sector (Billions USD)",
            labels={'Market_Cap': 'Market Cap (Billions USD)'}
        )
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Geographic Distribution":
        # Geographic distribution
        country_counts = df['Country'].value_counts().head(10)
        fig = px.pie(
            values=country_counts.values,
            names=country_counts.index,
            title="Companies by Country (Top 10)"
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Exchange Distribution":
        # Exchange distribution
        exchange_counts = df['Exchange'].value_counts().head(10)
        fig = px.bar(
            x=exchange_counts.index,
            y=exchange_counts.values,
            title="Companies by Exchange",
            labels={'x': 'Exchange', 'y': 'Number of Companies'}
        )
        st.plotly_chart(fig, use_container_width=True)

    elif chart_type == "Market Cap Scatter":
        # Market cap scatter plot
        fig = px.scatter(
            df,
            x='Symbol',
            y='Market_Cap',
            color='Sector',
            size='Market_Cap',
            hover_data=['Name', 'Country'],
            title="Market Cap Distribution",
            labels={'Market_Cap': 'Market Cap (Billions USD)'}
        )
        fig.update_xaxis(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)


def populate_sample_companies():
    """Populate cache with sample companies for demonstration"""
    if 'search_filter' not in st.session_state:
        st.session_state.search_filter = AdvancedSearchFilter()

    search_filter = st.session_state.search_filter

    # Only populate if cache is empty or very small
    if len(search_filter.company_cache.get_all_companies()) < 20:
        sample_symbols = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'JPM', 'BAC', 'WMT', 'PG', 'JNJ', 'V', 'UNH', 'DIS', 'HD', 'MA',
            'PFE', 'VZ', 'ADBE', 'CRM', 'PYPL', 'INTC', 'CSCO', 'PEP', 'T',
            'ABT', 'TMO', 'COST'
        ]

        with st.spinner("Loading company data... This may take a moment."):
            # Use progress bar
            progress_bar = st.progress(0)
            for i, symbol in enumerate(sample_symbols):
                search_filter.fetch_company_info(symbol)
                progress_bar.progress((i + 1) / len(sample_symbols))

            progress_bar.empty()
            st.success(f"Loaded {len(sample_symbols)} companies into cache!")