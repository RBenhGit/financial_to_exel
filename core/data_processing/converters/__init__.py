"""
Data Processing Converters
==========================

Converts raw API responses from various financial data providers into the
project's standardized field-name format.

All converters inherit from BaseConverter and implement a consistent interface.

Available Converters:
- AlphaVantageConverter  – Alpha Vantage API
- FMPConverter           – Financial Modeling Prep API
- YfinanceConverter      – Yahoo Finance (yfinance library)
- PolygonConverter       – Polygon.io API
- TwelveDataConverter    – Twelve Data API
"""

from .base_converter import BaseConverter
from .alpha_vantage_converter import AlphaVantageConverter
from .fmp_converter import FMPConverter
from .yfinance_converter import YfinanceConverter
from .polygon_converter import PolygonConverter
from .twelve_data_converter import TwelveDataConverter

__all__ = [
    "BaseConverter",
    "AlphaVantageConverter",
    "FMPConverter",
    "YfinanceConverter",
    "PolygonConverter",
    "TwelveDataConverter",
]
