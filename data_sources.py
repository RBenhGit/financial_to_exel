"""
Alternative Financial Data Sources Module

This module implements a unified data adapter pattern for multiple financial data sources
including Alpha Vantage, Financial Modeling Prep, Polygon.io, and existing Excel inputs.
It provides fallback hierarchy, rate limiting, and standardized data formats.

Features:
- Unified data adapter interface
- Multiple API provider support
- Automatic fallback hierarchy
- Rate limiting and caching
- Data quality validation
- Cost management and usage tracking
"""

import os
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Protocol
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import hashlib
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

class DataSourceType(Enum):
    """Types of financial data sources"""
    EXCEL = "excel"
    ALPHA_VANTAGE = "alpha_vantage"
    FINANCIAL_MODELING_PREP = "fmp"
    POLYGON = "polygon"
    YFINANCE = "yfinance"

class DataSourcePriority(Enum):
    """Priority levels for data sources"""
    PRIMARY = 1
    SECONDARY = 2
    TERTIARY = 3
    FALLBACK = 4

@dataclass
class ApiCredentials:
    """Container for API credentials and configuration"""
    api_key: str
    base_url: str
    rate_limit_calls: int = 5  # calls per period
    rate_limit_period: int = 60  # seconds
    timeout: int = 30
    retry_attempts: int = 3
    cost_per_call: float = 0.0  # Cost in USD per API call
    monthly_limit: int = 1000  # Monthly call limit
    is_active: bool = True

@dataclass
class DataSourceConfig:
    """Configuration for a data source"""
    source_type: DataSourceType
    priority: DataSourcePriority
    credentials: Optional[ApiCredentials] = None
    is_enabled: bool = True
    quality_threshold: float = 0.8  # Minimum data quality score
    cache_ttl_hours: int = 24

@dataclass
class FinancialDataRequest:
    """Request parameters for financial data"""
    ticker: str
    data_types: List[str] = None  # ['price', 'fundamentals', 'ratios']
    period: str = 'annual'  # 'annual', 'quarterly', 'daily'
    limit: int = 10
    force_refresh: bool = False
    
    def __post_init__(self):
        if self.data_types is None:
            self.data_types = ['price', 'fundamentals']

@dataclass
class DataQualityMetrics:
    """Metrics for evaluating data quality"""
    completeness: float = 0.0  # Percentage of non-null values
    accuracy: float = 0.0  # Data accuracy score
    timeliness: float = 0.0  # How recent the data is
    consistency: float = 0.0  # Consistency with other sources
    overall_score: float = 0.0
    
    def calculate_overall_score(self):
        """Calculate overall quality score"""
        weights = {'completeness': 0.3, 'accuracy': 0.3, 'timeliness': 0.2, 'consistency': 0.2}
        self.overall_score = (
            self.completeness * weights['completeness'] +
            self.accuracy * weights['accuracy'] +
            self.timeliness * weights['timeliness'] +
            self.consistency * weights['consistency']
        )
        return self.overall_score

@dataclass
class DataSourceResponse:
    """Response from a data source"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    source_type: Optional[DataSourceType] = None
    quality_metrics: Optional[DataQualityMetrics] = None
    error_message: Optional[str] = None
    response_time: float = 0.0
    api_calls_used: int = 0
    cost_incurred: float = 0.0
    cache_hit: bool = False

class FinancialDataProvider(ABC):
    """Abstract base class for financial data providers"""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.last_request_time = datetime.min
        self._request_count = 0
        self._session = requests.Session()
        
    @abstractmethod
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch financial data from the provider"""
        pass
    
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Validate API credentials"""
        pass
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting"""
        if not self.config.credentials:
            return
            
        time_since_last = (datetime.now() - self.last_request_time).total_seconds()
        min_interval = self.config.credentials.rate_limit_period / self.config.credentials.rate_limit_calls
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
    
    def _standardize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize data format across providers"""
        # This method should be implemented by subclasses
        return raw_data
    
    def _calculate_quality_metrics(self, data: Dict[str, Any]) -> DataQualityMetrics:
        """Calculate data quality metrics"""
        metrics = DataQualityMetrics()
        
        if not data:
            return metrics
        
        # Calculate completeness
        total_fields = 0
        complete_fields = 0
        
        def count_fields(obj, depth=0):
            nonlocal total_fields, complete_fields
            if depth > 3:  # Prevent infinite recursion
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    total_fields += 1
                    if value is not None and value != '' and value != 0:
                        complete_fields += 1
                    if isinstance(value, (dict, list)):
                        count_fields(value, depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, (dict, list)):
                        count_fields(item, depth + 1)
        
        count_fields(data)
        metrics.completeness = complete_fields / total_fields if total_fields > 0 else 0.0
        
        # Calculate timeliness (assuming data has timestamp or date)
        current_time = datetime.now()
        data_timestamp = None
        
        # Look for timestamp fields
        timestamp_fields = ['timestamp', 'last_updated', 'date', 'reportDate']
        for field in timestamp_fields:
            if field in data and data[field]:
                try:
                    if isinstance(data[field], str):
                        data_timestamp = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                    elif isinstance(data[field], datetime):
                        data_timestamp = data[field]
                    break
                except:
                    continue
        
        if data_timestamp:
            age_hours = (current_time - data_timestamp).total_seconds() / 3600
            # More recent data gets higher score
            metrics.timeliness = max(0.0, 1.0 - (age_hours / (24 * 30)))  # 30 days = 0 score
        else:
            metrics.timeliness = 0.5  # Default if no timestamp
        
        # For now, set accuracy and consistency to reasonable defaults
        # These would be calculated by comparing with other sources in practice
        metrics.accuracy = 0.85  # Assume good accuracy
        metrics.consistency = 0.80  # Assume reasonable consistency
        
        metrics.calculate_overall_score()
        return metrics

class AlphaVantageProvider(FinancialDataProvider):
    """Alpha Vantage API provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://www.alphavantage.co/query"
    
    def validate_credentials(self) -> bool:
        """Validate Alpha Vantage API key"""
        if not self.config.credentials or not self.config.credentials.api_key:
            return False
        
        try:
            test_url = f"{self.base_url}?function=GLOBAL_QUOTE&symbol=AAPL&apikey={self.config.credentials.api_key}"
            response = self._session.get(test_url, timeout=10)
            data = response.json()
            
            # Check if we got an error message indicating invalid API key
            return "Error Message" not in data and "Global Quote" in data
            
        except Exception as e:
            logger.error(f"Alpha Vantage credential validation failed: {e}")
            return False
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch data from Alpha Vantage"""
        start_time = time.time()
        response = DataSourceResponse(success=False, source_type=DataSourceType.ALPHA_VANTAGE)
        
        try:
            if not self.config.credentials:
                response.error_message = "No credentials configured for Alpha Vantage"
                return response
            
            self._enforce_rate_limit()
            
            # Build API request based on data types requested
            data = {}
            api_calls = 0
            
            for data_type in request.data_types:
                if data_type == 'price':
                    price_data = self._fetch_price_data(request.ticker)
                    if price_data:
                        data.update(price_data)
                        api_calls += 1
                
                elif data_type == 'fundamentals':
                    fundamental_data = self._fetch_fundamental_data(request.ticker)
                    if fundamental_data:
                        data.update(fundamental_data)
                        api_calls += 1
            
            if data:
                standardized_data = self._standardize_data(data)
                response.data = standardized_data
                response.success = True
                response.quality_metrics = self._calculate_quality_metrics(standardized_data)
            else:
                response.error_message = "No data retrieved from Alpha Vantage"
            
            response.api_calls_used = api_calls
            response.cost_incurred = api_calls * self.config.credentials.cost_per_call
            self.last_request_time = datetime.now()
            
        except Exception as e:
            response.error_message = f"Alpha Vantage API error: {str(e)}"
            logger.error(f"Alpha Vantage fetch error: {e}")
        
        response.response_time = time.time() - start_time
        return response
    
    def _fetch_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch current price data"""
        try:
            url = f"{self.base_url}?function=GLOBAL_QUOTE&symbol={ticker}&apikey={self.config.credentials.api_key}"
            response = self._session.get(url, timeout=self.config.credentials.timeout)
            data = response.json()
            
            if "Global Quote" in data:
                quote = data["Global Quote"]
                return {
                    "current_price": float(quote.get("05. price", 0)),
                    "change_percent": float(quote.get("10. change percent", "0%").replace("%", "")),
                    "volume": int(quote.get("06. volume", 0)),
                    "last_updated": quote.get("07. latest trading day"),
                    "source": "alpha_vantage_quote"
                }
        except Exception as e:
            logger.error(f"Alpha Vantage price fetch error: {e}")
        return None
    
    def _fetch_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data including financial statements"""
        try:
            result = {}
            
            # Get company overview with key fundamentals
            overview_url = f"{self.base_url}?function=OVERVIEW&symbol={ticker}&apikey={self.config.credentials.api_key}"
            overview_response = self._session.get(overview_url, timeout=self.config.credentials.timeout)
            overview_data = overview_response.json()
            
            if overview_data and "Symbol" in overview_data:
                result.update({
                    "market_cap": float(overview_data.get("MarketCapitalization", 0)),
                    "pe_ratio": float(overview_data.get("PERatio", 0)) if overview_data.get("PERatio") != "None" else None,
                    "pb_ratio": float(overview_data.get("PriceToBookRatio", 0)) if overview_data.get("PriceToBookRatio") != "None" else None,
                    "dividend_yield": float(overview_data.get("DividendYield", 0)) if overview_data.get("DividendYield") != "None" else None,
                    "eps": float(overview_data.get("EPS", 0)) if overview_data.get("EPS") != "None" else None,
                    "revenue_ttm": float(overview_data.get("RevenueTTM", 0)),
                    "profit_margin": float(overview_data.get("ProfitMargin", 0)) if overview_data.get("ProfitMargin") != "None" else None,
                    "beta": float(overview_data.get("Beta", 0)) if overview_data.get("Beta") != "None" else None,
                    "source": "alpha_vantage_overview"
                })
                
                # Add financial statements
                financial_statements = self._fetch_financial_statements(ticker)
                if financial_statements:
                    result.update(financial_statements)
                
                return result
                
        except Exception as e:
            logger.error(f"Alpha Vantage fundamental fetch error: {e}")
        return None
    
    def _fetch_financial_statements(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch financial statements from Alpha Vantage"""
        try:
            statements = {}
            
            # Get Income Statement
            income_url = f"{self.base_url}?function=INCOME_STATEMENT&symbol={ticker}&apikey={self.config.credentials.api_key}"
            income_response = self._session.get(income_url, timeout=self.config.credentials.timeout)
            income_data = income_response.json()
            
            if "annualReports" in income_data:
                statements["income_statement"] = income_data["annualReports"]
            
            time.sleep(1)  # Respect rate limits
            
            # Get Balance Sheet
            balance_url = f"{self.base_url}?function=BALANCE_SHEET&symbol={ticker}&apikey={self.config.credentials.api_key}"
            balance_response = self._session.get(balance_url, timeout=self.config.credentials.timeout)
            balance_data = balance_response.json()
            
            if "annualReports" in balance_data:
                statements["balance_sheet"] = balance_data["annualReports"]
            
            time.sleep(1)  # Respect rate limits
            
            # Get Cash Flow Statement
            cashflow_url = f"{self.base_url}?function=CASH_FLOW&symbol={ticker}&apikey={self.config.credentials.api_key}"
            cashflow_response = self._session.get(cashflow_url, timeout=self.config.credentials.timeout)
            cashflow_data = cashflow_response.json()
            
            if "annualReports" in cashflow_data:
                statements["cash_flow"] = cashflow_data["annualReports"]
                
                # Calculate FCF from cash flow statement
                fcf_data = self._calculate_fcf_from_alpha_vantage(cashflow_data["annualReports"])
                if fcf_data:
                    statements.update(fcf_data)
            
            return statements if statements else None
            
        except Exception as e:
            logger.error(f"Alpha Vantage financial statements fetch error: {e}")
            return None
    
    def _calculate_fcf_from_alpha_vantage(self, cashflow_reports: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate Free Cash Flow from Alpha Vantage cash flow data using unified converter"""
        try:
            if not cashflow_reports:
                return None
            
            # Use the unified converter and calculation
            from alpha_vantage_converter import AlphaVantageConverter
            from financial_calculations import calculate_unified_fcf
            
            # Convert Alpha Vantage data to standardized format
            standardized_data = AlphaVantageConverter.convert_financial_data({"annualReports": cashflow_reports})
            
            # Calculate FCF using unified function
            fcf_result = calculate_unified_fcf(standardized_data)
            
            if fcf_result.get("success"):
                # Format result to match expected structure
                latest_report = cashflow_reports[0]
                return {
                    "free_cash_flow": fcf_result["free_cash_flow"],
                    "operating_cash_flow": fcf_result["operating_cash_flow"],
                    "capital_expenditures": fcf_result["capital_expenditures"],
                    "fcf_year": latest_report.get("fiscalDateEnding"),
                    "fcf_source": "alpha_vantage_unified_calculation",
                    "fcf_margin_percent": fcf_result.get("fcf_margin_percent")
                }
            else:
                logger.error(f"Unified FCF calculation failed for Alpha Vantage: {fcf_result.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Alpha Vantage FCF calculation error: {e}")
            return None

class FinancialModelingPrepProvider(FinancialDataProvider):
    """Financial Modeling Prep API provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://financialmodelingprep.com/api/v3"
    
    def validate_credentials(self) -> bool:
        """Validate FMP API key"""
        if not self.config.credentials or not self.config.credentials.api_key:
            return False
        
        try:
            test_url = f"{self.base_url}/quote/AAPL?apikey={self.config.credentials.api_key}"
            response = self._session.get(test_url, timeout=10)
            data = response.json()
            
            # FMP returns an error object if API key is invalid
            return not isinstance(data, dict) or "error" not in data
            
        except Exception as e:
            logger.error(f"FMP credential validation failed: {e}")
            return False
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch data from Financial Modeling Prep"""
        start_time = time.time()
        response = DataSourceResponse(success=False, source_type=DataSourceType.FINANCIAL_MODELING_PREP)
        
        try:
            if not self.config.credentials:
                response.error_message = "No credentials configured for Financial Modeling Prep"
                return response
            
            self._enforce_rate_limit()
            
            data = {}
            api_calls = 0
            
            for data_type in request.data_types:
                if data_type == 'price':
                    price_data = self._fetch_price_data(request.ticker)
                    if price_data:
                        data.update(price_data)
                        api_calls += 1
                
                elif data_type == 'fundamentals':
                    fundamental_data = self._fetch_fundamental_data(request.ticker)
                    if fundamental_data:
                        data.update(fundamental_data)
                        api_calls += 1
            
            if data:
                standardized_data = self._standardize_data(data)
                response.data = standardized_data
                response.success = True
                response.quality_metrics = self._calculate_quality_metrics(standardized_data)
            else:
                response.error_message = "No data retrieved from Financial Modeling Prep"
            
            response.api_calls_used = api_calls
            response.cost_incurred = api_calls * self.config.credentials.cost_per_call
            self.last_request_time = datetime.now()
            
        except Exception as e:
            response.error_message = f"FMP API error: {str(e)}"
            logger.error(f"FMP fetch error: {e}")
        
        response.response_time = time.time() - start_time
        return response
    
    def _fetch_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch current price data"""
        try:
            url = f"{self.base_url}/quote/{ticker}?apikey={self.config.credentials.api_key}"
            response = self._session.get(url, timeout=self.config.credentials.timeout)
            data = response.json()
            
            if data and isinstance(data, list) and len(data) > 0:
                quote = data[0]
                return {
                    "current_price": float(quote.get("price", 0)),
                    "change_percent": float(quote.get("changesPercentage", 0)),
                    "volume": int(quote.get("volume", 0)),
                    "market_cap": float(quote.get("marketCap", 0)),
                    "last_updated": datetime.now().isoformat(),
                    "source": "fmp_quote"
                }
        except Exception as e:
            logger.error(f"FMP price fetch error: {e}")
        return None
    
    def _fetch_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data including financial statements"""
        try:
            result = {}
            
            # Get company profile with key metrics
            profile_url = f"{self.base_url}/profile/{ticker}?apikey={self.config.credentials.api_key}"
            profile_response = self._session.get(profile_url, timeout=self.config.credentials.timeout)
            profile_data = profile_response.json()
            
            if profile_data and isinstance(profile_data, list) and len(profile_data) > 0:
                profile = profile_data[0]
                result.update({
                    "market_cap": float(profile.get("mktCap", 0)),
                    "pe_ratio": float(profile.get("pe", 0)) if profile.get("pe") else None,
                    "beta": float(profile.get("beta", 0)) if profile.get("beta") else None,
                    "dividend_yield": float(profile.get("lastDiv", 0)) if profile.get("lastDiv") else None,
                    "sector": profile.get("sector"),
                    "industry": profile.get("industry"),
                    "country": profile.get("country"),
                    "source": "fmp_profile"
                })
                
                # Add financial statements
                financial_statements = self._fetch_financial_statements_fmp(ticker)
                if financial_statements:
                    result.update(financial_statements)
                
                return result
                
        except Exception as e:
            logger.error(f"FMP fundamental fetch error: {e}")
        return None
    
    def _fetch_financial_statements_fmp(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch financial statements from Financial Modeling Prep"""
        try:
            statements = {}
            
            # Get Income Statement
            income_url = f"{self.base_url}/income-statement/{ticker}?limit=5&apikey={self.config.credentials.api_key}"
            income_response = self._session.get(income_url, timeout=self.config.credentials.timeout)
            income_data = income_response.json()
            
            if income_data and isinstance(income_data, list):
                statements["income_statement"] = income_data
            
            # Get Balance Sheet
            balance_url = f"{self.base_url}/balance-sheet-statement/{ticker}?limit=5&apikey={self.config.credentials.api_key}"
            balance_response = self._session.get(balance_url, timeout=self.config.credentials.timeout)
            balance_data = balance_response.json()
            
            if balance_data and isinstance(balance_data, list):
                statements["balance_sheet"] = balance_data
            
            # Get Cash Flow Statement
            cashflow_url = f"{self.base_url}/cash-flow-statement/{ticker}?limit=5&apikey={self.config.credentials.api_key}"
            cashflow_response = self._session.get(cashflow_url, timeout=self.config.credentials.timeout)
            cashflow_data = cashflow_response.json()
            
            if cashflow_data and isinstance(cashflow_data, list):
                statements["cash_flow"] = cashflow_data
                
                # Calculate FCF from cash flow statement
                fcf_data = self._calculate_fcf_from_fmp(cashflow_data)
                if fcf_data:
                    statements.update(fcf_data)
            
            return statements if statements else None
            
        except Exception as e:
            logger.error(f"FMP financial statements fetch error: {e}")
            return None
    
    def _calculate_fcf_from_fmp(self, cashflow_reports: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate Free Cash Flow from FMP cash flow data using converter and unified calculation"""
        try:
            from fmp_converter import FMPConverter
            from financial_calculations import calculate_unified_fcf
            
            if not cashflow_reports:
                return None
            
            # Convert FMP data to standardized format
            standardized_data = FMPConverter.convert_financial_data(cashflow_reports)
            if not standardized_data:
                logger.warning("FMP data conversion failed")
                return None
            
            # Use unified FCF calculation
            fcf_result = calculate_unified_fcf(standardized_data)
            if not fcf_result:
                logger.warning("Unified FCF calculation failed for FMP data")
                return None
            
            # Add FMP-specific metadata
            latest_report = cashflow_reports[0] if cashflow_reports else {}
            fcf_result["fcf_year"] = latest_report.get("calendarYear")
            fcf_result["fcf_source"] = "fmp_calculated"
            
            return fcf_result
            
        except Exception as e:
            logger.error(f"FMP FCF calculation error: {e}")
            return None

class PolygonProvider(FinancialDataProvider):
    """Polygon.io API provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        self.base_url = "https://api.polygon.io"
    
    def validate_credentials(self) -> bool:
        """Validate Polygon API key"""
        if not self.config.credentials or not self.config.credentials.api_key:
            return False
        
        try:
            test_url = f"{self.base_url}/v2/last/trade/AAPL?apikey={self.config.credentials.api_key}"
            response = self._session.get(test_url, timeout=10)
            
            # Polygon returns 401 for invalid API key
            return response.status_code != 401
            
        except Exception as e:
            logger.error(f"Polygon credential validation failed: {e}")
            return False
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch data from Polygon.io"""
        start_time = time.time()
        response = DataSourceResponse(success=False, source_type=DataSourceType.POLYGON)
        
        try:
            if not self.config.credentials:
                response.error_message = "No credentials configured for Polygon.io"
                return response
            
            self._enforce_rate_limit()
            
            data = {}
            api_calls = 0
            
            for data_type in request.data_types:
                if data_type == 'price':
                    price_data = self._fetch_price_data(request.ticker)
                    if price_data:
                        data.update(price_data)
                        api_calls += 1
                
                elif data_type == 'fundamentals':
                    fundamental_data = self._fetch_fundamental_data(request.ticker)
                    if fundamental_data:
                        data.update(fundamental_data)
                        api_calls += 1
            
            if data:
                standardized_data = self._standardize_data(data)
                response.data = standardized_data
                response.success = True
                response.quality_metrics = self._calculate_quality_metrics(standardized_data)
            else:
                response.error_message = "No data retrieved from Polygon.io"
            
            response.api_calls_used = api_calls
            response.cost_incurred = api_calls * self.config.credentials.cost_per_call
            self.last_request_time = datetime.now()
            
        except Exception as e:
            response.error_message = f"Polygon API error: {str(e)}"
            logger.error(f"Polygon fetch error: {e}")
        
        response.response_time = time.time() - start_time
        return response
    
    def _fetch_price_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch current price data"""
        try:
            # Get last trade
            url = f"{self.base_url}/v2/last/trade/{ticker}?apikey={self.config.credentials.api_key}"
            response = self._session.get(url, timeout=self.config.credentials.timeout)
            data = response.json()
            
            if data.get("status") == "OK" and "results" in data:
                results = data["results"]
                return {
                    "current_price": float(results.get("p", 0)),  # price
                    "volume": int(results.get("s", 0)),  # size
                    "timestamp": results.get("t"),  # timestamp
                    "last_updated": datetime.now().isoformat(),
                    "source": "polygon_last_trade"
                }
        except Exception as e:
            logger.error(f"Polygon price fetch error: {e}")
        return None
    
    def _fetch_fundamental_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data including financial statements"""
        try:
            result = {}
            
            # Get ticker details
            details_url = f"{self.base_url}/v3/reference/tickers/{ticker}?apikey={self.config.credentials.api_key}"
            details_response = self._session.get(details_url, timeout=self.config.credentials.timeout)
            details_data = details_response.json()
            
            if details_data.get("status") == "OK" and "results" in details_data:
                results = details_data["results"]
                result.update({
                    "market_cap": float(results.get("market_cap", 0)),
                    "shares_outstanding": float(results.get("share_class_shares_outstanding", 0)),
                    "currency": results.get("currency_name"),
                    "locale": results.get("locale"),
                    "type": results.get("type"),
                    "description": results.get("description"),
                    "source": "polygon_ticker_details"
                })
                
                # Add financial statements (Note: Polygon's financials API might be limited)
                financial_statements = self._fetch_financial_statements_polygon(ticker)
                if financial_statements:
                    result.update(financial_statements)
                
                return result
                
        except Exception as e:
            logger.error(f"Polygon fundamental fetch error: {e}")
        return None
    
    def _fetch_financial_statements_polygon(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Fetch financial statements from Polygon (limited availability)"""
        try:
            statements = {}
            
            # Note: Polygon's financials API might require higher tier access
            # Get basic financials if available
            financials_url = f"{self.base_url}/vX/reference/financials?ticker={ticker}&apikey={self.config.credentials.api_key}"
            financials_response = self._session.get(financials_url, timeout=self.config.credentials.timeout)
            
            if financials_response.status_code == 200:
                financials_data = financials_response.json()
                
                if financials_data.get("status") == "OK" and "results" in financials_data:
                    results = financials_data["results"]
                    
                    if results:
                        # Process financial data if available
                        statements["financials"] = results
                        
                        # Try to calculate FCF if cash flow data is available
                        fcf_data = self._calculate_fcf_from_polygon(results)
                        if fcf_data:
                            statements.update(fcf_data)
            
            return statements if statements else None
            
        except Exception as e:
            logger.error(f"Polygon financial statements fetch error: {e}")
            return None
    
    def _calculate_fcf_from_polygon(self, financial_results: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Calculate Free Cash Flow from Polygon financial data using converter and unified calculation"""
        try:
            from polygon_converter import PolygonConverter
            from financial_calculations import calculate_unified_fcf
            
            if not financial_results:
                return None
            
            # Convert Polygon data to standardized format
            polygon_response = {"results": financial_results}
            standardized_data = PolygonConverter.convert_financial_data(polygon_response)
            if not standardized_data:
                logger.warning("Polygon data conversion failed")
                return None
            
            # Use unified FCF calculation
            fcf_result = calculate_unified_fcf(standardized_data)
            if not fcf_result:
                logger.warning("Unified FCF calculation failed for Polygon data")
                return None
            
            # Add Polygon-specific metadata
            latest_result = financial_results[0] if financial_results else {}
            fcf_result["fcf_year"] = latest_result.get("fiscal_year")
            fcf_result["fcf_source"] = "polygon_calculated"
            
            return fcf_result
            
        except Exception as e:
            logger.error(f"Polygon FCF calculation error: {e}")
            return None

class ExcelDataProvider(FinancialDataProvider):
    """Excel file data provider (existing functionality)"""
    
    def __init__(self, config: DataSourceConfig, base_path: str):
        super().__init__(config)
        self.base_path = Path(base_path)
    
    def validate_credentials(self) -> bool:
        """Validate Excel file access"""
        return self.base_path.exists() and self.base_path.is_dir()
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch data from Excel files"""
        start_time = time.time()
        response = DataSourceResponse(success=False, source_type=DataSourceType.EXCEL)
        
        try:
            # Use existing centralized data manager for Excel loading
            from centralized_data_manager import CentralizedDataManager
            
            data_manager = CentralizedDataManager(str(self.base_path))
            excel_data = data_manager.load_excel_data(request.ticker.upper())
            
            if excel_data:
                # Convert Excel data to standardized format
                standardized_data = self._standardize_excel_data(excel_data, request.ticker)
                response.data = standardized_data
                response.success = True
                response.quality_metrics = self._calculate_quality_metrics(standardized_data)
            else:
                response.error_message = f"No Excel data found for {request.ticker}"
            
        except Exception as e:
            response.error_message = f"Excel data error: {str(e)}"
            logger.error(f"Excel fetch error: {e}")
        
        response.response_time = time.time() - start_time
        return response
    
    def _standardize_excel_data(self, excel_data: Dict[str, pd.DataFrame], ticker: str) -> Dict[str, Any]:
        """Convert Excel data to standardized format"""
        try:
            # Extract key financial metrics from Excel data
            result = {
                "ticker": ticker.upper(),
                "source": "excel_files",
                "financial_statements": {}
            }
            
            # Process different statement types
            for key, df in excel_data.items():
                if not df.empty:
                    # Convert DataFrame to dict while preserving structure
                    result["financial_statements"][key] = df.to_dict('records')
            
            result["last_updated"] = datetime.now().isoformat()
            return result
            
        except Exception as e:
            logger.error(f"Excel data standardization error: {e}")
            return {"ticker": ticker, "source": "excel_files", "error": str(e)}

class YfinanceProvider(FinancialDataProvider):
    """Yahoo Finance (yfinance) API provider"""
    
    def __init__(self, config: DataSourceConfig):
        super().__init__(config)
        # yfinance doesn't require API key authentication
        try:
            import yfinance as yf
            self.yf = yf
        except ImportError:
            raise ImportError("yfinance library is required. Install it with: pip install yfinance")
    
    def validate_credentials(self) -> bool:
        """Validate yfinance availability (no credentials needed)"""
        try:
            # Test with a simple ticker to ensure yfinance is working
            test_ticker = self.yf.Ticker("AAPL")
            info = test_ticker.info
            return len(info) > 0
        except Exception as e:
            logger.error(f"yfinance validation failed: {e}")
            return False
    
    def fetch_data(self, request: FinancialDataRequest) -> DataSourceResponse:
        """Fetch data from Yahoo Finance using yfinance"""
        start_time = time.time()
        response = DataSourceResponse(success=False, source_type=DataSourceType.YFINANCE)
        
        try:
            self._enforce_rate_limit()
            
            ticker = self.yf.Ticker(request.ticker)
            data = {}
            api_calls = 0
            
            for data_type in request.data_types:
                if data_type == 'price':
                    price_data = self._fetch_price_data(ticker)
                    if price_data:
                        data.update(price_data)
                        api_calls += 1
                
                elif data_type == 'fundamentals':
                    fundamental_data = self._fetch_fundamental_data(ticker)
                    if fundamental_data:
                        data.update(fundamental_data)
                        api_calls += 1
            
            if data:
                standardized_data = self._standardize_data(data)
                response.data = standardized_data
                response.success = True
                response.quality_metrics = self._calculate_quality_metrics(standardized_data)
            else:
                response.error_message = f"No data retrieved from yfinance for {request.ticker}"
            
            response.api_calls_used = api_calls
            response.cost_incurred = 0.0  # yfinance is free
            self.last_request_time = datetime.now()
            
        except Exception as e:
            response.error_message = f"yfinance API error: {str(e)}"
            logger.error(f"yfinance fetch error: {e}")
        
        response.response_time = time.time() - start_time
        return response
    
    def _fetch_price_data(self, ticker) -> Optional[Dict[str, Any]]:
        """Fetch current price data from yfinance"""
        try:
            info = ticker.info
            hist = ticker.history(period="1d", interval="1d")
            
            if not hist.empty and info:
                latest = hist.iloc[-1]
                return {
                    "current_price": float(latest['Close']) if 'Close' in latest else float(info.get('currentPrice', 0)),
                    "volume": int(latest['Volume']) if 'Volume' in latest else int(info.get('volume', 0)),
                    "market_cap": float(info.get('marketCap', 0)),
                    "last_updated": datetime.now().isoformat(),
                    "source": "yfinance_price"
                }
        except Exception as e:
            logger.error(f"yfinance price fetch error: {e}")
        return None
    
    def _fetch_fundamental_data(self, ticker) -> Optional[Dict[str, Any]]:
        """Fetch fundamental data from yfinance"""
        try:
            info = ticker.info
            financials = ticker.financials
            balance_sheet = ticker.balance_sheet
            cashflow = ticker.cashflow
            
            if info:
                result = {
                    "market_cap": float(info.get('marketCap', 0)),
                    "pe_ratio": float(info.get('trailingPE', 0)) if info.get('trailingPE') else None,
                    "pb_ratio": float(info.get('priceToBook', 0)) if info.get('priceToBook') else None,
                    "dividend_yield": float(info.get('dividendYield', 0)) if info.get('dividendYield') else None,
                    "eps": float(info.get('trailingEps', 0)) if info.get('trailingEps') else None,
                    "revenue_ttm": float(info.get('totalRevenue', 0)),
                    "profit_margin": float(info.get('profitMargins', 0)) if info.get('profitMargins') else None,
                    "beta": float(info.get('beta', 0)) if info.get('beta') else None,
                    "sector": info.get('sector'),
                    "industry": info.get('industry'),
                    "source": "yfinance_fundamentals"
                }
                
                # Add financial statements if available
                if not financials.empty:
                    result["financials"] = financials.to_dict('records')
                
                if not balance_sheet.empty:
                    result["balance_sheet"] = balance_sheet.to_dict('records')
                
                if not cashflow.empty:
                    result["cashflow"] = cashflow.to_dict('records')
                    
                    # Calculate FCF from cashflow statement
                    fcf_data = self._calculate_fcf_from_cashflow(cashflow)
                    if fcf_data:
                        result.update(fcf_data)
                
                return result
        except Exception as e:
            logger.error(f"yfinance fundamental fetch error: {e}")
        return None
    
    def _calculate_fcf_from_cashflow(self, cashflow) -> Optional[Dict[str, Any]]:
        """Calculate Free Cash Flow from yfinance cashflow statement using converter and unified calculation"""
        try:
            from yfinance_converter import YfinanceConverter
            from financial_calculations import calculate_unified_fcf
            
            if cashflow.empty:
                return None
            
            # Convert yfinance data to standardized format
            standardized_data = YfinanceConverter.convert_financial_data(cashflow)
            if not standardized_data:
                logger.warning("yfinance data conversion failed")
                return None
            
            # Use unified FCF calculation
            fcf_result = calculate_unified_fcf(standardized_data)
            if not fcf_result:
                logger.warning("Unified FCF calculation failed for yfinance data")
                return None
            
            # Add yfinance-specific metadata
            latest_year = cashflow.columns[0] if len(cashflow.columns) > 0 else None
            fcf_result["fcf_year"] = str(latest_year)[:4] if latest_year else None
            fcf_result["fcf_source"] = "yfinance_calculated"
            
            return fcf_result
            
        except Exception as e:
            logger.error(f"yfinance FCF calculation error: {e}")
            return None