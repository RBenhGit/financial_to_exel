"""
Statement Field Mapper
======================

Configurable system for mapping extracted financial statement fields to standardized
calculation inputs. Supports multiple mapping strategies including exact match,
fuzzy matching, and regex patterns.

This module integrates with the existing field extraction system to provide intelligent
field name resolution and standardization across different Excel formats and reporting
standards (GAAP, IFRS).

Key Features:
- Configuration-driven field mappings from YAML
- Fuzzy string matching for field name variations
- Company-specific and industry-specific mapping rules
- Support for GAAP and IFRS reporting standards
- Comprehensive validation and confidence scoring
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml

from ..exceptions import (
    DataSourceException,
    DataValidationException,
    ErrorCategory,
    ErrorSeverity,
    RecoveryStrategy,
)

logger = logging.getLogger(__name__)


class MappingStrategy(Enum):
    """Available field mapping strategies"""

    EXACT_MATCH = "exact_match"  # Direct field name match
    FUZZY_MATCH = "fuzzy_match"  # Fuzzy string matching
    REGEX_MATCH = "regex_match"  # Pattern-based matching
    ALIAS_MATCH = "alias_match"  # Lookup in alias tables


class ConfigurationError(DataSourceException):
    """Exception raised when configuration loading or validation fails"""

    def __init__(self, message: str, config_path: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recovery_strategy=RecoveryStrategy.USE_FALLBACK,
            **kwargs,
        )
        self.config_path = config_path


@dataclass
class MappingResult:
    """Result of a field mapping operation"""

    input_field_name: str
    mapped_field_name: Optional[str]
    confidence_score: float  # 0.0 to 1.0
    strategy_used: MappingStrategy
    is_successful: bool
    alternatives: List[Tuple[str, float]] = field(
        default_factory=list
    )  # [(field_name, score)]
    notes: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate mapping result"""
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError(
                f"Confidence score must be between 0.0 and 1.0, got {self.confidence_score}"
            )


class StatementFieldMapper:
    """
    Configurable field mapper for standardizing financial statement field names.

    This class provides intelligent field name resolution using multiple strategies:
    - Exact matching for known field names
    - Fuzzy matching for variations and typos
    - Regex patterns for complex field name structures
    - Company-specific and industry-specific rules
    - Reporting standard-specific mappings (GAAP, IFRS)

    The mapper loads configuration from field_mapping_config.yaml which defines
    the standard field names, aliases, and mapping rules.
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        fuzzy_threshold: float = 0.8,
        enable_fuzzy_matching: bool = True,
    ):
        """
        Initialize the StatementFieldMapper.

        Args:
            config_path: Path to field_mapping_config.yaml. If None, uses default location.
            fuzzy_threshold: Minimum similarity score for fuzzy matching (0.0 to 1.0)
            enable_fuzzy_matching: Whether to enable fuzzy matching fallback
        """
        self.fuzzy_threshold = fuzzy_threshold
        self.enable_fuzzy_matching = enable_fuzzy_matching

        # Configuration storage
        self.config: Dict[str, Any] = {}
        self.default_mappings: Dict[str, str] = {}
        self.company_specific_mappings: Dict[str, Dict[str, str]] = {}
        self.industry_mappings: Dict[str, Dict[str, str]] = {}
        self.reporting_standard_mappings: Dict[str, Dict[str, str]] = {}
        self.field_aliases: Dict[str, List[str]] = {}
        self.required_fields: Set[str] = set()
        self.regex_patterns: Dict[str, str] = {}
        self.field_transformations: Dict[str, Any] = {}
        self.validation_rules: Dict[str, Any] = {}
        self.mapping_quality: Dict[str, Any] = {}
        self.fuzzy_matching_config: Dict[str, Any] = {}

        # Performance tracking
        self._stats = {
            "total_mappings": 0,
            "exact_matches": 0,
            "fuzzy_matches": 0,
            "regex_matches": 0,
            "alias_matches": 0,
            "failed_mappings": 0,
        }

        # Load configuration
        self.config_path = self._resolve_config_path(config_path)
        self.load_configuration()

        logger.info(
            f"Initialized StatementFieldMapper with config from {self.config_path}"
        )

    def _resolve_config_path(self, config_path: Optional[str]) -> Path:
        """Resolve the configuration file path"""
        if config_path:
            return Path(config_path)

        # Default locations to check (in order of priority)
        project_root = Path(__file__).parent.parent.parent.parent
        default_locations = [
            project_root / "config" / "field_mapping_config.yaml",
            Path("config/field_mapping_config.yaml"),
            Path("config/field_mappings.yaml"),
            Path(__file__).parent / "field_mapping_config.yaml",
        ]

        for location in default_locations:
            if location.exists():
                return location

        # If no config found, will be created with defaults
        return project_root / "config" / "field_mapping_config.yaml"

    def load_configuration(self) -> None:
        """
        Load field mapping configuration from YAML file.

        The configuration file should have the following structure:
        ```yaml
        default_mappings:
          revenue: "Total Revenue"
          net_income: "Net Income"

        company_specific_mappings:
          AAPL:
            revenue: "Net Sales"
          MSFT:
            revenue: "Total Revenue"

        industry_mappings:
          technology:
            revenue: "Product and Service Revenue"

        reporting_standard_mappings:
          GAAP:
            revenue: "Revenue"
          IFRS:
            revenue: "Turnover"

        field_aliases:
          revenue:
            - "Sales"
            - "Total Sales"
            - "Net Sales"

        required_fields:
          - revenue
          - net_income
          - operating_cash_flow

        regex_patterns:
          revenue: "^(Total\\s+)?(Net\\s+)?Revenue$"
        ```

        Raises:
            ConfigurationError: If configuration file is invalid or cannot be loaded
        """
        try:
            if not self.config_path.exists():
                logger.warning(
                    f"Configuration file not found at {self.config_path}. "
                    "Using default configuration."
                )
                self._create_default_configuration()
                return

            with open(self.config_path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f)

            # Validate configuration structure
            self._validate_configuration()

            # Extract configuration sections
            self.default_mappings = self.config.get("default_mappings", {})
            self.company_specific_mappings = self.config.get(
                "company_specific_mappings", {}
            )
            self.industry_mappings = self.config.get("industry_mappings", {})
            self.reporting_standard_mappings = self.config.get(
                "reporting_standard_mappings", {}
            )
            self.field_aliases = self.config.get("field_aliases", {})
            self.required_fields = set(self.config.get("required_fields", []))
            self.regex_patterns = self.config.get("regex_patterns", {})
            self.field_transformations = self.config.get("field_transformations", {})
            self.validation_rules = self.config.get("validation_rules", {})
            self.mapping_quality = self.config.get("mapping_quality", {})
            self.fuzzy_matching_config = self.config.get("fuzzy_matching", {})

            # Override fuzzy threshold if specified in config
            config_threshold = self.fuzzy_matching_config.get("default_threshold")
            if config_threshold and self.fuzzy_threshold == 0.8:  # Only if not explicitly set
                self.fuzzy_threshold = config_threshold

            logger.info(
                f"Loaded field mapping configuration: "
                f"{len(self.default_mappings)} default mappings, "
                f"{len(self.company_specific_mappings)} company-specific rules, "
                f"{len(self.field_aliases)} field aliases, "
                f"{len(self.required_fields)} required fields"
            )

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse YAML configuration: {str(e)}",
                config_path=str(self.config_path),
                original_exception=e,
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration: {str(e)}",
                config_path=str(self.config_path),
                original_exception=e,
            )

    def _validate_configuration(self) -> None:
        """Validate loaded configuration structure"""
        required_sections = ["default_mappings"]

        for section in required_sections:
            if section not in self.config:
                raise ConfigurationError(
                    f"Configuration missing required section: {section}",
                    config_path=str(self.config_path),
                )

        # Validate field_aliases structure
        if "field_aliases" in self.config:
            aliases = self.config["field_aliases"]
            if not isinstance(aliases, dict):
                raise ConfigurationError(
                    "field_aliases must be a dictionary",
                    config_path=str(self.config_path),
                )

            for field_name, alias_list in aliases.items():
                if not isinstance(alias_list, list):
                    raise ConfigurationError(
                        f"Aliases for '{field_name}' must be a list",
                        config_path=str(self.config_path),
                    )

    def _create_default_configuration(self) -> None:
        """Create default configuration when no config file exists"""
        self.default_mappings = {
            # Income Statement
            "revenue": "Total Revenue",
            "net_income": "Net Income",
            "operating_income": "Operating Income",
            "gross_profit": "Gross Profit",
            "ebit": "EBIT",
            "ebitda": "EBITDA",
            # Balance Sheet
            "total_assets": "Total Assets",
            "total_liabilities": "Total Liabilities",
            "shareholders_equity": "Shareholders' Equity",
            "cash_and_equivalents": "Cash and Cash Equivalents",
            # Cash Flow
            "operating_cash_flow": "Net Cash from Operating Activities",
            "capital_expenditures": "Capital Expenditures",
            "free_cash_flow": "Free Cash Flow",
        }

        self.field_aliases = {
            "revenue": ["Sales", "Total Sales", "Net Sales", "Revenues"],
            "net_income": ["Net Earnings", "Profit", "Net Profit", "Earnings"],
            "operating_cash_flow": ["Cash from Operations", "Operating Cash"],
            "capital_expenditures": ["CapEx", "PP&E Purchases"],
        }

        self.required_fields = {
            "revenue",
            "net_income",
            "total_assets",
            "operating_cash_flow",
        }

        logger.info("Created default field mapping configuration")

    def map_field(
        self,
        input_field_name: str,
        company_ticker: Optional[str] = None,
        industry: Optional[str] = None,
        reporting_standard: Optional[str] = None,
    ) -> MappingResult:
        """
        Map an input field name to a standardized field name.

        Applies mapping strategies in order of priority:
        1. Exact match in company-specific mappings
        2. Exact match in industry mappings
        3. Exact match in reporting standard mappings
        4. Exact match in default mappings
        5. Alias lookup
        6. Regex pattern matching
        7. Fuzzy matching (if enabled)

        Args:
            input_field_name: The field name to map
            company_ticker: Optional company ticker for company-specific rules
            industry: Optional industry for industry-specific rules
            reporting_standard: Optional reporting standard (GAAP, IFRS)

        Returns:
            MappingResult with mapped field name and metadata
        """
        self._stats["total_mappings"] += 1

        # Normalize input
        normalized_input = self._normalize_field_name(input_field_name)

        # Try mapping strategies in order
        result = None

        # 1. Company-specific mapping
        if company_ticker and company_ticker in self.company_specific_mappings:
            result = self._try_exact_match(
                normalized_input, self.company_specific_mappings[company_ticker]
            )
            if result and result.is_successful:
                result.notes.append(f"Matched using company-specific rule for {company_ticker}")
                self._stats["exact_matches"] += 1
                return result

        # 2. Industry-specific mapping
        if industry and industry in self.industry_mappings:
            result = self._try_exact_match(
                normalized_input, self.industry_mappings[industry]
            )
            if result and result.is_successful:
                result.notes.append(f"Matched using industry-specific rule for {industry}")
                self._stats["exact_matches"] += 1
                return result

        # 3. Reporting standard mapping
        if (
            reporting_standard
            and reporting_standard in self.reporting_standard_mappings
        ):
            result = self._try_exact_match(
                normalized_input, self.reporting_standard_mappings[reporting_standard]
            )
            if result and result.is_successful:
                result.notes.append(
                    f"Matched using {reporting_standard} reporting standard rule"
                )
                self._stats["exact_matches"] += 1
                return result

        # 4. Default mapping
        result = self._try_exact_match(normalized_input, self.default_mappings)
        if result and result.is_successful:
            result.notes.append("Matched using default mapping")
            self._stats["exact_matches"] += 1
            return result

        # 5. Alias lookup
        result = self._try_alias_match(normalized_input)
        if result and result.is_successful:
            result.notes.append("Matched using field alias")
            self._stats["alias_matches"] += 1
            return result

        # 6. Regex pattern matching
        result = self._try_regex_match(normalized_input)
        if result and result.is_successful:
            result.notes.append("Matched using regex pattern")
            self._stats["regex_matches"] += 1
            return result

        # 7. Fuzzy matching (fallback)
        if self.enable_fuzzy_matching:
            result = self._try_fuzzy_match(normalized_input)
            if result and result.is_successful:
                result.notes.append(
                    f"Matched using fuzzy matching (score: {result.confidence_score:.2f})"
                )
                self._stats["fuzzy_matches"] += 1
                return result

        # No match found
        self._stats["failed_mappings"] += 1
        return MappingResult(
            input_field_name=input_field_name,
            mapped_field_name=None,
            confidence_score=0.0,
            strategy_used=MappingStrategy.EXACT_MATCH,
            is_successful=False,
            notes=["No mapping found for field name"],
        )

    def _normalize_field_name(self, field_name: str) -> str:
        """Normalize field name for consistent matching"""
        if not field_name:
            return ""

        # Convert to lowercase
        normalized = field_name.lower().strip()

        # Remove extra whitespace
        normalized = re.sub(r"\s+", " ", normalized)

        return normalized

    def _try_exact_match(
        self, normalized_input: str, mapping_dict: Dict[str, str]
    ) -> Optional[MappingResult]:
        """Try exact match in provided mapping dictionary"""
        if not mapping_dict:
            return None

        # Check for direct match against both keys and display names
        for standard_field, display_name in mapping_dict.items():
            # Check if input matches the standard field key
            if normalized_input == standard_field.lower():
                return MappingResult(
                    input_field_name=normalized_input,
                    mapped_field_name=standard_field,
                    confidence_score=1.0,
                    strategy_used=MappingStrategy.EXACT_MATCH,
                    is_successful=True,
                )
            # Check if input matches the display name value
            if display_name and normalized_input == display_name.lower():
                return MappingResult(
                    input_field_name=normalized_input,
                    mapped_field_name=standard_field,
                    confidence_score=1.0,
                    strategy_used=MappingStrategy.EXACT_MATCH,
                    is_successful=True,
                )

        return None

    def _try_alias_match(self, normalized_input: str) -> Optional[MappingResult]:
        """Try matching against field aliases"""
        for standard_field, aliases in self.field_aliases.items():
            for alias in aliases:
                if normalized_input == alias.lower():
                    return MappingResult(
                        input_field_name=normalized_input,
                        mapped_field_name=standard_field,
                        confidence_score=0.95,  # Slightly lower than exact match
                        strategy_used=MappingStrategy.ALIAS_MATCH,
                        is_successful=True,
                    )

        return None

    def _try_regex_match(self, normalized_input: str) -> Optional[MappingResult]:
        """Try matching using regex patterns"""
        for standard_field, pattern in self.regex_patterns.items():
            try:
                if re.match(pattern, normalized_input, re.IGNORECASE):
                    return MappingResult(
                        input_field_name=normalized_input,
                        mapped_field_name=standard_field,
                        confidence_score=0.9,
                        strategy_used=MappingStrategy.REGEX_MATCH,
                        is_successful=True,
                    )
            except re.error as e:
                logger.warning(f"Invalid regex pattern for {standard_field}: {e}")
                continue

        return None

    def _try_fuzzy_match(self, normalized_input: str) -> Optional[MappingResult]:
        """Try fuzzy matching against all standard field names"""
        best_match = None
        best_score = 0.0
        alternatives = []

        # Check against all standard fields and their aliases
        all_candidates = []

        # Add default mappings
        for standard_field in self.default_mappings.keys():
            all_candidates.append((standard_field, standard_field.lower()))

        # Add aliases
        for standard_field, aliases in self.field_aliases.items():
            for alias in aliases:
                all_candidates.append((standard_field, alias.lower()))

        # Calculate similarity scores
        for standard_field, candidate_text in all_candidates:
            score = self._calculate_similarity(normalized_input, candidate_text)

            if score > best_score:
                best_score = score
                best_match = standard_field

            if score >= self.fuzzy_threshold:
                alternatives.append((standard_field, score))

        # Sort alternatives by score
        alternatives.sort(key=lambda x: x[1], reverse=True)

        if best_score >= self.fuzzy_threshold:
            return MappingResult(
                input_field_name=normalized_input,
                mapped_field_name=best_match,
                confidence_score=best_score,
                strategy_used=MappingStrategy.FUZZY_MATCH,
                is_successful=True,
                alternatives=alternatives[:5],  # Top 5 alternatives
            )

        return None

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings.

        Uses SequenceMatcher from difflib for fuzzy matching.

        Args:
            str1: First string
            str2: Second string

        Returns:
            Similarity score between 0.0 and 1.0
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def batch_map_fields(
        self,
        field_names: List[str],
        company_ticker: Optional[str] = None,
        industry: Optional[str] = None,
        reporting_standard: Optional[str] = None,
    ) -> Dict[str, MappingResult]:
        """
        Map multiple field names at once.

        Args:
            field_names: List of field names to map
            company_ticker: Optional company ticker
            industry: Optional industry
            reporting_standard: Optional reporting standard

        Returns:
            Dictionary mapping input field names to MappingResults
        """
        results = {}

        for field_name in field_names:
            result = self.map_field(
                field_name,
                company_ticker=company_ticker,
                industry=industry,
                reporting_standard=reporting_standard,
            )
            results[field_name] = result

        return results

    def validate_required_fields(
        self, mapped_fields: Dict[str, MappingResult]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields have been successfully mapped.

        Args:
            mapped_fields: Dictionary of field mapping results

        Returns:
            Tuple of (all_required_mapped, missing_required_fields)
        """
        successfully_mapped = {
            result.mapped_field_name
            for result in mapped_fields.values()
            if result.is_successful and result.mapped_field_name
        }

        missing_required = self.required_fields - successfully_mapped

        return len(missing_required) == 0, list(missing_required)

    def get_statistics(self) -> Dict[str, Any]:
        """Get mapping performance statistics"""
        total = max(self._stats["total_mappings"], 1)

        return {
            "total_mappings": self._stats["total_mappings"],
            "exact_matches": self._stats["exact_matches"],
            "fuzzy_matches": self._stats["fuzzy_matches"],
            "regex_matches": self._stats["regex_matches"],
            "alias_matches": self._stats["alias_matches"],
            "failed_mappings": self._stats["failed_mappings"],
            "success_rate": 1.0
            - (self._stats["failed_mappings"] / total),
            "exact_match_rate": self._stats["exact_matches"] / total,
            "fuzzy_match_rate": self._stats["fuzzy_matches"] / total,
        }

    def reset_statistics(self) -> None:
        """Reset mapping statistics"""
        for key in self._stats:
            self._stats[key] = 0

    def validate_mappings(
        self,
        mapped_fields: Dict[str, MappingResult],
        data_values: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate mapped fields for completeness, quality, and data integrity.

        This method performs comprehensive validation:
        1. Required field presence check
        2. Mapping confidence assessment
        3. Data type validation (if data provided)
        4. Duplicate mapping detection
        5. Field coverage analysis

        Args:
            mapped_fields: Dictionary of field mapping results from batch_map_fields
            data_values: Optional dictionary of actual data values for type validation

        Returns:
            Tuple of (is_valid, validation_report)
            - is_valid: True if all critical validations pass
            - validation_report: Detailed validation results and recommendations
        """
        validation_report = {
            "timestamp": datetime.now().isoformat(),
            "is_valid": True,
            "required_fields_status": {},
            "mapping_quality": {},
            "warnings": [],
            "errors": [],
            "recommendations": [],
            "statistics": {},
        }

        # 1. Check required fields
        successfully_mapped = {
            result.mapped_field_name
            for result in mapped_fields.values()
            if result.is_successful and result.mapped_field_name
        }

        missing_required = self.required_fields - successfully_mapped
        validation_report["required_fields_status"] = {
            "all_present": len(missing_required) == 0,
            "total_required": len(self.required_fields),
            "found": len(successfully_mapped & self.required_fields),
            "missing": list(missing_required),
        }

        if missing_required:
            validation_report["is_valid"] = False
            for field in missing_required:
                validation_report["errors"].append(
                    f"Critical field '{field}' is missing or unmapped"
                )
                logger.error(f"Required field '{field}' not found in mapped fields")

        # 2. Mapping confidence assessment
        low_confidence_mappings = []
        failed_mappings = []

        for input_field, result in mapped_fields.items():
            if not result.is_successful:
                failed_mappings.append(input_field)
            elif result.confidence_score < 0.7:
                low_confidence_mappings.append((input_field, result.confidence_score))

        validation_report["mapping_quality"] = {
            "total_fields": len(mapped_fields),
            "successful": len(
                [r for r in mapped_fields.values() if r.is_successful]
            ),
            "failed": len(failed_mappings),
            "low_confidence_count": len(low_confidence_mappings),
            "average_confidence": sum(
                r.confidence_score for r in mapped_fields.values()
            )
            / max(len(mapped_fields), 1),
        }

        if failed_mappings:
            validation_report["warnings"].append(
                f"{len(failed_mappings)} field(s) could not be mapped: {', '.join(failed_mappings[:5])}"
            )

        if low_confidence_mappings:
            validation_report["warnings"].append(
                f"{len(low_confidence_mappings)} field(s) have low confidence scores (<0.7)"
            )
            for field, score in low_confidence_mappings[:3]:
                validation_report["recommendations"].append(
                    f"Review mapping for '{field}' (confidence: {score:.2f}) - "
                    f"consider adding explicit mapping rule"
                )

        # 3. Data type validation (if data provided)
        if data_values:
            type_validation_results = self._validate_data_types(
                mapped_fields, data_values
            )
            validation_report["data_type_validation"] = type_validation_results

            if type_validation_results.get("errors"):
                validation_report["is_valid"] = False
                validation_report["errors"].extend(type_validation_results["errors"])

        # 4. Duplicate mapping detection
        mapped_to_counts = {}
        for result in mapped_fields.values():
            if result.is_successful and result.mapped_field_name:
                mapped_to_counts[result.mapped_field_name] = (
                    mapped_to_counts.get(result.mapped_field_name, 0) + 1
                )

        duplicates = {k: v for k, v in mapped_to_counts.items() if v > 1}
        if duplicates:
            validation_report["warnings"].append(
                f"Multiple input fields mapped to same standard field: {duplicates}"
            )
            validation_report["recommendations"].append(
                "Review duplicate mappings to ensure correct field identification"
            )

        # 5. Field coverage analysis
        coverage_stats = self._analyze_field_coverage(mapped_fields)
        validation_report["statistics"]["coverage"] = coverage_stats

        if coverage_stats["success_rate"] < 0.8:
            validation_report["recommendations"].append(
                f"Low mapping success rate ({coverage_stats['success_rate']:.1%}). "
                "Consider reviewing field mapping configuration."
            )

        # 6. Strategy distribution
        strategy_stats = self._analyze_mapping_strategies(mapped_fields)
        validation_report["statistics"]["strategies"] = strategy_stats

        if strategy_stats.get("fuzzy_match", 0) / max(len(mapped_fields), 1) > 0.5:
            validation_report["recommendations"].append(
                "High reliance on fuzzy matching detected. "
                "Consider adding more explicit mapping rules for better accuracy."
            )

        # Summary logging
        if validation_report["is_valid"]:
            logger.info(
                f"Mapping validation passed: {validation_report['mapping_quality']['successful']}/{len(mapped_fields)} fields mapped successfully"
            )
        else:
            logger.warning(
                f"Mapping validation failed: {len(validation_report['errors'])} errors, "
                f"{len(validation_report['warnings'])} warnings"
            )

        return validation_report["is_valid"], validation_report

    def _validate_data_types(
        self, mapped_fields: Dict[str, MappingResult], data_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data types of mapped fields.

        Args:
            mapped_fields: Mapping results
            data_values: Actual data values

        Returns:
            Dictionary with validation results
        """
        results = {"valid_count": 0, "invalid_count": 0, "errors": [], "warnings": []}

        for input_field, result in mapped_fields.items():
            if not result.is_successful or result.mapped_field_name not in data_values:
                continue

            value = data_values[result.mapped_field_name]

            # Check if numeric fields contain numeric values
            numeric_field_patterns = [
                "revenue",
                "income",
                "assets",
                "liabilities",
                "equity",
                "cash",
                "flow",
                "expenditure",
            ]

            is_numeric_field = any(
                pattern in result.mapped_field_name.lower()
                for pattern in numeric_field_patterns
            )

            if is_numeric_field:
                try:
                    float(value)
                    results["valid_count"] += 1
                except (ValueError, TypeError):
                    results["invalid_count"] += 1
                    results["errors"].append(
                        f"Field '{result.mapped_field_name}' expected numeric value, got {type(value).__name__}"
                    )

        return results

    def _analyze_field_coverage(self, mapped_fields: Dict[str, MappingResult]) -> Dict[str, Any]:
        """Analyze field mapping coverage statistics."""
        total = len(mapped_fields)
        successful = sum(1 for r in mapped_fields.values() if r.is_successful)

        return {
            "total_fields": total,
            "successfully_mapped": successful,
            "failed_mappings": total - successful,
            "success_rate": successful / max(total, 1),
        }

    def _analyze_mapping_strategies(
        self, mapped_fields: Dict[str, MappingResult]
    ) -> Dict[str, int]:
        """Analyze which mapping strategies were used."""
        strategy_counts = {}

        for result in mapped_fields.values():
            if result.is_successful:
                strategy_name = result.strategy_used.value
                strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1

        return strategy_counts

    def get_mapping_quality_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive mapping quality metrics.

        Returns:
            Dictionary with detailed quality metrics including:
            - Overall statistics
            - Strategy performance
            - Confidence distribution
            - Recommendations for improvement
        """
        stats = self.get_statistics()

        metrics = {
            "statistics": stats,
            "configuration": {
                "fuzzy_threshold": self.fuzzy_threshold,
                "fuzzy_matching_enabled": self.enable_fuzzy_matching,
                "required_fields_count": len(self.required_fields),
                "default_mappings_count": len(self.default_mappings),
                "company_specific_rules": len(self.company_specific_mappings),
                "field_aliases_count": len(self.field_aliases),
            },
            "health": {
                "overall_health": self._calculate_mapper_health(stats),
                "recommendations": self._generate_health_recommendations(stats),
            },
        }

        return metrics

    def _calculate_mapper_health(self, stats: Dict[str, Any]) -> str:
        """Calculate overall health status of the mapper."""
        success_rate = stats.get("success_rate", 0.0)

        if success_rate >= 0.95:
            return "Excellent"
        elif success_rate >= 0.85:
            return "Good"
        elif success_rate >= 0.70:
            return "Fair"
        else:
            return "Poor"

    def _generate_health_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on mapper statistics."""
        recommendations = []

        success_rate = stats.get("success_rate", 0.0)
        exact_match_rate = stats.get("exact_match_rate", 0.0)
        fuzzy_match_rate = stats.get("fuzzy_match_rate", 0.0)

        if success_rate < 0.8:
            recommendations.append(
                "Low success rate detected. Review field mapping configuration and add more explicit rules."
            )

        if exact_match_rate < 0.5 and fuzzy_match_rate > 0.3:
            recommendations.append(
                "Heavy reliance on fuzzy matching. Consider adding more exact mappings for improved accuracy."
            )

        if stats.get("failed_mappings", 0) > 10:
            recommendations.append(
                "High number of failed mappings. Review unmapped fields and update configuration."
            )

        return recommendations

    def get_fallback_value(
        self, field_name: str, data_source: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        Get fallback value for a missing critical field.

        Implements fallback strategies:
        1. Check alternate field names
        2. Use calculated/derived values
        3. Apply industry defaults
        4. Return None with warning

        Args:
            field_name: Standard field name that is missing
            data_source: Available data that might contain alternate values

        Returns:
            Fallback value or None if no fallback available
        """
        logger.info(f"Attempting to find fallback value for missing field: {field_name}")

        # 1. Check aliases for alternate field names
        if field_name in self.field_aliases:
            if data_source:
                for alias in self.field_aliases[field_name]:
                    if alias in data_source:
                        logger.info(
                            f"Found fallback for '{field_name}' using alias '{alias}'"
                        )
                        return data_source[alias]

        # 2. Apply field-specific fallback logic
        fallback_strategies = {
            "free_cash_flow": self._fallback_fcf,
            "ebitda": self._fallback_ebitda,
            "enterprise_value": self._fallback_ev,
        }

        if field_name in fallback_strategies and data_source:
            try:
                fallback_value = fallback_strategies[field_name](data_source)
                if fallback_value is not None:
                    logger.info(
                        f"Calculated fallback value for '{field_name}': {fallback_value}"
                    )
                    return fallback_value
            except Exception as e:
                logger.warning(
                    f"Failed to calculate fallback for '{field_name}': {e}"
                )

        logger.warning(f"No fallback value available for '{field_name}'")
        return None

    def _fallback_fcf(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate Free Cash Flow as fallback: OCF - CapEx"""
        ocf = data.get("operating_cash_flow")
        capex = data.get("capital_expenditures")

        if ocf is not None and capex is not None:
            return float(ocf) - abs(float(capex))
        return None

    def _fallback_ebitda(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate EBITDA as fallback: Net Income + Interest + Taxes + D&A"""
        net_income = data.get("net_income")
        interest = data.get("interest_expense", 0)
        taxes = data.get("income_tax_expense", 0)
        depreciation = data.get("depreciation_and_amortization", 0)

        if net_income is not None:
            return (
                float(net_income)
                + float(interest)
                + float(taxes)
                + float(depreciation)
            )
        return None

    def _fallback_ev(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate Enterprise Value as fallback: Market Cap + Debt - Cash"""
        market_cap = data.get("market_capitalization")
        total_debt = data.get("total_debt")
        cash = data.get("cash_and_equivalents")

        if market_cap is not None and total_debt is not None and cash is not None:
            return float(market_cap) + float(total_debt) - float(cash)
        return None

    # Integration Methods for FinancialCalculator and EnhancedDataManager

    def standardize_financial_data(
        self,
        raw_data: Dict[str, Any],
        company_ticker: Optional[str] = None,
        industry: Optional[str] = None,
        reporting_standard: Optional[str] = None,
        apply_fallbacks: bool = True,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Standardize raw financial data from Excel or API sources.

        This method is the primary integration point for FinancialCalculator and
        EnhancedDataManager. It takes raw field names and values, maps them to
        standardized field names, validates the mappings, and optionally applies
        fallback strategies for missing critical fields.

        Args:
            raw_data: Dictionary with raw field names as keys and values
            company_ticker: Optional company ticker for company-specific mappings
            industry: Optional industry for industry-specific rules
            reporting_standard: Optional reporting standard (GAAP, IFRS)
            apply_fallbacks: Whether to apply fallback calculations for missing fields

        Returns:
            Tuple of (standardized_data, mapping_metadata)
            - standardized_data: Dictionary with standardized field names and values
            - mapping_metadata: Validation report and mapping information
        """
        logger.info(
            f"Standardizing financial data: {len(raw_data)} raw fields for "
            f"company={company_ticker}, industry={industry}, standard={reporting_standard}"
        )

        # 1. Map all field names
        field_names = list(raw_data.keys())
        mapping_results = self.batch_map_fields(
            field_names,
            company_ticker=company_ticker,
            industry=industry,
            reporting_standard=reporting_standard,
        )

        # 2. Create standardized data dictionary
        standardized_data = {}
        for input_field, result in mapping_results.items():
            if result.is_successful and result.mapped_field_name:
                # Use the raw data value with the standardized field name
                standardized_data[result.mapped_field_name] = raw_data[input_field]

        # 3. Validate mappings
        is_valid, validation_report = self.validate_mappings(
            mapping_results, standardized_data
        )

        # 4. Apply fallback strategies if enabled and validation found issues
        if apply_fallbacks and not is_valid:
            missing_fields = validation_report["required_fields_status"].get(
                "missing", []
            )
            fallbacks_applied = []

            for field in missing_fields:
                fallback_value = self.get_fallback_value(field, standardized_data)
                if fallback_value is not None:
                    standardized_data[field] = fallback_value
                    fallbacks_applied.append(field)

            if fallbacks_applied:
                validation_report["fallbacks_applied"] = fallbacks_applied
                logger.info(
                    f"Applied fallback values for {len(fallbacks_applied)} fields: {fallbacks_applied}"
                )

                # Re-validate after applying fallbacks
                is_valid, validation_report = self.validate_mappings(
                    mapping_results, standardized_data
                )

        # 5. Prepare metadata
        metadata = {
            "validation_report": validation_report,
            "mapping_results": {
                k: {
                    "mapped_to": v.mapped_field_name,
                    "confidence": v.confidence_score,
                    "strategy": v.strategy_used.value,
                }
                for k, v in mapping_results.items()
                if v.is_successful
            },
            "timestamp": datetime.now().isoformat(),
            "company_ticker": company_ticker,
            "industry": industry,
            "reporting_standard": reporting_standard,
        }

        logger.info(
            f"Standardization complete: {len(standardized_data)} standardized fields, "
            f"validation_passed={is_valid}"
        )

        return standardized_data, metadata

    def get_integration_helper(self) -> "FieldMapperIntegrationHelper":
        """
        Get integration helper for easy use in FinancialCalculator and EnhancedDataManager.

        Returns:
            FieldMapperIntegrationHelper instance bound to this mapper
        """
        return FieldMapperIntegrationHelper(self)

    def __repr__(self) -> str:
        return (
            f"StatementFieldMapper("
            f"config={self.config_path}, "
            f"fuzzy_threshold={self.fuzzy_threshold})"
        )


class FieldMapperIntegrationHelper:
    """
    Helper class to simplify integration of StatementFieldMapper with other components.

    This class provides convenience methods that wrap the mapper functionality in
    patterns commonly needed by FinancialCalculator and EnhancedDataManager.
    """

    def __init__(self, mapper: StatementFieldMapper):
        """
        Initialize integration helper.

        Args:
            mapper: StatementFieldMapper instance to use
        """
        self.mapper = mapper
        self._cached_standardized_data = {}

    def process_excel_data(
        self,
        excel_data: Dict[str, Any],
        company_ticker: Optional[str] = None,
        cache_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process Excel data and return standardized fields.

        Args:
            excel_data: Raw Excel data dictionary
            company_ticker: Company ticker symbol
            cache_key: Optional cache key for result caching

        Returns:
            Standardized financial data dictionary
        """
        # Check cache
        if cache_key and cache_key in self._cached_standardized_data:
            logger.debug(f"Using cached standardized data for {cache_key}")
            return self._cached_standardized_data[cache_key]

        # Standardize data
        standardized_data, metadata = self.mapper.standardize_financial_data(
            excel_data, company_ticker=company_ticker, apply_fallbacks=True
        )

        # Cache if requested
        if cache_key:
            self._cached_standardized_data[cache_key] = standardized_data

        return standardized_data

    def get_required_field(
        self, field_name: str, data_source: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Get a required field value with automatic fallback.

        Args:
            field_name: Standardized field name
            data_source: Data source to check

        Returns:
            Field value or fallback value, None if not available
        """
        if field_name in data_source:
            return data_source[field_name]

        return self.mapper.get_fallback_value(field_name, data_source)

    def validate_data_completeness(
        self, data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields are present in data.

        Args:
            data: Standardized financial data

        Returns:
            Tuple of (is_complete, missing_fields)
        """
        # Create mapping results from existing data
        mapping_results = {}
        for field in self.mapper.required_fields:
            if field in data:
                mapping_results[field] = MappingResult(
                    input_field_name=field,
                    mapped_field_name=field,
                    confidence_score=1.0,
                    strategy_used=MappingStrategy.EXACT_MATCH,
                    is_successful=True,
                )

        is_complete, missing = self.mapper.validate_required_fields(mapping_results)
        return is_complete, missing

    def get_mapper_statistics(self) -> Dict[str, Any]:
        """
        Get current mapper statistics.

        Returns:
            Statistics dictionary
        """
        return self.mapper.get_statistics()

    def clear_cache(self) -> None:
        """Clear cached standardized data."""
        self._cached_standardized_data.clear()
        logger.debug("Cleared field mapper integration cache")
