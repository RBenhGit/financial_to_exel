"""
Utilities package for common functionality across the financial analysis application.

This package provides centralized utilities to eliminate code duplication and
provide consistent functionality across modules.
"""

# Import available utilities
try:
    from .growth_calculator import GrowthRateCalculator
except ImportError:
    GrowthRateCalculator = None

try:
    from .excel_processor import UnifiedExcelProcessor
except ImportError:
    UnifiedExcelProcessor = None

try:
    from .plotting_utils import PlottingUtils
except ImportError:
    PlottingUtils = None

__all__ = [
    name
    for name in ['GrowthRateCalculator', 'UnifiedExcelProcessor', 'PlottingUtils']
    if globals().get(name) is not None
]
