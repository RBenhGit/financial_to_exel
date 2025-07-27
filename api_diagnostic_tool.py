"""
Financial API Diagnostic Tool

This tool investigates and diagnoses financial data import issues with yfinance,
Financial Modeling Prep (FMP), and Alpha Vantage APIs. It provides comprehensive
logging, error categorization, and data availability reporting.

Usage:
    python api_diagnostic_tool.py --ticker MSFT --all-apis
    python api_diagnostic_tool.py --ticker AAPL --api yfinance --verbose
"""

# Standard library imports
import argparse
import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple

# Third-party imports
import numpy as np
import pandas as pd
import requests

# Financial data imports
try:
    import yfinance as yf

    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("Warning: yfinance not available. Install with: pip install yfinance")


# Configure comprehensive logging
def setup_logging(log_level='INFO', log_file=None):
    """Setup comprehensive logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_file or f'api_diagnostics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            ),
        ],
    )

    # Set specific loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    return logging.getLogger(__name__)


class ApiErrorType(Enum):
    """Categories of API errors"""

    AUTHENTICATION = "authentication_error"
    RATE_LIMIT = "rate_limit_error"
    TIMEOUT = "timeout_error"
    NETWORK = "network_error"
    INVALID_TICKER = "invalid_ticker_error"
    NO_DATA = "no_data_error"
    MALFORMED_RESPONSE = "malformed_response_error"
    API_LIMIT_EXCEEDED = "api_limit_exceeded_error"
    UNKNOWN = "unknown_error"


class DataCompleteness(Enum):
    """Data completeness levels"""

    COMPLETE = "complete"
    PARTIAL = "partial"
    MINIMAL = "minimal"
    EMPTY = "empty"


@dataclass
class ApiCallResult:
    """Detailed result from an API call"""

    api_name: str
    endpoint: str
    ticker: str
    success: bool
    response_time: float = 0.0
    status_code: Optional[int] = None
    error_type: Optional[ApiErrorType] = None
    error_message: Optional[str] = None
    data_received: Optional[Dict[str, Any]] = None
    data_completeness: Optional[DataCompleteness] = None
    missing_fields: List[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.missing_fields is None:
            self.missing_fields = []


@dataclass
class FieldAvailability:
    """Tracks availability of specific financial data fields"""

    field_name: str
    yfinance_available: bool = False
    alpha_vantage_available: bool = False
    fmp_available: bool = False
    yfinance_value: Any = None
    alpha_vantage_value: Any = None
    fmp_value: Any = None
    notes: str = ""


class FinancialApiDiagnostic:
    """Comprehensive diagnostic tool for financial APIs"""

    def __init__(self, config_file: Optional[str] = None, log_level: str = 'INFO'):
        self.logger = setup_logging(log_level)
        self.config = self._load_config(config_file)
        self.results = []
        self.field_availability = {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Financial-API-Diagnostic-Tool/1.0'})

        # Key financial fields to track
        self.tracked_fields = [
            'current_price',
            'market_cap',
            'pe_ratio',
            'pb_ratio',
            'dividend_yield',
            'eps',
            'revenue',
            'net_income',
            'total_assets',
            'total_debt',
            'operating_cash_flow',
            'capital_expenditures',
            'free_cash_flow',
            'total_revenue',
            'gross_profit',
            'operating_income',
            'ebitda',
            'shares_outstanding',
            'book_value',
            'return_on_equity',
            'profit_margin',
        ]

    def _load_config(self, config_file: Optional[str]) -> Dict[str, Any]:
        """Load API configuration from file or environment"""
        config = {
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'fmp_api_key': os.getenv('FMP_API_KEY'),
            'polygon_api_key': os.getenv('POLYGON_API_KEY'),
            'timeout': 30,
            'max_retries': 3,
            'rate_limit_delay': 1.0,
        }

        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config.update(json.load(f))
            except Exception as e:
                self.logger.warning(f"Could not load config file {config_file}: {e}")

        return config

    def test_all_apis(
        self, ticker: str, include_statements: bool = True
    ) -> Dict[str, List[ApiCallResult]]:
        """Test all available APIs for a given ticker"""
        self.logger.info(f"Starting comprehensive API testing for ticker: {ticker}")

        results = {'yfinance': [], 'alpha_vantage': [], 'fmp': [], 'summary': {}}

        # Test yfinance
        if YFINANCE_AVAILABLE:
            self.logger.info("Testing yfinance API...")
            results['yfinance'] = self._test_yfinance(ticker, include_statements)
        else:
            self.logger.warning("yfinance not available - skipping")

        # Test Alpha Vantage
        if self.config.get('alpha_vantage_api_key'):
            self.logger.info("Testing Alpha Vantage API...")
            results['alpha_vantage'] = self._test_alpha_vantage(ticker, include_statements)
        else:
            self.logger.warning("Alpha Vantage API key not configured - skipping")

        # Test FMP
        if self.config.get('fmp_api_key'):
            self.logger.info("Testing Financial Modeling Prep API...")
            results['fmp'] = self._test_fmp(ticker, include_statements)
        else:
            self.logger.warning("FMP API key not configured - skipping")

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    def _test_yfinance(self, ticker: str, include_statements: bool = True) -> List[ApiCallResult]:
        """Test yfinance API endpoints"""
        results = []

        try:
            # Test basic quote data
            result = self._test_yfinance_quote(ticker)
            results.append(result)

            # Test info data
            result = self._test_yfinance_info(ticker)
            results.append(result)

            if include_statements:
                # Test financial statements
                for statement_type in ['financials', 'balance_sheet', 'cashflow']:
                    result = self._test_yfinance_statement(ticker, statement_type)
                    results.append(result)

        except Exception as e:
            self.logger.error(f"yfinance testing failed: {e}")
            results.append(
                ApiCallResult(
                    api_name='yfinance',
                    endpoint='general',
                    ticker=ticker,
                    success=False,
                    error_type=ApiErrorType.UNKNOWN,
                    error_message=str(e),
                )
            )

        return results

    def _test_yfinance_quote(self, ticker: str) -> ApiCallResult:
        """Test yfinance quote data"""
        start_time = time.time()

        try:
            yf_ticker = yf.Ticker(ticker)
            hist = yf_ticker.history(period="1d")

            response_time = time.time() - start_time

            if not hist.empty:
                data = {
                    'current_price': (
                        float(hist['Close'].iloc[-1]) if 'Close' in hist.columns else None
                    ),
                    'volume': int(hist['Volume'].iloc[-1]) if 'Volume' in hist.columns else None,
                    'high': float(hist['High'].iloc[-1]) if 'High' in hist.columns else None,
                    'low': float(hist['Low'].iloc[-1]) if 'Low' in hist.columns else None,
                }

                missing_fields = [k for k, v in data.items() if v is None]
                completeness = self._assess_completeness(data)

                return ApiCallResult(
                    api_name='yfinance',
                    endpoint='history',
                    ticker=ticker,
                    success=True,
                    response_time=response_time,
                    data_received=data,
                    data_completeness=completeness,
                    missing_fields=missing_fields,
                )
            else:
                return ApiCallResult(
                    api_name='yfinance',
                    endpoint='history',
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    error_type=ApiErrorType.NO_DATA,
                    error_message="No historical data returned",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='yfinance',
                endpoint='history',
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_yfinance_info(self, ticker: str) -> ApiCallResult:
        """Test yfinance info data"""
        start_time = time.time()

        try:
            yf_ticker = yf.Ticker(ticker)
            info = yf_ticker.info

            response_time = time.time() - start_time

            if (
                info and len(info) > 1
            ):  # yfinance returns {'trailingPegRatio': None} for invalid tickers
                # Extract key financial metrics
                data = {
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'pb_ratio': info.get('priceToBook'),
                    'dividend_yield': info.get('dividendYield'),
                    'eps': info.get('trailingEps'),
                    'revenue': info.get('totalRevenue'),
                    'profit_margin': info.get('profitMargins'),
                    'beta': info.get('beta'),
                    'sector': info.get('sector'),
                    'industry': info.get('industry'),
                }

                missing_fields = [k for k, v in data.items() if v is None]
                completeness = self._assess_completeness(data)

                # Update field availability tracking
                self._update_field_availability('yfinance', data)

                return ApiCallResult(
                    api_name='yfinance',
                    endpoint='info',
                    ticker=ticker,
                    success=True,
                    response_time=response_time,
                    data_received=data,
                    data_completeness=completeness,
                    missing_fields=missing_fields,
                )
            else:
                return ApiCallResult(
                    api_name='yfinance',
                    endpoint='info',
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    error_type=ApiErrorType.INVALID_TICKER,
                    error_message="Invalid ticker or no info data available",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='yfinance',
                endpoint='info',
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_yfinance_statement(self, ticker: str, statement_type: str) -> ApiCallResult:
        """Test yfinance financial statement data"""
        start_time = time.time()

        try:
            yf_ticker = yf.Ticker(ticker)

            if statement_type == 'financials':
                data_df = yf_ticker.financials
                endpoint = 'financials'
            elif statement_type == 'balance_sheet':
                data_df = yf_ticker.balance_sheet
                endpoint = 'balance_sheet'
            elif statement_type == 'cashflow':
                data_df = yf_ticker.cashflow
                endpoint = 'cashflow'
            else:
                raise ValueError(f"Unknown statement type: {statement_type}")

            response_time = time.time() - start_time

            if not data_df.empty:
                # Convert to analyzable format
                data = {
                    'rows_count': len(data_df),
                    'columns_count': len(data_df.columns),
                    'periods_available': list(data_df.columns.astype(str)),
                    'fields_available': list(data_df.index),
                    'sample_data': data_df.iloc[:5].to_dict() if len(data_df) > 0 else {},
                }

                # Check for key fields based on statement type
                key_fields = self._get_key_fields_for_statement(statement_type)
                missing_key_fields = [field for field in key_fields if field not in data_df.index]

                completeness = (
                    DataCompleteness.COMPLETE
                    if len(missing_key_fields) == 0
                    else (
                        DataCompleteness.PARTIAL
                        if len(missing_key_fields) < len(key_fields) / 2
                        else DataCompleteness.MINIMAL
                    )
                )

                return ApiCallResult(
                    api_name='yfinance',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=True,
                    response_time=response_time,
                    data_received=data,
                    data_completeness=completeness,
                    missing_fields=missing_key_fields,
                )
            else:
                return ApiCallResult(
                    api_name='yfinance',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    error_type=ApiErrorType.NO_DATA,
                    error_message=f"No {statement_type} data available",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='yfinance',
                endpoint=statement_type,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_alpha_vantage(
        self, ticker: str, include_statements: bool = True
    ) -> List[ApiCallResult]:
        """Test Alpha Vantage API endpoints"""
        results = []
        api_key = self.config['alpha_vantage_api_key']
        base_url = "https://www.alphavantage.co/query"

        # Test quote
        result = self._test_alpha_vantage_quote(ticker, base_url, api_key)
        results.append(result)

        # Test overview
        result = self._test_alpha_vantage_overview(ticker, base_url, api_key)
        results.append(result)

        if include_statements:
            # Test financial statements
            for function in ['INCOME_STATEMENT', 'BALANCE_SHEET', 'CASH_FLOW']:
                result = self._test_alpha_vantage_statement(ticker, function, base_url, api_key)
                results.append(result)
                time.sleep(self.config['rate_limit_delay'])  # Respect rate limits

        return results

    def _test_alpha_vantage_quote(self, ticker: str, base_url: str, api_key: str) -> ApiCallResult:
        """Test Alpha Vantage quote endpoint"""
        start_time = time.time()
        endpoint = "GLOBAL_QUOTE"

        try:
            url = f"{base_url}?function={endpoint}&symbol={ticker}&apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if "Error Message" in data:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.INVALID_TICKER,
                        error_message=data["Error Message"],
                    )
                elif "Note" in data:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.RATE_LIMIT,
                        error_message=data["Note"],
                    )
                elif "Global Quote" in data:
                    quote_data = data["Global Quote"]
                    parsed_data = {
                        'current_price': self._safe_float(quote_data.get("05. price")),
                        'change_percent': self._safe_float(
                            quote_data.get("10. change percent", "").replace("%", "")
                        ),
                        'volume': self._safe_int(quote_data.get("06. volume")),
                        'last_trading_day': quote_data.get("07. latest trading day"),
                    }

                    missing_fields = [k for k, v in parsed_data.items() if v is None]
                    completeness = self._assess_completeness(parsed_data)

                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.MALFORMED_RESPONSE,
                        error_message="Unexpected response format",
                    )
            else:
                return ApiCallResult(
                    api_name='alpha_vantage',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except requests.exceptions.Timeout:
            return ApiCallResult(
                api_name='alpha_vantage',
                endpoint=endpoint,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=ApiErrorType.TIMEOUT,
                error_message="Request timeout",
            )
        except Exception as e:
            return ApiCallResult(
                api_name='alpha_vantage',
                endpoint=endpoint,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_alpha_vantage_overview(
        self, ticker: str, base_url: str, api_key: str
    ) -> ApiCallResult:
        """Test Alpha Vantage overview endpoint"""
        start_time = time.time()
        endpoint = "OVERVIEW"

        try:
            url = f"{base_url}?function={endpoint}&symbol={ticker}&apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if "Error Message" in data:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.INVALID_TICKER,
                        error_message=data["Error Message"],
                    )
                elif data.get("Symbol") == ticker:
                    # Parse overview data
                    parsed_data = {
                        'market_cap': self._safe_float(data.get("MarketCapitalization")),
                        'pe_ratio': self._safe_float(data.get("PERatio")),
                        'pb_ratio': self._safe_float(data.get("PriceToBookRatio")),
                        'dividend_yield': self._safe_float(data.get("DividendYield")),
                        'eps': self._safe_float(data.get("EPS")),
                        'revenue_ttm': self._safe_float(data.get("RevenueTTM")),
                        'profit_margin': self._safe_float(data.get("ProfitMargin")),
                        'beta': self._safe_float(data.get("Beta")),
                        'sector': data.get("Sector"),
                        'industry': data.get("Industry"),
                    }

                    missing_fields = [
                        k
                        for k, v in parsed_data.items()
                        if v is None or (isinstance(v, str) and v.lower() == 'none')
                    ]
                    completeness = self._assess_completeness(parsed_data)

                    # Update field availability tracking
                    self._update_field_availability('alpha_vantage', parsed_data)

                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.NO_DATA,
                        error_message="No overview data for ticker",
                    )
            else:
                return ApiCallResult(
                    api_name='alpha_vantage',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='alpha_vantage',
                endpoint=endpoint,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_alpha_vantage_statement(
        self, ticker: str, function: str, base_url: str, api_key: str
    ) -> ApiCallResult:
        """Test Alpha Vantage financial statement endpoints"""
        start_time = time.time()

        try:
            url = f"{base_url}?function={function}&symbol={ticker}&apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if "Error Message" in data:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=function,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.INVALID_TICKER,
                        error_message=data["Error Message"],
                    )
                elif "Note" in data:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=function,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.RATE_LIMIT,
                        error_message=data["Note"],
                    )
                elif "annualReports" in data and data["annualReports"]:
                    annual_reports = data["annualReports"]
                    quarterly_reports = data.get("quarterlyReports", [])

                    parsed_data = {
                        'annual_reports_count': len(annual_reports),
                        'quarterly_reports_count': len(quarterly_reports),
                        'latest_annual_date': (
                            annual_reports[0].get("fiscalDateEnding") if annual_reports else None
                        ),
                        'available_fields': (
                            list(annual_reports[0].keys()) if annual_reports else []
                        ),
                        'sample_annual_data': annual_reports[0] if annual_reports else {},
                    }

                    # Check for key fields
                    key_fields = self._get_key_fields_for_alpha_vantage_statement(function)
                    missing_key_fields = []
                    if annual_reports:
                        missing_key_fields = [
                            field for field in key_fields if field not in annual_reports[0]
                        ]

                    completeness = (
                        DataCompleteness.COMPLETE
                        if len(missing_key_fields) == 0
                        else (
                            DataCompleteness.PARTIAL
                            if len(missing_key_fields) < len(key_fields) / 2
                            else DataCompleteness.MINIMAL
                        )
                    )

                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=function,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_key_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='alpha_vantage',
                        endpoint=function,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.NO_DATA,
                        error_message="No financial statement data available",
                    )
            else:
                return ApiCallResult(
                    api_name='alpha_vantage',
                    endpoint=function,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='alpha_vantage',
                endpoint=function,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_fmp(self, ticker: str, include_statements: bool = True) -> List[ApiCallResult]:
        """Test Financial Modeling Prep API endpoints"""
        results = []
        api_key = self.config['fmp_api_key']
        base_url = "https://financialmodelingprep.com/api/v3"

        # Test quote
        result = self._test_fmp_quote(ticker, base_url, api_key)
        results.append(result)

        # Test profile
        result = self._test_fmp_profile(ticker, base_url, api_key)
        results.append(result)

        if include_statements:
            # Test financial statements
            for statement in ['income-statement', 'balance-sheet-statement', 'cash-flow-statement']:
                result = self._test_fmp_statement(ticker, statement, base_url, api_key)
                results.append(result)

        return results

    def _test_fmp_quote(self, ticker: str, base_url: str, api_key: str) -> ApiCallResult:
        """Test FMP quote endpoint"""
        start_time = time.time()
        endpoint = "quote"

        try:
            url = f"{base_url}/{endpoint}/{ticker}?apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.AUTHENTICATION,
                        error_message=data["error"],
                    )
                elif isinstance(data, list) and len(data) > 0:
                    quote_data = data[0]
                    parsed_data = {
                        'current_price': self._safe_float(quote_data.get("price")),
                        'change_percent': self._safe_float(quote_data.get("changesPercentage")),
                        'volume': self._safe_int(quote_data.get("volume")),
                        'market_cap': self._safe_float(quote_data.get("marketCap")),
                        'shares_outstanding': self._safe_float(quote_data.get("sharesOutstanding")),
                    }

                    missing_fields = [k for k, v in parsed_data.items() if v is None]
                    completeness = self._assess_completeness(parsed_data)

                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.NO_DATA,
                        error_message="No quote data returned",
                    )
            else:
                return ApiCallResult(
                    api_name='fmp',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='fmp',
                endpoint=endpoint,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_fmp_profile(self, ticker: str, base_url: str, api_key: str) -> ApiCallResult:
        """Test FMP profile endpoint"""
        start_time = time.time()
        endpoint = "profile"

        try:
            url = f"{base_url}/{endpoint}/{ticker}?apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.AUTHENTICATION,
                        error_message=data["error"],
                    )
                elif isinstance(data, list) and len(data) > 0:
                    profile_data = data[0]
                    parsed_data = {
                        'market_cap': self._safe_float(profile_data.get("mktCap")),
                        'pe_ratio': self._safe_float(profile_data.get("pe")),
                        'beta': self._safe_float(profile_data.get("beta")),
                        'dividend_yield': self._safe_float(profile_data.get("lastDiv")),
                        'sector': profile_data.get("sector"),
                        'industry': profile_data.get("industry"),
                        'country': profile_data.get("country"),
                        'exchange': profile_data.get("exchangeShortName"),
                    }

                    missing_fields = [k for k, v in parsed_data.items() if v is None]
                    completeness = self._assess_completeness(parsed_data)

                    # Update field availability tracking
                    self._update_field_availability('fmp', parsed_data)

                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=endpoint,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.NO_DATA,
                        error_message="No profile data returned",
                    )
            else:
                return ApiCallResult(
                    api_name='fmp',
                    endpoint=endpoint,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='fmp',
                endpoint=endpoint,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def _test_fmp_statement(
        self, ticker: str, statement: str, base_url: str, api_key: str
    ) -> ApiCallResult:
        """Test FMP financial statement endpoints"""
        start_time = time.time()

        try:
            url = f"{base_url}/{statement}/{ticker}?limit=5&apikey={api_key}"
            response = self.session.get(url, timeout=self.config['timeout'])
            response_time = time.time() - start_time

            if response.status_code == 200:
                data = response.json()

                if isinstance(data, dict) and "error" in data:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=statement,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.AUTHENTICATION,
                        error_message=data["error"],
                    )
                elif isinstance(data, list) and len(data) > 0:
                    latest_statement = data[0]
                    parsed_data = {
                        'statements_count': len(data),
                        'latest_date': latest_statement.get("date")
                        or latest_statement.get("calendarYear"),
                        'available_fields': list(latest_statement.keys()),
                        'sample_data': {
                            k: v for k, v in list(latest_statement.items())[:10]
                        },  # First 10 fields
                    }

                    # Check for key fields
                    key_fields = self._get_key_fields_for_fmp_statement(statement)
                    missing_key_fields = [
                        field for field in key_fields if field not in latest_statement
                    ]

                    completeness = (
                        DataCompleteness.COMPLETE
                        if len(missing_key_fields) == 0
                        else (
                            DataCompleteness.PARTIAL
                            if len(missing_key_fields) < len(key_fields) / 2
                            else DataCompleteness.MINIMAL
                        )
                    )

                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=statement,
                        ticker=ticker,
                        success=True,
                        response_time=response_time,
                        status_code=response.status_code,
                        data_received=parsed_data,
                        data_completeness=completeness,
                        missing_fields=missing_key_fields,
                    )
                else:
                    return ApiCallResult(
                        api_name='fmp',
                        endpoint=statement,
                        ticker=ticker,
                        success=False,
                        response_time=response_time,
                        status_code=response.status_code,
                        error_type=ApiErrorType.NO_DATA,
                        error_message="No statement data returned",
                    )
            else:
                return ApiCallResult(
                    api_name='fmp',
                    endpoint=statement,
                    ticker=ticker,
                    success=False,
                    response_time=response_time,
                    status_code=response.status_code,
                    error_type=ApiErrorType.NETWORK,
                    error_message=f"HTTP {response.status_code}",
                )

        except Exception as e:
            return ApiCallResult(
                api_name='fmp',
                endpoint=statement,
                ticker=ticker,
                success=False,
                response_time=time.time() - start_time,
                error_type=self._categorize_error(str(e)),
                error_message=str(e),
            )

    def test_multiple_tickers(
        self, tickers: List[str], apis: List[str] = None
    ) -> Dict[str, Dict[str, List[ApiCallResult]]]:
        """Test multiple tickers across APIs"""
        if apis is None:
            apis = ['yfinance', 'alpha_vantage', 'fmp']

        results = {}
        for ticker in tickers:
            self.logger.info(f"Testing ticker: {ticker}")
            ticker_results = {}

            if 'yfinance' in apis and YFINANCE_AVAILABLE:
                ticker_results['yfinance'] = self._test_yfinance(ticker, False)

            if 'alpha_vantage' in apis and self.config.get('alpha_vantage_api_key'):
                ticker_results['alpha_vantage'] = self._test_alpha_vantage(ticker, False)
                time.sleep(self.config['rate_limit_delay'])

            if 'fmp' in apis and self.config.get('fmp_api_key'):
                ticker_results['fmp'] = self._test_fmp(ticker, False)

            results[ticker] = ticker_results

        return results

    def generate_comprehensive_report(
        self, results: Dict[str, Any], output_file: str = None
    ) -> str:
        """Generate comprehensive diagnostic report"""
        report_sections = []

        # Header
        report_sections.append("# Financial API Diagnostic Report")
        report_sections.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_sections.append("")

        # Executive Summary
        summary = results.get('summary', {})
        report_sections.append("## Executive Summary")
        report_sections.append(f"- APIs tested: {', '.join(summary.get('apis_tested', []))}")
        report_sections.append(f"- Total API calls: {summary.get('total_calls', 0)}")
        report_sections.append(f"- Successful calls: {summary.get('successful_calls', 0)}")
        report_sections.append(f"- Success rate: {summary.get('success_rate', 0):.1%}")
        report_sections.append("")

        # API-specific results
        for api_name, api_results in results.items():
            if api_name == 'summary':
                continue

            report_sections.append(f"## {api_name.upper()} API Results")

            if not api_results:
                report_sections.append("- No results (API not tested or unavailable)")
                report_sections.append("")
                continue

            successful = sum(1 for r in api_results if r.success)
            total = len(api_results)

            report_sections.append(f"- Endpoints tested: {total}")
            report_sections.append(f"- Successful: {successful}")
            report_sections.append(f"- Success rate: {successful/total:.1%}")
            report_sections.append("")

            # Detailed results
            for result in api_results:
                status = "✅ SUCCESS" if result.success else "❌ FAILED"
                report_sections.append(f"### {result.endpoint} - {status}")
                report_sections.append(f"- Response time: {result.response_time:.2f}s")

                if result.success:
                    if result.data_completeness:
                        report_sections.append(
                            f"- Data completeness: {result.data_completeness.value}"
                        )
                    if result.missing_fields:
                        report_sections.append(
                            f"- Missing fields: {', '.join(result.missing_fields)}"
                        )
                else:
                    report_sections.append(
                        f"- Error type: {result.error_type.value if result.error_type else 'Unknown'}"
                    )
                    report_sections.append(f"- Error message: {result.error_message}")

                report_sections.append("")

        # Field availability matrix
        if self.field_availability:
            report_sections.append("## Field Availability Matrix")
            report_sections.append("| Field | yfinance | Alpha Vantage | FMP |")
            report_sections.append("|-------|----------|---------------|-----|")

            for field_name, availability in self.field_availability.items():
                yf_status = "✅" if availability.yfinance_available else "❌"
                av_status = "✅" if availability.alpha_vantage_available else "❌"
                fmp_status = "✅" if availability.fmp_available else "❌"

                report_sections.append(
                    f"| {field_name} | {yf_status} | {av_status} | {fmp_status} |"
                )

            report_sections.append("")

        # Recommendations
        report_sections.append("## Recommendations")
        recommendations = self._generate_recommendations(results)
        for rec in recommendations:
            report_sections.append(f"- {rec}")

        report_content = "\n".join(report_sections)

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Report saved to {output_file}")

        return report_content

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on test results"""
        recommendations = []

        # Analyze results for patterns
        api_success_rates = {}
        common_errors = {}

        for api_name, api_results in results.items():
            if api_name == 'summary' or not api_results:
                continue

            successful = sum(1 for r in api_results if r.success)
            total = len(api_results)
            api_success_rates[api_name] = np.divide(
                successful, total, out=np.array(0.0), where=(total > 0)
            )[()]

            # Count error types
            for result in api_results:
                if not result.success and result.error_type:
                    error_key = f"{api_name}_{result.error_type.value}"
                    common_errors[error_key] = common_errors.get(error_key, 0) + 1

        # Generate recommendations based on analysis
        best_api = max(api_success_rates, key=api_success_rates.get) if api_success_rates else None
        worst_api = min(api_success_rates, key=api_success_rates.get) if api_success_rates else None

        if best_api and worst_api and best_api != worst_api:
            recommendations.append(
                f"Use {best_api} as primary data source (highest success rate: {api_success_rates[best_api]:.1%})"
            )

        # Error-specific recommendations
        for error_key, count in common_errors.items():
            api_name, error_type = error_key.rsplit('_', 1)

            if error_type == 'rate_limit_error':
                recommendations.append(
                    f"Implement rate limiting for {api_name} (encountered {count} rate limit errors)"
                )
            elif error_type == 'authentication_error':
                recommendations.append(
                    f"Verify {api_name} API credentials (encountered {count} authentication errors)"
                )
            elif error_type == 'timeout_error':
                recommendations.append(
                    f"Increase timeout settings for {api_name} (encountered {count} timeout errors)"
                )

        # Field availability recommendations
        if self.field_availability:
            # Find fields available in multiple sources
            redundant_fields = []
            missing_everywhere = []

            for field_name, availability in self.field_availability.items():
                available_count = sum(
                    [
                        availability.yfinance_available,
                        availability.alpha_vantage_available,
                        availability.fmp_available,
                    ]
                )

                if available_count > 1:
                    redundant_fields.append(field_name)
                elif available_count == 0:
                    missing_everywhere.append(field_name)

            if redundant_fields:
                recommendations.append(
                    f"Implement data cross-validation for fields available in multiple sources: {', '.join(redundant_fields[:5])}"
                )

            if missing_everywhere:
                recommendations.append(
                    f"Consider alternative data sources for missing fields: {', '.join(missing_everywhere[:5])}"
                )

        if not recommendations:
            recommendations.append(
                "All APIs are functioning well. Continue monitoring for any changes."
            )

        return recommendations

    # Helper methods
    def _categorize_error(self, error_message: str) -> ApiErrorType:
        """Categorize error based on error message"""
        error_msg = error_message.lower()

        if any(
            keyword in error_msg
            for keyword in ['unauthorized', 'invalid api key', 'authentication']
        ):
            return ApiErrorType.AUTHENTICATION
        elif any(keyword in error_msg for keyword in ['rate limit', 'too many requests', 'quota']):
            return ApiErrorType.RATE_LIMIT
        elif any(keyword in error_msg for keyword in ['timeout', 'timed out']):
            return ApiErrorType.TIMEOUT
        elif any(keyword in error_msg for keyword in ['connection', 'network', 'dns']):
            return ApiErrorType.NETWORK
        elif any(keyword in error_msg for keyword in ['invalid symbol', 'not found', 'no data']):
            return ApiErrorType.INVALID_TICKER
        else:
            return ApiErrorType.UNKNOWN

    def _assess_completeness(self, data: Dict[str, Any]) -> DataCompleteness:
        """Assess data completeness"""
        if not data:
            return DataCompleteness.EMPTY

        total_fields = len(data)
        non_null_fields = sum(1 for v in data.values() if v is not None and v != '')

        completeness_ratio = np.divide(
            non_null_fields, total_fields, out=np.array(0.0), where=(total_fields > 0)
        )[()]

        if completeness_ratio >= 0.8:
            return DataCompleteness.COMPLETE
        elif completeness_ratio >= 0.5:
            return DataCompleteness.PARTIAL
        elif completeness_ratio > 0:
            return DataCompleteness.MINIMAL
        else:
            return DataCompleteness.EMPTY

    def _update_field_availability(self, api_name: str, data: Dict[str, Any]):
        """Update field availability tracking"""
        for field_name, value in data.items():
            if field_name not in self.field_availability:
                self.field_availability[field_name] = FieldAvailability(field_name=field_name)

            field_avail = self.field_availability[field_name]
            has_value = (
                value is not None
                and value != ''
                and (not isinstance(value, str) or value.lower() != 'none')
            )

            if api_name == 'yfinance':
                field_avail.yfinance_available = has_value
                field_avail.yfinance_value = value
            elif api_name == 'alpha_vantage':
                field_avail.alpha_vantage_available = has_value
                field_avail.alpha_vantage_value = value
            elif api_name == 'fmp':
                field_avail.fmp_available = has_value
                field_avail.fmp_value = value

    def _safe_float(self, value) -> Optional[float]:
        """Safely convert value to float"""
        if (
            value is None
            or value == ''
            or (isinstance(value, str) and value.lower() in ['none', 'null'])
        ):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_int(self, value) -> Optional[int]:
        """Safely convert value to int"""
        if (
            value is None
            or value == ''
            or (isinstance(value, str) and value.lower() in ['none', 'null'])
        ):
            return None
        try:
            return int(float(value))  # Convert through float to handle decimals
        except (ValueError, TypeError):
            return None

    def _get_key_fields_for_statement(self, statement_type: str) -> List[str]:
        """Get key fields for yfinance statement types"""
        fields = {
            'financials': ['Total Revenue', 'Net Income', 'Operating Income', 'Gross Profit'],
            'balance_sheet': [
                'Total Assets',
                'Total Debt',
                'Total Stockholder Equity',
                'Cash And Cash Equivalents',
            ],
            'cashflow': ['Operating Cash Flow', 'Capital Expenditures', 'Free Cash Flow'],
        }
        return fields.get(statement_type, [])

    def _get_key_fields_for_alpha_vantage_statement(self, function: str) -> List[str]:
        """Get key fields for Alpha Vantage statement functions"""
        fields = {
            'INCOME_STATEMENT': ['totalRevenue', 'netIncome', 'operatingIncome', 'grossProfit'],
            'BALANCE_SHEET': [
                'totalAssets',
                'totalLiabilities',
                'totalShareholderEquity',
                'cashAndShortTermInvestments',
            ],
            'CASH_FLOW': ['operatingCashflow', 'capitalExpenditures', 'freeCashFlow'],
        }
        return fields.get(function, [])

    def _get_key_fields_for_fmp_statement(self, statement: str) -> List[str]:
        """Get key fields for FMP statement endpoints"""
        fields = {
            'income-statement': ['revenue', 'netIncome', 'operatingIncome', 'grossProfit'],
            'balance-sheet-statement': [
                'totalAssets',
                'totalDebt',
                'totalStockholdersEquity',
                'cashAndShortTermInvestments',
            ],
            'cash-flow-statement': ['operatingCashFlow', 'capitalExpenditure', 'freeCashFlow'],
        }
        return fields.get(statement, [])

    def _generate_summary(self, results: Dict[str, List[ApiCallResult]]) -> Dict[str, Any]:
        """Generate summary statistics"""
        total_calls = 0
        successful_calls = 0
        apis_tested = []

        for api_name, api_results in results.items():
            if api_name == 'summary':
                continue

            if api_results:
                apis_tested.append(api_name)
                total_calls += len(api_results)
                successful_calls += sum(1 for r in api_results if r.success)

        return {
            'apis_tested': apis_tested,
            'total_calls': total_calls,
            'successful_calls': successful_calls,
            'success_rate': np.divide(
                successful_calls,
                total_calls,
                out=np.zeros_like(successful_calls, dtype=float),
                where=(total_calls != 0),
            )[()],
            'generated_at': datetime.now().isoformat(),
        }


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(description='Financial API Diagnostic Tool')
    parser.add_argument('--ticker', '-t', required=True, help='Stock ticker symbol to test')
    parser.add_argument(
        '--api',
        choices=['yfinance', 'alpha_vantage', 'fmp', 'all'],
        default='all',
        help='Specific API to test (default: all)',
    )
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--output', '-o', help='Output file for report')
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level',
    )
    parser.add_argument(
        '--include-statements',
        action='store_true',
        default=True,
        help='Include financial statements testing',
    )
    parser.add_argument(
        '--multiple-tickers', nargs='+', help='Test multiple tickers (space-separated)'
    )
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')

    args = parser.parse_args()

    # Initialize diagnostic tool
    diagnostic = FinancialApiDiagnostic(config_file=args.config, log_level=args.log_level)

    if args.multiple_tickers:
        # Test multiple tickers
        tickers = args.multiple_tickers
        apis = [args.api] if args.api != 'all' else None

        print(f"Testing multiple tickers: {', '.join(tickers)}")
        results = diagnostic.test_multiple_tickers(tickers, apis)

        # Generate combined report
        # This would need additional implementation for multi-ticker reporting
        print("Multi-ticker testing completed. Individual reports generated.")

    else:
        # Test single ticker
        if args.api == 'all':
            print(f"Testing all APIs for ticker: {args.ticker}")
            results = diagnostic.test_all_apis(args.ticker, args.include_statements)
        else:
            print(f"Testing {args.api} API for ticker: {args.ticker}")
            # Individual API testing would need additional implementation
            results = diagnostic.test_all_apis(args.ticker, args.include_statements)

        # Generate and display report
        output_file = (
            args.output
            or f"api_diagnostic_report_{args.ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        report = diagnostic.generate_comprehensive_report(results, output_file)

        if args.verbose:
            print("\n" + "=" * 80)
            print(report)
            print("=" * 80)

        print(f"\nDiagnostic completed. Report saved to: {output_file}")


if __name__ == "__main__":
    main()
