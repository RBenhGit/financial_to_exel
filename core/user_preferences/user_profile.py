"""
User Profile Data Models

Defines the core data structures for user profiles and preferences
in the financial analysis application.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class AnalysisMethodology(Enum):
    """Preferred analysis methodologies"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class CurrencyPreference(Enum):
    """Supported currency preferences"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    ILS = "ILS"  # Israeli Shekel for TASE stocks


class RegionPreference(Enum):
    """Regional market preferences"""
    NORTH_AMERICA = "north_america"
    EUROPE = "europe"
    ASIA_PACIFIC = "asia_pacific"
    EMERGING_MARKETS = "emerging_markets"
    GLOBAL = "global"
    ISRAEL = "israel"  # TASE market


@dataclass
class FinancialPreferences:
    """User's financial analysis preferences"""

    # Default valuation parameters
    default_discount_rate: float = 0.10  # 10%
    default_terminal_growth_rate: float = 0.025  # 2.5%
    default_projection_years: int = 5
    risk_free_rate: float = 0.03  # 3%
    market_risk_premium: float = 0.06  # 6%

    # Analysis methodology
    methodology: AnalysisMethodology = AnalysisMethodology.MODERATE

    # Regional and currency preferences
    primary_currency: CurrencyPreference = CurrencyPreference.USD
    preferred_regions: List[RegionPreference] = field(default_factory=lambda: [RegionPreference.GLOBAL])

    # DCF specific preferences
    dcf_terminal_method: str = "perpetual_growth"  # or "exit_multiple"
    dcf_sensitivity_analysis: bool = True

    # Risk assessment preferences
    include_beta_adjustment: bool = True
    use_country_risk_premium: bool = False

    # Custom parameters for specific methodologies
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DisplayPreferences:
    """User interface and display preferences"""

    # Number formatting
    decimal_places: int = 2
    use_thousands_separator: bool = True
    percentage_decimal_places: int = 1

    # Chart preferences
    chart_theme: str = "plotly"  # plotly, seaborn, matplotlib
    default_chart_type: str = "line"  # line, bar, candlestick
    show_grid: bool = True
    animation_enabled: bool = True

    # Table preferences
    max_rows_per_page: int = 50
    show_tooltips: bool = True
    highlight_negative_values: bool = True

    # Color preferences
    positive_color: str = "#00C851"  # Green
    negative_color: str = "#FF4444"  # Red
    neutral_color: str = "#33B5E5"  # Blue

    # Layout preferences
    sidebar_expanded: bool = True
    show_advanced_options: bool = False
    compact_mode: bool = False


@dataclass
class NotificationPreferences:
    """User notification and alert preferences"""

    # Email notifications (future feature)
    email_enabled: bool = False
    email_address: Optional[str] = None

    # In-app notifications
    show_calculation_warnings: bool = True
    show_data_quality_alerts: bool = True
    show_performance_tips: bool = True

    # Frequency settings
    daily_summary: bool = False
    weekly_report: bool = False

    # Alert thresholds
    price_change_threshold: float = 0.05  # 5% change
    valuation_change_threshold: float = 0.10  # 10% change


@dataclass
class DataSourcePreferences:
    """Data source and processing preferences"""

    # Primary data source preference
    prefer_excel_over_api: bool = True
    auto_refresh_data: bool = False
    cache_duration_hours: int = 24

    # API preferences
    preferred_api_sources: List[str] = field(default_factory=lambda: ["alpha_vantage", "yfinance"])
    api_timeout_seconds: int = 30
    max_retry_attempts: int = 3

    # Data quality preferences
    strict_validation: bool = False
    allow_missing_data: bool = True
    outlier_detection: bool = True

    # Export preferences
    default_export_format: str = "xlsx"  # xlsx, csv, json
    include_charts_in_export: bool = True
    export_directory: Optional[str] = None


@dataclass
class WatchListPreferences:
    """Watch list and portfolio tracking preferences"""

    # Default watch list settings
    max_companies_per_list: int = 50
    auto_sort_by: str = "market_cap"  # market_cap, alphabetical, performance

    # Refresh settings
    auto_refresh_enabled: bool = False
    refresh_interval_minutes: int = 60

    # Columns to display
    default_columns: List[str] = field(default_factory=lambda: [
        "ticker", "company_name", "current_price", "market_cap",
        "pe_ratio", "fcf_yield", "last_updated"
    ])

    # Alert settings
    price_alerts_enabled: bool = False
    valuation_alerts_enabled: bool = False


@dataclass
class UserPreferences:
    """Complete user preferences container"""

    financial: FinancialPreferences = field(default_factory=FinancialPreferences)
    display: DisplayPreferences = field(default_factory=DisplayPreferences)
    notifications: NotificationPreferences = field(default_factory=NotificationPreferences)
    data_sources: DataSourcePreferences = field(default_factory=DataSourcePreferences)
    watch_lists: WatchListPreferences = field(default_factory=WatchListPreferences)

    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "1.0"


@dataclass
class UserProfile:
    """Complete user profile with preferences and metadata"""

    # Basic profile information
    user_id: str
    username: str
    email: Optional[str] = None

    # Profile metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    login_count: int = 0

    # User preferences
    preferences: UserPreferences = field(default_factory=UserPreferences)

    # Usage statistics
    total_analyses_run: int = 0
    favorite_companies: List[str] = field(default_factory=list)
    recent_searches: List[str] = field(default_factory=list)

    # Custom settings
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary format"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserProfile':
        """Create UserProfile from dictionary"""
        # Handle datetime fields
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_login' in data and isinstance(data['last_login'], str):
            data['last_login'] = datetime.fromisoformat(data['last_login'])

        # Handle preferences nested structure
        if 'preferences' in data and isinstance(data['preferences'], dict):
            prefs_data = data['preferences']

            # Handle last_updated in preferences
            if 'last_updated' in prefs_data and isinstance(prefs_data['last_updated'], str):
                prefs_data['last_updated'] = datetime.fromisoformat(prefs_data['last_updated'])

            # Create preference objects with enum handling
            financial_data = prefs_data.get('financial', {})
            # Convert enum strings back to enum objects
            if 'methodology' in financial_data and isinstance(financial_data['methodology'], str):
                financial_data['methodology'] = AnalysisMethodology(financial_data['methodology'])
            if 'primary_currency' in financial_data and isinstance(financial_data['primary_currency'], str):
                financial_data['primary_currency'] = CurrencyPreference(financial_data['primary_currency'])
            if 'preferred_regions' in financial_data and isinstance(financial_data['preferred_regions'], list):
                financial_data['preferred_regions'] = [RegionPreference(r) for r in financial_data['preferred_regions']]

            financial_prefs = FinancialPreferences(**financial_data)
            display_prefs = DisplayPreferences(**prefs_data.get('display', {}))
            notification_prefs = NotificationPreferences(**prefs_data.get('notifications', {}))
            data_source_prefs = DataSourcePreferences(**prefs_data.get('data_sources', {}))
            watch_list_prefs = WatchListPreferences(**prefs_data.get('watch_lists', {}))

            data['preferences'] = UserPreferences(
                financial=financial_prefs,
                display=display_prefs,
                notifications=notification_prefs,
                data_sources=data_source_prefs,
                watch_lists=watch_list_prefs,
                last_updated=prefs_data.get('last_updated', datetime.now()),
                version=prefs_data.get('version', '1.0')
            )

        return cls(**data)

    def update_login_info(self) -> None:
        """Update login information"""
        self.last_login = datetime.now()
        self.login_count += 1

    def add_recent_search(self, search_term: str, max_recent: int = 10) -> None:
        """Add a search term to recent searches"""
        if search_term in self.recent_searches:
            self.recent_searches.remove(search_term)

        self.recent_searches.insert(0, search_term)

        # Keep only the most recent searches
        if len(self.recent_searches) > max_recent:
            self.recent_searches = self.recent_searches[:max_recent]

    def add_favorite_company(self, ticker: str) -> None:
        """Add a company to favorites"""
        ticker = ticker.upper()
        if ticker not in self.favorite_companies:
            self.favorite_companies.append(ticker)

    def remove_favorite_company(self, ticker: str) -> None:
        """Remove a company from favorites"""
        ticker = ticker.upper()
        if ticker in self.favorite_companies:
            self.favorite_companies.remove(ticker)

    def increment_analysis_count(self) -> None:
        """Increment the total analysis counter"""
        self.total_analyses_run += 1

    def get_financial_defaults(self) -> Dict[str, Any]:
        """Get financial analysis defaults for easy access"""
        return {
            'discount_rate': self.preferences.financial.default_discount_rate,
            'terminal_growth_rate': self.preferences.financial.default_terminal_growth_rate,
            'projection_years': self.preferences.financial.default_projection_years,
            'risk_free_rate': self.preferences.financial.risk_free_rate,
            'market_risk_premium': self.preferences.financial.market_risk_premium,
            'primary_currency': self.preferences.financial.primary_currency.value,
            'methodology': self.preferences.financial.methodology.value
        }

    def get_display_defaults(self) -> Dict[str, Any]:
        """Get display preferences for easy access"""
        return {
            'decimal_places': self.preferences.display.decimal_places,
            'chart_theme': self.preferences.display.chart_theme,
            'show_grid': self.preferences.display.show_grid,
            'positive_color': self.preferences.display.positive_color,
            'negative_color': self.preferences.display.negative_color,
            'sidebar_expanded': self.preferences.display.sidebar_expanded
        }


def create_default_user_profile(user_id: str, username: str, email: Optional[str] = None) -> UserProfile:
    """Create a new user profile with default preferences"""
    return UserProfile(
        user_id=user_id,
        username=username,
        email=email,
        preferences=UserPreferences()
    )