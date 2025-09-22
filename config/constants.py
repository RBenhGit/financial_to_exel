"""
Financial Analysis Application Constants
========================================

This module centralizes all hardcoded values, magic numbers, and configuration
constants used throughout the financial analysis application. This improves
maintainability and consistency across the codebase.

All constants follow naming convention: UPPERCASE_WITH_UNDERSCORES
"""

# ============================================================================
# API CONFIGURATION CONSTANTS
# ============================================================================

# Timeout Settings
DEFAULT_NETWORK_TIMEOUT = 30.0  # seconds
DEFAULT_API_TIMEOUT = 15.0  # seconds
API_TIMEOUT_SECONDS = 15.0  # seconds (alias for compatibility)
YFINANCE_HISTORY_TIMEOUT = 15.0  # seconds

# Rate Limiting
DEFAULT_RATE_LIMIT_DELAY = 1.0  # seconds between requests
API_RETRY_ATTEMPTS = 3
API_BACKOFF_FACTOR = 2.0

# API Base URLs
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"
POLYGON_BASE_URL = "https://api.polygon.io"

# ============================================================================
# DATA PROCESSING CONSTANTS
# ============================================================================

# Data Quality Thresholds
MIN_DATA_COMPLETENESS_RATIO = 0.7  # 70%
MAX_OUTLIER_STANDARD_DEVIATIONS = 3.0

# Numeric Precision
DEFAULT_DECIMAL_PLACES = 2
FINANCIAL_PRECISION = 4
PERCENTAGE_PRECISION = 1
DEFAULT_FINANCIAL_SCALE_FACTOR = 1000000  # Default scale for financial values (millions)

# Data Validation
MIN_VALID_YEAR = 1900
MAX_VALID_YEAR = 2100
MIN_VALID_PRICE = 0.01
MAX_VALID_MARKET_CAP = 1e15  # $1 quadrillion

# ============================================================================
# FILE SYSTEM CONSTANTS
# ============================================================================

# Default Directories
DEFAULT_EXPORT_DIR = "exports"
DEFAULT_DATA_DIR = "data"
DEFAULT_CACHE_DIR = "data/cache"
DEFAULT_LOG_DIR = "logs"

# File Extensions
EXCEL_EXTENSIONS = [".xlsx", ".xls"]
CSV_EXTENSION = ".csv"
JSON_EXTENSION = ".json"
LOG_EXTENSION = ".log"

# File Size Limits (bytes)
MAX_EXCEL_FILE_SIZE = 100 * 1024 * 1024  # 100MB
MAX_CSV_FILE_SIZE = 50 * 1024 * 1024   # 50MB

# ============================================================================
# FINANCIAL CALCULATION CONSTANTS
# ============================================================================

# DCF Default Assumptions
DEFAULT_DISCOUNT_RATE = 0.10  # 10%
DEFAULT_TERMINAL_GROWTH_RATE = 0.025  # 2.5%
DEFAULT_PROJECTION_YEARS = 10

# Growth Rate Bounds
MIN_DISCOUNT_RATE = 0.01  # 1%
MAX_DISCOUNT_RATE = 0.50  # 50%
MIN_GROWTH_RATE = -0.10   # -10%
MAX_GROWTH_RATE = 0.30    # 30%

# Risk-Free Rate Proxies
TREASURY_10Y_PROXY = 0.04  # 4%
RISK_FREE_RATE_FLOOR = 0.0  # 0%

# Market Risk Premium
MARKET_RISK_PREMIUM = 0.06  # 6%
BETA_FLOOR = 0.1
BETA_CEILING = 3.0

# ============================================================================
# HTTP STATUS CODES
# ============================================================================

HTTP_OK = 200
HTTP_NOT_FOUND = 404
HTTP_RATE_LIMITED = 429
HTTP_SERVER_ERROR = 500

# ============================================================================
# ERROR HANDLING CONSTANTS
# ============================================================================

# Error Classification
ERROR_TIMEOUT = "timeout_error"
ERROR_RATE_LIMIT = "rate_limit_error"
ERROR_DATA_MISSING = "data_missing_error"
ERROR_NETWORK = "network_error"
ERROR_VALIDATION = "validation_error"

# Retry Logic
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
MAX_RETRY_DELAY = 60.0     # seconds

# ============================================================================
# UI AND DISPLAY CONSTANTS
# ============================================================================

# Default Display Values
UNKNOWN_COMPANY_NAME = "Unknown Company"
UNKNOWN_TICKER = "N/A"
UNKNOWN_FCF_TYPE = "Not Specified"
DEFAULT_COMPANY_DISPLAY_NAME = "Company"

# Test/Demo Values
TEST_COMPANY_NAME = "Sample Company"
TEST_COMPANY_TICKER = "SMPL"

# Number Formatting
CURRENCY_SYMBOL = "$"
PERCENTAGE_SYMBOL = "%"
THOUSAND_SEPARATOR = ","
DECIMAL_SEPARATOR = "."

# Chart Colors (Professional Theme)
PRIMARY_COLOR = "#1f77b4"
SECONDARY_COLOR = "#ff7f0e"
SUCCESS_COLOR = "#2ca02c"
WARNING_COLOR = "#ff7f0e"
ERROR_COLOR = "#d62728"

# ============================================================================
# LOGGING CONSTANTS
# ============================================================================

# Log Levels
LOG_LEVEL_DEBUG = "DEBUG"
LOG_LEVEL_INFO = "INFO"
LOG_LEVEL_WARNING = "WARNING"
LOG_LEVEL_ERROR = "ERROR"
LOG_LEVEL_CRITICAL = "CRITICAL"

# Log Format Templates
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s"
SIMPLE_LOG_FORMAT = "%(levelname)s: %(message)s"

# Log File Settings
MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 5
LOG_ROTATION_WHEN = "midnight"

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

# Cache TTL (Time To Live) in seconds
DEFAULT_CACHE_TTL = 24 * 3600  # 24 hours
PRICE_CACHE_TTL = 15 * 60      # 15 minutes
FINANCIAL_DATA_CACHE_TTL = 6 * 3600  # 6 hours
METADATA_CACHE_TTL = 7 * 24 * 3600   # 7 days
CACHE_EXPIRY_MINUTES = 60      # 60 minutes for general cache expiry

# Cache Size Limits
MAX_CACHE_ENTRIES = 1000
MAX_CACHE_SIZE_MB = 100

# ============================================================================
# DATE AND TIME CONSTANTS
# ============================================================================

# Date Formats
DATE_FORMAT_ISO = "%Y-%m-%d"
DATE_FORMAT_US = "%m/%d/%Y"
DATE_FORMAT_DISPLAY = "%B %d, %Y"
TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

# Business Days and Periods
TRADING_DAYS_PER_YEAR = 252
BUSINESS_DAYS_PER_WEEK = 5
MONTHS_PER_YEAR = 12
QUARTERS_PER_YEAR = 4

# ============================================================================
# EXCEL PROCESSING CONSTANTS
# ============================================================================

# Excel Structure
DEFAULT_HEADER_ROW = 1
DEFAULT_DATA_START_ROW = 2
DEFAULT_DATA_START_COLUMN = 4
LTM_COLUMN_INDEX = 15
MAX_SCAN_ROWS = 59
MAX_SCAN_COLUMNS = 16

# Standard Financial Statement Names
FINANCIAL_STATEMENT_NAMES = [
    "Income Statement",
    "Balance Sheet",
    "Cash Flow Statement",
    "Statement of Income",
    "Statement of Financial Position",
    "Statement of Cash Flows",
    "Profit and Loss Statement",
    "P&L Statement"
]

# Excel Validation
MIN_EXCEL_COLUMNS = 5
MIN_EXCEL_ROWS = 10
MAX_EXCEL_COLUMNS = 100
MAX_EXCEL_ROWS = 10000

# Company Name Search Positions (row, column)
COMPANY_NAME_POSITIONS = [(2, 3), (1, 3), (3, 3), (2, 2)]

# ============================================================================
# FINANCIAL STATEMENT FIELD NAMES
# ============================================================================

# Alpha Vantage Field Names
AV_CURRENT_PRICE = "05. price"
AV_CHANGE_PERCENT = "10. change percent"  
AV_VOLUME = "06. volume"
AV_TRADING_DAY = "07. latest trading day"

# Standard Field Names for Normalization
NORMALIZED_FIELDS = {
    "current_price": "current_price",
    "market_cap": "market_cap", 
    "shares_outstanding": "shares_outstanding",
    "revenue": "total_revenue",
    "net_income": "net_income",
    "operating_cash_flow": "operating_cash_flow",
    "free_cash_flow": "free_cash_flow"
}

# ============================================================================
# ENVIRONMENT CONSTANTS
# ============================================================================

# Environment Names
ENV_DEVELOPMENT = "development"
ENV_TESTING = "testing" 
ENV_PRODUCTION = "production"

# Environment Variable Names
ENV_VAR_ENVIRONMENT = "FINANCIAL_ANALYSIS_ENV"
ENV_VAR_LOG_LEVEL = "FINANCIAL_ANALYSIS_LOG_LEVEL"
ENV_VAR_CACHE_DIR = "FINANCIAL_ANALYSIS_CACHE_DIR"

# API Key Environment Variables
ENV_ALPHA_VANTAGE_KEY = "ALPHA_VANTAGE_API_KEY"
ENV_FMP_KEY = "FMP_API_KEY"
ENV_POLYGON_KEY = "POLYGON_API_KEY"
ENV_YFINANCE_KEY = "YFINANCE_API_KEY"  # For future use

# ============================================================================
# STATISTICAL CONSTANTS
# ============================================================================

# Confidence Intervals
CONFIDENCE_95_PERCENT = 0.95
CONFIDENCE_99_PERCENT = 0.99
Z_SCORE_95_PERCENT = 1.96
Z_SCORE_99_PERCENT = 2.58

# Statistical Thresholds
MIN_SAMPLE_SIZE = 5
CORRELATION_THRESHOLD = 0.5
R_SQUARED_THRESHOLD = 0.7

# ============================================================================
# BUSINESS LOGIC CONSTANTS  
# ============================================================================

# Valuation Model Types
DCF_MODEL_TYPE = "DCF"
DDM_MODEL_TYPE = "DDM"
PB_MODEL_TYPE = "P/B"

# FCF Types
FCFE_TYPE = "FCFE"  # Free Cash Flow to Equity
FCFF_TYPE = "FCFF"  # Free Cash Flow to Firm
LFCF_TYPE = "LFCF"  # Levered Free Cash Flow

# Terminal Value Methods
GORDON_GROWTH_METHOD = "gordon_growth"
EXIT_MULTIPLE_METHOD = "exit_multiple"
PERPETUAL_GROWTH_METHOD = "perpetual_growth"

# Market Sectors (for sector-specific analysis)
TECH_SECTOR = "Technology"
FINANCE_SECTOR = "Financial Services"
HEALTHCARE_SECTOR = "Healthcare"
ENERGY_SECTOR = "Energy"
CONSUMER_SECTOR = "Consumer"
INDUSTRIAL_SECTOR = "Industrial"