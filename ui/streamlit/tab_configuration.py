"""
Tab Configuration Module for Streamlit Financial Analysis Dashboard

This module provides centralized tab configuration and management for the main
Streamlit application, replacing the complex conditional logic with a clean,
maintainable system.
"""

from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import streamlit as st


@dataclass
class TabDefinition:
    """Definition for a single tab in the dashboard."""
    key: str
    icon: str
    name: str
    full_name: str
    requires_features: List[str] = None
    description: str = ""

    def __post_init__(self):
        if self.requires_features is None:
            self.requires_features = []

    @property
    def display_name(self) -> str:
        """Get the display name with icon."""
        return f"{self.icon} {self.name}"


class TabManager:
    """Manages tab creation and configuration for the dashboard."""

    # Core tab definitions - always available
    CORE_TABS = [
        TabDefinition("search", "🔍", "Company Search", "Company Search & Discovery"),
        TabDefinition("fcf", "📈", "FCF Analysis", "Free Cash Flow Analysis"),
        TabDefinition("dcf", "💰", "DCF Valuation", "Discounted Cash Flow Valuation"),
        TabDefinition("ddm", "🏆", "DDM Valuation", "Dividend Discount Model Valuation"),
        TabDefinition("pb", "📊", "P/B Analysis", "Price-to-Book Analysis"),
        TabDefinition("esg", "🌱", "ESG Analysis", "Environmental, Social & Governance Analysis"),
        TabDefinition("ratios", "🧮", "Financial Ratios", "Financial Ratios Analysis"),
        TabDefinition("trends", "📊", "Financial Trends", "Financial Trends Analysis"),
        TabDefinition("comparison", "🔄", "Company Comparison", "Company Comparison Dashboard"),
        TabDefinition("report", "📄", "Generate Report", "Generate Analysis Reports"),
        TabDefinition("watchlist", "📊", "Watch Lists", "Watch Lists Management"),
        TabDefinition("performance", "🚀", "Performance Monitor", "Performance Monitoring Dashboard"),
        TabDefinition("help", "📚", "Help & Guide", "Help & User Guide"),
    ]

    # Feature-dependent tabs
    FEATURE_TABS = [
        TabDefinition("realtime", "📈", "Real-Time Prices", "Real-Time Price Monitoring",
                     requires_features=["REAL_TIME_PRICES_AVAILABLE"]),
        TabDefinition("portfolio", "💼", "Portfolio Analysis", "Portfolio Analysis Dashboard",
                     requires_features=["PORTFOLIO_VISUALIZATION_AVAILABLE"]),
        TabDefinition("risk", "⚡", "Risk Analysis", "Risk Analysis Dashboard",
                     requires_features=["RISK_ANALYSIS_AVAILABLE"]),
        TabDefinition("preferences", "⚙️", "User Preferences", "User Preferences Settings",
                     requires_features=["USER_PREFERENCES_AVAILABLE"]),
        TabDefinition("collaboration", "🤝", "Collaboration", "Collaboration Features",
                     requires_features=["COLLABORATION_AVAILABLE"]),
    ]

    # Special tabs for limited modes
    WELCOME_TAB = TabDefinition("welcome", "🏠", "Welcome", "Welcome Page")

    def __init__(self, feature_flags: Dict[str, bool] = None):
        """Initialize TabManager with feature flags."""
        self.feature_flags = feature_flags or {}

    def get_available_tabs(self, include_welcome: bool = False) -> List[TabDefinition]:
        """Get list of available tabs based on feature flags."""
        available_tabs = list(self.CORE_TABS)

        # Add feature-dependent tabs if available
        for tab in self.FEATURE_TABS:
            if self._is_tab_available(tab):
                available_tabs.append(tab)

        # Add welcome tab if requested
        if include_welcome:
            available_tabs.append(self.WELCOME_TAB)

        return available_tabs

    def _is_tab_available(self, tab: TabDefinition) -> bool:
        """Check if a tab should be available based on feature flags."""
        if not tab.requires_features:
            return True

        return all(
            self.feature_flags.get(feature, False)
            for feature in tab.requires_features
        )

    def create_tabs(self, include_welcome: bool = False) -> Tuple[List, Dict[str, int]]:
        """
        Create Streamlit tabs and return tab objects with mapping.

        Returns:
            Tuple of (tab_objects_list, tab_key_to_index_mapping)
        """
        available_tabs = self.get_available_tabs(include_welcome)

        # Create display names for tabs
        tab_names = [tab.display_name for tab in available_tabs]

        # Create the tabs using Streamlit
        tab_objects = st.tabs(tab_names)

        # Create mapping from tab keys to indices
        tab_mapping = {
            tab.key: idx for idx, tab in enumerate(available_tabs)
        }

        return tab_objects, tab_mapping

    def create_tabs_with_variables(self, include_welcome: bool = False) -> Tuple[Dict[str, any], Dict[str, any]]:
        """
        Create tabs and return them as a dictionary with named variables.

        This method provides backward compatibility with the existing code
        that expects specific variable names.

        Returns:
            Tuple of (variable_dict, enhanced_tab_mapping)
        """
        tab_objects, tab_mapping = self.create_tabs(include_welcome)

        # Create dictionary with standard variable names
        result = {}

        # Get available tabs for mapping
        available_tabs = self.get_available_tabs(include_welcome)

        # Create enhanced mapping with tab objects
        enhanced_mapping = {}

        # Assign tab objects to variables based on tab keys
        for i, tab in enumerate(available_tabs):
            tab_obj = tab_objects[i]
            enhanced_mapping[tab.key] = {"object": tab_obj, "index": i, "definition": tab}

            if tab.key == "search":
                result["tab_search"] = tab_obj
            elif tab.key == "welcome":
                result["welcome_tab"] = tab_obj
            else:
                # Assign to numbered variables in order
                tab_num = len([k for k in result.keys() if k.startswith("tab") and k[3:].isdigit()])
                result[f"tab{tab_num + 1}"] = tab_obj

        return result, enhanced_mapping

    def get_limited_tabs(self) -> Tuple[List, Dict[str, int]]:
        """
        Get limited tab set for when no data is available.
        Only includes search, watchlist, help, and optionally welcome.
        """
        limited_tabs = [
            self.CORE_TABS[0],  # search
            self.CORE_TABS[9],  # watchlist
            self.CORE_TABS[11], # help
        ]

        # Add real-time prices if available
        if self.feature_flags.get("REAL_TIME_PRICES_AVAILABLE", False):
            realtime_tab = next(
                (tab for tab in self.FEATURE_TABS if tab.key == "realtime"),
                None
            )
            if realtime_tab:
                limited_tabs.insert(-1, realtime_tab)

        # Add welcome tab
        limited_tabs.append(self.WELCOME_TAB)

        # Create display names and tabs
        tab_names = [tab.display_name for tab in limited_tabs]
        tab_objects = st.tabs(tab_names)

        # Create mapping
        tab_mapping = {
            tab.key: idx for idx, tab in enumerate(limited_tabs)
        }

        return tab_objects, tab_mapping

    def create_limited_tabs_with_variables(self) -> Dict[str, any]:
        """Create limited tabs with backward-compatible variable names."""
        tab_objects, tab_mapping = self.get_limited_tabs()

        result = {}

        # Map based on available tabs
        if "realtime" in tab_mapping:
            # With real-time prices: search, watchlist, realtime, help, welcome
            result["tab_search"] = tab_objects[tab_mapping["search"]]
            result["tab6"] = tab_objects[tab_mapping["watchlist"]]
            result["tab7"] = tab_objects[tab_mapping["realtime"]]
            result["tab8"] = tab_objects[tab_mapping["help"]]
            result["welcome_tab"] = tab_objects[tab_mapping["welcome"]]
        else:
            # Without real-time prices: search, watchlist, help, welcome
            result["tab_search"] = tab_objects[tab_mapping["search"]]
            result["tab6"] = tab_objects[tab_mapping["watchlist"]]
            result["tab7"] = tab_objects[tab_mapping["help"]]
            result["welcome_tab"] = tab_objects[tab_mapping["welcome"]]

        return result, tab_mapping


def create_feature_flags(**kwargs) -> Dict[str, bool]:
    """
    Helper function to create feature flags dictionary.

    Args:
        **kwargs: Feature flag names and their boolean values

    Returns:
        Dictionary of feature flags
    """
    return kwargs


# Convenience function for backward compatibility
def create_tabs_for_features(
    real_time_prices: bool = False,
    user_preferences: bool = False,
    collaboration: bool = False,
    portfolio_visualization: bool = False,
    risk_analysis: bool = False,
    include_welcome: bool = False
) -> Tuple[Dict[str, any], Dict[str, int]]:
    """
    Create tabs based on feature availability - backward compatibility function.

    Returns:
        Tuple of (variable_dict, tab_mapping)
    """
    feature_flags = {
        "REAL_TIME_PRICES_AVAILABLE": real_time_prices,
        "USER_PREFERENCES_AVAILABLE": user_preferences,
        "COLLABORATION_AVAILABLE": collaboration,
        "PORTFOLIO_VISUALIZATION_AVAILABLE": portfolio_visualization,
        "RISK_ANALYSIS_AVAILABLE": risk_analysis,
    }

    tab_manager = TabManager(feature_flags)
    return tab_manager.create_tabs_with_variables(include_welcome)