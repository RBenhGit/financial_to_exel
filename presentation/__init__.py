"""
Presentation Layer - Business Logic to UI Bridge
===============================================

Orchestrates communication between business logic and UI components
without coupling domain logic to presentation concerns.
"""

from .financial_presenter import FinancialAnalysisPresenter
from .dcf_presenter import DCFAnalysisPresenter  
from .watchlist_presenter import WatchListPresenter
from .settings_presenter import SettingsPresenter

__all__ = [
    'FinancialAnalysisPresenter',
    'DCFAnalysisPresenter', 
    'WatchListPresenter',
    'SettingsPresenter'
]