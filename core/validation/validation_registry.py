"""
Validation Registry - Centralized Configuration and Rule Management

This module provides a centralized registry for validation rules, configurations,
and dynamic rule management for the financial analysis system.
"""

from typing import Dict, List, Any, Callable, Optional, Type, Union
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path
from datetime import datetime
import inspect

import logging

# Create ValidationError exception if not available
class ValidationError(Exception):
    """Validation error exception"""
    pass


class RuleType(Enum):
    """Types of validation rules"""
    
    FORMAT = "format"                    # Data format validation (e.g., ticker format)
    RANGE = "range"                      # Numeric range validation
    CONSISTENCY = "consistency"          # Cross-data consistency checks
    COMPLETENESS = "completeness"        # Data completeness validation
    QUALITY = "quality"                  # Data quality metrics
    BUSINESS = "business"                # Business logic validation
    SECURITY = "security"                # Security and access validation
    PERFORMANCE = "performance"          # Performance impact validation


class RuleScope(Enum):
    """Scope where validation rules apply"""
    
    SYSTEM = "system"                    # System-level validation
    DATA = "data"                        # Data-level validation
    CALCULATION = "calculation"          # Calculation-specific validation
    REPORTING = "reporting"              # Reporting and output validation
    TESTING = "testing"                  # Testing environment validation
    GLOBAL = "global"                    # Applies to all scopes


@dataclass
class ValidationRule:
    """Individual validation rule definition"""
    
    # Rule identification
    rule_id: str
    name: str
    description: str
    
    # Rule classification
    rule_type: RuleType
    scope: RuleScope
    priority: str  # critical, high, medium, low
    
    # Rule implementation
    validator_function: Optional[Callable] = None
    validator_class: Optional[Type] = None
    validator_module: Optional[str] = None
    
    # Rule configuration
    parameters: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Rule metadata
    enabled: bool = True
    created_date: datetime = field(default_factory=datetime.now)
    modified_date: Optional[datetime] = None
    created_by: str = "system"
    
    # Rule dependencies and relationships
    depends_on: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)
    
    # Error handling
    error_message_template: str = ""
    remediation_template: str = ""
    
    def validate_parameters(self) -> bool:
        """Validate rule parameters are consistent"""
        if self.validator_function and not callable(self.validator_function):
            return False
        
        if self.validator_class and not inspect.isclass(self.validator_class):
            return False
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert rule to dictionary for serialization"""
        return {
            'rule_id': self.rule_id,
            'name': self.name,
            'description': self.description,
            'rule_type': self.rule_type.value,
            'scope': self.scope.value,
            'priority': self.priority,
            'parameters': self.parameters,
            'thresholds': self.thresholds,
            'enabled': self.enabled,
            'created_date': self.created_date.isoformat(),
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'created_by': self.created_by,
            'depends_on': self.depends_on,
            'conflicts_with': self.conflicts_with,
            'error_message_template': self.error_message_template,
            'remediation_template': self.remediation_template,
            'validator_module': self.validator_module
        }


@dataclass
class RuleSet:
    """Collection of related validation rules"""
    
    name: str
    description: str
    version: str = "1.0.0"
    rules: List[ValidationRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, rule: ValidationRule):
        """Add a rule to the set"""
        if not isinstance(rule, ValidationRule):
            raise ValueError("Must provide ValidationRule instance")
        
        # Check for duplicates
        if any(r.rule_id == rule.rule_id for r in self.rules):
            raise ValueError(f"Rule {rule.rule_id} already exists in set")
        
        self.rules.append(rule)
    
    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get rule by ID"""
        return next((r for r in self.rules if r.rule_id == rule_id), None)
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove rule by ID"""
        rule = self.get_rule(rule_id)
        if rule:
            self.rules.remove(rule)
            return True
        return False
    
    def get_rules_by_type(self, rule_type: RuleType) -> List[ValidationRule]:
        """Get all rules of specific type"""
        return [r for r in self.rules if r.rule_type == rule_type]
    
    def get_rules_by_scope(self, scope: RuleScope) -> List[ValidationRule]:
        """Get all rules for specific scope"""
        return [r for r in self.rules if r.scope == scope or r.scope == RuleScope.GLOBAL]
    
    def get_enabled_rules(self) -> List[ValidationRule]:
        """Get all enabled rules"""
        return [r for r in self.rules if r.enabled]


class ValidationRegistry:
    """
    Centralized registry for validation rules and configurations
    
    This registry manages all validation rules across the system, providing
    dynamic rule loading, configuration management, and rule dependency resolution.
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize the validation registry
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        self.logger = logging.getLogger(__name__)
        self.rule_sets: Dict[str, RuleSet] = {}
        self.global_config: Dict[str, Any] = {}
        self.config_file = config_file
        
        # Load default rules
        self._load_default_rules()
        
        # Load configuration if provided
        if config_file and Path(config_file).exists():
            self.load_config(config_file)
        
        self.logger.info(f"ValidationRegistry initialized with {len(self.get_all_rules())} rules")
    
    def _load_default_rules(self):
        """Load default validation rules for financial analysis"""
        default_rules = RuleSet(
            name="financial_defaults",
            description="Default financial analysis validation rules",
            version="1.0.0"
        )
        
        # Ticker format validation rule
        ticker_rule = ValidationRule(
            rule_id="ticker_format",
            name="Ticker Symbol Format",
            description="Validates ticker symbol format according to exchange standards",
            rule_type=RuleType.FORMAT,
            scope=RuleScope.DATA,
            priority="critical",
            validator_module="input_validator",
            parameters={
                "validation_level": "moderate",
                "allow_exchange_suffixes": True
            },
            error_message_template="Invalid ticker format: {ticker}",
            remediation_template="Use standard ticker format (e.g., AAPL, MSFT.TO)"
        )
        default_rules.add_rule(ticker_rule)
        
        # Network connectivity rule
        network_rule = ValidationRule(
            rule_id="network_connectivity",
            name="Network Connectivity Check",
            description="Validates network connectivity for data sources",
            rule_type=RuleType.SECURITY,
            scope=RuleScope.SYSTEM,
            priority="high",
            validator_module="input_validator",
            parameters={
                "timeout": 10.0,
                "test_urls": [
                    "https://finance.yahoo.com",
                    "https://query1.finance.yahoo.com"
                ]
            },
            error_message_template="Network connectivity failed: {error}",
            remediation_template="Check internet connection and firewall settings"
        )
        default_rules.add_rule(network_rule)
        
        # Financial data completeness rule
        completeness_rule = ValidationRule(
            rule_id="financial_data_completeness",
            name="Financial Data Completeness",
            description="Validates completeness of financial statement data",
            rule_type=RuleType.COMPLETENESS,
            scope=RuleScope.DATA,
            priority="high",
            validator_module="data_validator",
            parameters={
                "min_years_required": 3,
                "required_statements": ["income_fy", "balance_fy", "cashflow_fy"]
            },
            thresholds={
                "min_completeness_score": 70.0
            },
            error_message_template="Insufficient financial data completeness: {score}%",
            remediation_template="Ensure all required financial statements are available"
        )
        default_rules.add_rule(completeness_rule)
        
        # Numeric range validation rule
        numeric_range_rule = ValidationRule(
            rule_id="numeric_range_validation",
            name="Numeric Range Validation",
            description="Validates numeric values are within reasonable ranges",
            rule_type=RuleType.RANGE,
            scope=RuleScope.DATA,
            priority="medium",
            validator_module="data_validator",
            thresholds={
                "min_value": -1e12,  # -1 trillion
                "max_value": 1e12,   # 1 trillion
                "max_growth_rate": 5.0  # 500%
            },
            error_message_template="Value outside reasonable range: {value}",
            remediation_template="Review source data for accuracy"
        )
        default_rules.add_rule(numeric_range_rule)
        
        # Testing metadata rule
        testing_rule = ValidationRule(
            rule_id="testing_metadata_usage",
            name="Testing Metadata Usage",
            description="Ensures metadata is only used for testing purposes",
            rule_type=RuleType.BUSINESS,
            scope=RuleScope.TESTING,
            priority="critical",
            parameters={
                "allow_metadata_in_production": False,
                "metadata_markers": ["_test", "_mock", "_sample"]
            },
            error_message_template="Metadata usage detected in non-testing context",
            remediation_template="Ensure metadata is only used in testing environment"
        )
        default_rules.add_rule(testing_rule)
        
        # Calculation consistency rule
        calculation_rule = ValidationRule(
            rule_id="calculation_consistency",
            name="Calculation Input Consistency",
            description="Validates consistency of calculation inputs",
            rule_type=RuleType.CONSISTENCY,
            scope=RuleScope.CALCULATION,
            priority="high",
            validator_module="data_validator",
            parameters={
                "check_working_capital": True,
                "check_fcf_reasonableness": True,
                "check_growth_patterns": True
            },
            error_message_template="Calculation input inconsistency detected: {issue}",
            remediation_template="Review financial statement relationships"
        )
        default_rules.add_rule(calculation_rule)
        
        # Add default rule set
        self.register_rule_set(default_rules)
    
    def register_rule_set(self, rule_set: RuleSet):
        """Register a new rule set"""
        if not isinstance(rule_set, RuleSet):
            raise ValueError("Must provide RuleSet instance")
        
        if rule_set.name in self.rule_sets:
            self.logger.warning(f"Overriding existing rule set: {rule_set.name}")
        
        self.rule_sets[rule_set.name] = rule_set
        self.logger.info(f"Registered rule set '{rule_set.name}' with {len(rule_set.rules)} rules")
    
    def unregister_rule_set(self, name: str) -> bool:
        """Unregister a rule set"""
        if name in self.rule_sets:
            del self.rule_sets[name]
            self.logger.info(f"Unregistered rule set: {name}")
            return True
        return False
    
    def get_rule_set(self, name: str) -> Optional[RuleSet]:
        """Get rule set by name"""
        return self.rule_sets.get(name)
    
    def get_all_rules(self) -> List[ValidationRule]:
        """Get all rules from all rule sets"""
        all_rules = []
        for rule_set in self.rule_sets.values():
            all_rules.extend(rule_set.rules)
        return all_rules
    
    def get_rules_by_scope(self, scope: RuleScope, enabled_only: bool = True) -> List[ValidationRule]:
        """Get all rules for a specific scope"""
        rules = []
        for rule_set in self.rule_sets.values():
            scope_rules = rule_set.get_rules_by_scope(scope)
            if enabled_only:
                scope_rules = [r for r in scope_rules if r.enabled]
            rules.extend(scope_rules)
        return rules
    
    def get_rules_by_type(self, rule_type: RuleType, enabled_only: bool = True) -> List[ValidationRule]:
        """Get all rules of a specific type"""
        rules = []
        for rule_set in self.rule_sets.values():
            type_rules = rule_set.get_rules_by_type(rule_type)
            if enabled_only:
                type_rules = [r for r in type_rules if r.enabled]
            rules.extend(type_rules)
        return rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[ValidationRule]:
        """Get rule by ID across all rule sets"""
        for rule_set in self.rule_sets.values():
            rule = rule_set.get_rule(rule_id)
            if rule:
                return rule
        return None
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a specific rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = True
            rule.modified_date = datetime.now()
            self.logger.info(f"Enabled rule: {rule_id}")
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a specific rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.enabled = False
            rule.modified_date = datetime.now()
            self.logger.info(f"Disabled rule: {rule_id}")
            return True
        return False
    
    def update_rule_parameters(self, rule_id: str, parameters: Dict[str, Any]) -> bool:
        """Update parameters for a specific rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.parameters.update(parameters)
            rule.modified_date = datetime.now()
            self.logger.info(f"Updated parameters for rule: {rule_id}")
            return True
        return False
    
    def update_rule_thresholds(self, rule_id: str, thresholds: Dict[str, float]) -> bool:
        """Update thresholds for a specific rule"""
        rule = self.get_rule_by_id(rule_id)
        if rule:
            rule.thresholds.update(thresholds)
            rule.modified_date = datetime.now()
            self.logger.info(f"Updated thresholds for rule: {rule_id}")
            return True
        return False
    
    def validate_rule_dependencies(self) -> List[str]:
        """Validate rule dependencies and return conflicts"""
        conflicts = []
        all_rules = self.get_all_rules()
        rule_ids = {rule.rule_id for rule in all_rules}
        
        for rule in all_rules:
            # Check if dependencies exist
            for dep_id in rule.depends_on:
                if dep_id not in rule_ids:
                    conflicts.append(f"Rule {rule.rule_id} depends on non-existent rule {dep_id}")
            
            # Check for circular dependencies (simple check)
            for dep_id in rule.depends_on:
                dep_rule = self.get_rule_by_id(dep_id)
                if dep_rule and rule.rule_id in dep_rule.depends_on:
                    conflicts.append(f"Circular dependency between {rule.rule_id} and {dep_id}")
            
            # Check conflicts
            for conflict_id in rule.conflicts_with:
                conflict_rule = self.get_rule_by_id(conflict_id)
                if conflict_rule and conflict_rule.enabled and rule.enabled:
                    conflicts.append(f"Conflicting enabled rules: {rule.rule_id} and {conflict_id}")
        
        return conflicts
    
    def load_config(self, config_file: str):
        """Load configuration from file"""
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)
            
            # Load global configuration
            self.global_config.update(config_data.get('global_config', {}))
            
            # Load rule sets
            for rule_set_data in config_data.get('rule_sets', []):
                rule_set = self._parse_rule_set(rule_set_data)
                self.register_rule_set(rule_set)
            
            self.logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_file}", error=e)
            raise ValidationError(f"Configuration load failed: {str(e)}")
    
    def save_config(self, config_file: str):
        """Save current configuration to file"""
        config_data = {
            'global_config': self.global_config,
            'rule_sets': [self._serialize_rule_set(rs) for rs in self.rule_sets.values()],
            'generated_at': datetime.now().isoformat()
        }
        
        config_path = Path(config_file)
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    yaml.dump(config_data, f, default_flow_style=False)
                else:
                    json.dump(config_data, f, indent=2, default=str)
            
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {config_file}", error=e)
            raise ValidationError(f"Configuration save failed: {str(e)}")
    
    def _parse_rule_set(self, rule_set_data: Dict[str, Any]) -> RuleSet:
        """Parse rule set from configuration data"""
        rule_set = RuleSet(
            name=rule_set_data['name'],
            description=rule_set_data.get('description', ''),
            version=rule_set_data.get('version', '1.0.0'),
            metadata=rule_set_data.get('metadata', {})
        )
        
        for rule_data in rule_set_data.get('rules', []):
            rule = ValidationRule(
                rule_id=rule_data['rule_id'],
                name=rule_data['name'],
                description=rule_data.get('description', ''),
                rule_type=RuleType(rule_data['rule_type']),
                scope=RuleScope(rule_data['scope']),
                priority=rule_data['priority'],
                parameters=rule_data.get('parameters', {}),
                thresholds=rule_data.get('thresholds', {}),
                enabled=rule_data.get('enabled', True),
                depends_on=rule_data.get('depends_on', []),
                conflicts_with=rule_data.get('conflicts_with', []),
                error_message_template=rule_data.get('error_message_template', ''),
                remediation_template=rule_data.get('remediation_template', ''),
                validator_module=rule_data.get('validator_module')
            )
            rule_set.add_rule(rule)
        
        return rule_set
    
    def _serialize_rule_set(self, rule_set: RuleSet) -> Dict[str, Any]:
        """Serialize rule set to configuration data"""
        return {
            'name': rule_set.name,
            'description': rule_set.description,
            'version': rule_set.version,
            'metadata': rule_set.metadata,
            'rules': [rule.to_dict() for rule in rule_set.rules]
        }
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        all_rules = self.get_all_rules()
        
        stats = {
            'total_rule_sets': len(self.rule_sets),
            'total_rules': len(all_rules),
            'enabled_rules': len([r for r in all_rules if r.enabled]),
            'disabled_rules': len([r for r in all_rules if not r.enabled]),
            'rules_by_type': {},
            'rules_by_scope': {},
            'rules_by_priority': {}
        }
        
        # Count by type
        for rule_type in RuleType:
            stats['rules_by_type'][rule_type.value] = len(self.get_rules_by_type(rule_type, False))
        
        # Count by scope
        for scope in RuleScope:
            stats['rules_by_scope'][scope.value] = len(self.get_rules_by_scope(scope, False))
        
        # Count by priority
        for rule in all_rules:
            priority = rule.priority
            stats['rules_by_priority'][priority] = stats['rules_by_priority'].get(priority, 0) + 1
        
        return stats


# Global registry instance
_registry_instance: Optional[ValidationRegistry] = None


def get_validation_registry() -> ValidationRegistry:
    """Get the global validation registry instance"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ValidationRegistry()
    return _registry_instance


def initialize_registry(config_file: str = None) -> ValidationRegistry:
    """Initialize the global validation registry with configuration"""
    global _registry_instance
    _registry_instance = ValidationRegistry(config_file)
    return _registry_instance


if __name__ == "__main__":
    # Example usage
    print("=== Validation Registry Test ===")
    
    # Initialize registry
    registry = ValidationRegistry()
    
    # Print statistics
    stats = registry.get_registry_stats()
    print(f"\nRegistry Statistics:")
    print(f"Total Rules: {stats['total_rules']}")
    print(f"Enabled Rules: {stats['enabled_rules']}")
    print(f"Rules by Type: {stats['rules_by_type']}")
    
    # Test rule retrieval
    ticker_rules = registry.get_rules_by_type(RuleType.FORMAT)
    print(f"\nFormat Rules: {len(ticker_rules)}")
    for rule in ticker_rules:
        print(f"  - {rule.name}: {rule.description}")
    
    # Test rule modification
    print("\nTesting rule modification...")
    success = registry.update_rule_parameters(
        'ticker_format',
        {'validation_level': 'strict'}
    )
    print(f"Parameter update success: {success}")
    
    # Validate dependencies
    conflicts = registry.validate_rule_dependencies()
    print(f"Dependency conflicts: {len(conflicts)}")
    
    print("\n=== Test Complete ===")