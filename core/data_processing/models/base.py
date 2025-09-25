"""
Base Financial Statement Model
==============================

Base Pydantic model providing common fields and functionality for all
financial statement types.

This base class includes:
- Common identification fields (ticker, period, currency)
- Reporting metadata (period type, data source)
- Standard validation patterns
- Factory methods for model instantiation
- Utility methods for data access and transformation
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Annotated


class ReportingPeriod(str, Enum):
    """Standard reporting periods for financial statements"""
    ANNUAL = "annual"
    QUARTERLY = "quarterly"
    LTM = "ltm"  # Last Twelve Months
    TTM = "ttm"  # Trailing Twelve Months


class Currency(str, Enum):
    """Supported currencies for financial data"""
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    ILS = "ILS"  # Israeli Shekel
    CAD = "CAD"
    AUD = "AUD"


class DataSource(str, Enum):
    """Data sources for financial information"""
    EXCEL = "excel"
    YFINANCE = "yfinance"
    FMP = "fmp"  # Financial Modeling Prep
    ALPHA_VANTAGE = "alpha_vantage"
    POLYGON = "polygon"
    MANUAL = "manual"


class BaseFinancialStatementModel(BaseModel):
    """
    Base model for all financial statement types with common fields
    and validation patterns.
    """

    # Core identification fields
    company_ticker: Annotated[str, Field(min_length=1, max_length=10)] = Field(
        ...,
        description="Stock ticker symbol (e.g., AAPL, MSFT)",
        example="AAPL"
    )

    company_name: Optional[str] = Field(
        None,
        description="Full company name",
        example="Apple Inc."
    )

    period_end_date: Union[str, datetime] = Field(
        ...,
        description="End date of the reporting period (YYYY-MM-DD or datetime)",
        example="2023-12-31"
    )

    # Reporting metadata
    reporting_period: ReportingPeriod = Field(
        ReportingPeriod.ANNUAL,
        description="Type of reporting period"
    )

    currency: Currency = Field(
        Currency.USD,
        description="Currency for financial values"
    )

    data_source: Optional[DataSource] = Field(
        None,
        description="Source of the financial data"
    )

    # Data processing metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when model was created"
    )

    updated_at: Optional[datetime] = Field(
        None,
        description="Timestamp when model was last updated"
    )

    fiscal_year: Optional[int] = Field(
        None,
        ge=1900,
        le=2100,
        description="Fiscal year for the reporting period"
    )

    # Data quality indicators
    data_quality_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Data quality score (0-1, where 1 is highest quality)"
    )

    missing_fields: Optional[list] = Field(
        default_factory=list,
        description="List of expected fields that are missing or null"
    )

    # Additional metadata
    notes: Optional[str] = Field(
        None,
        description="Additional notes or comments about the data"
    )

    class Config:
        """Pydantic model configuration"""
        use_enum_values = True
        validate_assignment = True
        arbitrary_types_allowed = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }
        schema_extra = {
            "example": {
                "company_ticker": "AAPL",
                "company_name": "Apple Inc.",
                "period_end_date": "2023-09-30",
                "reporting_period": "annual",
                "currency": "USD",
                "data_source": "yfinance",
                "fiscal_year": 2023,
                "data_quality_score": 0.95
            }
        }

    @field_validator('period_end_date', mode='before')
    @classmethod
    def parse_period_end_date(cls, v):
        """Parse period end date from various formats"""
        if isinstance(v, str):
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d %H:%M:%S']:
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Invalid date format: {v}")
        elif isinstance(v, datetime):
            return v.date()
        return v

    @field_validator('company_ticker', mode='before')
    @classmethod
    def normalize_ticker(cls, v):
        """Normalize ticker symbol to uppercase"""
        if isinstance(v, str):
            return v.upper().strip()
        return v

    @model_validator(mode='after')
    def validate_data_consistency(self):
        """Validate cross-field consistency"""
        # Set fiscal year from period_end_date if not provided
        if self.fiscal_year is None and self.period_end_date:
            if hasattr(self.period_end_date, 'year'):
                self.fiscal_year = self.period_end_date.year
            elif isinstance(self.period_end_date, str):
                try:
                    self.fiscal_year = datetime.strptime(self.period_end_date.split()[0], '%Y-%m-%d').year
                except ValueError:
                    pass

        # Ensure updated_at is after created_at if both are set
        if self.created_at and self.updated_at and self.updated_at < self.created_at:
            raise ValueError("updated_at cannot be before created_at")

        return self

    def get_period_identifier(self) -> str:
        """Get a unique identifier for this reporting period"""
        return f"{self.company_ticker}_{self.fiscal_year}_{self.reporting_period.value}"

    def to_dict(self, exclude_none: bool = True) -> Dict[str, Any]:
        """Convert model to dictionary with optional None exclusion"""
        return self.dict(exclude_none=exclude_none)

    def update_timestamp(self):
        """Update the updated_at timestamp to current time"""
        self.updated_at = datetime.utcnow()

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any], **kwargs):
        """Factory method to create model from dictionary data"""
        # Merge kwargs with data, with kwargs taking precedence
        merged_data = {**data, **kwargs}
        return cls(**merged_data)

    @classmethod
    def get_currency_multiplier(cls, currency: Union[str, Currency]) -> float:
        """Get currency multiplier for unit conversion"""
        # This could be extended to fetch real exchange rates
        # For now, return 1.0 as a placeholder
        return 1.0

    def validate_field_completeness(self, required_fields: list) -> list:
        """
        Validate that required fields are present and not None

        Args:
            required_fields: List of field names that are required

        Returns:
            List of missing field names
        """
        missing = []
        for field_name in required_fields:
            value = getattr(self, field_name, None)
            if value is None:
                missing.append(field_name)

        self.missing_fields = missing
        return missing

    def calculate_data_quality_score(self) -> float:
        """
        Calculate a data quality score based on field completeness
        and data consistency. Should be overridden in subclasses.

        Returns:
            Float between 0-1 representing data quality
        """
        # Basic implementation - override in subclasses
        total_fields = len(self.__fields__)
        missing_count = len(self.missing_fields or [])

        if total_fields == 0:
            return 1.0

        completeness_score = 1.0 - (missing_count / total_fields)
        self.data_quality_score = max(0.0, completeness_score)
        return self.data_quality_score