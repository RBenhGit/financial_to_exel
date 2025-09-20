"""
Portfolio Data Persistence Module
=================================

This module provides data persistence functionality for portfolios, enabling
users to save, load, and manage their portfolios across sessions.

Key Features:
- JSON-based portfolio storage
- Portfolio versioning and backup
- Import/export functionality
- Data validation and migration
- User portfolio management

Storage Structure:
- data/portfolios/user_portfolios.json - Main portfolio storage
- data/portfolios/backups/ - Portfolio backups
- data/portfolios/exports/ - Export files
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from datetime import datetime, date
from dataclasses import asdict
import logging
import shutil
from enum import Enum

from .portfolio_models import (
    Portfolio, PortfolioHolding, PortfolioType,
    RebalancingStrategy, PositionSizingMethod,
    PortfolioAnalysisResult, create_sample_portfolio
)
from core.data_processing.data_contracts import MetadataInfo, DataQuality

logger = logging.getLogger(__name__)


class PortfolioStorageError(Exception):
    """Exception raised for portfolio storage operations"""
    pass


class PortfolioVersionError(Exception):
    """Exception raised for portfolio version conflicts"""
    pass


class PortfolioDataManager:
    """
    Comprehensive portfolio data management system

    Handles persistence, versioning, backup, and restoration of user portfolios
    """

    def __init__(self, base_path: Optional[str] = None):
        """Initialize portfolio data manager with storage configuration"""
        self.base_path = Path(base_path) if base_path else Path("data/portfolios")
        self.portfolios_file = self.base_path / "user_portfolios.json"
        self.backups_dir = self.base_path / "backups"
        self.exports_dir = self.base_path / "exports"

        # Create directories if they don't exist
        self._ensure_directories()

        # Portfolio cache for performance
        self._portfolio_cache: Dict[str, Portfolio] = {}
        self._cache_timestamp: Optional[datetime] = None

        logger.info(f"Portfolio data manager initialized with base path: {self.base_path}")

    def _ensure_directories(self) -> None:
        """Create necessary directories for portfolio storage"""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.backups_dir.mkdir(parents=True, exist_ok=True)
            self.exports_dir.mkdir(parents=True, exist_ok=True)

            # Create default portfolio file if it doesn't exist
            if not self.portfolios_file.exists():
                self._create_default_portfolio_file()

        except Exception as e:
            logger.error(f"Error creating portfolio directories: {e}")
            raise PortfolioStorageError(f"Failed to create portfolio directories: {e}")

    def _create_default_portfolio_file(self) -> None:
        """Create default portfolio storage file with sample data"""
        try:
            # Create sample portfolio for demonstration
            sample_portfolio = create_sample_portfolio()

            default_data = {
                "version": "1.0",
                "created_date": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "portfolios": {
                    sample_portfolio.portfolio_id: self._portfolio_to_dict(sample_portfolio)
                },
                "metadata": {
                    "total_portfolios": 1,
                    "storage_format": "json",
                    "backup_enabled": True
                }
            }

            with open(self.portfolios_file, 'w') as f:
                json.dump(default_data, f, indent=2, default=self._json_serializer)

            logger.info("Created default portfolio storage file with sample portfolio")

        except Exception as e:
            logger.error(f"Error creating default portfolio file: {e}")
            raise PortfolioStorageError(f"Failed to create default portfolio file: {e}")

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for portfolio objects"""
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            return obj.__dict__
        return str(obj)

    def _portfolio_to_dict(self, portfolio: Portfolio) -> Dict[str, Any]:
        """Convert portfolio object to dictionary for JSON storage"""
        try:
            # Convert portfolio to dictionary
            portfolio_dict = asdict(portfolio)

            # Handle special serialization cases
            portfolio_dict['portfolio_type'] = portfolio.portfolio_type.value
            portfolio_dict['rebalancing_strategy'] = portfolio.rebalancing_strategy.value
            portfolio_dict['position_sizing_method'] = portfolio.position_sizing_method.value

            # Convert dates to strings
            if portfolio_dict.get('inception_date'):
                portfolio_dict['inception_date'] = portfolio.inception_date.isoformat()
            if portfolio_dict.get('last_rebalance_date'):
                portfolio_dict['last_rebalance_date'] = portfolio.last_rebalance_date.isoformat()

            # Add persistence metadata
            portfolio_dict['_persistence_metadata'] = {
                'saved_date': datetime.now().isoformat(),
                'version': '1.0',
                'format': 'json'
            }

            return portfolio_dict

        except Exception as e:
            logger.error(f"Error converting portfolio to dictionary: {e}")
            raise PortfolioStorageError(f"Failed to serialize portfolio: {e}")

    def _dict_to_portfolio(self, portfolio_dict: Dict[str, Any]) -> Portfolio:
        """Convert dictionary to portfolio object"""
        try:
            # Create a copy to avoid modifying original
            data = portfolio_dict.copy()

            # Remove persistence metadata
            data.pop('_persistence_metadata', None)

            # Convert enum strings back to enums
            if 'portfolio_type' in data:
                data['portfolio_type'] = PortfolioType(data['portfolio_type'])
            if 'rebalancing_strategy' in data:
                data['rebalancing_strategy'] = RebalancingStrategy(data['rebalancing_strategy'])
            if 'position_sizing_method' in data:
                data['position_sizing_method'] = PositionSizingMethod(data['position_sizing_method'])

            # Convert date strings back to dates
            if 'inception_date' in data and isinstance(data['inception_date'], str):
                data['inception_date'] = datetime.fromisoformat(data['inception_date']).date()
            if 'last_rebalance_date' in data and isinstance(data['last_rebalance_date'], str):
                data['last_rebalance_date'] = datetime.fromisoformat(data['last_rebalance_date']).date()

            # Convert holdings list to PortfolioHolding objects
            if 'holdings' in data:
                holdings = []
                for holding_data in data['holdings']:
                    # Handle nested objects in holdings
                    if 'metadata' in holding_data and holding_data['metadata']:
                        holding_data['metadata'] = MetadataInfo(**holding_data['metadata'])
                    else:
                        holding_data['metadata'] = MetadataInfo()

                    # Convert dates in holdings
                    if 'purchase_date' in holding_data and isinstance(holding_data['purchase_date'], str):
                        holding_data['purchase_date'] = datetime.fromisoformat(holding_data['purchase_date']).date()
                    if 'last_rebalance_date' in holding_data and isinstance(holding_data['last_rebalance_date'], str):
                        holding_data['last_rebalance_date'] = datetime.fromisoformat(holding_data['last_rebalance_date']).date()

                    holdings.append(PortfolioHolding(**holding_data))
                data['holdings'] = holdings

            # Handle metadata object
            if 'metadata' in data and data['metadata']:
                data['metadata'] = MetadataInfo(**data['metadata'])
            else:
                data['metadata'] = MetadataInfo()

            # Create portfolio object
            portfolio = Portfolio(**data)

            return portfolio

        except Exception as e:
            logger.error(f"Error converting dictionary to portfolio: {e}")
            raise PortfolioStorageError(f"Failed to deserialize portfolio: {e}")

    def _load_portfolio_data(self) -> Dict[str, Any]:
        """Load portfolio data from storage file"""
        try:
            if not self.portfolios_file.exists():
                self._create_default_portfolio_file()

            with open(self.portfolios_file, 'r') as f:
                data = json.load(f)

            # Validate data structure
            if not isinstance(data, dict) or 'portfolios' not in data:
                raise PortfolioStorageError("Invalid portfolio data format")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error loading portfolios: {e}")
            raise PortfolioStorageError(f"Corrupted portfolio data file: {e}")
        except Exception as e:
            logger.error(f"Error loading portfolio data: {e}")
            raise PortfolioStorageError(f"Failed to load portfolio data: {e}")

    def _save_portfolio_data(self, data: Dict[str, Any]) -> None:
        """Save portfolio data to storage file with backup"""
        try:
            # Create backup before saving
            self._create_backup()

            # Update metadata
            data['last_modified'] = datetime.now().isoformat()
            data['metadata']['total_portfolios'] = len(data['portfolios'])

            # Write to temporary file first
            temp_file = self.portfolios_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2, default=self._json_serializer)

            # Atomic replacement
            shutil.move(str(temp_file), str(self.portfolios_file))

            # Clear cache to force reload
            self._portfolio_cache.clear()
            self._cache_timestamp = None

            logger.info("Portfolio data saved successfully")

        except Exception as e:
            logger.error(f"Error saving portfolio data: {e}")
            raise PortfolioStorageError(f"Failed to save portfolio data: {e}")

    def _create_backup(self) -> None:
        """Create backup of current portfolio data"""
        try:
            if self.portfolios_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.backups_dir / f"portfolios_backup_{timestamp}.json"
                shutil.copy2(str(self.portfolios_file), str(backup_file))

                # Keep only last 10 backups
                self._cleanup_old_backups()

        except Exception as e:
            logger.warning(f"Failed to create backup: {e}")

    def _cleanup_old_backups(self, max_backups: int = 10) -> None:
        """Remove old backup files, keeping only the most recent ones"""
        try:
            backup_files = list(self.backups_dir.glob("portfolios_backup_*.json"))
            if len(backup_files) > max_backups:
                # Sort by modification time and remove oldest
                backup_files.sort(key=lambda x: x.stat().st_mtime)
                for old_backup in backup_files[:-max_backups]:
                    old_backup.unlink()

        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")

    def _refresh_cache(self) -> None:
        """Refresh portfolio cache if needed"""
        try:
            file_mtime = datetime.fromtimestamp(self.portfolios_file.stat().st_mtime)

            if (not self._cache_timestamp or
                file_mtime > self._cache_timestamp or
                not self._portfolio_cache):

                data = self._load_portfolio_data()
                self._portfolio_cache = {}

                for portfolio_id, portfolio_data in data['portfolios'].items():
                    self._portfolio_cache[portfolio_id] = self._dict_to_portfolio(portfolio_data)

                self._cache_timestamp = datetime.now()
                logger.debug("Portfolio cache refreshed")

        except Exception as e:
            logger.error(f"Error refreshing portfolio cache: {e}")

    # Public API Methods

    def save_portfolio(self, portfolio: Portfolio) -> bool:
        """
        Save a portfolio to persistent storage

        Args:
            portfolio: Portfolio object to save

        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Validate portfolio
            if not portfolio.portfolio_id or not portfolio.name:
                raise ValueError("Portfolio must have valid ID and name")

            # Load current data
            data = self._load_portfolio_data()

            # Convert portfolio to dictionary
            portfolio_dict = self._portfolio_to_dict(portfolio)

            # Save to data structure
            data['portfolios'][portfolio.portfolio_id] = portfolio_dict

            # Save to file
            self._save_portfolio_data(data)

            logger.info(f"Portfolio '{portfolio.name}' saved successfully")
            return True

        except Exception as e:
            logger.error(f"Error saving portfolio '{portfolio.portfolio_id}': {e}")
            return False

    def load_portfolio(self, portfolio_id: str) -> Optional[Portfolio]:
        """
        Load a portfolio from persistent storage

        Args:
            portfolio_id: ID of portfolio to load

        Returns:
            Portfolio object if found, None otherwise
        """
        try:
            self._refresh_cache()

            if portfolio_id in self._portfolio_cache:
                logger.info(f"Portfolio '{portfolio_id}' loaded from cache")
                return self._portfolio_cache[portfolio_id]

            logger.warning(f"Portfolio '{portfolio_id}' not found")
            return None

        except Exception as e:
            logger.error(f"Error loading portfolio '{portfolio_id}': {e}")
            return None

    def list_portfolios(self) -> List[Dict[str, Any]]:
        """
        Get list of all saved portfolios with summary information

        Returns:
            List of portfolio summary dictionaries
        """
        try:
            self._refresh_cache()

            portfolio_list = []

            for portfolio_id, portfolio in self._portfolio_cache.items():
                summary = {
                    'portfolio_id': portfolio.portfolio_id,
                    'name': portfolio.name,
                    'description': portfolio.description,
                    'portfolio_type': portfolio.portfolio_type.value,
                    'holdings_count': len(portfolio.holdings),
                    'total_value': sum(h.market_value or 0 for h in portfolio.holdings),
                    'inception_date': portfolio.inception_date.isoformat() if portfolio.inception_date else None,
                    'last_update': portfolio.last_update.isoformat() if portfolio.last_update else None
                }
                portfolio_list.append(summary)

            # Sort by last update (most recent first)
            portfolio_list.sort(key=lambda x: x['last_update'] or '', reverse=True)

            return portfolio_list

        except Exception as e:
            logger.error(f"Error listing portfolios: {e}")
            return []

    def delete_portfolio(self, portfolio_id: str) -> bool:
        """
        Delete a portfolio from persistent storage

        Args:
            portfolio_id: ID of portfolio to delete

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Load current data
            data = self._load_portfolio_data()

            if portfolio_id not in data['portfolios']:
                logger.warning(f"Portfolio '{portfolio_id}' not found for deletion")
                return False

            # Remove portfolio
            del data['portfolios'][portfolio_id]

            # Save updated data
            self._save_portfolio_data(data)

            logger.info(f"Portfolio '{portfolio_id}' deleted successfully")
            return True

        except Exception as e:
            logger.error(f"Error deleting portfolio '{portfolio_id}': {e}")
            return False

    def export_portfolio(self, portfolio_id: str, export_format: str = 'json') -> Optional[str]:
        """
        Export a portfolio to external file

        Args:
            portfolio_id: ID of portfolio to export
            export_format: Export format ('json', 'csv', 'excel')

        Returns:
            Path to exported file if successful, None otherwise
        """
        try:
            portfolio = self.load_portfolio(portfolio_id)
            if not portfolio:
                return None

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if export_format.lower() == 'json':
                export_file = self.exports_dir / f"{portfolio_id}_export_{timestamp}.json"
                portfolio_dict = self._portfolio_to_dict(portfolio)

                with open(export_file, 'w') as f:
                    json.dump(portfolio_dict, f, indent=2, default=self._json_serializer)

            else:
                raise ValueError(f"Unsupported export format: {export_format}")

            logger.info(f"Portfolio '{portfolio_id}' exported to {export_file}")
            return str(export_file)

        except Exception as e:
            logger.error(f"Error exporting portfolio '{portfolio_id}': {e}")
            return None

    def import_portfolio(self, file_path: str) -> Optional[Portfolio]:
        """
        Import a portfolio from external file

        Args:
            file_path: Path to file to import

        Returns:
            Imported Portfolio object if successful, None otherwise
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"Import file not found: {file_path}")

            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    portfolio_dict = json.load(f)

                # Remove persistence metadata if present
                portfolio_dict.pop('_persistence_metadata', None)

                # Convert to portfolio object
                portfolio = self._dict_to_portfolio(portfolio_dict)

                # Generate new ID to avoid conflicts
                portfolio.portfolio_id = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

                logger.info(f"Portfolio imported from {file_path}")
                return portfolio

            else:
                raise ValueError(f"Unsupported import format: {file_path.suffix}")

        except Exception as e:
            logger.error(f"Error importing portfolio from '{file_path}': {e}")
            return None

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage system statistics

        Returns:
            Dictionary with storage statistics
        """
        try:
            self._refresh_cache()

            stats = {
                'total_portfolios': len(self._portfolio_cache),
                'storage_file_size': self.portfolios_file.stat().st_size if self.portfolios_file.exists() else 0,
                'backup_count': len(list(self.backups_dir.glob("*.json"))),
                'export_count': len(list(self.exports_dir.glob("*.json"))),
                'last_modified': datetime.fromtimestamp(
                    self.portfolios_file.stat().st_mtime
                ).isoformat() if self.portfolios_file.exists() else None,
                'cache_status': 'active' if self._portfolio_cache else 'empty'
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting storage stats: {e}")
            return {}


# Global portfolio data manager instance
_portfolio_manager: Optional[PortfolioDataManager] = None


def get_portfolio_manager() -> PortfolioDataManager:
    """Get global portfolio data manager instance"""
    global _portfolio_manager
    if _portfolio_manager is None:
        _portfolio_manager = PortfolioDataManager()
    return _portfolio_manager


def save_portfolio(portfolio: Portfolio) -> bool:
    """Convenience function to save a portfolio"""
    return get_portfolio_manager().save_portfolio(portfolio)


def load_portfolio(portfolio_id: str) -> Optional[Portfolio]:
    """Convenience function to load a portfolio"""
    return get_portfolio_manager().load_portfolio(portfolio_id)


def list_portfolios() -> List[Dict[str, Any]]:
    """Convenience function to list all portfolios"""
    return get_portfolio_manager().list_portfolios()


def delete_portfolio(portfolio_id: str) -> bool:
    """Convenience function to delete a portfolio"""
    return get_portfolio_manager().delete_portfolio(portfolio_id)