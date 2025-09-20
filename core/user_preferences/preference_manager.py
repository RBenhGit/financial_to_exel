"""
User Preference Manager

Handles storage, retrieval, and management of user preferences and profiles
for the financial analysis application.
"""

import json
import logging
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import threading

from .user_profile import UserProfile, UserPreferences, create_default_user_profile

logger = logging.getLogger(__name__)


class UserPreferenceManager:
    """Manages user preferences with persistent storage and caching"""

    def __init__(self, data_directory: Optional[str] = None, auto_save: bool = True):
        """
        Initialize the preference manager

        Args:
            data_directory: Directory to store user preference files
            auto_save: Whether to automatically save changes
        """
        self.auto_save = auto_save
        self._lock = threading.Lock()
        self._cache: Dict[str, UserProfile] = {}
        self._current_user: Optional[UserProfile] = None

        # Set up data directory
        if data_directory:
            self.data_dir = Path(data_directory)
        else:
            self.data_dir = Path("data") / "user_preferences"

        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Configuration file for manager settings
        self.config_file = self.data_dir / "manager_config.json"
        self._load_manager_config()

        logger.info(f"UserPreferenceManager initialized with data directory: {self.data_dir}")

    def _load_manager_config(self) -> None:
        """Load manager configuration settings"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.auto_save = config.get('auto_save', self.auto_save)
                    logger.info("Manager configuration loaded")
            else:
                self._save_manager_config()
        except Exception as e:
            logger.warning(f"Failed to load manager config: {e}")

    def _save_manager_config(self) -> None:
        """Save manager configuration settings"""
        try:
            config = {
                'auto_save': self.auto_save,
                'last_updated': datetime.now().isoformat(),
                'version': '1.0'
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save manager config: {e}")

    def _get_user_file_path(self, user_id: str) -> Path:
        """Get the file path for a user's preferences"""
        # Hash user_id for filename safety
        safe_id = hashlib.md5(user_id.encode()).hexdigest()[:16]
        return self.data_dir / f"user_{safe_id}.json"

    def _serialize_datetime(self, obj: Any) -> Any:
        """Custom JSON serializer for datetime and enum objects"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        # Handle enum serialization
        if hasattr(obj, 'value'):
            return obj.value
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    def create_user(
        self,
        user_id: str,
        username: str,
        email: Optional[str] = None,
        preferences: Optional[UserPreferences] = None
    ) -> UserProfile:
        """
        Create a new user profile

        Args:
            user_id: Unique user identifier
            username: Display username
            email: Optional email address
            preferences: Optional custom preferences (defaults will be used if None)

        Returns:
            UserProfile: The created user profile
        """
        with self._lock:
            if self.user_exists(user_id):
                raise ValueError(f"User {user_id} already exists")

            profile = create_default_user_profile(user_id, username, email)
            if preferences:
                profile.preferences = preferences

            self._cache[user_id] = profile

            if self.auto_save:
                self._save_user_profile(profile)

            logger.info(f"Created new user profile: {user_id} ({username})")
            return profile

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        """
        Get a user profile

        Args:
            user_id: User identifier

        Returns:
            UserProfile or None if not found
        """
        with self._lock:
            # Check cache first
            if user_id in self._cache:
                return self._cache[user_id]

            # Load from file
            profile = self._load_user_profile(user_id)
            if profile:
                self._cache[user_id] = profile

            return profile

    def update_user(self, user_profile: UserProfile) -> bool:
        """
        Update an existing user profile

        Args:
            user_profile: Updated user profile

        Returns:
            bool: True if successful
        """
        with self._lock:
            try:
                user_id = user_profile.user_id
                self._cache[user_id] = user_profile

                if self.auto_save:
                    return self._save_user_profile(user_profile)

                return True
            except Exception as e:
                logger.error(f"Failed to update user {user_profile.user_id}: {e}")
                return False

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user profile

        Args:
            user_id: User identifier

        Returns:
            bool: True if successful
        """
        with self._lock:
            try:
                # Remove from cache
                if user_id in self._cache:
                    del self._cache[user_id]

                # Remove file
                user_file = self._get_user_file_path(user_id)
                if user_file.exists():
                    user_file.unlink()

                # Clear current user if it's the deleted user
                if self._current_user and self._current_user.user_id == user_id:
                    self._current_user = None

                logger.info(f"Deleted user profile: {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete user {user_id}: {e}")
                return False

    def user_exists(self, user_id: str) -> bool:
        """
        Check if a user exists

        Args:
            user_id: User identifier

        Returns:
            bool: True if user exists
        """
        return user_id in self._cache or self._get_user_file_path(user_id).exists()

    def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users with basic information

        Returns:
            List of user information dictionaries
        """
        users = []

        # Get users from files
        for user_file in self.data_dir.glob("user_*.json"):
            try:
                with open(user_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    users.append({
                        'user_id': data.get('user_id'),
                        'username': data.get('username'),
                        'email': data.get('email'),
                        'created_at': data.get('created_at'),
                        'last_login': data.get('last_login'),
                        'login_count': data.get('login_count', 0)
                    })
            except Exception as e:
                logger.warning(f"Failed to read user file {user_file}: {e}")

        return users

    def set_current_user(self, user_id: str) -> bool:
        """
        Set the current active user

        Args:
            user_id: User identifier

        Returns:
            bool: True if successful
        """
        profile = self.get_user(user_id)
        if profile:
            self._current_user = profile
            profile.update_login_info()
            if self.auto_save:
                self._save_user_profile(profile)
            logger.info(f"Set current user: {user_id}")
            return True
        return False

    def get_current_user(self) -> Optional[UserProfile]:
        """
        Get the current active user

        Returns:
            UserProfile or None if no current user
        """
        return self._current_user

    def clear_current_user(self) -> None:
        """Clear the current active user"""
        self._current_user = None

    def update_preferences(
        self,
        user_id: str,
        preferences: UserPreferences,
        save_immediately: bool = None
    ) -> bool:
        """
        Update user preferences

        Args:
            user_id: User identifier
            preferences: New preferences
            save_immediately: Override auto_save setting

        Returns:
            bool: True if successful
        """
        profile = self.get_user(user_id)
        if not profile:
            return False

        profile.preferences = preferences
        profile.preferences.last_updated = datetime.now()

        self._cache[user_id] = profile

        should_save = save_immediately if save_immediately is not None else self.auto_save
        if should_save:
            return self._save_user_profile(profile)

        return True

    def get_preferences(self, user_id: str) -> Optional[UserPreferences]:
        """
        Get user preferences

        Args:
            user_id: User identifier

        Returns:
            UserPreferences or None if user not found
        """
        profile = self.get_user(user_id)
        return profile.preferences if profile else None

    def backup_all_users(self, backup_path: Optional[str] = None) -> bool:
        """
        Create a backup of all user data

        Args:
            backup_path: Optional custom backup path

        Returns:
            bool: True if successful
        """
        try:
            if backup_path:
                backup_dir = Path(backup_path)
            else:
                backup_dir = self.data_dir / "backups" / datetime.now().strftime("%Y%m%d_%H%M%S")

            backup_dir.mkdir(parents=True, exist_ok=True)

            # Copy all user files
            for user_file in self.data_dir.glob("user_*.json"):
                backup_file = backup_dir / user_file.name
                backup_file.write_text(user_file.read_text(encoding='utf-8'), encoding='utf-8')

            # Copy manager config
            if self.config_file.exists():
                backup_config = backup_dir / self.config_file.name
                backup_config.write_text(
                    self.config_file.read_text(encoding='utf-8'),
                    encoding='utf-8'
                )

            logger.info(f"User data backed up to: {backup_dir}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup user data: {e}")
            return False

    def save_all(self) -> bool:
        """
        Save all cached profiles to disk

        Returns:
            bool: True if all saves successful
        """
        success = True
        with self._lock:
            for profile in self._cache.values():
                if not self._save_user_profile(profile):
                    success = False
        return success

    def _save_user_profile(self, profile: UserProfile) -> bool:
        """Save a user profile to disk"""
        try:
            user_file = self._get_user_file_path(profile.user_id)
            profile_data = profile.to_dict()

            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, default=self._serialize_datetime)

            logger.debug(f"Saved user profile: {profile.user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user profile {profile.user_id}: {e}")
            return False

    def _load_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Load a user profile from disk"""
        try:
            user_file = self._get_user_file_path(user_id)
            if not user_file.exists():
                return None

            with open(user_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            profile = UserProfile.from_dict(data)
            logger.debug(f"Loaded user profile: {user_id}")
            return profile
        except Exception as e:
            logger.error(f"Failed to load user profile {user_id}: {e}")
            return None

    def get_user_analytics(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user analytics and usage statistics

        Args:
            user_id: User identifier

        Returns:
            Analytics dictionary or None if user not found
        """
        profile = self.get_user(user_id)
        if not profile:
            return None

        return {
            'user_id': profile.user_id,
            'username': profile.username,
            'created_at': profile.created_at.isoformat() if profile.created_at else None,
            'last_login': profile.last_login.isoformat() if profile.last_login else None,
            'login_count': profile.login_count,
            'total_analyses': profile.total_analyses_run,
            'favorite_companies_count': len(profile.favorite_companies),
            'recent_searches_count': len(profile.recent_searches),
            'preferences_last_updated': profile.preferences.last_updated.isoformat(),
            'custom_settings_count': len(profile.custom_settings)
        }


# Global instance
_preference_manager: Optional[UserPreferenceManager] = None


def get_preference_manager(
    data_directory: Optional[str] = None,
    auto_save: bool = True
) -> UserPreferenceManager:
    """
    Get the global preference manager instance

    Args:
        data_directory: Directory for user preference files
        auto_save: Whether to automatically save changes

    Returns:
        UserPreferenceManager instance
    """
    global _preference_manager
    if _preference_manager is None:
        _preference_manager = UserPreferenceManager(data_directory, auto_save)
    return _preference_manager


def set_preference_manager(manager: UserPreferenceManager) -> None:
    """Set a custom preference manager instance"""
    global _preference_manager
    _preference_manager = manager