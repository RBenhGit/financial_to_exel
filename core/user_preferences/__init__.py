"""
User Preferences System

This module provides personalized user preferences and customization options
with user profile management for the financial analysis application.
"""

from .user_profile import UserProfile, UserPreferences
from .preference_manager import UserPreferenceManager
from .ui_preferences import UIPreferences, ThemePreferences

__all__ = [
    'UserProfile',
    'UserPreferences',
    'UserPreferenceManager',
    'UIPreferences',
    'ThemePreferences'
]