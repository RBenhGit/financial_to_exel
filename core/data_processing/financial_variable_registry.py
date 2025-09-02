"""
Financial Variable Registry
==========================

Core variable definition schema and metadata management system for standardized
financial data processing across all components of the investment analysis platform.

This module implements a singleton registry pattern to maintain a centralized catalog
of all financial variables with their metadata, validation rules, data types, and
source-specific aliases. It ensures data consistency and provides a foundation for
variable-driven data processing workflows.

Key Features
------------
- **Centralized Variable Catalog**: Single source of truth for all financial variables
- **Thread-Safe Operations**: Concurrent access support with proper locking
- **Variable Categories**: Organized classification (Income Statement, Balance Sheet, etc.)
- **Source Aliases**: Multi-source field name mapping support  
- **Data Validation**: Built-in validation rules and type checking
- **Serialization Support**: JSON/YAML export for configuration management

Usage Example
-------------
>>> from financial_variable_registry import FinancialVariableRegistry, VariableDefinition
>>> 
>>> # Get the singleton registry instance
>>> registry = FinancialVariableRegistry()
>>> 
>>> # Register a new variable
>>> revenue_def = VariableDefinition(
...     name="revenue", 
...     category=VariableCategory.INCOME_STATEMENT,
...     data_type="float",
...     units="millions_usd",
...     description="Total company revenue",
...     aliases={"yfinance": "totalRevenue", "excel": "Revenue"}
... )
>>> registry.register_variable(revenue_def)
>>> 
>>> # Retrieve variable definition
>>> var_def = registry.get_variable_definition("revenue")
>>> print(var_def.description)  # "Total company revenue"
"""

import json
import logging
import threading
import yaml
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

# Configure logging
logger = logging.getLogger(__name__)


class VariableCategory(Enum):
    """Financial variable categories for organizational purposes"""
    INCOME_STATEMENT = "income_statement"
    BALANCE_SHEET = "balance_sheet" 
    CASH_FLOW = "cash_flow"
    RATIOS = "ratios"
    MARKET_DATA = "market_data"
    CALCULATED = "calculated"
    DERIVED = "derived"        # For variables calculated from other variables
    METADATA = "metadata"      # For non-numeric metadata fields


class DataType(Enum):
    """Supported data types for financial variables"""
    FLOAT = "float"
    INTEGER = "integer"
    PERCENTAGE = "percentage"  # Float representing percentage (0.05 = 5%)
    STRING = "string"
    DATE = "date"
    BOOLEAN = "boolean"
    CURRENCY = "currency"      # Float with currency metadata
    SHARES = "shares"          # Integer/float for share counts


class Units(Enum):
    """Standard units for financial variables"""
    # Currency units (absolute values)
    DOLLARS = "dollars"
    MILLIONS_USD = "millions_usd"
    BILLIONS_USD = "billions_usd"
    THOUSANDS_USD = "thousands_usd"
    
    # Percentage units
    PERCENTAGE = "percentage"
    BASIS_POINTS = "basis_points"  # 100 basis points = 1%
    
    # Count units
    SHARES = "shares"
    SHARES_MILLIONS = "shares_millions"
    
    # Ratio units (dimensionless)
    RATIO = "ratio"
    MULTIPLE = "multiple"
    
    # Time units
    YEARS = "years"
    DAYS = "days"
    
    # Other
    NONE = "none"
    TEXT = "text"


@dataclass
class ValidationRule:
    """Validation rule for variable values"""
    rule_type: str              # "range", "positive", "not_null", "regex", etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    warning_only: bool = False  # True for warnings, False for errors
    
    def validate(self, value: Any) -> tuple[bool, str]:
        """
        Validate a value against this rule
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if value is None and self.rule_type != "not_null":
            return True, ""  # Allow None values unless explicitly checking for not_null
            
        try:
            if self.rule_type == "not_null":
                is_valid = value is not None
                message = self.error_message or "Value cannot be null"
                
            elif self.rule_type == "positive":
                is_valid = value > 0 if value is not None else True
                message = self.error_message or "Value must be positive"
                
            elif self.rule_type == "non_negative":
                is_valid = value >= 0 if value is not None else True
                message = self.error_message or "Value must be non-negative"
                
            elif self.rule_type == "range":
                min_val = self.parameters.get("min", float('-inf'))
                max_val = self.parameters.get("max", float('inf'))
                is_valid = min_val <= value <= max_val if value is not None else True
                message = self.error_message or f"Value must be between {min_val} and {max_val}"
                
            elif self.rule_type == "percentage_range":
                # Assumes percentages are stored as decimals (0.05 = 5%)
                min_pct = self.parameters.get("min", 0.0)
                max_pct = self.parameters.get("max", 1.0)
                is_valid = min_pct <= value <= max_pct if value is not None else True
                message = self.error_message or f"Percentage must be between {min_pct*100}% and {max_pct*100}%"
                
            else:
                # Unknown rule type - skip validation
                return True, ""
                
            return is_valid, message if not is_valid else ""
            
        except (TypeError, ValueError) as e:
            return False, f"Validation error: {str(e)}"


@dataclass
class VariableDefinition:
    """Complete definition of a financial variable with metadata and validation"""
    
    # Core identification
    name: str                                    # Standard variable name (snake_case)
    category: VariableCategory
    data_type: DataType
    units: Units = Units.NONE
    
    # Documentation
    description: str = ""
    long_description: str = ""                   # Detailed explanation
    calculation_method: str = ""                 # How the variable is calculated
    
    # Source mappings
    aliases: Dict[str, str] = field(default_factory=dict)  # source -> field_name
    
    # Validation and constraints
    validation_rules: List[ValidationRule] = field(default_factory=list)
    required: bool = False                       # Whether variable is required
    default_value: Optional[Any] = None
    
    # Metadata
    tags: Set[str] = field(default_factory=set) # For filtering/grouping
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    version: str = "1.0.0"
    
    # Relationships
    depends_on: List[str] = field(default_factory=list)  # Variables this depends on
    derived_from: List[str] = field(default_factory=list) # Variables this is derived from
    
    def __post_init__(self):
        """Validate and normalize the variable definition"""
        if not self.name:
            raise ValueError("Variable name is required")
        
        # Normalize name to snake_case
        self.name = self.name.lower().replace(' ', '_').replace('-', '_')
        
        # Ensure aliases is a dict
        if not isinstance(self.aliases, dict):
            self.aliases = {}
        
        # Convert sets to ensure JSON serialization compatibility
        if isinstance(self.tags, list):
            self.tags = set(self.tags)
    
    def add_alias(self, source: str, field_name: str) -> None:
        """Add an alias mapping for a specific data source"""
        self.aliases[source] = field_name
        self.updated_at = datetime.now()
    
    def add_validation_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule to this variable"""
        self.validation_rules.append(rule)
        self.updated_at = datetime.now()
    
    def validate_value(self, value: Any) -> tuple[bool, List[str]]:
        """
        Validate a value against all rules for this variable
        
        Args:
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        errors = []
        is_valid = True
        
        for rule in self.validation_rules:
            rule_valid, message = rule.validate(value)
            if not rule_valid:
                if rule.warning_only:
                    logger.warning(f"Validation warning for {self.name}: {message}")
                else:
                    is_valid = False
                    errors.append(message)
        
        return is_valid, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        
        # Convert enums to strings
        data['category'] = self.category.value
        data['data_type'] = self.data_type.value
        data['units'] = self.units.value
        
        # Convert sets to lists
        data['tags'] = list(self.tags)
        
        # Convert datetime to ISO strings
        data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        
        return data


class FinancialVariableRegistry:
    """
    Singleton registry for managing financial variable definitions with thread-safe operations.
    
    This class maintains a centralized catalog of all financial variables used across
    the investment analysis platform, providing:
    - Variable registration and retrieval
    - Category-based organization
    - Source-specific alias resolution
    - Data validation capabilities
    - Thread-safe concurrent access
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the registry if not already initialized"""
        if hasattr(self, '_initialized'):
            return
            
        self._initialized = True
        self._variables: Dict[str, VariableDefinition] = {}
        self._category_index: Dict[VariableCategory, Set[str]] = {
            category: set() for category in VariableCategory
        }
        self._alias_index: Dict[str, Dict[str, str]] = {}  # source -> {alias -> standard_name}
        self._tags_index: Dict[str, Set[str]] = {}         # tag -> {variable_names}
        self._access_lock = threading.RLock()
        
        logger.info("FinancialVariableRegistry initialized")
    
    def register_variable(self, variable_def: VariableDefinition) -> bool:
        """
        Register a new variable definition in the registry
        
        Args:
            variable_def: The variable definition to register
            
        Returns:
            True if successful, False if variable already exists with different definition
        """
        with self._access_lock:
            if variable_def.name in self._variables:
                existing = self._variables[variable_def.name]
                if existing.version == variable_def.version:
                    logger.warning(f"Variable {variable_def.name} already registered with same version")
                    return False
                else:
                    logger.info(f"Updating variable {variable_def.name} from {existing.version} to {variable_def.version}")
            
            # Store the variable
            self._variables[variable_def.name] = variable_def
            
            # Update category index
            self._category_index[variable_def.category].add(variable_def.name)
            
            # Update alias index
            for source, alias in variable_def.aliases.items():
                if source not in self._alias_index:
                    self._alias_index[source] = {}
                self._alias_index[source][alias] = variable_def.name
            
            # Update tags index
            for tag in variable_def.tags:
                if tag not in self._tags_index:
                    self._tags_index[tag] = set()
                self._tags_index[tag].add(variable_def.name)
            
            logger.info(f"Registered variable: {variable_def.name} ({variable_def.category.value})")
            return True
    
    def get_variable_definition(self, name: str) -> Optional[VariableDefinition]:
        """
        Retrieve a variable definition by name
        
        Args:
            name: The variable name to look up
            
        Returns:
            VariableDefinition if found, None otherwise
        """
        with self._access_lock:
            return self._variables.get(name)
    
    def get_variables_by_category(self, category: VariableCategory) -> List[VariableDefinition]:
        """
        Get all variables in a specific category
        
        Args:
            category: The category to filter by
            
        Returns:
            List of variable definitions in the category
        """
        with self._access_lock:
            variable_names = self._category_index[category]
            return [self._variables[name] for name in variable_names if name in self._variables]
    
    def get_variables_by_tag(self, tag: str) -> List[VariableDefinition]:
        """
        Get all variables with a specific tag
        
        Args:
            tag: The tag to filter by
            
        Returns:
            List of variable definitions with the tag
        """
        with self._access_lock:
            if tag not in self._tags_index:
                return []
            variable_names = self._tags_index[tag]
            return [self._variables[name] for name in variable_names if name in self._variables]
    
    def resolve_alias(self, source: str, alias: str) -> Optional[str]:
        """
        Resolve a source-specific alias to standard variable name
        
        Args:
            source: The data source (e.g., "yfinance", "excel")
            alias: The source-specific field name
            
        Returns:
            Standard variable name if found, None otherwise
        """
        with self._access_lock:
            return self._alias_index.get(source, {}).get(alias)
    
    def get_aliases_for_source(self, source: str) -> Dict[str, str]:
        """
        Get all aliases for a specific source
        
        Args:
            source: The data source name
            
        Returns:
            Dictionary mapping aliases to standard names
        """
        with self._access_lock:
            return self._alias_index.get(source, {}).copy()
    
    def validate_value(self, variable_name: str, value: Any) -> tuple[bool, List[str]]:
        """
        Validate a value against the rules for a specific variable
        
        Args:
            variable_name: The variable to validate against
            value: The value to validate
            
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        variable_def = self.get_variable_definition(variable_name)
        if not variable_def:
            return False, [f"Variable {variable_name} not found in registry"]
        
        return variable_def.validate_value(value)
    
    def list_all_variables(self) -> List[str]:
        """Get list of all registered variable names"""
        with self._access_lock:
            return list(self._variables.keys())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        with self._access_lock:
            stats = {
                "total_variables": len(self._variables),
                "categories": {
                    category.value: len(names) 
                    for category, names in self._category_index.items()
                },
                "sources_with_aliases": list(self._alias_index.keys()),
                "total_aliases": sum(len(aliases) for aliases in self._alias_index.values()),
                "tags": list(self._tags_index.keys())
            }
            return stats
    
    def export_to_json(self, file_path: Optional[Union[str, Path]] = None) -> str:
        """
        Export all variable definitions to JSON format
        
        Args:
            file_path: Optional file path to save to
            
        Returns:
            JSON string representation
        """
        with self._access_lock:
            export_data = {
                "schema_version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "variables": {name: var_def.to_dict() for name, var_def in self._variables.items()}
            }
            
            json_str = json.dumps(export_data, indent=2, default=str)
            
            if file_path:
                Path(file_path).write_text(json_str, encoding='utf-8')
                logger.info(f"Exported {len(self._variables)} variables to {file_path}")
            
            return json_str
    
    def export_to_yaml(self, file_path: Optional[Union[str, Path]] = None) -> str:
        """
        Export all variable definitions to YAML format
        
        Args:
            file_path: Optional file path to save to
            
        Returns:
            YAML string representation
        """
        with self._access_lock:
            export_data = {
                "schema_version": "1.0.0",
                "exported_at": datetime.now().isoformat(),
                "variables": {name: var_def.to_dict() for name, var_def in self._variables.items()}
            }
            
            yaml_str = yaml.dump(export_data, default_flow_style=False, sort_keys=False)
            
            if file_path:
                Path(file_path).write_text(yaml_str, encoding='utf-8')
                logger.info(f"Exported {len(self._variables)} variables to {file_path}")
            
            return yaml_str
    
    def import_from_json(self, json_data: Union[str, Dict[str, Any], Path]) -> int:
        """
        Import variable definitions from JSON data
        
        Args:
            json_data: JSON string, dictionary, or file path
            
        Returns:
            Number of variables imported
        """
        if isinstance(json_data, Path) or (isinstance(json_data, str) and Path(json_data).exists()):
            data = json.loads(Path(json_data).read_text(encoding='utf-8'))
        elif isinstance(json_data, str):
            data = json.loads(json_data)
        else:
            data = json_data
        
        imported_count = 0
        variables_data = data.get('variables', {})
        
        for name, var_dict in variables_data.items():
            try:
                # Convert string enums back to enum instances
                var_dict['category'] = VariableCategory(var_dict['category'])
                var_dict['data_type'] = DataType(var_dict['data_type'])
                var_dict['units'] = Units(var_dict['units'])
                
                # Convert datetime strings back to datetime objects
                if 'created_at' in var_dict:
                    var_dict['created_at'] = datetime.fromisoformat(var_dict['created_at'])
                if 'updated_at' in var_dict and var_dict['updated_at']:
                    var_dict['updated_at'] = datetime.fromisoformat(var_dict['updated_at'])
                
                # Convert tags list to set
                if 'tags' in var_dict:
                    var_dict['tags'] = set(var_dict['tags'])
                
                # Reconstruct validation rules
                if 'validation_rules' in var_dict:
                    rules = []
                    for rule_dict in var_dict['validation_rules']:
                        rules.append(ValidationRule(**rule_dict))
                    var_dict['validation_rules'] = rules
                
                var_def = VariableDefinition(**var_dict)
                
                if self.register_variable(var_def):
                    imported_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to import variable {name}: {str(e)}")
        
        logger.info(f"Imported {imported_count} variables from JSON")
        return imported_count
    
    def clear_registry(self) -> None:
        """Clear all variables from the registry (use with caution)"""
        with self._access_lock:
            count = len(self._variables)
            self._variables.clear()
            self._category_index = {category: set() for category in VariableCategory}
            self._alias_index.clear()
            self._tags_index.clear()
            logger.warning(f"Cleared {count} variables from registry")


# Convenience function to get the singleton instance
def get_registry() -> FinancialVariableRegistry:
    """Get the singleton FinancialVariableRegistry instance"""
    return FinancialVariableRegistry()