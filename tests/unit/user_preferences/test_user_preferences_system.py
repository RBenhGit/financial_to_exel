"""
Test suite for the user preferences system

Tests the complete user preferences functionality including
profile management, preferences storage, and UI integration.
"""

import json
import os
import tempfile
import shutil
import pytest
from datetime import datetime
from pathlib import Path

from core.user_preferences.user_profile import (
    UserProfile, UserPreferences, FinancialPreferences, DisplayPreferences,
    NotificationPreferences, DataSourcePreferences, WatchListPreferences,
    AnalysisMethodology, CurrencyPreference, RegionPreference,
    create_default_user_profile
)
from core.user_preferences.preference_manager import UserPreferenceManager
from core.user_preferences.ui_preferences import (
    UIPreferences, ThemePreferences, LayoutPreferences, AccessibilityPreferences,
    ThemeMode, ChartStyle, LayoutMode, ColorScheme
)


class TestUserProfile:
    """Test UserProfile data model functionality"""

    def test_create_default_profile(self):
        """Test creating a default user profile"""
        profile = create_default_user_profile("test_user", "Test User", "test@example.com")

        assert profile.user_id == "test_user"
        assert profile.username == "Test User"
        assert profile.email == "test@example.com"
        assert isinstance(profile.preferences, UserPreferences)
        assert profile.total_analyses_run == 0
        assert len(profile.favorite_companies) == 0

    def test_profile_to_dict_and_from_dict(self):
        """Test serialization and deserialization of user profile"""
        original_profile = create_default_user_profile("test_user", "Test User")
        original_profile.add_favorite_company("AAPL")
        original_profile.add_recent_search("Apple Inc")
        original_profile.increment_analysis_count()

        # Convert to dict and back
        profile_dict = original_profile.to_dict()
        reconstructed_profile = UserProfile.from_dict(profile_dict)

        assert reconstructed_profile.user_id == original_profile.user_id
        assert reconstructed_profile.username == original_profile.username
        assert reconstructed_profile.total_analyses_run == original_profile.total_analyses_run
        assert reconstructed_profile.favorite_companies == original_profile.favorite_companies
        assert reconstructed_profile.recent_searches == original_profile.recent_searches

    def test_financial_defaults(self):
        """Test getting financial defaults from profile"""
        profile = create_default_user_profile("test_user", "Test User")
        defaults = profile.get_financial_defaults()

        assert 'discount_rate' in defaults
        assert 'terminal_growth_rate' in defaults
        assert 'projection_years' in defaults
        assert defaults['primary_currency'] == 'USD'

    def test_add_remove_favorites(self):
        """Test adding and removing favorite companies"""
        profile = create_default_user_profile("test_user", "Test User")

        # Add favorites
        profile.add_favorite_company("AAPL")
        profile.add_favorite_company("msft")  # Should be converted to uppercase
        assert "AAPL" in profile.favorite_companies
        assert "MSFT" in profile.favorite_companies

        # Remove favorite
        profile.remove_favorite_company("AAPL")
        assert "AAPL" not in profile.favorite_companies
        assert "MSFT" in profile.favorite_companies

    def test_recent_searches(self):
        """Test recent search functionality"""
        profile = create_default_user_profile("test_user", "Test User")

        # Add searches
        profile.add_recent_search("Apple")
        profile.add_recent_search("Microsoft")
        profile.add_recent_search("Google")

        assert len(profile.recent_searches) == 3
        assert profile.recent_searches[0] == "Google"  # Most recent first

        # Add duplicate (should move to front)
        profile.add_recent_search("Apple")
        assert profile.recent_searches[0] == "Apple"
        assert len(profile.recent_searches) == 3  # No duplicates


class TestUserPreferenceManager:
    """Test UserPreferenceManager functionality"""

    def setup_method(self):
        """Set up test environment with temporary directory"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = UserPreferenceManager(data_directory=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir)

    def test_create_and_get_user(self):
        """Test creating and retrieving users"""
        # Create user
        profile = self.manager.create_user("test_user", "Test User", "test@example.com")
        assert profile.user_id == "test_user"
        assert profile.username == "Test User"
        assert profile.email == "test@example.com"

        # Retrieve user
        retrieved_profile = self.manager.get_user("test_user")
        assert retrieved_profile is not None
        assert retrieved_profile.user_id == "test_user"
        assert retrieved_profile.username == "Test User"

    def test_user_exists(self):
        """Test checking if user exists"""
        assert not self.manager.user_exists("nonexistent_user")

        self.manager.create_user("test_user", "Test User")
        assert self.manager.user_exists("test_user")

    def test_update_user(self):
        """Test updating user profile"""
        # Create user
        profile = self.manager.create_user("test_user", "Test User")
        profile.add_favorite_company("AAPL")

        # Update user
        success = self.manager.update_user(profile)
        assert success

        # Retrieve and verify
        retrieved_profile = self.manager.get_user("test_user")
        assert "AAPL" in retrieved_profile.favorite_companies

    def test_delete_user(self):
        """Test deleting users"""
        # Create user
        self.manager.create_user("test_user", "Test User")
        assert self.manager.user_exists("test_user")

        # Delete user
        success = self.manager.delete_user("test_user")
        assert success
        assert not self.manager.user_exists("test_user")

    def test_current_user_management(self):
        """Test current user management"""
        # Create user
        self.manager.create_user("test_user", "Test User")

        # Set current user
        success = self.manager.set_current_user("test_user")
        assert success

        # Get current user
        current_user = self.manager.get_current_user()
        assert current_user is not None
        assert current_user.user_id == "test_user"

        # Clear current user
        self.manager.clear_current_user()
        assert self.manager.get_current_user() is None

    def test_update_preferences(self):
        """Test updating user preferences"""
        # Create user
        self.manager.create_user("test_user", "Test User")

        # Update preferences
        new_prefs = UserPreferences()
        new_prefs.financial.default_discount_rate = 0.12
        new_prefs.display.decimal_places = 3

        success = self.manager.update_preferences("test_user", new_prefs)
        assert success

        # Verify update
        retrieved_prefs = self.manager.get_preferences("test_user")
        assert retrieved_prefs.financial.default_discount_rate == 0.12
        assert retrieved_prefs.display.decimal_places == 3

    def test_list_users(self):
        """Test listing all users"""
        # Create multiple users
        self.manager.create_user("user1", "User One")
        self.manager.create_user("user2", "User Two")

        # List users
        users = self.manager.list_users()
        assert len(users) == 2

        user_ids = [user['user_id'] for user in users]
        assert "user1" in user_ids
        assert "user2" in user_ids

    def test_user_analytics(self):
        """Test user analytics functionality"""
        # Create user and add some activity
        profile = self.manager.create_user("test_user", "Test User")
        profile.increment_analysis_count()
        profile.add_favorite_company("AAPL")
        profile.add_recent_search("Apple")
        self.manager.update_user(profile)

        # Get analytics
        analytics = self.manager.get_user_analytics("test_user")
        assert analytics is not None
        assert analytics['total_analyses'] == 1
        assert analytics['favorite_companies_count'] == 1
        assert analytics['recent_searches_count'] == 1

    def test_persistence(self):
        """Test that data persists across manager instances"""
        # Create user with first manager
        self.manager.create_user("test_user", "Test User")

        # Create new manager instance with same directory
        new_manager = UserPreferenceManager(data_directory=self.temp_dir)

        # Verify user exists in new manager
        assert new_manager.user_exists("test_user")
        profile = new_manager.get_user("test_user")
        assert profile.username == "Test User"


class TestUIPreferences:
    """Test UI preferences functionality"""

    def test_theme_preferences(self):
        """Test theme preferences functionality"""
        theme_prefs = ThemePreferences()
        theme_prefs.mode = ThemeMode.DARK
        theme_prefs.chart_style = ChartStyle.MINIMAL

        # Test color scheme retrieval
        colors = theme_prefs.get_active_colors()
        assert colors is not None

        # Test CSS generation
        css = theme_prefs.get_streamlit_css()
        assert isinstance(css, str)
        assert "background-color" in css

    def test_layout_preferences(self):
        """Test layout preferences functionality"""
        layout_prefs = LayoutPreferences()
        layout_prefs.mode = LayoutMode.COMPACT
        layout_prefs.rows_per_page = 50

        assert layout_prefs.mode == LayoutMode.COMPACT
        assert layout_prefs.rows_per_page == 50

    def test_accessibility_preferences(self):
        """Test accessibility preferences functionality"""
        accessibility_prefs = AccessibilityPreferences()
        accessibility_prefs.high_contrast_mode = True
        accessibility_prefs.large_text_mode = True

        assert accessibility_prefs.high_contrast_mode is True
        assert accessibility_prefs.large_text_mode is True

    def test_ui_preferences_config(self):
        """Test UI preferences configuration generation"""
        ui_prefs = UIPreferences()

        # Test chart configuration
        chart_config = ui_prefs.get_chart_config()
        assert 'height' in chart_config
        assert 'color_palette' in chart_config

        # Test table configuration
        table_config = ui_prefs.get_table_config()
        assert 'rows_per_page' in table_config
        assert 'enable_sorting' in table_config


class TestFinancialPreferences:
    """Test financial preferences functionality"""

    def test_default_values(self):
        """Test default financial preference values"""
        prefs = FinancialPreferences()

        assert prefs.default_discount_rate == 0.10
        assert prefs.default_terminal_growth_rate == 0.025
        assert prefs.default_projection_years == 5
        assert prefs.methodology == AnalysisMethodology.MODERATE
        assert prefs.primary_currency == CurrencyPreference.USD

    def test_enum_values(self):
        """Test enum values for financial preferences"""
        # Test methodology enum
        assert AnalysisMethodology.CONSERVATIVE.value == "conservative"
        assert AnalysisMethodology.AGGRESSIVE.value == "aggressive"

        # Test currency enum
        assert CurrencyPreference.USD.value == "USD"
        assert CurrencyPreference.EUR.value == "EUR"
        assert CurrencyPreference.ILS.value == "ILS"

        # Test region enum
        assert RegionPreference.NORTH_AMERICA.value == "north_america"
        assert RegionPreference.ISRAEL.value == "israel"


class TestDataSourcePreferences:
    """Test data source preferences functionality"""

    def test_default_values(self):
        """Test default data source preference values"""
        prefs = DataSourcePreferences()

        assert prefs.prefer_excel_over_api is True
        assert prefs.auto_refresh_data is False
        assert prefs.cache_duration_hours == 24
        assert prefs.api_timeout_seconds == 30

    def test_api_preferences(self):
        """Test API-related preferences"""
        prefs = DataSourcePreferences()

        assert "alpha_vantage" in prefs.preferred_api_sources
        assert "yfinance" in prefs.preferred_api_sources
        assert prefs.max_retry_attempts == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])